#!/usr/bin/env python3
"""Rendu du realm Keycloak + secrets Kubernetes pour la cible kind LaStarter.

Réutilise le MOTEUR du CLI compose (import depuis cli/lastarter_cli) :
- build_realm_clients() construit les clients OIDC depuis le catalogue
  (discussions/docs/drive/meet — mêmes clients que compose) ;
- render_realm() rend le gabarit committé identity/realm-lastarter.json.

Différences volontaires avec le rendu compose :
- origins kind : http://<label>.localhost:8080 (ingress HTTP sur :8080, pas
  la passerelle TLS :8443) — obtenu en forçant le scheme « http » du moteur
  et un domaine PORTÉ (localhost:8080) ;
- secrets GÉNÉRÉS À NEUF : aucune valeur du coffre compose ne traverse ici.

RÈGLE SECRETS : tout rendu contenant un secret vit dans deploy/k8s/.runtime/
(gitignoré) ; les manifests committed ne contiennent que des placeholders.
Idempotent : les secrets existants de secrets.env sont réutilisés tels quels
(invariant CLI), seuls les manquants sont générés.

Sorties (deploy/k8s/.runtime/) :
  secrets.env                coffre k8s (source de vérité locale)
  realm-lastarter.json       realm rendu (import Keycloak au premier boot)
  secret-postgres.yaml       Secret : compte + mot de passe postgres
  secret-keycloak.yaml       Secret : admin bootstrap Keycloak + db
  secret-drive.yaml          Secret : OIDC/S3/Django/superuser drive
  secret-keycloak-theme.yaml Secret : thème de login (identity/keycloak-theme)
  values-drive-secrets.yaml  overlay helm drive (secrets literals)

Usage : python deploy/k8s/kind/render-realm.py
"""

from __future__ import annotations

import base64
import json
import secrets as pysecrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "deploy" / "k8s" / ".runtime"
IDENTITY = REPO_ROOT / "identity"

DOMAIN = "localhost:8080"  # ingress kind : ports hôtes 8080 -> 80 (HTTP)
BRAND_NAME = "LaStarter"

# Coffre k8s : (clé, rôle). Nommage aligné sur le coffre compose.
SECRET_SPECS = [
    ("demo_user_password", "utilisateur de démonstration (realm lastarter)"),
    ("kc_admin_password", "console admin Keycloak (realm master)"),
    ("postgres_password", "superuser postgres — bases keycloak + drive"),
    ("drive_django_secret_key", "SECRET_KEY Django (drive)"),
    ("drive_s3_secret", "secret S3 rustfs (backend + rustfs + s3-init)"),
    ("drive_oidc_secret", "client OIDC drive"),
    ("discussions_oidc_secret", "client OIDC discussions (synapse)"),
    ("docs_oidc_secret", "client OIDC docs"),
    ("meet_oidc_secret", "client OIDC meet"),
    ("drive_superuser_password", "superuser Django drive (console /admin)"),
]


def parse_secrets_env(path: Path) -> dict[str, str]:
    """Même format que le coffre CLI (KEY=VALUE, lignes # ignorées)."""
    if not path.is_file():
        return {}
    vault: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        vault[key.strip()] = value.strip()
    return vault


def yaml_str(value: str) -> str:
    """Chaîne YAML sûre (JSON est un sous-ensemble YAML)."""
    return json.dumps(value, ensure_ascii=False)


def secret_manifest(name: str, namespace: str, data: dict[str, str]) -> str:
    lines = [
        "# RENDU par deploy/k8s/kind/render-realm.py — JAMAIS commité (.runtime/).",
        "apiVersion: v1",
        "kind: Secret",
        "metadata:",
        f"  name: {name}",
        f"  namespace: {namespace}",
        "type: Opaque",
        "stringData:",
    ]
    lines += [f"  {key}: {yaml_str(value)}" for key, value in sorted(data.items())]
    return "\n".join(lines) + "\n"


def theme_secret_manifest() -> str:
    """Thème de login lastarter (identity/keycloak-theme) en Secret k8s.

    Clés aplaties ('/' -> '.') ; le Deployment remet les chemins réels via
    volumes[].secret.items[].path (mapping miroir dans manifests/20-keycloak.yaml).
    """
    root = IDENTITY / "keycloak-theme" / "lastarter"
    if not root.is_dir():
        raise SystemExit(f"thème introuvable : {root}")
    lines = [
        "# RENDU par deploy/k8s/kind/render-realm.py — JAMAIS commité (.runtime/).",
        "apiVersion: v1",
        "kind: Secret",
        "metadata:",
        "  name: keycloak-theme",
        "  namespace: lastarter",
        "type: Opaque",
        "data:",
    ]
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        key = rel.replace("/", ".")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        lines.append(f"  {key}: {data}")
    return "\n".join(lines) + "\n"


def values_drive_secrets(vault: dict[str, str]) -> str:
    """Overlay helm drive : les secrets literals (consommés par backend.envVars)."""
    return "\n".join(
        [
            "# RENDU par deploy/k8s/kind/render-realm.py — JAMAIS commité (.runtime/).",
            "# Overlay des secrets drive : helm install -f values-drive.yaml -f CE FICHIER.",
            "backend:",
            "  envVars:",
            f"    DB_PASSWORD: {yaml_str(vault['postgres_password'])}",
            f"    AWS_S3_SECRET_ACCESS_KEY: {yaml_str(vault['drive_s3_secret'])}",
            f"    OIDC_RP_CLIENT_SECRET: {yaml_str(vault['drive_oidc_secret'])}",
            f"    DJANGO_SECRET_KEY: {yaml_str(vault['drive_django_secret_key'])}",
            "    DJANGO_SUPERUSER_EMAIL: " + yaml_str("admin@lastarter.local"),
            f"    DJANGO_SUPERUSER_PASSWORD: {yaml_str(vault['drive_superuser_password'])}",
        ]
    ) + "\n"


