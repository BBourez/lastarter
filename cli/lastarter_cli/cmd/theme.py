"""Rendu du thÃ¨me LaStarter (palettes Compound â†’ CSS injectÃ© par la passerelle).

Le thÃ¨me est dÃ©fini dans themes/<nom>.toml (palette, typo, composants).
Le CLI le rend dans .runtime/theme.css en substituant les jetons de
identity/theme.css.tpl. La passerelle sert ce fichier sur /__lastarter/theme.css
sur tous les sous-domaines et l'injecte dans le HTML via nginx sub_filter.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

class ThemeError(Exception):
    """Erreur de chargement ou de rendu de thÃ¨me."""


def load_theme(repo_root: Path, theme_name: str) -> dict:
    """Charge themes/<nom>.toml ; Erreur claire si absent."""
    theme_path = repo_root / "themes" / f"{theme_name}.toml"
    if not theme_path.is_file():
        available = [
            p.stem for p in (repo_root / "themes").glob("*.toml") if p.stem != "README"
        ]
        raise ThemeError(
            f"thÃ¨me Â« {theme_name} Â» introuvable (disponibles : {', '.join(sorted(available)) or 'aucun'})"
        )
    with theme_path.open("rb") as fh:
        return tomllib.load(fh)


def list_themes(repo_root: Path) -> list[dict]:
    """Liste les thÃ¨mes disponibles (nom, label) pour l'invite interactive."""
    themes = []
    for path in sorted((repo_root / "themes").glob("*.toml")):
        try:
            with path.open("rb") as fh:
                data = tomllib.load(fh)
            meta = data.get("theme", {})
            themes.append({"name": meta.get("name", path.stem), "label": meta.get("label", path.stem)})
        except (tomllib.TOMLDecodeError, OSError):
            continue  # fichier illisible : ignorÃ© silencieusement dans la liste
    return themes


def _flatten_palette(theme: dict, palette_name: str) -> dict[str, str]:
    """Aplatit [palette.<nom>] en {clÃ©: valeur} (les clÃ©s deviennent des strings)."""
    palette = theme.get("palette", {}).get(palette_name, {})
    return {str(k): str(v) for k, v in palette.items()}


def render_theme_css(repo_root: Path, theme_name: str, brand: dict) -> str:
    """Rend theme.css : substitue les jetons du template avec la palette + marque.

    brand : {"name": str, "color": str, "logo_url": str}
    """
    theme = load_theme(repo_root, theme_name)
    meta = theme.get("theme", {})
    components = theme.get("components", {})

    context: dict[str, str] = {}
    for pal_name, token_prefix in [
        ("primary", "primary"),
        ("neutral", "neutral"),
        ("info", "info"),
        ("success", "success"),
        ("warning", "warning"),
        ("danger", "danger"),
    ]:
        for key, value in _flatten_palette(theme, pal_name).items():
            # Jeton du template : doubles accolades {{prefix_clé}} — l'entourage
            # est construit par concaténation (f-string doublerait mal).
            context["{{" + f"{token_prefix}_{key}" + "}}"] = value

    context["{{font_family}}"] = meta.get("font_family", "Inter, sans-serif")
    context["{{canvas}}"] = meta.get("canvas", "#ffffff")
    context["{{button_radius}}"] = components.get("button_radius", "8px")
    context["{{button_height}}"] = components.get("button_height", "40px")
    context["{{brand_name}}"] = brand.get("name", "LaStarter")
    context["{{brand_color}}"] = brand.get("color", context.get("{{primary_700}}", "#0bc491"))
    context["{{logo_url}}"] = brand.get("logo_url", "")

    template_path = repo_root / "identity" / "theme.css.tpl"
    template = template_path.read_text(encoding="utf-8")
    rendered = template
    for token, value in context.items():
        rendered = rendered.replace(token, value)
    return rendered
