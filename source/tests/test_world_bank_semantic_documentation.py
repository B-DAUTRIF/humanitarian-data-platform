from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.providers.world_bank_health.parameters import (
    SEMANTIC_PARAMETER_MAPPING,
    WORLD_BANK_PARAMETER_DOCUMENTATION,
    parameter_documentation,
)
from app.providers.world_bank_health.semantic_interface import (
    WorldBankSemanticRequest,
    provider_semantic_search,
    router,
    semantic_contract,
)


class WorldBankSemanticDocumentationTests(unittest.TestCase):
    def test_machine_readable_parameter_matrix_has_core_native_parameters(self):
        required = {
            "country", "indicator", "source", "date", "page", "per_page", "mrv", "mrnev",
            "gapfill", "frequency", "footnote", "format", "language", "search",
        }
        self.assertTrue(required.issubset(WORLD_BANK_PARAMETER_DOCUMENTATION))

    def test_documented_but_unimplemented_capabilities_are_explicit(self):
        for name in ("topic", "incomeLevel", "region", "lendingType", "downloadformat", "dataformat"):
            self.assertIn(name, WORLD_BANK_PARAMETER_DOCUMENTATION)
            self.assertNotEqual(WORLD_BANK_PARAMETER_DOCUMENTATION[name]["qualification"], "IMPLÉMENTÉ ET QUALIFIÉ")

    def test_json_qualification_does_not_claim_xml(self):
        row = WORLD_BANK_PARAMETER_DOCUMENTATION["format"]
        self.assertEqual(row["allowed_values"], ["json"])
        self.assertIn("XML", row["constraints"])

    def test_semantic_payload_fixes_source_and_preserves_project_uuid(self):
        request = WorldBankSemanticRequest(
            project_id="00000000-0000-4000-8000-000000000001",
            query="malaria",
            location="Rwanda",
            date_from="2020-01-01",
            date_to="2025-12-31",
            result_limit=17,
        )
        canonical = request.canonical_payload()
        self.assertEqual(canonical.sources, ["world-bank-health"])
        self.assertEqual(canonical.location, "Rwanda")
        self.assertEqual(str(canonical.project_id), "00000000-0000-4000-8000-000000000001")
        self.assertNotEqual(str(canonical.project_id), canonical.location)

    def test_project_id_semantic_mapping_has_no_native_target(self):
        self.assertEqual(SEMANTIC_PARAMETER_MAPPING["project_id"]["native_targets"], [])
        self.assertIn("Never sent", SEMANTIC_PARAMETER_MAPPING["project_id"]["world_bank_translation"])

    def test_semantic_contract_points_to_canonical_router(self):
        contract = semantic_contract()
        self.assertEqual(contract["fixed_sources"], ["world-bank-health"])
        self.assertEqual(contract["canonical_router"]["plan"], "/api/semantic/plan")
        self.assertEqual(contract["canonical_router"]["search"], "/api/semantic/search")
        self.assertTrue(contract["invariants"]["location_never_overwrites_project_id"])
        self.assertTrue(contract["invariants"]["bounded_empty_result_is_not_provider_wide_absence"])

    def test_bridge_routes_are_exposed(self):
        paths = {route.path for route in router.routes}
        expected = {
            "/api/providers/world-bank-health/parameters",
            "/api/providers/world-bank-health/semantic-contract",
            "/api/providers/world-bank-health/semantic-ui",
            "/api/providers/world-bank-health/semantic/plan",
            "/api/providers/world-bank-health/semantic/search",
        }
        self.assertTrue(expected.issubset(paths))

    def test_semantic_search_delegates_to_canonical_router(self):
        source = inspect.getsource(provider_semantic_search)
        self.assertIn("semantic_search", source)
        self.assertNotIn("api.worldbank.org", source)
        self.assertNotIn("httpx", source)

    def test_parameter_documentation_counts_are_consistent(self):
        record = parameter_documentation()
        count = len(record["parameters"])
        totals = record["counts"]
        self.assertEqual(totals["documented_in_hdp_matrix"], count)
        self.assertGreater(totals["implemented_and_qualified"], 0)
        self.assertGreater(totals["planned"], 0)


if __name__ == "__main__":
    unittest.main()
