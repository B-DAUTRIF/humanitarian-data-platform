from __future__ import annotations

import os
import secrets
import sys
import unittest
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
from pglast import parse_sql


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_timeline import GLOBAL_TIMELINE_QUERY, PROJECT_TIMELINE_QUERY, list_timeline  # noqa: E402


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


class TimelineSqlContractTest(unittest.TestCase):
    def test_unified_timeline_queries_are_valid_postgresql(self) -> None:
        parse_sql(GLOBAL_TIMELINE_QUERY.replace("%s", "NULL"))
        parse_sql(PROJECT_TIMELINE_QUERY.replace("%s", "NULL"))


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "recette PostgreSQL réelle activée uniquement avec HDP_BACKUP_RESTORE_TEST_DATABASE_URL",
)
class TimelinePostgresIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database_name = f"hdp_timeline_{secrets.token_hex(6)}"
        self.database_url = self._database_url(self.database_name)
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database_name)))
        self.project_id = uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self._create_schema(connection)
            connection.execute("INSERT INTO projects (id,name) VALUES (%s,'Chronologie')", (self.project_id,))

    def tearDown(self) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()",
                (self.database_name,),
            )
            connection.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(self.database_name)))

    @staticmethod
    def _create_schema(connection: psycopg.Connection[object]) -> None:
        statements = (
            "CREATE TABLE projects (id UUID PRIMARY KEY,name TEXT NOT NULL)",
            """CREATE TABLE application_timeline (
                   id UUID PRIMARY KEY,project_id UUID REFERENCES projects(id),scope TEXT NOT NULL,
                   event_type TEXT NOT NULL,object_type TEXT NOT NULL,object_id TEXT,status TEXT NOT NULL,
                   summary TEXT NOT NULL,details JSONB NOT NULL,actor TEXT NOT NULL,occurred_at TIMESTAMPTZ NOT NULL
               )""",
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY,description TEXT NOT NULL,applied_at TIMESTAMPTZ NOT NULL)",
            """CREATE TABLE source_api_versions (
                   id UUID PRIMARY KEY,source_id TEXT NOT NULL,api_version TEXT NOT NULL,
                   documentation_sha256 CHAR(64),verified_at TIMESTAMPTZ NOT NULL,
                   valid_from TIMESTAMPTZ NOT NULL,valid_until TIMESTAMPTZ
               )""",
            "CREATE TABLE source_endpoints (id UUID PRIMARY KEY,api_version_id UUID NOT NULL REFERENCES source_api_versions(id),endpoint_id TEXT NOT NULL)",
            """CREATE TABLE endpoint_activation_history (
                   id UUID PRIMARY KEY,endpoint_id UUID NOT NULL REFERENCES source_endpoints(id),
                   previous_state TEXT NOT NULL,new_state TEXT NOT NULL,evidence JSONB NOT NULL,
                   actor TEXT NOT NULL,occurred_at TIMESTAMPTZ NOT NULL
               )""",
            """CREATE TABLE federated_searches (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),query TEXT NOT NULL,
                   criteria JSONB NOT NULL,sources JSONB NOT NULL,status TEXT NOT NULL,
                   started_at TIMESTAMPTZ NOT NULL,finished_at TIMESTAMPTZ
               )""",
            """CREATE TABLE acquisitions (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),source TEXT NOT NULL,
                   query TEXT NOT NULL,retrieved_at TIMESTAMPTZ NOT NULL,sha256 CHAR(64) NOT NULL,item_count INTEGER NOT NULL
               )""",
            "CREATE TABLE project_scripts (id UUID PRIMARY KEY,name TEXT NOT NULL)",
            """CREATE TABLE script_executions (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),script_id UUID NOT NULL REFERENCES project_scripts(id),
                   language TEXT NOT NULL,status TEXT NOT NULL,requested_at TIMESTAMPTZ NOT NULL,error TEXT
               )""",
            """CREATE TABLE resource_refresh_schedules (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),resource_id UUID NOT NULL
               )""",
            """CREATE TABLE resource_refresh_runs (
                   id UUID PRIMARY KEY,refresh_schedule_id UUID NOT NULL REFERENCES resource_refresh_schedules(id),
                   acquisition_id UUID,error TEXT,started_at TIMESTAMPTZ NOT NULL,status TEXT NOT NULL
               )""",
            """CREATE TABLE signal_events (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),source TEXT NOT NULL,
                   title TEXT NOT NULL,severity NUMERIC NOT NULL,confidence NUMERIC NOT NULL,
                   themes JSONB NOT NULL,locations JSONB NOT NULL,received_at TIMESTAMPTZ NOT NULL
               )""",
        )
        for statement in statements:
            connection.execute(statement)

    def _database_url(self, database_name: str) -> str:
        parsed = urlparse(TEST_DATABASE_URL)
        return urlunparse(parsed._replace(path=f"/{database_name}"))

    def test_global_timeline_unifies_migrations_contracts_activations_and_audit(self) -> None:
        version_id, endpoint_id = uuid.uuid4(), uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute("INSERT INTO schema_migrations VALUES ('6.0.0-test','Test',%s)", (NOW,))
            connection.execute(
                "INSERT INTO source_api_versions VALUES (%s,'who','v1',%s,%s,%s,NULL)",
                (version_id, "a" * 64, NOW, NOW),
            )
            connection.execute("INSERT INTO source_endpoints VALUES (%s,%s,'search')", (endpoint_id, version_id))
            connection.execute(
                "INSERT INTO endpoint_activation_history VALUES (%s,%s,'inventoried','active_global',%s,'operator',%s)",
                (uuid.uuid4(), endpoint_id, Jsonb({"test_report_sha256": "b" * 64}), NOW),
            )
            connection.execute(
                "INSERT INTO application_timeline VALUES (%s,NULL,'global','application.started','application','6.0.0-dev','completed','Application démarrée','{}','system',%s)",
                (uuid.uuid4(), NOW),
            )
            items = list_timeline(connection, "global", None, None, 100)
        self.assertEqual(
            {item["event_type"] for item in items},
            {"migration.applied", "connector.contract_imported", "connector.endpoint_state", "application.started"},
        )

    def test_project_timeline_unifies_search_acquisition_script_refresh_signal_and_v6_audit(self) -> None:
        search_id, acquisition_id, script_id, execution_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        refresh_schedule_id, refresh_id, signal_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            connection.execute(
                "INSERT INTO federated_searches VALUES (%s,%s,'choléra',%s,%s,'completed',%s,%s)",
                (search_id, self.project_id, Jsonb({}), Jsonb(["who", "hdx"]), NOW, NOW),
            )
            connection.execute(
                "INSERT INTO acquisitions VALUES (%s,%s,'hdx','choléra',%s,%s,2)",
                (acquisition_id, self.project_id, NOW, "c" * 64),
            )
            connection.execute("INSERT INTO project_scripts VALUES (%s,'Incidence')", (script_id,))
            connection.execute(
                "INSERT INTO script_executions VALUES (%s,%s,%s,'python','completed',%s,NULL)",
                (execution_id, self.project_id, script_id, NOW),
            )
            connection.execute(
                "INSERT INTO resource_refresh_schedules VALUES (%s,%s,%s)",
                (refresh_schedule_id, self.project_id, uuid.uuid4()),
            )
            connection.execute(
                "INSERT INTO resource_refresh_runs VALUES (%s,%s,%s,NULL,%s,'completed')",
                (refresh_id, refresh_schedule_id, acquisition_id, NOW),
            )
            connection.execute(
                "INSERT INTO signal_events VALUES (%s,%s,'rss','Alerte choléra',0.8,0.9,%s,%s,%s)",
                (signal_id, self.project_id, Jsonb(["cholera"]), Jsonb(["France"]), NOW),
            )
            connection.execute(
                "INSERT INTO application_timeline VALUES (%s,%s,'project','cache.materialized','cache_entry',%s,'completed','Cache matérialisé','{}','system',%s)",
                (uuid.uuid4(), self.project_id, str(uuid.uuid4()), NOW),
            )
            items = list_timeline(connection, "project", self.project_id, None, 100)
        self.assertEqual(
            {item["event_type"] for item in items},
            {"search.federated", "acquisition.completed", "script.execution", "resource.refresh", "signal.ingested", "cache.materialized"},
        )
