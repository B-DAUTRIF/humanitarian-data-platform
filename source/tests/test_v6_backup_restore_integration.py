from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlparse, urlunparse

import psycopg
from psycopg import sql


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_backup import (  # noqa: E402
    ACTION_WORKER_SCHEMA_VERSION,
    BackupError,
    SIGNALS_RESTORE_ACTION_WORKER_TABLES,
    SIGNALS_RESTORE_CORE_TABLES,
    TEMPORARY_RESTORE_DATABASE_PREFIX,
    _scoped_restore_inventory,
    build_manifest,
    create_global_dump,
    export_project_graph,
    publish_bundle,
    restore_global_backup_to_temporary_database,
    restore_project_backup_to_temporary_database,
    restore_signals_backup_to_temporary_database,
    select_signal_backup_events,
)


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
SCHEMA_VERSIONS = ["fixture-001"]


def _signals_inventory_manifest(tables: set[str], schema_versions: list[str]) -> dict[str, object]:
    return {
        "manifest_version": "1.0",
        "scope": "signals",
        "schema_versions": schema_versions,
        "restore_automatically_authorized": False,
        "files": [
            {"name": f"{table}.jsonl", "size_bytes": 0, "sha256": "0" * 64}
            for table in sorted(tables)
        ],
        "row_counts": {table: 0 for table in tables},
    }


