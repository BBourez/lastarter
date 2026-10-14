"""Point d'entrée lastarter-cli — argparse pur stdlib, zéro dépendance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .cmd import deploy as cmd_deploy
from .cmd import detect as cmd_detect
from .cmd import init as cmd_init
from .cmd import licenses as cmd_licenses
from .cmd import smoke as cmd_smoke
from .cmd.deploy import DeployError


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
    init.add_argument("--theme", help="Thème visuel (ex. element-light, element-dark — cf. themes/)")
    init.add_argument("--brand-color", dest="brand_color", help="Couleur de marque en hex (ex. #0bc491)")
    init.add_argument("--logo-url", dest="logo_url", help="URL du logo client (affiché dans le portail)")

    sub.add_parser("list", help="Lister les briques du catalogue")

    deploy = sub.add_parser("deploy", help="Déployer un client (docker compose, gates puis up --wait)")
    deploy.add_argument("--client", required=True, help="Slug du déploiement (ex. demo-coop)")
    deploy.add_argument("--pull", action="store_true", help="docker compose pull avant le déploiement")
    deploy.add_argument("--down", action="store_true", help="Arrêter le déploiement (volumes conservés)")

    ps = sub.add_parser("ps", help="État des conteneurs d'un déploiement")
    ps.add_argument("--client", required=True, help="Slug du déploiement")

    detect = sub.add_parser("detect", help="Audit d'environnement : IP, Docker, k8s, DNS, ports")
    detect.add_argument("--domain", help="Domaine cible (résolution DNS des sous-domaines)")
    detect.add_argument("--public-ip", action="store_true", help="Détecter aussi l'IP publique (api.ipify.org)")

    sub.add_parser("licenses", help="Gate licence : bloquer toute brique hors liste blanche")

    smoke = sub.add_parser("smoke", help="Vérifier chaque surface d'un déploiement (post-release)")
    smoke.add_argument("--client", required=True, help="Slug du déploiement")

    sbom = sub.add_parser("sbom", help="Générer l'inventaire CycloneDX des briques épinglées")
    sbom.add_argument("--client", required=True, help="Slug du déploiement")
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
    try:
        if opts.command == "init":
            return cmd_init.run_init(opts)
        if opts.command == "deploy":
            return cmd_deploy.run_deploy(opts)
        if opts.command == "ps":
            return cmd_deploy.run_ps(opts)
        if opts.command == "detect":
            return cmd_detect.run_detect(opts)
        if opts.command == "licenses":
            return cmd_licenses.run_licenses(opts)
        if opts.command == "smoke":
            return cmd_smoke.run_smoke(opts)
        if opts.command == "sbom":
            return cmd_smoke.run_sbom(opts)
        if opts.command == "list":
            return run_list()
    except (DeployError, KeyError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
