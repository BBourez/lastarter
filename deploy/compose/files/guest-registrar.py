#!/usr/bin/env python3
"""LaStarter — registrar d'invités Meet.

Crée de VRAIS comptes Matrix via le shared secret d'inscription de Synapse
(les comptes « guest » ne peuvent pas obtenir de jeton OpenID, donc pas
rejoindre l'appel SFU — cf. M_GUEST_ACCESS_FORBIDDEN sur la couche auth).

POST /register {"display_name": "..."} →
  {"user_id", "access_token", "device_id"}

Même posture de sécurité que l'inscription guest : n'importe qui peut créer
un compte à nom aléatoire, sans mot de passe utilisable (aléatoire jeté).
"""

import hashlib
import hmac
import json
import os
import secrets
import string
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

SYNAPSE = os.environ.get("SYNAPSE_URL", "http://discussions_synapse:8008")
SHARED_SECRET = os.environ.get("GUEST_REG_SECRET", "")
ALPHABET = string.ascii_letters + string.digits


def register_user(display_name: str) -> dict:
    """Inscription via l'API admin de Synapse (nonce + HMAC du shared secret)."""
    with urllib.request.urlopen(f"{SYNAPSE}/_synapse/admin/v1/register", timeout=10) as r:
        nonce = json.loads(r.read())["nonce"]

    username = "invite_" + "".join(secrets.choice(ALPHABET) for _ in range(12))
    password = secrets.token_urlsafe(24)  # jeté : le pseudo n'a pas de mdp
    mac = hmac.new(
        key=SHARED_SECRET.encode("utf-8"),
        digestmod=hashlib.sha1,
        msg=b"\x00".join(
            [
                nonce.encode("ascii"),
                username.encode("utf-8"),
                password.encode("utf-8"),
                b"notadmin",
            ]
        ),
    ).hexdigest()

    body = json.dumps(
        {"nonce": nonce, "username": username, "password": password, "mac": mac, "admin": False}
    ).encode()
    req = urllib.request.Request(
        f"{SYNAPSE}/_synapse/admin/v1/register",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        creds = json.loads(r.read())

    # Nom affiché = le pseudo choisi
    req2 = urllib.request.Request(
        f"{SYNAPSE}/_matrix/client/v3/profile/{creds['user_id']}/displayname",
        data=json.dumps({"displayname": display_name}).encode(),
        headers={"Authorization": f"Bearer {creds['access_token']}", "Content-Type": "application/json"},
        method="PUT",
    )
    urllib.request.urlopen(req2, timeout=10)
    return creds


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/register":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
            name = str(data.get("display_name", ""))[:64].strip() or "Invité"
            creds = register_user(name)
            body = json.dumps(creds).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:  # noqa: BLE001
            body = json.dumps({"error": str(e)}).encode()
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args) -> None:  # noqa: N802
        print("[guest-registrar]", fmt % args, flush=True)


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
