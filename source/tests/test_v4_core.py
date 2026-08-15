from __future__ import annotations

import sys
import unittest
from pathlib import Path
import re
import tempfile
import zipfile


APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.local_library import (  # noqa: E402
    normalize_update_frequency,
    script_language,
    validate_upload_content,
    validate_upload_category,
)
from app.sql_workspace import validate_readonly_sql  # noqa: E402


class LocalLibraryContractTest(unittest.TestCase):
    def test_data_scripts_and_documents_have_separate_allowlists(self) -> None:
        self.assertEqual(validate_upload_category("cases.csv", "data"), ("csv", False))
        self.assertEqual(validate_upload_category("areas.geojson", "data"), ("geojson", True))
        self.assertEqual(validate_upload_category("analyse.py", "script"), ("py", False))
        self.assertEqual(validate_upload_category("note.pdf", "document"), ("pdf", False))
        with self.assertRaisesRegex(ValueError, "refusée"):
            validate_upload_category("payload.exe", "document")

    def test_script_language_and_frequency_are_bounded(self) -> None:
        self.assertEqual(script_language("analysis.R"), "r")
        self.assertEqual(script_language("query.sql"), "sql")
        self.assertIsNone(script_language("notebook.ipynb"))
        self.assertEqual(normalize_update_frequency("Hebdomadaire "), "Hebdomadaire")
        with self.assertRaisesRegex(ValueError, "trop longue"):
            normalize_update_frequency("x" * 121)

    def test_upload_content_uses_signatures_and_rejects_active_archives(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "data.csv"
            csv_path.write_text("iso3,value\nMLI,1\n", encoding="utf-8")
            validate_upload_content(csv_path, "csv", "data")
            fake_pdf = root / "fake.pdf"
            fake_pdf.write_bytes(b"MZ executable")
            with self.assertRaisesRegex(ValueError, "PDF"):
                validate_upload_content(fake_pdf, "pdf", "document")
            macro = root / "macro.docx"
            with zipfile.ZipFile(macro, "w") as archive:
                archive.writestr("word/document.xml", "<document/>")
                archive.writestr("word/vbaProject.bin", b"macro")
            with self.assertRaisesRegex(ValueError, "macro"):
                validate_upload_content(macro, "docx", "document")


class SqlWorkspaceContractTest(unittest.TestCase):
    def test_selects_on_project_views_are_accepted(self) -> None:
        query = "SELECT source, count(*) FROM hdp_resources GROUP BY source ORDER BY source"
        self.assertEqual(validate_readonly_sql(query), query)
        self.assertEqual(
            validate_readonly_sql("EXPLAIN SELECT * FROM hdp_acquisitions LIMIT 5"),
            "EXPLAIN SELECT * FROM hdp_acquisitions LIMIT 5",
        )

    def test_mutations_and_multiple_statements_are_rejected(self) -> None:
        for query in (
            "DELETE FROM hdp_resources",
            "SELECT * FROM hdp_resources; DROP VIEW hdp_resources",
            "WITH deleted AS (DELETE FROM hdp_resources RETURNING *) SELECT * FROM deleted",
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                validate_readonly_sql(query)


class V4StaticContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main_source = (APP_ROOT / "app" / "main.py").read_text(encoding="utf-8")
        cls.html = (APP_ROOT / "static" / "index.html").read_text(encoding="utf-8")

    def test_v4_routes_are_exposed(self) -> None:
        for route in (
            "/api/projects/{project_id}/federated-search",
            "/api/projects/{project_id}/uploads",
            "/api/resources/{resource_id}/refresh-schedule",
            "/api/projects/{project_id}/sql/schema",
            "/api/projects/{project_id}/sql/query",
            "/api/projects/{project_id}/processing-runs",
            "/api/processing/operations",
            "/api/map/layers/{layer_id}",
        ):
            self.assertIn(route, self.main_source)

    def test_requested_navigation_and_inline_controls_are_visible(self) -> None:
        for marker in (
            'id="brand-home"',
            'id="view-home"',
            'id="search-source-list"',
            'id="search-source-fields"',
            'id="upload-form"',
            'id="map-local-resources"',
            'data-view="sql"',
            'id="view-sql"',
            'id="processing-form"',
            'id="processing-history"',
        ):
            self.assertIn(marker, self.html)

    def test_literal_dom_references_point_to_existing_ids(self) -> None:
        ids = set(re.findall(r'\bid="([A-Za-z0-9_-]+)"', self.html))
        references = set(re.findall(r"q\('#([A-Za-z0-9_-]+)'\)", self.html))
        self.assertEqual(sorted(references - ids), [])

    def test_base_tables_dangerous_functions_and_comma_joins_are_rejected(self) -> None:
        for query in (
            "SELECT * FROM local_resources",
            "SELECT pg_read_file('/etc/passwd') FROM hdp_resources",
            "SELECT * FROM hdp_resources, projects",
            "SELECT mystery(title) FROM hdp_resources",
        ):
            with self.subTest(query=query), self.assertRaises(ValueError):
                validate_readonly_sql(query)


if __name__ == "__main__":
    unittest.main()
