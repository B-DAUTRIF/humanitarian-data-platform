from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_router import (  # noqa: E402
    SOURCE_CAPABILITIES,
    build_execution_plan,
    build_semantic_intent,
    resolve_geography,
)


class SemanticRouterTest(unittest.TestCase):
    def test_rwanda_is_resolved_from_name_case_insensitively(self) -> None:
        geography = resolve_geography("RWANDA")
        self.assertIsNotNone(geography)
        assert geography is not None
        self.assertEqual(geography.name, "Rwanda")
        self.assertEqual(geography.iso3, "RWA")
        self.assertEqual(geography.m49, "646")

    def test_rwanda_is_resolved_from_iso3_and_m49(self) -> None:
        self.assertEqual(resolve_geography("RWA").m49, "646")  # type: ignore[union-attr]
        self.assertEqual(resolve_geography("646").iso3, "RWA")  # type: ignore[union-attr]

    def test_exact_country_keyword_becomes_geographic_intent(self) -> None:
        intent = build_semantic_intent(query="RWANDA")
        self.assertEqual(intent.interpretation, "keyword_resolved_as_geography")
        self.assertEqual(intent.keywords, "")
        self.assertEqual(intent.location, "Rwanda")
        self.assertEqual(intent.geography.iso3, "RWA")  # type: ignore[union-attr]

    def test_non_country_keyword_is_not_rewritten(self) -> None:
        intent = build_semantic_intent(query="cholera")
        self.assertEqual(intent.interpretation, "literal")
        self.assertEqual(intent.keywords, "cholera")
        self.assertEqual(intent.location, "")
        self.assertIsNone(intent.geography)

    def test_explicit_location_preserves_keywords(self) -> None:
        intent = build_semantic_intent(query="cholera", location="Rwanda")
        self.assertEqual(intent.keywords, "cholera")
        self.assertEqual(intent.location, "Rwanda")
        self.assertEqual(intent.interpretation, "explicit_location")

    def test_all_ten_sources_receive_a_route(self) -> None:
        sources = list(SOURCE_CAPABILITIES)
        plan = build_execution_plan(sources, query="RWANDA")
        self.assertEqual(len(plan["routes"]), 10)
        self.assertEqual({r["source"] for r in plan["routes"]}, set(sources))
        for route in plan["routes"]:
            self.assertEqual(route["parameters"]["location"], "Rwanda")
            self.assertIn(route["status"], {"routable", "partial"})

    def test_unverified_provider_identifiers_are_not_invented(self) -> None:
        plan = build_execution_plan(["dhs", "hdx-hapi", "unhcr"], query="RWANDA")
        for route in plan["routes"]:
            params = route["parameters"]
            self.assertNotIn("country_ids", params)
            self.assertNotIn("location_code", params)
            self.assertNotIn("country_of_origin", params)
            self.assertNotIn("country_of_asylum", params)
            self.assertTrue(route["warnings"])

    def test_post_filter_limit_is_explicit(self) -> None:
        route = build_execution_plan(["hdx"], query="RWANDA")["routes"][0]
        self.assertEqual(route["criteria"]["geography"], "post_filter")
        self.assertTrue(any("exhaustivité" in warning for warning in route["warnings"]))

    def test_invalid_date_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_execution_plan(["hdx"], query="cholera", date_from="2026-08-30", date_to="2026-01-01")

    def test_unknown_location_remains_literal_and_is_not_claimed_as_resolved(self) -> None:
        intent = build_semantic_intent(query="cholera", location="Kigali")
        self.assertIsNone(intent.geography)
        self.assertEqual(intent.location, "Kigali")


if __name__ == "__main__":
    unittest.main()
