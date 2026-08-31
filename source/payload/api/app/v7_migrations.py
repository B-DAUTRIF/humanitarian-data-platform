from __future__ import annotations

"""Idempotent V7 semantic/provider/provenance/job schema, isolated from legacy migrations."""


def apply_v7_migrations() -> None:
    from .main import database_connection

    statements = [
        """
        CREATE TABLE IF NOT EXISTS semantic_searches (
            id UUID PRIMARY KEY,
            project_id UUID NULL,
            query_fingerprint CHAR(64) NOT NULL,
            contract_version TEXT NOT NULL,
            request_json JSONB NOT NULL,
            intent_json JSONB NOT NULL,
            plan_json JSONB NOT NULL,
            status TEXT NOT NULL,
            result_snapshot_hash CHAR(64),
            source_count INTEGER NOT NULL DEFAULT 0 CHECK (source_count >= 0),
            item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_semantic_searches_fingerprint ON semantic_searches(query_fingerprint, started_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_semantic_searches_project ON semantic_searches(project_id, started_at DESC)",
        """
        CREATE TABLE IF NOT EXISTS semantic_source_executions (
            id UUID PRIMARY KEY,
            semantic_search_id UUID NOT NULL REFERENCES semantic_searches(id) ON DELETE CASCADE,
            source_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            completeness TEXT NOT NULL,
            native_request JSONB NOT NULL DEFAULT '{}'::jsonb,
            criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
            item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
            response_hash CHAR(64),
            error TEXT,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            finished_at TIMESTAMPTZ,
            UNIQUE (semantic_search_id, source_id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_semantic_source_execution_search ON semantic_source_executions(semantic_search_id, source_id)",
        """
        CREATE TABLE IF NOT EXISTS semantic_mapping_evidence (
            id BIGSERIAL PRIMARY KEY,
            source_id TEXT NOT NULL,
            concept TEXT NOT NULL,
            canonical_value TEXT NOT NULL,
            provider_value TEXT NOT NULL,
            capability_mode TEXT NOT NULL,
            confidence TEXT NOT NULL,
            evidence_url TEXT NOT NULL,
            contract_version TEXT NOT NULL,
            verified_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(source_id, concept, canonical_value, provider_value, contract_version)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS semantic_jobs (
            id UUID PRIMARY KEY,
            project_id UUID NOT NULL,
            request_json JSONB NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('queued','running','completed','partial','failed','cancelled')),
            progress SMALLINT NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
            cancel_requested BOOLEAN NOT NULL DEFAULT FALSE,
            result_json JSONB,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_semantic_jobs_project_created ON semantic_jobs(project_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_semantic_jobs_status ON semantic_jobs(status, created_at)",
        """
        CREATE TABLE IF NOT EXISTS provider_schema_versions (
            provider_id TEXT NOT NULL,
            api_version TEXT NOT NULL,
            descriptor_hash CHAR(64) NOT NULL,
            descriptor_json JSONB NOT NULL,
            evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (provider_id, api_version, descriptor_hash)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS provider_field_catalog (
            provider_id TEXT NOT NULL,
            api_version TEXT NOT NULL,
            content_type TEXT NOT NULL,
            field_path TEXT NOT NULL,
            field_type TEXT NOT NULL,
            capabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
            description TEXT,
            abbreviation TEXT,
            evidence_url TEXT,
            observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (provider_id, api_version, content_type, field_path)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_provider_field_catalog_provider ON provider_field_catalog(provider_id, content_type)",
        """
        CREATE TABLE IF NOT EXISTS provider_vocabulary_cache (
            provider_id TEXT NOT NULL,
            vocabulary_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            payload_hash CHAR(64) NOT NULL,
            etag TEXT,
            last_modified TEXT,
            retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            PRIMARY KEY (provider_id, vocabulary_id, payload_hash)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS provider_vocabulary_values (
            provider_id TEXT NOT NULL,
            vocabulary_id TEXT NOT NULL,
            provider_value TEXT NOT NULL,
            label TEXT,
            parent_value TEXT,
            aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            valid_from TIMESTAMPTZ,
            valid_to TIMESTAMPTZ,
            PRIMARY KEY (provider_id, vocabulary_id, provider_value)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS provider_raw_artifacts (
            id UUID PRIMARY KEY,
            provider_id TEXT NOT NULL,
            semantic_search_id UUID NULL REFERENCES semantic_searches(id) ON DELETE SET NULL,
            project_id UUID NULL,
            request_fingerprint CHAR(64) NOT NULL,
            response_hash CHAR(64) NOT NULL,
            content_type TEXT,
            media_type TEXT NOT NULL DEFAULT 'application/json',
            http_status INTEGER,
            artifact_uri TEXT,
            inline_payload JSONB,
            request_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            acquired_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (artifact_uri IS NOT NULL OR inline_payload IS NOT NULL),
            UNIQUE(provider_id, response_hash)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_provider_raw_artifacts_search ON provider_raw_artifacts(semantic_search_id, provider_id)",
        """
        CREATE TABLE IF NOT EXISTS provider_normalizations (
            id UUID PRIMARY KEY,
            raw_artifact_id UUID NOT NULL REFERENCES provider_raw_artifacts(id) ON DELETE CASCADE,
            normalization_version TEXT NOT NULL,
            normalized_hash CHAR(64) NOT NULL,
            record_count INTEGER NOT NULL DEFAULT 0 CHECK (record_count >= 0),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(raw_artifact_id, normalization_version)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS provider_schema_drift_events (
            id UUID PRIMARY KEY,
            provider_id TEXT NOT NULL,
            api_version TEXT,
            event_type TEXT NOT NULL,
            field_path TEXT,
            expected_json JSONB,
            observed_json JSONB,
            evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            status TEXT NOT NULL DEFAULT 'open',
            detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            resolved_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_provider_schema_drift_open ON provider_schema_drift_events(provider_id, status, detected_at DESC)",
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_semantic_searches_project') THEN
            ALTER TABLE semantic_searches ADD CONSTRAINT fk_semantic_searches_project
              FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
          END IF;
        END $$
        """,
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_semantic_jobs_project') THEN
            ALTER TABLE semantic_jobs ADD CONSTRAINT fk_semantic_jobs_project
              FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
          END IF;
        END $$
        """,
        """
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_provider_raw_artifacts_project') THEN
            ALTER TABLE provider_raw_artifacts ADD CONSTRAINT fk_provider_raw_artifacts_project
              FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
          END IF;
        END $$
        """,
    ]
    with database_connection() as connection:
        for statement in statements:
            connection.execute(statement)
