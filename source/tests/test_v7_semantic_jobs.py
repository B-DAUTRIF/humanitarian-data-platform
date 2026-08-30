from __future__ import annotations

import ast
import json
import unittest
import uuid
from unittest.mock import patch

from fastapi import HTTPException

from app.v6_semantic_api import SemanticSearchRequest
from app.v7_semantic_jobs import _repro_script, export_semantic_job


class SemanticJobsTests(unittest.TestCase):
    def payload(self) -> SemanticSearchRequest:
        return SemanticSearchRequest(
            sources=["world-bank-health"],
            query="malaria",
            location="RWA",
            date_from="2020-01-01",
            date_to="2025-12-31",
        )

    def test_python_reproduction_script_is_valid_and_secret_free(self) -> None:
        script = _repro_script(self.payload(), "python")
        ast.parse(script)
        self.assertIn("HDP_LOCAL_TOKEN", script)
        self.assertNotIn("Bearer secret", script)
        self.assertIn("/api/semantic/search", script)

    def test_r_reproduction_script_uses_hdp_api(self) -> None:
        script = _repro_script(self.payload(), "r")
        self.assertIn("library(httr2)", script)
        self.assertIn("/api/semantic/search", script)
        self.assertIn("HDP_LOCAL_TOKEN", script)

    def test_json_and_csv_exports_preserve_result(self) -> None:
        job_id = uuid.uuid4()
        fake = {
            "result": {
                "query_fingerprint": "a" * 64,
                "items": [{"title": "A", "value": 1, "metadata": {"native": True}}],
            }
        }
        with patch("app.v7_semantic_jobs._job_row", return_value=fake):
            json_response = export_semantic_job(job_id, "json")
            csv_response = export_semantic_job(job_id, "csv")
        self.assertEqual(json.loads(json_response.body)["query_fingerprint"], "a" * 64)
        self.assertIn(b"title", csv_response.body)
        self.assertIn(b"metadata", csv_response.body)

    def test_geojson_export_never_invents_geometry(self) -> None:
        job_id = uuid.uuid4()
        with patch("app.v7_semantic_jobs._job_row", return_value={"result": {"items": [{"title": "A"}]}}):
            with self.assertRaises(HTTPException) as raised:
                export_semantic_job(job_id, "geojson")
        self.assertEqual(raised.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
