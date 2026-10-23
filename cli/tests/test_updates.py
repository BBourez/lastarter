"""Tests offline de la veille amont (`lastarter check-updates`) — fetcher injecté.

AUCUN appel réseau : le fetcher est un stub ; l'API réelle (urllib) est la
même sans injection. Détails vérifiés : endpoint par amont (/tags suitenumerique,
/releases element-hq), exclusion des pré-releases, comparaison sémantique,
format du rapport JSON (source du workflow CI de veille).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace

from lastarter_cli.cmd.updates import (
    UpdatesError,
    check_updates,
    is_prerelease,
    latest_version,
    parse_version,
)

CLI_DIR = Path(__file__).resolve().parents[1]


def _brick(repo: str, pin: str) -> SimpleNamespace:
    return SimpleNamespace(upstream_repo=repo, upstream_pin=pin)


class SemverTests(unittest.TestCase):
    def test_parse_version_tolere_prefixe_et_suffixes(self):
        self.assertEqual(parse_version("v1.12.32"), (1, 12, 32))
        self.assertEqual(parse_version("26.3.2"), (26, 3, 2))
        self.assertEqual(parse_version("V0.25.2"), (0, 25, 2))
        self.assertEqual(parse_version("v1.0.0-rc1"), (1, 0, 0))
        self.assertIsNone(parse_version("main"))
        self.assertIsNone(parse_version(""))

    def test_prereleases_exclues(self):
        self.assertTrue(is_prerelease("v1.37.0-pre"))
        self.assertTrue(is_prerelease("v1.37.0-preprod"))
        self.assertTrue(is_prerelease("v1.36.5-rc1"))
        self.assertTrue(is_prerelease("v1.36.5-RC2"))
        self.assertFalse(is_prerelease("v1.36.4"))

    def test_latest_version_choisit_le_max_semantique_hors_prerelease(self):
        tags = ["v1.36.2", "v1.37.0-pre", "v1.36.9-preprod", "v1.36.5-rc1", "v1.36.4"]
        self.assertEqual(latest_version(tags), "v1.36.4")
        self.assertIsNone(latest_version(["v1.38.0-pre", "demo"]))


class CheckUpdatesOfflineTests(unittest.TestCase):
    """Fetchers injectés : zéro réseau, zéro écriture."""

    def setUp(self):
        self.bricks = {
            "meet": _brick("https://github.com/suitenumerique/meet", "v1.36.2"),
            "discussions": _brick("https://github.com/element-hq/element-web", "v1.12.32"),
        }

    def test_detection_nouveau_tag(self):
        calls: list[str] = []

        def fetcher(url: str) -> list:
            calls.append(url)
            if "suitenumerique/meet" in url:
                return [{"name": "v1.36.2"}, {"name": "v1.36.3"}]  # /tags : champ name
            return [{"tag_name": "v1.12.32"}]  # /releases : champ tag_name

        rows = check_updates(self.bricks, fetcher=fetcher)
        by_name = {row["brique"]: row for row in rows}
        # suitenumerique : pas de releases amont → endpoint /tags.
        self.assertTrue(any("/repos/suitenumerique/meet/tags" in url for url in calls))
        # element-hq : releases publiées → endpoint /releases.
        self.assertTrue(any("/repos/element-hq/element-web/releases" in url for url in calls))
        self.assertEqual(by_name["meet"]["latest"], "v1.36.3")
        self.assertFalse(by_name["meet"]["a_jour"])
        self.assertEqual(by_name["discussions"]["pin"], "v1.12.32")
        self.assertTrue(by_name["discussions"]["a_jour"])
        # Rapport sérialisable : source directe du workflow CI de veille.
        payload = json.dumps(rows, ensure_ascii=False)
        self.assertIn('"brique"', payload)
        self.assertIn('"a_jour"', payload)

    def test_exclusion_preprod(self):
        """Le « latest » suitenumerique est une preprod : JAMAIS proposé."""

        def fetcher(url: str) -> list:
            return [
                {"name": "v1.36.2"},
                {"name": "v1.37.0-pre"},
                {"name": "v1.36.9-preprod"},
                {"name": "v1.36.5-rc1"},
            ]

        rows = check_updates({"meet": self.bricks["meet"]}, fetcher=fetcher)
        self.assertEqual(rows[0]["latest"], "v1.36.2")
        self.assertTrue(rows[0]["a_jour"])

    def test_pin_en_retour_est_signale(self):
        def fetcher(url: str) -> list:
            return [{"name": "v2.0.0"}]

        rows = check_updates(
            {"drive": _brick("https://github.com/suitenumerique/drive", "v0.25.2")},
            fetcher=fetcher,
        )
        self.assertEqual(rows[0]["brique"], "drive")
        self.assertEqual(rows[0]["latest"], "v2.0.0")
        self.assertFalse(rows[0]["a_jour"])

    def test_erreur_reseau_remontee_propre(self):
        def fetcher(url: str) -> list:
            raise urllib.error.URLError("dns indisponible")

        with self.assertRaises(UpdatesError):
            check_updates(self.bricks, fetcher=fetcher)


class RunCheckUpdatesTests(unittest.TestCase):
    """Point d'entrée CLI : --json (sortie machine) et --strict (gate)."""

    def _run(self, opts, fetcher) -> tuple[int, str, str]:
        from lastarter_cli.cmd import updates as upd

        out, err = io.StringIO(), io.StringIO()
        cwd = os.getcwd()
        os.chdir(CLI_DIR)  # find_catalogue remonte depuis cli/
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = upd.run_check_updates(opts, fetcher=fetcher)
        finally:
            os.chdir(cwd)
        return code, out.getvalue(), err.getvalue()

    def test_sortie_json_couvre_tout_le_catalogue(self):
        def fetcher(url: str) -> list:
            return [{"name": "v1.0.0"}]

        code, out, _err = self._run(SimpleNamespace(json=True, strict=False), fetcher)
        self.assertEqual(code, 0)
        rows = json.loads(out)
        self.assertEqual(
            {row["brique"] for row in rows},
            {"keycloak", "discussions", "drive", "meet", "docs"},
        )
        for row in rows:
            self.assertEqual(set(row), {"brique", "pin", "latest", "a_jour"})

    def test_strict_echoue_si_retard(self):
        def fetcher(url: str) -> list:
            # Un tag très en avance sur tous les pins → tous en retard.
            return [{"name": "v99.0.0"}]

        code, _out, err = self._run(SimpleNamespace(json=False, strict=True), fetcher)
        self.assertEqual(code, 1)
        self.assertIn("--strict", err)


if __name__ == "__main__":
    unittest.main()
