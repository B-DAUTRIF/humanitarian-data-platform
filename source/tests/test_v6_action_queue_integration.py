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

from app.v6_action_queue import (  # noqa: E402
    cancel_action_request,
    claim_next_action_request,
    decide_action_request,
    execute_claimed_action_request,
    mark_action_request_failed,
    recover_stale_action_requests,
)
from app.v6_action_observability import list_project_action_requests  # noqa: E402


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
NOW = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "recette PostgreSQL réelle activée uniquement avec HDP_BACKUP_RESTORE_TEST_DATABASE_URL",
)
class ActionQueuePostgresIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database_name = f"hdp_action_queue_{secrets.token_hex(6)}"
        self.database_url = self._database_url(self.database_name)
        self._create_database()
        self.project_id = uuid.uuid4()
        self.event_id = uuid.uuid4()
        self.evaluation_id = uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self._create_schema(connection)
            connection.execute(
                "INSERT INTO projects (id,name) VALUES (%s,'Action queue fixture')",
                (self.project_id,),
            )
            connection.execute(
                """INSERT INTO project_data_policies
                   (project_id,automatic_request_limit,automatic_download_bytes,automatic_duration_seconds)
                   VALUES (%s,10,1000000,300)""",
                (self.project_id,),
            )
            connection.execute(
                "INSERT INTO signal_events (id,project_id) VALUES (%s,%s)",
                (self.event_id, self.project_id),
            )
            connection.execute(
                """INSERT INTO rule_evaluations (id,project_id,triggering_event_id)
                   VALUES (%s,%s,%s)""",
                (self.evaluation_id, self.project_id, self.event_id),
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

    def _create_database(self) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database_name)))

    @staticmethod
    def _create_schema(connection: psycopg.Connection[object]) -> None:
        statements = (
            "CREATE TABLE projects (id UUID PRIMARY KEY,name TEXT NOT NULL)",
            """CREATE TABLE project_data_policies (
                   project_id UUID PRIMARY KEY REFERENCES projects(id),
                   automatic_request_limit INTEGER NOT NULL,
                   automatic_download_bytes BIGINT NOT NULL,
                   automatic_duration_seconds INTEGER NOT NULL
               )""",
            "CREATE TABLE signal_events (id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id))",
            """CREATE TABLE rule_evaluations (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   triggering_event_id UUID REFERENCES signal_events(id)
               )""",
            """CREATE TABLE action_requests (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   evaluation_id UUID NOT NULL REFERENCES rule_evaluations(id),action_type TEXT NOT NULL,
                   risk_level TEXT NOT NULL,status TEXT NOT NULL,parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
                   limits JSONB NOT NULL DEFAULT '{}'::jsonb,idempotency_key CHAR(64) NOT NULL UNIQUE,
                   requested_at TIMESTAMPTZ NOT NULL,decided_at TIMESTAMPTZ,decided_by TEXT,
                   decision_reason TEXT,attempt_count INTEGER NOT NULL DEFAULT 0,max_attempts INTEGER NOT NULL DEFAULT 3,
                   next_attempt_at TIMESTAMPTZ,lease_owner TEXT,lease_expires_at TIMESTAMPTZ,
                   cancel_requested_at TIMESTAMPTZ,cancelled_at TIMESTAMPTZ,completed_at TIMESTAMPTZ,last_error TEXT
               )""",
            """CREATE TABLE action_executions (
                   id UUID PRIMARY KEY,request_id UUID NOT NULL REFERENCES action_requests(id),
                   attempt_number INTEGER NOT NULL,status TEXT NOT NULL,input_sha256 CHAR(64) NOT NULL,
                   output_sha256 CHAR(64),result JSONB NOT NULL DEFAULT '{}'::jsonb,error TEXT,
                   started_at TIMESTAMPTZ NOT NULL,finished_at TIMESTAMPTZ,worker_id TEXT,
                   UNIQUE (request_id,attempt_number)
               )""",
            """CREATE TABLE application_timeline (
                   id UUID PRIMARY KEY,project_id UUID REFERENCES projects(id),scope TEXT NOT NULL,
                   event_type TEXT NOT NULL,object_type TEXT NOT NULL,object_id TEXT NOT NULL,status TEXT NOT NULL,
                   summary TEXT NOT NULL,details JSONB NOT NULL,actor TEXT NOT NULL,occurred_at TIMESTAMPTZ NOT NULL
               )""",
            """CREATE TABLE internal_notifications (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id),title TEXT NOT NULL,
                   body TEXT NOT NULL,severity TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL,read_at TIMESTAMPTZ
               )""",
            """CREATE TABLE project_tasks (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id),title TEXT NOT NULL,
                   description TEXT NOT NULL,priority TEXT NOT NULL,status TEXT NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL
               )""",
            """CREATE TABLE signal_classifications (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id),
                   signal_event_id UUID NOT NULL REFERENCES signal_events(id),labels JSONB NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL
               )""",
            """CREATE TABLE action_drafts (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id),channel TEXT NOT NULL,
                   status TEXT NOT NULL,document JSONB NOT NULL,content_sha256 CHAR(64) NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
                   decided_at TIMESTAMPTZ,decided_by TEXT,decision_reason TEXT NOT NULL DEFAULT ''
               )""",
            """CREATE TABLE automated_data_jobs (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),
                   request_id UUID NOT NULL UNIQUE REFERENCES action_requests(id),job_type TEXT NOT NULL,
                   parameters JSONB NOT NULL,status TEXT NOT NULL,result JSONB NOT NULL DEFAULT '{}'::jsonb,
                   error TEXT,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL,
                   started_at TIMESTAMPTZ,finished_at TIMESTAMPTZ
               )""",
        )
        for statement in statements:
            connection.execute(statement)

    def _request(
        self,
        action_type: str,
        parameters: dict[str, object] | None = None,
        limits: dict[str, object] | None = None,
        *,
        status: str = "queued",
    ) -> uuid.UUID:
        request_id = uuid.uuid4()
        risk = "preparatory" if action_type.endswith("_draft") else "safe"
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                """INSERT INTO action_requests
                   (id,project_id,evaluation_id,action_type,risk_level,status,parameters,limits,
                    idempotency_key,requested_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    request_id,
                    self.project_id,
                    self.evaluation_id,
                    action_type,
                    risk,
                    status,
                    Jsonb(parameters or {}),
                    Jsonb(limits or {}),
                    secrets.token_hex(32),
                    NOW,
                ),
            )
        return request_id

    def _claim(self, *, now: datetime = NOW, lease_seconds: int = 120) -> dict[str, object] | None:
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            return claim_next_action_request(
                connection,
                "integration-worker",
                now,
                lease_seconds=lease_seconds,
            )

    def _execute(self, request: dict[str, object], *, now: datetime = NOW) -> dict[str, object]:
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            return execute_claimed_action_request(connection, request, now)

    def test_notification_is_executed_once_and_audited(self) -> None:
        request_id = self._request(
            "notification",
            {"title": "Alerte interne", "body": "Contrôle requis", "severity": "warning"},
        )
        request = self._claim()
        self.assertIsNotNone(request)
        assert request is not None
        result = self._execute(request, now=NOW + timedelta(seconds=1))
        self.assertEqual(result["status"], "completed")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM internal_notifications WHERE request_id=%s", (request_id,)).fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT status FROM action_requests WHERE id=%s", (request_id,)).fetchone()[0], "completed")
            self.assertEqual(connection.execute("SELECT status FROM action_executions WHERE request_id=%s", (request_id,)).fetchone()[0], "completed")
            self.assertEqual(connection.execute("SELECT count(*) FROM application_timeline WHERE object_id=%s", (str(request_id),)).fetchone()[0], 1)
        self.assertIsNone(self._claim(now=NOW + timedelta(seconds=2)))

    def test_running_request_can_be_cancelled_without_effect(self) -> None:
        request_id = self._request("hdp_task", {"title": "Ne doit pas être créée"})
        request = self._claim()
        self.assertIsNotNone(request)
        assert request is not None
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            cancellation = cancel_action_request(
                connection,
                request_id,
                "integration-operator",
                "Recette d'annulation",
                NOW + timedelta(seconds=1),
            )
        self.assertEqual(cancellation["status"], "cancel_requested")
        result = self._execute(request, now=NOW + timedelta(seconds=2))
        self.assertEqual(result["status"], "cancelled")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM project_tasks WHERE request_id=%s", (request_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT status FROM action_executions WHERE request_id=%s", (request_id,)).fetchone()[0], "cancelled")

    def test_policy_is_rechecked_after_claim_before_effect(self) -> None:
        request_id = self._request(
            "data_refresh",
            {"source": "hdx", "query": "cholera", "result_limit": 10},
            limits={"estimated_requests": 5, "estimated_bytes": 100000, "estimated_duration_seconds": 0},
        )
        request = self._claim()
        self.assertIsNotNone(request)
        assert request is not None
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                "UPDATE project_data_policies SET automatic_request_limit=1 WHERE project_id=%s",
                (self.project_id,),
            )
        result = self._execute(request, now=NOW + timedelta(seconds=1))
        self.assertEqual(result["status"], "pending_approval")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM automated_data_jobs WHERE request_id=%s", (request_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT status FROM action_executions WHERE request_id=%s", (request_id,)).fetchone()[0], "blocked")

    def test_explicit_approval_can_override_the_recorded_project_limit(self) -> None:
        request_id = self._request(
            "data_search",
            {"source": "reliefweb", "query": "cholera", "result_limit": 10},
            limits={"estimated_requests": 20, "estimated_bytes": 0, "estimated_duration_seconds": 0},
            status="pending_approval",
        )
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            decision = decide_action_request(
                connection,
                request_id,
                "approve",
                "integration-operator",
                "Volume explicitement approuvé pour la recette",
                NOW + timedelta(seconds=1),
            )
        self.assertEqual(decision["status"], "approved")
        request = self._claim(now=NOW + timedelta(seconds=2))
        self.assertIsNotNone(request)
        assert request is not None
        self.assertTrue(request["approved_override"])
        result = self._execute(request, now=NOW + timedelta(seconds=3))
        self.assertEqual(result["status"], "completed")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM automated_data_jobs WHERE request_id=%s", (request_id,)).fetchone()[0], 1)

    def test_expired_lease_is_requeued_and_claimed_with_new_attempt(self) -> None:
        request_id = self._request("email_draft", {"document": {"subject": "Veille"}})
        first = self._claim(lease_seconds=5)
        self.assertIsNotNone(first)
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            recovered = recover_stale_action_requests(connection, NOW + timedelta(seconds=6))
        self.assertEqual(recovered, 1)
        second = self._claim(now=NOW + timedelta(seconds=7))
        self.assertIsNotNone(second)
        assert second is not None
        self.assertEqual(second["attempt_number"], 2)
        result = self._execute(second, now=NOW + timedelta(seconds=8))
        self.assertEqual(result["status"], "completed")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            statuses = [row[0] for row in connection.execute("SELECT status FROM action_executions WHERE request_id=%s ORDER BY attempt_number", (request_id,)).fetchall()]
        self.assertEqual(statuses, ["failed", "completed"])

    def test_external_action_is_never_claimed_by_internal_worker(self) -> None:
        request_id = self._request(
            "webhook",
            {
                "webhook_version_id": str(uuid.uuid4()),
                "configuration_sha256": "a" * 64,
            },
            status="approved",
        )
        self.assertIsNone(self._claim())
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self.assertEqual(connection.execute("SELECT status FROM action_requests WHERE id=%s", (request_id,)).fetchone()[0], "approved")
            self.assertEqual(connection.execute("SELECT count(*) FROM action_executions WHERE request_id=%s", (request_id,)).fetchone()[0], 0)

    def test_invalid_effect_is_rolled_back_and_retried_with_backoff(self) -> None:
        request_id = self._request("hdp_task", {"title": "Priorité invalide", "priority": "unbounded"})
        request = self._claim()
        self.assertIsNotNone(request)
        assert request is not None
        with self.assertRaisesRegex(ValueError, "priority"):
            self._execute(request, now=NOW + timedelta(seconds=1))
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            result = mark_action_request_failed(
                connection,
                request,
                "hdp_task.priority: valeur invalide",
                NOW + timedelta(seconds=1),
            )
        self.assertEqual(result["status"], "queued")
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            row = connection.execute(
                "SELECT status,next_attempt_at,attempt_count FROM action_requests WHERE id=%s",
                (request_id,),
            ).fetchone()
            self.assertEqual(row[0], "queued")
            self.assertGreater(row[1], NOW + timedelta(seconds=1))
            self.assertEqual(row[2], 1)
            self.assertEqual(connection.execute("SELECT count(*) FROM project_tasks WHERE request_id=%s", (request_id,)).fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT status FROM action_executions WHERE request_id=%s", (request_id,)).fetchone()[0], "failed")

    def test_operator_view_exposes_attempts_decision_draft_and_data_job(self) -> None:
        draft_request_id = self._request("email_draft", {"document": {"subject": "Bulletin choléra"}})
        first = self._claim(lease_seconds=5)
        self.assertIsNotNone(first)
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            recover_stale_action_requests(connection, NOW + timedelta(seconds=6))
        second = self._claim(now=NOW + timedelta(seconds=7))
        self.assertIsNotNone(second)
        assert second is not None
        self._execute(second, now=NOW + timedelta(seconds=8))

        job_request_id = self._request(
            "data_search",
            {"sources": ["hdx"], "query": "cholera", "result_limit": 10},
            {"estimated_requests": 1, "estimated_bytes": 0, "estimated_duration_seconds": 0},
        )
        job_request = self._claim(now=NOW + timedelta(seconds=9))
        self.assertIsNotNone(job_request)
        assert job_request is not None
        self._execute(job_request, now=NOW + timedelta(seconds=10))

        rejected_request_id = self._request("notification", status="pending_approval")
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            decide_action_request(
                connection,
                rejected_request_id,
                "reject",
                "integration-operator",
                "Action refusée pendant la recette",
                NOW + timedelta(seconds=11),
            )
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            items = list_project_action_requests(connection, self.project_id)

        draft = next(item for item in items if item["id"] == draft_request_id)
        self.assertEqual([item["status"] for item in draft["executions"]], ["failed", "completed"])
        self.assertEqual(draft["draft_status"], "draft")
        self.assertEqual(draft["draft_title"], "Bulletin choléra")
        job = next(item for item in items if item["id"] == job_request_id)
        self.assertIsNotNone(job["data_job_id"])
        self.assertEqual(job["data_job_status"], "queued")
        rejected = next(item for item in items if item["id"] == rejected_request_id)
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["decision_reason"], "Action refusée pendant la recette")


if __name__ == "__main__":
    unittest.main()
