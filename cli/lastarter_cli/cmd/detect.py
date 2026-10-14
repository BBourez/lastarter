"""`lastarter detect` — audit d'environnement avant installation (clef en main).

Sans effet de bord : détecte l'IP publique, les interfaces, Docker, un éventuel
cluster Kubernetes (contexte courant + IP du nœud), la résolution DNS du domaine
cible et la disponibilité des ports requis. Aucune information n'est envoyée
ailleurs que la requête IP (api.ipify.org) — opt-in via --public-ip.
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

REQUIRED_PORTS = {
    "8443": "passerelle TLS (entrée unique)",
    "7880": "livekit signalisation (visio/chat)",
    "7881": "livekit RTC tcp",
}


def _run(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=15, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def public_ip() -> str | None:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=8) as response:
            return response.read().decode().strip()
    except Exception:  # noqa: BLE001 — détection best effort
        return None


def local_ips() -> list[str]:
    ips: set[str] = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ips)


def kubernetes() -> dict | None:
    """Détecte un cluster : variables d'env (in-pod), sinon kubectl (poste)."""
    k8s_host = None
    for key in ("KUBERNETES_SERVICE_HOST", "KUBERNETES_SERVICE_PORT"):
        if key in __import__("os").environ:
            k8s_host = f"{__import__('os').environ['KUBERNETES_SERVICE_HOST']}:{__import__('os').environ.get('KUBERNETES_SERVICE_PORT', '443')}"
            break
    context = _run(["kubectl", "config", "current-context"])
    nodes = _run(["kubectl", "get", "nodes", "-o", "jsonpath={range .items[*]}{.status.addresses[0].address} {end}"])
    if not (k8s_host or context):
        return None
    return {"service_host": k8s_host, "context": context, "node_ips": (nodes or "").split()}


def dns_resolves(domain: str) -> str | None:
    try:
        return socket.gethostbyname(domain.split(":")[0])
    except OSError:
        return None


def port_free(port: str) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        return sock.connect_ex(("127.0.0.1", int(port))) != 0


def run_detect(opts) -> int:
    print("LaStarter — audit d'environnement (aucune modification)\n")
    print("Hôte")
    ips = local_ips()
    print(f"  interfaces locales  : {', '.join(ips) or 'n/a'}")
    if opts.public_ip:
        ip = public_ip()
        print(f"  IP publique         : {ip or 'indétectable (hors ligne ?)'}")

    print("\nConteneurs")
    version = _run(["docker", "version", "--format", "{{.Server.Version}}"])
    print(f"  Docker              : {'v' + version if version else 'ABSENT — requis pour la cible compose'}")
    compose = _run(["docker", "compose", "version", "--short"])
    print(f"  Compose             : {compose or 'n/a'}")

    print("\nKubernetes")
    k8s = kubernetes()
    if k8s:
        print(f"  contexte kubectl    : {k8s['context'] or 'n/a'}")
        if k8s["service_host"]:
            print(f"  service (in-pod)    : {k8s['service_host']}")
        if k8s["node_ips"]:
            print(f"  IPs des nœuds       : {', '.join(k8s['node_ips'])}")
        print("  → cible Helm umbrella disponible (phase 5)")
    else:
        print("  aucun cluster détecté (cible compose mono-VM)")

    print("\nDNS")
    if opts.domain:
        resolved = dns_resolves(opts.domain)
        bare = opts.domain.split(":")[0]
        for label in ("id", "drive", "meet", "chat", "matrix"):
            sub = dns_resolves(f"{label}.{bare}")
            if sub:
                print(f"  {label}.{bare:<20} → {sub}")
        print(f"  {bare:<24} → {resolved or 'NE RÉSOUT PAS (en local *.localhost suffit aux navigateurs)'}")

    print("\nPorts requis (libres = OK)")
    for port, usage in REQUIRED_PORTS.items():
        state = "libre" if port_free(port) else "OCCUPÉ"
        print(f"  {port:<5} {usage:<38} {state}")

    print("\nRécapitulatif JSON (machine) — aucun secret :")
    print(json.dumps({
        "local_ips": ips,
        "docker": version,
        "kubernetes": k8s,
        "ports_free": {p: port_free(p) for p in REQUIRED_PORTS},
    }, ensure_ascii=False, indent=2))
    return 0
