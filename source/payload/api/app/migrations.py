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
