"""`lastarter check-updates` — veille amont, zéro dépendance (urllib stdlib).

Pour chaque brique du catalogue (champs `upstream_repo` + `upstream_pin`),
interroge l'API GitHub et rend un rapport {brique, pin, latest, a_jour} :

- repos suitenumerique : PAS de releases publiées → endpoint /tags ;
- repos element-hq : releases publiées → endpoint /releases (tag_name) ;
- les pré-releases sont exclues (`-pre`, `-preprod`, `-rcN` — le « latest »
  lasuite est une preprod, on ne veut JAMAIS la proposer) ;
- comparaison sémantique via un mini-parseur semver stdlib (vX.Y.Z).

La commande N'ÉCRIT RIEN : elle est la source du workflow CI de veille.
Le fetcher est injectable (`check_updates(bricks, fetcher=…)`) pour les tests
offline — aucun appel réseau en test.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from ..catalogue import find_catalogue, load_catalogue

GITHUB_API = "https://api.github.com"
_REPO_RE = re.compile(r"https?://github\.com/([^/]+)/([^/]+?)/?$")


class UpdatesError(Exception):
    """Erreur attendue de la veille amont — remontée propre en exit 1."""


# ---------------------------------------------------------------------------
# Mini-parseur semver (stdlib)


def parse_version(pin: str) -> tuple[int, ...] | None:
    """'v1.12.32' → (1, 12, 32) ; None si la version n'est pas sémantique.

    Tolère le préfixe v/V, un suffixe de build (+…) et un suffixe de
    pré-release (-…) — seuls les composants numériques comparent.
    """
    core = str(pin).strip().lstrip("vV").split("+", 1)[0].split("-", 1)[0]
    parts = core.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def is_prerelease(tag: str) -> bool:
    """Pré-release à exclure de la veille : -pre, -preprod, -rc1, etc.

    « -pre » couvre « -preprod » (préfixe) ; « -rc » couvre « -rc1 ».
    """
    lowered = str(tag).lower()
    return "-pre" in lowered or "-rc" in lowered


def latest_version(tags: list[str]) -> str | None:
    """Tag de version le plus récent (comparaison sémantique), hors pré-releases."""
    best: tuple[int, ...] | None = None
    best_tag: str | None = None
    for tag in tags:
        if is_prerelease(tag):
            continue
        key = parse_version(tag)
        if key is None:
            continue
        if best is None or key > best:
            best, best_tag = key, tag
    return best_tag


# ---------------------------------------------------------------------------
# Interrogation amont


def default_fetcher(url: str) -> list:
    """Fetch GitHub API → liste JSON décodée (injectable pour tests offline)."""
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "lastarter-check-updates/1",
            # Pagination : la 1re page (100 items) suffit pour la veille.
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, list):
        raise UpdatesError(f"réponse inattendue de {url} (liste attendue)")
    return data


def _api_url(repo_url: str, kind: str, api_base: str = GITHUB_API) -> str:
    """https://github.com/owner/repo → API /tags ou /releases (100 premiers)."""
    match = _REPO_RE.match(str(repo_url).strip())
    if not match:
        raise UpdatesError(f"repo amont non GitHub : {repo_url}")
    return f"{api_base}/repos/{match.group(1)}/{match.group(2)}/{kind}?per_page=100"


def check_updates(bricks: dict, fetcher=None, api_base: str = GITHUB_API) -> list[dict]:
    """Compare chaque pin du catalogue au dernier tag/release amont.

    fetcher : callable url -> liste JSON (défaut : default_fetcher, urllib).
    Retourne [{brique, pin, latest, a_jour}] trié par nom de brique.
    N'écrit RIEN — la commande est la source du workflow CI de veille.
    """
    fetch = fetcher or default_fetcher
    rows: list[dict] = []
    for name in sorted(bricks):
        brick = bricks[name]
        # suitenumerique ne publie pas de releases (tags seuls) ; element-hq oui.
        kind = "releases" if "element-hq" in str(brick.upstream_repo) else "tags"
        try:
            entries = fetch(_api_url(brick.upstream_repo, kind, api_base))
        except urllib.error.HTTPError as exc:
            raise UpdatesError(f"{name} : HTTP {exc.code} sur {kind} amont") from exc
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            raise UpdatesError(f"{name} : interrogation amont impossible ({exc})") from exc
        tags = [e.get("tag_name") or e.get("name") or "" for e in entries if isinstance(e, dict)]
        latest = latest_version(tags) or ""
        pin_key, latest_key = parse_version(brick.upstream_pin), parse_version(latest)
        rows.append(
            {
                "brique": name,
                "pin": str(brick.upstream_pin),
                "latest": latest,
                "a_jour": bool(latest_key is not None and pin_key == latest_key),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Point d'entrée


def run_check_updates(opts, fetcher=None) -> int:
    """Point d'entrée `lastarter check-updates` (--json, --strict)."""
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé (lancer depuis le dépôt LaStarter).", file=sys.stderr)
        return 1
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        for error in errors:
            print(f"catalogue invalide : {error}", file=sys.stderr)
        return 1

    try:
        rows = check_updates(bricks, fetcher=fetcher)
    except UpdatesError as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1

    if getattr(opts, "json", False):
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"Veille amont — {len(rows)} briques (GitHub, pré-releases exclues)")
        print(f"  {'brique':<14} {'pin':<12} {'latest':<12} statut")
        print("  " + "-" * 56)
        for row in rows:
            if row["a_jour"]:
                status = "à jour"
            elif row["latest"]:
                status = "À METTRE À JOUR"
            else:
                status = "pin non comparable"
            print(f"  {row['brique']:<14} {row['pin']:<12} {row['latest']:<12} {status}")

    outdated = [row["brique"] for row in rows if not row["a_jour"]]
    if getattr(opts, "strict", False) and outdated:
        print(
            f"\n--strict : {len(outdated)} brique(s) en retard : {', '.join(outdated)}",
            file=sys.stderr,
        )
        return 1
    return 0
