from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_contracts import Completeness, can_claim_empty_valid  # noqa: E402
from app.semantic_router import SOURCE_CAPABILITIES, build_execution_plan, build_semantic_intent, resolve_geography  # noqa: E402


class SemanticRouterTest(unittest.TestCase):
    def test_rwanda_name_iso3_m49_resolve_same_entity(self) -> None:
        for value in ("RWANDA", "RWA", "646"):
            geo = resolve_geography(value)
            self.assertIsNotNone(geo)
            assert geo is not None
            self.assertEqual((geo.name, geo.iso3, geo.m49), ("Rwanda", "RWA", "646"))

    def test_country_keyword_becomes_geographic_intent(self) -> None:
        intent = build_semantic_intent(query="RWANDA")
        self.assertEqual(intent.interpretation, "keyword_resolved_as_geography")
        self.assertEqual(intent.keywords, "")
        self.assertEqual(intent.location, "Rwanda")

    def test_literal_keyword_is_preserved(self) -> None:
        intent = build_semantic_intent(query="cholera")
        self.assertEqual(intent.keywords, "cholera")
        self.assertIsNone(intent.geography)

    def test_all_ten_sources_receive_explicit_operations(self) -> None:
        plan = build_execution_plan(list(SOURCE_CAPABILITIES), query="RWANDA")
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(len(plan["routes"]), 10)
        for route in plan["routes"]:
            self.assertTrue(route["operation"])
            self.assertIn("executable", route)
            self.assertIn("completeness", route)
            self.assertIn("evidence", route)

    def test_reliefweb_rwanda_uses_documented_country_filter(self) -> None:
        route = build_execution_plan(["reliefweb"], query="RWANDA")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "translated_filter")
        self.assertEqual(route["native_parameters"]["filter[field]"], "country")
        self.assertEqual(route["native_parameters"]["filter[value]"], "Rwanda")

    def test_hdx_geography_only_is_not_fake_post_filtered(self) -> None:
        route = build_execution_plan(["hdx"], query="RWANDA")["routes"][0]
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")

    def test_provider_specific_ids_are_not_invented(self) -> None:
        plan = build_execution_plan(["dhs", "hdx-hapi", "unhcr"], query="RWANDA")
        for route in plan["routes"]:
            self.assertFalse(route["executable"])
            self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")

    def test_non_exhaustive_post_filter_cannot_claim_empty(self) -> None:
        for state in (Completeness.BOUNDED, Completeness.SAMPLED, Completeness.PARTIAL, Completeness.UNKNOWN):
            self.assertFalse(can_claim_empty_valid(completeness=state, used_post_filter=True))
        self.assertTrue(can_claim_empty_valid(completeness=Completeness.EXHAUSTIVE, used_post_filter=True))
        self.assertTrue(can_claim_empty_valid(completeness=Completeness.PAGINATED_EXHAUSTIVE, used_post_filter=True))

    def test_invalid_date_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_execution_plan(["reliefweb"], query="cholera", date_from="2026-08-30", date_to="2026-01-01")

    def test_unknown_location_is_not_claimed_as_resolved(self) -> None:
        intent = build_semantic_intent(query="cholera", location="Kigali")
        self.assertIsNone(intent.geography)
        self.assertEqual(intent.location, "Kigali")


if __name__ == "__main__":
    unittest.main()
