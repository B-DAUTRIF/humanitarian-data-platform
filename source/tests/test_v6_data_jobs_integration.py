from __future__ import annotations

import os
import secrets
import sys
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.migrations import MIGRATIONS  # noqa: E402
from app.v6_data_jobs import (  # noqa: E402
    begin_data_job_source,
    cancel_data_job,
    claim_next_data_job,
    complete_data_job_attempt,
    finish_data_job_source,
    initialize_data_job_sources,
    recover_stale_data_jobs,
)
from app.v6_action_observability import list_project_data_jobs  # noqa: E402


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
NOW = datetime(2026, 8, 24, 11, 0, tzinfo=UTC)


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "recette PostgreSQL réelle activée uniquement avec HDP_BACKUP_RESTORE_TEST_DATABASE_URL",
)
class AutomatedDataJobsPostgresIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database_name = f"hdp_data_jobs_{secrets.token_hex(6)}"
        self.database_url = self._database_url(self.database_name)
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database_name)))
        self.project_id = uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self._create_schema(connection)
            connection.execute(
                "INSERT INTO projects (id,name) VALUES (%s,'Data jobs fixture')",
                (self.project_id,),
            )

    def tearDown(self) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()",
                (self.database_name,),
            )
            connection.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(self.database_name)))

    def _database_url(self, database_name: str) -> str:
        parsed = urlparse(TEST_DATABASE_URL)
        return urlunparse(parsed._replace(path=f"/{database_name}"))

    @staticmethod
    def _create_schema(connection: psycopg.Connection[object]) -> None:
        statements = (
            "CREATE TABLE projects (id UUID PRIMARY KEY,name TEXT NOT NULL)",
            """CREATE TABLE automated_data_jobs (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE,job_type TEXT NOT NULL,
                   parameters JSONB NOT NULL,status TEXT NOT NULL,result JSONB NOT NULL DEFAULT '{}'::jsonb,
                   error TEXT,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
                   started_at TIMESTAMPTZ,finished_at TIMESTAMPTZ
               )""",
            """CREATE TABLE acquisitions (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),schedule_id UUID,
                   source TEXT NOT NULL,query TEXT NOT NULL,retrieved_at TIMESTAMPTZ NOT NULL,
                   sha256 CHAR(64) NOT NULL,item_count INTEGER NOT NULL,raw_path TEXT NOT NULL,
                   parameters JSONB NOT NULL DEFAULT '{}'::jsonb
               )""",
            """CREATE TABLE application_timeline (
                   id UUID PRIMARY KEY,project_id UUID REFERENCES projects(id),scope TEXT NOT NULL,
                   event_type TEXT NOT NULL,object_type TEXT NOT NULL,object_id TEXT NOT NULL,status TEXT NOT NULL,
                   summary TEXT NOT NULL,details JSONB NOT NULL,actor TEXT NOT NULL,occurred_at TIMESTAMPTZ NOT NULL
               )""",
        )
        for statement in statements:
            connection.execute(statement)
        for version in ("6.0.0-012-data-job-workers", "6.0.0-013-legacy-rule-migration"):
            migration = next(item for item in MIGRATIONS if item.version == version)
            for statement in migration.statements:
                connection.execute(statement)

    def _job(self, *, sources: list[str] | None = None, maximum: int = 3) -> uuid.UUID:
        job_id = uuid.uuid4()
        parameters = {
            "sources": sources or ["hdx", "reliefweb"],
            "query": "cholera",
            "result_limit": 10,
        }
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                """INSERT INTO automated_data_jobs
                   (id,project_id,request_id,job_type,parameters,status,max_attempts,created_at,updated_at)
                   VALUES (%s,%s,%s,'data_search',%s,'queued',%s,%s,%s)""",
                (job_id, self.project_id, uuid.uuid4(), Jsonb(parameters), maximum, NOW, NOW),
            )
        return job_id

    def _claim(self, now: datetime = NOW, *, lease_seconds: int = 30) -> dict[str, object] | None:
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            return claim_next_data_job(connection, "integration-data-worker", now, lease_seconds=lease_seconds)

    def _acquisition(self, job_id: uuid.UUID, source: str, when: datetime) -> uuid.UUID:
        acquisition_id = uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                """INSERT INTO acquisitions
                   (id,project_id,source,query,retrieved_at,sha256,item_count,raw_path,parameters,
                    automated_data_job_id,automated_data_job_source)
                   VALUES (%s,%s,%s,'cholera',%s,%s,2,%s,'{}'::jsonb,%s,%s)""",
                (
                    acquisition_id, self.project_id, source, when, "a" * 64,
                    f"raw/{source}.json", job_id, source,
                ),
            )
        return acquisition_id

    def test_only_one_worker_claims_a_queued_job(self) -> None:
        self._job(sources=["hdx"])
        first = self._claim()
        self.assertIsNotNone(first)
        self.assertIsNone(self._claim())

    def test_legacy_datagrid_job_type_is_accepted_and_claimed(self) -> None:
        job_id = uuid.uuid4()
        parameters = {
            "query": "cholera France",
            "dimensions": ["affected-people"],
            "locations": ["France"],
            "refresh_due_resources": True,
            "estimated_requests": 1,
            "estimated_bytes": 0,
            "estimated_duration_seconds": 45,
        }
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                """INSERT INTO automated_data_jobs
                   (id,project_id,request_id,job_type,parameters,status,created_at,updated_at)
                   VALUES (%s,%s,%s,'legacy_datagrid_search_and_due_refresh',%s,'queued',%s,%s)""",
                (job_id, self.project_id, uuid.uuid4(), Jsonb(parameters), NOW, NOW),
            )
        claimed = self._claim()
        self.assertIsNotNone(claimed)
        assert claimed is not None
        self.assertEqual(claimed["id"], job_id)
        self.assertEqual(claimed["job_type"], "legacy_datagrid_search_and_due_refresh")

    def test_operator_view_lists_jobs_without_optional_status_type_ambiguity(self) -> None:
        job_id = self._job(sources=["hdx"])
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            items = list_project_data_jobs(connection, self.project_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], job_id)
        self.assertEqual(items[0]["status"], "queued")
        self.assertEqual(items[0]["source_results"], [])

    def test_partial_attempt_retries_only_failed_source_then_completes(self) -> None:
        job_id = self._job()
        job = self._claim()
        self.assertIsNotNone(job)
        assert job is not None
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            initialize_data_job_sources(connection, job, ["hdx", "reliefweb"], NOW)
            self.assertTrue(begin_data_job_source(connection, job, "hdx", NOW)["execute"])
        hdx_acquisition = self._acquisition(job_id, "hdx", NOW)
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            finish_data_job_source(
                connection, job, "hdx", "completed", {"item_count": 2},
                acquisition_id=hdx_acquisition, now=NOW,
            )
            self.assertTrue(begin_data_job_source(connection, job, "reliefweb", NOW)["execute"])
            finish_data_job_source(connection, job, "reliefweb", "failed", error="HTTP 503", now=NOW)
            first_result = complete_data_job_attempt(connection, job, NOW)
        self.assertEqual(first_result["status"], "queued")

        second = self._claim(NOW + timedelta(seconds=2))
        self.assertIsNotNone(second)
        assert second is not None
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            hdx_state = begin_data_job_source(connection, second, "hdx", NOW + timedelta(seconds=2))
            reliefweb_state = begin_data_job_source(connection, second, "reliefweb", NOW + timedelta(seconds=2))
        self.assertFalse(hdx_state["execute"])
        self.assertTrue(reliefweb_state["execute"])
        reliefweb_acquisition = self._acquisition(job_id, "reliefweb", NOW + timedelta(seconds=2))
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            finish_data_job_source(
                connection, second, "reliefweb", "completed", {"item_count": 2},
                acquisition_id=reliefweb_acquisition, now=NOW + timedelta(seconds=2),
            )
            final = complete_data_job_attempt(connection, second, NOW + timedelta(seconds=2))
        self.assertEqual(final["status"], "completed")
        self.assertEqual(final["summary"]["completed"], 2)
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM acquisitions WHERE automated_data_job_id=%s", (job_id,)
                ).fetchone()[0],
                2,
            )

    def test_running_job_cancellation_preserves_completed_source(self) -> None:
        job_id = self._job()
        job = self._claim()
        self.assertIsNotNone(job)
        assert job is not None
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            initialize_data_job_sources(connection, job, ["hdx", "reliefweb"], NOW)
            begin_data_job_source(connection, job, "hdx", NOW)
        acquisition_id = self._acquisition(job_id, "hdx", NOW)
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            finish_data_job_source(
                connection, job, "hdx", "completed", {"item_count": 2},
                acquisition_id=acquisition_id, now=NOW,
            )
            cancellation = cancel_data_job(
                connection, job_id, "integration-operator", "Arrêt demandé", NOW,
            )
        self.assertTrue(cancellation["cancel_requested"])
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            state = begin_data_job_source(connection, job, "reliefweb", NOW)
            self.assertFalse(state["execute"])
            finish_data_job_source(connection, job, "reliefweb", "cancelled", error="cancel_requested", now=NOW)
            final = complete_data_job_attempt(connection, job, NOW)
        self.assertEqual(final["status"], "partial")
        self.assertEqual(final["summary"], {"completed": 1, "failed": 0, "cancelled": 1})

    def test_expired_lease_requeues_before_acquisition_and_stops_after_one(self) -> None:
        job_id = self._job(sources=["hdx"])
        first = self._claim()
        self.assertIsNotNone(first)
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            self.assertEqual(recover_stale_data_jobs(connection, NOW + timedelta(seconds=31)), 1)
        second = self._claim(NOW + timedelta(seconds=32))
        self.assertIsNotNone(second)
        self._acquisition(job_id, "hdx", NOW + timedelta(seconds=32))
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            self.assertEqual(recover_stale_data_jobs(connection, NOW + timedelta(seconds=63)), 1)
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            row = connection.execute(
                "SELECT status,error FROM automated_data_jobs WHERE id=%s", (job_id,)
            ).fetchone()
        self.assertEqual(row, ("partial", "worker_lease_expired_after_acquisition"))
        self.assertIsNone(self._claim(NOW + timedelta(seconds=64)))
