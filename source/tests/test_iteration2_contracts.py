from __future__ import annotations

import json
import sys
import tempfile
import unittest
import uuid
import zipfile
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = SOURCE_ROOT / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.map_utils import export_bundle, load_geojson  # noqa: E402
from app.rss_registry import build_rss_url, parse_rss, rss_catalog  # noqa: E402
from app.script_runtime import (  # noqa: E402
    prepare_execution_job,
    read_execution_result,
    script_sha256,
    validate_execution_request,
)


class ScriptRuntimeContractTest(unittest.TestCase):
    def test_execution_is_limited_to_python_and_r_without_network(self) -> None:
        self.assertEqual(validate_execution_request("python", 60, 4096)["network_enabled"], False)
        self.assertEqual(validate_execution_request("r", 60, 4096)["allowed_hosts"], [])
        for language in ("shell", "sql", "other"):
            with self.assertRaises(ValueError):
                validate_execution_request(language, 60, 4096)
        with self.assertRaises(ValueError):
            validate_execution_request("python", 60, 4096, network_enabled=True)
        with self.assertRaises(ValueError):
            validate_execution_request("python", 60, 4096, allowed_hosts=["example.org"])

    def test_spool_job_is_bounded_and_recoverable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            execution_id = uuid.uuid4()
            job = prepare_execution_job(root, execution_id, "python", "print('ok')\n", 10, 4096)
            self.assertEqual(job.parent, root / "pending" / "python")
            self.assertEqual((job / "script.sha256").read_text(), script_sha256("print('ok')\n"))
            result = read_execution_result(root, execution_id, "python", 4096)
            self.assertEqual(result["status"], "queued")


class RssRegistryContractTest(unittest.TestCase):
    def test_registry_contains_only_verified_reliefweb_https_feeds(self) -> None:
        catalog = rss_catalog()
        self.assertEqual(len(catalog), 4)
        for feed in catalog:
            self.assertTrue(feed["base_url"].startswith("https://reliefweb.int/"))
            self.assertEqual(feed["verified_at"], "2026-08-15")
            self.assertIn("reliefweb.int", feed["allowed_hosts"])
        url = build_rss_url("reliefweb-reports", "cholera Mozambique", "fr")
        self.assertIn("lang=fr", url)
        self.assertIn("search=cholera+Mozambique", url)

    def test_rss_and_atom_are_parsed_without_html_execution(self) -> None:
        rss = b"""<?xml version='1.0'?><rss><channel><item><guid>a-1</guid><title>Alerte</title><link>https://reliefweb.int/report/x</link><description><![CDATA[<b>Texte</b> utile]]></description><pubDate>Fri, 15 Aug 2026 08:00:00 GMT</pubDate></item></channel></rss>"""
        items = parse_rss(rss)
        self.assertEqual(items[0]["external_id"], "a-1")
        self.assertEqual(items[0]["summary"], "Texte utile")
        self.assertEqual(items[0]["published_at"].year, 2026)
        with self.assertRaises(ValueError):
            parse_rss(b"<!DOCTYPE rss [<!ENTITY x 'bad'>]><rss/>")


class MapUtilitiesContractTest(unittest.TestCase):
    def test_geojson_is_bounded_and_export_contains_qgis_and_r(self) -> None:
        collection = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2.35, 48.85]}, "properties": {"name": "Paris"}}
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "layer.geojson"
            source.write_text(json.dumps(collection), encoding="utf-8")
            features = load_geojson(source)
            self.assertEqual(features[0]["properties"]["name"], "Paris")
            bundle = export_bundle(root / "bundle.zip", "Villes", collection)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
            self.assertIn("import_R.R", names)
            self.assertIn("import_qgis.py", names)
            self.assertIn("README.txt", names)
            self.assertTrue(any(name.endswith(".geojson") for name in names))


class IterationTwoStaticContractTest(unittest.TestCase):
    def test_compose_enforces_networkless_unprivileged_runners(self) -> None:
        compose = (SOURCE_ROOT / "payload" / "compose.yaml").read_text(encoding="utf-8")
        for service in ("runner-python", "runner-r"):
            self.assertIn(f"  {service}:", compose)
        self.assertGreaterEqual(compose.count("network_mode: none"), 2)
        self.assertGreaterEqual(compose.count('cap_drop: ["ALL"]'), 2)
        self.assertNotIn("docker.sock", compose)
        self.assertIn("execution_spool:/app/execution_spool", compose)

    def test_runner_never_invokes_a_shell(self) -> None:
        runner = (SOURCE_ROOT / "payload" / "runner" / "runner.c").read_text(encoding="utf-8")
        self.assertIn("execve(command", runner)
        self.assertIn("setrlimit", runner)
        self.assertNotIn("system(", runner)
        self.assertNotIn("popen(", runner)

    def test_native_installer_builds_and_starts_required_runners(self) -> None:
        installer = (SOURCE_ROOT / "src" / "installer.c").read_text(encoding="utf-8")
        self.assertIn("build --quiet api runner-python github-api", installer)
        self.assertIn("up -d --no-build db runner-python github-api api", installer)
        self.assertIn("build --quiet r-service runner-r", installer)
        self.assertIn("db r-service runner-python runner-r github-api api", installer)

    def test_api_and_interface_expose_iteration_two_modules(self) -> None:
        main = (API_ROOT / "app" / "main.py").read_text(encoding="utf-8")
        html = (API_ROOT / "static" / "index.html").read_text(encoding="utf-8")
        for route in (
            "/api/projects/{project_id}/execution-settings",
            "/api/scripts/{script_id}/executions",
            "/api/rss/catalog",
            "/api/projects/{project_id}/timeline",
            "/api/projects/{project_id}/map/layers",
            "/api/resources/{resource_id}/map/import",
        ):
            self.assertIn(route, main)
        for element_id in ("view-rss", "view-timeline", "view-map", "execution-settings-form"):
            self.assertIn(f'id="{element_id}"', html)
        self.assertIn("version 4.0.0", html)
        self.assertIn('/static/vendor/leaflet/leaflet.js', html)
        self.assertNotIn('unpkg.com', html)
        self.assertTrue((API_ROOT / "static" / "vendor" / "leaflet" / "LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
