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
