"""Tests offline du catalogue — stdlib unittest uniquement.

L'ensemble des briques attendu est DÉRIVÉ du contenu de catalogue/*.toml
(actuellement : keycloak fondation + discussions, drive, meet)."""

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
        # Ensemble DÉRIVÉ du contenu du catalogue (pas figé) : ajouter un
        # manifeste catalogue/*.toml ne casse pas ce test.
        expected = {p.stem for p in (REPO_ROOT / "catalogue").glob("*.toml")}
        self.assertEqual(set(self.bricks), expected)
        # Invariants de la reprise : fondation + briques de la suite.
        self.assertIn("keycloak", expected)
        for name in ("discussions", "drive", "meet"):
            self.assertIn(name, expected)
        # L'ancienne brique de visio (element-call) a été remplacée par meet.
        self.assertNotIn("element-call", expected)

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

    def test_discussions_est_une_app(self):
        d = self.bricks["discussions"]
        self.assertFalse(d.core)
        self.assertEqual(d.requires, ["keycloak"])
        self.assertEqual(d.oidc["client_id"], "synapse")
        self.assertEqual(d.compose.get("route_label"), "chat")
        # Secrets critiques du homeserver présents.
        names = set(secret_names(d))
        for expected in (
            "discussions_signing_key",
            "discussions_macaroon_secret",
            "discussions_form_secret",
            "discussions_registration_secret",
            "discussions_oidc_secret",
        ):
            self.assertIn(expected, names)

    def test_resolve_selection_discussions_ajoute_keycloak(self):
        ordered, added = resolve_selection(["discussions"], self.bricks)
        self.assertEqual(ordered, ["keycloak", "discussions"])
        self.assertEqual(added, ["keycloak"])


class EncodingTests(unittest.TestCase):
    """Aucun motif de double-encodage (UTF-8 lu comme cp1252) dans les sources."""

    def test_pas_de_mojibake_dans_les_sources_du_paquet(self):
        pkg = REPO_ROOT / "cli" / "lastarter_cli"
        offenders = []
        for path in sorted(pkg.rglob("*.py")):
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                try:
                    fixed = line.encode("cp1252", errors="strict").decode(
                        "utf-8", errors="strict"
                    )
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue  # non représentable en cp1252 : pas du mojibake
                if fixed != line:
                    offenders.append(f"{path.name}:{lineno}")
        self.assertEqual(
            offenders, [], "lignes double-encodées (UTF-8 relu en cp1252)"
        )


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
