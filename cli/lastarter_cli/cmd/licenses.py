"""`lastarter licenses` — gate licence : bloque toute brique hors liste blanche.

Source de vérité : les champs `license` du catalogue. La liste blanche reflète
docs/licences.md (registre validé à la main). Toute divergence (nouvelle brique,
changement de régime d'un amont) fait échouer la CI jusqu'à mise à jour du registre.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ..catalogue import Brick, find_catalogue, load_catalogue

# Licences acceptées, par comparaison EXACTE (valeur complète uniquement — la
# multilicence Element est acceptée comme valeur exacte, pas par préfixe :
# « GPL-3.0-or-later » ou « AGPL-3.0 OR <autre> » ne passent pas). Toute valeur
# non couverte ici doit d'abord passer par une mise à jour motivée de
# docs/licences.md.
ALLOWED_LICENSES = {
    "MIT",
    "Apache-2.0",
    "AGPL-3.0-only",
    "GPL-3.0",
    # Multilicence Element (client chat) : LaStarter choisit AGPL-3.0.
    "AGPL-3.0 OR GPL-3.0 OR Element-Commercial",
}


def license_allowed(value: str) -> bool:
    """Comparaison exacte contre la liste blanche (ni préfixe, ni sous-chaîne)."""
    return value in ALLOWED_LICENSES


def gate(bricks: dict[str, Brick]) -> tuple[list[str], list[str]]:
    """Retourne (ok, rejets). Un rejet = licence hors liste OU absente du registre."""
    registry = Path(find_catalogue(Path.cwd()) or Path.cwd()).parent / "docs" / "licences.md"
    registry_text = registry.read_text(encoding="utf-8") if registry.is_file() else ""
    ok: list[str] = []
    rejected: list[str] = []
    for name, brick in sorted(bricks.items()):
        reasons = []
        if not license_allowed(brick.license):
            reasons.append(f"licence non autorisée : {brick.license}")
        if registry_text and f"`{name}`" not in registry_text:
            reasons.append("absente du registre docs/licences.md")
        if reasons:
            rejected.append(f"{name} — " + " ; ".join(reasons))
        else:
            ok.append(name)
    return ok, rejected


def run_licenses(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé.", file=sys.stderr)
        return 1
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        for error in errors:
            print(f"catalogue invalide : {error}", file=sys.stderr)
        return 1

    ok, rejected = gate(bricks)
    print(f"Gate licence — {len(ok)} briques conformes, {len(rejected)} rejetées")
    for name in ok:
        brick = bricks[name]
        print(f"  ✓ {name:<13} {brick.license}")
    for line in rejected:
        print(f"  ✗ {line}")
    if rejected:
        print(
            "\nBloquant : mettre à jour docs/licences.md (analyse juridique) puis "
            "ALLOWED_LICENSES si la licence est réellement acceptable.",
            file=sys.stderr,
        )
        return 1
    return 0
