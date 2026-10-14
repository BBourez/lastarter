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
import subprocess
import sys
import tomllib
from pathlib import Path

from ..catalogue import Brick, find_catalogue, load_catalogue

SECRET_TOKEN = re.compile(r"\{secret:([a-z0-9_]+)\}", re.IGNORECASE)
REALM_SECRET_TOKEN = re.compile(r"\{\{SECRET:([a-z0-9_]+)\}\}", re.IGNORECASE)


class DeployError(Exception):
    """Erreur attendue — remontée propre en exit 1."""


# ---------------------------------------------------------------------------
# Contextes et rendus


def compute_origin(domain: str) -> str:
    """Schéma+domaine : http en local (POC), https sinon."""
    host = domain.split(":")[0]
    local = host in {"localhost", "127.0.0.1", "::1", "[::1]", "host.docker.internal"}
    return f"http://{domain}" if local else f"https://{domain}"


def _context(answers: dict) -> dict[str, str]:
    domain = answers["domain"]
    host = domain.split(":")[0]
    return {
        "{domain}": domain,
        "{origin}": compute_origin(domain),
        "{brand_name}": answers.get("brand_name", "LaStarter"),
        # POC : média servi directement par rustfs sur le port hôte 9000 (phase 3 : media-auth)
        "{domain_s3}": f"{host}:9000",
    }


def render_runtime_env(draft: str, answers: dict, vault: dict[str, str]) -> str:
    """Substitue les jetons d'un draft committable en env d'exécution (avec secrets)."""
    context = _context(answers)

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


def render_realm(template: str, answers: dict, vault: dict[str, str]) -> str:
    """Rend le realm Keycloak ({{ORIGIN}}, {{DOMAIN}}, {{SECRET:x}})."""
    rendered = template.replace("{{ORIGIN}}", compute_origin(answers["domain"]))
    rendered = rendered.replace("{{DOMAIN}}", answers["domain"])

    def secret(match: re.Match) -> str:
        name = match.group(1)
        if name not in vault:
            raise DeployError(f"secret manquant dans secrets.env : {name}")
        return vault[name]

    return REALM_SECRET_TOKEN.sub(secret, rendered)


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
    compose_env: dict[str, str] = {}
    for name in selected:
        draft_path = deployment_dir / "env" / f"{name}.env"
        if not draft_path.is_file():
            raise DeployError(f"env draft manquant : {draft_path} (rejouer `lastarter init`)")
        rendered = render_runtime_env(draft_path.read_text(encoding="utf-8"), answers, vault)
        (runtime_dir / f"{name}.env").write_text(rendered, encoding="utf-8")
        for line in rendered.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, value = line.partition("=")
                compose_env[key.strip()] = value.strip()

    # Realm Keycloak (si la brique est déployée).
    realm_template = repo_root / "identity" / "realm-lastarter.json"
    if "keycloak" in selected and realm_template.is_file():
        realm_rendered = render_realm(realm_template.read_text(encoding="utf-8"), answers, vault)
        realm_path = runtime_dir / "realm-lastarter.json"
        realm_path.write_text(realm_rendered, encoding="utf-8")
        compose_env["REALM_JSON_PATH"] = _portable(realm_path)

    compose_env["LASTARTER_CLIENT"] = slug
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

    # 1. Infrastructure (DB, cache, S3, keycloak) — healthchecks verts.
    infra: list[str] = []
    for name in selected:
        infra.extend(bricks[name].compose.get("infra_services", []))
    if infra:
        result = run(base + ["up", "-d", "--wait", *dict.fromkeys(infra)])
        if result.returncode != 0:
            raise DeployError("échec du démarrage de l'infrastructure (voir logs ci-dessus)")

    # 2. Migrations (one-off, une par brique qui en déclare).
    for name in selected:
        brick = bricks[name]
        service = brick.compose.get("migrate_service")
        command = brick.compose.get("migrate_command")
        if not (service and command):
            continue
        result = run(base + ["run", "--rm", service, *shlex.split(command)])
        if result.returncode != 0:
            raise DeployError(f"migration échouée pour {name}")

    # 3. Ensemble de la pile.
    result = run(base + ["up", "-d", "--wait"])
    if result.returncode != 0:
        raise DeployError("échec du démarrage (voir logs ci-dessus)")

    print(f"\nDéploiement « {slug} » opérationnel.")
    origin = compute_origin(answers["domain"])
    print(f"  Entrée         : {origin}")
    print(f"  Console SSO    : {origin}/admin (admin / mot de passe : secrets.env:kc_admin_password)")
    print(f"  Utilisateur démo : demo / secrets.env:demo_user_password")
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
