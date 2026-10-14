"""Tests offline du catalogue et des writers d'init — stdlib unittest uniquement."""

from __future__ import annotations

import json
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
            {"keycloak", "drive", "meet", "synapse", "element-web", "transfers"},
        )

    def test_keycloak_is_core_foundation(self):
        self.assertTrue(self.bricks["keycloak"].core)
        self.assertEqual(self.bricks["keycloak"].requires, [])

    def test_drive_is_stable_and_requires_keycloak(self):
        drive = self.bricks["drive"]
        self.assertTrue(drive.is_selectable)
        self.assertEqual(drive.requires, ["keycloak"])

    def test_chat_bricks_are_planned(self):
        self.assertEqual(self.bricks["synapse"].maturity, "planned")
        self.assertEqual(self.bricks["element-web"].maturity, "planned")
        self.assertEqual(self.bricks["element-web"].requires, ["synapse"])

    def test_resolve_selection_adds_core_and_dependencies(self):
        ordered, added = resolve_selection(["drive"], self.bricks)
        self.assertEqual(ordered, ["keycloak", "drive"])
        self.assertEqual(added, ["keycloak"])

    def test_resolve_selection_orders_dependency_chain(self):
        ordered, added = resolve_selection(["element-web"], self.bricks)
        self.assertEqual(ordered, ["keycloak", "synapse", "element-web"])
        self.assertIn("keycloak", added)
        self.assertIn("synapse", added)

    def test_resolve_selection_rejects_unknown_brick(self):
        with self.assertRaises(KeyError):
            resolve_selection(["inconnue"], self.bricks)

    def test_secret_names_extracted_from_env(self):
        self.assertEqual(
            set(secret_names(self.bricks["drive"])),
            {
                "django_secret_key",
                "django_superuser_password",
                "drive_db_password",
                "s3_secret_key",
                "oidc_client_secret",
            },
        )
        self.assertEqual(
            set(secret_names(self.bricks["keycloak"])),
            {"kc_admin_password", "kc_db_password", "demo_user_password"},
        )


class WriterTests(unittest.TestCase):
    def setUp(self):
        self.catalogue_dir = REPO_ROOT / "catalogue"
        self.bricks, _ = load_catalogue(self.catalogue_dir)
        self.answers = {
            "client_name": "Demo Coop",
            "client_slug": "demo-coop",
            "domain": "demo.coop.example.com",
            "brand_name": "LaStarter",
        }

    def test_slugify_handles_accents_and_case(self):
        self.assertEqual(slugify("Démo Coop — 2026"), "demo-coop-2026")
        self.assertEqual(slugify("ACME"), "acme")

    def test_generate_secrets_never_regenerates(self):
        names, _ = resolve_selection(["drive"], self.bricks)
        ordered = [self.bricks[n] for n in names]
        first = generate_secrets(ordered, None)
        existing = {"secrets": dict(first)}
        second = generate_secrets(ordered, existing)
        self.assertEqual(first, second)

    def test_render_env_keeps_secret_tokens_out_of_committable_drafts(self):
        names, _ = resolve_selection(["drive"], self.bricks)
        ordered = [self.bricks[n] for n in names]
        generate_secrets(ordered, None)  # le coffre existe, mais n'est pas injecté
        rendered = render_env(self.bricks["drive"], self.answers)
        self.assertIn("DJANGO_ALLOWED_HOSTS={app_host}", rendered)
        self.assertIn("OIDC_RP_CLIENT_SECRET={secret:oidc_client_secret}", rendered)
        self.assertNotIn("{origin}=", rendered)  # jetons déploy (pas subst. à l'init)
        self.assertIn("DJANGO_EMAIL_BRAND_NAME=LaStarter", rendered)

    def test_render_template_substitutes_placeholders_except_secrets(self):
        self.assertEqual(
            render_template("https://{domain}/a", self.answers),
            "https://demo.coop.example.com/a",
        )
        self.assertEqual(render_template("x={secret:absent}", self.answers), "x={secret:absent}")

    def test_manifest_is_valid_toml(self):
        names, _ = resolve_selection(["drive"], self.bricks)
        ordered = [self.bricks[n] for n in names]
        manifest = render_manifest(ordered, self.answers, "2026-01-01T00:00:00+00:00")
        parsed = tomllib.loads(manifest)
        self.assertEqual(parsed["client"]["domain"], "demo.coop.example.com")
        self.assertEqual(parsed["bricks"]["drive"]["license"], "MIT")
        self.assertEqual(parsed["bricks"]["keycloak"]["pin"], "26.3.2")

    def test_answers_roundtrip_via_json(self):
        encoded = json.dumps(self.answers, ensure_ascii=False)
        self.assertEqual(json.loads(encoded)["client_name"], "Demo Coop")

    def test_find_catalogue_from_repo_root(self):
        self.assertEqual(find_catalogue(REPO_ROOT), self.catalogue_dir)


if __name__ == "__main__":
    unittest.main()
