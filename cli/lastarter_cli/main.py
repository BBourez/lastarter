"""Point d'entrée lastarter-cli — argparse pur stdlib, zéro dépendance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .cmd import init as cmd_init


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lastarter",
        description="Installateur modulaire de la suite LaStarter (maquette phase 1).",
    )
    parser.add_argument("--version", action="version", version=f"lastarter-cli {__version__}")

    sub = parser.add_subparsers(dest="command")

    init = sub.add_parser("init", help="Configurer un déploiement client (génère deployments/<client>/)")
    init.add_argument("--client", help="Nom du client (ex. « ACME »)")
    init.add_argument("--domain", help="Domaine principal (ex. acme.example.com)")
    init.add_argument("--brand", default="LaStarter", help="Nom de marque affiché (défaut : LaStarter)")
    init.add_argument("--bricks", help="Briques sélectionnées, séparées par des virgules (ex. drive,meet)")
    init.add_argument("--non-interactive", action="store_true", help="Mode scripté (sans questionnaire)")
    init.add_argument("--all", action="store_true", help="Inclure les briques 'planned' (phases futures)")
    init.add_argument("--output", help="Dossier racine des déploiements (défaut : <repo>/deployments)")

    sub.add_parser("list", help="Lister les briques du catalogue")
    return parser


def run_list() -> int:
    from .catalogue import find_catalogue, load_catalogue

    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé (lancer depuis le dépôt LaStarter).", file=sys.stderr)
        return 1
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        for error in errors:
            print(f"catalogue invalide : {error}", file=sys.stderr)
        return 1

    print(f"Catalogue : {catalogue_dir}")
    print()
    print(f"{'brique':<14} {'catégorie':<16} {'licence':<46} {'maturité':<8} note")
    print("-" * 100)
    for brick in sorted(bricks.values(), key=lambda b: (b.category, b.name)):
        flags = []
        if brick.core:
            flags.append("fondation")
        flags.append("stable" if brick.is_selectable else "planned")
        requires = f"-> {','.join(brick.requires)}" if brick.requires else ""
        print(f"{brick.name:<14} {brick.category:<16} {brick.license:<46} {'/'.join(flags):<8} {requires}")
    print()
    print("Fondation = toujours installée. Sélection via `lastarter init`.")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Sortie déterministe en UTF-8 (consoles Windows cp1252 par défaut).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):  # flux déjà fermés / non reconfigurables
            pass
    parser = build_parser()
    opts = parser.parse_args(argv)
    if opts.command == "init":
        return cmd_init.run_init(opts)
    if opts.command == "list":
        return run_list()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
