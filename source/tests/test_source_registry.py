from __future__ import annotations

import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.source_registry import (  # noqa: E402
    CONNECTORS,
    GLOBAL_SCHEMA,
    connector_definition,
    enrich_source_catalog,
    merge_values,
    request_preview,
    validate_values,
)


class SourceRegistryContractTest(unittest.TestCase):
    def test_seven_live_connectors_have_versioned_contracts(self) -> None:
        self.assertEqual(
            set(CONNECTORS),
            {
                "hdx",
                "reliefweb",
                "who-gho",
                "world-bank-health",
                "unicef-sdmx",
                "un-sdg",
                "dhs",
            },
        )
        for source_id in CONNECTORS:
            definition = connector_definition(source_id)
            self.assertEqual(definition["registry_version"], "3.0.0-iteration-1")
            self.assertTrue(definition["documentation_evidence"])
            self.assertEqual(
                merge_values(source_id, definition["project_defaults"], scope="project"),
                definition["project_defaults"],
            )

    def test_empty_stored_query_is_valid_but_bounded(self) -> None:
        values = connector_definition("hdx")["project_defaults"]
        self.assertEqual(values["query"], "")
        values["query"] = "x" * 201
        with self.assertRaisesRegex(ValueError, "trop long"):
            validate_values("hdx", values, scope="project")

    def test_global_settings_reject_unknown_and_invalid_values(self) -> None:
        defaults = {
            name: definition["default"]
            for name, definition in GLOBAL_SCHEMA["properties"].items()
        }
        self.assertEqual(validate_values("hdx", defaults, scope="global"), defaults)
        with self.assertRaisesRegex(ValueError, "Paramètres inconnus"):
            validate_values("hdx", {**defaults, "token": "secret"}, scope="global")
        with self.assertRaisesRegex(ValueError, "maximum"):
            validate_values("hdx", {**defaults, "timeout_seconds": 999}, scope="global")

    def test_array_parameters_are_validated_and_deduplicated(self) -> None:
        defaults = connector_definition("dhs")["project_defaults"]
        values = validate_values(
            "dhs",
            {**defaults, "query": "cholera", "country_ids": ["ML", "ML", "SN"]},
            scope="project",
        )
        self.assertEqual(values["country_ids"], ["ML", "SN"])
        with self.assertRaisesRegex(ValueError, "format attendu"):
            validate_values(
                "dhs",
                {**defaults, "query": "cholera", "country_ids": ["M L"]},
                scope="project",
            )

    def test_preview_stays_on_allowlist_and_never_contains_a_secret(self) -> None:
        for source_id in CONNECTORS:
            definition = connector_definition(source_id)
            values = {**definition["project_defaults"], "query": "cholera"}
            preview = request_preview(source_id, values)
            self.assertIn(urlparse(preview["url"]).hostname, definition["allowed_hosts"])
            self.assertIn(preview["display_url"], preview["curl"])
            self.assertNotIn("real-secret", preview["curl"])
        reliefweb = request_preview(
            "reliefweb",
            {**connector_definition("reliefweb")["project_defaults"], "query": "cholera"},
        )
        self.assertIn("RELIEFWEB_APPNAME", reliefweb["display_url"])

    def test_reference_portal_is_enriched_without_project_contract(self) -> None:
        catalog = enrich_source_catalog(
            [
                {
                    "id": "reference",
                    "documentation_url": "https://example.org/docs",
                    "searchable": False,
                }
            ]
        )
        self.assertIsNone(catalog[0]["project_schema"])
        self.assertEqual(catalog[0]["documentation_evidence"], ["https://example.org/docs"])


if __name__ == "__main__":
    unittest.main()