class SignalsInventoryCompatibilityTest(unittest.TestCase):
    def test_legacy_signal_manifest_keeps_the_original_required_tables(self) -> None:
        manifest = _signals_inventory_manifest(set(SIGNALS_RESTORE_CORE_TABLES), ["fixture-001"])
        self.assertEqual(set(_scoped_restore_inventory(manifest)), SIGNALS_RESTORE_CORE_TABLES)

    def test_action_worker_migration_requires_all_new_effect_tables(self) -> None:
        incomplete = _signals_inventory_manifest(
            set(SIGNALS_RESTORE_CORE_TABLES),
            ["fixture-001", ACTION_WORKER_SCHEMA_VERSION],
        )
        with self.assertRaisesRegex(BackupError, "action_drafts"):
            _scoped_restore_inventory(incomplete)
        complete_tables = SIGNALS_RESTORE_CORE_TABLES | SIGNALS_RESTORE_ACTION_WORKER_TABLES
        complete = _signals_inventory_manifest(
            set(complete_tables),
            ["fixture-001", ACTION_WORKER_SCHEMA_VERSION],
        )
        self.assertEqual(set(_scoped_restore_inventory(complete)), complete_tables)


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "recette PostgreSQL réelle activée uniquement avec HDP_BACKUP_RESTORE_TEST_DATABASE_URL",
)
class TemporaryPostgresRestoreIntegrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source_database = f"hdp_backup_source_{secrets.token_hex(6)}"
        self.source_url = self._database_url(self.source_database)
        self._create_database(self.source_database)
        with psycopg.connect(self.source_url, autocommit=True) as connection:
            connection.execute(
                """CREATE TABLE schema_migrations (
                       version TEXT PRIMARY KEY,
                       description TEXT NOT NULL,
                       applied_at TIMESTAMPTZ NOT NULL
                   )"""
            )
            connection.execute(
                "INSERT INTO schema_migrations VALUES (%s,%s,%s)",
                (SCHEMA_VERSIONS[0], "fixture", datetime.now(UTC)),
            )
            connection.execute("CREATE TABLE restore_probe (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            connection.execute("INSERT INTO restore_probe VALUES (1,'verified')")
            connection.execute("CREATE TABLE projects (id UUID PRIMARY KEY, name TEXT NOT NULL)")
            connection.execute(
                """CREATE TABLE signal_events (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       payload JSONB NOT NULL,
                       occurred_at TIMESTAMPTZ NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE signal_rules (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       name TEXT NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE signal_actions (
                       id UUID PRIMARY KEY,
                       event_id UUID NOT NULL REFERENCES signal_events(id),
                       rule_id UUID NOT NULL REFERENCES signal_rules(id)
                   )"""
            )
            connection.execute(
                """CREATE TABLE rule_definitions (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       name TEXT NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE rule_versions (
                       id UUID PRIMARY KEY,
                       definition_id UUID NOT NULL REFERENCES rule_definitions(id),
                       version_number INTEGER NOT NULL
                   )"""
            )
            connection.execute(
                """CREATE TABLE rule_evaluations (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       definition_id UUID NOT NULL REFERENCES rule_definitions(id),
                       rule_version_id UUID NOT NULL REFERENCES rule_versions(id),
                       triggering_event_id UUID NOT NULL REFERENCES signal_events(id)
                   )"""
            )
            connection.execute(
                """CREATE TABLE action_requests (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       evaluation_id UUID NOT NULL REFERENCES rule_evaluations(id)
                   )"""
            )
            connection.execute(
                """CREATE TABLE action_executions (
                       id UUID PRIMARY KEY,
                       request_id UUID NOT NULL REFERENCES action_requests(id)
                )"""
            )
            connection.execute(
                """CREATE TABLE data_artifacts (
                       id UUID PRIMARY KEY,
                       project_id UUID NOT NULL REFERENCES projects(id),
                       path TEXT,
                       sha256 CHAR(64)
                   )"""
            )

    def tearDown(self) -> None:
        self._drop_database(self.source_database)

    def _database_url(self, database: str) -> str:
        parsed = urlparse(TEST_DATABASE_URL)
        return urlunparse(parsed._replace(path=f"/{database}"))

    def _create_database(self, database: str) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))

    def _drop_database(self, database: str) -> None:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s",
                (database,),
            )
            connection.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(database)))

    def _bundle(self, root: Path) -> Path:
        dump = root / "postgresql-global.dump"
        create_global_dump(self.source_url, dump, timeout_seconds=120)
        manifest = build_manifest(
            backup_id="global-integration",
            application_version="6.0.0-dev",
            schema_versions=SCHEMA_VERSIONS,
            scope="global",
            selector={"project_id": None, "signal_ids": []},
            files=[dump],
            row_counts={"postgresql-global": -1},
        )
        return publish_bundle(root, "global-integration", [dump], manifest)

    def _signals_bundle(
        self,
        root: Path,
        *,
        duplicate_project: bool = False,
        multi_project: bool = False,
    ) -> Path:
        identifiers = {
            "project": "11111111-1111-4111-8111-111111111111",
            "project_two": "11111111-1111-4111-8111-222222222222",
            "event": "22222222-2222-4222-8222-222222222222",
            "event_two": "22222222-2222-4222-8222-333333333333",
            "signal_rule": "33333333-3333-4333-8333-333333333333",
            "signal_action": "44444444-4444-4444-8444-444444444444",
            "definition": "55555555-5555-4555-8555-555555555555",
            "version": "66666666-6666-4666-8666-666666666666",
            "evaluation": "77777777-7777-4777-8777-777777777777",
            "request": "88888888-8888-4888-8888-888888888888",
            "execution": "99999999-9999-4999-8999-999999999999",
        }
        rows = {
            "projects": [{"id": identifiers["project"], "name": "Projet restauré"}],
            "signal_events": [
                {
                    "id": identifiers["event"],
                    "project_id": identifiers["project"],
                    "payload": {"source": "fixture"},
                    "occurred_at": "2026-08-01T12:00:00+00:00",
                }
            ],
            "signal_rules": [
                {
                    "id": identifiers["signal_rule"],
                    "project_id": identifiers["project"],
                    "name": "Règle fixture",
                }
            ],
            "signal_actions": [
                {
                    "id": identifiers["signal_action"],
                    "event_id": identifiers["event"],
                    "rule_id": identifiers["signal_rule"],
                }
            ],
            "rule_definitions": [
                {
                    "id": identifiers["definition"],
                    "project_id": identifiers["project"],
                    "name": "Définition fixture",
                }
            ],
            "rule_versions": [
                {
                    "id": identifiers["version"],
                    "definition_id": identifiers["definition"],
                    "version_number": 1,
                }
            ],
            "rule_evaluations": [
                {
                    "id": identifiers["evaluation"],
                    "project_id": identifiers["project"],
                    "definition_id": identifiers["definition"],
                    "rule_version_id": identifiers["version"],
                    "triggering_event_id": identifiers["event"],
                }
            ],
            "action_requests": [
                {
                    "id": identifiers["request"],
                    "project_id": identifiers["project"],
                    "evaluation_id": identifiers["evaluation"],
                }
            ],
            "action_executions": [
                {"id": identifiers["execution"], "request_id": identifiers["request"]}
            ],
        }
        if duplicate_project:
            rows["projects"].append(dict(rows["projects"][0]))
        if multi_project:
            rows["projects"].append(
                {"id": identifiers["project_two"], "name": "Second projet restauré"}
            )
            rows["signal_events"].append(
                {
                    "id": identifiers["event_two"],
                    "project_id": identifiers["project_two"],
                    "payload": {"source": "fixture-global"},
                    "occurred_at": "2026-08-02T12:00:00+00:00",
                }
            )
        files: list[Path] = []
        row_counts: dict[str, int] = {}
        for table, documents in rows.items():
            path = root / f"{table}.jsonl"
            path.write_text(
                "".join(json.dumps(document, ensure_ascii=False) + "\n" for document in documents),
                encoding="utf-8",
            )
            files.append(path)
            row_counts[table] = len(documents)
        manifest = build_manifest(
            backup_id="signals-integration",
            application_version="6.0.0-dev",
            schema_versions=SCHEMA_VERSIONS,
            scope="signals",
            selector={
                "project_id": None if multi_project else identifiers["project"],
                "signal_ids": [] if multi_project else [identifiers["event"]],
                "selection_mode": "global" if multi_project else "explicit_ids",
            },
            files=files,
            row_counts=row_counts,
        )
        return publish_bundle(root, "signals-integration", files, manifest)

    def _project_bundle(self, root: Path, *, duplicate_artifact: bool = False) -> tuple[Path, int]:
        project_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        event_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
        rule_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
        action_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
        artifact_id = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
        data_directory = root / "data"
        asset = data_directory / "projects" / project_id / "evidence.json"
        asset.parent.mkdir(parents=True)
        asset.write_text('{"verified":true}\n', encoding="utf-8")
        relative_asset = asset.relative_to(data_directory).as_posix()
        with psycopg.connect(self.source_url, autocommit=True) as connection:
            connection.execute("INSERT INTO projects VALUES (%s,%s)", (project_id, "Projet fixture"))
            connection.execute(
                "INSERT INTO signal_events VALUES (%s,%s,%s)",
                (event_id, project_id, json.dumps({"source": "fixture"})),
            )
            connection.execute(
                "INSERT INTO signal_rules VALUES (%s,%s,%s)",
                (rule_id, project_id, "Règle fixture"),
            )
            connection.execute(
                "INSERT INTO signal_actions VALUES (%s,%s,%s)",
                (action_id, event_id, rule_id),
            )
            connection.execute(
                "INSERT INTO data_artifacts VALUES (%s,%s,%s,%s)",
                (artifact_id, project_id, relative_asset, None),
            )
        with psycopg.connect(self.source_url, autocommit=False) as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            files, row_counts, assets = export_project_graph(
                connection,
                root,
                project_id,
                data_directory,
            )
            connection.commit()
        if duplicate_artifact:
            artifact_file = root / "data_artifacts.jsonl"
            first_line = artifact_file.read_text(encoding="utf-8")
            artifact_file.write_text(first_line + first_line, encoding="utf-8")
            row_counts["data_artifacts"] = 2
        manifest = build_manifest(
            backup_id="project-integration",
            application_version="6.0.0-dev",
            schema_versions=SCHEMA_VERSIONS,
            scope="project",
            selector={"project_id": project_id, "signal_ids": []},
            files=files,
            row_counts=row_counts,
        )
        manifest["project_assets"] = assets
        bundle = publish_bundle(root, "project-integration", files, manifest)
        return bundle, asset.stat().st_size

    def test_global_dump_is_restored_verified_and_temporary_database_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle = self._bundle(Path(directory))
            with patch("app.v6_backup.secrets.token_hex", return_value=token):
                report = restore_global_backup_to_temporary_database(
                    bundle,
                    TEST_DATABASE_URL,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            self.assertEqual(report["status"], "temporary_restore_verified")
            self.assertTrue(report["restore_executed"])
            self.assertTrue(report["temporary_database_dropped"])
            self.assertEqual(report["collision_policy"], "reject_without_overwrite")
            self.assertGreaterEqual(report["restored_table_count"], 2)
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)

    def test_existing_temporary_database_collision_is_rejected_without_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            colliding_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle = self._bundle(Path(directory))
            self._create_database(colliding_database)
            try:
                with (
                    patch("app.v6_backup.secrets.token_hex", return_value=token),
                    self.assertRaisesRegex(BackupError, "collision ou droits insuffisants"),
                ):
                    restore_global_backup_to_temporary_database(
                        bundle,
                        TEST_DATABASE_URL,
                        expected_application_version="6.0.0-dev",
                        expected_schema_versions=SCHEMA_VERSIONS,
                        timeout_seconds=120,
                    )
                with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                    exists = connection.execute(
                        "SELECT 1 FROM pg_database WHERE datname=%s", (colliding_database,)
                    ).fetchone()
                self.assertIsNotNone(exists)
            finally:
                self._drop_database(colliding_database)

    def test_signal_bundle_is_restored_in_dependency_order_and_database_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle = self._signals_bundle(Path(directory))
            with patch("app.v6_backup.secrets.token_hex", return_value=token):
                report = restore_signals_backup_to_temporary_database(
                    bundle,
                    self.source_url,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            self.assertEqual(report["scope"], "signals")
            self.assertEqual(report["restored_table_count"], 9)
            self.assertEqual(report["restored_row_count"], 9)
            self.assertTrue(report["temporary_database_dropped"])
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)

    def test_multi_project_signal_bundle_is_restored_and_database_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle = self._signals_bundle(Path(directory), multi_project=True)
            with patch("app.v6_backup.secrets.token_hex", return_value=token):
                report = restore_signals_backup_to_temporary_database(
                    bundle,
                    self.source_url,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            self.assertEqual(report["restored_table_count"], 9)
            self.assertEqual(report["restored_row_count"], 11)
            self.assertTrue(report["temporary_database_dropped"])
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)

    def test_signal_selector_applies_project_and_half_open_period(self) -> None:
        project_one = "aaaaaaaa-1111-4111-8111-111111111111"
        project_two = "aaaaaaaa-2222-4222-8222-222222222222"
        event_one = "bbbbbbbb-1111-4111-8111-111111111111"
        event_boundary = "bbbbbbbb-2222-4222-8222-222222222222"
        event_other_project = "bbbbbbbb-3333-4333-8333-333333333333"
        start = datetime(2026, 8, 1, tzinfo=UTC)
        end = datetime(2026, 8, 2, tzinfo=UTC)
        with psycopg.connect(self.source_url, autocommit=True) as connection:
            connection.execute(
                "INSERT INTO projects(id,name) VALUES (%s,'Projet un'),(%s,'Projet deux')",
                (project_one, project_two),
            )
            connection.execute(
                """INSERT INTO signal_events(id,project_id,payload,occurred_at)
                   VALUES (%s,%s,'{}',%s),(%s,%s,'{}',%s),(%s,%s,'{}',%s)""",
                (
                    event_one,
                    project_one,
                    datetime(2026, 8, 1, 12, tzinfo=UTC),
                    event_boundary,
                    project_one,
                    end,
                    event_other_project,
                    project_two,
                    datetime(2026, 8, 1, 18, tzinfo=UTC),
                ),
            )
            selected, projects = select_signal_backup_events(
                connection,
                project_id=project_one,
                signal_ids=[],
                signal_from=start,
                signal_to=end,
            )
            self.assertEqual([str(identifier) for identifier in selected], [event_one])
            self.assertEqual([str(identifier) for identifier in projects], [project_one])
            selected, projects = select_signal_backup_events(
                connection,
                project_id=None,
                signal_ids=[],
                signal_from=start,
                signal_to=end,
            )
            self.assertEqual(
                {str(identifier) for identifier in selected},
                {event_one, event_other_project},
            )
            self.assertEqual(
                {str(identifier) for identifier in projects},
                {project_one, project_two},
            )

    def test_duplicate_signal_bundle_identifier_is_rejected_and_database_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle = self._signals_bundle(Path(directory), duplicate_project=True)
            with (
                patch("app.v6_backup.secrets.token_hex", return_value=token),
                self.assertRaisesRegex(BackupError, "collision d'identifiant"),
            ):
                restore_signals_backup_to_temporary_database(
                    bundle,
                    self.source_url,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)

    def test_project_graph_and_asset_are_restored_then_database_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle, asset_size = self._project_bundle(Path(directory))
            with patch("app.v6_backup.secrets.token_hex", return_value=token):
                report = restore_project_backup_to_temporary_database(
                    bundle,
                    self.source_url,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            self.assertEqual(report["scope"], "project")
            self.assertEqual(report["restored_table_count"], 5)
            self.assertEqual(report["restored_row_count"], 5)
            self.assertEqual(report["verified_asset_count"], 1)
            self.assertEqual(report["verified_asset_size_bytes"], asset_size)
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)

    def test_duplicate_project_artifact_identifier_rolls_back_and_drops_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            token = secrets.token_hex(8)
            temporary_database = f"{TEMPORARY_RESTORE_DATABASE_PREFIX}{token}"
            bundle, _ = self._project_bundle(Path(directory), duplicate_artifact=True)
            with (
                patch("app.v6_backup.secrets.token_hex", return_value=token),
                self.assertRaisesRegex(BackupError, "collision d'identifiant"),
            ):
                restore_project_backup_to_temporary_database(
                    bundle,
                    self.source_url,
                    expected_application_version="6.0.0-dev",
                    expected_schema_versions=SCHEMA_VERSIONS,
                    timeout_seconds=120,
                )
            with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
                exists = connection.execute(
                    "SELECT 1 FROM pg_database WHERE datname=%s", (temporary_database,)
                ).fetchone()
            self.assertIsNone(exists)


if __name__ == "__main__":
    unittest.main()
