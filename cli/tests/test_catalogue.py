"""Tests offline du catalogue — stdlib unittest uniquement.
Catalogue CORE : keycloak uniquement (fondation), zéro app."""

from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from lastarter_cli.catalogue import (
    find_catalogue,
    load_catalogue,
    resolve_selection,
    secret_names,
)
from lastarter_cli.cmd.init import (
    generate_secrets,
    render_env,
    render_manifest,
    render_template,
    slugify,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.catalogue_dir = REPO_ROOT / "catalogue"
        self.bricks, self.errors = load_catalogue(self.catalogue_dir)

    def test_catalogue_loads_without_errors(self):
        self.assertEqual(self.errors, [])
        self.assertEqual(
            set(self.bricks),
            {"keycloak"},
        )

    def test_keycloak_is_core_foundation(self):
        self.assertTrue(self.bricks["keycloak"].core)
        self.assertEqual(self.bricks["keycloak"].requires, [])

    def test_keycloak_has_oidc_realm(self):
        kc = self.bricks["keycloak"]
        self.assertTrue(kc.oidc.get("client_id") or kc.core)

    def test_resolve_selection_with_no_apps(self):
        ordered, added = resolve_selection([], self.bricks)
        self.assertEqual(ordered, ["keycloak"])
        self.assertEqual(added, ["keycloak"])

    def test_keycloak_secrets_generated(self):
        names = secret_names(self.bricks["keycloak"])
        self.assertIsInstance(names, list)


class InitWriterTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("ACME Corp"), "acme-corp")
        self.assertEqual(slugify("Héllo Wörld"), "hello-world")

    def test_render_manifest_contains_client_info(self):
        answers = {
            "client_name": "Test",
            "client_slug": "test",
            "domain": "test.example.com",
            "brand_name": "Test",
            "theme": "element-light",
            "brand_color": "#0bc491",
            "logo_url": "",
        }
        manifest = render_manifest([], answers, "2026-01-01T00:00:00Z")
        self.assertIn('name = "Test"', manifest)
        self.assertIn("theme", manifest)


if __name__ == "__main__":
    unittest.main()
