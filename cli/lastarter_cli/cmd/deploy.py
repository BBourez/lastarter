"""`lastarter deploy` — assemblage et lancement docker-compose d'un déploiement client.

Phase 2 : cible mono-VM (compose). Gates avant tout effet réseau :
docker présent, déploiement initialisé, secrets présents, chaque brique sélectionnée
possède un fichier compose. Les secrets ne quittent jamais `deployments/<client>/.runtime/`
(gitignoré) — les drafts committables ne contiennent que des jetons.
"""

from __future__ import annotations

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
    """Extrait OIDC_RP_CLIENT_SECRET d'un env rendu (source unique : la brique)."""
    for line in rendered_env.splitlines():
        if line.startswith("OIDC_RP_CLIENT_SECRET="):
            return line.partition("=")[2].strip()
    raise DeployError("OIDC_RP_CLIENT_SECRET absent de l'env rendu")


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
                "defaultClientScopes": ["web-origins", "acr", "roles", "profile", "email"],
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

    SANs explicites pour chaque hôte déployé (CPython 3.12+ refuse les wildcards
    sur un domaine mono-label type *.localhost côté vérification stricte ; les
    navigateurs, eux, acceptent le wildcard). Retourne (ca, crt, key, changé) —
    `changé` = certificats (re)générés → le serveur doit recharger.
    """
    certs_dir = runtime_dir / "certs"
    certs_dir.mkdir(parents=True, exist_ok=True)
    ca, crt, key = certs_dir / "ca.crt", certs_dir / "server.crt", certs_dir / "server.key"
    ca_key = certs_dir / "ca.key"
    wanted_sans = sorted(set(san_names) | {"localhost", "*.localhost"})
    marker = certs_dir / ".sans"
    current_sans = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""
    leaf_current = crt.is_file() and key.is_file() and current_sans == "\n".join(wanted_sans)
    if ca.is_file() and leaf_current:
        return ca, crt, key, False

    # CA créée UNE fois (confiance navigateur stable) ; seul le certificat
    # feuille est re-émis quand la liste d'hôtes change.
    san_line = ",".join(f"DNS:{name}" for name in wanted_sans)
    make_ca = "" if ca.is_file() and ca_key.is_file() else (
        "openssl req -x509 -newkey rsa:2048 -nodes -days 3650 "
        "-keyout /certs/ca.key -out /certs/ca.crt -subj '/CN=LaStarter POC CA'; "
    )
    script = (
        "set -e; "
        + make_ca
        + "openssl req -newkey rsa:2048 -nodes "
        "-keyout /certs/server.key -out /certs/server.csr -subj '/CN=localhost'; "
        f"printf 'subjectAltName={san_line}\\nbasicConstraints=CA:FALSE\\n' > /certs/san.ext; "
        "openssl x509 -req -in /certs/server.csr -CA /certs/ca.crt -CAkey /certs/ca.key "
        "-CAcreateserial -out /certs/server.crt -days 825 -extfile /certs/san.ext; "
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
        "    # Endpoints SSO accessibles aussi sur l'apex (outillage/CLI, compat).",
    ]
    for path in ("/realms/", "/resources/", "/js/", "/admin/"):
        lines += [
            f"    location {path} {{",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            "        set $backend_keycloak keycloak:8080;",
            "        proxy_pass http://$backend_keycloak;",
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
        "        proxy_set_header Host $http_host;",
        "        proxy_set_header X-Forwarded-Proto https;",
        "    }",
        "}",
        "",
    ]
    # Serveur d'identité dédié : id.<domaine> → Keycloak (toute l'auth).
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
        "    location / {",
        "        resolver 127.0.0.11 valid=10s ipv6=off;",
        "        set $backend_keycloak keycloak:8080;",
        "        proxy_pass http://$backend_keycloak;",
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
        if api_target:
            lines += [
                "    location /api/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_api {api_target};",
                "        proxy_pass http://$backend_api;",
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
                "        proxy_set_header Host $http_host;",
                "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
                "        proxy_set_header X-Forwarded-Proto https;",
                "    }",
                "",
                "    location /static/ {",
                "        resolver 127.0.0.11 valid=10s ipv6=off;",
                f"        set $backend_static {api_target};",
                "        proxy_pass http://$backend_static;",
                "        proxy_set_header Host $http_host;",
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
            "        proxy_set_header Host $http_host;",
            '        add_header Service-Worker-Allowed "/";',
            '        add_header Cache-Control "no-cache";',
            "    }",
            "",
        ]
        # Element Call : accessible directement (standalone + widget).
        # Pas de redirection — meet.<domaine> est la visio standalone séparée.
        lines += [
            "    location / {",
            "        resolver 127.0.0.11 valid=10s ipv6=off;",
            f"        set $backend_front {brick.compose['frontend_target']};",
            "        proxy_pass http://$backend_front;",
            "        proxy_set_header Host $http_host;",
            "        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;",
            "        proxy_set_header X-Forwarded-Proto https;",
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


def render_lk_registration(answers: dict, vault: dict[str, str]) -> str:
    """Rend le registration YAML de l'appservice lk-jwt-service (MSC4512)."""
    bare = answers["domain"].split(":")[0]
    return (
        "# LaStarter — appservice lk-jwt-service (rendu par lastarter-cli).\n"
        'id: "lk-jwt-service"\n'
        f'as_token: "{vault["lk_as_token"]}"\n'
        f'hs_token: "{vault["lk_hs_token"]}"\n'
        'sender_localpart: "_lk_jwt_service"\n'
        "namespaces:\n"
        "  users:\n"
        "    - exclusive: false\n"
        f"      regex: \"@.*:{re.escape(bare)}\"  # tous les utilisateurs locaux\n"
        "# Synapse pousse les évènements et proxifie rtc/livekit (MSC4512) ici :\n"
        'url: "http://lk-jwt-service:6080"\n'
        "io.element.msc4502.scopes:\n"
        '  ["urn:matrix:client:io.element.msc4502:rooms:is_joined"]\n'
        "io.element.msc4512.proxy_prefix: \"rtc/livekit\"\n"
        "io.element.msc4512.proxy_url: \"http://lk-jwt-service:6080\"\n"
    )


