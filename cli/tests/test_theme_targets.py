"""Tests des cibles d'habillage dérivées d'UNE palette (themes/*.toml).

Couvert ici :
- thème custom NATIF Element Web (custom_themes.compound, default_theme) ;
- JSON THEME_CUSTOMIZATION_FILE_PATH drive (structure amont exacte) ;
- monogramme SVG par défaut (branding out-of-the-box).
"""

from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from lastarter_cli.cmd.theme import (
    ThemeError,
    build_custom_theme,
    build_drive_theme_customization,
    default_logo_svg,
)

REPO = Path(__file__).resolve().parent.parent.parent  # lastarter/


class CustomThemeTests(unittest.TestCase):
    """Thème custom Element Web : compound dérivé du gabarit CSS (une source)."""

    def test_custom_theme_light(self):
        theme = build_custom_theme(REPO, "element-light")
        self.assertEqual(theme["name"], "element-light")
        self.assertFalse(theme["is_dark"])
        compound = theme["compound"]
        self.assertTrue(compound)
        for key, value in compound.items():
            self.assertTrue(key.startswith("--cpd-color-"), key)
            self.assertTrue(value.startswith("#"), key)
        # Mapping pris sur identity/theme.css.tpl : mêmes valeurs que le CSS.
        self.assertEqual(compound.get("--cpd-color-green-700"), "#0bc491")
        self.assertEqual(compound.get("--cpd-color-gray-100"), "#fbfcfd")

    def test_custom_theme_dark(self):
        theme = build_custom_theme(REPO, "element-dark")
        self.assertTrue(theme["is_dark"])
        self.assertEqual(theme["compound"].get("--cpd-color-green-700"), "#005a43")
        # Canvas sombre : token {{canvas}} du gabarit résolu depuis [theme].
        self.assertEqual(theme["compound"].get("--cpd-color-bg-canvas-default"), "#101317")

    def test_theme_inexistant_leve_erreur(self):
        with self.assertRaises(ThemeError):
            build_custom_theme(REPO, "inexistant")


class ElementConfigInjectionTests(unittest.TestCase):
    """Injection custom_themes + default_theme dans la config discussions rendue."""

    def test_config_rendue_contient_theme_custom_valide(self):
        from lastarter_cli.cmd.deploy import render_discussions_element_config

        template = (REPO / "identity" / "element-discussions-config.json").read_text(encoding="utf-8")
        rendered = render_discussions_element_config(
            template,
            {"domain": "localhost:8443", "brand_name": "Acme", "theme": "element-light"},
            REPO,
        )
        config = json.loads(rendered)  # le rendu reste du JSON valide
        # Jetons d'origine substitués (comportement existant préservé).
        self.assertEqual(
            config["default_server_config"]["m.homeserver"]["base_url"],
            "https://chat.localhost:8443",
        )
        self.assertEqual(config["brand"], "Acme")
        # Mécanisme natif amont (docs/theming.md) : compound est un FRÈRE de
        # colors au niveau du thème custom, clés = variables --cpd-color-*.
        custom = config["setting_defaults"]["custom_themes"][0]
        self.assertEqual(custom["name"], "element-light")
        self.assertFalse(custom["is_dark"])
        self.assertIn("--cpd-color-green-700", custom["compound"])
        self.assertNotIn("compound", custom.get("colors", {}))
        # Nommage amont : un thème custom est référencé « custom-<name> ».
        self.assertEqual(config["default_theme"], "custom-element-light")


class DriveCustomizationTests(unittest.TestCase):
    """JSON THEME_CUSTOMIZATION_FILE_PATH drive — structure amont exacte."""

    def test_structure_conforme_au_modele_amont(self):
        data = build_drive_theme_customization(
            "ACME",
            "https://acme.example.com",
            "https://drive.acme.example.com/__lastarter/branding/logo.svg",
        )
        footer = data["footer"]
        # Repli hors langue « default » + bloc « fr » (cf. default.json amont).
        self.assertIn("default", footer)
        self.assertIn("fr", footer)
        for locale in ("default", "fr"):
            self.assertIn("license", footer[locale])
            self.assertIn("label", footer[locale]["license"])
            self.assertIn("href", footer[locale]["license"]["link"])
        # Clés FooterProps amont (@gouvfr-lasuite/ui-components).
        self.assertEqual(footer["default"]["externalLinks"][0]["label"], "ACME")
        self.assertEqual(
            footer["default"]["logo"]["src"],
            "https://drive.acme.example.com/__lastarter/branding/logo.svg",
        )
        self.assertEqual(footer["default"]["logo"]["alt"], "ACME")
        self.assertIn("legalLinks", footer["fr"])
        json.dumps(data, ensure_ascii=False)  # sérialisable

    def test_sans_logo_pas_de_cle_logo(self):
        data = build_drive_theme_customization("ACME", "https://a.example.com")
        self.assertNotIn("logo", data["footer"]["default"])
        self.assertIn("externalLinks", data["footer"]["default"])


class DefaultLogoTests(unittest.TestCase):
    def test_monogramme_svg_valide(self):
        svg = default_logo_svg("Acme Corp", "#0bc491")
        root = ET.fromstring(svg)  # XML valide
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn(">A</text>", svg)  # monogramme = 1re lettre
        self.assertIn("#0bc491", svg)  # couleur = primaire de la palette

    def test_monogramme_echappe_le_nom(self):
        svg = default_logo_svg("<&>", "#0bc491")
        ET.fromstring(svg)  # caractères XML spéciaux échappés


if __name__ == "__main__":
    unittest.main()
