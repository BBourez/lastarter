"""`lastarter deploy` â€” assemblage et lancement docker-compose d'un dÃ©ploiement client.

Phase 2 : cible mono-VM (compose). Gates avant tout effet rÃ©seau :
docker prÃ©sent, dÃ©ploiement initialisÃ©, secrets prÃ©sents, chaque brique sÃ©lectionnÃ©e
possÃ¨de un fichier compose. Les secrets ne quittent jamais `deployments/<client>/.runtime/`
(gitignorÃ©) â€” les drafts committables ne contiennent que des jetons.
"""

from __future__ import annotations

import hashlib
import hmac
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
    """Erreur attendue â€” remontÃ©e propre en exit 1."""


# ---------------------------------------------------------------------------
# Contextes et rendus


def _scheme(domain: str) -> str:
    """Toujours https : le POC local aussi passe par la passerelle TLS
    (les apps La Suite forcent SECURE_SSL_REDIRECT en configuration prod,
    et livekit/wss + mÃ©dia exigent une origine sÃ©curisÃ©e)."""
    return "https"


def compute_origin(domain: str) -> str:
    """Origine du domaine apex (SSO)."""
    return f"{_scheme(domain)}://{domain}"


def app_origin(domain: str, label: str) -> str:
    """Origine d'une app : <label>.<domaine> (routage passerelle)."""
    return f"{_scheme(domain)}://{label}.{domain}"


def _id_origin(domain: str) -> str:
    """Origine du service d'identitÃ© : id.<domaine>."""
    return f"{_scheme(domain)}://id.{domain}"


def _context(answers: dict, label: str | None, s3_port: str = "9000") -> dict[str, str]:
    domain = answers["domain"]
    scheme = _scheme(domain)
    context = {
        "{domain}": domain,
        # SSO sur son propre hÃ´te dÃ©diÃ© : id.<domaine> (l'identitÃ© a sa marque).
        "{sso_origin}": f"{scheme}://id.{domain}",
        "{id_origin}": f"{scheme}://id.{domain}",
        "{ws}": "wss",
        "{brand_name}": answers.get("brand_name", "LaStarter"),
    }
    # S3 mÃ©dia : routÃ© par la passerelle (sous-domaine dÃ©diÃ© par brique).
    if label:
        context["{domain_s3}"] = f"{label}-media.{domain}"
    else:
        context["{domain_s3}"] = f"s3.{domain}"
    if label:
        context["{origin}"] = f"{scheme}://{label}.{domain}"
        context["{app_host}"] = f"{label}.{domain}"
        # ALLOWED_HOSTS Django : domaine SANS port (split_domain_port Ã  la validation).
        context["{app_bare}"] = f"{label}.{domain.split(':')[0]}"
    else:
        context["{origin}"] = context["{sso_origin}"]
        context["{app_host}"] = domain
        context["{app_bare}"] = domain.split(":")[0]
    # Les apps La Suite en mode Production/Feature forcent SECURE_SSL_REDIRECT :
    # la passerelle sert TLS partout (POC compris), on sert donc Feature.
    context["{django_configuration}"] = "Feature"
    # Domaine apex sans schÃ©ma ni port (server_name Matrix, HS_SERVER_NAME rtc).
    context["{domain_bare}"] = domain.split(":")[0]
    return context


