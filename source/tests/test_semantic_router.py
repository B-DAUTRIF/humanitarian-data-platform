from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_contracts import Completeness, can_claim_empty_valid  # noqa: E402
from app.semantic_provenance import query_fingerprint, result_snapshot_hash  # noqa: E402
from app.semantic_router import SOURCE_CAPABILITIES, build_execution_plan, build_semantic_intent, resolve_geography  # noqa: E402


class SemanticRouterTest(unittest.TestCase):
    def test_rwanda_name_iso3_m49_resolve_same_entity(self) -> None:
        for value in ("RWANDA", "RWA", "646"):
            geo = resolve_geography(value)
            self.assertIsNotNone(geo)
            assert geo is not None
            self.assertEqual((geo.name, geo.iso3, geo.m49), ("Rwanda", "RWA", "646"))

    def test_paludisme_translation_is_explicit(self) -> None:
        intent = build_semantic_intent(query="paludisme", location="Rwanda")
        self.assertEqual(intent.keywords, "paludisme")
        self.assertEqual(intent.canonical_keywords, "malaria")
        self.assertTrue(intent.semantic_notes)

    def test_country_keyword_becomes_geographic_intent(self) -> None:
        intent = build_semantic_intent(query="RWANDA")
        self.assertEqual(intent.interpretation, "keyword_resolved_as_geography")
        self.assertEqual(intent.keywords, "")
        self.assertEqual(intent.location, "Rwanda")

    def test_all_ten_sources_have_operation_and_evidence(self) -> None:
        plan = build_execution_plan(list(SOURCE_CAPABILITIES), query="paludisme", location="Rwanda", date_from="2020-01-01", date_to="2025-12-31")
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(plan["contract_version"], "7.0.0")
        self.assertEqual(len(plan["routes"]), 10)
        self.assertRegex(plan["query_fingerprint"], r"^[0-9a-f]{64}$")
        for route in plan["routes"]:
            self.assertTrue(route["operation"])
            self.assertIn("executable", route)
            self.assertIn("completeness", route)
            self.assertTrue(route["evidence"])

    def test_reliefweb_uses_documented_country_and_date_filters(self) -> None:
        route = build_execution_plan(["reliefweb"], query="cholera", location="Rwanda", date_from="2020-01-01", date_to="2025-12-31")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "translated_filter")
        self.assertEqual(route["native_parameters"]["filter[field]"], "country")
        self.assertEqual(route["native_parameters"]["filter[value]"], "Rwanda")
        self.assertEqual(route["native_parameters"]["filter_date_field"], "date.created")

    def test_hapi_rwanda_uses_verified_iso3_location_code(self) -> None:
        route = build_execution_plan(["hdx-hapi"], query="RWANDA")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "translated_filter")
        self.assertEqual(route["native_parameters"]["location_code"], "RWA")
        self.assertEqual(route["parameters"]["location_code"], "RWA")

    def test_unhcr_generic_country_preserves_both_roles(self) -> None:
        route = build_execution_plan(["unhcr"], query="RWANDA")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["native_parameters"]["iso3"], "RWA")
        self.assertEqual(route["native_parameters"]["country_roles"], ["origin", "asylum"])

    def test_un_sdg_uses_m49_and_year_range(self) -> None:
        route = build_execution_plan(["un-sdg"], query="malaria", location="Rwanda", date_from="2020-01-01", date_to="2025-12-31")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["native_parameters"]["areaCode"], 646)
        self.assertEqual(route["native_parameters"]["timePeriodStart"], 2020)
        self.assertEqual(route["native_parameters"]["timePeriodEnd"], 2025)

    def test_world_bank_uses_iso3_and_year_range(self) -> None:
        route = build_execution_plan(["world-bank-health"], query="malaria", location="Rwanda", date_from="2020-01-01", date_to="2025-12-31")["routes"][0]
        self.assertTrue(route["executable"])
        self.assertEqual(route["native_parameters"]["country"], "RWA")
        self.assertEqual(route["native_parameters"]["date"], "2020:2025")

    def test_dhs_does_not_substitute_iso3_as_dhs_country_id(self) -> None:
        route = build_execution_plan(["dhs"], query="RWANDA")["routes"][0]
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")
        self.assertEqual(route["native_parameters"]["iso3_lookup"], "RWA")
        self.assertNotIn("country_ids", route["parameters"])

    def test_hdx_geography_only_is_blocked(self) -> None:
        route = build_execution_plan(["hdx"], query="RWANDA")["routes"][0]
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")

    def test_who_observation_route_is_schema_drift_blocked(self) -> None:
        route = build_execution_plan(["who-gho"], query="malaria", location="Rwanda")["routes"][0]
        self.assertFalse(route["executable"])
        self.assertTrue(any("requalification" in warning for warning in route["warnings"]))

    def test_non_exhaustive_post_filter_cannot_claim_empty(self) -> None:
        for state in (Completeness.BOUNDED, Completeness.SAMPLED, Completeness.PARTIAL, Completeness.UNKNOWN):
            self.assertFalse(can_claim_empty_valid(completeness=state, used_post_filter=True))
        self.assertTrue(can_claim_empty_valid(completeness=Completeness.EXHAUSTIVE, used_post_filter=True))
        self.assertTrue(can_claim_empty_valid(completeness=Completeness.PAGINATED_EXHAUSTIVE, used_post_filter=True))

    def test_fingerprints_are_deterministic_and_distinct(self) -> None:
        plan = build_execution_plan(["un-sdg", "world-bank-health"], query="paludisme", location="Rwanda")
        fp = plan["query_fingerprint"]
        copy = dict(plan)
        copy.pop("query_fingerprint")
        self.assertEqual(fp, query_fingerprint(copy))
        self.assertNotEqual(result_snapshot_hash([], [{"value": 1}]), result_snapshot_hash([], [{"value": 2}]))

    def test_invalid_date_range_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_execution_plan(["reliefweb"], query="cholera", date_from="2026-08-30", date_to="2026-01-01")


if __name__ == "__main__":
    unittest.main()
