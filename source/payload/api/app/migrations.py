from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Migration:
    version: str
    description: str
    statements: tuple[str, ...]


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version="3.0.0-001-source-settings",
        description="Registre configurable des sources et paramètres par projet",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS source_global_settings (
                source_id TEXT PRIMARY KEY,
                settings JSONB NOT NULL DEFAULT '{}'::jsonb,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_source_settings (
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                schedule_defaults JSONB NOT NULL DEFAULT '{}'::jsonb,
                updated_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (project_id, source_id)
            )
            """,
            "ALTER TABLE acquisitions ADD COLUMN IF NOT EXISTS parameters JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE schedules ADD COLUMN IF NOT EXISTS parameters JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS subject TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS geographic_scope TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS resource_type TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS organization TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb",
            """
            CREATE INDEX IF NOT EXISTS acquisitions_project_source_idx
            ON acquisitions(project_id, source, retrieved_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS local_resources_library_idx
            ON local_resources(project_id, source, format, updated_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS project_source_settings_project_idx
            ON project_source_settings(project_id, source_id)
            """,
        ),
    ),
    Migration(
        version="3.0.0-002-script-execution",
        description="Versions immuables et exécutions Python/R isolées sans réseau",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS project_execution_settings (
                project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                python_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                r_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                timeout_seconds INTEGER NOT NULL DEFAULT 60,
                max_output_bytes INTEGER NOT NULL DEFAULT 262144,
                network_policy TEXT NOT NULL DEFAULT 'disabled',
                allowed_hosts JSONB NOT NULL DEFAULT '[]'::jsonb,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS script_versions (
                id UUID PRIMARY KEY,
                script_id UUID NOT NULL REFERENCES project_scripts(id) ON DELETE CASCADE,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                version_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                language TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                content_sha256 CHAR(64) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (script_id, version_number)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS script_executions (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                script_id UUID NOT NULL REFERENCES project_scripts(id) ON DELETE CASCADE,
                script_version_id UUID NOT NULL REFERENCES script_versions(id),
                language TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_at TIMESTAMPTZ NOT NULL,
                started_at TIMESTAMPTZ,
                finished_at TIMESTAMPTZ,
                timeout_seconds INTEGER NOT NULL,
                max_output_bytes INTEGER NOT NULL,
                network_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                exit_code INTEGER,
                stdout TEXT NOT NULL DEFAULT '',
                stderr TEXT NOT NULL DEFAULT '',
                stdout_sha256 CHAR(64),
                stderr_sha256 CHAR(64),
                report_path TEXT,
                report_sha256 CHAR(64),
                error TEXT
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS script_versions_script_idx
            ON script_versions(script_id, version_number DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS script_executions_project_idx
            ON script_executions(project_id, requested_at DESC)
            """,
        ),
    ),
    Migration(
        version="3.0.0-003-rss",
        description="Registre RSS officiel et abonnements par projet",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS rss_subscriptions (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                registry_id TEXT NOT NULL,
                name TEXT NOT NULL,
                query TEXT NOT NULL DEFAULT '',
                language TEXT NOT NULL DEFAULT 'en',
                interval_minutes INTEGER NOT NULL DEFAULT 360,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                next_fetch_at TIMESTAMPTZ NOT NULL,
                last_fetch_at TIMESTAMPTZ,
                last_status TEXT,
                last_error TEXT,
                etag TEXT,
                last_modified TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                archived_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rss_items (
                id UUID PRIMARY KEY,
                subscription_id UUID NOT NULL REFERENCES rss_subscriptions(id) ON DELETE CASCADE,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                published_at TIMESTAMPTZ,
                raw JSONB NOT NULL DEFAULT '{}'::jsonb,
                first_seen_at TIMESTAMPTZ NOT NULL,
                UNIQUE (subscription_id, external_id)
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS rss_subscriptions_due_idx
            ON rss_subscriptions(enabled, next_fetch_at)
            """,
            """
            CREATE INDEX IF NOT EXISTS rss_items_subscription_idx
            ON rss_items(subscription_id, published_at DESC, first_seen_at DESC)
            """,
        ),
    ),
    Migration(
        version="3.0.0-004-mapping",
        description="Couches GeoJSON PostGIS et export QGIS/R",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS map_layers (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                resource_id UUID REFERENCES local_resources(id) ON DELETE SET NULL,
                name TEXT NOT NULL,
                feature_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                UNIQUE (project_id, resource_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS map_features (
                id UUID PRIMARY KEY,
                layer_id UUID NOT NULL REFERENCES map_layers(id) ON DELETE CASCADE,
                properties JSONB NOT NULL DEFAULT '{}'::jsonb,
                geom geometry(Geometry, 4326),
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS map_layers_project_idx
            ON map_layers(project_id, updated_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS map_features_layer_idx
            ON map_features(layer_id)
            """,
            """
            CREATE INDEX IF NOT EXISTS map_features_geom_idx
            ON map_features USING GIST(geom)
            """,
        ),
    ),
    Migration(
        version="4.0.0-001-federated-lineage",
        description="Recherches fédérées et lignée des données brut/normalisé/dérivé",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS federated_searches (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                query TEXT NOT NULL,
                criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
                sources JSONB NOT NULL DEFAULT '[]'::jsonb,
                status TEXT NOT NULL,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS federated_search_members (
                search_id UUID NOT NULL REFERENCES federated_searches(id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                acquisition_id UUID REFERENCES acquisitions(id) ON DELETE SET NULL,
                status TEXT NOT NULL,
                item_count INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                PRIMARY KEY (search_id, source_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS data_artifacts (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                stage TEXT NOT NULL CHECK (stage IN ('raw', 'normalized', 'derived')),
                acquisition_id UUID REFERENCES acquisitions(id) ON DELETE SET NULL,
                resource_id UUID REFERENCES local_resources(id) ON DELETE SET NULL,
                script_execution_id UUID REFERENCES script_executions(id) ON DELETE SET NULL,
                parent_artifact_id UUID REFERENCES data_artifacts(id) ON DELETE SET NULL,
                path TEXT,
                sha256 CHAR(64),
                media_type TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS federated_searches_project_idx
            ON federated_searches(project_id, started_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS data_artifacts_project_stage_idx
            ON data_artifacts(project_id, stage, created_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS data_artifacts_parent_idx
            ON data_artifacts(parent_artifact_id)
            """,
        ),
    ),
    Migration(
        version="4.0.0-002-local-library",
        description="Téléversements locaux et planification de l’actualisation par fichier",
        statements=(
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS origin_kind TEXT NOT NULL DEFAULT 'download'",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS update_frequency TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS original_filename TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ",
            """
            CREATE TABLE IF NOT EXISTS resource_refresh_schedules (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                resource_id UUID NOT NULL REFERENCES local_resources(id) ON DELETE CASCADE,
                mode TEXT NOT NULL CHECK (mode IN ('source_acquisition', 'manual_replacement')),
                interval_minutes INTEGER NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                next_run_at TIMESTAMPTZ NOT NULL,
                last_run_at TIMESTAMPTZ,
                last_status TEXT,
                last_error TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                archived_at TIMESTAMPTZ,
                UNIQUE (resource_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS resource_refresh_runs (
                id UUID PRIMARY KEY,
                refresh_schedule_id UUID NOT NULL REFERENCES resource_refresh_schedules(id) ON DELETE CASCADE,
                acquisition_id UUID REFERENCES acquisitions(id) ON DELETE SET NULL,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                status TEXT NOT NULL,
                error TEXT
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS resource_refresh_due_idx
            ON resource_refresh_schedules(enabled, next_run_at)
            """,
            """
            CREATE INDEX IF NOT EXISTS resource_refresh_project_idx
            ON resource_refresh_schedules(project_id, updated_at DESC)
            """,
        ),
    ),
    Migration(
        version="4.0.0-003-sql-workspace",
        description="Vues SQL en lecture seule et limitées au projet actif",
        statements=(
            """
            CREATE OR REPLACE VIEW hdp_acquisitions AS
            SELECT id, project_id, schedule_id, source, query, retrieved_at,
                   sha256, item_count, parameters
            FROM acquisitions
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE OR REPLACE VIEW hdp_resources AS
            SELECT id, project_id, acquisition_id, source, dataset_id, resource_id,
                   title, format, filename, sha256, size_bytes, content_type, status,
                   created_at, updated_at, m49_code, iso3_code, cod_family, cod_level,
                   publisher, license_id, subject, published_at, geographic_scope,
                   resource_type, organization, origin_kind, update_frequency, uploaded_at
            FROM local_resources
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
                  AND deleted_at IS NULL
            """,
            """
            CREATE OR REPLACE VIEW hdp_schedules AS
            SELECT id, project_id, name, source, query, result_limit, auto_download,
                   interval_minutes, enabled, next_run_at, last_run_at, last_status,
                   last_error, created_at, updated_at
            FROM schedules
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
                  AND archived_at IS NULL
            """,
            """
            CREATE OR REPLACE VIEW hdp_artifacts AS
            SELECT id, project_id, stage, acquisition_id, resource_id,
                   script_execution_id, parent_artifact_id, path, sha256,
                   media_type, metadata, created_at
            FROM data_artifacts
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE OR REPLACE VIEW hdp_federated_searches AS
            SELECT id, project_id, query, criteria, sources, status,
                   started_at, finished_at
            FROM federated_searches
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE TABLE IF NOT EXISTS sql_query_audit (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                query_sha256 CHAR(64) NOT NULL,
                status TEXT NOT NULL,
                row_count INTEGER NOT NULL DEFAULT 0,
                duration_ms INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                executed_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS sql_query_audit_project_idx
            ON sql_query_audit(project_id, executed_at DESC)
            """,
        ),
    ),
    Migration(
        version="4.0.0-004-processing",
        description="Recettes guidées, exécutions reproductibles et lignée explicite",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS processing_recipes (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                definition JSONB NOT NULL,
                definition_sha256 CHAR(64) NOT NULL,
                generated_script_id UUID REFERENCES project_scripts(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS processing_runs (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                recipe_id UUID NOT NULL REFERENCES processing_recipes(id),
                input_resource_id UUID NOT NULL REFERENCES local_resources(id),
                output_resource_id UUID REFERENCES local_resources(id) ON DELETE SET NULL,
                status TEXT NOT NULL,
                rows_read BIGINT NOT NULL DEFAULT 0,
                rows_written BIGINT NOT NULL DEFAULT 0,
                report JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS lineage_edges (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                parent_artifact_id UUID NOT NULL REFERENCES data_artifacts(id) ON DELETE CASCADE,
                child_artifact_id UUID NOT NULL REFERENCES data_artifacts(id) ON DELETE CASCADE,
                relation TEXT NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (parent_artifact_id, child_artifact_id, relation)
            )
            """,
            """
            CREATE OR REPLACE VIEW hdp_processing_runs AS
            SELECT id, project_id, recipe_id, input_resource_id, output_resource_id,
                   status, rows_read, rows_written, report, error, started_at, finished_at
            FROM processing_runs
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE INDEX IF NOT EXISTS processing_recipes_project_idx
            ON processing_recipes(project_id, updated_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS processing_runs_project_idx
            ON processing_runs(project_id, started_at DESC)
            """,
            """
            CREATE INDEX IF NOT EXISTS lineage_edges_project_idx
            ON lineage_edges(project_id, created_at DESC)
            """,
        ),
    ),
    Migration(
        version="5.0.0-001-intelligence-core",
        description="Data Grid, métadonnées HDX, signaux syndromiques et notebooks Jupyter",
        statements=(
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS expected_update_at TIMESTAMPTZ",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS reliability JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS schema_metadata JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS source_metadata JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS supersedes_resource_id UUID REFERENCES local_resources(id) ON DELETE SET NULL",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS http_etag TEXT",
            "ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS http_last_modified TEXT",
            """
            CREATE TABLE IF NOT EXISTS hdx_metadata_records (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                dataset_id TEXT NOT NULL,
                resource_id TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                data_grid_dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,
                geography JSONB NOT NULL DEFAULT '[]'::jsonb,
                temporal_coverage JSONB NOT NULL DEFAULT '{}'::jsonb,
                structure JSONB NOT NULL DEFAULT '{}'::jsonb,
                formats JSONB NOT NULL DEFAULT '[]'::jsonb,
                update_periodicity TEXT,
                expected_update_at TIMESTAMPTZ,
                reliability JSONB NOT NULL DEFAULT '{}'::jsonb,
                source_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                observed_at TIMESTAMPTZ NOT NULL,
                UNIQUE (project_id, dataset_id, resource_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS signal_events (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source TEXT NOT NULL,
                external_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                occurred_at TIMESTAMPTZ NOT NULL,
                received_at TIMESTAMPTZ NOT NULL,
                locations JSONB NOT NULL DEFAULT '[]'::jsonb,
                themes JSONB NOT NULL DEFAULT '[]'::jsonb,
                severity NUMERIC NOT NULL DEFAULT 0,
                confidence NUMERIC NOT NULL DEFAULT 0,
                evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
                raw JSONB NOT NULL DEFAULT '{}'::jsonb,
                UNIQUE (project_id, source, external_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS signal_rules (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                locations JSONB NOT NULL DEFAULT '[]'::jsonb,
                themes JSONB NOT NULL DEFAULT '[]'::jsonb,
                min_severity NUMERIC NOT NULL DEFAULT 0,
                min_confidence NUMERIC NOT NULL DEFAULT 0,
                lookback_hours INTEGER NOT NULL DEFAULT 168,
                data_grid_dimensions JSONB NOT NULL DEFAULT '[]'::jsonb,
                query_template TEXT NOT NULL DEFAULT '{title} {themes} {locations}',
                refresh_due_resources BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS signal_actions (
                id UUID PRIMARY KEY,
                event_id UUID NOT NULL REFERENCES signal_events(id) ON DELETE CASCADE,
                rule_id UUID NOT NULL REFERENCES signal_rules(id) ON DELETE CASCADE,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                UNIQUE (event_id, rule_id, action_type)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS syndromic_snapshots (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                scope_key TEXT NOT NULL,
                window_start TIMESTAMPTZ NOT NULL,
                window_end TIMESTAMPTZ NOT NULL,
                event_count INTEGER NOT NULL,
                score NUMERIC NOT NULL,
                themes JSONB NOT NULL DEFAULT '{}'::jsonb,
                locations JSONB NOT NULL DEFAULT '{}'::jsonb,
                evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notebooks (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                kernel TEXT NOT NULL CHECK (kernel IN ('python3', 'ir')),
                description TEXT NOT NULL DEFAULT '',
                current_revision INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notebook_revisions (
                id UUID PRIMARY KEY,
                notebook_id UUID NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                revision_number INTEGER NOT NULL,
                document JSONB NOT NULL,
                document_sha256 CHAR(64) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (notebook_id, revision_number)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notebook_cell_executions (
                id UUID PRIMARY KEY,
                notebook_id UUID NOT NULL REFERENCES notebooks(id) ON DELETE CASCADE,
                revision_id UUID NOT NULL REFERENCES notebook_revisions(id),
                cell_index INTEGER NOT NULL,
                script_execution_id UUID REFERENCES script_executions(id) ON DELETE SET NULL,
                code_sha256 CHAR(64) NOT NULL,
                requested_at TIMESTAMPTZ NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS hdx_metadata_search_idx ON hdx_metadata_records(project_id, observed_at DESC)",
            "CREATE INDEX IF NOT EXISTS signal_events_scope_idx ON signal_events(project_id, occurred_at DESC)",
            "CREATE INDEX IF NOT EXISTS signal_rules_project_idx ON signal_rules(project_id, enabled)",
            "CREATE INDEX IF NOT EXISTS signal_actions_event_idx ON signal_actions(event_id, started_at DESC)",
            "CREATE INDEX IF NOT EXISTS syndromic_project_idx ON syndromic_snapshots(project_id, window_end DESC)",
            "CREATE INDEX IF NOT EXISTS notebooks_project_idx ON notebooks(project_id, updated_at DESC)",
            """
            CREATE OR REPLACE VIEW hdp_signals AS
            SELECT id, project_id, source, external_id, title, summary, occurred_at,
                   locations, themes, severity, confidence, evidence
            FROM signal_events
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE OR REPLACE VIEW hdp_hdx_metadata AS
            SELECT id, project_id, dataset_id, resource_id, title, description,
                   data_grid_dimensions, geography, temporal_coverage, structure,
                   formats, update_periodicity, expected_update_at, reliability, observed_at
            FROM hdx_metadata_records
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
        ),
    ),
    Migration(
        version="6.0.0-001-rules-catalog-cache",
        description="Règles ET/OU versionnées, catalogue exhaustif et cache traçable",
        statements=(
            "ALTER TABLE hdx_metadata_records ADD COLUMN IF NOT EXISTS raw_snapshot_id UUID",
            "ALTER TABLE signal_rules ADD COLUMN IF NOT EXISTS migrated_definition_id UUID",
            "ALTER TABLE signal_actions ADD COLUMN IF NOT EXISTS idempotency_key CHAR(64)",
            "CREATE UNIQUE INDEX IF NOT EXISTS signal_actions_idempotency_idx ON signal_actions(idempotency_key) WHERE idempotency_key IS NOT NULL",
            """
            CREATE TABLE IF NOT EXISTS rule_definitions (
                id UUID PRIMARY KEY,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                scope TEXT NOT NULL CHECK (scope IN ('global', 'project')),
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                current_version_number INTEGER NOT NULL DEFAULT 1,
                legacy_signal_rule_id UUID UNIQUE REFERENCES signal_rules(id) ON DELETE SET NULL,
                created_by TEXT NOT NULL DEFAULT 'local-operator',
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                CHECK ((scope = 'global' AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL))
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rule_versions (
                id UUID PRIMARY KEY,
                definition_id UUID NOT NULL REFERENCES rule_definitions(id) ON DELETE CASCADE,
                version_number INTEGER NOT NULL,
                schema_version TEXT NOT NULL,
                rule_tree JSONB NOT NULL,
                actions JSONB NOT NULL DEFAULT '[]'::jsonb,
                definition_sha256 CHAR(64) NOT NULL,
                created_by TEXT NOT NULL DEFAULT 'local-operator',
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (definition_id, version_number),
                UNIQUE (definition_id, definition_sha256)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rule_inheritance (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                global_definition_id UUID NOT NULL REFERENCES rule_definitions(id) ON DELETE CASCADE,
                project_definition_id UUID REFERENCES rule_definitions(id) ON DELETE SET NULL,
                adopted_version_id UUID REFERENCES rule_versions(id) ON DELETE SET NULL,
                proposed_version_id UUID REFERENCES rule_versions(id) ON DELETE SET NULL,
                status TEXT NOT NULL DEFAULT 'current' CHECK (status IN ('current', 'update_proposed', 'overridden', 'rejected', 'suspended')),
                proposed_at TIMESTAMPTZ,
                decided_at TIMESTAMPTZ,
                UNIQUE (project_id, global_definition_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rule_evaluations (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                definition_id UUID NOT NULL REFERENCES rule_definitions(id) ON DELETE CASCADE,
                rule_version_id UUID NOT NULL REFERENCES rule_versions(id),
                triggering_event_id UUID REFERENCES signal_events(id) ON DELETE SET NULL,
                input_version_sha256 CHAR(64) NOT NULL,
                window_start TIMESTAMPTZ,
                window_end TIMESTAMPTZ NOT NULL,
                matched BOOLEAN NOT NULL,
                events_examined JSONB NOT NULL DEFAULT '[]'::jsonb,
                proof JSONB NOT NULL,
                simulated BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS action_requests (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                evaluation_id UUID NOT NULL REFERENCES rule_evaluations(id) ON DELETE CASCADE,
                action_type TEXT NOT NULL,
                risk_level TEXT NOT NULL CHECK (risk_level IN ('safe', 'preparatory', 'external')),
                status TEXT NOT NULL CHECK (status IN ('queued', 'pending_approval', 'approved', 'rejected', 'running', 'completed', 'failed', 'blocked')),
                parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                limits JSONB NOT NULL DEFAULT '{}'::jsonb,
                idempotency_key CHAR(64) NOT NULL UNIQUE,
                requested_at TIMESTAMPTZ NOT NULL,
                decided_at TIMESTAMPTZ,
                decided_by TEXT,
                decision_reason TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS action_executions (
                id UUID PRIMARY KEY,
                request_id UUID NOT NULL REFERENCES action_requests(id) ON DELETE CASCADE,
                attempt_number INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed', 'blocked')),
                input_sha256 CHAR(64) NOT NULL,
                output_sha256 CHAR(64),
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT,
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                UNIQUE (request_id, attempt_number)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS source_api_versions (
                id UUID PRIMARY KEY,
                source_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                documentation_url TEXT NOT NULL,
                documentation_sha256 CHAR(64),
                verified_at TIMESTAMPTZ NOT NULL,
                valid_from TIMESTAMPTZ NOT NULL,
                valid_until TIMESTAMPTZ,
                raw_contract JSONB NOT NULL DEFAULT '{}'::jsonb,
                UNIQUE (source_id, api_version, valid_from)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS source_endpoints (
                id UUID PRIMARY KEY,
                api_version_id UUID NOT NULL REFERENCES source_api_versions(id) ON DELETE CASCADE,
                endpoint_id TEXT NOT NULL,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                authentication JSONB NOT NULL DEFAULT '{}'::jsonb,
                formats JSONB NOT NULL DEFAULT '[]'::jsonb,
                limits JSONB NOT NULL DEFAULT '{}'::jsonb,
                cache_contract JSONB NOT NULL DEFAULT '{}'::jsonb,
                allowed_hosts JSONB NOT NULL DEFAULT '[]'::jsonb,
                state TEXT NOT NULL CHECK (state IN ('inventoried', 'contract_imported', 'adapter_implemented', 'tests_validated', 'active_global', 'active_project', 'suspended', 'obsolete')),
                contract_sha256 CHAR(64) NOT NULL,
                activated_at TIMESTAMPTZ,
                suspended_at TIMESTAMPTZ,
                UNIQUE (api_version_id, endpoint_id, method, path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS endpoint_parameters (
                id UUID PRIMARY KEY,
                endpoint_id UUID NOT NULL REFERENCES source_endpoints(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                location TEXT NOT NULL CHECK (location IN ('path', 'query', 'header', 'cookie', 'body')),
                schema JSONB NOT NULL,
                required BOOLEAN NOT NULL DEFAULT FALSE,
                documented BOOLEAN NOT NULL DEFAULT TRUE,
                supported BOOLEAN NOT NULL DEFAULT FALSE,
                sensitive BOOLEAN NOT NULL DEFAULT FALSE,
                description TEXT NOT NULL DEFAULT '',
                dependencies JSONB NOT NULL DEFAULT '[]'::jsonb,
                UNIQUE (endpoint_id, location, name)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS response_fields (
                id UUID PRIMARY KEY,
                endpoint_id UUID NOT NULL REFERENCES source_endpoints(id) ON DELETE CASCADE,
                field_path TEXT NOT NULL,
                schema JSONB NOT NULL,
                documented BOOLEAN NOT NULL DEFAULT FALSE,
                observed BOOLEAN NOT NULL DEFAULT FALSE,
                nullable BOOLEAN NOT NULL DEFAULT TRUE,
                cardinality TEXT,
                first_seen_version TEXT,
                last_seen_at TIMESTAMPTZ,
                UNIQUE (endpoint_id, field_path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS connector_capabilities (
                source_id TEXT NOT NULL,
                capability TEXT NOT NULL CHECK (capability IN ('discover', 'describe', 'search', 'preview', 'acquire', 'refresh', 'provenance')),
                support_level TEXT NOT NULL CHECK (support_level IN ('native', 'hdp_equivalent', 'partial', 'unavailable')),
                state TEXT NOT NULL CHECK (state IN ('inventoried', 'contract_imported', 'adapter_implemented', 'tests_validated', 'active_global', 'active_project', 'suspended', 'obsolete')),
                endpoint_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
                equivalent_recipe JSONB,
                tested_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (source_id, capability)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS raw_metadata_snapshots (
                id UUID PRIMARY KEY,
                source_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                external_id TEXT,
                content JSONB NOT NULL,
                content_sha256 CHAR(64) NOT NULL,
                http_etag TEXT,
                http_last_modified TEXT,
                observed_at TIMESTAMPTZ NOT NULL,
                UNIQUE (source_id, api_version, endpoint_id, content_sha256)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS catalog_records (
                id UUID PRIMARY KEY,
                source_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                external_id TEXT NOT NULL,
                record_type TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                normalized_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                unmapped_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
                raw_snapshot_id UUID NOT NULL REFERENCES raw_metadata_snapshots(id),
                connector_version TEXT NOT NULL,
                transformation_version TEXT NOT NULL,
                confidence JSONB NOT NULL DEFAULT '{}'::jsonb,
                observed_at TIMESTAMPTZ NOT NULL,
                valid_until TIMESTAMPTZ,
                UNIQUE (source_id, api_version, endpoint_id, external_id, observed_at)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                id UUID PRIMARY KEY,
                cache_key CHAR(64) NOT NULL UNIQUE,
                source_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                canonical_parameters JSONB NOT NULL,
                output_format TEXT NOT NULL,
                connector_version TEXT NOT NULL,
                transformation_version TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                content_sha256 CHAR(64) NOT NULL,
                size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
                http_etag TEXT,
                http_last_modified TEXT,
                fetched_at TIMESTAMPTZ NOT NULL,
                next_validation_at TIMESTAMPTZ NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('fresh', 'revalidating', 'stale', 'failed', 'superseded')),
                supersedes_cache_entry_id UUID REFERENCES cache_entries(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_data_policies (
                project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                stale_policy TEXT NOT NULL DEFAULT 'stale_if_error' CHECK (stale_policy IN ('block', 'allow_stale', 'stale_if_error', 'manual')),
                max_stale_mode TEXT NOT NULL DEFAULT 'manual' CHECK (max_stale_mode IN ('fixed_duration', 'frequency_multiple', 'frequency_with_project_cap', 'manual')),
                fixed_duration_seconds INTEGER,
                frequency_multiple NUMERIC,
                project_cap_seconds INTEGER,
                automatic_request_limit INTEGER NOT NULL DEFAULT 100,
                automatic_download_bytes BIGINT NOT NULL DEFAULT 104857600,
                automatic_duration_seconds INTEGER NOT NULL DEFAULT 300,
                updated_at TIMESTAMPTZ NOT NULL,
                CHECK (fixed_duration_seconds IS NULL OR fixed_duration_seconds > 0),
                CHECK (frequency_multiple IS NULL OR frequency_multiple > 0),
                CHECK (project_cap_seconds IS NULL OR project_cap_seconds > 0)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS application_timeline (
                id UUID PRIMARY KEY,
                project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
                scope TEXT NOT NULL CHECK (scope IN ('global', 'project')),
                event_type TEXT NOT NULL,
                object_type TEXT NOT NULL,
                object_id TEXT,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                details JSONB NOT NULL DEFAULT '{}'::jsonb,
                actor TEXT NOT NULL DEFAULT 'system',
                occurred_at TIMESTAMPTZ NOT NULL,
                CHECK ((scope = 'global' AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL))
            )
            """,
            "CREATE INDEX IF NOT EXISTS rule_definitions_scope_idx ON rule_definitions(scope, project_id, enabled)",
            "CREATE INDEX IF NOT EXISTS rule_evaluations_project_idx ON rule_evaluations(project_id, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS action_requests_status_idx ON action_requests(project_id, status, requested_at)",
            "CREATE INDEX IF NOT EXISTS source_endpoints_state_idx ON source_endpoints(state, api_version_id)",
            "CREATE INDEX IF NOT EXISTS response_fields_endpoint_idx ON response_fields(endpoint_id, field_path)",
            "CREATE INDEX IF NOT EXISTS catalog_records_search_idx ON catalog_records(source_id, record_type, observed_at DESC)",
            "CREATE INDEX IF NOT EXISTS cache_entries_revalidation_idx ON cache_entries(state, next_validation_at)",
            "CREATE INDEX IF NOT EXISTS application_timeline_scope_idx ON application_timeline(scope, project_id, occurred_at DESC)",
            """
            CREATE OR REPLACE VIEW hdp_rule_evaluations AS
            SELECT id, project_id, definition_id, rule_version_id,
                   triggering_event_id, matched, proof, simulated, created_at
            FROM rule_evaluations
            WHERE project_id = NULLIF(current_setting('hdp.project_id', TRUE), '')::uuid
            """,
            """
            CREATE OR REPLACE VIEW hdp_catalog AS
            SELECT id, source_id, api_version, endpoint_id, external_id,
                   record_type, title, normalized_metadata, confidence, observed_at,
                   valid_until
            FROM catalog_records
            """,
        ),
    ),
    Migration(
        version="6.0.0-002-rule-inheritance-bootstrap",
        description="Initialisation sans effet de bord de l'héritage des règles globales",
        statements=(
            """
            INSERT INTO project_data_policies (project_id, updated_at)
            SELECT p.id, CURRENT_TIMESTAMP
            FROM projects p
            ON CONFLICT (project_id) DO NOTHING
            """,
            """
            INSERT INTO rule_inheritance
                (id,project_id,global_definition_id,adopted_version_id,status,decided_at)
            SELECT (
                       substr(md5(p.id::text || ':' || d.id::text),1,8) || '-' ||
                       substr(md5(p.id::text || ':' || d.id::text),9,4) || '-' ||
                       substr(md5(p.id::text || ':' || d.id::text),13,4) || '-' ||
                       substr(md5(p.id::text || ':' || d.id::text),17,4) || '-' ||
                       substr(md5(p.id::text || ':' || d.id::text),21,12)
                   )::uuid,
                   p.id,d.id,v.id,'current',CURRENT_TIMESTAMP
            FROM projects p
            CROSS JOIN rule_definitions d
            JOIN rule_versions v ON v.definition_id=d.id
             AND v.version_number=d.current_version_number
            WHERE d.scope='global'
            ON CONFLICT (project_id,global_definition_id) DO NOTHING
            """,
        ),
    ),
    Migration(
        version="6.0.0-003-connector-activation",
        description="Activation progressive et distincte des contrats de connecteurs",
        statements=(
            "ALTER TABLE source_endpoints ADD COLUMN IF NOT EXISTS adapter_version TEXT",
            "ALTER TABLE source_endpoints ADD COLUMN IF NOT EXISTS test_evidence JSONB NOT NULL DEFAULT '{}'::jsonb",
            "ALTER TABLE source_endpoints ADD COLUMN IF NOT EXISTS state_updated_at TIMESTAMPTZ",
            """
            CREATE TABLE IF NOT EXISTS endpoint_activation_history (
                id UUID PRIMARY KEY,
                endpoint_id UUID NOT NULL REFERENCES source_endpoints(id) ON DELETE CASCADE,
                previous_state TEXT NOT NULL,
                new_state TEXT NOT NULL,
                evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
                actor TEXT NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_endpoint_activations (
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                endpoint_id UUID NOT NULL REFERENCES source_endpoints(id) ON DELETE CASCADE,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                settings JSONB NOT NULL DEFAULT '{}'::jsonb,
                activated_by TEXT NOT NULL,
                activated_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (project_id, endpoint_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS endpoint_activation_history_idx ON endpoint_activation_history(endpoint_id, occurred_at DESC)",
            "CREATE INDEX IF NOT EXISTS project_endpoint_activations_idx ON project_endpoint_activations(project_id, enabled)",
        ),
    ),
    Migration(
        version="6.0.0-004-cache-materialization",
        description="Révisions atomiques, revalidation et partage du cache public V6",
        statements=(
            "ALTER TABLE cache_entries DROP CONSTRAINT IF EXISTS cache_entries_cache_key_key",
            "ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS media_type TEXT NOT NULL DEFAULT 'application/json'",
            "ALTER TABLE cache_entries ADD COLUMN IF NOT EXISTS validation_requested_at TIMESTAMPTZ",
            "CREATE UNIQUE INDEX IF NOT EXISTS cache_entries_current_key_idx ON cache_entries(cache_key) WHERE state <> 'superseded'",
            """
            CREATE TABLE IF NOT EXISTS project_cache_references (
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                cache_entry_id UUID NOT NULL REFERENCES cache_entries(id) ON DELETE CASCADE,
                purpose TEXT NOT NULL DEFAULT 'acquisition',
                referenced_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (project_id, cache_entry_id, purpose)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS cache_revalidations (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                cache_entry_id UUID NOT NULL REFERENCES cache_entries(id) ON DELETE CASCADE,
                outcome TEXT NOT NULL CHECK (outcome IN ('not_modified', 'modified', 'failed', 'forced')),
                request_etag TEXT,
                request_last_modified TEXT,
                response_etag TEXT,
                response_last_modified TEXT,
                details JSONB NOT NULL DEFAULT '{}'::jsonb,
                actor TEXT NOT NULL,
                occurred_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS equivalent_materializations (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                capability TEXT NOT NULL CHECK (capability IN ('discover', 'describe', 'search', 'preview', 'acquire', 'refresh', 'provenance')),
                cache_entry_id UUID NOT NULL REFERENCES cache_entries(id) ON DELETE CASCADE,
                recipe JSONB NOT NULL,
                recipe_sha256 CHAR(64) NOT NULL,
                materialized_at TIMESTAMPTZ NOT NULL,
                materialized_by TEXT NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS project_cache_references_idx ON project_cache_references(project_id, referenced_at DESC)",
            "CREATE INDEX IF NOT EXISTS cache_revalidations_entry_idx ON cache_revalidations(cache_entry_id, occurred_at DESC)",
            "CREATE INDEX IF NOT EXISTS equivalent_materializations_project_idx ON equivalent_materializations(project_id, source_id, capability, materialized_at DESC)",
        ),
    ),
    Migration(
        version="6.0.0-005-catalog-lineage-scheduling",
        description="Métadonnées brutes immuables, lignée et planification du catalogue V6",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS catalog_ingestion_runs (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                connector_version TEXT NOT NULL,
                transformation_version TEXT NOT NULL,
                acquisition_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                record_count INTEGER NOT NULL CHECK (record_count >= 0),
                status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
                started_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                actor TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS catalog_field_lineage (
                id UUID PRIMARY KEY,
                catalog_record_id UUID NOT NULL REFERENCES catalog_records(id) ON DELETE CASCADE,
                target_path TEXT NOT NULL,
                source_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
                recipe JSONB NOT NULL,
                connector_version TEXT NOT NULL,
                transformation_version TEXT NOT NULL,
                confidence JSONB NOT NULL,
                UNIQUE (catalog_record_id, target_path)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_catalog_references (
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                catalog_record_id UUID NOT NULL REFERENCES catalog_records(id) ON DELETE CASCADE,
                ingestion_run_id UUID NOT NULL REFERENCES catalog_ingestion_runs(id) ON DELETE CASCADE,
                referenced_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (project_id, catalog_record_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS catalog_update_schedules (
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                source_id TEXT NOT NULL,
                endpoint_id TEXT NOT NULL,
                api_version TEXT NOT NULL,
                interval_minutes INTEGER NOT NULL CHECK (interval_minutes >= 15),
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                acquisition_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                next_run_at TIMESTAMPTZ NOT NULL,
                last_run_at TIMESTAMPTZ,
                last_status TEXT,
                last_error TEXT,
                updated_at TIMESTAMPTZ NOT NULL,
                updated_by TEXT NOT NULL,
                PRIMARY KEY (project_id, source_id, endpoint_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS catalog_ingestion_runs_project_idx ON catalog_ingestion_runs(project_id, started_at DESC)",
            "CREATE INDEX IF NOT EXISTS catalog_field_lineage_record_idx ON catalog_field_lineage(catalog_record_id, target_path)",
            "CREATE INDEX IF NOT EXISTS catalog_update_schedules_due_idx ON catalog_update_schedules(enabled, next_run_at)",
        ),
    ),
    Migration(
        version="6.0.0-006-rss-source-lifecycle",
        description="Candidats RSS versionnés, contrôles et abonnements approuvés",
        statements=(
            "ALTER TABLE rss_subscriptions ADD COLUMN IF NOT EXISTS feed_definition JSONB",
            "ALTER TABLE rss_subscriptions ADD COLUMN IF NOT EXISTS feed_source_id UUID",
            """
            CREATE TABLE IF NOT EXISTS rss_feed_sources (
                id UUID PRIMARY KEY,
                source_key TEXT NOT NULL,
                version_number INTEGER NOT NULL,
                name TEXT NOT NULL,
                organization TEXT NOT NULL,
                region TEXT NOT NULL,
                themes JSONB NOT NULL DEFAULT '[]'::jsonb,
                languages JSONB NOT NULL DEFAULT '[]'::jsonb,
                feed_url TEXT NOT NULL,
                portal_url TEXT NOT NULL,
                evidence_url TEXT NOT NULL,
                protocol TEXT NOT NULL,
                license TEXT NOT NULL,
                declared_frequency TEXT NOT NULL,
                allowed_hosts JSONB NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('draft', 'validated', 'approved', 'suspended', 'rejected')),
                created_at TIMESTAMPTZ NOT NULL,
                created_by TEXT NOT NULL,
                decided_at TIMESTAMPTZ,
                decided_by TEXT,
                UNIQUE (source_key, version_number)
            )
            """,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname='rss_subscriptions_feed_source_fk'
                ) THEN
                    ALTER TABLE rss_subscriptions
                    ADD CONSTRAINT rss_subscriptions_feed_source_fk
                    FOREIGN KEY (feed_source_id) REFERENCES rss_feed_sources(id) ON DELETE SET NULL;
                END IF;
            END $$
            """,
            """
            CREATE TABLE IF NOT EXISTS rss_feed_checks (
                id UUID PRIMARY KEY,
                feed_source_id UUID NOT NULL REFERENCES rss_feed_sources(id) ON DELETE CASCADE,
                status TEXT NOT NULL CHECK (status IN ('passed', 'failed')),
                requested_url TEXT NOT NULL,
                final_url TEXT,
                http_etag TEXT,
                http_last_modified TEXT,
                content_sha256 CHAR(64),
                schema_sha256 CHAR(64),
                schema_changed BOOLEAN NOT NULL DEFAULT FALSE,
                item_count INTEGER,
                error TEXT,
                checked_at TIMESTAMPTZ NOT NULL,
                checked_by TEXT NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS rss_feed_sources_state_idx ON rss_feed_sources(state, organization, region)",
            "CREATE INDEX IF NOT EXISTS rss_feed_checks_source_idx ON rss_feed_checks(feed_source_id, checked_at DESC)",
        ),
    ),
    Migration(
        version="6.0.0-007-database-backups",
        description="Sauvegardes globales, projet et signaux avec manifeste",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS database_backups (
                id UUID PRIMARY KEY,
                scope TEXT NOT NULL CHECK (scope IN ('global', 'project', 'signals')),
                project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
                selector JSONB NOT NULL DEFAULT '{}'::jsonb,
                status TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
                storage_path TEXT,
                bundle_sha256 CHAR(64),
                size_bytes BIGINT,
                manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                finished_at TIMESTAMPTZ,
                created_by TEXT NOT NULL,
                CHECK ((scope='global' AND project_id IS NULL) OR (scope<>'global' AND project_id IS NOT NULL))
            )
            """,
            "CREATE INDEX IF NOT EXISTS database_backups_scope_idx ON database_backups(scope, project_id, created_at DESC)",
        ),
    ),
    Migration(
        version="6.0.0-008-passkey-operator-auth",
        description="Authentification forte WebAuthn de l'opérateur unique",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS operator_webauthn_credentials (
                id UUID PRIMARY KEY,
                credential_id BYTEA NOT NULL UNIQUE,
                public_key BYTEA NOT NULL,
                sign_count BIGINT NOT NULL DEFAULT 0,
                transports JSONB NOT NULL DEFAULT '[]'::jsonb,
                aaguid TEXT,
                device_type TEXT,
                backed_up BOOLEAN NOT NULL DEFAULT FALSE,
                label TEXT NOT NULL DEFAULT 'Passkey opérateur',
                created_at TIMESTAMPTZ NOT NULL,
                last_used_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS operator_auth_challenges (
                id UUID PRIMARY KEY,
                kind TEXT NOT NULL CHECK (kind IN ('registration', 'authentication')),
                challenge BYTEA NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS operator_sessions (
                id UUID PRIMARY KEY,
                token_sha256 CHAR(64) NOT NULL UNIQUE,
                credential_id UUID NOT NULL REFERENCES operator_webauthn_credentials(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                last_seen_at TIMESTAMPTZ NOT NULL,
                revoked_at TIMESTAMPTZ
            )
            """,
            "CREATE INDEX IF NOT EXISTS operator_auth_challenges_expiry_idx ON operator_auth_challenges(expires_at, used_at)",
            "CREATE INDEX IF NOT EXISTS operator_sessions_expiry_idx ON operator_sessions(expires_at, revoked_at)",
        ),
    ),
    Migration(
        version="6.0.0-009-spip-publication-bridge",
        description="Brouillons SPIP publics, validation humaine et passerelle à droits minimaux",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS spip_connections (
                id UUID PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                token_sha256 CHAR(64) NOT NULL UNIQUE,
                scopes JSONB NOT NULL,
                enabled BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL,
                last_used_at TIMESTAMPTZ,
                revoked_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS spip_publication_drafts (
                id UUID PRIMARY KEY,
                series_id UUID NOT NULL,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK (kind IN ('documentation','news','feed_curation','alert_curation','project_share')),
                title TEXT NOT NULL,
                summary TEXT NOT NULL DEFAULT '',
                revision INTEGER NOT NULL CHECK (revision > 0),
                status TEXT NOT NULL CHECK (status IN ('draft','approved','exported','rejected','withdrawn')),
                document JSONB NOT NULL,
                content_sha256 CHAR(64) NOT NULL,
                supersedes_id UUID REFERENCES spip_publication_drafts(id) ON DELETE RESTRICT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                approved_at TIMESTAMPTZ,
                withdrawn_at TIMESTAMPTZ,
                decision_reason TEXT NOT NULL DEFAULT '',
                UNIQUE (series_id, revision),
                CHECK ((status IN ('approved','exported') AND approved_at IS NOT NULL) OR status NOT IN ('approved','exported')),
                CHECK ((status='withdrawn' AND withdrawn_at IS NOT NULL) OR status<>'withdrawn')
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS spip_external_mappings (
                connection_id UUID NOT NULL REFERENCES spip_connections(id) ON DELETE CASCADE,
                series_id UUID NOT NULL,
                external_id TEXT NOT NULL DEFAULT '',
                external_url TEXT NOT NULL DEFAULT '',
                last_publication_id UUID NOT NULL REFERENCES spip_publication_drafts(id) ON DELETE RESTRICT,
                last_status TEXT NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (connection_id, series_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS spip_delivery_events (
                id UUID PRIMARY KEY,
                connection_id UUID NOT NULL REFERENCES spip_connections(id) ON DELETE CASCADE,
                publication_id UUID NOT NULL REFERENCES spip_publication_drafts(id) ON DELETE RESTRICT,
                event_type TEXT NOT NULL,
                idempotency_key TEXT NOT NULL,
                request JSONB NOT NULL,
                response JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (connection_id, idempotency_key)
            )
            """,
            "CREATE INDEX IF NOT EXISTS spip_publication_changes_idx ON spip_publication_drafts(status, updated_at, id)",
            "CREATE INDEX IF NOT EXISTS spip_publication_project_idx ON spip_publication_drafts(project_id, updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS spip_delivery_publication_idx ON spip_delivery_events(publication_id, created_at DESC)",
        ),
    ),
    Migration(
        version="6.0.0-010-public-mail-ingestion",
        description="Import EML public, pièces jointes confinées et rattachement aux projets",
        statements=(
            """
            CREATE TABLE IF NOT EXISTS mail_messages (
                id UUID PRIMARY KEY,
                message_key CHAR(64) NOT NULL UNIQUE,
                subject TEXT NOT NULL,
                sent_at TIMESTAMPTZ,
                received_at TIMESTAMPTZ NOT NULL,
                sender_domain TEXT NOT NULL DEFAULT '',
                sender_sha256 CHAR(64) NOT NULL DEFAULT '',
                body_text TEXT NOT NULL DEFAULT '',
                body_sha256 CHAR(64) NOT NULL,
                public_source_url TEXT NOT NULL,
                data_classification TEXT NOT NULL CHECK (data_classification='public'),
                attachment_count INTEGER NOT NULL DEFAULT 0 CHECK (attachment_count BETWEEN 0 AND 50),
                malware_scan_status TEXT NOT NULL CHECK (malware_scan_status IN ('not_available','passed','failed')),
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mail_attachments (
                id UUID PRIMARY KEY,
                message_id UUID NOT NULL REFERENCES mail_messages(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes BIGINT NOT NULL CHECK (size_bytes BETWEEN 0 AND 26214400),
                sha256 CHAR(64) NOT NULL,
                storage_path TEXT NOT NULL,
                malware_scan_status TEXT NOT NULL CHECK (malware_scan_status IN ('not_available','passed','failed')),
                created_at TIMESTAMPTZ NOT NULL,
                UNIQUE (message_id, sha256, filename)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS mail_project_links (
                message_id UUID NOT NULL REFERENCES mail_messages(id) ON DELETE CASCADE,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                signal_event_id UUID NOT NULL REFERENCES signal_events(id) ON DELETE CASCADE,
                linked_at TIMESTAMPTZ NOT NULL,
                linked_by TEXT NOT NULL,
                PRIMARY KEY (message_id, project_id),
                UNIQUE (signal_event_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS mail_messages_received_idx ON mail_messages(received_at DESC)",
            "CREATE INDEX IF NOT EXISTS mail_project_links_project_idx ON mail_project_links(project_id, linked_at DESC)",
        ),
    ),
    Migration(
        version="6.0.0-011-action-workers",
        description="File d'actions idempotente, reprise, annulation et effets internes auditables",
        statements=(
            "ALTER TABLE action_requests DROP CONSTRAINT IF EXISTS action_requests_status_check",
            """ALTER TABLE action_requests ADD CONSTRAINT action_requests_status_check
               CHECK (status IN ('queued','pending_approval','approved','rejected','running',
                                 'cancel_requested','cancelled','completed','failed','blocked'))""",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 100)",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts BETWEEN 1 AND 10)",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS lease_owner TEXT",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS cancel_requested_at TIMESTAMPTZ",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ",
            "ALTER TABLE action_requests ADD COLUMN IF NOT EXISTS last_error TEXT",
            "ALTER TABLE action_executions DROP CONSTRAINT IF EXISTS action_executions_status_check",
            """ALTER TABLE action_executions ADD CONSTRAINT action_executions_status_check
               CHECK (status IN ('running','completed','failed','blocked','cancelled'))""",
            "ALTER TABLE action_executions ADD COLUMN IF NOT EXISTS worker_id TEXT",
            """
            CREATE TABLE IF NOT EXISTS internal_notifications (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
                created_at TIMESTAMPTZ NOT NULL,
                read_at TIMESTAMPTZ
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS project_tasks (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL CHECK (priority IN ('low','normal','high','urgent')),
                status TEXT NOT NULL CHECK (status IN ('open','in_progress','completed','cancelled')),
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS signal_classifications (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
                signal_event_id UUID NOT NULL REFERENCES signal_events(id) ON DELETE CASCADE,
                labels JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMPTZ NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS action_drafts (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
                channel TEXT NOT NULL CHECK (channel IN ('email','spip')),
                status TEXT NOT NULL CHECK (status IN ('draft','approved','rejected','withdrawn')),
                document JSONB NOT NULL,
                content_sha256 CHAR(64) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                decided_at TIMESTAMPTZ,
                decided_by TEXT,
                decision_reason TEXT NOT NULL DEFAULT ''
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automated_data_jobs (
                id UUID PRIMARY KEY,
                project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id) ON DELETE CASCADE,
                job_type TEXT NOT NULL CHECK (job_type IN ('data_search','data_refresh')),
                parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                status TEXT NOT NULL CHECK (status IN ('queued','running','completed','partial','failed','cancelled')),
                result JSONB NOT NULL DEFAULT '{}'::jsonb,
                error TEXT,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                started_at TIMESTAMPTZ,
                finished_at TIMESTAMPTZ
            )
            """,
            "CREATE INDEX IF NOT EXISTS action_requests_worker_idx ON action_requests(status,next_attempt_at,requested_at)",
            "CREATE INDEX IF NOT EXISTS action_requests_lease_idx ON action_requests(lease_expires_at) WHERE status IN ('running','cancel_requested')",
            "CREATE INDEX IF NOT EXISTS action_executions_request_idx ON action_executions(request_id,attempt_number DESC)",
            "CREATE INDEX IF NOT EXISTS internal_notifications_project_idx ON internal_notifications(project_id,created_at DESC)",
            "CREATE INDEX IF NOT EXISTS project_tasks_project_idx ON project_tasks(project_id,status,updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS signal_classifications_signal_idx ON signal_classifications(signal_event_id,created_at DESC)",
            "CREATE INDEX IF NOT EXISTS action_drafts_project_idx ON action_drafts(project_id,status,updated_at DESC)",
            "CREATE INDEX IF NOT EXISTS automated_data_jobs_worker_idx ON automated_data_jobs(status,created_at)",
        ),
    ),
)


def migration_versions() -> tuple[str, ...]:
    return tuple(migration.version for migration in MIGRATIONS)


def apply_migrations(connection: Any, applied_at: datetime) -> list[str]:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL
        )
        """
    )
    rows = connection.execute("SELECT version FROM schema_migrations").fetchall()
    applied = {str(row[0]) for row in rows}
    executed: list[str] = []
    for migration in MIGRATIONS:
        if migration.version in applied:
            continue
        for statement in migration.statements:
            connection.execute(statement)
        connection.execute(
            """
            INSERT INTO schema_migrations (version, description, applied_at)
            VALUES (%s, %s, %s)
            """,
            (migration.version, migration.description, applied_at),
        )
        executed.append(migration.version)
    return executed
