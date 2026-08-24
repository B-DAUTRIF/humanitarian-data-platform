from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.v6_backup import select_signal_backup_events  # noqa: E402


class _Rows:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.rows = rows

    def fetchall(self) -> list[tuple[str, str]]:
        return self.rows


class _Connection:
    def __init__(self, rows: list[tuple[str, str]]) -> None:
        self.rows = rows
        self.query = ""
        self.parameters: tuple[object, ...] = ()

    def execute(self, query: str, parameters: tuple[object, ...]) -> _Rows:
        self.query = query
        self.parameters = parameters
        return _Rows(self.rows)


class SignalBackupSelectionTest(unittest.TestCase):
    def test_global_selection_keeps_all_projects_and_uses_fixed_parameters(self) -> None:
        connection = _Connection([("signal-b", "project-b"), ("signal-a", "project-a")])
        selected, projects = select_signal_backup_events(
            connection,
            project_id=None,
            signal_ids=[],
            signal_from=None,
            signal_to=None,
        )
        self.assertEqual(selected, ["signal-b", "signal-a"])
        self.assertEqual(projects, ["project-a", "project-b"])
        self.assertIn("%s::uuid IS NULL", connection.query)
        self.assertNotIn("project-a", connection.query)
        self.assertEqual(connection.parameters, (None, None, False, [], None, None, None, None))

    def test_explicit_project_selection_is_bound_without_sql_interpolation(self) -> None:
        connection = _Connection([("signal-a", "project-a")])
        selected, projects = select_signal_backup_events(
            connection,
            project_id="project-a",
            signal_ids=["signal-a"],
            signal_from=None,
            signal_to=None,
        )
        self.assertEqual(selected, ["signal-a"])
        self.assertEqual(projects, ["project-a"])
        self.assertEqual(connection.parameters[:4], ("project-a", "project-a", True, ["signal-a"]))
        self.assertNotIn("signal-a", connection.query)

    def test_period_is_half_open(self) -> None:
        start = datetime(2026, 8, 1, tzinfo=UTC)
        end = datetime(2026, 8, 2, tzinfo=UTC)
        connection = _Connection([])
        select_signal_backup_events(
            connection,
            project_id=None,
            signal_ids=[],
            signal_from=start,
            signal_to=end,
        )
        self.assertIn("occurred_at>=%s", connection.query)
        self.assertIn("occurred_at<%s", connection.query)
        self.assertEqual(connection.parameters[4:], (start, start, end, end))


if __name__ == "__main__":
    unittest.main()
