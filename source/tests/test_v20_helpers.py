from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.scheduler_utils import next_run_at, validate_interval  # noqa: E402
from app.security import (  # noqa: E402
    confined_path,
    resource_key,
    safe_filename,
    safe_query_fragment,
    sha256_file,
    validate_public_url,
)


class SecurityHelpersTest(unittest.TestCase):
    def test_safe_filename_removes_paths_and_windows_characters(self) -> None:
        self.assertEqual(safe_filename("../rapport:final?.csv"), "rapport_final_.csv")

    def test_safe_query_fragment_is_bounded(self) -> None:
        self.assertEqual(safe_query_fragment(" Choléra / Mozambique "), "Chol-ra-Mozambique")
        self.assertLessEqual(len(safe_query_fragment("x" * 200)), 50)

    def test_confined_path_rejects_escape(self) -> None:
        root = Path("/tmp/hdp-test-root")
        with self.assertRaises(ValueError):
            confined_path(root, "../../etc/passwd")

    def test_resource_key_is_stable(self) -> None:
        self.assertEqual(resource_key(None, "https://example.org/a.csv"), resource_key(None, "https://example.org/a.csv"))
        self.assertEqual(resource_key("abc", "https://example.org/one"), "abc")

    def test_sha256_file_streams_known_content(self) -> None:
        path = Path("/tmp/hdp-v20-hash-test.txt")
        path.write_bytes(b"HDP 2.0")
        try:
            self.assertEqual(sha256_file(path), "199ae50c94f80346463d33091acf2e51a2a8a6ec45ae7865746c773a12a9c56a")
        finally:
            path.unlink(missing_ok=True)

    @patch("app.security.socket.getaddrinfo")
    def test_private_destination_is_rejected(self, resolver) -> None:
        resolver.return_value = [(2, 1, 6, "", ("127.0.0.1", 443))]
        with self.assertRaisesRegex(ValueError, "non publique"):
            validate_public_url("https://example.org/file.csv")

    @patch("app.security.socket.getaddrinfo")
    def test_public_destination_is_accepted(self, resolver) -> None:
        resolver.return_value = [(2, 1, 6, "", ("93.184.216.34", 443))]
        self.assertEqual(validate_public_url("https://example.org/a"), "https://example.org/a")


class SchedulerHelpersTest(unittest.TestCase):
    def test_interval_bounds(self) -> None:
        with self.assertRaises(ValueError):
            validate_interval(14)
        self.assertEqual(validate_interval(15), 15)

    def test_next_run(self) -> None:
        now = datetime(2026, 8, 7, 10, 0, tzinfo=UTC)
        self.assertEqual(next_run_at(now, 60), datetime(2026, 8, 7, 11, 0, tzinfo=UTC))


if __name__ == "__main__":
    unittest.main()
