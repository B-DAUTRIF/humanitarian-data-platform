from __future__ import annotations

import ast
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = SOURCE_ROOT / "payload" / "github-api" / "app.py"
COMPOSE_PATH = SOURCE_ROOT / "payload" / "compose.yaml"


class GitHubApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = APP_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.compose = COMPOSE_PATH.read_text(encoding="utf-8")

    def test_gateway_is_valid_python_and_final_version(self) -> None:
        self.assertIsInstance(self.tree, ast.Module)
        self.assertIn('APP_VERSION = "5.0.0"', self.source)
        self.assertIn('"X-GitHub-Api-Version": API_VERSION', self.source)

    def test_gateway_exposes_bounded_classic_github_functions(self) -> None:
        for route in (
            "/repository", "/branches", "/commits", "/issues", "/pulls",
            "/releases", "/workflows", "/contents/{content_path:path}",
            "/rate-limit", "/workflows/{workflow_id}/dispatch",
        ):
            self.assertIn(f'("{route}"', self.source)
        self.assertIn("per_page: int = Query(30, ge=1, le=100)", self.source)

    def test_writes_are_disabled_by_default_and_token_is_never_returned(self) -> None:
        self.assertIn('GITHUB_API_WRITE_ENABLED", "false"', self.source)
        self.assertIn("def require_write()", self.source)
        self.assertNotIn('"token": TOKEN', self.source)
        self.assertNotIn('"github_token": TOKEN', self.source)

    def test_compose_uses_one_authenticated_local_api(self) -> None:
        self.assertNotIn("  github-api:", self.compose)
        self.assertIn('127.0.0.1:${HDP_PORT:-8080}:8080', self.compose)
        self.assertIn("HDP_LOCAL_TOKEN: ${HDP_LOCAL_TOKEN}", self.compose)
        api = self.compose.split("  api:", 1)[1]
        self.assertIn("read_only: true", api)
        self.assertIn('cap_drop: ["ALL"]', api)
        self.assertIn('security_opt: ["no-new-privileges:true"]', api)


if __name__ == "__main__":
    unittest.main()
