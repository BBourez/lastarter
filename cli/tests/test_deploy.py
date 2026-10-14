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
    render_element_config,
    render_lk_registration,
    render_portal_config,
    render_realm,
    render_runtime_env,
    render_synapse_homeserver,
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
    "domain": "localhost:8443",
    "brand_name": "LaStarter",
}


class OriginTests(unittest.TestCase):
    def test_toujours_https_meme_en_local(self):
        # La passerelle sert TLS partout (POC : CA locale) — scheme unique.
        self.assertEqual(compute_origin("localhost:8443"), "https://localhost:8443")
        self.assertEqual(compute_origin("acme.example.com"), "https://acme.example.com")

    def test_app_origin_par_label(self):
        self.assertEqual(app_origin("localhost:8443", "drive"), "https://drive.localhost:8443")
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
        draft = "URL={origin}\nSSO={sso_origin}\nWS={ws}://livekit.{domain}\nHOST={app_host}\nCONF={django_configuration}\n"
        rendered = render_runtime_env(draft, ANSWERS, self.vault, label="meet")
        self.assertIn("URL=https://meet.localhost:8443", rendered)
        self.assertIn("SSO=https://id.localhost:8443", rendered)  # identité sur id.<domaine>
        self.assertIn("WS=wss://livekit.localhost:8443", rendered)
        self.assertIn("HOST=meet.localhost:8443", rendered)
        self.assertIn("CONF=Feature", rendered)

    def test_domain_s3_passe_par_la_passerelle(self):
        rendered = render_runtime_env("S3=https://{domain_s3}", ANSWERS, self.vault, label="meet")
        self.assertIn("S3=https://meet-media.localhost:8443", rendered)

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
        self.assertEqual(by_id["drive"]["redirectUris"], ["https://drive.localhost:8443/*"])
        self.assertEqual(by_id["meet"]["redirectUris"], ["https://meet.localhost:8443/*"])

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
        self.assertIn("server_name localhost _;", edge)          # apex → portail
        self.assertIn("server_name id.localhost;", edge)          # id → keycloak
        self.assertIn("server_name drive.localhost;", edge)       # app drive
        self.assertIn("set $backend_front drive_frontend:3000;", edge)
        self.assertIn("server_name meet.localhost;", edge)        # app meet
        self.assertIn("server_name livekit.localhost;", edge)     # SFU ws
        self.assertIn('proxy_set_header Connection "upgrade";', edge)
        # L'apex ET id.<domaine> routent vers l'identité (toute l'auth vit sur id).
        self.assertIn("proxy_pass http://$backend_keycloak;", edge)
        self.assertNotIn("server_name drive.localhost:8083;", edge)      # port interdit
        self.assertNotIn("server_name drive.localhost:8083;", edge)      # port interdit


    def test_homeserver_synapse_rendu_endpoints_scindes(self):
        template = (
            "server_name: {{SERVER_NAME}}\n"
            "public_baseurl: {{MATRIX_ORIGIN}}/\n"
            "issuer: {{SSO_ORIGIN}}/realms/lastarter\n"
            'secret: "{{SECRET:synapse_oidc_secret}}"\n'
        )
        vault = {"synapse_oidc_secret": "s3cret-syn"}
        rendered = render_synapse_homeserver(template, ANSWERS, vault)
        self.assertIn("server_name: localhost", rendered)
        self.assertIn("public_baseurl: https://matrix.localhost:8443/", rendered)
        self.assertIn("issuer: https://id.localhost:8443/realms/lastarter", rendered)
        self.assertIn('secret: "s3cret-syn"', rendered)
        self.assertNotIn("{{", rendered)

    def test_lk_registration_rendu(self):
        vault = {"lk_as_token": "as-123", "lk_hs_token": "hs-456"}
        rendered = render_lk_registration(ANSWERS, vault)
        self.assertIn('as_token: "as-123"', rendered)
        self.assertIn('hs_token: "hs-456"', rendered)
        self.assertIn("regex: \"@.*:localhost\"", rendered)
        self.assertIn('url: "http://lk_jwt_service:6080"', rendered)
        self.assertIn("msc4512.proxy_prefix: \"rtc/livekit\"", rendered)

    def test_element_config_rendu_theme_et_homeserver(self):
        template = (
            '{\n  "brand": "{{BRAND}}",\n  "default_theme": "custom-{{THEME_NAME}}",\n'
            '  "default_server_config": {"m.homeserver": {"base_url": "{{MATRIX_ORIGIN}}",'
            ' "server_name": "{{SERVER_NAME}}"}},\n'
            '  "setting_defaults": {"custom_themes": [{{CUSTOM_THEME}}]}\n}\n'
        )
        rendered = render_element_config(template, ANSWERS, self.bricks["element-web"])
        parsed = json.loads(rendered)
        self.assertEqual(parsed["brand"], "LaStarter")
        self.assertEqual(parsed["default_theme"], "custom-LaStarter Light")
        self.assertEqual(
            parsed["default_server_config"]["m.homeserver"]["base_url"],
            "https://matrix.localhost:8443",
        )
        theme = parsed["setting_defaults"]["custom_themes"][0]
        self.assertEqual(theme["accent-color"], "#4F46E5")
        self.assertNotIn("name", theme)  # extrait vers THEME_NAME

    def test_cle_signature_synapse_format_b64(self):
        import base64

        names = self.bricks["synapse"].extra_secrets
        self.assertIn("synapse_signing_key:b64", names)
        # Un secret b64 généré : 44 caractères, décodable en 32 octets.
        from lastarter_cli.cmd.init import generate_secrets

        order, _ = resolve_selection(["synapse"], self.bricks)
        vault = generate_secrets([self.bricks[n] for n in order], None)
        self.assertEqual(len(vault["synapse_signing_key"]), 44)
        self.assertEqual(len(base64.b64decode(vault["synapse_signing_key"])), 32)

    def test_edge_sans_api_target_pour_element_web(self):
        names, _ = resolve_selection(["element-web"], self.bricks)
        selected = [self.bricks[n] for n in names]
        edge = render_edge(selected, ANSWERS)
        self.assertIn("server_name chat.localhost;", edge)
        self.assertIn("set $backend_front element_web:80;", edge)
        block = edge.split("server_name chat.localhost;")[1].split("}")[0]
        self.assertNotIn("location /api/", block)  # app statique : pas de /api/


    def test_portail_genere_depuis_les_briques(self):
        names, _ = resolve_selection(["drive", "meet", "element-web"], self.bricks)
        selected = [self.bricks[n] for n in names]
        config = json.loads(render_portal_config(selected, ANSWERS))
        self.assertEqual(config["brand"], "LaStarter")
        self.assertIn("account_url", config)
        self.assertIn("id.localhost:8443", config["account_url"])
        by_name = {a["name"]: a for a in config["apps"]}
        self.assertIn("Drive", by_name)  # titre avant le tiret
        self.assertIn("Meet", by_name)
        self.assertIn("Chat", by_name)
        self.assertNotIn("Synapse", " ".join(by_name))  # backend : pas de tuile
        self.assertEqual(by_name["Drive"]["emoji"], "📁")
        self.assertEqual(
            by_name["Drive"]["url"], "https://drive.localhost:8443"
        )

    def test_edge_apex_portail_et_id_keycloak(self):
        names, _ = resolve_selection(["drive"], self.bricks)
        selected = [self.bricks[n] for n in names]
        edge = render_edge(selected, ANSWERS)
        self.assertIn("set $backend_portal portal:80;", edge)   # apex → portail
        self.assertIn("server_name localhost _;", edge)
        self.assertIn("server_name id.localhost;", edge)        # id → keycloak
        self.assertIn("set $backend_keycloak keycloak:8080;", edge)
        # Les endpoints SSO restent joignables sur l'apex (outillage CLI).
        self.assertIn("location /realms/ {", edge)


    def test_edge_acces_vpn_genere_allow_deny(self):
        names, _ = resolve_selection(["drive"], self.bricks)
        selected = [self.bricks[n] for n in names]
        # Sans champ access : pas de restriction.
        edge = render_edge(selected, ANSWERS)
        self.assertNotIn("deny all;", edge)
        # Avec access = "vpn" : allow réseaux privés + deny all.
        # NB : resolve_selection ajoute les fondations en tête — cibler par nom.
        vpn_brick = next(b for b in selected if b.name == "drive")
        vpn_brick.compose["access"] = "vpn"
        try:
            edge_vpn = render_edge(selected, ANSWERS)
            self.assertIn("allow 10.0.0.0/8", edge_vpn)
            self.assertIn("allow 100.64.0.0/10", edge_vpn)  # WireGuard/CGNAT
            self.assertIn("deny all;", edge_vpn)
            self.assertIn("Accès restreint : VPN/LAN uniquement (drive)", edge_vpn)
        finally:
            vpn_brick.compose.pop("access", None)


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
