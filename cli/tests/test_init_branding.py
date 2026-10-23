"""Tests offline du branding CLI : `init` (logo, noms d'app) + passerelle.

`init` est exécuté en sous-processus (`--non-interactive --output <tmp>`) :
aucun déploiement réel n'est touché et l'invariant « rejeu conserve » est
vérifié sur un second passage.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_init(args: list[str], output: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, "-m", "lastarter_cli", "init", "--non-interactive",
            "--client", "Brand Test", "--domain", "bt.example.com", "--bricks", "drive",
            "--output", str(output), *args,
        ],
        capture_output=True, text=True, cwd=CLI_DIR,
    )


class InitBrandingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.output = Path(self._tmp.name)

    def test_logo_fourni_et_noms_apps(self):
        logo = self.output / "source.svg"
        logo.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        result = _run_init(
            ["--logo", str(logo), "--app-name-drive", "Espace documents"], self.output
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        deployment = self.output / "brand-test"
        answers = json.loads((deployment / "answers.json").read_text(encoding="utf-8"))
        # Structure brand/apps demandée (+ miroirs rétro-compatibles).
        self.assertEqual(answers["brand"]["name"], "LaStarter")
        self.assertEqual(answers["brand"]["logo_path"], "branding/logo.svg")
        self.assertEqual(answers["apps"]["drive"]["label"], "Espace documents")
        self.assertEqual(answers["brand_name"], "LaStarter")
        # Le logo est COPIÉ (pas référencé) dans branding/.
        self.assertEqual(
            (deployment / "branding" / "logo.svg").read_text(encoding="utf-8"),
            '<svg xmlns="http://www.w3.org/2000/svg"/>',
        )
        # URL par défaut : branding servi par la passerelle sur /__lastarter/.
        self.assertEqual(answers["logo_url"], "/__lastarter/branding/logo.svg")
        # Le manifeste reprend le nom d'affichage.
        manifest = (deployment / "lastarter.toml").read_text(encoding="utf-8")
        self.assertIn('label = "Espace documents"', manifest)

    def test_monogramme_genere_sans_logo(self):
        result = _run_init([], self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        deployment = self.output / "brand-test"
        answers = json.loads((deployment / "answers.json").read_text(encoding="utf-8"))
        self.assertEqual(answers["brand"]["logo_path"], "branding/logo.svg")
        svg = (deployment / "branding" / "logo.svg").read_text(encoding="utf-8")
        self.assertIn("<svg", svg)
        # Monogramme : 1re lettre du nom de marque + couleur primaire de la palette.
        self.assertIn(">L</text>", svg)
        self.assertIn("#0bc491", svg)

    def test_rejeu_conserve_le_logo(self):
        first = _run_init([], self.output)
        self.assertEqual(first.returncode, 0, first.stderr)
        logo = self.output / "brand-test" / "branding" / "logo.svg"
        first_content = logo.read_text(encoding="utf-8")
        # Rejeu avec une autre couleur : le logo existant n'est PAS régénéré.
        second = _run_init(["--brand-color", "#123456"], self.output)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(logo.read_text(encoding="utf-8"), first_content)

    def test_logo_refuse_hors_svg_png(self):
        bad = self.output / "logo.gif"
        bad.write_bytes(b"GIF89a")
        result = _run_init(["--logo", str(bad)], self.output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("svg", (result.stderr + result.stdout).lower())

    def test_logo_png_copie_sous_son_extension(self):
        png = self.output / "source.png"
        # En-tête PNG minimal (le CLI ne valide pas les octets, seulement l'extension).
        png.write_bytes(b"\x89PNG\r\n\x1a\n")
        result = _run_init(["--logo", str(png)], self.output)
        self.assertEqual(result.returncode, 0, result.stderr)
        answers = json.loads(
            (self.output / "brand-test" / "answers.json").read_text(encoding="utf-8")
        )
        self.assertEqual(answers["brand"]["logo_path"], "branding/logo.png")
        self.assertTrue((self.output / "brand-test" / "branding" / "logo.png").is_file())
        self.assertEqual(answers["logo_url"], "/__lastarter/branding/logo.png")


class EdgeBrandingTests(unittest.TestCase):
    """La passerelle sert le branding sur /__lastarter/branding/ (edge + compose)."""

    def test_render_edge_sert_le_branding(self):
        from lastarter_cli.catalogue import load_catalogue
        from lastarter_cli.cmd.deploy import render_edge

        bricks, errors = load_catalogue(REPO_ROOT / "catalogue")
        self.assertEqual(errors, [])
        edge = render_edge(
            list(bricks.values()), {"domain": "localhost:8443", "brand_name": "Test"}
        )
        self.assertIn("location /__lastarter/branding/ {", edge)
        self.assertIn("/var/www/lastarter-theme/branding/", edge)
        # Le theme.css reste injecté (seul sub_filter couleurs restant autorisé).
        self.assertIn("location = /__lastarter/theme.css", edge)
        # Le montage passerelle consomme BRANDING_DIR (deploy/compose).
        compose_text = (REPO_ROOT / "deploy" / "compose" / "keycloak.yml").read_text(encoding="utf-8")
        self.assertIn("${BRANDING_DIR}:/var/www/lastarter-theme/branding", compose_text)


class DriveRenderTests(unittest.TestCase):
    """Rendus drive : FRONTEND_THEME suit la palette, customization écrite."""

    def _vault(self):
        return {
            "drive_oidc_secret": "s3cret",
            "drive_django_key": "k",
            "drive_s3_secret": "v4ult-s3cret",
        }

    def test_backend_env_frontend_theme_parametrable(self):
        from lastarter_cli.cmd.deploy import render_drive_backend_env

        light = render_drive_backend_env({"domain": "localhost:8443"}, self._vault())
        self.assertIn("FRONTEND_THEME=dsfr-light", light)  # défaut inchangé
        dark = render_drive_backend_env(
            {"domain": "localhost:8443"}, self._vault(), frontend_theme="dsfr-dark"
        )
        self.assertIn("FRONTEND_THEME=dsfr-dark", dark)

    def test_backend_env_secret_s3_depuis_coffre(self):
        """Invariant : AWS_S3_SECRET_ACCESS_KEY == vault["drive_s3_secret"].

        drive_rustfs et drive_createbuckets consomment ${DRIVE_S3_SECRET_KEY}
        (même secret du coffre) — une valeur en dur ferait signer les requêtes
        S3 du backend avec une autre clé (403 SignatureDoesNotMatch : uploads,
        listes et /media inutilisables).
        """
        from lastarter_cli.cmd.deploy import DeployError, render_drive_backend_env

        vault = self._vault()
        env = render_drive_backend_env({"domain": "localhost:8443"}, vault)
        self.assertIn(f"AWS_S3_SECRET_ACCESS_KEY={vault['drive_s3_secret']}", env)
        self.assertNotIn("AWS_S3_SECRET_ACCESS_KEY=password", env)
        # rustfs/createbuckets consomment bien le MÊME secret du coffre.
        compose = (REPO_ROOT / "deploy" / "compose" / "drive.yml").read_text(encoding="utf-8")
        self.assertIn("RUSTFS_SECRET_KEY: ${DRIVE_S3_SECRET_KEY}", compose)
        # Secret absent du coffre → erreur explicite (aucune valeur par défaut).
        with self.assertRaises(DeployError):
            render_drive_backend_env(
                {"domain": "localhost:8443"},
                {"drive_oidc_secret": "s3cret", "drive_django_key": "k"},
            )


class CertSanTests(unittest.TestCase):
    """Le certificat POC couvre le domaine apex (portail servi sur https://<domaine>)."""

    def test_san_inclut_apex_id_apps_extras(self):
        from lastarter_cli.catalogue import load_catalogue
        from lastarter_cli.cmd.deploy import cert_san_names_for

        bricks, errors = load_catalogue(REPO_ROOT / "catalogue")
        self.assertEqual(errors, [])
        sans = cert_san_names_for(list(bricks.values()), "localhost:8443")
        self.assertIn("localhost", sans)          # apex nu (portail) — défaut corrigé
        self.assertIn("id.localhost", sans)       # SSO
        self.assertIn("chat.localhost", sans)     # discussions
        self.assertIn("drive.localhost", sans)    # drive
        self.assertIn("meet.localhost", sans)     # meet
        self.assertIn("livekit.localhost", sans)  # serveur additionnel (SFU)


if __name__ == "__main__":
    unittest.main()
