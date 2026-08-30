from __future__ import annotations

import unittest

from source.payload.api.app.semantic_provenance import canonical_json, query_fingerprint


class SemanticProvenanceSecurityTests(unittest.TestCase):
    def test_common_secret_key_variants_are_redacted_recursively(self) -> None:
        value = {
            "Authorization": "Bearer TOPSECRET",
            "api-key": "TOPSECRET",
            "nested": {
                "access_token": "TOPSECRET",
                "clientSecret": "TOPSECRET",
                "provider_password": "TOPSECRET",
            },
            "token_count": 12,
        }
        serialized = canonical_json(value).decode("utf-8")
        self.assertNotIn("TOPSECRET", serialized)
        self.assertIn('"token_count":12', serialized)

    def test_secret_value_changes_do_not_change_fingerprint(self) -> None:
        def plan(secret: str) -> dict:
            return {
                "schema_version": 2,
                "contract_version": "7.0.0",
                "intent": {"keywords": "malaria"},
                "project_context": {"project_id": "p"},
                "routes": [
                    {
                        "source": "reliefweb",
                        "operation": "query_documents",
                        "executable": True,
                        "project_enabled": True,
                        "native_parameters": {"api_key": secret, "country": "Rwanda"},
                        "criteria": {"geography": "translated_filter"},
                        "completeness": "bounded",
                    }
                ],
            }

        self.assertEqual(query_fingerprint(plan("ONE")), query_fingerprint(plan("TWO")))

    def test_non_secret_semantics_change_fingerprint(self) -> None:
        base = {
            "schema_version": 2,
            "contract_version": "7.0.0",
            "intent": {"keywords": "malaria"},
            "project_context": {"project_id": "p"},
            "routes": [
                {
                    "source": "world-bank-health",
                    "operation": "query_observations",
                    "executable": True,
                    "project_enabled": True,
                    "native_parameters": {"country": "RWA"},
                    "criteria": {"geography": "translated_filter"},
                    "completeness": "bounded",
                }
            ],
        }
        changed = {**base, "intent": {"keywords": "cholera"}}
        self.assertNotEqual(query_fingerprint(base), query_fingerprint(changed))


if __name__ == "__main__":
    unittest.main()
