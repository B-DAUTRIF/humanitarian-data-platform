from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_contracts import Completeness, can_claim_empty_valid  # noqa: E402
from app.semantic_router import SOURCE_CAPABILITIES, build_execution_plan  # noqa: E402


class V7UseCaseMatrixTests(unittest.TestCase):
    def _plan(self, **kwargs):
        return build_execution_plan(list(SOURCE_CAPABILITIES), **kwargs)

    def test_rwanda_name_iso3_and_m49_produce_same_provider_mappings(self) -> None:
        plans = [self._plan(query="malaria", location=value) for value in ("Rwanda", "RWA", "646")]
        geographies = [plan["intent"]["geography"] for plan in plans]
        for geo in geographies:
            self.assertEqual((geo["name"], geo["iso3"], geo["m49"]), ("Rwanda", "RWA", "646"))
        mappings = [
            [(route["source"], route["native_parameters"], route["criteria"], route["executable"]) for route in plan["routes"]]
            for plan in plans
        ]
        self.assertEqual(mappings[0], mappings[1])
        self.assertEqual(mappings[1], mappings[2])

    def test_paludisme_and_malaria_have_same_canonical_provider_term(self) -> None:
        french = self._plan(query="paludisme", location="Rwanda")
        english = self._plan(query="malaria", location="Rwanda")
        self.assertEqual(french["intent"]["canonical_keywords"], "malaria")
        self.assertEqual(english["intent"]["canonical_keywords"], "malaria")
        for left, right in zip(french["routes"], english["routes"], strict=True):
            self.assertEqual(left["source"], right["source"])
            self.assertEqual(left["native_parameters"], right["native_parameters"])

    def test_reference_epidemiology_use_case_is_explicit_for_all_sources(self) -> None:
        plan = self._plan(
            query="paludisme",
            location="Rwanda",
            date_from="2020-01-01",
            date_to="2025-12-31",
        )
        self.assertEqual(len(plan["routes"]), 10)
        for route in plan["routes"]:
            self.assertTrue(route["operation"])
            self.assertIn(route["completeness"], {"exhaustive", "paginated_exhaustive", "bounded", "sampled", "partial", "unknown"})
            self.assertTrue(route["criteria"], route["source"])
            self.assertTrue(route["evidence"], route["source"])
            if not route["executable"]:
                self.assertTrue(route["warnings"], route["source"])

    def test_geography_only_never_uses_unverified_generic_fallback(self) -> None:
        plan = self._plan(location="Rwanda")
        routes = {route["source"]: route for route in plan["routes"]}
        for source in ("hdx", "dhs", "unicef-sdmx", "gdacs", "who-gho"):
            self.assertFalse(routes[source]["executable"], source)
        self.assertEqual(routes["reliefweb"]["native_parameters"]["filter[value]"], "Rwanda")
        self.assertEqual(routes["world-bank-health"]["native_parameters"]["country"], "RWA")
        self.assertEqual(routes["un-sdg"]["native_parameters"]["areaCode"], 646)
        self.assertEqual(routes["hdx-hapi"]["native_parameters"]["location_code"], "RWA")
        self.assertEqual(routes["unhcr"]["native_parameters"]["country_roles"], ["origin", "asylum"])

    def test_date_only_routes_are_explicit_about_native_or_post_filtering(self) -> None:
        plan = self._plan(date_from="2024-01-01", date_to="2024-12-31")
        allowed = {"native_filter", "translated_filter", "post_filter", "unsupported", "blocked_missing_mapping"}
        for route in plan["routes"]:
            self.assertIn(route["criteria"].get("time"), allowed, route["source"])
            if route["criteria"].get("time") == "post_filter":
                self.assertNotIn(route["completeness"], {"exhaustive", "paginated_exhaustive"})

    def test_bounded_post_filter_can_never_claim_valid_empty(self) -> None:
        self.assertFalse(
            can_claim_empty_valid(
                completeness=Completeness.BOUNDED,
                used_post_filter=True,
            )
        )

    def test_unhcr_country_roles_remain_distinct(self) -> None:
        plan = build_execution_plan(["unhcr"], query="malaria", location="Rwanda")
        route = plan["routes"][0]
        self.assertEqual(route["native_parameters"]["country_roles"], ["origin", "asylum"])
        self.assertIn("deux", " ".join(route["warnings"]).casefold())


if __name__ == "__main__":
    unittest.main()
