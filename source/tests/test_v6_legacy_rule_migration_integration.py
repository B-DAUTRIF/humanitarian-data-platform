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


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_legacy_rules import (  # noqa: E402
    LEGACY_DATAGRID_ACTION,
    migrate_legacy_signal_rules,
)


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
NOW = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "recette PostgreSQL réelle activée uniquement avec HDP_BACKUP_RESTORE_TEST_DATABASE_URL",
)
class LegacyRuleMigrationPostgresIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.database_name = f"hdp_legacy_rules_{secrets.token_hex(6)}"
        self.database_url = self._database_url(self.database_name)
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.database_name)))
        self.project_id, self.legacy_rule_id = uuid.uuid4(), uuid.uuid4()
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            self._create_schema(connection)
            connection.execute(
                "INSERT INTO projects (id,name) VALUES (%s,'Migration fixture')",
                (self.project_id,),
            )
            connection.execute(
                """INSERT INTO signal_rules
                   (id,project_id,name,enabled,locations,themes,min_severity,min_confidence,
                    lookback_hours,data_grid_dimensions,query_template,refresh_due_resources,
                    created_at,updated_at)
                   VALUES (%s,%s,'Règle V5',TRUE,%s,%s,0.4,0.6,72,%s,%s,TRUE,%s,%s)""",
                (
                    self.legacy_rule_id,
                    self.project_id,
                    Jsonb(["France"]),
                    Jsonb(["cholera"]),
                    Jsonb(["affected-people"]),
                    "{title} {themes} {locations}",
                    NOW,
                    NOW,
                ),
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
        for statement in (
            "CREATE TABLE projects (id UUID PRIMARY KEY,name TEXT NOT NULL)",
            """CREATE TABLE signal_rules (
                   id UUID PRIMARY KEY,project_id UUID NOT NULL REFERENCES projects(id),name TEXT NOT NULL,
                   enabled BOOLEAN NOT NULL,locations JSONB NOT NULL,themes JSONB NOT NULL,
                   min_severity NUMERIC NOT NULL,min_confidence NUMERIC NOT NULL,lookback_hours INTEGER NOT NULL,
                   data_grid_dimensions JSONB NOT NULL,query_template TEXT NOT NULL,
                   refresh_due_resources BOOLEAN NOT NULL,created_at TIMESTAMPTZ NOT NULL,
                   updated_at TIMESTAMPTZ NOT NULL,migrated_definition_id UUID
               )""",
            """CREATE TABLE rule_definitions (
                   id UUID PRIMARY KEY,project_id UUID REFERENCES projects(id),scope TEXT NOT NULL,
                   name TEXT NOT NULL,description TEXT NOT NULL,enabled BOOLEAN NOT NULL,
                   current_version_number INTEGER NOT NULL,legacy_signal_rule_id UUID UNIQUE,
                   created_by TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL,updated_at TIMESTAMPTZ NOT NULL
               )""",
            """CREATE TABLE rule_versions (
                   id UUID PRIMARY KEY,definition_id UUID NOT NULL REFERENCES rule_definitions(id),
                   version_number INTEGER NOT NULL,schema_version TEXT NOT NULL,rule_tree JSONB NOT NULL,
                   actions JSONB NOT NULL,definition_sha256 CHAR(64) NOT NULL,created_by TEXT NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL,UNIQUE(definition_id,version_number)
               )""",
            """CREATE TABLE application_timeline (
                   id UUID PRIMARY KEY,project_id UUID REFERENCES projects(id),scope TEXT NOT NULL,
                   event_type TEXT NOT NULL,object_type TEXT NOT NULL,object_id TEXT NOT NULL,
                   status TEXT NOT NULL,summary TEXT NOT NULL,details JSONB NOT NULL,actor TEXT NOT NULL,
                   occurred_at TIMESTAMPTZ NOT NULL
               )""",
        ):
            connection.execute(statement)

    def test_preview_then_confirm_is_atomic_linked_and_idempotent(self) -> None:
        with psycopg.connect(self.database_url, autocommit=False) as connection:
            preview = migrate_legacy_signal_rules(connection, self.project_id, confirm=False)
        self.assertFalse(preview["confirmed"])
        self.assertEqual(preview["candidates"][0]["rule_tree"]["children"][-1]["value"], 72.0)
        self.assertEqual(preview["candidates"][0]["actions"][0]["type"], LEGACY_DATAGRID_ACTION)

        with psycopg.connect(self.database_url, autocommit=False) as connection:
            result = migrate_legacy_signal_rules(connection, self.project_id, confirm=True)
        self.assertEqual(len(result["migrated"]), 1)
        definition_id = uuid.UUID(result["migrated"][0]["definition_id"])
        with psycopg.connect(self.database_url, autocommit=True) as connection:
            legacy = connection.execute(
                "SELECT enabled,migrated_definition_id FROM signal_rules WHERE id=%s",
                (self.legacy_rule_id,),
            ).fetchone()
            definition = connection.execute(
                "SELECT enabled,legacy_signal_rule_id FROM rule_definitions WHERE id=%s",
                (definition_id,),
            ).fetchone()
            actions = connection.execute(
                "SELECT actions FROM rule_versions WHERE definition_id=%s",
                (definition_id,),
            ).fetchone()[0]
        self.assertEqual(legacy, (False, definition_id))
        self.assertEqual(definition, (True, self.legacy_rule_id))
        self.assertEqual(actions[0]["parameters"]["query_template"], "{title} {themes} {locations}")

        with psycopg.connect(self.database_url, autocommit=False) as connection:
            repeated = migrate_legacy_signal_rules(connection, self.project_id, confirm=True)
        self.assertEqual(repeated["migrated"], [])
        self.assertEqual(repeated["already_migrated"][0]["definition_id"], str(definition_id))