def main() -> None:
    RUNTIME.mkdir(parents=True, exist_ok=True)

    # Moteur du CLI : sys.path avant l'import du package.
    sys.path.insert(0, str(REPO_ROOT))
    from cli.lastarter_cli.catalogue import load_catalogue  # noqa: E402
    from cli.lastarter_cli.cmd import deploy as cli_deploy  # noqa: E402

    # POC kind en HTTP : le moteur force « https » (passerelle compose TLS).
    # Ici scheme http + domaine PORTÉ -> app_origin() donne
    # http://<label>.localhost:8080 (ports k8s, pas 8443).
    cli_deploy._scheme = lambda domain: "http"  # noqa: SLF001
    answers = {"domain": DOMAIN, "brand_name": BRAND_NAME}

    # 1. Coffre : réutilise, ne génère que le manquant (append-only).
    vault = parse_secrets_env(RUNTIME / "secrets.env")
    created: list[str] = []
    for name, _comment in SECRET_SPECS:
        if not vault.get(name):
            vault[name] = pysecrets.token_urlsafe(32)
            created.append(name)

    # 2. Clients OIDC via le moteur : mêmes briques que compose, secrets k8s.
    bricks, errors = load_catalogue(REPO_ROOT / "catalogue")
    if errors:
        raise SystemExit("catalogue invalide : " + " ; ".join(errors))
    app_bricks = sorted(
        (b for b in bricks.values() if not b.core and b.oidc.get("client_id")),
        key=lambda b: b.name,
    )
    rendered_envs = {
        brick.name: f"OIDC_RP_CLIENT_SECRET={vault[brick.name + '_oidc_secret']}"
        for brick in app_bricks
    }
    brick_clients = json.loads(cli_deploy.build_realm_clients(app_bricks, rendered_envs, answers))
    clients_json = json.dumps(
        cli_deploy.ACCOUNT_CONSOLE_CLIENTS + brick_clients, indent=2, ensure_ascii=False
    )

    # 3. Realm rendu (gabarit committé, jetons {{SECRET:...}} substitués).
    template = (IDENTITY / "realm-lastarter.json").read_text(encoding="utf-8")
    realm = cli_deploy.render_realm(template, answers, vault, clients_json)
    json.loads(realm)  # garde-fou : JSON valide

    # 4. Écritures (.runtime/ uniquement).
    (RUNTIME / "secrets.env").write_text(
        "\n".join(
            ["# SECRETS GENERES POUR LA CIBLE KIND — JAMAIS COMMITER (.runtime/ gitignore).",
             "# Idempotent : les valeurs existantes ne sont JAMAIS modifiées (invariant CLI).", ""]
            + [f"# {comment}\n{name}={vault[name]}\n" for name, comment in SECRET_SPECS]
        ),
        encoding="utf-8",
    )
    (RUNTIME / "realm-lastarter.json").write_text(realm, encoding="utf-8")
    (RUNTIME / "secret-postgres.yaml").write_text(
        secret_manifest(
            "postgres-secrets",
            "lastarter",
            {"POSTGRES_USER": "lastarter", "POSTGRES_PASSWORD": vault["postgres_password"], "POSTGRES_DB": "postgres"},
        ),
        encoding="utf-8",
    )
    (RUNTIME / "secret-keycloak.yaml").write_text(
        secret_manifest(
            "keycloak-secrets",
            "lastarter",
            {
                "KC_BOOTSTRAP_ADMIN_USERNAME": "admin",
                "KC_BOOTSTRAP_ADMIN_PASSWORD": vault["kc_admin_password"],
                "KC_DB_USERNAME": "lastarter",
                "KC_DB_PASSWORD": vault["postgres_password"],
            },
        ),
        encoding="utf-8",
    )
    (RUNTIME / "secret-drive.yaml").write_text(
        secret_manifest(
            "drive-secrets",
            "lastarter",
            {
                "OIDC_RP_CLIENT_SECRET": vault["drive_oidc_secret"],
                "AWS_S3_SECRET_ACCESS_KEY": vault["drive_s3_secret"],
                "RUSTFS_SECRET_KEY": vault["drive_s3_secret"],
                "DJANGO_SECRET_KEY": vault["drive_django_secret_key"],
                "DB_PASSWORD": vault["postgres_password"],
                "DJANGO_SUPERUSER_EMAIL": "admin@lastarter.local",
                "DJANGO_SUPERUSER_PASSWORD": vault["drive_superuser_password"],
            },
        ),
        encoding="utf-8",
    )
    (RUNTIME / "secret-keycloak-theme.yaml").write_text(theme_secret_manifest(), encoding="utf-8")
    (RUNTIME / "values-drive-secrets.yaml").write_text(values_drive_secrets(vault), encoding="utf-8")

    print(f"Realm rendu : {RUNTIME / 'realm-lastarter.json'} ({len(brick_clients) + 2} clients OIDC)")
    for brick in app_bricks:
        client = next(c for c in brick_clients if c["clientId"] == brick.oidc["client_id"])
        print(f"  client {client['clientId']} -> {client['redirectUris'][0]}")
    print(f"Secrets : {'générés (' + ', '.join(created) + ')' if created else 'inchangés'} -> {RUNTIME / 'secrets.env'}")
    print("Mot de passe démo : demo / secrets.env:demo_user_password")


if __name__ == "__main__":
    main()
