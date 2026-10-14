"""`lastarter init` — questionnaire client et génération de deployments/<client>/.

Maquette phase 1 : génère l'arbre de configuration, ne déploie rien.

Invariants (repris du modèle st-cli) :
- les secrets sont générés une seule fois, puis repris tels quels d'answers.json ;
- un `init` rejoué sur un déploiement existant pré-remplit toutes les réponses ;
- aucune valeur déjà commitée n'est écrasée sans confirmation affichée.
"""

from __future__ import annotations

import json
import re
import secrets as pysecrets
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from .. import __version__
from ..catalogue import Brick, find_catalogue, load_catalogue, resolve_selection, secret_names
from .. import prompts


def slugify(text: str) -> str:
    """Nom de dossier sûr : minuscules, sans accents, tirets."""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "client"


# ---------------------------------------------------------------------------
# Réponses


def load_answers(deployment_dir: Path) -> dict | None:
    path = deployment_dir / "answers.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def gather_answers(
    bricks: dict[str, Brick],
    deployments_root: Path,
    client: str | None,
    domain: str | None,
    brand: str | None,
    wanted: list[str] | None,
    non_interactive: bool,
    include_planned: bool,
) -> dict:
    """Constitue les réponses, interactives ou non, avec pré-remplissage sur rejeu."""
    slug = slugify(client or "")
    deployment_dir = deployments_root / slug if slug else None
    existing = load_answers(deployment_dir) if deployment_dir else None

    if non_interactive:
        if not client or not domain or not wanted:
            raise SystemExit(
                "init --non-interactive requiert --client, --domain et --bricks."
            )
        return {
            "client_name": client,
            "client_slug": slug,
            "domain": domain,
            "brand_name": brand or "LaStarter",
            "bricks": wanted,
        }

    # Interactif, pré-rempli depuis l'existant.
    print(
        "LaStarter — configuration d'un déploiement client"
        + (" (rejeu : Entrée conserve les valeurs actuelles)" if existing else "")
    )
    client_name = prompts.ask("Nom du client", existing.get("client_name") if existing else client)
    slug = slugify(client_name)
    domain = prompts.ask("Domaine principal", (existing or {}).get("domain", domain or ""))
    brand_name = prompts.ask("Nom de marque affiché", (existing or {}).get("brand_name", brand or "LaStarter"))

    selectable = [
        b for b in bricks.values()
        if not b.core and (b.is_selectable or include_planned)
    ]
    labels = [
        f"{b.title} [{b.name}]"
        + ("" if b.is_selectable else " (à venir — phase 4)")
        + (f" — requis par d'autres briques" if any(b.name in o.requires for o in bricks.values()) else "")
        for b in selectable
    ]
    previous = set((existing or {}).get("bricks", []))
    preselected = [b.name in previous for b in selectable]
    chosen = prompts.ask_checkboxes("Briques à installer (les briques fondation sont incluses d'office) :", labels, preselected)
    return {
        "client_name": client_name,
        "client_slug": slug,
        "domain": domain,
        "brand_name": brand_name,
        "bricks": [selectable[i].name for i in chosen],
    }


def parse_secrets_env(path: Path) -> dict[str, str]:
    """Lit secrets.env (KEY=VALUE, lignes # ignorées) — source de vérité du coffre."""
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


def generate_secrets(ordered: list[Brick], existing: dict | None) -> dict[str, str]:
    """Génère les secrets manquants ; reprend tels quels ceux déjà connus (invariant).

    Formats : urlsafe (token_urlsafe(32)) ou b64 (base64 standard de 32 octets —
    ex. clé de signature ed25519 Matrix, dont le seed EST la clé privée).
    """
    import base64

    from ..catalogue import iter_secret_specs

    vault: dict[str, str] = dict((existing or {}).get("secrets", {}))
    for brick in ordered:
        for name, fmt in iter_secret_specs(brick):
            if name in vault:
                continue
            raw = pysecrets.token_bytes(32)
            if fmt == "b64":
                vault[name] = base64.b64encode(raw).decode()  # 44 caractères standard
            else:
                vault[name] = pysecrets.token_urlsafe(32)
    return vault


