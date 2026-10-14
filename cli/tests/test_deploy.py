"""Tests offline du module deploy — rendus runtime, realm, edge, gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lastarter_cli.catalogue import load_catalogue, resolve_selection, secret_names
from lastarter_cli.cmd.deploy import (
    DeployError,
    app_origin,
    build_realm_clients,
    compose_base,
    compute_origin,
    render_edge,
    render_realm,
    render_runtime_env,
    validate_compose_targets,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REALM_TEMPLATE = (
    '{"realm": "lastarter", '
    '"clients": {{CLIENTS_JSON}}, '
    '"users": [{"username": "demo", "credentials": [{"value": "{{SECRET:demo_user_password}}"}]}]}'
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

    def test_app_origin_par_label(self):
        self.assertEqual(app_origin("localhost:8083", "drive"), "http://drive.localhost:8083")
        self.assertEqual(app_origin("acme.example.com", "meet"), "https://meet.acme.example.com")


class RuntimeRenderTests(unittest.TestCase):
    def setUp(self):
        self.bricks, self.errors = load_catalogue(REPO_ROOT / "catalogue")
        self.assertEqual(self.errors, [])
        self.vault = {
            "oidc_client_secret": "s3cret-oidc",
            "meet_oidc_client_secret": "s3cret-meet",
            "demo_user_password": "s3cret-demo",
            "django_secret_key": "s3cret-django",
        }

    def test_contexte_par_brique_label_et_ws(self):
        draft = "URL={origin}\nSSO={sso_origin}\nWS={ws}://livekit.{domain}\nHOST={app_host}\n"
        rendered = render_runtime_env(draft, ANSWERS, self.vault, label="meet")
        self.assertIn("URL=http://meet.localhost:8083", rendered)
        self.assertIn("SSO=http://localhost:8083", rendered)
        self.assertIn("WS=ws://livekit.localhost:8083", rendered)
        self.assertIn("HOST=meet.localhost:8083", rendered)

    def test_s3_port_par_brique(self):
        rendered = render_runtime_env(
            "S3=http://{domain_s3}", ANSWERS, self.vault, label="meet", s3_port="9010"
        )
        self.assertIn("S3=http://localhost:9010", rendered)

    def test_secret_manquant_rejette(self):
        with self.assertRaises(DeployError):
            render_runtime_env("K={secret:absent}", ANSWERS, self.vault)

    def test_realm_clients_dynamiques(self):
        names, _ = resolve_selection(["drive", "meet"], self.bricks)
        selected = [self.bricks[n] for n in names]
        rendered_envs = {
            "drive": "OIDC_RP_CLIENT_SECRET=s3cret-oidc\n",
            "meet": "OIDC_RP_CLIENT_SECRET=s3cret-meet\n",
        }
        clients = json.loads(build_realm_clients(selected, rendered_envs, ANSWERS))
        by_id = {c["clientId"]: c for c in clients}
        self.assertEqual(set(by_id), {"drive", "meet"})
        self.assertEqual(by_id["drive"]["secret"], "s3cret-oidc")
        self.assertEqual(by_id["drive"]["redirectUris"], ["http://drive.localhost:8083/*"])
        self.assertEqual(by_id["meet"]["redirectUris"], ["http://meet.localhost:8083/*"])

    def test_realm_rendu_avec_clients(self):
        clients = json.dumps([{"clientId": "drive", "secret": "s"}])
        rendered = render_realm(REALM_TEMPLATE, ANSWERS, self.vault, clients)
        parsed = json.loads(rendered)
        self.assertEqual(parsed["clients"][0]["clientId"], "drive")
        self.assertEqual(parsed["users"][0]["credentials"][0]["value"], "s3cret-demo")
        self.assertNotIn("{{", rendered)

    def test_realm_secret_manquant_rejette(self):
        with self.assertRaises(DeployError):
            render_realm(REALM_TEMPLATE, ANSWERS, {}, "[]")

    def test_edge_generee_par_brique(self):
        names, _ = resolve_selection(["drive", "meet"], self.bricks)
        selected = [self.bricks[n] for n in names]
        edge = render_edge(selected, ANSWERS)
        self.assertIn("server_name localhost _;", edge)          # apex SSO (sans port)
        self.assertIn("server_name drive.localhost;", edge)       # app drive
        self.assertIn("proxy_pass http://drive_frontend:3000;", edge)
        self.assertIn("server_name meet.localhost;", edge)        # app meet
        self.assertIn("server_name livekit.localhost;", edge)     # SFU ws
        self.assertIn('proxy_set_header Connection "upgrade";', edge)
        self.assertIn("return 302 http://drive.localhost:8083/;", edge)  # apex → 1re app
        self.assertNotIn("server_name drive.localhost:8083;", edge)      # port interdit


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
            for name in ("keycloak", "drive", "meet"):
                (compose_dir / f"{name}.yml").write_text("services: {}", encoding="utf-8")
            with self.assertRaises(DeployError):
                validate_compose_targets(["keycloak", "element-web"], self.bricks, compose_dir)

    def test_briques_poc_acceptees(self):
        with tempfile.TemporaryDirectory() as tmp:
            compose_dir = Path(tmp)
            for name in ("keycloak", "drive", "meet"):
                (compose_dir / f"{name}.yml").write_text("services: {}", encoding="utf-8")
            validate_compose_targets(["keycloak", "drive", "meet"], self.bricks, compose_dir)

    def test_secrets_par_brique_dans_le_coffre(self):
        self.assertIn("meet_oidc_client_secret", secret_names(self.bricks["meet"]))
        self.assertIn("meet_s3_secret_key", secret_names(self.bricks["meet"]))


if __name__ == "__main__":
    unittest.main()