def render_synapse_homeserver(template: str, answers: dict, vault: dict[str, str]) -> str:
    """Rend homeserver.yaml : endpoints OIDC scindés + secrets du coffre."""
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

    rendered = template.replace("{{SSO_ORIGIN}}", _id_origin(domain))  # cohérence cookies : id.<domaine> partout
    rendered = rendered.replace("{{MATRIX_ORIGIN}}", matrix_origin)
    rendered = rendered.replace("{{SERVER_NAME}}", bare)
    return REALM_SECRET_TOKEN.sub(secret, rendered)


def render_element_config(template: str, answers: dict, brick: Brick) -> str:
    """Rend config.json element-web : marque + homeserver + thème personnalisé."""
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
    """Rend config.json element-call (mode standalone) : homeserver + LiveKit."""
    domain = answers["domain"]
    bare = domain.split(":")[0]
    port = domain.split(":")[1] if ":" in domain else ""
    scheme = _scheme(domain)
    matrix_origin = f"{scheme}://matrix.{bare}" + (f":{port}" if port else "")
    livekit_url = f"wss://livekit.{bare}" + (f":{port}" if port else "")
    rendered = template.replace("{{MATRIX_ORIGIN}}", matrix_origin)
    rendered = rendered.replace("{{LIVEKIT_URL}}", livekit_url)
    rendered = rendered.replace("{{BRAND}}", answers.get("brand_name", "LaStarter"))
    return rendered


