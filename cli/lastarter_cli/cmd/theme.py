"""Rendu du thème LaStarter — UNE palette themes/<nom>.toml, PLUSIEURS cibles.

Cibles générées depuis la même source de vérité :
1. theme.css (identity/theme.css.tpl) injecté par la passerelle (sub_filter) ;
2. le thème custom NATIF d'Element Web (discussions) : setting_defaults
   .custom_themes[{name, is_dark, compound}] + default_theme "custom-<nom>"
   (docs/theming.md amont) — les clés compound (--cpd-color-*) sont dérivées
   du MÊME gabarit que le CSS, donc toujours cohérentes ;
3. le JSON THEME_CUSTOMIZATION_FILE_PATH amont drive (docs/customization.md)
   : footer {default, fr} aux clés FooterProps (externalLinks/legalLinks/
   license/logo) ;
4. le logo par défaut (monogramme SVG) servi par la passerelle sur
   /__lastarter/branding/.

Aucun patch code amont : uniquement des mécanismes natifs par config/env.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from xml.sax.saxutils import escape

class ThemeError(Exception):
    """Erreur de chargement ou de rendu de thème."""


def load_theme(repo_root: Path, theme_name: str) -> dict:
    """Charge themes/<nom>.toml ; Erreur claire si absent."""
    theme_path = repo_root / "themes" / f"{theme_name}.toml"
    if not theme_path.is_file():
        available = [
            p.stem for p in (repo_root / "themes").glob("*.toml") if p.stem != "README"
        ]
        raise ThemeError(
            f"thème « {theme_name} » introuvable (disponibles : {', '.join(sorted(available)) or 'aucun'})"
        )
    with theme_path.open("rb") as fh:
        return tomllib.load(fh)


def list_themes(repo_root: Path) -> list[dict]:
    """Liste les thèmes disponibles (nom, label) pour l'invite interactive."""
    themes = []
    for path in sorted((repo_root / "themes").glob("*.toml")):
        try:
            with path.open("rb") as fh:
                data = tomllib.load(fh)
            meta = data.get("theme", {})
            themes.append({"name": meta.get("name", path.stem), "label": meta.get("label", path.stem)})
        except (tomllib.TOMLDecodeError, OSError):
            continue  # fichier illisible : ignoré silencieusement dans la liste
    return themes


def _flatten_palette(theme: dict, palette_name: str) -> dict[str, str]:
    """Aplatit [palette.<nom>] en {clé: valeur} (les clés deviennent des strings)."""
    palette = theme.get("palette", {}).get(palette_name, {})
    return {str(k): str(v) for k, v in palette.items()}


def primary_color(theme: dict) -> str:
    """Couleur primaire de la palette (step 700, sinon première valeur)."""
    palette = theme.get("palette", {}).get("primary", {})
    value = palette.get("700") or next(iter(palette.values()), "")
    return str(value or "#0bc491")


# Jetons couleurs du gabarit CSS : `--cpd-color-x: {{token}};` (valeurs littérales
# uniquement — les références var() du gabarit sont dérivées côté navigateur).
_COMPOUND_TOKEN = re.compile(r"(--cpd-color-[a-z0-9-]+)\s*:\s*\{\{([a-z0-9_]+)\}\}\s*;")


def compound_colors(theme: dict, repo_root: Path) -> dict[str, str]:
    """Résout les jetons compound du gabarit CSS depuis la palette TOML.

    Retourne {variable_css: valeur} — ex. {"--cpd-color-green-700": "#0bc491"}.
    Scan de identity/theme.css.tpl : une SEULE source de vérité, le thème custom
    Element Web reste synchronisé avec le CSS injecté par la passerelle.
    """
    template_path = repo_root / "identity" / "theme.css.tpl"
    if not template_path.is_file():
        raise ThemeError(f"gabarit introuvable : {template_path}")
    template = template_path.read_text(encoding="utf-8")
    palettes = theme.get("palette", {})
    canvas = str(theme.get("theme", {}).get("canvas", ""))
    resolved: dict[str, str] = {}
    for variable, token in _COMPOUND_TOKEN.findall(template):
        value = ""
        if token == "canvas":
            value = canvas
        else:
            scale, _, step = token.partition("_")
            value = str(palettes.get(scale, {}).get(step, ""))
        if value.startswith("#"):
            resolved[variable] = value
    return resolved


def build_custom_theme(repo_root: Path, theme_name: str) -> dict:
    """Construit le thème custom NATIF Element Web (docs/theming.md amont).

    Format amont (type CustomTheme, apps/web/src/theme.ts) : {name, is_dark,
    compound} — `compound` est un FRÈRE de `colors` (pas imbriqué dedans) et
    porte les overrides de tokens sémantiques `--cpd-color-*`. Référencé par
    default_theme = "custom-<name>".
    """
    theme = load_theme(repo_root, theme_name)
    meta = theme.get("theme", {})
    compound = compound_colors(theme, repo_root)
    if not compound:
        raise ThemeError(
            f"palette « {theme_name} » : aucun jeton --cpd-color-* résoluble depuis identity/theme.css.tpl"
        )
    return {
        "name": str(meta.get("name", theme_name)),
        "is_dark": bool(meta.get("dark", False)),
        "compound": dict(sorted(compound.items())),
    }


def build_drive_theme_customization(brand_name: str, portal_origin: str, logo_url: str = "") -> dict:
    """Construit le JSON THEME_CUSTOMIZATION_FILE_PATH amont drive.

    Structure EXACTE documentée par l'amont (docs/customization.md +
    src/backend/drive/configuration/theme/default.json) : {"footer": {…}} avec
    un bloc par langue + repli "default" ; les clés internes suivent
    FooterProps amont (@gouvfr-lasuite/ui-components) : externalLinks,
    legalLinks, license {label, link{label, href}}, logo {src, height, alt}.
    """
    license_line = {
        "label": "Propulsé par",
        "link": {"label": brand_name, "href": portal_origin},
    }
    footer_default: dict = {
        "externalLinks": [{"label": brand_name, "href": portal_origin}],
        "license": license_line,
    }
    if logo_url:
        footer_default["logo"] = {"src": logo_url, "height": "32px", "alt": brand_name}
    return {
        "footer": {
            "default": footer_default,
            "fr": {
                "legalLinks": [
                    {"label": "Mentions légales & sources", "href": f"{portal_origin}/sources.html"},
                ],
                "license": license_line,
            },
        },
    }


def default_logo_svg(brand_name: str, color: str) -> str:
    """Monogramme SVG par défaut : 1re lettre du nom de marque sur la couleur
    primaire de la palette — l'habillage fonctionne sans aucun fichier fourni."""
    letter = escape((brand_name or "L").strip()[:1].upper() or "L")
    fill = escape(color or "#0bc491")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64" role="img">\n'
        f'  <rect width="64" height="64" rx="14" fill="{fill}"/>\n'
        '  <text x="32" y="34" text-anchor="middle" dominant-baseline="central" '
        'font-family="Inter, \'Segoe UI\', system-ui, sans-serif" font-size="34" '
        f'font-weight="600" fill="#ffffff">{letter}</text>\n'
        "</svg>\n"
    )


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
