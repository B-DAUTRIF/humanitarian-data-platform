from __future__ import annotations

import sys
import unittest
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.federated_search import filter_catalog_items, unified_federated_items  # noqa: E402
from app.source_registry import connector_definition, validate_values  # noqa: E402


class EpidemiologistCholeraSurveillanceUseCaseTest(unittest.TestCase):
    """Acceptance test for an epidemiologist investigating cholera in Mozambique."""

    SOURCES = ("who-gho", "hdx", "reliefweb", "gdacs", "hdx-hapi")

    def test_selected_sources_expose_common_epidemiology_criteria(self) -> None:
        for source_id in self.SOURCES:
            definition = connector_definition(source_id)
            properties = definition["project_schema"]["properties"]
            with self.subTest(source=source_id):
                self.assertTrue(
                    {"query", "date_from", "date_to", "location", "result_limit"}
                    <= set(properties)
                )

    def test_epidemiologist_can_build_a_bounded_cholera_query_for_each_source(self) -> None:
        for source_id in self.SOURCES:
            defaults = connector_definition(source_id)["project_defaults"]
            values = validate_values(
                source_id,
                {
                    **defaults,
                    "query": "cholera",
                    "date_from": "2026-03-01",
                    "date_to": "2026-03-31",
                    "location": "Mozambique",
                    "result_limit": 50,
                    "auto_download": False,
                },
                scope="project",
            )
            with self.subTest(source=source_id):
                self.assertEqual(values["query"], "cholera")
                self.assertEqual(values["location"], "Mozambique")
                self.assertEqual(values["date_from"], "2026-03-01")
                self.assertEqual(values["date_to"], "2026-03-31")
                self.assertLessEqual(values["result_limit"], 100)
                self.assertFalse(values["auto_download"])

    def test_federated_results_keep_only_the_target_place_and_period(self) -> None:
        source_results = [
            (
                "gdacs",
                [
                    {
                        "id": "gdacs-flood-moz",
                        "title": "Flood - Mozambique",
                        "date": "2026-03-04T00:00:00Z",
                        "geographic_scope": "Mozambique",
                        "resources": [{"format": "geojson", "url": "https://example.test/gdacs.geojson"}],
                    },
                    {
                        "id": "gdacs-madagascar",
                        "title": "Flood - Madagascar",
                        "date": "2026-03-04",
                        "geographic_scope": "Madagascar",
                    },
                ],
            ),
            (
                "reliefweb",
                [
                    {
                        "id": "rw-cholera-moz",
                        "title": "Cholera situation update - Mozambique",
                        "date": "2026-03-18",
                        "geographic_scope": "Mozambique",
                        "resources": [{"format": "html", "url": "https://example.test/report"}],
                    },
                    {
                        "id": "rw-old",
                        "title": "Cholera archive - Mozambique",
                        "date": "2026-02-28",
                        "geographic_scope": "Mozambique",
                    },
                ],
            ),
            (
                "who-gho",
                [
                    {
                        "id": "who-cholera",
                        "title": "Cholera indicator - Mozambique",
                        "date": "2026-03-20",
                        "geographic_scope": "Mozambique",
                        "resources": [{"format": "json", "url": "https://example.test/who.json"}],
                    }
                ],
            ),
        ]

        filtered = [
            (
                source_id,
                filter_catalog_items(
                    items,
                    date_from="2026-03-01",
                    date_to="2026-03-31",
                    location="mozambique",
                ),
            )
            for source_id, items in source_results
        ]
        unified = unified_federated_items(filtered)

        self.assertEqual(
            [item["id"] for item in unified],
            ["who-cholera", "rw-cholera-moz", "gdacs-flood-moz"],
        )
        self.assertEqual(
            {item["connector_id"] for item in unified},
            {"who-gho", "reliefweb", "gdacs"},
        )
        self.assertTrue(all(item.get("date") for item in unified))
        self.assertTrue(all("Mozambique" in item.get("title", "") for item in unified))

    def test_surveillance_output_preserves_source_and_machine_readable_resources(self) -> None:
        unified = unified_federated_items(
            [
                (
                    "gdacs",
                    [
                        {
                            "id": "event-1",
                            "title": "Flood - Mozambique",
                            "date": "2026-03-04",
                            "geographic_scope": "Mozambique",
                            "resources": [{"format": "geojson", "url": "https://example.test/event.geojson"}],
                        }
                    ],
                ),
                (
                    "who-gho",
                    [
                        {
                            "id": "indicator-1",
                            "title": "Cholera indicator - Mozambique",
                            "date": "2026-03-20",
                            "geographic_scope": "Mozambique",
                            "resources": [{"format": "json", "url": "https://example.test/indicator.json"}],
                        }
                    ],
                ),
            ]
        )

        self.assertEqual({item["connector_id"] for item in unified}, {"gdacs", "who-gho"})
        formats = {
            resource["format"]
            for item in unified
            for resource in item.get("resources", [])
        }
        self.assertTrue({"geojson", "json"} <= formats)


if __name__ == "__main__":
    unittest.main()
