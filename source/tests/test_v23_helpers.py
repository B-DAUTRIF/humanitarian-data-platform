from __future__ import annotations

import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.scheduler_utils import next_run_at, validate_interval  # noqa: E402
from app.project_integrations import (  # noqa: E402
    GEO_SCALES,
    github_repository_endpoint,
    select_geodata_resources,
    validate_hdx_dataset_id,
    validate_repository_name,
)
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
        path = Path("/tmp/hdp-v23-hash-test.txt")
        path.write_bytes(b"HDP 2.3")
        try:
            self.assertEqual(sha256_file(path), "c0c791b2ed726bede5dd3fbee5859b827836305496c7916529c4703f04614553")
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


class ProjectIntegrationsTest(unittest.TestCase):
    def test_scale_catalog_is_ordered_from_terrain_to_world(self) -> None:
        self.assertEqual([item["id"] for item in GEO_SCALES], ["terrain", "local", "national", "regional", "world"])
        self.assertEqual([item["rank"] for item in GEO_SCALES], [1, 2, 3, 4, 5])

    def test_repository_name_validation(self) -> None:
        self.assertEqual(validate_repository_name(" crise-mali_2026 "), "crise-mali_2026")
        with self.assertRaises(ValueError):
            validate_repository_name("nom avec espaces")

    def test_repository_endpoint_selects_user_or_organization(self) -> None:
        self.assertEqual(github_repository_endpoint("", "octocat"), "https://api.github.com/user/repos")
        self.assertEqual(github_repository_endpoint("OctoCat", "octocat"), "https://api.github.com/user/repos")
        self.assertEqual(github_repository_endpoint("ocha", "octocat"), "https://api.github.com/orgs/ocha/repos")

    def test_hdx_dataset_id_validation(self) -> None:
        self.assertEqual(validate_hdx_dataset_id(" COD-AB-GLOBAL "), "cod-ab-global")
        with self.assertRaises(ValueError):
            validate_hdx_dataset_id("https://example.org/dataset")

    def test_geodata_resource_selection_uses_format_aliases(self) -> None:
        resources = [
            {"name": "Boundaries", "format": "GeoJSON", "url": "https://example.org/a.zip"},
            {"name": "File Geodatabase", "format": "ZIP", "url": "https://example.org/b.zip"},
            {"name": "Boundaries", "format": "SHP ZIP", "url": "https://example.org/d.zip"},
            {"name": "Table", "format": "CSV", "url": "https://example.org/c.csv"},
        ]
        self.assertEqual(len(select_geodata_resources(resources, "geojson")), 1)
        self.assertEqual(len(select_geodata_resources(resources, "geodatabase")), 1)
        self.assertEqual(len(select_geodata_resources(resources, "shapefile")), 1)


if __name__ == "__main__":
    unittest.main()