# ---------------------------------------------------------------------------
# Rendu


def render_template(value: str, answers: dict) -> str:
    """Substitue les jetons non sensibles ({domain}, {brand_name}).

    Les jetons {secret:…} restent tels quels dans les brouillons committables :
    les valeurs réelles vivent dans secrets.env (gitignoré) et ne sont
    substituées qu'au déploiement (modèle st-cli : refs commitées + coffre).
    """
    rendered = str(value).replace("{domain}", answers["domain"])
    return rendered.replace("{brand_name}", answers["brand_name"])


def render_env(brick: Brick, answers: dict) -> str:
    lines = [
        f"# lastarter — brouillon d'environnement pour la brique « {brick.name} ».",
        "# Généré par `lastarter init` — à ajuster puis versionner.",
        "# Les jetons {secret:…} sont substitués au déploiement depuis secrets.env",
        "# (jamais committé en clair).",
        "",
    ]
    merged = dict(brick.branding_env)
    merged.update(brick.env)
    for key, value in merged.items():
        lines.append(f"{key}={render_template(value, answers)}")
    return "\n".join(lines) + "\n"


def toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_manifest(ordered: list[Brick], answers: dict, created: str) -> str:
    lines = [
        "# Généré par lastarter-cli — ne pas éditer à la main.",
        "# Pour modifier : rejouer `lastarter init` (réponses pré-remplies).",
        "",
        "[client]",
        f"name = {toml_value(answers['client_name'])}",
        f"slug = {toml_value(answers['client_slug'])}",
        f"domain = {toml_value(answers['domain'])}",
        f"brand_name = {toml_value(answers['brand_name'])}",
        f"created = {toml_value(created)}",
        f"cli_version = {toml_value(__version__)}",
        "",
    ]
    for brick in ordered:
        lines += [
            f"[bricks.{brick.name}]",
            f"title = {toml_value(brick.title)}",
            f"pin = {toml_value(brick.upstream_pin)}",
            f"license = {toml_value(brick.license)}",
            f"upstream = {toml_value(brick.upstream_repo)}",
            "",
        ]
    return "\n".join(lines)


def render_sources(ordered: list[Brick]) -> str:
    copyleft = {"AGPL-3.0", "GPL-3.0"}
    lines = [
        "# Mentions sources (conformité licences)",
        "",
        "Chaque brique est déployée **non modifiée**, épinglée à la version ci-dessous.",
        "Pour les licences copyleft (AGPL/GPL), ce document constitue l'offre de source",
        "de la version exacte servie ; toute modification éventuelle serait publiée et",
        "référencée ici (cf. docs/licences.md du dépôt LaStarter).",
        "",
        "| Brique | Licence | Version épinglée | Source |",
        "|---|---|---|---|",
    ]
    for brick in ordered:
        lines.append(
            f"| {brick.title} | {brick.license} | {brick.upstream_pin} | {brick.upstream_repo} |"
        )
    lines += [
        "",
        "Marques : « La Suite », « Element », « Tchap » et logos associés appartiennent à",
        "leurs titulaires et n'apparaissent pas dans les interfaces livrées (branding",
        "LaStarter / client final). Les notices de copyright amont restent dans les",
        "fichiers sources et ce document.",
        "",
    ]
    return "\n".join(lines)