def render_runtime_env(
    draft: str, answers: dict, vault: dict[str, str], label: str | None = None, s3_port: str = "9000"
) -> str:
    """Substitue les jetons d'un draft committable en env d'exÃ©cution (avec secrets)."""
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

    Django (drive, messagesâ€¦) : OIDC_RP_CLIENT_SECRET.
    Node.js (projects) : OIDC_CLIENT_SECRET.
    """
    for line in rendered_env.splitlines():
        if line.startswith("OIDC_RP_CLIENT_SECRET="):
            return line.partition("=")[2].strip()
    for line in rendered_env.splitlines():
        if line.startswith("OIDC_CLIENT_SECRET="):
            return line.partition("=")[2].strip()
    raise DeployError("OIDC_RP_CLIENT_SECRET / OIDC_CLIENT_SECRET absent de l'env rendu")


# Clients de console de compte injectÃ©s dans le realm importÃ© : requis pour
# l'audience "account" (scope + mapper du template) et l'API /account/*.
# Le secret OIDC de chaque brique reste gÃ©rÃ© par build_realm_clients.
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
    source unique, toujours synchronisÃ©e.
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
                "consentRequired": False,  # consentement implicite : apps de premiÃ¨re partie, pas d'Ã©cran Â« Continue to your account Â»
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
                # Scope Â« account Â» obligatoire : il porte le mapper
                # audience-account (sans lui, l'API console de compte rÃ©pond 401).
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


def ensure_dev_certs(runtime_dir: Path, san_names: list[str]) -> tuple[Path, Path, Path, bool]:
    """CA locale + certificat pour la passerelle TLS (POC).

    SANs explicites pour chaque hÃ´te dÃ©ployÃ© (CPython 3.12+ refuse les wildcards
    sur un domaine mono-label type *.localhost cÃ´tÃ© vÃ©rification stricte ; les
    navigateurs, eux, acceptent le wildcard). Retourne (ca, crt, key, changÃ©) â€”
    `changÃ©` = certificats (re)gÃ©nÃ©rÃ©s â†’ le serveur doit recharger.
    """
    certs_dir = runtime_dir / "certs"
    certs_dir.mkdir(parents=True, exist_ok=True)
    ca, crt, key = certs_dir / "ca.crt", certs_dir / "server.crt", certs_dir / "server.key"
    ca_key = certs_dir / "ca.key"
    # SANs explicites uniquement â€” JAMAIS de "*.localhost" : service_identity
    # (Twisted/Synapse) rejette le certificat ENTIER dÃ¨s qu'il voit un wildcard
    # mono-label (Â« too few host components for wildcard usage Â», RFC 6125),
    # mÃªme si des noms explicites sont prÃ©sents. LeÃ§on du POC chat.localhost.
    wanted_sans = sorted(set(san_names) | {"localhost"})
    marker = certs_dir / ".sans"
    current_sans = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    leaf_current = crt.is_file() and key.is_file() and current_sans == "\n".join(wanted_sans)
    if ca.is_file() and leaf_current:
        return ca, crt, key, False

    # CA crÃ©Ã©e UNE fois (confiance navigateur stable) ; seul le certificat
    # feuille est re-Ã©mis quand la liste d'hÃ´tes change.
    san_line = ",".join(f"DNS:{name}" for name in wanted_sans)
    make_ca = "" if ca.is_file() and ca_key.is_file() else (
        # Extensions X.509 obligatoires : Python/OpenSSL modernes refusent une
        # CA sans basicConstraints/keyUsage (Â« CA cert does not include key
        # usage extension Â»). LeÃ§on du POC.
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
        raise DeployError(f"Ã©chec de gÃ©nÃ©ration des certificats POC : {result.stderr[:300]}")
    marker.write_text("\n".join(wanted_sans) + "\n", encoding="utf-8")
    return ca, crt, key, True


VPN_ALLOW = "10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 100.64.0.0/10 127.0.0.1"


def _theme_nginx_block(include_auto_login: bool = True, auth_url: str = "/api/v1.0/authenticate/") -> list[str]:
    """Bloc nginx commun : sert le thÃ¨me CSS et l'injecte dans le HTML.

    include_auto_login=False pour le portail/login (pas de redirect auth).
    auth_url : URL de redirection selon la brique (Django vs Sails.js).
    """
    if include_auto_login:
        inject = f'<link rel="stylesheet" href="/__lastarter/theme.css"><script src="/__lastarter/auto-login.js" data-auth="{auth_url}"></script></head>'
    else:
        inject = '<link rel="stylesheet" href="/__lastarter/theme.css"></head>'
    return [
        "    # ThÃ¨me LaStarter : CSS (palette + marque blanche) injectÃ© dans le HTML.",
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
        # Fonts Inter (mÃªme source qu'Element Web : @fontsource/inter).
        "    location /__lastarter/fonts/ {",
        "        alias /var/www/lastarter-theme/fonts/;",
        '        add_header Cache-Control "public, max-age=31536000";',
        '        add_header Access-Control-Allow-Origin *;',
        "    }",
        f"    sub_filter '</head>' '{inject}';",
        # sub_filter doit aussi traiter les CSS (dÃ©faut : text/html seulement).
        "    sub_filter_types text/css application/javascript;",
        # Couleurs Cunningham hardcodÃ©es â†’ palette Element (focus, borders, text).
        "    sub_filter '#5e5cd0' '#0bc491';",
        "    sub_filter '#4844ad' '#009b78';",
        "    sub_filter '#4844AD' '#009b78';",
        "    sub_filter '#3e3b98' '#007a61';",
        "    sub_filter '#6969df' '#0bc491';",
        "    sub_filter '#534fc2' '#009b78';",
        "    sub_filter '#534FC2' '#009b78';",
        "    sub_filter '#8184fc' '#71d7ae';",
        "    sub_filter '#8184FC' '#71d7ae';",
        "    sub_filter '#7576ee' '#71d7ae';",
        "    sub_filter '#7576EE' '#71d7ae';",
        "    sub_filter '#5E5CD0' '#0bc491';",
        "    sub_filter '#69697d' '#656d77';",
        "    sub_filter_once off;",
        "",
    ]


def render_edge(bricks: list[Brick], answers: dict) -> str:
    """GÃ©nÃ¨re la conf nginx de la passerelle : apex â†’ SSO, <label>.<domain> â†’ app.

    ContrÃ´le d'accÃ¨s par brique : access = "vpn" restreint l'app aux rÃ©seaux
    privÃ©s (LAN + WireGuard/CGNAT + loopback) ; "public" (dÃ©faut) sans limite.
    L'identitÃ© (id.<domaine>) reste toujours accessible dÃ¨s qu'une app publique
    existe â€” le SSO doit joignable pour se connecter.
    """
    domain = answers["domain"]
    bare = domain.split(":")[0]  # server_name nginx : jamais de port
    lines: list[str] = [
        "# LaStarter â€” passerelle gÃ©nÃ©rÃ©e par lastarter-cli (ne pas Ã©diter Ã  la main).",
        "# Apex â†’ portail ; id.<domaine> â†’ Keycloak (auth) ; apps = sous-domaines.",
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
        "    # Le portail vit Ã  la racine de l'apex.",
        "    location / {",
        "        resolver 127.0.0.11 valid=10s ipv6=off;",
        "        set $backend_portal portal:80;",
        "        proxy_pass http://$backend_portal;",
        "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
        "        proxy_set_header X-Forwarded-Proto https;",
        "    }",
        "}",
        "",
    ]
    # Serveur d'identitÃ© dÃ©diÃ© : id.<domaine> â†’ Keycloak (toute l'auth).
    # PAS d'injection theme.css ici : la page de login a SON theme complet
    # (identity/keycloak-theme : deux colonnes, tokens Compound, Inter) â€”
    # le CSS d'app injectÃ© via sub_filter ajouterait des bordures/cartes
    # par-dessus et casserait le design.
    lines += [
        "# IdentitÃ© â€” id.<domaine> â†’ Keycloak",
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
        # Element Web / Element Call / Discussions : DÃ‰JÃ€ en Compound natif â€” NE PAS
        # injecter le thÃ¨me (il entrerait en conflit avec leurs styles propres),
        # ni l'auto-login (leur SSO est natif : Synapse OIDC / Matrix).
        if brick.name not in ("element-web", "element-call", "discussions"):
            # URL d'auth par brique : Django â†’ /api/v1.0/authenticate/, Sails â†’ /login.
            auth_url = "/login" if brick.name == "projects" else "/api/v1.0/authenticate/"
            lines += _theme_nginx_block(auth_url=auth_url)

        # Shell LaStarter : la racine sert le shell (sidebar Element Web + iframe).
        # L'app originale est servie sur /app/ avec sa sidebar masquÃ©e.
        if brick.name == "transfers":
            lines += [
                "    # Shell LaStarter : sidebar Element Web Ã  la racine.",
                "    location = / {",
                "        root /var/www/lastarter-shell;",
                "        try_files /transfers.html =404;",
                "    }",
                "",
                "    # App originale dans l'iframe (sidebar masquÃ©e).",
                "    location /app/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_shell {brick.compose['frontend_target']};",
                "        proxy_pass http://$backend_shell/;",
                '        proxy_set_header Accept-Encoding "";',
                "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",
                # Masquer la sidebar/header de l'app dans l'iframe.
                "        sub_filter '</head>' '<style>.c__left-panel,.c__header,nav[class*=\"sidebar\"],header[class*=\"topbar\"]{display:none!important}body{margin:0!important}</style></head>';",
                "        sub_filter_once on;",
                "        sub_filter_types text/html;",
                "    }",
                "",
            ]

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
                "        proxy_set_header X-Forwarded-Proto https;",  # Ã©vite la boucle 301 SECURE_SSL_REDIRECT
                "    }",
                "",
            ]
        if brick.compose.get("access") == "vpn":
            lines += [
                f"    # AccÃ¨s restreint : VPN/LAN uniquement ({brick.name}).",
                f"    allow {VPN_ALLOW.replace(' ', '; allow ')};",
                "    deny all;",
                "",
            ]
        lines += [
            "    # Service Worker : header requis derriÃ¨re un reverse proxy",
            "    # (l'enregistrement Ã©choue sans lui dans les navigateurs Chromium).",
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
        # Blocage passerelle pour TOUTES les apps â†’ redirect vers /.
        lines += [
            "    location = /login { return 302 https://$host/; }",
            "    location = /register { return 302 https://$host/; }",
            "    location = /signup { return 302 https://$host/; }",
            "",
        ]
        # Discussions (Element Web + Synapse) : same-origin validÃ© en POC â€”
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
        # Element Call standalone : proxy Matrix API sur le MEME domaine (same-origin,
        # Ã©vite les problÃ¨mes CORS/certificat cross-domain).
        if brick.name == "element-call":
            # Same-origin : proxy Matrix API sur meet.<domaine> avec le Host header
            # de chat.<domaine> (public_baseurl de notre Synapse) pour Ã©viter la
            # canonicalisation Synapse.
            chat_host = f"chat.{bare}" + (f":{domain.split(':')[1]}" if ":" in domain else "")
            lines += [
                "    # Matrix API proxy (same-origin, Host: chat = public_baseurl).",
                "    location /_matrix/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_matrix discussions_synapse:8008;",
                "        proxy_pass http://$backend_matrix;",
                f"        proxy_set_header Host {chat_host};",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
                "    # Synapse OIDC callback (same-origin SSO).",
                "    location /_synapse/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_syn discussions_synapse:8008;",
                "        proxy_pass http://$backend_syn;",
                f"        proxy_set_header Host {chat_host};",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
                "    # MatrixRTC Authorization (lk-jwt-service)",
                "    location /livekit/jwt/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_jwt lk-jwt-service:6080;",
                "        proxy_pass http://$backend_jwt;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                "    }",
                "",
                "    # LiveKit SFU websocket",
                "    location /livekit/sfu/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_sfu call_livekit:7880;",
                "        proxy_pass http://$backend_sfu;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_send_timeout 120;",
                "        proxy_read_timeout 120;",
                "        proxy_buffering off;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                "    }",
                "",
            ]
        # Element Call : routes MatrixRTC sur le domaine matrix (docs self_hosting).
        if brick.name == "synapse":
            lines += [
                "    # Element Call : MatrixRTC Authorization + SFU websocket",
                "    # CORS requis : element-call (meet.<domaine>) appelle matrix.<domaine>.",
                "    location /livekit/jwt/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_jwt lk-jwt-service:6080;",
                "        proxy_pass http://$backend_jwt;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                # CORS : element-call est sur meet.<domaine> â‰  matrix.<domaine>.
                '        add_header Access-Control-Allow-Origin * always;',
                '        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS, PUT, DELETE" always;',
                '        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;',
                "        if ($request_method = OPTIONS) { return 204; }",
                "    }",
                "",
                "    location /livekit/sfu/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                "        set $backend_sfu call_livekit:7880;",
                "        proxy_pass http://$backend_sfu;",
                "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "        proxy_send_timeout 120;",
                "        proxy_read_timeout 120;",
                "        proxy_buffering off;",
                "        proxy_http_version 1.1;",
                "        proxy_set_header Upgrade $http_upgrade;",
                '        proxy_set_header Connection "upgrade";',
                "    }",
                "",
            ]
        lines += [
            "    # Element Call SPA index (chargÃ© par le wrapper aprÃ¨s auth)",
            "    location = /element-call-index.html {",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            "        set $backend_ec element_call:8080;",
            "        proxy_pass http://$backend_ec/index.html;",
            "        proxy_set_header Accept-Encoding \"\";",  # sub_filter : HTML non gzip
        "        proxy_set_header Host $http_host;",
            "    }",
            "",
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
                f"# {brick.title} â€” {extra.get('label', '')}",
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
        raise DeployError(f"dÃ©ploiement inconnu : {manifest_path} (lancer `lastarter init`)")
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
                f"la brique Â« {name} Â» n'a pas de cible compose (phase future) â€” "
                "retirer du dÃ©ploiement ou utiliser `lastarter init`"
            )


def render_lk_registration(answers: dict, vault: dict[str, str]) -> str:
    """Rend le registration YAML de l'appservice lk-jwt-service (MSC4512)."""
    bare = answers["domain"].split(":")[0]
    return (
        "# LaStarter â€” appservice lk-jwt-service (rendu par lastarter-cli).\n"
        'id: "lk-jwt-service"\n'
        f'as_token: "{vault["lk_as_token"]}"\n'
        f'hs_token: "{vault["lk_hs_token"]}"\n'
        'sender_localpart: "_lk_jwt_service"\n'
        "namespaces:\n"
        "  users:\n"
        "    - exclusive: false\n"
        f"      regex: \"@.*:{re.escape(bare)}\"  # tous les utilisateurs locaux\n"
        "# Synapse pousse les Ã©vÃ¨nements et proxifie rtc/livekit (MSC4512) ici :\n"
        'url: "http://lk-jwt-service:6080"\n'
        "io.element.msc4502.scopes:\n"
        '  ["urn:matrix:client:io.element.msc4502:rooms:is_joined"]\n'
        "io.element.msc4512.proxy_prefix: \"rtc/livekit\"\n"
        "io.element.msc4512.proxy_url: \"http://lk-jwt-service:6080\"\n"
    )