APP_EMOJI = {
    "drive": "📁",
    "meet": "🎥",
    "element-web": "💬",
    "element-call": "📞",
    "transfers": "📨",
    "messages": "✉️",
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
        short = brick.title.split("—")[0].strip()
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

    # Réglages du realm : inscription libre, thème custom, sécurité brute-force.
    status, text = _http_json(f"{admin}", method="GET", token=token, ca_file=ca_file)
    if status != 200:
        raise DeployError(f"lecture realm impossible (HTTP {status})")
    realm = json.loads(text)
    realm.update(
        {
            "registrationAllowed": True,
            "resetPasswordAllowed": True,
            "bruteForceProtected": True,
            "rememberMe": True,
            "loginWithEmailAllowed": True,
            "loginTheme": "lastarter",
        }
    )
    status, _ = _http_json(f"{admin}", method="PUT", token=token, body=realm, ca_file=ca_file)
    if status not in (200, 204):
        raise DeployError(f"mise à jour du realm impossible (HTTP {status})")

    _ensure_realm_user(admin, token, "demo", "Demo", demo_password, ca_file)
    if realm_admin_password:
        _ensure_realm_user(admin, token, "admin", "Admin", realm_admin_password, ca_file)


def provision_realm_clients(base_url: str, admin_user: str, admin_password: str, clients_json: str, ca_file: Path | None = None) -> list[str]:
    """Crée ou met à jour chaque client OIDC du realm `lastarter` via l'API admin.

    Idempotent : GET par clientId, POST si absent, PUT sinon (secret + redirects).
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
    done: list[str] = []
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
            status, _ = _http_json(
                f"{admin}/clients/{existing[0]['id']}", method="PUT", token=token, body=client, ca_file=ca_file
            )
        else:
            status, _ = _http_json(f"{admin}/clients", method="POST", token=token, body=client, ca_file=ca_file)
        if status not in (200, 201, 204):
            raise DeployError(f"synchronisation du client {client_id} impossible (HTTP {status})")
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
        clients_json = build_realm_clients(selected_bricks, rendered_envs, answers)
        realm_rendered = render_realm(
            realm_template.read_text(encoding="utf-8"), answers, vault, clients_json
        )
        realm_path = runtime_dir / "realm-lastarter.json"
        realm_path.write_text(realm_rendered, encoding="utf-8")
        compose_env["REALM_JSON_PATH"] = _portable(realm_path)

    # Synapse : homeserver.yaml + clé de signature rendus as-code.
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
        # Comme les envs : un bind mount changé ne redémarre pas synapse.
        homeserver_hash = hashlib.sha256(homeserver_rendered.encode()).hexdigest()
        applied = runtime_dir / ".synapse-homeserver.applied"
        if not applied.is_file() or applied.read_text(encoding="utf-8").strip() != homeserver_hash:
            to_recreate.setdefault("synapse_synapse", "homeserver.yaml changé")
            pending_markers.append((applied, homeserver_hash))
        signing_path = runtime_dir / "synapse-signing.key"
        signing_path.write_text(
            f"ed25519 0 {vault['synapse_signing_key']}\n", encoding="utf-8"
        )
        compose_env["SYNAPSE_HOMESERVER_PATH"] = _portable(homeserver_path)
        compose_env["SYNAPSE_SIGNING_KEY_PATH"] = _portable(signing_path)

        # Registration appservice rtc/livekit (monté en permanence dans synapse).
        registration_path = runtime_dir / "lk-jwt-service.yaml"
        registration_path.write_text(render_lk_registration(answers, vault), encoding="utf-8")
        compose_env["LK_REGISTRATION_PATH"] = _portable(registration_path)

    # element-web : config.json (marque + homeserver + thème) rendu as-code.
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

    # element-call : config.json standalone (homeserver + LiveKit).
    if "element-call" in selected:
        ec_template = repo_root / "identity" / "element-call-config.json"
        if ec_template.is_file():
            ec_path = runtime_dir / "element-call-config.json"
            ec_path.write_text(
                render_element_call_config(
                    ec_template.read_text(encoding="utf-8"), answers
                ),
                encoding="utf-8",
            )
            compose_env["ELEMENT_CALL_CONFIG_PATH"] = _portable(ec_path)

    # Portail : copie des pages + config générée dans .runtime/portal/ (montage unique).
    portal_dir = repo_root / "portal"
    if portal_dir.is_dir():
        runtime_portal = runtime_dir / "portal"
        shutil.copytree(portal_dir, runtime_portal, dirs_exist_ok=True)
        (runtime_portal / "portal-config.json").write_text(
            render_portal_config(selected_bricks, answers), encoding="utf-8"
        )
        compose_env["PORTAL_DIR"] = _portable(runtime_portal)

    # Certificats TLS POC — SANs explicites pour chaque hôte déployé (id + apps
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
    # Certificats changés → nginx recharge ses certs au boot : recreation gateway.
    if certs_changed:
        to_recreate.setdefault("gateway", "certificats TLS régénérés")
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
    infra: list[str] = []
    for name in selected:
        infra.extend(bricks[name].compose.get("infra_services", []))
    if infra:
        result = run(base + ["up", "-d", "--wait", *dict.fromkeys(infra)])
        if result.returncode != 0:
            raise DeployError("échec du démarrage de l'infrastructure (voir logs ci-dessus)")

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
    result = run(base + ["up", "-d", "--wait", "--remove-orphans"])
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
        )
        print(f"Clients OIDC synchronisés via l'API admin : {', '.join(provisioned)}")

    print(f"\nDéploiement « {slug} » opérationnel (TLS, port 8443).")
    id_url = _id_origin(answers["domain"])
    print(f"  Portail       : {compute_origin(answers['domain'])} — entrée unique de la suite")
    print(f"  Identité (SSO) : {id_url} — inscription activée, console {id_url}/admin")
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
