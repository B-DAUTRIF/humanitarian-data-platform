from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "v7_reliefweb_use_case_qualification.py"
spec = importlib.util.spec_from_file_location("v7_reliefweb_use_case_qualification", TOOL)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ReliefWebUseCaseQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = module.run_qualification()

    def test_every_feature_has_exactly_five_cases(self) -> None:
        self.assertTrue(self.report["feature_case_counts"])
        self.assertTrue(all(count == 5 for count in self.report["feature_case_counts"].values()))

    def test_every_case_has_five_cycles(self) -> None:
        self.assertTrue(all(len(case["cycles"]) == 5 for case in self.report["cases"]))

    def test_deterministic_cases_pass(self) -> None:
        failed = [case for case in self.report["cases"] if case["status"] == "DEFECT"]
        self.assertEqual(failed, [], failed[:5])

    def test_content_types_all_covered(self) -> None:
        covered = {case["content_type"] for case in self.report["cases"] if case["feature"].startswith("content_type:")}
        self.assertEqual(covered, set(module.CONTENT_TYPES))

    def test_live_blocker_is_not_hidden(self) -> None:
        self.assertEqual(self.report["live_status"], "BLOCKED_PENDING_PROVIDER_ACCEPTANCE_OF_APPNAME")
        self.assertIn("HTTP 403", self.report["live_known_observation"])
        self.assertNotEqual(self.report["status"], "QUALIFIED")


if __name__ == "__main__":
    unittest.main()