def render_synapse_homeserver(template: str, answers: dict, vault: dict[str, str]) -> str:
    """Rend homeserver.yaml : endpoints OIDC scindÃ©s + secrets du coffre."""
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    matrix_origin = f"{scheme}://matrix.{bare}" + (f":{port}" if port else "")

    def secret(match: re.Match) -> str:
        name = match.group(1)
        if name not in vault:
            raise DeployError(f"secret manquant dans secrets.env : {name}")
        return vault[name]

    rendered = template.replace("{{SSO_ORIGIN}}", _id_origin(domain))  # cohÃ©rence cookies : id.<domaine> partout
    rendered = rendered.replace("{{MATRIX_ORIGIN}}", matrix_origin)
    # Element Call vit sur meet.<domaine> : le JWT SFU doit Ãªtre mÃªme-origine.
    meet_origin = f"{scheme}://meet.{bare}" + (f":{port}" if port else "")
    rendered = rendered.replace("{{MEET_ORIGIN}}", meet_origin)
    rendered = rendered.replace("{{SERVER_NAME}}", bare)
    return REALM_SECRET_TOKEN.sub(secret, rendered)


def render_element_config(template: str, answers: dict, brick: Brick) -> str:
    """Rend config.json element-web : marque + homeserver + thÃ¨me personnalisÃ©."""
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    matrix_origin = f"{scheme}://matrix.{bare}" + (f":{port}" if port else "")
    chat_origin = f"{scheme}://chat.{bare}" + (f":{port}" if port else "")
    theme = dict(brick.branding_custom_theme)
    theme_name = theme.pop("name", "LaStarter")

    rendered = template.replace("{{BRAND}}", answers.get("brand_name", "LaStarter"))
    rendered = rendered.replace("{{THEME_NAME}}", theme_name)
    rendered = rendered.replace("{{MATRIX_ORIGIN}}", matrix_origin)
    rendered = rendered.replace("{{CHAT_ORIGIN}}", chat_origin)
    # Appels de salon (Element Call) : SPA + widget sur call.<domaine>.
    call_origin = f"{scheme}://call.{bare}" + (f":{port}" if port else "")
    rendered = rendered.replace("{{CALL_ORIGIN}}", call_origin)
    rendered = rendered.replace("{{SERVER_NAME}}", bare)
    rendered = rendered.replace("{{CUSTOM_THEME}}", json.dumps(theme))
    return rendered


