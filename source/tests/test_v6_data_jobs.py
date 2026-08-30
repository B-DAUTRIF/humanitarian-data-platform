from __future__ import annotations

import sys
import unittest
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_data_jobs import DataJobError, validate_data_job_parameters  # noqa: E402


class DataJobParametersTest(unittest.TestCase):
    def test_sources_are_explicit_bounded_and_deduplicated(self) -> None:
        result = validate_data_job_parameters(
            {
                "sources": ["HDX", "reliefweb", "hdx"],
                "query": " cholera ",
                "result_limit": 20,
                "source_parameters": {"hdx": {"start": 0}},
                "estimated_requests": 2,
            }
        )
        self.assertEqual(result["sources"], ["hdx", "reliefweb"])
        self.assertEqual(result["query"], "cholera")
        self.assertEqual(result["source_parameters"]["reliefweb"], {})

    def test_missing_source_or_query_is_rejected_before_network(self) -> None:
        for parameters in ({}, {"source": "hdx"}, {"query": "cholera"}):
            with self.subTest(parameters=parameters), self.assertRaises(DataJobError):
                validate_data_job_parameters(parameters)

    def test_secrets_and_unselected_source_parameters_are_rejected(self) -> None:
        with self.assertRaisesRegex(DataJobError, "secret"):
            validate_data_job_parameters(
                {"source": "hdx", "query": "cholera", "source_parameters": {"hdx": {"api_token": "x"}}}
            )
        with self.assertRaisesRegex(DataJobError, "non sélectionnées"):
            validate_data_job_parameters(
                {"source": "hdx", "query": "cholera", "source_parameters": {"reliefweb": {}}}
            )
