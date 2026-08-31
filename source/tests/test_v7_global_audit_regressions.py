from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_contracts import Completeness, can_claim_empty_valid  # noqa: E402
from app.v6_semantic_api import SemanticSearchRequest, _project_plan  # noqa: E402


class V7GlobalAuditRegressionTests(unittest.TestCase):
    def test_non_exhaustive_search_never_claims_empty_valid(self) -> None:
        for state in (
            Completeness.BOUNDED,
            Completeness.SAMPLED,
            Completeness.PARTIAL,
            Completeness.UNKNOWN,
        ):
            for used_post_filter in (False, True):
                self.assertFalse(
                    can_claim_empty_valid(
                        completeness=state,
                        used_post_filter=used_post_filter,
                    )
                )

    def test_only_exhaustive_coverage_can_claim_empty_valid(self) -> None:
        for state in (Completeness.EXHAUSTIVE, Completeness.PAGINATED_EXHAUSTIVE):
            for used_post_filter in (False, True):
                self.assertTrue(
                    can_claim_empty_valid(
                        completeness=state,
                        used_post_filter=used_post_filter,
                    )
                )

    def test_project_parameters_reach_provider_execution_route(self) -> None:
        fake_main = types.ModuleType("app.main")
        fake_main.ensure_project = lambda project_id: None
        fake_main.get_project_source_settings = lambda project_id, source_id: {
            "enabled": True,
            "parameters": {"language": "fr", "per_page": 77},
            "schedule_defaults": {},
        }
        payload = SemanticSearchRequest(
            sources=["world-bank-health"],
            query="malaria",
            location="Rwanda",
        )
        with patch.dict(sys.modules, {"app.main": fake_main}):
            plan = _project_plan(payload, payload.sources)
        route = plan["routes"][0]
        self.assertEqual(route["provider_configuration"], {"language": "fr", "per_page": 77})
        self.assertEqual(
            plan["project_context"]["sources"]["world-bank-health"]["parameters"],
            route["provider_configuration"],
        )


if __name__ == "__main__":
    unittest.main()
