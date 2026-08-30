from __future__ import annotations

import ast
import unittest
from html.parser import HTMLParser
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
MAIN_PATH = SOURCE_ROOT / "payload" / "api" / "app" / "main.py"
HTML_PATH = SOURCE_ROOT / "payload" / "api" / "static" / "index.html"
INSTALLER_PATH = SOURCE_ROOT / "src" / "installer.c"
RESOURCE_PATH = SOURCE_ROOT / "src" / "installer.rc"
BUILD_PATH = SOURCE_ROOT / "build.sh"
COMPOSE_PATH = SOURCE_ROOT / "payload" / "compose.yaml"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.add(value)


class IterationOneStaticContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_text = MAIN_PATH.read_text(encoding="utf-8")
        cls.html_text = HTML_PATH.read_text(encoding="utf-8")
        cls.installer_text = INSTALLER_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.main_text)

    def test_python_api_source_is_syntactically_valid(self) -> None:
        self.assertIsInstance(self.tree, ast.Module)

    def test_new_api_routes_are_present_without_removing_legacy_search(self) -> None:
        required = {
            '"/api/search"',
            '"/api/acquisitions"',
            '"/api/source-settings"',
            '"/api/source-settings/{source_id}"',
            '"/api/projects/{project_id}/sources"',
            '"/api/projects/{project_id}/sources/{source_id}"',
            '"/api/projects/{project_id}/sources/{source_id}/preview"',
        }
        for route in required:
            self.assertIn(route, self.main_text)

    def test_literal_sql_placeholder_counts_match_tuple_arguments(self) -> None:
        mismatches = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Call) or len(node.args) < 2:
                continue
            function = node.func
            if not isinstance(function, ast.Attribute) or function.attr != "execute":
                continue
            statement, parameters = node.args[:2]
            if not isinstance(statement, ast.Constant) or not isinstance(statement.value, str):
                continue
            if not isinstance(parameters, (ast.Tuple, ast.List)):
                continue
            placeholders = statement.value.count("%s")
            arguments = len(parameters.elts)
            if placeholders != arguments:
                mismatches.append((getattr(node, "lineno", 0), placeholders, arguments))
        self.assertEqual(mismatches, [])

    def test_interface_exposes_both_configuration_scopes_and_library_filters(self) -> None:
        parser = IdCollector()
        parser.feed(self.html_text)
        expected_ids = {
            "view-source-settings",
            "global-source-form",
            "project-source-form",
            "project-source-request",
            "resource-filter-source",
            "resource-filter-format",
            "resource-filter-subject",
            "resource-filter-organization",
            "resource-filter-geography",
        }
        self.assertTrue(expected_ids.issubset(parser.ids))
        self.assertIn("6.0.0", self.html_text)

    def test_legacy_25_capabilities_remain_visible(self) -> None:
        for element_id in (
            "search-form",
            "project-form",
            "github-form",
            "geodata-form",
            "script-form",
            "schedule-form",
        ):
            self.assertIn(f'id="{element_id}"', self.html_text)

    def test_windows_build_metadata_targets_version_600(self) -> None:
        self.assertIn('#define APP_VERSION L"6.0.0"', self.installer_text)
        self.assertIn("HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0.exe", BUILD_PATH.read_text(encoding="utf-8"))
        resources = RESOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("FILEVERSION 6,0,0,0", resources)
        self.assertIn('VALUE "ProductVersion", "6.0.0"', resources)

    def test_windows_upgrade_preserves_unknown_environment_lines(self) -> None:
        self.assertIn("is_managed_environment_line", self.installer_text)
        self.assertIn("append_environment_bytes", self.installer_text)
        self.assertIn("const char *cursor = existing", self.installer_text)
        for managed_key in (
            "POSTGRES_PASSWORD",
            "RELIEFWEB_APPNAME",
            "HDX_HAPI_APP_IDENTIFIER",
            "GITHUB_TOKEN",
            "HDP_PORT",
        ):
            self.assertIn(f'"{managed_key}"', self.installer_text)
        self.assertIn(".env.backup-before-v6.0.0", self.installer_text)
        self.assertIn("CopyFileW(env_path, backup_path, FALSE)", self.installer_text)
        self.assertIn("Mise à niveau d'une installation existante", self.installer_text)

    def test_upgrade_path_contains_no_destructive_database_operation(self) -> None:
        uppercase = self.main_text.upper()
        for forbidden in ("DROP TABLE", "DROP COLUMN", "TRUNCATE TABLE"):
            self.assertNotIn(forbidden, uppercase)

    def test_compose_identity_and_storage_stay_compatible(self) -> None:
        compose = COMPOSE_PATH.read_text(encoding="utf-8")
        self.assertIn("name: humanitarian-data-platform", compose)
        self.assertIn("postgres_data:/var/lib/postgresql/data", compose)
        self.assertIn("./data:/app/data", compose)
        self.assertIn('127.0.0.1:${HDP_PORT:-8080}:8080', compose)

    def test_installer_does_not_delete_docker_volumes(self) -> None:
        lowered = self.installer_text.lower()
        self.assertNotIn("down -v", lowered)
        self.assertNotIn("volume rm", lowered)


if __name__ == "__main__":
    unittest.main()
