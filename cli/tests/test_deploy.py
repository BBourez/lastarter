"""Tests offline du module deploy — rendus runtime, gates, origine."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lastarter_cli.catalogue import load_catalogue, secret_names
from lastarter_cli.cmd.deploy import (
    DeployError,
    compose_base,
    compute_origin,
    render_realm,
    render_runtime_env,
    validate_compose_targets,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REALM_TEMPLATE = json.dumps(
    {
        "realm": "lastarter",
        "clients": [
            {
                "clientId": "drive",
                "secret": "{{SECRET:oidc_client_secret}}",
                "redirectUris": ["{{ORIGIN}}/*"],
            }
        ],
        "users": [
            {"username": "demo", "credentials": [{"value": "{{SECRET:demo_user_password}}"}]}
        ],
    }
)

ANSWERS = {
    "client_name": "Demo Coop",
    "client_slug": "demo-coop",
    "domain": "localhost:8083",
    "brand_name": "LaStarter",
}


class OriginTests(unittest.TestCase):
    def test_http_en_local_https_en_production(self):
        self.assertEqual(compute_origin("localhost:8083"), "http://localhost:8083")
        self.assertEqual(compute_origin("127.0.0.1"), "http://127.0.0.1")
        self.assertEqual(compute_origin("acme.example.com"), "https://acme.example.com")


class RuntimeRenderTests(unittest.TestCase):
    def setUp(self):
        self.vault = {
            "oidc_client_secret": "s3cret-oidc",
            "demo_user_password": "s3cret-demo",
            "django_secret_key": "s3cret-django",
        }

    def test_substitue_tokens_secrets_et_contexte(self):
        draft = (
            "# en-tête\n"
            "DJANGO_ALLOWED_HOSTS={domain}\n"
            "OIDC_OP_AUTHORIZATION_ENDPOINT={origin}/realms/lastarter/auth\n"
            "OIDC_RP_CLIENT_SECRET={secret:oidc_client_secret}\n"
            "DJANGO_EMAIL_BRAND_NAME={brand_name}\n"
            "AWS_S3_DOMAIN_REPLACE=http://{domain_s3}\n"
        )
        rendered = render_runtime_env(draft, ANSWERS, self.vault)
        self.assertIn("DJANGO_ALLOWED_HOSTS=localhost:8083", rendered)
        self.assertIn("OIDC_OP_AUTHORIZATION_ENDPOINT=http://localhost:8083/realms/lastarter/auth", rendered)
        self.assertIn("OIDC_RP_CLIENT_SECRET=s3cret-oidc", rendered)
        self.assertIn("DJANGO_EMAIL_BRAND_NAME=LaStarter", rendered)
        self.assertIn("AWS_S3_DOMAIN_REPLACE=http://localhost:9000", rendered)
        self.assertIn("# en-tête", rendered)  # structure conservée

    def test_secret_manquant_rejette(self):
        with self.assertRaises(DeployError):
            render_runtime_env("K={secret:absent}", ANSWERS, self.vault)

    def test_realm_rendu_completement(self):
        rendered = render_realm(REALM_TEMPLATE, ANSWERS, self.vault)
        parsed = json.loads(rendered)
        self.assertEqual(parsed["clients"][0]["secret"], "s3cret-oidc")
        self.assertEqual(parsed["clients"][0]["redirectUris"], ["http://localhost:8083/*"])
        self.assertEqual(parsed["users"][0]["credentials"][0]["value"], "s3cret-demo")
        self.assertNotIn("{{", rendered)

    def test_realm_secret_manquant_rejette(self):
        with self.assertRaises(DeployError):
            render_realm(REALM_TEMPLATE, ANSWERS, {})


class ComposeCommandTests(unittest.TestCase):
    def test_f_devant_chaque_fichier(self):
        files = [Path("base.yml"), Path("keycloak.yml"), Path("drive.yml")]
        env = Path("runtime") / "compose.env"
        base = compose_base(env, "demo-coop", files)
        self.assertEqual(
            base,
            [
                "docker", "compose",
                "--env-file", str(env),
                "-p", "demo-coop",
                "-f", str(files[0]),
                "-f", str(files[1]),
                "-f", str(files[2]),
            ],
        )
        self.assertEqual(base.count("-f"), 3)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.bricks, self.errors = load_catalogue(REPO_ROOT / "catalogue")
        self.assertEqual(self.errors, [])

    def test_brique_sans_cible_compose_refusee(self):
        with tempfile.TemporaryDirectory() as tmp:
            compose_dir = Path(tmp)
            (compose_dir / "keycloak.yml").write_text("services: {}", encoding="utf-8")
            (compose_dir / "drive.yml").write_text("services: {}", encoding="utf-8")
            with self.assertRaises(DeployError):
                validate_compose_targets(["keycloak", "element-web"], self.bricks, compose_dir)

    def test_briques_poc_acceptees(self):
        with tempfile.TemporaryDirectory() as tmp:
            compose_dir = Path(tmp)
            for name in ("keycloak", "drive"):
                (compose_dir / f"{name}.yml").write_text("services: {}", encoding="utf-8")
            validate_compose_targets(["keycloak", "drive"], self.bricks, compose_dir)  # ne lève pas

    def test_extra_secrets_du_realm_dans_le_coffre(self):
        self.assertIn("demo_user_password", secret_names(self.bricks["keycloak"]))


if __name__ == "__main__":
    unittest.main()
