from __future__ import annotations

import sys
import tempfile
import unittest
import warnings
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_catalog import (  # noqa: E402
    CatalogValidationError,
    FreshnessPolicy,
    cache_decision,
    canonical_cache_key,
    contract_diff,
    maximum_stale_seconds,
    preserve_unmapped_fields,
    validate_capability_matrix,
    validate_endpoint_contract,
    validate_endpoint_transition,
)
from app.v6_actions import ActionValidationError, action_status, validate_actions  # noqa: E402
from app.v6_rules import (  # noqa: E402
    RuleValidationError,
    evaluate_rule,
    legacy_signal_rule_tree,
    rule_sha256,
    validate_rule_tree,
)
from app.v6_storage import (  # noqa: E402
    StorageValidationError,
    content_addressed_path,
    publish_atomically,
    serialize_public_content,
    validation_delay_seconds,
)
from app.v6_openapi import (  # noqa: E402
    OpenApiInventoryError,
    document_sha256,
    inventory_openapi_document,
)
from app.v6_backup import (  # noqa: E402
    BackupError,
    build_manifest,
    pg_dump_command,
    prevalidate_backup_bundle,
    publish_bundle,
    restore_global_backup_to_temporary_database,
    restore_signals_backup_to_temporary_database,
)


NOW = datetime(2026, 8, 21, 10, 0, tzinfo=UTC)


def event(identifier: str, hours_ago: int, **values):
    return {
        "id": identifier,
        "external_id": identifier,
        "occurred_at": NOW - timedelta(hours=hours_ago),
        "severity": values.pop("severity", 0.5),
        "confidence": values.pop("confidence", 0.8),
        "locations": values.pop("locations", ["France"]),
        "themes": values.pop("themes", ["cholera"]),
        **values,
    }


class RuleEngineTest(unittest.TestCase):
    def test_nested_and_or_conditions(self) -> None:
        tree = {
            "type": "group",
            "operator": "AND",
            "children": [
                {"type": "condition", "field": "locations", "op": "contains", "value": "France"},
                {
                    "type": "group",
                    "operator": "OR",
                    "children": [
                        {"type": "condition", "field": "themes", "op": "contains", "value": "cholera"},
                        {"type": "condition", "field": "themes", "op": "contains", "value": "dengue"},
                    ],
                },
            ],
        }
        result = evaluate_rule(tree, event("current", 0), [event("current", 0)], now=NOW)
        self.assertTrue(result["matched"])
        self.assertEqual(result["proof"]["operator"], "AND")
        self.assertEqual(len(result["rule_sha256"]), 64)

    def test_count_correlation_uses_window_and_filter(self) -> None:
        tree = {
            "type": "correlation",
            "mode": "count",
            "window_hours": 24,
            "filter": {"type": "condition", "field": "themes", "op": "contains", "value": "cholera"},
            "comparator": "gte",
            "threshold": 3,
        }
        history = [event("a", 1), event("b", 3), event("c", 12), event("old", 30)]
        result = evaluate_rule(tree, history[0], history, now=NOW)
        self.assertTrue(result["matched"])
        self.assertEqual(result["proof"]["count"], 3)

    def test_sequence_requires_order(self) -> None:
        tree = {
            "type": "correlation",
            "mode": "sequence",
            "window_hours": 72,
            "steps": [
                {"type": "condition", "field": "stage", "op": "eq", "value": "suspected"},
                {"type": "condition", "field": "stage", "op": "eq", "value": "confirmed"},
            ],
        }
        history = [event("suspected", 48, stage="suspected"), event("confirmed", 2, stage="confirmed")]
        self.assertTrue(evaluate_rule(tree, history[-1], history, now=NOW)["matched"])
        self.assertFalse(evaluate_rule(tree, history[-1], list(reversed(history)), now=NOW - timedelta(hours=50))["matched"])

    def test_absence_matches_when_expected_event_is_missing(self) -> None:
        tree = {
            "type": "correlation",
            "mode": "absence",
            "window_hours": 24,
            "expected": {"type": "condition", "field": "kind", "op": "eq", "value": "daily-report"},
        }
        history = [event("other", 2, kind="alert")]
        self.assertTrue(evaluate_rule(tree, history[0], history, now=NOW)["matched"])

    def test_trend_supports_fixed_and_rolling_references(self) -> None:
        fixed = {
            "type": "correlation",
            "mode": "trend",
            "field": "value",
            "aggregation": "mean",
            "current_window_hours": 24,
            "baseline_window_hours": 24,
            "reference": "fixed",
            "baseline_value": 10,
            "comparator": "gte",
            "threshold": 5,
        }
        rolling = {**fixed, "reference": "rolling"}
        rolling.pop("baseline_value")
        history = [event("baseline", 30, value=10), event("current-a", 8, value=18), event("current-b", 2, value=16)]
        self.assertTrue(evaluate_rule(fixed, history[-1], history, now=NOW)["matched"])
        self.assertTrue(evaluate_rule(rolling, history[-1], history, now=NOW)["matched"])

    def test_validation_is_strict_and_bounded(self) -> None:
        with self.assertRaises(RuleValidationError):
            validate_rule_tree({"type": "condition", "field": "x", "op": "eq", "value": 1, "unknown": True})
        node = {"type": "condition", "field": "x", "op": "eq", "value": 1}
        for _ in range(14):
            node = {"type": "group", "operator": "AND", "children": [node]}
        with self.assertRaises(RuleValidationError):
            validate_rule_tree(node)

    def test_legacy_rule_is_converted_without_losing_thresholds(self) -> None:
        tree = legacy_signal_rule_tree(
            {"min_severity": 0.4, "min_confidence": 0.6, "locations": ["France"], "themes": ["cholera"]}
        )
        self.assertEqual(tree["operator"], "AND")
        self.assertTrue(evaluate_rule(tree, event("x", 0), [event("x", 0)], now=NOW)["matched"])
        self.assertEqual(len(rule_sha256(tree)), 64)


