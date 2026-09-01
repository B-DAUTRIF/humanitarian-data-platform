from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


class V7TraceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.old_data_dir = os.environ.get("DATA_DIR")
        os.environ["DATA_DIR"] = self.temp.name
        from app import v7_trace
        v7_trace.TRACE_ID.set("")

    def tearDown(self) -> None:
        if self.old_data_dir is None:
            os.environ.pop("DATA_DIR", None)
        else:
            os.environ["DATA_DIR"] = self.old_data_dir
        self.temp.cleanup()

    def test_redaction_hides_secrets_and_url_credentials(self) -> None:
        from app.v7_trace import redact
        value = redact({
            "token": "abc",
            "password": "def",
            "normal": "Rwanda",
            "url": "https://example.test/x?api_key=secret&country=RWA",
            "nested": {"Authorization": "Bearer private"},
        })
        self.assertEqual(value["token"], "***REDACTED***")
        self.assertEqual(value["password"], "***REDACTED***")
        self.assertEqual(value["normal"], "Rwanda")
        self.assertNotIn("secret", value["url"])
        self.assertIn("country=RWA", value["url"])
        self.assertEqual(value["nested"]["Authorization"], "***REDACTED***")

    def test_trace_event_writes_jsonl_with_trace_id(self) -> None:
        from app.v7_trace import trace_event
        first = trace_event("test.start", project_id="p1")
        second = trace_event("test.finish", status="success")
        self.assertEqual(first["trace_id"], second["trace_id"])
        files = list((Path(self.temp.name) / "logs" / "trace").glob("HDP_TRACE_*.jsonl"))
        self.assertEqual(len(files), 1)
        rows = [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()]
        self.assertEqual([row["event"] for row in rows], ["test.start", "test.finish"])
        self.assertEqual(rows[0]["project_id"], "p1")

    def test_export_snapshot_is_immutable_and_closed(self) -> None:
        from app.v7_trace import _create_export_snapshot, _trace_path, trace_event
        trace_event("before.export", value="A")
        source = _trace_path()
        snapshot = _create_export_snapshot()
        self.assertTrue(snapshot.exists())
        self.assertNotEqual(source, snapshot)
        frozen = snapshot.read_bytes()
        self.assertGreater(len(frozen), 0)
        trace_event("after.export", value="B")
        self.assertEqual(snapshot.read_bytes(), frozen)
        self.assertGreater(source.stat().st_size, len(frozen))
        with snapshot.open("rb") as handle:
            self.assertEqual(handle.read(), frozen)

    def test_export_response_has_stable_length_and_attachment_name(self) -> None:
        from app.v7_trace import trace_event, trace_export
        trace_event("download.test", status="ok")
        response = trace_export()
        path = Path(response.path)
        self.assertTrue(path.exists())
        self.assertEqual(int(response.headers["content-length"]), path.stat().st_size)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn("attachment", response.headers["content-disposition"].lower())
        self.assertIn("HDP_TRACE_EXPORT_", response.headers["content-disposition"])


if __name__ == "__main__":
    unittest.main()
