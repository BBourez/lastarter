"""Tests du système de thèmes LaStarter (palettes Compound → CSS injecté)."""

import unittest
from pathlib import Path

from lastarter_cli.cmd.theme import (
    ThemeError,
    list_themes,
    load_theme,
    render_theme_css,
)

REPO = Path(__file__).resolve().parent.parent.parent  # lastarter/


class ThemeLoadingTests(unittest.TestCase):
    def test_liste_les_themes_disponibles(self):
        themes = list_themes(REPO)
        names = [t["name"] for t in themes]
        self.assertIn("element-light", names)
        self.assertIn("element-dark", names)

    def test_theme_inexistant_leve_erreur_claire(self):
        with self.assertRaises(ThemeError) as ctx:
            load_theme(REPO, "inexistant")
        self.assertIn("inexistant", str(ctx.exception))
        self.assertIn("element-light", str(ctx.exception))


class ThemeRenderTests(unittest.TestCase):
    def test_rendu_light_contient_palette_complexe(self):
        css = render_theme_css(
            REPO, "element-light",
            {"name": "Acme Corp", "color": "#0bc491", "logo_url": ""},
        )
        # Pont Cunningham : brand → vert Element.
        self.assertIn("--c--globals--colors--brand-650: #0bc491;", css)
        self.assertIn("--c--globals--colors--brand-700: #0bc491;", css)
        # Logo apps La Suite → couleur de marque.
        self.assertIn("--c--globals--colors--logo-1-light: #0bc491;", css)
        # Typographie Inter.
        self.assertIn("Inter", css)
        # Composants.
        self.assertIn("border-radius: 8px;", css)
        # Marque blanche.
        self.assertIn('--lastarter-brand-name: "Acme Corp";', css)

    def test_rendu_dark_canvas_sombre(self):
        css = render_theme_css(
            REPO, "element-dark",
            {"name": "X", "color": "#0bc491", "logo_url": ""},
        )
        # Canvas sombre Compound dark.
        self.assertIn("--lastarter-canvas: #101317;", css)
        # La palette dark a des valeurs sombres pour primary-700.
        self.assertIn("--c--globals--colors--brand-700: #005a43;", css)

    def test_couleur_marque_personnalisee_remplace_default(self):
        css = render_theme_css(
            REPO, "element-light",
            {"name": "Y", "color": "#ff6b35", "logo_url": ""},
        )
        # brand_color = couleur custom → --lastarter-brand-color.
        self.assertIn("--lastarter-brand-color: #ff6b35;", css)
        # La palette elle-même reste celle du thème (seul brand-color change).
        self.assertIn("--c--globals--colors--brand-650: #0bc491;", css)

    def test_logo_url_dans_variable_css(self):
        css = render_theme_css(
            REPO, "element-light",
            {"name": "Z", "color": "#0bc491", "logo_url": "https://acme.com/l.png"},
        )
        self.assertIn('--lastarter-logo-url: url("https://acme.com/l.png");', css)


class EdgeInjectionTests(unittest.TestCase):
    """Le sub_filter et la location theme.css doivent être dans edge.conf."""

    def test_render_edge_contient_theme_et_subfilter(self):
        from lastarter_cli.cmd.deploy import render_edge
        from lastarter_cli.catalogue import load_catalogue

        bricks, errors = load_catalogue(REPO / "catalogue")
        self.assertEqual(errors, [])
        answers = {
            "domain": "localhost:8443",
            "brand_name": "Test",
        }
        edge = render_edge(list(bricks.values()), answers)
        # Sert le CSS du thème.
        self.assertIn("location = /__lastarter/theme.css", edge)
        # L'injecte dans le HTML.
        self.assertIn("sub_filter", edge)
        self.assertIn("__lastarter/theme.css", edge)


if __name__ == "__main__":
    unittest.main()
