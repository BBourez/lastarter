"""Tests gate licence + SBOM — stdlib, offline (smoke live = recette)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from lastarter_cli.cmd.licenses import gate, license_allowed
from lastarter_cli.catalogue import load_catalogue

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_DIR = Path(__file__).resolve().parents[1]


class LicenseGateTests(unittest.TestCase):
    def setUp(self):
        self.bricks, self.errors = load_catalogue(REPO_ROOT / "catalogue")
        self.assertEqual(self.errors, [])

    def test_licences_autorisees(self):
        self.assertTrue(license_allowed("MIT"))
        self.assertTrue(license_allowed("Apache-2.0"))
        self.assertTrue(license_allowed("AGPL-3.0-only"))
        self.assertTrue(license_allowed("AGPL-3.0 OR GPL-3.0 OR Element-Commercial"))
        self.assertFalse(license_allowed("Proprietary"))
        self.assertFalse(license_allowed(""))
        # Comparaison EXACTE : ni préfixe, ni sous-chaîne, ni multilicence partielle.
        self.assertFalse(license_allowed("GPL-3.0-or-later"))
        self.assertFalse(license_allowed("AGPL-3.0-only-or-later"))
        self.assertFalse(license_allowed("AGPL-3.0 OR GPL-3.0"))
        self.assertFalse(license_allowed("AGPL-3.0 OR n'importe quoi"))
        self.assertFalse(license_allowed("MIT-or-later"))

    def test_catalogue_complet_conforme(self):
        ok, rejected = gate(self.bricks)
        self.assertEqual(rejected, [])
        self.assertEqual(set(ok), set(self.bricks))

    def test_brique_hors_liste_rejetee(self):
        rogue = dict(self.bricks)
        # Cloner keycloak (la seule brique) avec une licence propriétaire.
        base = self.bricks["keycloak"]
        rogue["rogue"] = type(base)(
            **{**base.__dict__, "name": "rogue", "license": "Proprietary"}
        )
        ok, rejected = gate(rogue)
        self.assertIn("rogue", " ".join(rejected))
        self.assertNotIn("rogue", ok)


class SbomIntegrationTests(unittest.TestCase):
    """Test SBOM : nécessite un déploiement existant. Skip si absent."""

    @unittest.skip("SBOM : test d'intégration — rejouer après un deploy complet")
    def test_sbom_genere_cyclonedx(self):
        deployment = REPO_ROOT / "deployments" / "demo-coop"
        if not deployment.is_dir():
            self.skipTest("pas de déploiement demo-coop (init pas encore joué)")
        result = subprocess.run(
            [sys.executable, "-m", "lastarter_cli", "sbom", "--client", "demo-coop"],
            capture_output=True, text=True, cwd=CLI_DIR,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        sbom_path = deployment / "sbom.json"
        sbom = json.loads(sbom_path.read_text(encoding="utf-8"))
        self.assertEqual(sbom["bomFormat"], "CycloneDX")
        names = {c["name"] for c in sbom["components"]}
        self.assertIn("keycloak", names)
        for component in sbom["components"]:
            self.assertTrue(component["version"])
            self.assertTrue(component["licenses"][0]["license"]["id"])
            self.assertTrue(component["externalReferences"][0]["url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
