from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_router import build_execution_plan  # noqa: E402


class SemanticInputContractTests(unittest.TestCase):
    def test_completely_empty_search_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "au moins un critère"):
            build_execution_plan(["reliefweb"])

    def test_geography_only_search_remains_valid(self) -> None:
        plan = build_execution_plan(["reliefweb"], location="Rwanda")
        self.assertEqual(plan["intent"]["geography"]["iso3"], "RWA")
        self.assertTrue(plan["principles"]["semantic_request_requires_explicit_criterion"])

    def test_date_only_search_remains_valid(self) -> None:
        plan = build_execution_plan(
            ["gdacs"], date_from="2024-01-01", date_to="2024-12-31"
        )
        self.assertEqual(plan["routes"][0]["criteria"]["time"], "native_filter")


if __name__ == "__main__":
    unittest.main()
