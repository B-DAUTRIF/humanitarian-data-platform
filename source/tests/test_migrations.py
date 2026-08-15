from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.migrations import MIGRATIONS, apply_migrations, migration_versions  # noqa: E402


class Result:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, applied=()):
        self.applied = tuple(applied)
        self.calls: list[tuple[str, object]] = []

    def execute(self, statement, parameters=None):
        normalized = " ".join(statement.split())
        self.calls.append((normalized, parameters))
        if normalized == "SELECT version FROM schema_migrations":
            return Result((version,) for version in self.applied)
        return Result()


class MigrationContractTest(unittest.TestCase):
    def test_versions_are_unique_and_monotonic(self) -> None:
        versions = migration_versions()
        self.assertEqual(len(versions), len(set(versions)))
        self.assertEqual(versions, tuple(sorted(versions)))

    def test_first_run_applies_every_statement_and_records_version(self) -> None:
        connection = FakeConnection()
        applied_at = datetime(2026, 8, 14, 10, 0, tzinfo=UTC)
        self.assertEqual(apply_migrations(connection, applied_at), list(migration_versions()))
        executed_sql = [statement for statement, _ in connection.calls]
        for migration in MIGRATIONS:
            for statement in migration.statements:
                self.assertIn(" ".join(statement.split()), executed_sql)
        inserts = [params for sql, params in connection.calls if sql.startswith("INSERT INTO schema_migrations")]
        self.assertEqual(inserts[0][0], migration_versions()[0])
        self.assertEqual(inserts[0][2], applied_at)

    def test_second_run_is_idempotent(self) -> None:
        connection = FakeConnection(migration_versions())
        applied = apply_migrations(connection, datetime.now(UTC))
        self.assertEqual(applied, [])
        self.assertFalse(
            any(sql.startswith("ALTER TABLE") for sql, _ in connection.calls),
            "Une migration déjà enregistrée ne doit pas être rejouée.",
        )


if __name__ == "__main__":
    unittest.main()
