from __future__ import annotations

import sys
import unittest
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.health_sources import (  # noqa: E402
    SEARCHABLE_SOURCE_IDS,
    parse_dhs_indicators,
    parse_un_sdg_indicators,
    parse_unicef_dataflows,
    parse_who_indicators,
    parse_world_bank_indicators,
    source_catalog,
)


class HealthSourceCatalogTest(unittest.TestCase):
    def test_catalog_separates_live_connectors_and_reference_portals(self) -> None:
        catalog = source_catalog()
        self.assertEqual(len(catalog), 18)
        self.assertEqual(len({source["id"] for source in catalog}), len(catalog))
        self.assertEqual(
            {source["id"] for source in catalog if source["searchable"]},
            set(SEARCHABLE_SOURCE_IDS),
        )
        self.assertTrue(all(source["portal_url"].startswith("https://") for source in catalog))
        self.assertTrue(
            all(
                source["mode"] == "reference_portal"
                for source in catalog
                if not source["searchable"]
            )
        )

    def test_catalog_returns_an_independent_copy(self) -> None:
        first = source_catalog()
        first[0]["name"] = "modifié"
        first[0]["domains"].append("test")
        second = source_catalog()
        self.assertNotEqual(second[0]["name"], "modifié")
        self.assertNotIn("test", second[0]["domains"])


class HealthSourceParserTest(unittest.TestCase):
    def test_who_indicator_parser_filters_and_builds_observation_resource(self) -> None:
        payload = {
            "value": [
                {
                    "IndicatorCode": "WHOSIS_000001",
                    "IndicatorName": "Life expectancy at birth",
                    "Definition": "Average number of years",
                },
                {"IndicatorCode": "AIR_1", "IndicatorName": "Air pollution"},
            ]
        }
        items = parse_who_indicators(payload, "life expectancy", 10)
        self.assertEqual([item["id"] for item in items], ["WHOSIS_000001"])
        self.assertEqual(items[0]["resources"][0]["format"], "json")
        self.assertIn("WHOSIS_000001", items[0]["resources"][0]["url"])

    def test_world_bank_parser_uses_wdi_metadata_and_csv_download(self) -> None:
        payload = [
            {"page": 1, "pages": 1},
            [
                {
                    "id": "SH.DYN.MORT",
                    "name": "Mortality rate, under-5",
                    "sourceNote": "Probability per 1,000 live births",
                },
                {"id": "NY.GDP.MKTP.CD", "name": "GDP"},
            ],
        ]
        items = parse_world_bank_indicators(payload, "mortality", 5)
        self.assertEqual([item["id"] for item in items], ["SH.DYN.MORT"])
        self.assertTrue(items[0]["resources"][0]["url"].endswith("downloadformat=csv"))
        self.assertEqual(items[0]["resources"][0]["format"], "zip")

    def test_unicef_parser_handles_nested_sdmx_dataflows(self) -> None:
        payload = {
            "data": {
                "dataflows": [
                    {
                        "agencyID": "UNICEF",
                        "id": "CME",
                        "version": "1.0",
                        "name": "Child mortality estimates",
                    },
                    {
                        "agencyID": "UNICEF",
                        "id": "EDUCATION",
                        "version": "1.0",
                        "name": "Education",
                    },
                ]
            }
        }
        items = parse_unicef_dataflows(payload, "child mortality", 10)
        self.assertEqual([item["id"] for item in items], ["CME"])
        self.assertIn("format=csvfile", items[0]["resources"][0]["url"])

    def test_un_sdg_parser_filters_indicator_descriptions(self) -> None:
        payload = [
            {"code": "3.2.1", "description": "Under-five mortality rate"},
            {"code": "4.1.1", "description": "Education proficiency"},
        ]
        items = parse_un_sdg_indicators(payload, "mortality", 10)
        self.assertEqual([item["id"] for item in items], ["3.2.1"])
        self.assertIn("indicator=3.2.1", items[0]["resources"][0]["url"])

    def test_dhs_parser_keeps_aggregate_indicator_access_separate(self) -> None:
        payload = {
            "Data": [
                {
                    "IndicatorId": "CN_NUTS_C_HA2",
                    "Label": "Children stunted",
                    "Definition": "Percentage of children under age five",
                },
                {"IndicatorId": "ED_SCHL_W_PRI", "Label": "Primary education"},
            ]
        }
        items = parse_dhs_indicators(payload, "children stunted", 10)
        self.assertEqual([item["id"] for item in items], ["CN_NUTS_C_HA2"])
        self.assertIn("indicatorIds=CN_NUTS_C_HA2", items[0]["resources"][0]["url"])


if __name__ == "__main__":
    unittest.main()
