from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.v6_semantic_api import DEFAULT_PROJECT_ID  # noqa: E402
from app.v7_semantic_ui import semantic_router_ui_safe  # noqa: E402


class SemanticUiProjectIdRegressionTest(unittest.TestCase):
    def test_simple_mode_uses_canonical_default_project_uuid(self) -> None:
        page = semantic_router_ui_safe()
        project = str(DEFAULT_PROJECT_ID)
        self.assertIn(f"const DEFAULT_PROJECT_ID='{project}'", page)
        self.assertIn("mode==='simple'?DEFAULT_PROJECT_ID", page)
        self.assertIn('id="location"', page)
        self.assertIn('id="project_id"', page)

    def test_project_field_is_not_a_geography_field(self) -> None:
        page = semantic_router_ui_safe()
        self.assertIn("Un pays comme Rwanda doit être saisi", page)
        self.assertIn("Identifiant projet invalide", page)
        self.assertIn('name="hdp_project_uuid"', page)
        self.assertIn('autocomplete="off"', page)

    def test_invalid_project_uuid_is_blocked_before_fetch(self) -> None:
        page = semantic_router_ui_safe()
        self.assertIn("function validUuid", page)
        self.assertIn("if(!validUuid(projectValue))", page)
        self.assertNotIn("project_id:q('#project_id').value", page)


if __name__ == "__main__":
    unittest.main()
