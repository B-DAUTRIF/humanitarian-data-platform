from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.source_registry import (  # noqa: E402
    CONNECTORS,
    GLOBAL_BASE_SCHEMA,
    GLOBAL_SCHEMA_EXTRAS,
    connector_definition,
    merge_values,
    request_preview,
    validate_values,
)
from app.technology_registry import (  # noqa: E402
    GOOGLE_DRIVE_FOLDER_URL,
    technology_catalog,
)


class SourceSpecificConfigurationTest(unittest.TestCase):
    def test_each_live_connector_has_a_distinct_global_contract(self) -> None:
        self.assertEqual(set(GLOBAL_SCHEMA_EXTRAS), set(CONNECTORS))
        signatures = set()
        for source_id in CONNECTORS:
            schema = connector_definition(source_id)["global_settings_schema"]
            source_specific = set(schema["properties"]) - set(GLOBAL_BASE_SCHEMA["properties"])
            self.assertGreaterEqual(len(source_specific), 2, source_id)
            signatures.add(tuple(sorted(source_specific)))
        self.assertGreaterEqual(len(signatures), 8)

    def test_v4_global_values_are_migrated_by_default_merging(self) -> None:
        legacy = {
            "enabled": True,
            "timeout_seconds": 52,
            "retry_count": 3,
            "backoff_seconds": 4,
        }
        for source_id in CONNECTORS:
            merged = merge_values(source_id, legacy, scope="global")
            self.assertEqual(merged["timeout_seconds"], 52)
            self.assertIn("connect_timeout_seconds", merged)
            self.assertIn("max_response_bytes", merged)
            self.assertIn("user_agent", merged)

    def test_response_size_and_http_identity_are_bounded(self) -> None:
        values = connector_definition("hdx")["global_defaults"]
        self.assertGreaterEqual(values["max_response_bytes"], 100_000)
        with self.assertRaisesRegex(ValueError, "maximum"):
            validate_values(
                "hdx",
                {**values, "max_response_bytes": 200_000_001},
                scope="global",
            )
        with self.assertRaisesRegex(ValueError, "trop court"):
            validate_values("hdx", {**values, "user_agent": "x"}, scope="global")

    def test_profiles_explain_auth_formats_tools_and_terms(self) -> None:
        for source_id in CONNECTORS:
            profile = connector_definition(source_id)["technical_profile"]
            self.assertTrue(profile["protocol"])
            self.assertTrue(profile["formats"])
            self.assertTrue(profile["authentication"])
            self.assertTrue(profile["freshness"])
            self.assertTrue(profile["terms"])
            self.assertTrue(profile["python_tools"])
            self.assertTrue(profile["r_tools"])
            self.assertGreaterEqual(len(profile["official_links"]), 3)

    def test_every_official_source_link_is_https(self) -> None:
        for source_id in CONNECTORS:
            for link in connector_definition(source_id)["official_links"]:
                self.assertEqual(urlparse(link["url"]).scheme, "https", (source_id, link))
                self.assertTrue(link["label"])

    def test_preview_contains_redacted_curl_python_and_r(self) -> None:
        for source_id in CONNECTORS:
            defaults = connector_definition(source_id)["project_defaults"]
            preview = request_preview(source_id, {**defaults, "query": "cholera"})
            self.assertIn("curl --fail", preview["curl"])
            self.assertIn("import httpx", preview["code_examples"]["python"])
            self.assertIn("library(httr2)", preview["code_examples"]["r"])
            self.assertNotIn("real-secret", repr(preview))
        self.assertIn("<RELIEFWEB_APPNAME>", request_preview(
            "reliefweb",
            {**connector_definition("reliefweb")["project_defaults"], "query": "cholera"},
        )["code_examples"]["python"])


class TechnologyCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = technology_catalog()
        cls.html = (API_ROOT / "static" / "index.html").read_text(encoding="utf-8")
        cls.main = (API_ROOT / "app" / "main.py").read_text(encoding="utf-8")

    def test_catalog_is_large_structured_and_versioned(self) -> None:
        self.assertEqual(self.catalog["version"], "5.0.0")
        self.assertGreaterEqual(self.catalog["resource_count"], 20)
        self.assertGreaterEqual(self.catalog["link_count"], 70)
        self.assertGreaterEqual(len(self.catalog["categories"]), 8)

    def test_catalog_links_are_https_or_local(self) -> None:
        for item in self.catalog["items"]:
            self.assertIn(item["status"], {"used", "recommended"})
            for link in item["links"]:
                self.assertTrue(link["url"].startswith(("https://", "/")), link)

    def test_google_drive_distribution_target_is_exposed(self) -> None:
        self.assertEqual(
            GOOGLE_DRIVE_FOLDER_URL,
            "https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0",
        )
        self.assertIn(GOOGLE_DRIVE_FOLDER_URL, self.html)

    def test_user_technology_page_and_api_are_exposed(self) -> None:
        for marker in (
            'data-view="technologies"',
            'id="view-technologies"',
            'id="technology-catalog"',
            'id="technology-drive-link"',
            "loadTechnologies()",
        ):
            self.assertIn(marker, self.html)
        self.assertIn('@app.get("/api/technologies")', self.main)

    def test_interface_keeps_literal_dom_references_resolved(self) -> None:
        ids = set(re.findall(r'\bid="([A-Za-z0-9_-]+)"', self.html))
        references = set(re.findall(r"q\('#([A-Za-z0-9_-]+)'\)", self.html))
        self.assertEqual(sorted(references - ids), [])


if __name__ == "__main__":
    unittest.main()
