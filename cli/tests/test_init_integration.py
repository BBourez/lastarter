"""Tests d'intégration d'`init` — sous-processus, invariants de sécurité du coffre."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

CLI_DIR = Path(__file__).resolve().parents[1]

from lastarter_cli.cmd.init import parse_secrets_env  # noqa: E402


class ParseSecretsEnvTests(unittest.TestCase):
    def test_parses_kv_and_ignores_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "secrets.env"
            path.write_text(
                "# en-tête\nA=1\n\nB = deux mots \n.pas_un_kv\n", encoding="utf-8"
            )
            self.assertEqual(parse_secrets_env(path), {"A": "1", "B": "deux mots"})

    def test_missing_file_returns_empty(self):
        self.assertEqual(parse_secrets_env(Path("nulle/part.env")), {})


class InitIntegrationTests(unittest.TestCase):
    def _run_init(self, deployments: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable, "-m", "lastarter_cli", "init",
                "--non-interactive",
                "--client", "Demo Coop",
                "--domain", "demo.coop.example.com",
                "--bricks", "drive",
                "--output", str(deployments),
            ],
            capture_output=True, text=True, cwd=CLI_DIR,
        )

    def test_init_twice_keeps_vault_stable_and_answers_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            deployments = Path(tmp) / "deployments"
            first = self._run_init(deployments)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = deployments / "demo-coop"

            # answers.json est committable : aucun secret dedans.
            answers = json.loads((target / "answers.json").read_text(encoding="utf-8"))
            self.assertNotIn("secrets", answers)

            # secrets.env est la seule source des valeurs.
            secrets_before = (target / "secrets.env").read_text(encoding="utf-8")
            self.assertIn("kc_admin_password=", secrets_before)

            # Les brouillons committables ne contiennent que des jetons.
            drive_env = (target / "env" / "drive.env").read_text(encoding="utf-8")
            self.assertIn("OIDC_RP_CLIENT_SECRET={secret:oidc_client_secret}", drive_env)
            for line in secrets_before.splitlines():
                if "=" in line and not line.startswith("#"):
                    _, _, value = line.partition("=")
                    self.assertNotIn(value, drive_env)

            # Le manifeste est un TOML valide avec les briques résolues.
            manifest = tomllib.loads((target / "lastarter.toml").read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["bricks"]), {"keycloak", "drive"})

            # Rejeu : le coffre est inchangé (jamais re-généré).
            second = self._run_init(deployments)
            self.assertEqual(second.returncode, 0, second.stderr)
            secrets_after = (target / "secrets.env").read_text(encoding="utf-8")
            self.assertEqual(secrets_before, secrets_after)


if __name__ == "__main__":
    unittest.main()