def render_readme(ordered: list[Brick], answers: dict) -> str:
    lines = [
        f"# Déploiement « {answers['client_name']} »",
        "",
        f"- Domaine : {answers['domain']}",
        f"- Marque : {answers['brand_name']}",
        f"- Briques : {', '.join(b.name for b in ordered)}",
        "",
        "## Contenu",
        "",
        "- `lastarter.toml` — manifeste du déploiement (versions épinglées).",
        "- `answers.json` — réponses du questionnaire (rejeu `lastarter init`).",
        "- `env/<brique>.env` — brouillons d'environnement committables (jetons `{secret:…}` substitués au déploiement depuis `secrets.env`).",
        "- `secrets.env` — secrets réels : **ne jamais commiter** (chiffrer : SOPS/ansible-vault, phase 3).",
        "- `SOURCES.md` — mentions licences (obligation copyleft).",
        "",
        "## Étapes suivantes (phase 2)",
        "",
        "1. Ajuster `env/*.env` si besoin (valeurs par défaut issues du catalogue).",
        "2. `lastarter deploy` (à venir) : compose + realm Keycloak provisionné.",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Point d'entrée


def run_init(opts) -> int:
    """Point d'entrée `lastarter init` (opts = argparse namespace de main.build_parser)."""

    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé (lancer depuis le dépôt LaStarter).", file=sys.stderr)
        return 1
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        for error in errors:
            print(f"catalogue invalide : {error}", file=sys.stderr)
        return 1

    deployments_root = (
        Path(opts.output) if opts.output else catalogue_dir.parent / "deployments"
    )
    answers = gather_answers(
        bricks,
        deployments_root,
        opts.client,
        opts.domain,
        opts.brand,
        [b.strip() for b in opts.bricks.split(",")] if opts.bricks else None,
        opts.non_interactive,
        opts.all,
    )

    existing = load_answers(deployments_root / answers["client_slug"])
    ordered_names, added = resolve_selection(answers["bricks"], bricks)
    ordered = [bricks[name] for name in ordered_names]
    if added:
        print(f"Briques ajoutées automatiquement (dépendances/fondation) : {', '.join(added)}")
    for name in answers["bricks"]:
        if bricks[name].maturity == "planned" and not opts.all:
            print(
                f"avertissement : {name} est 'planned' (phase future) — "
                "config générée à titre de préparation.",
            )

    # Le coffre (secrets.env, gitignoré) est l'unique source des secrets :
    # answers.json est committable et ne doit jamais en contenir.
    target = deployments_root / answers["client_slug"]
    vault = generate_secrets(ordered, {"secrets": parse_secrets_env(target / "secrets.env")})
    answers["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    (target / "env").mkdir(parents=True, exist_ok=True)

    (target / "answers.json").write_text(
        json.dumps(answers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (target / "lastarter.toml").write_text(
        render_manifest(ordered, answers, answers["generated_at"]), encoding="utf-8"
    )
    (target / "SOURCES.md").write_text(render_sources(ordered), encoding="utf-8")
    (target / "README.md").write_text(render_readme(ordered, answers), encoding="utf-8")
    for brick in ordered:
        (target / "env" / f"{brick.name}.env").write_text(
            render_env(brick, answers), encoding="utf-8"
        )
    secrets_header = (
        "# SECRETS GENERES PAR lastarter-cli — NE JAMAIS COMMITER.\n"
        "# A chiffrer (SOPS / ansible-vault) avant tout partage. Phase 3 : backend secrets.\n"
        "# Invariant : les valeurs existantes ne sont JAMAIS modifiées ; les secrets\n"
        "# nouveaux (cataloge enrichi) sont ajoutés en fin de fichier (append-only).\n"
    )
    secrets_path = target / "secrets.env"
    if not secrets_path.is_file():
        body = "\n".join(f"{k}={v}" for k, v in sorted(vault.items()))
        secrets_path.write_text(secrets_header + body + "\n", encoding="utf-8")
    else:
        # Croissance append-only : aucun secret existant n'est réécrit/régénéré.
        existing_keys = {
            line.partition("=")[0].strip()
            for line in secrets_path.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.lstrip().startswith("#")
        }
        new_lines = [f"{k}={v}" for k, v in sorted(vault.items()) if k not in existing_keys]
        if new_lines:
            with secrets_path.open("a", encoding="utf-8") as handle:
                handle.write("\n".join(new_lines) + "\n")

    print(f"\nDéploiement généré : {target}")
    print(f"Briques : {', '.join(ordered_names)}")
    print("Prochaine étape : ajuster env/*.env puis (phase 2) `lastarter deploy`.")
    return 0