def base_contract() -> dict:
    return {
        "source_id": "who-gho",
        "api_version": "v1",
        "endpoint_id": "Indicator.List",
        "method": "GET",
        "path": "/api/Indicator",
        "state": "inventoried",
        "documentation_url": "https://example.invalid/docs",
        "allowed_hosts": ["ghoapi.azureedge.net"],
        "parameters": [
            {
                "name": "$filter",
                "location": "query",
                "schema": {"type": "string", "maxLength": 500},
                "required": False,
                "supported": False,
            }
        ],
        "response_fields": [
            {"path": "value[].IndicatorCode", "schema": {"type": "string"}, "documented": True}
        ],
    }


class CatalogAndCacheTest(unittest.TestCase):
    def test_endpoint_contract_is_versioned_and_strict(self) -> None:
        normalized = validate_endpoint_contract(base_contract())
        self.assertEqual(normalized["method"], "GET")
        self.assertEqual(len(normalized["contract_sha256"]), 64)
        self.assertFalse(normalized["parameters"][0]["supported"])

    def test_contract_diff_detects_breaking_removal_and_type_change(self) -> None:
        previous = base_contract()
        current = base_contract()
        current["parameters"] = []
        current["response_fields"][0]["schema"] = {"type": "number"}
        diff = contract_diff(previous, current)
        self.assertTrue(diff["breaking"])
        self.assertEqual(diff["parameters"]["removed"], [["query", "$filter"]])

    def test_capability_matrix_fills_missing_common_capabilities(self) -> None:
        matrix = validate_capability_matrix(
            {"search": {"support": "native", "state": "tests_validated", "endpoint_ids": ["Indicator.List"]}}
        )
        self.assertEqual(matrix["search"]["support"], "native")
        self.assertEqual(matrix["preview"]["support"], "unavailable")

    def test_endpoint_activation_is_progressive_and_obsolete_is_terminal(self) -> None:
        self.assertEqual(
            validate_endpoint_transition("inventoried", "contract_imported"),
            ("contract_imported", "progressed"),
        )
        self.assertEqual(
            validate_endpoint_transition("tests_validated", "active_global"),
            ("active_global", "progressed"),
        )
        with self.assertRaises(CatalogValidationError):
            validate_endpoint_transition("inventoried", "tests_validated")
        with self.assertRaises(CatalogValidationError):
            validate_endpoint_transition("obsolete", "inventoried")

    def test_endpoint_can_be_suspended_and_only_resume_at_a_validated_stage(self) -> None:
        self.assertEqual(
            validate_endpoint_transition("adapter_implemented", "suspended"),
            ("suspended", "suspended"),
        )
        self.assertEqual(
            validate_endpoint_transition("suspended", "tests_validated"),
            ("tests_validated", "resumed_with_validation"),
        )
        with self.assertRaises(CatalogValidationError):
            validate_endpoint_transition("suspended", "inventoried")

    def test_cache_key_is_stable_and_rejects_secrets(self) -> None:
        arguments = {
            "source_id": "who-gho",
            "api_version": "v1",
            "endpoint_id": "Indicator.List",
            "parameters": {"query": "cholera", "page": 1},
            "output_format": "JSON",
            "connector_version": "6.0.0",
            "transformation_version": "1",
        }
        first = canonical_cache_key(**arguments)
        second = canonical_cache_key(**{**arguments, "parameters": {"page": 1, "query": "cholera"}})
        self.assertEqual(first[0], second[0])
        with self.assertRaises(CatalogValidationError):
            canonical_cache_key(**{**arguments, "parameters": {"api_key": "forbidden"}})

    def test_stale_if_error_refreshes_first_then_uses_admissible_cache(self) -> None:
        policy = FreshnessPolicy(
            project_policy="stale_if_error",
            max_stale_mode="fixed_duration",
            fixed_duration_seconds=172_800,
        )
        common = {
            "cached_at": NOW - timedelta(days=1),
            "next_validation_at": NOW - timedelta(hours=1),
            "now": NOW,
            "policy": policy,
        }
        self.assertEqual(cache_decision(**common, source_failed=False)["decision"], "refresh_required")
        self.assertEqual(cache_decision(**common, source_failed=True)["decision"], "use_stale")

    def test_all_maximum_stale_modes_are_supported_without_hidden_default(self) -> None:
        self.assertEqual(
            maximum_stale_seconds(
                FreshnessPolicy(max_stale_mode="frequency_multiple", frequency_multiple=3), 3600
            ),
            10_800,
        )
        self.assertEqual(
            maximum_stale_seconds(
                FreshnessPolicy(
                    max_stale_mode="frequency_with_project_cap",
                    frequency_multiple=10,
                    project_cap_seconds=7200,
                ),
                3600,
            ),
            7200,
        )
        self.assertIsNone(maximum_stale_seconds(FreshnessPolicy(max_stale_mode="manual"), None))

    def test_manual_maximum_age_requires_approval(self) -> None:
        decision = cache_decision(
            cached_at=NOW - timedelta(days=3),
            next_validation_at=NOW - timedelta(days=2),
            now=NOW,
            source_failed=True,
            policy=FreshnessPolicy(project_policy="stale_if_error", max_stale_mode="manual"),
        )
        self.assertEqual(decision["decision"], "pending_approval")

    def test_unmapped_raw_fields_are_preserved(self) -> None:
        unmapped = preserve_unmapped_fields(
            {"id": "x", "metadata": {"title": "A", "new_field": 42}, "items": [{"value": 1}]},
            {"id", "metadata.title", "items[].value"},
        )
        self.assertEqual(unmapped, {"metadata.new_field": 42})

    def test_public_cache_is_canonical_atomic_and_shared_by_content(self) -> None:
        first_data, media_type, suffix = serialize_public_content({"b": 2, "a": 1}, "json")
        second_data, _, _ = serialize_public_content({"a": 1, "b": 2}, "json")
        self.assertEqual(first_data, second_data)
        self.assertEqual(media_type, "application/json")
        with tempfile.TemporaryDirectory() as directory:
            first_path, first_sha, first_created = publish_atomically(
                Path(directory), "a" * 64, first_data, suffix
            )
            second_path, second_sha, second_created = publish_atomically(
                Path(directory), "b" * 64, second_data, suffix
            )
            self.assertTrue(first_created)
            self.assertFalse(second_created)
            self.assertEqual(first_path, second_path)
            self.assertEqual(first_sha, second_sha)
            self.assertEqual(first_path.read_bytes(), first_data)

    def test_cache_storage_rejects_unsafe_identifiers_and_requires_freshness_signal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(StorageValidationError):
                content_addressed_path(Path(directory), "../escape", "a" * 64, ".json")
        with self.assertRaises(StorageValidationError):
            validation_delay_seconds(source_frequency_seconds=None, source_duration_seconds=None)
        self.assertEqual(
            validation_delay_seconds(source_frequency_seconds=7200, source_duration_seconds=3600),
            3600,
        )

    def test_openapi_inventory_extracts_every_operation_parameter_body_and_response_field(self) -> None:
        specification = {
            "openapi": "3.0.3",
            "info": {"title": "Example", "version": "1"},
            "servers": [{"url": "https://api.example.org/v1"}],
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                        },
                    }
                }
            },
            "paths": {
                "/items/{item_id}": {
                    "parameters": [
                        {"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "get": {
                        "operationId": "Items.Get",
                        "parameters": [
                            {"name": "include", "in": "query", "schema": {"type": "string", "enum": ["all"]}}
                        ],
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {"schema": {"$ref": "#/components/schemas/Item"}}
                                }
                            }
                        },
                    },
                    "post": {
                        "operationId": "Items.Update",
                        "requestBody": {
                            "required": True,
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Item"}}},
                        },
                        "responses": {"204": {"description": "updated"}},
                    },
                }
            },
        }
        contracts = inventory_openapi_document(
            specification,
            source_id="example-source",
            api_version="1",
            documentation_url="https://api.example.org/openapi.json",
        )
        self.assertEqual(len(contracts), 2)
        get_contract = next(item for item in contracts if item["method"] == "GET")
        post_contract = next(item for item in contracts if item["method"] == "POST")
        self.assertEqual({item["name"] for item in get_contract["parameters"]}, {"item_id", "include"})
        self.assertEqual(post_contract["parameters"][-1]["location"], "body")
        self.assertIn("responses.200.application/json.id", {item["path"] for item in get_contract["response_fields"]})
        self.assertIn("api.example.org", get_contract["allowed_hosts"])
        self.assertEqual(len(document_sha256(specification)), 64)

    def test_openapi_inventory_refuses_remote_references(self) -> None:
        specification = {
            "openapi": "3.0.3",
            "paths": {
                "/items": {
                    "get": {
                        "parameters": [{"$ref": "https://untrusted.example/parameter.json"}],
                        "responses": {"200": {"description": "ok"}},
                    }
                }
            },
        }
        with self.assertRaises(OpenApiInventoryError):
            inventory_openapi_document(
                specification,
                source_id="example-source",
                api_version="1",
                documentation_url="https://api.example.org/openapi.json",
            )

    def test_backup_command_does_not_expose_password_and_manifest_is_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "signals.jsonl"
            data.write_text('{"id":"one"}\n', encoding="utf-8")
            command, environment = pg_dump_command(
                "postgresql://operator:very-secret@db.example:5433/hdp",
                root / "global.dump",
            )
            self.assertNotIn("very-secret", " ".join(command))
            self.assertEqual(environment["PGPASSWORD"], "very-secret")
            manifest = build_manifest(
                backup_id="signals-test",
                application_version="6.0.0-dev",
                schema_versions=["6.0.0-007-database-backups"],
                scope="signals",
                selector={"signal_ids": ["one"]},
                files=[data],
                row_counts={"signals": 1},
                created_at=NOW,
            )
            self.assertEqual(len(manifest["files"][0]["sha256"]), 64)
            self.assertFalse(manifest["restore_automatically_authorized"])
            bundle = publish_bundle(root, "signals-test", [data], manifest)
            self.assertTrue(bundle.is_file())
            validation = prevalidate_backup_bundle(bundle)
            self.assertEqual(validation["status"], "prevalidated")
            self.assertEqual(validation["file_count"], 1)
            self.assertFalse(validation["restore_automatically_authorized"])
            self.assertFalse(validation["restore_executed"])

    def test_backup_prevalidation_rejects_a_tampered_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "signals.jsonl"
            data.write_text('{"id":"one"}\n', encoding="utf-8")
            manifest = build_manifest(
                backup_id="tampered-test",
                application_version="6.0.0-dev",
                schema_versions=["6.0.0-007-database-backups"],
                scope="signals",
                selector={"signal_ids": ["one"]},
                files=[data],
                row_counts={"signals": 1},
                created_at=NOW,
            )
            manifest["files"][0]["sha256"] = "0" * 64
            bundle = publish_bundle(root, "tampered-test", [data], manifest)
            with self.assertRaisesRegex(BackupError, "empreinte incohérente"):
                prevalidate_backup_bundle(bundle)

    def test_backup_prevalidation_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "traversal.zip"
            with zipfile.ZipFile(bundle, "w") as archive:
                archive.writestr("manifest.json", "{}")
                archive.writestr("../escape.txt", "forbidden")
            with self.assertRaisesRegex(BackupError, "entrée de sauvegarde invalide"):
                prevalidate_backup_bundle(bundle)

    def test_backup_prevalidation_rejects_duplicate_entries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "duplicate.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(bundle, "w") as archive:
                    archive.writestr("manifest.json", "{}")
                    archive.writestr("manifest.json", "{}")
            with self.assertRaisesRegex(BackupError, "entrées dupliquées"):
                prevalidate_backup_bundle(bundle)

    def test_backup_prevalidation_rejects_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "symlink.zip"
            link = zipfile.ZipInfo("data/link")
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            with zipfile.ZipFile(bundle, "w") as archive:
                archive.writestr("manifest.json", "{}")
                archive.writestr(link, "target")
            with self.assertRaisesRegex(BackupError, "lien symbolique interdit"):
                prevalidate_backup_bundle(bundle)

    def test_backup_prevalidation_enforces_uncompressed_size_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "signals.jsonl"
            data.write_text('{"id":"one"}\n', encoding="utf-8")
            manifest = build_manifest(
                backup_id="limit-test",
                application_version="6.0.0-dev",
                schema_versions=["6.0.0-007-database-backups"],
                scope="signals",
                selector={"signal_ids": ["one"]},
                files=[data],
                row_counts={"signals": 1},
                created_at=NOW,
            )
            bundle = publish_bundle(root, "limit-test", [data], manifest)
            with self.assertRaisesRegex(BackupError, "taille décompressée autorisée"):
                prevalidate_backup_bundle(bundle, max_uncompressed_bytes=1)

    def test_temporary_restore_rejects_non_global_backup_before_database_access(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "signals.jsonl"
            data.write_text('{"id":"one"}\n', encoding="utf-8")
            manifest = build_manifest(
                backup_id="signals-not-restorable-globally",
                application_version="6.0.0-dev",
                schema_versions=["fixture-001"],
                scope="signals",
                selector={"signal_ids": ["one"]},
                files=[data],
                row_counts={"signals": 1},
                created_at=NOW,
            )
            bundle = publish_bundle(root, "signals-not-restorable-globally", [data], manifest)
            with self.assertRaisesRegex(BackupError, "seule une sauvegarde globale"):
                restore_global_backup_to_temporary_database(
                    bundle,
                    "postgresql://operator:secret@127.0.0.1/hdp",
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=["fixture-001"],
                )

    def test_temporary_restore_rejects_incompatible_application_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dump = root / "postgresql-global.dump"
            dump.write_bytes(b"not-opened-before-compatibility-check")
            manifest = build_manifest(
                backup_id="global-incompatible",
                application_version="5.0.2",
                schema_versions=["fixture-001"],
                scope="global",
                selector={},
                files=[dump],
                row_counts={"postgresql-global": -1},
                created_at=NOW,
            )
            bundle = publish_bundle(root, "global-incompatible", [dump], manifest)
            with self.assertRaisesRegex(BackupError, "version applicative"):
                restore_global_backup_to_temporary_database(
                    bundle,
                    "postgresql://operator:secret@127.0.0.1/hdp",
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=["fixture-001"],
                )

    def test_signal_restore_rejects_incomplete_dependency_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / "signal_events.jsonl"
            data.write_text('{"id":"one"}\n', encoding="utf-8")
            manifest = build_manifest(
                backup_id="signals-incomplete",
                application_version="6.0.0-dev",
                schema_versions=["fixture-001"],
                scope="signals",
                selector={"signal_ids": ["one"]},
                files=[data],
                row_counts={"signal_events": 1},
                created_at=NOW,
            )
            bundle = publish_bundle(root, "signals-incomplete", [data], manifest)
            with self.assertRaisesRegex(BackupError, "inventaire signaux incomplet"):
                restore_signals_backup_to_temporary_database(
                    bundle,
                    "postgresql://operator:secret@127.0.0.1/hdp",
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=["fixture-001"],
                )


class ActionPolicyTest(unittest.TestCase):
    def test_safe_action_is_queued_only_within_project_limits(self) -> None:
        action = {
            "type": "data_refresh",
            "parameters": {},
            "limits": {"estimated_requests": 2, "estimated_bytes": 1024, "estimated_duration_seconds": 5},
        }
        self.assertEqual(action_status(action, 10, 2048, 30), ("queued", "automatic_within_limits"))
        self.assertEqual(action_status(action, 1, 2048, 30)[0], "pending_approval")

    def test_action_estimates_are_strict_non_negative_integers(self) -> None:
        for invalid in (-1, True, "10", 1.5):
            with self.subTest(invalid=invalid), self.assertRaises(ActionValidationError):
                validate_actions(
                    [{"type": "notification", "parameters": {}, "limits": {"estimated_requests": invalid}}]
                )

    def test_external_actions_require_immutable_version_evidence(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_actions([{"type": "python_script", "parameters": {}, "limits": {}}])
        action = {
            "type": "python_script",
            "parameters": {
                "script_version_id": "d806e67e-9aee-4a79-9db1-b92121af81da",
                "script_sha256": "a" * 64,
            },
            "limits": {},
        }
        self.assertEqual(action_status(action, 100, 1000, 60)[0], "pending_approval")

    def test_actions_reject_nested_secret_names(self) -> None:
        with self.assertRaises(ActionValidationError):
            validate_actions(
                [{"type": "webhook", "parameters": {"headers": {"Authorization": "secret"}}, "limits": {}}]
            )


if __name__ == "__main__":
    unittest.main()