def render_element_call_config(template: str, answers: dict) -> str:
    """Rend config.json Element Call (mode standalone) : homeserver + LiveKit.

    Same-origin sur meet.<domaine> : l'API Matrix passe par la passerelle
    (Host: chat = public_baseurl du Synapse des Discussions).
    """
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    meet_origin = f"{_scheme(domain)}://meet.{bare}" + (f":{port}" if port else "")
    chat_origin = f"{_scheme(domain)}://chat.{bare}" + (f":{port}" if port else "")
    return (
        template.replace("{{MEET_ORIGIN}}", meet_origin)
        .replace("{{CHAT_ORIGIN}}", chat_origin)
        .replace("{{SERVER_NAME}}", bare)
        .replace("{{BRAND}}", answers.get("brand_name", "LaStarter"))
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


def render_discussions_element_config(template: str, answers: dict, meet_enabled: bool = False) -> str:
    """Rend config.json Element Web des Discussions : same-origin + marque.

    meet_enabled : ajoute le widget Element Call (pattern ess-helm use_exclusively).
    """
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    chat_origin = f"{scheme}://chat.{bare}" + (f":{port}" if port else "")
    meet_origin = f"{scheme}://meet.{bare}" + (f":{port}" if port else "")
    rendered = (
        template.replace("{{CHAT_ORIGIN}}", chat_origin)
        .replace("{{MEET_ORIGIN}}", meet_origin)
        .replace("{{SERVER_NAME}}", bare)
        .replace("{{BRAND}}", answers.get("brand_name", "LaStarter"))
    )
    if not meet_enabled:
        # Sans Meet : retirer les blocs features/element_call du template.
        parsed = json.loads(rendered)
        parsed.pop("features", None)
        parsed.pop("element_call", None)
        rendered = json.dumps(parsed, indent=4)
    return rendered


APP_EMOJI = {
    "drive": "ðŸ“",
    "meet": "ðŸŽ¥",
    "discussions": "ðŸ’¬",
    "element-web": "ðŸ’¬",
    "element-call": "ðŸ“ž",
    "transfers": "ðŸ“¨",
    "messages": "âœ‰ï¸",
    "projects": "ðŸ“Š",
}


def render_portal_config(bricks: list[Brick], answers: dict) -> str:
    """GÃ©nÃ¨re portal-config.json : tuiles des briques actives + compte SSO."""
    domain = answers["domain"]
    apps = []
    for brick in bricks:
        if brick.core or not brick.compose.get("frontend_target"):
            continue
        if brick.compose.get("portal_visible", "true") == "false":
            continue  # backends (ex. synapse) : pas de tuile
        label = brick.compose.get("route_label", brick.name)
        short = brick.title.split("â€”")[0].strip()
        apps.append(
            {
                "name": short,
                "description": brick.description,
                "url": app_origin(domain, label),
                "emoji": APP_EMOJI.get(brick.name, "â—†"),
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
    """RequÃªte HTTP JSON ou form-encoded, retourne (status, texte).

    ca_file : CA Ã  faire confiance (POC : CA locale de la passerelle TLS).
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
    """CrÃ©e l'utilisateur realm si absent et (re)synchronise son mot de passe."""
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
            raise DeployError(f"crÃ©ation utilisateur {username} impossible (HTTP {status})")
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
    """Applique les rÃ©glages realm (inscription, thÃ¨me, sÃ©curitÃ©) + utilisateurs.

    Idempotent via l'API admin â€” fait autoritÃ© aprÃ¨s le premier import du realm.
    Deux comptes : `demo` (dÃ©mo) et `admin` (admin DU realm â€” distinct de la
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

    # RÃ©glages du realm : inscription libre, thÃ¨me custom, sÃ©curitÃ© brute-force.
    status, text = _http_json(f"{admin}", method="GET", token=token, ca_file=ca_file)
    if status != 200:
        raise DeployError(f"lecture realm impossible (HTTP {status})")
    realm = json.loads(text)
    realm.update(
        {
            # SSO uniquement : l'inscription locale reste fermÃ©e (le realm as-code
            # provisionne les comptes ; les apps provisionnent Ã  la 1re connexion).
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
        raise DeployError(f"mise Ã  jour du realm impossible (HTTP {status})")

    _ensure_realm_user(admin, token, "demo", "Demo", demo_password, ca_file)
    if realm_admin_password:
        _ensure_realm_user(admin, token, "admin", "Admin", realm_admin_password, ca_file)


def provision_matrix_demo(base_url: str, server_name: str, shared_secret: str, username: str, password: str, ca_file: Path | None = None) -> bool:
    """Assure que le compte Matrix `demo` connaisse le mot de passe du coffre SSO.

    Element Call standalone n'a pas de SSO natif : son login password doit
    marcher. Le compte existe aprÃ¨s le 1er login SSO (provisionnÃ© par Synapse)
    sans password local â€” on le (re)pose via l'API admin, en bootstrappant un
    compte d'outillage `_lastaster_cli` (admin, secret du coffre).
    Retourne True si le login password de `demo` est opÃ©rationnel.
    """
    import socket as _socket

    # Les sous-domaines *.localhost ne rÃ©solvent que cÃ´tÃ© navigateurs : on
    # les Ã©pingle vers la boucle locale le temps de ces appels (la passerelle
    # publie 8443 sur l'hÃ´te).
    chat_host = urllib.parse.urlparse(base_url).hostname or ""
    _orig_getaddrinfo = _socket.getaddrinfo

    def _resolve(host, port, *args, **kwargs):
        if host == chat_host and host.endswith(".localhost"):
            return _orig_getaddrinfo("127.0.0.1", port, *args, **kwargs)
        return _orig_getaddrinfo(host, port, *args, **kwargs)

    _socket.getaddrinfo = _resolve
    try:
        return _provision_matrix_demo_inner(
            base_url, server_name, shared_secret, username, password, ca_file
        )
    finally:
        _socket.getaddrinfo = _orig_getaddrinfo


def _provision_matrix_demo_inner(base_url: str, server_name: str, shared_secret: str, username: str, password: str, ca_file: Path | None = None) -> bool:
    """Assure que le compte Matrix `demo` connaisse le mot de passe du coffre SSO.

    Element Call standalone n'a pas de SSO natif : son login password doit
    marcher. Le compte existe aprÃ¨s le 1er login SSO (provisionnÃ© par Synapse)
    sans password local â€” on le (re)pose via l'API admin, en bootstrappant un
    compte d'outillage `lastarter-cli-tool` (admin, secret du coffre).
    Retourne True si le login password de `demo` est opÃ©rationnel.
    """
    def _nonce() -> tuple[str, str] | None:
        status, text = _http_json(f"{base_url}/_synapse/admin/v1/register", method="GET", ca_file=ca_file)
        if status != 200:
            return None
        return json.loads(text)["nonce"], text

    def _register(user: str, pwd: str, admin: bool) -> int:
        got = _nonce()
        if not got:
            return -1
        nonce = got[0]
        mac = hmac.new(shared_secret.encode(), digestmod=hashlib.sha1)
        mac.update(nonce.encode()); mac.update(b"\x00")
        mac.update(user.encode()); mac.update(b"\x00")
        mac.update(pwd.encode()); mac.update(b"\x00")
        mac.update(b"admin" if admin else b"notadmin")
        status, text = _http_json(
            f"{base_url}/_synapse/admin/v1/register",
            method="POST",
            body={"nonce": nonce, "username": user, "password": pwd,
                  "admin": admin, "mac": mac.hexdigest()},
            ca_file=ca_file,
        )
        return status

    # 1) Compte demo direct (premier dÃ©ploiement, avant tout SSO).
    status = _register(username, password, admin=False)
    if status == 200:
        print(f"  matrix demo : compte @{username} crÃ©Ã© (password = coffre SSO)")
        return True

    # 2) DÃ©jÃ  prÃ©sent : reset via un compte d'outillage admin bootstrappÃ©.
    tool_user, tool_pwd = "lastarter-cli-tool", shared_secret
    status = _register(tool_user, tool_pwd, admin=True)
    if status not in (200, 400, 403):
        print(f"  matrix demo : bootstrap outillage impossible (HTTP {status})")
        return False
    status, text = _http_json(
        f"{base_url}/_matrix/client/v3/login",
        method="POST",
        body={"type": "m.login.password", "identifier": {"type": "m.id.user", "user": tool_user},
              "password": tool_pwd},
        ca_file=ca_file,
    )
    if status != 200:
        print(f"  matrix demo : login outillage impossible (HTTP {status}) {text[:120]}")
        return False
    admin_token = json.loads(text)["access_token"]
    status, text = _http_json(
        f"{base_url}/_synapse/admin/v1/reset_password/@{username}:{server_name}",
        method="POST", token=admin_token,
        body={"new_password": password, "logout_devices": False},
        ca_file=ca_file,
    )
    if status == 200:
        print(f"  matrix demo : password posÃ© (reset via outillage)")
        return True
    print(f"  matrix demo : reset password impossible (HTTP {status}) {text[:120]}")
    return False


def provision_realm_clients(base_url: str, admin_user: str, admin_password: str, clients_json: str, ca_file: Path | None = None, ensure_scopes: list[dict] | None = None) -> list[str]:
    """CrÃ©e ou met Ã  jour chaque client OIDC du realm `lastarter` via l'API admin.

    Idempotent : GET par clientId, POST si absent, PUT sinon (secret + redirects).
    `ensure_scopes` : dÃ©finitions de client scopes (avec mappers) lues depuis le
    template du realm â€” crÃ©Ã©es si absentes (un realm importÃ© avant leur ajout
    ne les possÃ¨de pas : Keycloak rejette alors Â« Invalid scopes: openid profile
    email Â» au premier login OIDC).
    Retourne la liste des clientIds synchronisÃ©s.
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

    # 0) Client scopes requis (avec mappers) : crÃ©Ã©s si absents.
    # NB : l'endpoint ignore le filtre ?name= (retourne tout) â€” tri cÃ´tÃ© client.
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
                continue  # dÃ©jÃ  prÃ©sent : l'API fait autoritÃ©, pas d'Ã©crasement
            payload = {k: v for k, v in scope.items() if k != "protocolMappers"}
            status, _ = _http_json(
                f"{admin}/client-scopes", method="POST", token=token, body=payload, ca_file=ca_file
            )
            if status not in (200, 201, 204):
                raise DeployError(f"crÃ©ation du client scope {name} impossible (HTTP {status})")
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
                    raise DeployError(f"crÃ©ation du mapper {mapper['name']} impossible (HTTP {status})")
            print(f"client scope crÃ©Ã© : {name}")

    done: list[str] = []
    # RÃ©solution id par nom des client scopes (pour le linkage ci-dessous).
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
        # Le PUT/POST client ne relie PAS les scopes : sans linkage dÃ©diÃ©,
        # Keycloak rejette Â« Invalid scopes Â» au premier login OIDC.
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
# ExÃ©cution docker compose


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
        print("Aucun dossier catalogue/ trouvÃ© (lancer depuis le dÃ©pÃ´t LaStarter).", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    compose_dir = repo_root / "deploy" / "compose"

    slug = opts.client
    manifest, answers, vault, bricks = load_deployment(repo_root, slug)
    selected = list(manifest.get("bricks", {}).keys())
    validate_compose_targets(selected, bricks, compose_dir)

    if shutil.which("docker") is None:
        raise DeployError("docker introuvable â€” installer Docker Engine/Desktop")

    deployment_dir = repo_root / "deployments" / slug
    runtime_dir = deployment_dir / ".runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    # Rendu runtime : env par brique + compose.env (substitution ${} du compose).
    # Anti-dÃ©rive : chaque brique dont l'env rendu change voit son service
    # principal re-crÃ©Ã© (bind mount/env_file changÃ©s â‰  recreation automatique).
    import hashlib

    compose_env: dict[str, str] = {}
    rendered_envs: dict[str, str] = {}
    to_recreate: dict[str, str] = {}  # service -> raison
    pending_markers: list[tuple[Path, str]] = []  # (marqueur, hash) Ã©crits aprÃ¨s succÃ¨s
    # DÃ©finitions de client scopes lues dans le template du realm : le
    # provisioning les garantit sur les realms importÃ©s avant leur ajout.
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
        # Les briques core (keycloak) se rendent sans label : leur identitÃ©
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
            # Le principal ET les services d'infra consomment le mÃªme env_file :
            # un env changÃ© doit les recrÃ©er tous (env_file â‰  recreation auto).
            targets = [principal] + list(bricks[name].compose.get("infra_services", []))
            for target in filter(None, targets):
                to_recreate.setdefault(target, f"env {name} changÃ©")
            pending_markers.append((marker, env_hash))

    # Realm Keycloak : clients OIDC gÃ©nÃ©rÃ©s depuis le catalogue (secret = celui
    # de chaque brique, extrait de l'env rendu).
    realm_template = repo_root / "identity" / "realm-lastarter.json"
    if "keycloak" in selected and realm_template.is_file():
        brick_clients = json.loads(build_realm_clients(selected_bricks, rendered_envs, answers))
        # Le placeholder est la VALEUR ENTIÃˆRE de "clients" : on fusionne les
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

    # Synapse : homeserver.yaml + clÃ© de signature rendus as-code.
    synapse_needs_recreate = False
    homeserver_hash = ""
    if "synapse" in selected:
        homeserver_template = repo_root / "identity" / "homeserver-synapse.yaml"
        if not homeserver_template.is_file():
            raise DeployError("identity/homeserver-synapse.yaml manquant")
        homeserver_rendered = render_synapse_homeserver(
            homeserver_template.read_text(encoding="utf-8"), answers, vault
        )
        homeserver_path = runtime_dir / "synapse-homeserver.yaml"
        homeserver_path.write_text(homeserver_rendered, encoding="utf-8")
        # Comme les envs : un bind mount changÃ© ne redÃ©marre pas synapse.
        homeserver_hash = hashlib.sha256(homeserver_rendered.encode()).hexdigest()
        applied = runtime_dir / ".synapse-homeserver.applied"
        if not applied.is_file() or applied.read_text(encoding="utf-8").strip() != homeserver_hash:
            to_recreate.setdefault("synapse_synapse", "homeserver.yaml changÃ©")
            pending_markers.append((applied, homeserver_hash))
        signing_path = runtime_dir / "synapse-signing.key"
        signing_path.write_text(
            f"ed25519 0 {vault['synapse_signing_key']}\n", encoding="utf-8"
        )
        compose_env["SYNAPSE_HOMESERVER_PATH"] = _portable(homeserver_path)
        compose_env["SYNAPSE_SIGNING_KEY_PATH"] = _portable(signing_path)

        # Registration appservice rtc/livekit (montÃ© en permanence dans synapse).
        registration_path = runtime_dir / "lk-jwt-service.yaml"
        registration_path.write_text(render_lk_registration(answers, vault), encoding="utf-8")
        compose_env["LK_REGISTRATION_PATH"] = _portable(registration_path)

    # element-web : config.json (marque + homeserver + thÃ¨me) rendu as-code.
    if "element-web" in selected:
        element_template = repo_root / "identity" / "element-config.json"
        if not element_template.is_file():
            raise DeployError("identity/element-config.json manquant")
        element_path = runtime_dir / "element-config.json"
        element_path.write_text(
            render_element_config(
                element_template.read_text(encoding="utf-8"), answers, bricks["element-web"]
            ),
            encoding="utf-8",
        )
        compose_env["ELEMENT_CONFIG_PATH"] = _portable(element_path)

    # Meet (Element Call) : config.json + livekit.yaml rendus dans
    # .runtime/meet/ (montage DOSSIER â€” les fichier uniques renvoient 0 octet
    # sous Docker Desktop Windows).
    if "element-call" in selected:
        meet_cfg = runtime_dir / "meet"
        meet_cfg.mkdir(parents=True, exist_ok=True)
        ec_template = repo_root / "identity" / "element-call-config.json"
        if not ec_template.is_file():
            raise DeployError("identity/element-call-config.json manquant")
        (meet_cfg / "config.json").write_text(
            render_element_call_config(ec_template.read_text(encoding="utf-8"), answers),
            encoding="utf-8",
        )
        livekit_tpl = repo_root / "deploy" / "compose" / "files" / "livekit-call.yaml"
        if livekit_tpl.is_file():
            shutil.copyfile(livekit_tpl, meet_cfg / "livekit-call.yaml")
        compose_env["MEET_CONFIG_DIR"] = _portable(meet_cfg)
        compose_env["MEET_ORIGIN"] = app_origin(answers["domain"], "meet")
        compose_env["MEET_ISSUER"] = f"{_id_origin(answers['domain'])}/realms/lastarter"

    # Discussions (Element Web + Synapse) : homeserver, signing key, config
    # element et log config rendus as-code â€” l'architecture same-origin validÃ©e.
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
        # Meet sÃ©lectionnÃ© : activer MatrixRTC (MSC3266/4143/4222) et monter
        # l'appservice lk-jwt-service (MSC4512) dans le homeserver.
        if "element-call" in selected:
            hs_rendered += (
                "\n# ==================== MATRIXRTC (Meet sÃ©lectionnÃ©) ====================\n"
                "# MSC3266 : member updates ; MSC4143 : sessions RTC ; MSC4222 : expiry.\n"
                "experimental_features:\n"
                "  msc3266_enabled: true\n"
                "  msc4143_enabled: true\n"
                "  msc4222_enabled: true\n"
                "# Appservice lk-jwt-service (jetons LiveKit, MSC4512).\n"
                "app_service_config_files:\n"
                "  - /config/lk-jwt-service.yaml\n"
                "# Guests : Element Call standalone (derriere le gate SSO) cree\n"
                "# une session invite SANS mot de passe — l'auth reste le gate.\n"
                "allow_guest_access: true\n"
            )
            (discussions_cfg / "lk-jwt-service.yaml").write_text(
                render_lk_registration(answers, vault), encoding="utf-8"
            )
        (discussions_cfg / "homeserver.yaml").write_text(hs_rendered, encoding="utf-8")
        hs_hash = hashlib.sha256(hs_rendered.encode()).hexdigest()
        applied = runtime_dir / ".discussions-homeserver.applied"
        if not applied.is_file() or applied.read_text(encoding="utf-8").strip() != hs_hash:
            to_recreate.setdefault("discussions_synapse", "homeserver.yaml discussions changÃ©")
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
            meet_enabled="element-call" in selected,
        )
        (discussions_cfg / "config.json").write_text(element_rendered, encoding="utf-8")
        # Anti-dÃ©rive : le conteneur COPIE config.json au boot â€” un changement
        # doit le recrÃ©er (bind mount â‰  recopie).
        el_hash = hashlib.sha256(element_rendered.encode()).hexdigest()
        el_applied = runtime_dir / ".discussions-element-config.applied"
        if not el_applied.is_file() or el_applied.read_text(encoding="utf-8").strip() != el_hash:
            to_recreate.setdefault("discussions_element_web", "config.json element changÃ©")
            pending_markers.append((el_applied, el_hash))
        compose_env["DISCUSSIONS_CONFIG_DIR"] = _portable(discussions_cfg)
        # RÃ©solution intra-conteneurs de la passerelle (POC .localhost).
        compose_env["LASTARTER_GATEWAY_SERVICE"] = "gateway"

    # Portail : copie des pages + config gÃ©nÃ©rÃ©e dans .runtime/portal/ (montage unique).
    portal_dir = repo_root / "portal"
    if portal_dir.is_dir():
        runtime_portal = runtime_dir / "portal"
        shutil.copytree(portal_dir, runtime_portal, dirs_exist_ok=True)
        (runtime_portal / "portal-config.json").write_text(
            render_portal_config(selected_bricks, answers), encoding="utf-8"
        )
        compose_env["PORTAL_DIR"] = _portable(runtime_portal)

    # ThÃ¨me LaStarter : rendu CSS (palette Compound + marque blanche) servi par
    # la passerelle sur /__lastarter/theme.css et injectÃ© via sub_filter.
    theme_name = answers.get("theme", "element-light")
    from .theme import render_theme_css

    theme_css = render_theme_css(
        repo_root,
        theme_name,
        {
            "name": answers.get("brand_name", "LaStarter"),
            "color": answers.get("brand_color", "#0bc491"),
            "logo_url": answers.get("logo_url", ""),
        },
    )
    theme_css_path = runtime_dir / "theme.css"
    old_theme = theme_css_path.read_text(encoding="utf-8") if theme_css_path.is_file() else None
    theme_css_path.write_text(theme_css, encoding="utf-8")
    compose_env["THEME_CSS_PATH"] = _portable(theme_css_path)
    if old_theme != theme_css:
        to_recreate.setdefault("gateway", "thÃ¨me changÃ©")
    print(f"ThÃ¨me Â« {theme_name} Â» rendu ({len(theme_css)} octets)")

    # Certificats TLS POC â€” SANs explicites pour chaque hÃ´te dÃ©ployÃ© (id + apps
    # + serveurs additionnels type media/livekit) ; CPython exige du non-wildcard.
    cert_bare = answers["domain"].split(":")[0]
    cert_san_names = [f"id.{cert_bare}"]
    for brick in selected_bricks:
        if brick.core:
            continue
        cert_san_names.append(f"{brick.compose.get('route_label', brick.name)}.{cert_bare}")
        for extra in brick.compose.get("extra_servers", []):
            cert_san_names.append(f"{extra['label']}.{cert_bare}")
    ca_path, crt_path, key_path, certs_changed = ensure_dev_certs(runtime_dir, cert_san_names)
    compose_env["CERTS_DIR"] = _portable(ca_path.parent)
    # Certificats changÃ©s â†’ nginx recharge ses certs au boot : recreation gateway.
    if certs_changed:
        to_recreate.setdefault("gateway", "certificats TLS rÃ©gÃ©nÃ©rÃ©s")
    # La CA est aussi copiÃ©e dans le dossier de config des Discussions :
    # Synapse la monte (magasin systÃ¨me) pour l'OIDC vers la passerelle TLS.
    for cfg_dir_name in ("discussions", "meet"):
        cfg_dir = runtime_dir / cfg_dir_name
        if cfg_dir.is_dir():
            shutil.copyfile(ca_path, cfg_dir / "ca.crt")
    # ThÃ¨me de login LaStarter (drop-in Keycloak).
    theme_dir = repo_root / "identity" / "keycloak-theme"
    if theme_dir.is_dir():
        compose_env["THEME_DIR"] = _portable(theme_dir)

    # Passerelle : conf nginx gÃ©nÃ©rÃ©e depuis les briques sÃ©lectionnÃ©es.
    # Un bind mount ne dÃ©clenche ni recreation ni reload : suivi de hash.
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
        to_recreate.setdefault("gateway", "conf passerelle changÃ©e")
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
            raise DeployError("Ã©chec de docker compose pull")

    # 0. Anti-dÃ©rive : re-CRÃ‰ER (sans dÃ©marrer) les services dont un fichier
    # montÃ© a changÃ© (env_file, config, homeserver, edge, certificats) â€” AVANT
    # tout dÃ©marrage : un conteneur pÃ©rimÃ© ferait Ã©chouer le --wait de l'infra.
    if to_recreate:
        for service, reason in to_recreate.items():
            print(f"recreation de {service} ({reason})")
            result = run(base + ["create", "--force-recreate", service])
            if result.returncode != 0:
                raise DeployError(f"Ã©chec de la recreation de {service} ({reason})")
        for marker_path, marker_hash in pending_markers:
            marker_path.write_text(marker_hash + "\n", encoding="utf-8")

    # 1. Infrastructure (DB, cache, S3, keycloak) â€” healthchecks verts.
    infra: list[str] = []
    for name in selected:
        infra.extend(bricks[name].compose.get("infra_services", []))
    if infra:
        result = run(base + ["up", "-d", "--wait", *dict.fromkeys(infra)])
        if result.returncode != 0:
            raise DeployError("Ã©chec du dÃ©marrage de l'infrastructure (voir logs ci-dessus)")

    # 2. PrÃ©paration one-off (ex. chown de volumes pour des images non-root).
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
            raise DeployError(f"prÃ©paration Ã©chouÃ©e pour {name}")

    # 3. Migrations (one-off, une par brique qui en dÃ©clare).
    for name in selected:
        brick = bricks[name]
        service = brick.compose.get("migrate_service")
        command = brick.compose.get("migrate_command")
        if not (service and command):
            continue
        result = run(base + ["run", "--rm", service, *shlex.split(command)])
        if result.returncode != 0:
            raise DeployError(f"migration Ã©chouÃ©e pour {name}")

    # 3. Ensemble de la pile (les services retirÃ©s du manifeste sont nettoyÃ©s).
    result = run(base + ["up", "-d", "--wait", "--remove-orphans"])
    if result.returncode != 0:
        raise DeployError("Ã©chec du dÃ©marrage (voir logs ci-dessus)")

    # 4. Clients OIDC : l'API admin fait autoritÃ© aprÃ¨s le premier import du realm
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
        # Provisionnement via l'apex (host rÃ©solvable par l'OS : *.localhost ne
        # rÃ©sout que cÃ´tÃ© navigateurs) â€” la passerelle route vers keycloak de
        # toute faÃ§on ; l'issuer OIDC reste https://id.<domaine> (KC_HOSTNAME).
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
        print(f"Clients OIDC synchronisÃ©s via l'API admin : {', '.join(provisioned)}")

        # Element-call same-origin : ajouter meet.<domaine> comme redirect URI
        # pour le client synapse (le SSO callback passe par meet.<domaine>).
        if "element-call" in selected:
            s, t = _http_json(
                f"{api_base}/admin/realms/lastarter/clients?clientId=synapse&exact=true",
                method="GET", token=json.loads(_http_json(
                    f"{api_base}/realms/master/protocol/openid-connect/token", "POST",
                    form={"grant_type": "password", "client_id": "admin-cli",
                          "username": admin_user, "password": vault["kc_admin_password"]},
                    ca_file=ca_path,
                )[1])["access_token"], ca_file=ca_path)
            if s == 200:
                clients = json.loads(t)
                if clients:
                    client = clients[0]
                    call_origin = app_origin(answers["domain"], "meet")
                    if call_origin not in client.get("redirectUris", []):
                        client["redirectUris"].append(f"{call_origin}/*")
                        client["webOrigins"].append(call_origin)
                        # Re-authentifier pour le PUT
                        s3, t3 = _http_json(
                            f"{api_base}/realms/master/protocol/openid-connect/token",
                            "POST",
                            form={"grant_type": "password", "client_id": "admin-cli",
                                  "username": admin_user, "password": vault["kc_admin_password"]},
                            ca_file=ca_path,
                        )
                        if s3 == 200:
                            s2, _ = _http_json(
                                f"{api_base}/admin/realms/lastarter/clients/{client['id']}",
                                method="PUT", token=json.loads(t3)["access_token"],
                                body=client, ca_file=ca_path,
                            )
                            if s2 in (200, 204):
                                print(f"Redirect URI ajoutÃ© : {call_origin}/*")

    # Matrix (Discussions) : compte demo avec le mot de passe du coffre â€”
    # Element Call standalone (meet.<domaine>) s'authentifie en password,
    # cette version du SPA n'ayant pas de SSO natif. Le chat reste 100% SSO.
    if "discussions" in selected and "element-call" in selected:
        chat_origin = app_origin(answers["domain"], "chat")
        provision_matrix_demo(
            base_url=chat_origin,
            server_name=answers["domain"].split(":")[0],
            shared_secret=vault["discussions_registration_secret"],
            username="demo",
            password=vault["demo_user_password"],
            ca_file=ca_path,
        )

    print(f"\nDÃ©ploiement Â« {slug} Â» opÃ©rationnel (TLS, port 8443).")
    id_url = _id_origin(answers["domain"])
    print(f"  Portail       : {compute_origin(answers['domain'])} â€” entrÃ©e unique de la suite")
    print(f"  IdentitÃ© (SSO) : {id_url} â€” inscription activÃ©e, console {id_url}/admin")
    for brick in selected_bricks:
        if brick.core:
            continue
        label = brick.compose.get("route_label", brick.name)
        print(f"  {brick.name:<12} : {app_origin(answers['domain'], label)}")
    print(f"  Connexion dÃ©mo : demo / secrets.env:demo_user_password")
    print(f"  Console admin  : admin / secrets.env:kc_admin_password")
    if (runtime_dir / "certs" / "ca.crt").is_file():
        print()
        print("  âš  POC TLS : faire confiance Ã  la CA locale UNE fois (navigateurs) :")
        print(f"    certutil -user -addstore Root \"{(runtime_dir / 'certs' / 'ca.crt')}\"")
        print("    (ou accepter l'avertissement par sous-domaine dans le navigateur)")
    run(base + ["ps"])
    return 0


def run_ps(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvÃ©.", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    slug = opts.client
    load_deployment(repo_root, slug)  # gates
    runtime_env_file = repo_root / "deployments" / slug / ".runtime" / "compose.env"
    if not runtime_env_file.is_file():
        raise DeployError("aucun .runtime/compose.env â€” lancer `lastarter deploy` d'abord")
    manifest = tomllib.loads((repo_root / "deployments" / slug / "lastarter.toml").read_text(encoding="utf-8"))
    compose_files = [repo_root / "deploy" / "compose" / "base.yml"] + [
        repo_root / "deploy" / "compose" / f"{n}.yml" for n in manifest.get("bricks", {})
    ]
    result = subprocess.run(compose_base(runtime_env_file, slug, compose_files) + ["ps"], check=False)
    return result.returncode


def _portable(path: Path) -> str:
    """Chemin en slashes pour docker compose sur Windows comme sur POSIX."""
    return str(path.resolve()).replace("\\", "/")
