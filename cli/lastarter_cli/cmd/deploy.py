"""`lastarter deploy` — assemblage et lancement docker-compose d'un déploiement client.

Phase 2 : cible mono-VM (compose). Gates avant tout effet réseau :
docker présent, déploiement initialisé, secrets présents, chaque brique sélectionnée
possède un fichier compose. Les secrets ne quittent jamais `deployments/<client>/.runtime/`
(gitignoré) — les drafts committables ne contiennent que des jetons.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import shutil
import ssl
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..catalogue import Brick, find_catalogue, load_catalogue

SECRET_TOKEN = re.compile(r"\{secret:([a-z0-9_]+)\}", re.IGNORECASE)
REALM_SECRET_TOKEN = re.compile(r"\{\{SECRET:([a-z0-9_]+)\}\}", re.IGNORECASE)


class DeployError(Exception):
    """Erreur attendue — remontée propre en exit 1."""


# ---------------------------------------------------------------------------
# Contextes et rendus


def _scheme(domain: str) -> str:
    """Toujours https : le POC local aussi passe par la passerelle TLS
    (les apps La Suite forcent SECURE_SSL_REDIRECT en configuration prod,
    et livekit/wss + média exigent une origine sécurisée)."""
    return "https"


def compute_origin(domain: str) -> str:
    """Origine du domaine apex (SSO)."""
    return f"{_scheme(domain)}://{domain}"


def app_origin(domain: str, label: str) -> str:
    """Origine d'une app : <label>.<domaine> (routage passerelle)."""
    return f"{_scheme(domain)}://{label}.{domain}"


def _id_origin(domain: str) -> str:
    """Origine du service d'identité : id.<domaine>."""
    return f"{_scheme(domain)}://id.{domain}"


def _context(answers: dict, label: str | None, s3_port: str = "9000") -> dict[str, str]:
    domain = answers["domain"]
    scheme = _scheme(domain)
    context = {
        "{domain}": domain,
        # SSO sur son propre hôte dédié : id.<domaine> (l'identité a sa marque).
        "{sso_origin}": f"{scheme}://id.{domain}",
        "{id_origin}": f"{scheme}://id.{domain}",
        "{ws}": "wss",
        "{brand_name}": answers.get("brand_name", "LaStarter"),
    }
    # S3 média : routé par la passerelle (sous-domaine dédié par brique).
    if label:
        context["{domain_s3}"] = f"{label}-media.{domain}"
    else:
        context["{domain_s3}"] = f"s3.{domain}"
    if label:
        context["{origin}"] = f"{scheme}://{label}.{domain}"
        context["{app_host}"] = f"{label}.{domain}"
        # ALLOWED_HOSTS Django : domaine SANS port (split_domain_port à la validation).
        context["{app_bare}"] = f"{label}.{domain.split(':')[0]}"
    else:
        context["{origin}"] = context["{sso_origin}"]
        context["{app_host}"] = domain
        context["{app_bare}"] = domain.split(":")[0]
    # Les apps La Suite en mode Production/Feature forcent SECURE_SSL_REDIRECT :
    # la passerelle sert TLS partout (POC compris), on sert donc Feature.
    context["{django_configuration}"] = "Feature"
    # Domaine apex sans schéma ni port (server_name Matrix, HS_SERVER_NAME rtc).
    context["{domain_bare}"] = domain.split(":")[0]
    return context


def render_runtime_env(
    draft: str, answers: dict, vault: dict[str, str], label: str | None = None, s3_port: str = "9000"
) -> str:
    """Substitue les jetons d'un draft committable en env d'exécution (avec secrets)."""
    context = _context(answers, label, s3_port)

    def substitute(value: str) -> str:
        def secret(match: re.Match) -> str:
            name = match.group(1)
            if name not in vault:
                raise DeployError(f"secret manquant dans secrets.env : {name}")
            return vault[name]

        value = SECRET_TOKEN.sub(secret, value)
        for token, replacement in context.items():
            value = value.replace(token, replacement)
        return value

    return "\n".join(substitute(line) for line in draft.splitlines()) + "\n"


def _client_secret_from_env(rendered_env: str) -> str:
    """Extrait le secret OIDC d'un env rendu (source unique : la brique).

    Django (drive, messages…) : OIDC_RP_CLIENT_SECRET.
    Node.js (projects) : OIDC_CLIENT_SECRET.
    """
    for line in rendered_env.splitlines():
        if line.startswith("OIDC_RP_CLIENT_SECRET="):
            return line.partition("=")[2].strip()
    for line in rendered_env.splitlines():
        if line.startswith("OIDC_CLIENT_SECRET="):
            return line.partition("=")[2].strip()
    raise DeployError("OIDC_RP_CLIENT_SECRET / OIDC_CLIENT_SECRET absent de l'env rendu")


# Clients de console de compte injectés dans le realm importé : requis pour
# l'audience "account" (scope + mapper du template) et l'API /account/*.
# Le secret OIDC de chaque brique reste géré par build_realm_clients.
ACCOUNT_CONSOLE_CLIENTS = [
    {
        "clientId": "account",
        "name": "Account API",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": True,
        "standardFlowEnabled": True,
        "redirectUris": ["/realms/lastarter/account/*"],
        "webOrigins": ["+"],
        "defaultClientScopes": [
            "web-origins", "acr", "roles", "profile", "basic", "email", "account",
        ],
    },
    {
        "clientId": "account-console",
        "name": "Account Console",
        "enabled": True,
        "protocol": "openid-connect",
        "publicClient": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False,
        "redirectUris": ["/realms/lastarter/account/*"],
        "webOrigins": ["+"],
        "defaultClientScopes": [
            "web-origins", "acr", "roles", "profile", "basic", "email", "account",
        ],
        "attributes": {"pkce.code.challenge.method": "S256"},
    },
]


def build_realm_clients(bricks: list[Brick], rendered_envs: dict[str, str], answers: dict) -> str:
    """Construit le tableau JSON des clients OIDC depuis le catalogue + env rendus.

    Le secret de chaque client est celui de sa brique (OIDC_RP_CLIENT_SECRET) :
    source unique, toujours synchronisée.
    """
    domain = answers["domain"]
    clients = []
    for brick in bricks:
        if brick.core or not brick.oidc.get("client_id"):
            continue
        origin = app_origin(domain, brick.compose.get("route_label", brick.name))
        clients.append(
            {
                "clientId": brick.oidc["client_id"],
                "description": f"LaStarter {brick.title} (OIDC)",
                "enabled": True,
                "consentRequired": False,  # consentement implicite : apps de première partie, pas d'écran « Continue to your account »
                "clientAuthenticatorType": "client-secret",
                "secret": _client_secret_from_env(rendered_envs[brick.name]),
                "redirectUris": [f"{origin}/*"],
                "webOrigins": [origin],
                "standardFlowEnabled": True,
                "implicitFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "serviceAccountsEnabled": False,
                "publicClient": False,
                "frontchannelLogout": True,
                "protocol": "openid-connect",
                "fullScopeAllowed": True,
                "attributes": {
                    "user.info.response.signature.alg": "RS256",
                    "post.logout.redirect.uris": f"{origin}/*",
                    "backchannel.logout.session.required": "true",
                },
                # Scope « account » obligatoire : il porte le mapper
                # audience-account (sans lui, l'API console de compte répond 401).
                "defaultClientScopes": ["web-origins", "acr", "roles", "profile", "basic", "email", "account"],
                "optionalClientScopes": ["address", "phone", "offline_access"],
            }
        )
    return json.dumps(clients, indent=2, ensure_ascii=False)


def render_realm(template: str, answers: dict, vault: dict[str, str], clients_json: str) -> str:
    """Rend le realm Keycloak ({{CLIENTS_JSON}}, {{ORIGIN}}, {{SECRET:x}})."""
    rendered = template.replace("{{CLIENTS_JSON}}", clients_json)
    rendered = rendered.replace("{{ORIGIN}}", compute_origin(answers["domain"]))

    def secret(match: re.Match) -> str:
        name = match.group(1)
        if name not in vault:
            raise DeployError(f"secret manquant dans secrets.env : {name}")
        return vault[name]

    return REALM_SECRET_TOKEN.sub(secret, rendered)


