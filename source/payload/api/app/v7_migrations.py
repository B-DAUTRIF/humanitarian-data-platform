from __future__ import annotations

"""Idempotent V7 semantic/provenance/job schema, isolated from legacy migrations."""


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
    ]
    with database_connection() as connection:
        for statement in statements:
            connection.execute(statement)
