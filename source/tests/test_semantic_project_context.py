from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import patch

from app.v6_semantic_api import SemanticSearchRequest, _blocked_status, _project_plan


class SemanticProjectContextTests(unittest.TestCase):
    def fake_main(self) -> types.ModuleType:
        module = types.ModuleType("app.main")
        module.ensure_project = lambda project_id: None
        module.get_project_source_settings = lambda project_id, source_id: {
            "project_id": str(project_id),
            "source_id": source_id,
            "enabled": source_id != "hdx",
            "parameters": {"example": source_id},
            "schedule_defaults": {},
        }
        return module

    def test_project_disabled_source_is_never_executable(self) -> None:
        payload = SemanticSearchRequest(
            sources=["hdx", "world-bank-health"],
            query="malaria",
            location="Rwanda",
            date_from="2020-01-01",
            date_to="2025-12-31",
        )
        with patch.dict(sys.modules, {"app.main": self.fake_main()}):
            plan = _project_plan(payload, payload.sources)
        routes = {route["source"]: route for route in plan["routes"]}
        self.assertFalse(routes["hdx"]["executable"])
        self.assertTrue(routes["hdx"]["project_blocked"])
        self.assertEqual(_blocked_status(routes["hdx"]), "configuration_error")
        self.assertTrue(routes["world-bank-health"]["project_enabled"])
        self.assertEqual(plan["project_context"]["project_id"], str(payload.project_id))
        self.assertEqual(len(plan["query_fingerprint"]), 64)

    def test_project_context_changes_query_fingerprint(self) -> None:
        payload = SemanticSearchRequest(sources=["world-bank-health"], query="malaria", location="RWA")
        enabled_main = self.fake_main()
        disabled_main = self.fake_main()
        disabled_main.get_project_source_settings = lambda project_id, source_id: {
            "enabled": False,
            "parameters": {},
            "schedule_defaults": {},
        }
        with patch.dict(sys.modules, {"app.main": enabled_main}):
            enabled = _project_plan(payload, payload.sources)
        with patch.dict(sys.modules, {"app.main": disabled_main}):
            disabled = _project_plan(payload, payload.sources)
        self.assertNotEqual(enabled["query_fingerprint"], disabled["query_fingerprint"])


if __name__ == "__main__":
    unittest.main()
