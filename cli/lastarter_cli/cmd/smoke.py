"""`lastarter smoke` et `lastarter sbom` — qualité d'un déploiement.

smoke : vérifie chaque surface exposée (portail, SSO, apps) en HTTPS avec la CA
du déploiement — opérationnalise les validations E2E post-déploiement / release.
sbom  : inventaire CycloneDX des briques épinglées (noms, versions, licences).
"""

from __future__ import annotations

import json
import socket
import ssl
import sys
import urllib.request
from pathlib import Path

from ..catalogue import Brick, find_catalogue, load_catalogue
from .deploy import DeployError, _id_origin, app_origin, compute_origin, load_deployment


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


def _fetch(url: str, ca_file: Path | None = None, follow: bool = True) -> tuple[int, str, str]:
    """Retourne (status, corps, Location). follow=False : expose les 3xx."""
    context = None
    if url.startswith("https") and ca_file is not None:
        context = ssl.create_default_context(cafile=str(ca_file))
    request = urllib.request.Request(url, headers={"User-Agent": "lastarter-smoke/1"})
    handlers: list = []
    if context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=context))
    if not follow:
        handlers.append(_NoRedirect())
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(request, timeout=15) as response:
            return response.status, response.read().decode(errors="replace"), response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace"), exc.headers.get("Location", "") if exc.headers else ""
    except (urllib.error.URLError, OSError) as exc:
        return 0, str(exc), ""


def _check(results: list, label: str, url: str, expect: int, contains: str | None = None,
           ca_file: Path | None = None, follow: bool = True, location_prefix: str | None = None) -> None:
    status, body, location = _fetch(url, ca_file, follow)
    ok = status == expect and (contains is None or contains in body)
    if ok and location_prefix is not None:
        ok = location.startswith(location_prefix)
    mark = "✓" if ok else "✗"
    detail = f"HTTP {status}" + (f" (attendu {expect})" if status != expect else "")
    if status == 0:
        detail += f" — {body[:120]}"  # cause réseau (DNS, TLS, refus)
    if ok is False and contains is not None and status == expect:
        detail += f" — contenu attendu manquant: {contains!r}"
    if ok is False and location_prefix is not None and status == expect:
        detail += f" — Location: {location[:100]!r}"
    results.append((ok, f"{mark} {label:<34} {detail}"))


def _enable_local_domain_resolution(bare_domain: str) -> None:
    """Résout <quelque-chose>.<bare> et <bare> en 127.0.0.1 quand le domaine
    est local (comportement navigateur pour *.localhost, absent de l'OS Windows)."""
    if bare_domain not in {"localhost", "127.0.0.1"}:
        return
    original_getaddrinfo = socket.getaddrinfo

    def patched(host, port, *args, **kwargs):
        if host == bare_domain or host.endswith(f".{bare_domain}"):
            return original_getaddrinfo("127.0.0.1", port, *args, **kwargs)
        return original_getaddrinfo(host, port, *args, **kwargs)

    socket.getaddrinfo = patched


def run_smoke(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé.", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        print("catalogue invalide : " + " ; ".join(errors), file=sys.stderr)
        return 1
    try:
        manifest, answers, _vault, _bricks = load_deployment(repo_root, opts.client)
    except (DeployError, KeyError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1

    ca_file = repo_root / "deployments" / opts.client / ".runtime" / "certs" / "ca.crt"
    domain = answers["domain"]
    _enable_local_domain_resolution(domain.split(":")[0])
    results: list[tuple[bool, str]] = []

    _check(results, "portail (apex /)", compute_origin(domain), 200, "portal-config", ca_file)
    _check(
        results, "SSO découverte OIDC (id.)",
        f"{_id_origin(domain)}/realms/lastarter/.well-known/openid-configuration",
        200, '"issuer"', ca_file,
    )
    for name, entry in manifest.get("bricks", {}).items():
        brick = bricks.get(name)
        if brick is None or brick.core:
            continue
        label = brick.compose.get("route_label", name)
        origin = app_origin(domain, label)
        if brick.compose.get("portal_visible", "true") == "false":
            if name == "element-call":
                # SPA widget (pas un backend Matrix) : juste vérifier qu'il répond.
                _check(results, f"{name} (SPA /)", origin, 200, None, ca_file)
                continue
            # Backend (ex. synapse) : API + chaîne SSO (redirect vers l'IdP).
            _check(results, f"{name} (API)", f"{origin}/_matrix/client/versions", 200, '"versions"', ca_file)
            _check(
                results, f"{name} (SSO redirect)",
                f"{origin}/_matrix/client/v3/login/sso/redirect?redirectUrl={origin}",
                302, None, ca_file, follow=False,
                location_prefix=_id_origin(domain),
            )
            continue
        _check(results, f"{name} (frontend /)", origin, 200, None, ca_file)
        if brick.compose.get("api_target"):
            _check(results, f"{name} (API config)", f"{origin}/api/v1.0/config/", 200, None, ca_file)

    for _ok, line in results:
        print(line)
    failed = [line for ok, line in results if not ok]
    if failed:
        print(f"\n{len(failed)} échec(s) — déploiement non conforme.", file=sys.stderr)
        return 1
    print(f"\nSmoke OK — {len(results)} surfaces vérifiées.")
    return 0


def run_sbom(opts) -> int:
    catalogue_dir = find_catalogue(Path.cwd())
    if catalogue_dir is None:
        print("Aucun dossier catalogue/ trouvé.", file=sys.stderr)
        return 1
    repo_root = catalogue_dir.parent
    bricks, errors = load_catalogue(catalogue_dir)
    if errors:
        print("catalogue invalide : " + " ; ".join(errors), file=sys.stderr)
        return 1
    try:
        manifest, _answers, _vault, _b = load_deployment(repo_root, opts.client)
    except (DeployError, KeyError) as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 1

    components = []
    for name in manifest.get("bricks", {}):
        brick = bricks[name]
        components.append(
            {
                "type": "application",
                "name": brick.name,
                "version": brick.upstream_pin,
                "licenses": [{"license": {"id": brick.license}}],
                "externalReferences": [
                    {"type": "vcs", "url": brick.upstream_repo}
                ],
            }
        )
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "metadata": {"component": {"type": "application", "name": f"lastarter-{opts.client}"}},
        "components": components,
    }
    target = repo_root / "deployments" / opts.client / "sbom.json"
    target.write_text(json.dumps(sbom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"SBOM écrit : {target} ({len(components)} composants)")
    return 0