def cert_san_names_for(selected_bricks: list[Brick], domain: str) -> list[str]:
    """SANs du certificat POC : domaine apex NU (le portail est servi sur
    https://<domaine>) + id.<domaine> (SSO) + chaque app + serveurs
    additionnels (media/livekit). ensure_dev_certs ajoute « localhost »."""
    cert_bare = domain.split(":")[0]
    names = [cert_bare, f"id.{cert_bare}"]
    for brick in selected_bricks:
        if brick.core:
            continue
        names.append(f"{brick.compose.get('route_label', brick.name)}.{cert_bare}")
        for extra in brick.compose.get("extra_servers", []):
            names.append(f"{extra['label']}.{cert_bare}")
    return names


def ensure_dev_certs(runtime_dir: Path, san_names: list[str]) -> tuple[Path, Path, Path, bool]:
    """CA locale + certificat pour la passerelle TLS (POC).

    SANs explicites pour chaque hôte déployé (CPython 3.12+ refuse les wildcards
    sur un domaine mono-label type *.localhost côté vérification stricte ; les
    navigateurs, eux, acceptent le wildcard). Retourne (ca, crt, key, changé) —
    `changé` = certificats (re)générés → le serveur doit recharger.
    """
    certs_dir = runtime_dir / "certs"
    certs_dir.mkdir(parents=True, exist_ok=True)
    ca, crt, key = certs_dir / "ca.crt", certs_dir / "server.crt", certs_dir / "server.key"
    ca_key = certs_dir / "ca.key"
    # SANs explicites uniquement — JAMAIS de "*.localhost" : service_identity
    # (Twisted/Synapse) rejette le certificat ENTIER dès qu'il voit un wildcard
    # mono-label (« too few host components for wildcard usage », RFC 6125),
    # même si des noms explicites sont présents. Leçon du POC chat.localhost.
    wanted_sans = sorted(set(san_names) | {"localhost"})
    marker = certs_dir / ".sans"
    current_sans = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    leaf_current = crt.is_file() and key.is_file() and current_sans == "\n".join(wanted_sans)
    if ca.is_file() and leaf_current:
        return ca, crt, key, False

    # CA créée UNE fois (confiance navigateur stable) ; seul le certificat
    # feuille est re-émis quand la liste d'hôtes change.
    san_line = ",".join(f"DNS:{name}" for name in wanted_sans)
    make_ca = "" if ca.is_file() and ca_key.is_file() else (
        # Extensions X.509 obligatoires : Python/OpenSSL modernes refusent une
        # CA sans basicConstraints/keyUsage (« CA cert does not include key
        # usage extension »). Leçon du POC.
        "openssl req -x509 -newkey rsa:2048 -nodes -days 3650 "
        "-keyout /certs/ca.key -out /certs/ca.crt -subj '/CN=LaStarter POC CA' "
        "-addext 'basicConstraints=critical,CA:TRUE' "
        "-addext 'keyUsage=critical,keyCertSign,cRLSign' "
        "-addext 'subjectKeyIdentifier=hash'; "
    )
    script = (
        "set -e; "
        + make_ca
        + "openssl req -newkey rsa:2048 -nodes "
        "-keyout /certs/server.key -out /certs/server.csr -subj '/CN=localhost'; "
        "printf 'basicConstraints=CA:FALSE\\n"
        "keyUsage=digitalSignature,keyEncipherment\\n"
        "extendedKeyUsage=serverAuth\\n"
        f"subjectAltName={san_line}\\n' > /certs/san.ext; "
        "openssl x509 -req -in /certs/server.csr -CA /certs/ca.crt -CAkey /certs/ca.key "
        "-CAcreateserial -out /certs/server.crt -days 825 -sha256 -extfile /certs/san.ext; "
        "rm -f /certs/server.csr /certs/san.ext /certs/ca.srl"
    )
    result = subprocess.run(
        [
            "docker", "run", "--rm",
            "-v", f"{_portable(certs_dir)}:/certs",
            "--entrypoint", "sh",
            "alpine/openssl", "-c", script,
        ],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0 or not (ca.is_file() and crt.is_file() and key.is_file()):
        raise DeployError(f"échec de génération des certificats POC : {result.stderr[:300]}")
    marker.write_text("\n".join(wanted_sans) + "\n", encoding="utf-8")
    return ca, crt, key, True


VPN_ALLOW = "10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 127.0.0.1"


def _theme_nginx_block(include_auto_login: bool = True, auth_url: str = "/api/v1.0/authenticate/") -> list[str]:
    """Bloc nginx commun : sert le thème CSS et l'injecte dans le HTML.

    include_auto_login=False pour le portail/login (pas de redirect auth).
    auth_url : URL de redirection selon la brique (Django vs Sails.js).
    """
    if include_auto_login:
        inject = f'<link rel="stylesheet" href="/__lastarter/theme.css"><script src="/__lastarter/auto-login.js" data-auth="{auth_url}"></script></head>'
    else:
        inject = '<link rel="stylesheet" href="/__lastarter/theme.css"></head>'
    return [
        "    # Thème LaStarter : CSS (palette + marque blanche) injecté dans le HTML.",
        "    location = /__lastarter/theme.css {",
        "        alias /var/www/lastarter-theme/theme.css;",
        "        default_type text/css;",
        '        add_header Cache-Control "no-cache";',
        "    }",
        f"    location = /__lastarter/auto-login.js {{",
        f"        alias /var/www/lastarter-theme/auto-login.js;",
        f"        default_type application/javascript;",
        f'        add_header Cache-Control "no-cache";',
        f"    }}",
        # Fonts Inter (même source qu'Element Web : @fontsource/inter).
        "    location /__lastarter/fonts/ {",
        "        alias /var/www/lastarter-theme/fonts/;",
        '        add_header Cache-Control "public, max-age=31536000";',
        '        add_header Access-Control-Allow-Origin *;',
        "    }",
        "    # Branding client (logo) : deployments/<client>/branding -> .runtime/branding,",
        "    # servi par la passerelle sur /__lastarter/branding/ (tous les sous-domaines).",
        "    location /__lastarter/branding/ {",
        "        alias /var/www/lastarter-theme/branding/;",
        '        add_header Cache-Control "no-cache";',
        "    }",
        f"    sub_filter '</head>' '{inject}';",
        "    sub_filter_once off;",
        "",
    ]


def render_edge(bricks: list[Brick], answers: dict) -> str:
    """Génère la conf nginx de la passerelle : apex → SSO, <label>.<domain> → app.

    Contrôle d'accès par brique : access = "vpn" restreint l'app aux réseaux
    privés (LAN + WireGuard/CGNAT + loopback) ; "public" (défaut) sans limite.
    L'identité (id.<domaine>) reste toujours accessible dès qu'une app publique
    existe — le SSO doit joignable pour se connecter.
    """
    domain = answers["domain"]
    bare = domain.split(":")[0]  # server_name nginx : jamais de port
    lines: list[str] = [
        "# LaStarter — passerelle générée par lastarter-cli (ne pas éditer à la main).",
        "# Apex → portail ; id.<domaine> → Keycloak (auth) ; apps = sous-domaines.",
        "server {",
        "    listen 8443 ssl default_server;",
        "    http2 on;",
        "    ssl_certificate /etc/nginx/certs/server.crt;",
        "    ssl_certificate_key /etc/nginx/certs/server.key;",
        f"    server_name {bare} _;",
        "    server_tokens off;",
        "    client_max_body_size 150m;",
        "",
    ]
    # Portail : PAS d'auto-login (le portail affiche les tuiles sans session).
    lines += _theme_nginx_block(include_auto_login=False)
    lines += [
        "    # Endpoints SSO accessibles aussi sur l'apex (outillage/CLI, compat).",
    ]
    for path in ("/realms/", "/resources/", "/js/", "/admin/"):
        lines += [
            f"    location {path} {{",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            "        set $backend_keycloak keycloak:8080;",
            "        proxy_pass http://$backend_keycloak;",
            "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
            "        proxy_set_header X-Forwarded-Proto https;",
            "    }",
        ]
    lines += [
        "",
        "    # Le portail vit à la racine de l'apex.",
        "    location / {",
        "        resolver 127.0.0.11 valid=10s ipv6=off;",
        "        set $backend_portal portal:80;",
        "        proxy_pass http://$backend_portal;",
        "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
        "        proxy_set_header X-Forwarded-Proto https;",
        "        # Portail : revalidation systématique (ETag/304) — jamais de cache",
        "        # périmé après l'ajout d'une brique (portal-config.json surtout).",
        '        add_header Cache-Control "no-cache" always;',
        "    }",
        "}",
        "",
    ]
    # Serveur d'identité dédié : id.<domaine> → Keycloak (toute l'auth).
    # PAS d'injection theme.css ici : la page de login a SON theme complet
    # (identity/keycloak-theme : deux colonnes, tokens Compound, Inter) —
    # le CSS d'app injecté via sub_filter ajouterait des bordures/cartes
    # par-dessus et casserait le design.
    lines += [
        "# Identité — id.<domaine> → Keycloak",
        "server {",
        "    listen 8443 ssl;",
        "    http2 on;",
        "    ssl_certificate /etc/nginx/certs/server.crt;",
        "    ssl_certificate_key /etc/nginx/certs/server.key;",
        f"    server_name id.{bare};",
        "    server_tokens off;",
        "    client_max_body_size 150m;",
        "",
    ]
    lines += [
        "    location / {",
        "        resolver 127.0.0.11 valid=10s ipv6=off;",
        "        set $backend_keycloak keycloak:8080;",
        "        proxy_pass http://$backend_keycloak;",
        "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
        "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
        "        proxy_set_header X-Forwarded-Proto https;",
        "    }",
        "}",
        "",
    ]
    apps = [b for b in bricks if not b.core and b.compose.get("frontend_target")]

    for brick in apps:
        label = brick.compose.get("route_label", brick.name)
        api_target = brick.compose.get("api_target")
        lines += [
            f"# {brick.title}",
            "server {",
            "    listen 8443 ssl;",
            "    http2 on;",
            "    ssl_certificate /etc/nginx/certs/server.crt;",
            "    ssl_certificate_key /etc/nginx/certs/server.key;",
            f"    server_name {label}.{bare};",
            "    server_tokens off;",
            "    client_max_body_size 150m;",
            "",
        ]
        # Discussions (Element Web) : DÉJÀ en Compound natif — NE PAS injecter le
        # thème (il entrerait en conflit avec ses styles propres), ni l'auto-login
        # (son SSO est natif : Synapse OIDC).
        if brick.name != "discussions":
            lines += _theme_nginx_block(auth_url="/api/v1.0/authenticate/")

        if api_target:
            lines += [
                "    location /api/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_api {api_target};",
                "        proxy_pass http://$backend_api;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Real-IP $remote_addr;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                "    }",
                "",
                # Django admin : route directe (Caddy distroless ne resout pas le DNS).
                "    location /admin/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_admin {api_target};",
                "        proxy_pass http://$backend_admin;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
                "    location /static/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_static {api_target};",
                "        proxy_pass http://$backend_static;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",  # évite la boucle 301 SECURE_SSL_REDIRECT
                "    }",
                "",
            ]
        if brick.compose.get("access") == "vpn":
            lines += [
                f"    # Accès restreint : VPN/LAN uniquement ({brick.name}).",
                f"    allow {VPN_ALLOW.replace(' ', '; allow ')};",
                "    deny all;",
                "",
            ]
        lines += [
            "    # Service Worker : header requis derrière un reverse proxy",
            "    # (l'enregistrement échoue sans lui dans les navigateurs Chromium).",
            "    location = /sw.js {",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            f"        set $backend_front {brick.compose['frontend_target']};",
            "        proxy_pass http://$backend_front;",
            "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
            '        add_header Service-Worker-Allowed "/";',
            '        add_header Cache-Control "no-cache";',
            "    }",
            "",
        ]
        # Aucune page /login ni /register : le SSO (id.<domaine>) fait l'auth.
        # Blocage passerelle pour TOUTES les apps → redirect vers /.
        lines += [
            "    location = /login { return 302 https://$host/; }",
            "    location = /register { return 302 https://$host/; }",
            "    location = /signup { return 302 https://$host/; }",
            "",
        ]
        # Discussions (Element Web + Synapse) : same-origin validé en POC —
        # l'API Matrix et le callback SSO vivent sur chat.<domaine> (un seul
        # certificat, pas de CORS, pas de canonicalisation Synapse).
        if brick.name == "discussions":
            lines += [
                "    # Matrix API -> Synapse (same-origin : un seul certificat).",
                "    location /_matrix/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_matrix discussions_synapse:8008;",
                "        proxy_pass http://$backend_matrix;",
                "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
                "    # Synapse OIDC callback (same-origin SSO).",
                "    location /_synapse/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_syn discussions_synapse:8008;",
                "        proxy_pass http://$backend_syn;",
                "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
            ]
        # Drive : medias S3 avec auth-request par le backend Django
        # (le bucket n'est JAMAIS exposé directement).
        if brick.name == "drive":
            lines += [
                "    # Medias : auth par le backend puis S3 rustfs (jamais direct).",
                "    location /media/ {",
                "        auth_request /drive-media-auth;",
                "        auth_request_set $authHeader $upstream_http_authorization;",
                "        auth_request_set $authDate $upstream_http_x_amz_date;",
                "        auth_request_set $authContentSha256 $upstream_http_x_amz_content_sha256;",
                "        proxy_set_header Authorization $authHeader;",
                "        proxy_set_header X-Amz-Date $authDate;",
                "        proxy_set_header X-Amz-Content-SHA256 $authContentSha256;",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                # Alias tiret (drive-rustfs) : aws-cli/botocore rejette les
                # noms d'hôte avec tiret bas (Invalid endpoint).
                "        set $backend_s3 drive-rustfs:9000;",
                "        proxy_pass http://$backend_s3;",
                "        proxy_set_header Host drive-rustfs:9000;",
                '        add_header Content-Disposition "attachment";',
                "    }",
                "    location = /drive-media-auth {",
                "        internal;",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_driveapi drive_backend:8000;",
                "        proxy_pass http://$backend_driveapi/api/v1.0/items/media-auth/;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_set_header Host $host;",
                "        proxy_set_header X-Original-URL $request_uri;",
                "        proxy_pass_request_body off;",
                '        proxy_set_header Content-Length "";',
                "        proxy_set_header X-Original-Method $request_method;",
                "    }",
                "",
            ]
        lines += [
            "    location / {",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            f"        set $backend_front {brick.compose['frontend_target']};",
            "        proxy_pass http://$backend_front;",
            "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
            "        proxy_set_header X-Forwarded-Proto https;",
            "        proxy_http_version 1.1;",
            "        proxy_set_header Upgrade $http_upgrade;",
            '        proxy_set_header Connection "upgrade";',
            "        proxy_read_timeout 3600s;",
            "    }",
            "}",
            "",
        ]

    # Serveurs additionnels (ex. SFU livekit pour meet) : websocket natif.
    for brick in bricks:
        for extra in brick.compose.get("extra_servers", []):
            lines += [
                f"# {brick.title} — {extra.get('label', '')}",
                "server {",
                "    listen 8443 ssl;",
                "    ssl_certificate /etc/nginx/certs/server.crt;",
                "    ssl_certificate_key /etc/nginx/certs/server.key;",
                f"    server_name {extra['label']}.{bare};",
                "    location / {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_extra {extra['target']};",
                "        proxy_pass http://$backend_extra;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                "        proxy_read_timeout 3600s;",
                "    }",
                "}",
                "",
            ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chargement et gates


def load_deployment(repo_root: Path, slug: str) -> tuple[dict, dict, dict[str, str], dict[str, Brick]]:
    catalogue_dir = repo_root / "catalogue"
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        raise DeployError("catalogue invalide : " + " ; ".join(errors))

    deployment_dir = repo_root / "deployments" / slug
    manifest_path = deployment_dir / "lastarter.toml"
    if not manifest_path.is_file():
        raise DeployError(f"déploiement inconnu : {manifest_path} (lancer `lastarter init`)")
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    answers_path = deployment_dir / "answers.json"
    if not answers_path.is_file():
        raise DeployError(f"answers.json manquant : {answers_path}")
    answers = json.loads(answers_path.read_text(encoding="utf-8"))

    from .init import parse_secrets_env

    vault = parse_secrets_env(deployment_dir / "secrets.env")
    if not vault:
        raise DeployError(
            f"secrets.env manquant ou vide : {deployment_dir / 'secrets.env'} "
            "(rejouer `lastarter init`)"
        )
    return manifest, answers, vault, bricks


def validate_compose_targets(selected: list[str], bricks: dict[str, Brick], compose_dir: Path) -> None:
    for name in selected:
        if not (compose_dir / f"{name}.yml").is_file():
            raise DeployError(
                f"la brique « {name} » n'a pas de cible compose (phase future) — "
                "retirer du déploiement ou utiliser `lastarter init`"
            )


def render_drive_backend_env(answers: dict, vault: dict[str, str], frontend_theme: str = "dsfr-light") -> str:
    """Rend l'env du backend Drive (Django + OIDC realm lastarter + S3 rustfs)."""
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    drive_origin = f"{scheme}://drive.{bare}" + (f":{port}" if port else "")
    id_origin = _id_origin(domain)

    def secret(name: str) -> str:
        if name not in vault:
            raise DeployError(f"secret manquant dans secrets.env : {name}")
        return vault[name]

    django_key = secret("kc_admin_password") if "drive_django_key" not in vault else secret("drive_django_key")
    return f"""# Rendu par lastarter-cli — ne pas éditer à la main.
DJANGO_SETTINGS_MODULE=drive.settings
DJANGO_CONFIGURATION=Production
DJANGO_SECRET_KEY={django_key}-drive
DJANGO_ALLOWED_HOSTS=drive.{bare},{bare}

DATABASE_URL=postgres://dinum:pass@drive_postgresql:5432/drive
DB_HOST=drive_postgresql
DB_NAME=drive
DB_USER=dinum
DB_PASSWORD=pass
DB_PORT=5432

AWS_S3_ACCESS_KEY_ID=drive
AWS_S3_SECRET_ACCESS_KEY={secret("drive_s3_secret")}
AWS_S3_REGION_NAME=eu-east-1
AWS_S3_SIGNATURE_VERSION=s3v4
AWS_S3_ENDPOINT_URL=http://drive-rustfs:9000
AWS_S3_DOMAIN_REPLACE={drive_origin}
MEDIA_BASE_URL={drive_origin}

REDIS_URL=redis://drive_redis:6379/0
# Celery : requis par l'amont (helm : CELERY_BROKER_URL) en plus de REDIS_URL —
# sinon les tâches async pointent redis://redis:6379 (hôte inexistant ici).
CELERY_BROKER_URL=redis://drive_redis:6379/0

OIDC_OP_JWKS_ENDPOINT={id_origin}/realms/lastarter/protocol/openid-connect/certs
OIDC_OP_AUTHORIZATION_ENDPOINT={id_origin}/realms/lastarter/protocol/openid-connect/auth
OIDC_OP_TOKEN_ENDPOINT={id_origin}/realms/lastarter/protocol/openid-connect/token
OIDC_OP_USER_ENDPOINT={id_origin}/realms/lastarter/protocol/openid-connect/userinfo
OIDC_RP_CLIENT_ID=drive
OIDC_RP_CLIENT_SECRET={secret("drive_oidc_secret")}
OIDC_RP_SIGN_ALGO=RS256
OIDC_RP_SCOPES=openid email profile
LOGIN_REDIRECT_URL={drive_origin}
LOGIN_REDIRECT_URL_FAILURE={drive_origin}
LOGOUT_REDIRECT_URL={drive_origin}
OIDC_REDIRECT_ALLOWED_HOSTS=drive.{bare}{":" + port if port else ""},id.{bare}{":" + port if port else ""}

FRONTEND_THEME={frontend_theme}
FRONTEND_FEEDBACK_BUTTON_SHOW=False
FRONTEND_FEEDBACK_MESSAGES_WIDGET_ENABLED=False
USER_RECONCILIATION_FORM_URL={drive_origin}
MALWARE_DETECTION_BACKEND=core.malware_detection.SleepyDummyBackend
FEATURES_INDEXED_SEARCH=False
WOPI_CLIENTS=
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
SEARCH_INDEXER_CLASS=
"""


def render_meet_livekit_config(answers: dict, vault: dict[str, str]) -> str:
    """Rend livekit.yaml du SFU meet (modèle docs/examples/livekit/server.yaml amont).

    Le backend signe les jetons d'accès avec la MÊME clé API (LIVEKIT_API_KEY /
    LIVEKIT_API_SECRET du catalogue) ; la signalisation websocket passe par
    livekit.<domaine> (passerelle), les ports RTC restent internes au réseau.
    """
    if "meet_livekit_secret" not in vault:
        raise DeployError("secret manquant dans secrets.env : meet_livekit_secret")
    return (
        "# LaStarter — configuration LiveKit du SFU meet (rendue par lastarter-cli).\n"
        "# Modèle : docs/examples/livekit/server.yaml (amont suitenumerique/meet).\n"
        "port: 7880\n"
        "bind_addresses:\n"
        '  - "0.0.0.0"\n'
        "rtc:\n"
        "  tcp_port: 7881\n"
        "  udp_port: 7882\n"
        "  use_external_ip: false\n"
        "redis:\n"
        "  address: meet_redis:6379\n"
        "keys:\n"
        "  meet: " + vault["meet_livekit_secret"] + "\n"
    )


def render_discussions_homeserver(template: str, answers: dict, vault: dict[str, str]) -> str:
    """Rend homeserver.yaml des Discussions : OIDC vers le SSO + secrets du coffre."""
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    chat_origin = f"{scheme}://chat.{bare}" + (f":{port}" if port else "")

    def secret(match: re.Match) -> str:
        name = match.group(1)
        if name not in vault:
            raise DeployError(f"secret manquant dans secrets.env : {name}")
        return vault[name]

    rendered = template.replace("{{SSO_ORIGIN}}", _id_origin(domain))
    rendered = rendered.replace("{{CHAT_ORIGIN}}", chat_origin)
    rendered = rendered.replace("{{SERVER_NAME}}", bare)
    return REALM_SECRET_TOKEN.sub(secret, rendered)


def render_discussions_element_config(template: str, answers: dict, repo_root: Path | None = None) -> str:
    """Rend config.json Element Web : same-origin + marque + thème NATIF.

    Habillage amont Element Web (docs/theming.md) : la palette
    themes/<theme>.toml devient un thème custom Compound
    (setting_defaults.custom_themes[{name, is_dark, compound}]) référencé par
    default_theme "custom-<nom>". Les clés compound (--cpd-color-*) sont
    dérivées du MÊME gabarit que le CSS passerelle (identity/theme.css.tpl).
    """
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    chat_origin = f"{scheme}://chat.{bare}" + (f":{port}" if port else "")
    rendered = (
        template.replace("{{CHAT_ORIGIN}}", chat_origin)
        .replace("{{SERVER_NAME}}", bare)
        .replace("{{BRAND}}", answers.get("brand_name", "LaStarter"))
    )
    if repo_root is None:
        return rendered
    from .theme import build_custom_theme

    custom = build_custom_theme(repo_root, answers.get("theme", "element-light"))
    config = json.loads(rendered)
    config.setdefault("setting_defaults", {})["custom_themes"] = [custom]
    # Nommage amont : un thème custom est référencé « custom-<name> ».
    config["default_theme"] = f"custom-{custom['name']}"
    return json.dumps(config, ensure_ascii=False, indent=4) + "\n"


def _brand_logo_url(answers: dict) -> str:
    """URL du logo client : logo_url explicite, sinon branding servi par la
    passerelle (chemin relatif — chaque sous-domaine sert /__lastarter/)."""
    explicit = answers.get("logo_url", "")
    if explicit:
        return explicit
    logo_file = (answers.get("brand") or {}).get("logo_path", "")
    return f"/__lastarter/branding/{Path(logo_file).name}" if logo_file else ""


APP_EMOJI = {
    "docs": "📝",
    "drive": "📁",
    "meet": "🎥",
    "discussions": "💬",
}


def render_portal_config(bricks: list[Brick], answers: dict) -> str:
    """Génère portal-config.json : tuiles des briques actives + compte SSO."""
    domain = answers["domain"]
    apps = []
    for brick in bricks:
        if brick.core or not brick.compose.get("frontend_target"):
            continue
        if brick.compose.get("portal_visible", "true") == "false":
            continue  # backends (ex. synapse) : pas de tuile
        label = brick.compose.get("route_label", brick.name)
        # Nom d'affichage : apps.<brique>.label (init --app-name-*) sinon titre court.
        short = (
            ((answers.get("apps") or {}).get(brick.name) or {}).get("label")
            or brick.title.split("—")[0].strip()
        )
        apps.append(
            {
                "name": short,
                "description": brick.description,
                "url": app_origin(domain, label),
                "emoji": APP_EMOJI.get(brick.name, "◆"),
            }
        )
    config = {
        "brand": answers.get("brand_name", "LaStarter"),
        "tagline": "La suite collaborative de votre organisation.",
        "account_url": f"{_id_origin(domain)}/realms/lastarter/account",
        "apps": apps,
    }
    return json.dumps(config, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Provisionnement Keycloak (API admin, stdlib urllib)


def _http_json(url: str, method: str, token: str | None = None, body: dict | None = None, form: dict | None = None, ca_file: Path | None = None) -> tuple[int, str]:
    """Requête HTTP JSON ou form-encoded, retourne (status, texte).

    ca_file : CA à faire confiance (POC : CA locale de la passerelle TLS).
    """
    data = None
    headers = {"Accept": "application/json"}
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    ssl_context = None
    if url.startswith("https") and ca_file is not None:
        ssl_context = ssl.create_default_context(cafile=str(ca_file))
    try:
        with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def _ensure_realm_user(admin: str, token: str, username: str, first_name: str,
                       password: str, ca_file: Path | None) -> None:
    """Crée l'utilisateur realm si absent et (re)synchronise son mot de passe."""
    status, text = _http_json(
        f"{admin}/users?username={urllib.parse.quote(username)}&exact=true",
        method="GET", token=token, ca_file=ca_file,
    )
    if status != 200:
        raise DeployError(f"recherche utilisateur {username} impossible (HTTP {status})")
    found = json.loads(text)
    if found:
        user_id = found[0]["id"]
    else:
        status, _ = _http_json(
            f"{admin}/users",
            method="POST",
            token=token,
            body={
                "username": username,
                "email": f"{username}@lastarter.local",
                "firstName": first_name,
                "lastName": "LaStarter",
                "enabled": True,
                "emailVerified": True,
            },
            ca_file=ca_file,
        )
        if status not in (200, 201):
            raise DeployError(f"création utilisateur {username} impossible (HTTP {status})")
        status, text = _http_json(
            f"{admin}/users?username={urllib.parse.quote(username)}&exact=true",
            method="GET", token=token, ca_file=ca_file,
        )
        user_id = json.loads(text)[0]["id"]
    status, _ = _http_json(
        f"{admin}/users/{user_id}/reset-password",
        method="PUT",
        token=token,
        body={"type": "password", "value": password, "temporary": False},
        ca_file=ca_file,
    )
    if status not in (200, 204):
        raise DeployError(f"mot de passe {username} impossible (HTTP {status})")


def provision_realm(base_url: str, admin_user: str, admin_password: str,
                    demo_password: str, realm_admin_password: str = "",
                    ca_file: Path | None = None) -> None:
    """Applique les réglages realm (inscription, thème, sécurité) + utilisateurs.

    Idempotent via l'API admin — fait autorité après le premier import du realm.
    Deux comptes : `demo` (démo) et `admin` (admin DU realm — distinct de la
    console master Keycloak).
    """
    auth = _http_json(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        method="POST",
        form={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_password,
        },
        ca_file=ca_file,
    )
    if auth[0] != 200:
        raise DeployError(f"authentification admin Keycloak impossible (HTTP {auth[0]}) : {auth[1][:200]}")
    token = json.loads(auth[1])["access_token"]
    admin = f"{base_url}/admin/realms/lastarter"

    # Réglages du realm : SSO uniquement (inscription fermée), thème custom, sécurité brute-force.
    status, text = _http_json(f"{admin}", method="GET", token=token, ca_file=ca_file)
    if status != 200:
        raise DeployError(f"lecture realm impossible (HTTP {status})")
    realm = json.loads(text)
    realm.update(
        {
            # SSO uniquement : l'inscription locale reste fermée (le realm as-code
            # provisionne les comptes ; les apps provisionnent à la 1re connexion).
            "registrationAllowed": False,
            "resetPasswordAllowed": True,
            "bruteForceProtected": True,
            "rememberMe": True,
            "loginWithEmailAllowed": True,
            "loginTheme": "lastarter",
            # Sessions : 1h en standard, 7 jours avec « Se souvenir de moi ».
            "ssoSessionIdleTimeout": 3600,             # 1h
            "ssoSessionMaxLifespan": 43200,            # 12h
            "ssoSessionIdleTimeoutRememberMe": 604800, # 7j (remember me)
            "ssoSessionMaxLifespanRememberMe": 604800, # 7j (remember me)
        }
    )
    status, _ = _http_json(f"{admin}", method="PUT", token=token, body=realm, ca_file=ca_file)
    if status not in (200, 204):
        raise DeployError(f"mise à jour du realm impossible (HTTP {status})")

    _ensure_realm_user(admin, token, "demo", "Demo", demo_password, ca_file)
    if realm_admin_password:
        _ensure_realm_user(admin, token, "admin", "Admin", realm_admin_password, ca_file)


def provision_realm_clients(base_url: str, admin_user: str, admin_password: str, clients_json: str, ca_file: Path | None = None, ensure_scopes: list[dict] | None = None) -> list[str]:
    """Crée ou met à jour chaque client OIDC du realm `lastarter` via l'API admin.

    Idempotent : GET par clientId, POST si absent, PUT sinon (secret + redirects).
    `ensure_scopes` : définitions de client scopes (avec mappers) lues depuis le
    template du realm — créées si absentes (un realm importé avant leur ajout
    ne les possède pas : Keycloak rejette alors « Invalid scopes: openid profile
    email » au premier login OIDC).
    Retourne la liste des clientIds synchronisés.
    """
    status, text = _http_json(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        method="POST",
        form={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": admin_user,
            "password": admin_password,
        },
        ca_file=ca_file,
    )
    if status != 200:
        raise DeployError(f"authentification admin Keycloak impossible (HTTP {status}) : {text[:200]}")
    token = json.loads(text)["access_token"]

    admin = f"{base_url}/admin/realms/lastarter"

    # 0) Client scopes requis (avec mappers) : créés si absents.
    # NB : l'endpoint ignore le filtre ?name= (retourne tout) — tri côté client.
    if ensure_scopes:
        status, text = _http_json(
            f"{admin}/client-scopes",
            method="GET", token=token, ca_file=ca_file,
        )
        if status != 200:
            raise DeployError(f"lecture client scopes impossible (HTTP {status})")
        existing_scope_names = {s["name"] for s in json.loads(text)}
        for scope in ensure_scopes:
            name = scope["name"]
            if name in existing_scope_names:
                continue  # déjà présent : l'API fait autorité, pas d'écrasement
            payload = {k: v for k, v in scope.items() if k != "protocolMappers"}
            status, _ = _http_json(
                f"{admin}/client-scopes", method="POST", token=token, body=payload, ca_file=ca_file
            )
            if status not in (200, 201, 204):
                raise DeployError(f"création du client scope {name} impossible (HTTP {status})")
            status, text = _http_json(
                f"{admin}/client-scopes",
                method="GET", token=token, ca_file=ca_file,
            )
            scope_id = next(s["id"] for s in json.loads(text) if s["name"] == name)
            for mapper in scope.get("protocolMappers", []):
                status, _ = _http_json(
                    f"{admin}/client-scopes/{scope_id}/protocol-mappers/models",
                    method="POST", token=token, body=mapper, ca_file=ca_file,
                )
                if status not in (200, 201, 204):
                    raise DeployError(f"création du mapper {mapper['name']} impossible (HTTP {status})")
            print(f"client scope créé : {name}")

    done: list[str] = []
    # Résolution id par nom des client scopes (pour le linkage ci-dessous).
    status, text = _http_json(
        f"{admin}/client-scopes", method="GET", token=token, ca_file=ca_file,
    )
    scope_ids_by_name = {s["name"]: s["id"] for s in json.loads(text)}
    for client in json.loads(clients_json):
        client_id = client["clientId"]
        status, text = _http_json(
            f"{admin}/clients?clientId={urllib.parse.quote(client_id)}",
            method="GET", token=token, ca_file=ca_file,
        )
        if status != 200:
            raise DeployError(f"lecture clients Keycloak impossible (HTTP {status})")
        existing = json.loads(text)
        if existing:
            internal_id = existing[0]["id"]
            status, _ = _http_json(
                f"{admin}/clients/{internal_id}", method="PUT", token=token, body=client, ca_file=ca_file
            )
        else:
            status, _ = _http_json(f"{admin}/clients", method="POST", token=token, body=client, ca_file=ca_file)
            if status not in (200, 201, 204):
                raise DeployError(f"synchronisation du client {client_id} impossible (HTTP {status})")
            status, text = _http_json(
                f"{admin}/clients?clientId={urllib.parse.quote(client_id)}",
                method="GET", token=token, ca_file=ca_file,
            )
            internal_id = json.loads(text)[0]["id"]
        if status not in (200, 201, 204):
            raise DeployError(f"synchronisation du client {client_id} impossible (HTTP {status})")
        # Le PUT/POST client ne relie PAS les scopes : sans linkage dédié,
        # Keycloak rejette « Invalid scopes » au premier login OIDC.
        status, text = _http_json(
            f"{admin}/clients/{internal_id}/default-client-scopes",
            method="GET", token=token, ca_file=ca_file,
        )
        linked = {s["name"] for s in json.loads(text)} if status == 200 else set()
        for scope_name in client.get("defaultClientScopes", []):
            if scope_name in linked or scope_name not in scope_ids_by_name:
                continue
            status, _ = _http_json(
                f"{admin}/clients/{internal_id}/default-client-scopes/{scope_ids_by_name[scope_name]}",
                method="PUT", token=token, ca_file=ca_file,
            )
            if status not in (200, 201, 204):
                raise DeployError(f"linkage du scope {scope_name} sur {client_id} impossible (HTTP {status})")
        done.append(client_id)
    return done


# ---------------------------------------------------------------------------
# Exécution docker compose


def compose_base(runtime_env_file: Path, slug: str, compose_files: list[Path]) -> list[str]:
    file_flags = [part for path in compose_files for part in ("-f", str(path))]
    return [
        "docker", "compose",
        "--env-file", str(runtime_env_file),
        "-p", slug,
        *file_flags,
    ]


def run_deploy(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé (lancer depuis le dépôt LaStarter).", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    compose_dir = repo_root / "deploy" / "compose"

    slug = opts.client
    manifest, answers, vault, bricks = load_deployment(repo_root, slug)
    selected = list(manifest.get("bricks", {}).keys())
    validate_compose_targets(selected, bricks, compose_dir)

    if shutil.which("docker") is None:
        raise DeployError("docker introuvable — installer Docker Engine/Desktop")

    deployment_dir = repo_root / "deployments" / slug
    runtime_dir = deployment_dir / ".runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    # Rendu runtime : env par brique + compose.env (substitution ${} du compose).
    # Anti-dérive : chaque brique dont l'env rendu change voit son service
    # principal re-créé (bind mount/env_file changés ≠ recreation automatique).
    import hashlib

    compose_env: dict[str, str] = {}
    rendered_envs: dict[str, str] = {}
    to_recreate: dict[str, str] = {}  # service -> raison
    pending_markers: list[tuple[Path, str]] = []  # (marqueur, hash) écrits après succès
    # Définitions de client scopes lues dans le template du realm : le
    # provisioning les garantit sur les realms importés avant leur ajout.
    realm_scope_definitions: list[dict] = []
    realm_tpl_for_scopes = repo_root / "identity" / "realm-lastarter.json"
    if realm_tpl_for_scopes.is_file():
        try:
            tpl_text = realm_tpl_for_scopes.read_text(encoding="utf-8")
            tpl_text = tpl_text.replace("{{CLIENTS_JSON}}", "[]")
            # Les jetons {{SECRET:x}} vivent DANS des guillemets JSON : substitution nue.
            tpl_text = REALM_SECRET_TOKEN.sub("__secret__", tpl_text)
            realm_tpl_json = json.loads(tpl_text)
            realm_scope_definitions = realm_tpl_json.get("clientScopes", [])
        except json.JSONDecodeError:
            pass  # template non parsable : le provisioning live reste fonctionnel
    selected_bricks = [bricks[name] for name in selected]
    for name in selected:
        draft_path = deployment_dir / "env" / f"{name}.env"
        if not draft_path.is_file():
            raise DeployError(f"env draft manquant : {draft_path} (rejouer `lastarter init`)")
        # Les briques core (keycloak) se rendent sans label : leur identité
        # est id.<domaine>, pas <name>.<domaine>.
        label = None if bricks[name].core else bricks[name].compose.get("route_label", name)
        s3_port = str(bricks[name].compose.get("s3_public_port", "9000"))
        rendered = render_runtime_env(
            draft_path.read_text(encoding="utf-8"), answers, vault, label, s3_port
        )
        rendered_envs[name] = rendered
        (runtime_dir / f"{name}.env").write_text(rendered, encoding="utf-8")
        for line in rendered.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                compose_env[key.strip()] = value.strip()

        env_hash = hashlib.sha256(rendered.encode()).hexdigest()
        marker = runtime_dir / f".env-{name}.applied"
        previous = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
        principal = (
            bricks[name].compose.get("recreate_service")
            or bricks[name].compose.get("migrate_service")
            or ""
        )
        if previous != env_hash:
            # Le principal ET les services d'infra consomment le même env_file :
            # un env changé doit les recréer tous (env_file ≠ recreation auto).
            targets = [principal] + list(bricks[name].compose.get("infra_services", []))
            for target in filter(None, targets):
                to_recreate.setdefault(target, f"env {name} changé")
            pending_markers.append((marker, env_hash))

    # Realm Keycloak : clients OIDC générés depuis le catalogue (secret = celui
    # de chaque brique, extrait de l'env rendu).
    realm_template = repo_root / "identity" / "realm-lastarter.json"
    if "keycloak" in selected and realm_template.is_file():
        brick_clients = json.loads(build_realm_clients(selected_bricks, rendered_envs, answers))
        # Le placeholder est la VALEUR ENTIÈRE de "clients" : on fusionne les
        # clients de console de compte (account/account-console, requis pour
        # l'audience "account") avec ceux des briques.
        realm_rendered = render_realm(
            realm_template.read_text(encoding="utf-8"),
            answers,
            vault,
            json.dumps(ACCOUNT_CONSOLE_CLIENTS + brick_clients, indent=2, ensure_ascii=False),
        )
        realm_path = runtime_dir / "realm-lastarter.json"
        realm_path.write_text(realm_rendered, encoding="utf-8")
        compose_env["REALM_JSON_PATH"] = _portable(realm_path)

    # Meet (suitenumerique) : livekit.yaml du SFU rendu as-code dans
    # .runtime/meet/ (montage DOSSIER — les mounts fichier unique renvoient
    # 0 octet sous Docker Desktop Windows). Images/OIDC/secrets passent par
    # l'env rendu du catalogue (meet.env -> compose.env).
    if "meet" in selected:
        meet_cfg = runtime_dir / "meet"
        meet_cfg.mkdir(parents=True, exist_ok=True)
        (meet_cfg / "livekit.yaml").write_text(
            render_meet_livekit_config(answers, vault), encoding="utf-8"
        )
        compose_env["MEET_CONFIG_DIR"] = _portable(meet_cfg)

    # Drive : env backend Django + personnalisation JSON rendus as-code dans
    # .runtime/drive/ (dossier monté /config côté conteneur, ro).
    if "drive" in selected:
        drive_cfg = runtime_dir / "drive"
        drive_cfg.mkdir(parents=True, exist_ok=True)
        from .theme import build_drive_theme_customization, load_theme

        # Thème natif amont : light/dark suit la palette (theme.dark).
        drive_theme_dark = load_theme(
            repo_root, answers.get("theme", "element-light")
        ).get("theme", {}).get("dark", False)
        drive_backend_env = render_drive_backend_env(
            answers, vault, frontend_theme="dsfr-dark" if drive_theme_dark else "dsfr-light"
        )
        (drive_cfg / "backend.env").write_text(drive_backend_env, encoding="utf-8")
        drive_origin = app_origin(answers["domain"], "drive")
        # THEME_CUSTOMIZATION_FILE_PATH (docs/customization.md amont) : footer
        # {default, fr} aux clés FooterProps, logo servi par la passerelle.
        logo_url = _brand_logo_url(answers)
        if logo_url.startswith("/"):
            logo_url = f"{drive_origin}{logo_url}"
        customization = build_drive_theme_customization(
            answers.get("brand_name", "LaStarter"), compute_origin(answers["domain"]), logo_url
        )
        (drive_cfg / "theme-customization.json").write_text(
            json.dumps(customization, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        compose_env["DRIVE_ORIGIN"] = drive_origin

    # Discussions (Element Web + Synapse) : homeserver, signing key, config
    # element et log config rendus as-code — l'architecture same-origin validée.
    # Tout vit dans .runtime/discussions/ : montage par DOSSIER (les mounts
    # fichier unique renvoient 0 octet sous Docker Desktop Windows).
    if "discussions" in selected:
        discussions_cfg = runtime_dir / "discussions"
        discussions_cfg.mkdir(parents=True, exist_ok=True)
        homeserver_tpl = repo_root / "identity" / "homeserver-discussions.yaml"
        if not homeserver_tpl.is_file():
            raise DeployError("identity/homeserver-discussions.yaml manquant")
        hs_rendered = render_discussions_homeserver(
            homeserver_tpl.read_text(encoding="utf-8"), answers, vault
        )
        (discussions_cfg / "homeserver.yaml").write_text(hs_rendered, encoding="utf-8")
        hs_hash = hashlib.sha256(hs_rendered.encode()).hexdigest()
        applied = runtime_dir / ".discussions-homeserver.applied"
        if not applied.is_file() or applied.read_text(encoding="utf-8").strip() != hs_hash:
            to_recreate.setdefault("discussions_synapse", "homeserver.yaml discussions changé")
            pending_markers.append((applied, hs_hash))
        (discussions_cfg / "discussions.signing.key").write_text(
            f"ed25519 0 {vault['discussions_signing_key']}\n", encoding="utf-8"
        )
        log_tpl = repo_root / "identity" / "discussions-synapse-log.yaml"
        if log_tpl.is_file():
            shutil.copyfile(log_tpl, discussions_cfg / "discussions.log.config")
        element_tpl = repo_root / "identity" / "element-discussions-config.json"
        if not element_tpl.is_file():
            raise DeployError("identity/element-discussions-config.json manquant")
        element_rendered = render_discussions_element_config(
            element_tpl.read_text(encoding="utf-8"),
            answers,
            repo_root,
        )
        (discussions_cfg / "config.json").write_text(element_rendered, encoding="utf-8")
        # Anti-dérive : le conteneur COPIE config.json au boot — un changement
        # doit le recréer (bind mount ≠ recopie).
        el_hash = hashlib.sha256(element_rendered.encode()).hexdigest()
        el_applied = runtime_dir / ".discussions-element-config.applied"
        if not el_applied.is_file() or el_applied.read_text(encoding="utf-8").strip() != el_hash:
            to_recreate.setdefault("discussions_element_web", "config.json element changé")
            pending_markers.append((el_applied, el_hash))
        compose_env["DISCUSSIONS_CONFIG_DIR"] = _portable(discussions_cfg)
        # Résolution intra-conteneurs de la passerelle (POC .localhost).
        compose_env["LASTARTER_GATEWAY_SERVICE"] = "gateway"

    # Portail : copie des pages + config générée dans .runtime/portal/ (montage unique).
    portal_dir = repo_root / "portal"
    if portal_dir.is_dir():
        runtime_portal = runtime_dir / "portal"
        shutil.copytree(portal_dir, runtime_portal, dirs_exist_ok=True)
        config_text = render_portal_config(selected_bricks, answers)
        (runtime_portal / "portal-config.json").write_text(config_text, encoding="utf-8")
        # Cache navigateur : l'URL de la config porte l'empreinte de son contenu.
        # Un HTML identique doit pointer vers une URL JAMAIS mise en cache, sinon
        # une copie périmée (ancienne liste d'apps) reste affichée des heures.
        digest = hashlib.sha256(config_text.encode("utf-8")).hexdigest()[:10]
        index_path = runtime_portal / "index.html"
        index_text = index_path.read_text(encoding="utf-8")
        patched = index_text.replace(
            'fetch("/portal-config.json"',
            f'fetch("/portal-config.json?v={digest}"',
        )
        if patched == index_text:
            raise DeployError(
                "portal/index.html : appel fetch de portal-config.json introuvable "
                "(template changé ?) — l'anti-cache par empreinte ne peut pas s'appliquer"
            )
        index_path.write_text(patched, encoding="utf-8")
        compose_env["PORTAL_DIR"] = _portable(runtime_portal)

    # Thème LaStarter : rendu CSS (palette Compound + marque blanche) servi par
    # la passerelle sur /__lastarter/theme.css et injecté via sub_filter.
    theme_name = answers.get("theme", "element-light")
    from .theme import render_theme_css

    theme_css = render_theme_css(
        repo_root,
        theme_name,
        {
            "name": answers.get("brand_name", "LaStarter"),
            "color": answers.get("brand_color", "#0bc491"),
            "logo_url": _brand_logo_url(answers),
        },
    )
    theme_css_path = runtime_dir / "theme.css"
    old_theme = theme_css_path.read_text(encoding="utf-8") if theme_css_path.is_file() else None
    theme_css_path.write_text(theme_css, encoding="utf-8")
    compose_env["THEME_CSS_PATH"] = _portable(theme_css_path)
    if old_theme != theme_css:
        to_recreate.setdefault("gateway", "thème changé")
    print(f"Thème « {theme_name} » rendu ({len(theme_css)} octets)")

    # Branding (logo) : deployments/<slug>/branding/ -> .runtime/branding/, servi
    # par la passerelle sur /__lastarter/branding/ (tous les sous-domaines).
    # Défaut out-of-the-box : monogramme SVG depuis la palette (1re lettre + primaire).
    branding_runtime = runtime_dir / "branding"
    branding_src = deployment_dir / "branding"
    if branding_src.is_dir() and any(branding_src.iterdir()):
        shutil.copytree(branding_src, branding_runtime, dirs_exist_ok=True)
    else:
        branding_runtime.mkdir(parents=True, exist_ok=True)
        if not any(branding_runtime.iterdir()):
            from .theme import default_logo_svg, load_theme, primary_color

            (branding_runtime / "logo.svg").write_text(
                default_logo_svg(
                    answers.get("brand_name", "LaStarter"),
                    primary_color(load_theme(repo_root, theme_name)),
                ),
                encoding="utf-8",
            )
    compose_env["BRANDING_DIR"] = _portable(branding_runtime)
    print(f"Branding : {branding_runtime} (servi sur /__lastarter/branding/)")

    # Certificats TLS POC — SANs explicites pour chaque hôte déployé (apex nu +
    # id + apps + serveurs additionnels type livekit) ; non-wildcard requis.
    cert_san_names = cert_san_names_for(selected_bricks, answers["domain"])
    ca_path, crt_path, key_path, certs_changed = ensure_dev_certs(runtime_dir, cert_san_names)
    compose_env["CERTS_DIR"] = _portable(ca_path.parent)
    # Certificats changés → nginx recharge ses certs au boot : recreation gateway.
    if certs_changed:
        to_recreate.setdefault("gateway", "certificats TLS régénérés")
    # La CA est aussi copiée dans le dossier de config des Discussions :
    # Synapse la monte (magasin système) pour l'OIDC vers la passerelle TLS.
    cfg_dir = runtime_dir / "discussions"
    if cfg_dir.is_dir():
        # Synapse la monte (magasin système) pour l'OIDC vers la passerelle TLS.
        shutil.copyfile(ca_path, cfg_dir / "ca.crt")
    # Thème de login LaStarter (drop-in Keycloak).
    theme_dir = repo_root / "identity" / "keycloak-theme"
    if theme_dir.is_dir():
        compose_env["THEME_DIR"] = _portable(theme_dir)

    # Passerelle : conf nginx générée depuis les briques sélectionnées.
    # Un bind mount ne déclenche ni recreation ni reload : suivi de hash.
    edge_path = runtime_dir / "edge.conf"
    edge_conf = render_edge(selected_bricks, answers)
    edge_hash_path = runtime_dir / ".edge.applied"
    previous_edge_hash = (
        edge_hash_path.read_text(encoding="utf-8").strip() if edge_hash_path.is_file() else ""
    )
    edge_hash = hashlib.sha256(edge_conf.encode()).hexdigest()
    edge_path.write_text(edge_conf, encoding="utf-8")
    compose_env["EDGE_CONF_PATH"] = _portable(edge_path)
    if edge_hash != previous_edge_hash:
        to_recreate.setdefault("gateway", "conf passerelle changée")
        pending_markers.append((edge_hash_path, edge_hash))

    compose_env["LASTARTER_CLIENT"] = slug
    compose_env["LASTARTER_DOMAIN"] = answers["domain"]
    compose_env["LASTARTER_HOST"] = answers["domain"].split(":")[0]  # sans port (extra_hosts)
    compose_env["RUNTIME_DIR"] = _portable(runtime_dir)
    runtime_env_file = runtime_dir / "compose.env"
    runtime_env_file.write_text(
        "\n".join(f"{k}={v}" for k, v in sorted(compose_env.items())) + "\n",
        encoding="utf-8",
    )

    compose_files = [compose_dir / "base.yml"] + [compose_dir / f"{n}.yml" for n in selected]
    base = compose_base(runtime_env_file, slug, compose_files)

    if opts.down:
        result = run(base + ["down"])
        return result.returncode

    def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
        print(f"$ {' '.join(args)}")
        return subprocess.run(args, check=False, **kwargs)

    if opts.pull:
        result = run(base + ["pull"])
        if result.returncode != 0:
            raise DeployError("échec de docker compose pull")

    # 0. Anti-dérive : re-CRÉER (sans démarrer) les services dont un fichier
    # monté a changé (env_file, config, homeserver, edge, certificats) — AVANT
    # tout démarrage : un conteneur périmé ferait échouer le --wait de l'infra.
    if to_recreate:
        for service, reason in to_recreate.items():
            print(f"recreation de {service} ({reason})")
            result = run(base + ["create", "--force-recreate", service])
            if result.returncode != 0:
                raise DeployError(f"échec de la recreation de {service} ({reason})")
        for marker_path, marker_hash in pending_markers:
            marker_path.write_text(marker_hash + "\n", encoding="utf-8")

    # 1. Infrastructure (DB, cache, S3, keycloak) — healthchecks verts.
    #    Les tâches one-shot (ex. création de buckets S3) sont exclues du
    #    --wait : `docker compose up --wait` échoue sur un conteneur qui se
    #    termine, MÊME en exit 0. Elles sont exécutées via `run --rm` ensuite.
    infra: list[str] = []
    oneshots: list[str] = []
    for name in selected:
        infra.extend(bricks[name].compose.get("infra_services", []))
        oneshots.extend(bricks[name].compose.get("oneshot_services", []))
    oneshots = list(dict.fromkeys(oneshots))
    infra_wait = [s for s in dict.fromkeys(infra) if s not in oneshots]
    if infra_wait:
        result = run(base + ["up", "-d", "--wait", *infra_wait])
        if result.returncode != 0:
            raise DeployError("échec du démarrage de l'infrastructure (voir logs ci-dessus)")
    for service in oneshots:
        result = run(base + ["run", "--rm", service])
        if result.returncode != 0:
            raise DeployError(f"échec de la tâche one-shot {service}")

    # 2. Préparation one-off (ex. chown de volumes pour des images non-root).
    for name in selected:
        brick = bricks[name]
        prepare = brick.compose.get("prepare_command")
        service = brick.compose.get("prepare_service")
        if not (prepare and service):
            continue
        result = run(
            base + [
                "run", "--rm",
                "--user", brick.compose.get("prepare_user", "0:0"),
                "--entrypoint", "sh",
                service, "-c", prepare,
            ]
        )
        if result.returncode != 0:
            raise DeployError(f"préparation échouée pour {name}")

    # 3. Migrations (one-off, une par brique qui en déclare).
    for name in selected:
        brick = bricks[name]
        service = brick.compose.get("migrate_service")
        command = brick.compose.get("migrate_command")
        if not (service and command):
            continue
        result = run(base + ["run", "--rm", service, *shlex.split(command)])
        if result.returncode != 0:
            raise DeployError(f"migration échouée pour {name}")

    # 3. Ensemble de la pile (les services retirés du manifeste sont nettoyés).
    #    Liste explicite : exclure les one-shots (déjà exécutés) sans quoi le
    #    --wait échouerait sur leur exit ; `config --services` fait autorité.
    listed = subprocess.run(
        base + ["config", "--services"], capture_output=True, text=True, check=False
    )
    if listed.returncode != 0:
        raise DeployError("échec de docker compose config --services")
    wait_services = [s for s in listed.stdout.split() if s not in oneshots]
    result = run(base + ["up", "-d", "--wait", "--remove-orphans", *wait_services])
    if result.returncode != 0:
        raise DeployError("échec du démarrage (voir logs ci-dessus)")

    # 4. Clients OIDC : l'API admin fait autorité après le premier import du realm
    #    (--import-realm ne re-importe pas un realm existant).
    clients = [
        brick for brick in selected_bricks
        if not brick.core and brick.oidc.get("client_id")
    ]
    if clients:
        admin_user = "admin"
        for line in rendered_envs.get("keycloak", "").splitlines():
            if line.startswith("KEYCLOAK_ADMIN="):
                admin_user = line.partition("=")[2].strip()
        # Provisionnement via l'apex (host résolvable par l'OS : *.localhost ne
        # résout que côté navigateurs) — la passerelle route vers keycloak de
        # toute façon ; l'issuer OIDC reste https://id.<domaine> (KC_HOSTNAME).
        api_base = compute_origin(answers["domain"])
        provision_realm(
            base_url=api_base,
            admin_user=admin_user,
            admin_password=vault["kc_admin_password"],
            demo_password=vault.get("demo_user_password", ""),
            realm_admin_password=vault.get("realm_admin_password", ""),
            ca_file=ca_path,
        )
        provisioned = provision_realm_clients(
            base_url=api_base,
            admin_user=admin_user,
            admin_password=vault["kc_admin_password"],
            clients_json=build_realm_clients(selected_bricks, rendered_envs, answers),
            ca_file=ca_path,
            ensure_scopes=realm_scope_definitions,
        )
        print(f"Clients OIDC synchronisés via l'API admin : {', '.join(provisioned)}")

    print(f"\nDéploiement « {slug} » opérationnel (TLS, port 8443).")
    id_url = _id_origin(answers["domain"])
    print(f"  Portail       : {compute_origin(answers['domain'])} — entrée unique de la suite")
    print(f"  Identité (SSO) : {id_url} — SSO uniquement (inscription fermée), console {id_url}/admin")
    for brick in selected_bricks:
        if brick.core:
            continue
        label = brick.compose.get("route_label", brick.name)
        print(f"  {brick.name:<12} : {app_origin(answers['domain'], label)}")
    print(f"  Connexion démo : demo / secrets.env:demo_user_password")
    print(f"  Console admin  : admin / secrets.env:kc_admin_password")
    if (runtime_dir / "certs" / "ca.crt").is_file():
        print()
        print("  ⚠ POC TLS : faire confiance à la CA locale UNE fois (navigateurs) :")
        print(f"    certutil -user -addstore Root \"{(runtime_dir / 'certs' / 'ca.crt')}\"")
        print("    (ou accepter l'avertissement par sous-domaine dans le navigateur)")
    run(base + ["ps"])
    return 0


def run_ps(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé.", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    slug = opts.client
    load_deployment(repo_root, slug)  # gates
    runtime_env_file = repo_root / "deployments" / slug / ".runtime" / "compose.env"
    if not runtime_env_file.is_file():
        raise DeployError("aucun .runtime/compose.env — lancer `lastarter deploy` d'abord")
    manifest = tomllib.loads((repo_root / "deployments" / slug / "lastarter.toml").read_text(encoding="utf-8"))
    compose_files = [repo_root / "deploy" / "compose" / "base.yml"] + [
        repo_root / "deploy" / "compose" / f"{n}.yml" for n in manifest.get("bricks", {})
    ]
    result = subprocess.run(compose_base(runtime_env_file, slug, compose_files) + ["ps"], check=False)
    return result.returncode


def _portable(path: Path) -> str:
    """Chemin en slashes pour docker compose sur Windows comme sur POSIX."""
    return str(path.resolve()).replace("\\", "/")
