from __future__ import annotations

import ast
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1]
API_APP = SOURCE_ROOT / "payload" / "api" / "app"
HTML = SOURCE_ROOT / "payload" / "api" / "static" / "index.html"
PROJECT_ROOT = SOURCE_ROOT.parent


class V6StaticContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.main = (API_APP / "main.py").read_text(encoding="utf-8")
        cls.features = (API_APP / "v6_features.py").read_text(encoding="utf-8")
        cls.rules = (API_APP / "v6_rules.py").read_text(encoding="utf-8")
        cls.catalog = (API_APP / "v6_catalog.py").read_text(encoding="utf-8")
        cls.actions = (API_APP / "v6_actions.py").read_text(encoding="utf-8")
        cls.action_queue = (API_APP / "v6_action_queue.py").read_text(encoding="utf-8")
        cls.action_observability = (API_APP / "v6_action_observability.py").read_text(encoding="utf-8")
        cls.data_jobs = (API_APP / "v6_data_jobs.py").read_text(encoding="utf-8")
        cls.storage = (API_APP / "v6_storage.py").read_text(encoding="utf-8")
        cls.openapi = (API_APP / "v6_openapi.py").read_text(encoding="utf-8")
        cls.backup = (API_APP / "v6_backup.py").read_text(encoding="utf-8")
        cls.migrations = (API_APP / "migrations.py").read_text(encoding="utf-8")
        cls.v5 = (API_APP / "v5_features.py").read_text(encoding="utf-8")
        cls.html = HTML.read_text(encoding="utf-8")

    def test_new_python_modules_are_syntactically_valid(self) -> None:
        for name, source in (
            ("v6_features.py", self.features),
            ("v6_rules.py", self.rules),
            ("v6_catalog.py", self.catalog),
            ("v6_actions.py", self.actions),
            ("v6_action_queue.py", self.action_queue),
            ("v6_action_observability.py", self.action_observability),
            ("v6_data_jobs.py", self.data_jobs),
            ("v6_storage.py", self.storage),
            ("v6_openapi.py", self.openapi),
            ("v6_backup.py", self.backup),
        ):
            with self.subTest(name=name):
                ast.parse(source)

    def test_application_declares_v6_without_renaming_qualified_installer(self) -> None:
        self.assertIn('APP_VERSION = "6.0.0-dev"', self.main)
        self.assertIn("app.include_router(v6_router)", self.main)
        self.assertIn("développement 6.0.0", self.html)
        self.assertIn("version 5.0.2", self.html)
        installer = (SOURCE_ROOT / "src" / "installer.c").read_text(encoding="utf-8")
        self.assertIn('#define APP_VERSION L"6.0.0-dev"', installer)

    def test_rule_connector_cache_and_policy_routes_are_exposed(self) -> None:
        for route in (
            '/rules/validate',
            '/rules/simulate',
            '/projects/{project_id}/rules',
            '/projects/{project_id}/rules/{definition_id}/evaluate',
            '/connectors/contracts/validate',
            '/connectors/contracts/diff',
            '/sources/{source_id}/endpoints',
            '/sources/{source_id}/contracts',
            '/sources/{source_id}/endpoints/{endpoint_uuid}',
            '/sources/{source_id}/endpoints/{endpoint_uuid}/state',
            '/projects/{project_id}/sources/{source_id}/endpoints/{endpoint_uuid}',
            '/sources/{source_id}/configuration',
            '/cache/key',
            '/cache/decision',
            '/projects/{project_id}/cache/materialize',
            '/projects/{project_id}/cache/{cache_entry_id}/revalidate',
            '/projects/{project_id}/cache',
            '/projects/{project_id}/sources/{source_id}/equivalents/{capability}/materialize',
            '/projects/{project_id}/catalog/import',
            '/projects/{project_id}/sources/{source_id}/catalog-schedule',
            '/projects/{project_id}/catalog-schedules',
            '/sources/{source_id}/openapi/inventory',
            '/rss/inventory-scope',
            '/rss/candidates',
            '/rss/candidates/{feed_source_id}/preview',
            '/rss/candidates/{feed_source_id}/decision',
            '/projects/{project_id}/rss/sources/{feed_source_id}/subscriptions',
            '/backups',
            '/backups/{backup_id}/prevalidate',
            '/backups/{backup_id}/restore/temporary',
            '/backups/{backup_id}/download',
            '/projects/{project_id}/data-policy',
            '/catalog',
            '/projects/{project_id}/rules/{definition_id}/inheritance',
            '/timeline',
            '/projects/{project_id}/timeline',
            '/projects/{project_id}/actions',
            '/actions/{request_id}/decision',
            '/actions/{request_id}/cancel',
            '/action-worker/run-once',
            '/projects/{project_id}/data-jobs',
            '/data-jobs/{job_id}/cancel',
        ):
            self.assertIn(route, self.features)
        self.assertIn('/api/v6/data-worker/run-once', self.main)

    def test_global_rule_inheritance_is_explicit_and_version_pinned(self) -> None:
        for marker in (
            "adopted_version_id",
            "proposed_version_id",
            "update_proposed",
            "restore_global",
            "Restaurez d'abord la règle globale",
            "v.id=i.adopted_version_id",
            "i.status IN ('current','update_proposed','rejected')",
            "rule.inheritance_decided",
        ):
            self.assertIn(marker, self.features)
        self.assertIn('version="6.0.0-002-rule-inheritance-bootstrap"', self.migrations)
        self.assertIn("ON CONFLICT (project_id,global_definition_id) DO NOTHING", self.migrations)

    def test_new_projects_initialize_v6_policy_and_global_rules(self) -> None:
        self.assertIn("INSERT INTO project_data_policies", self.main)
        self.assertIn("INSERT INTO rule_inheritance", self.main)
        self.assertIn("adopted_version_id", self.main)

    def test_v6_migration_contains_versioned_core_objects(self) -> None:
        self.assertIn('version="6.0.0-001-rules-catalog-cache"', self.migrations)
        for table in (
            "rule_definitions",
            "rule_versions",
            "rule_inheritance",
            "rule_evaluations",
            "action_requests",
            "action_executions",
            "source_api_versions",
            "source_endpoints",
            "endpoint_parameters",
            "response_fields",
            "connector_capabilities",
            "raw_metadata_snapshots",
            "catalog_records",
            "cache_entries",
            "project_data_policies",
            "application_timeline",
            "endpoint_activation_history",
            "project_endpoint_activations",
            "project_cache_references",
            "cache_revalidations",
            "equivalent_materializations",
            "catalog_ingestion_runs",
            "catalog_field_lineage",
            "project_catalog_references",
            "catalog_update_schedules",
            "rss_feed_sources",
            "rss_feed_checks",
            "database_backups",
            "operator_webauthn_credentials",
            "operator_auth_challenges",
            "operator_sessions",
            "spip_connections",
            "spip_publication_drafts",
            "spip_external_mappings",
            "spip_delivery_events",
            "mail_messages",
            "mail_attachments",
            "mail_project_links",
            "internal_notifications",
            "project_tasks",
            "signal_classifications",
            "action_drafts",
            "automated_data_jobs",
            "automated_data_job_results",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", self.migrations)
        self.assertIn('version="6.0.0-003-connector-activation"', self.migrations)
        self.assertIn('version="6.0.0-004-cache-materialization"', self.migrations)
        self.assertIn('version="6.0.0-005-catalog-lineage-scheduling"', self.migrations)
        self.assertIn('version="6.0.0-006-rss-source-lifecycle"', self.migrations)
        self.assertIn('version="6.0.0-007-database-backups"', self.migrations)
        self.assertIn('version="6.0.0-008-passkey-operator-auth"', self.migrations)
        self.assertIn('version="6.0.0-009-spip-publication-bridge"', self.migrations)
        self.assertIn('version="6.0.0-010-public-mail-ingestion"', self.migrations)
        self.assertIn('version="6.0.0-011-action-workers"', self.migrations)
        self.assertIn('version="6.0.0-012-data-job-workers"', self.migrations)

    def test_action_worker_is_transactional_idempotent_and_network_closed(self) -> None:
        for marker in (
            "FOR UPDATE SKIP LOCKED",
            "recover_stale_action_requests",
            "cancel_requested",
            "lease_expires_at",
            "automatic_request_limit",
            "ON CONFLICT (request_id) DO NOTHING",
            "action.retry_scheduled",
            "action.completed",
        ):
            self.assertIn(marker, self.action_queue)
        self.assertIn("EXECUTABLE_ACTION_TYPES", self.action_queue)
        self.assertNotIn('"webhook"}', self.action_queue)
        self.assertNotIn("download_public_file", self.action_queue)
        self.assertNotIn("subprocess", self.action_queue)

    def test_data_job_worker_is_leased_per_source_and_uses_existing_connectors(self) -> None:
        for marker in (
            "FOR UPDATE SKIP LOCKED",
            "recover_stale_data_jobs",
            "automated_data_job_results",
            "worker_lease_expired_after_acquisition",
            "data_job.retry_scheduled",
            "data_job.finished",
        ):
            self.assertIn(marker, self.data_jobs)
        self.assertIn("await execute_acquisition(", self.main)
        self.assertIn("automated_data_job_source=source", self.main)
        self.assertNotIn("download_public_file", self.data_jobs)
        for marker in (
            'data-view="actions"',
            'id="action-operation-list"',
            'id="data-job-operation-list"',
            "loadActionOperations",
            "decideActionOperation",
            "cancelDataJobOperation",
        ):
            self.assertIn(marker, self.html)
        for marker in ("jsonb_agg", "action_drafts", "automated_data_jobs", "executions", "%s::text IS NULL"):
            self.assertIn(marker, self.action_observability)

    def test_cache_materialization_is_content_addressed_and_versioned(self) -> None:
        for marker in (
            "publish_atomically",
            "pg_advisory_xact_lock",
            "shared_existing_artifact",
            "cache.revalidated",
            "cache.equivalent_materialized",
            "data_classification",
        ):
            self.assertIn(marker, self.features)
        self.assertIn("os.replace", self.storage)
        self.assertIn("os.fsync", self.storage)

    def test_catalog_preserves_raw_metadata_and_requires_field_lineage(self) -> None:
        for marker in (
            "raw_metadata_preserved",
            "preserve_unmapped_fields",
            "Une métadonnée indisponible doit être explicitement nulle",
            "Recette de lignée absente",
            "catalog.ingested",
            "catalog.schedule_updated",
            "acquisition_parameters_sha256",
        ):
            self.assertIn(marker, self.features)

    def test_openapi_inventory_is_exhaustive_but_does_not_activate_execution(self) -> None:
        for marker in (
            "HTTP_METHODS",
            "inherited_parameters",
            "requestBody",
            "response_fields",
            "seules les références OpenAPI locales sont admises",
        ):
            self.assertIn(marker, self.openapi)
        self.assertIn('"execution_activated": False', self.features)

    def test_rss_candidate_requires_preview_and_manual_approval(self) -> None:
        for marker in (
            "preview_and_parser_validation",
            "Un contrôle de flux réussi est requis avant approbation",
            "download_public_file",
            "allowed_hosts=frozenset",
            "rss.candidate_checked",
            "rss.source_decided",
        ):
            self.assertIn(marker, self.features)
        self.assertIn("feed_definition", self.main)
        self.assertIn("feed_source_id", self.main)

    def test_database_backups_cover_global_project_and_signal_scopes(self) -> None:
        for marker in (
            "create_global_dump",
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY",
            "signal_ids",
            "restore_automatically_authorized",
            "prevalidate_backup_bundle",
            "restore_global_backup_to_temporary_database",
            "restore_project_backup_to_temporary_database",
            "restore_signals_backup_to_temporary_database",
            "export_project_graph",
            "Sauvegarde non restaurable",
            "Restauration temporaire refusée",
            "verified_asset_count",
            '"projects"',
            '"signal_rules"',
            "L'empreinte de la sauvegarde est incohérente",
        ):
            self.assertIn(marker, self.features)
        self.assertIn("subprocess.run", self.backup)
        self.assertIn("information_schema.columns", self.backup)
        self.assertIn("hdp_project_backup_selection", self.backup)
        self.assertIn("PGPASSWORD", self.backup)
        self.assertIn('"restore_executed": False', self.backup)
        self.assertIn('"restore_automatically_authorized": False', self.backup)
        self.assertIn('"collision_policy": "reject_without_overwrite"', self.backup)
        self.assertIn('"temporary_database_dropped": True', self.backup)
        self.assertIn('"--single-transaction"', self.backup)
        dockerfile = (API_APP.parent / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("postgresql-client", dockerfile)

    def test_connector_activation_requires_contract_bound_test_evidence(self) -> None:
        for marker in (
            "activation_requires_validation",
            "test_report_sha256",
            "Le rapport doit viser le contrat courant",
            "Une ancienne version d'API ne peut plus être activée",
            "L'endpoint doit appartenir à la version courante et avoir des tests validés",
            "connector.endpoint_state",
            "connector.project_activation",
        ):
            self.assertIn(marker, self.features)

    def test_ui_exposes_rule_workspace_policy_and_source_submenu(self) -> None:
        for element_id in (
            "v6-rule-form",
            "v6-rule-tree",
            "v6-rule-simulate",
            "v6-rule-list",
            "v6-policy-form",
            "source-configuration-link",
            "source-endpoint-list",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn("button('Paramétrages'", self.html)

    def test_ui_proposes_a_bounded_frequency_based_stale_policy_without_silent_migration(self) -> None:
        self.assertIn("Fréquence × 3, plafond 7 jours — recommandé", self.html)
        self.assertIn("recommendationRequired?3:''", self.html)
        self.assertIn("recommendationRequired?604800:''", self.html)
        self.assertIn("Le projet reste en arbitrage manuel jusqu’à l’enregistrement", self.html)
        self.assertIn('"max_stale_mode": "manual"', self.features)

    def test_v5_metadata_and_signal_regressions_are_fixed(self) -> None:
        self.assertIn('keys = ["id", "dataset_id"', self.v5)
        self.assertIn("lookback_hours,data_grid_dimensions", self.v5)
        reservation = self.v5.index("'reserved'")
        side_effect = self.v5.index("perform_datagrid_search", reservation)
        self.assertLess(reservation, side_effect)
        self.assertIn('"temporal_coverage_explicit"', self.v5)
        self.assertIn('"license_explicit"', self.v5)

    def test_notice_and_todo_are_versioned(self) -> None:
        notice = PROJECT_ROOT / "docs" / "NOTICE_TECHNIQUE_FONCTIONNELLE_V6.md"
        api_v6 = PROJECT_ROOT / "docs" / "API_V6_DEV.md"
        architecture = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"
        wiki_home = PROJECT_ROOT / "wiki" / "Home.md"
        gate_notice = PROJECT_ROOT / "docs" / "V6_IMPLEMENTATION_GATE.md"
        gate_script = PROJECT_ROOT / "tools" / "run_v6_quality_gate.py"
        todo = (PROJECT_ROOT / "TODO_Mises_a_jour_HDP.md").read_text(encoding="utf-8")
        self.assertTrue(notice.is_file())
        self.assertIn("58 chemins V6", api_v6.read_text(encoding="utf-8"))
        self.assertIn("Compléments V6 de développement", architecture.read_text(encoding="utf-8"))
        self.assertIn("6.0.0-dev", wiki_home.read_text(encoding="utf-8"))
        self.assertTrue(gate_notice.is_file())
        self.assertTrue(gate_script.is_file())
        self.assertIn("après chaque nouvelle implémentation V6", gate_notice.read_text(encoding="utf-8"))
        self.assertIn("HDP_V6_IMPLEMENTATION_GATE", gate_script.read_text(encoding="utf-8"))
        for identifier in (
            "HDP6-010",
            "HDP6-020",
            "HDP6-030",
            "HDP6-040",
            "HDP6-070",
            "HDP6-080",
            "HDP6-090",
            "HDP6-100",
            "HDP6-110",
            "HDP6-120",
            "HDP6-130",
        ):
            self.assertIn(identifier, todo)


if __name__ == "__main__":
    unittest.main()
