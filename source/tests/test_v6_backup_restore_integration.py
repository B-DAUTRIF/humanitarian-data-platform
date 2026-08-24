from __future__ import annotations

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
    BackupError,
    TEMPORARY_RESTORE_DATABASE_PREFIX,
    build_manifest,
    create_global_dump,
    publish_bundle,
    restore_global_backup_to_temporary_database,
)


TEST_DATABASE_URL = os.getenv("HDP_BACKUP_RESTORE_TEST_DATABASE_URL", "").strip()
SCHEMA_VERSIONS = ["fixture-001"]


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


if __name__ == "__main__":
    unittest.main()
