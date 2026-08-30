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
    OFFICIAL_COD_SERIES,
    geodata_profile_changed,
    github_repository_endpoint,
    m49_country_entities,
    m49_scope,
    official_cod_metadata,
    select_geodata_resources,
    select_official_cod_datasets,
    un_m49_catalog,
    validate_hdx_dataset_id,
    validate_m49_code,
    validate_official_cod_policy,
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
    def test_m49_catalog_starts_with_world_and_contains_only_known_entities(self) -> None:
        catalog = un_m49_catalog()
        self.assertEqual(catalog[0]["code"], "001")
        self.assertEqual(catalog[0]["type_label"], "Monde")
        self.assertGreater(len(catalog), 270)

    def test_m49_scope_expands_to_descendant_countries(self) -> None:
        africa = m49_country_entities("002")
        self.assertGreater(len(africa), 50)
        self.assertTrue(any(item.get("iso3166") == "MLI" for item in africa))
        self.assertFalse(any(item.get("iso3166") == "FRA" for item in africa))
        self.assertEqual(m49_scope("466")["country_count"], 1)

    def test_m49_validation_rejects_unknown_code(self) -> None:
        self.assertEqual(validate_m49_code(" 001 "), "001")
        with self.assertRaises(ValueError):
            validate_m49_code("999")

    def test_geodata_profile_change_detects_algeria_to_sudan(self) -> None:
        current = {
            "m49_scope_code": "012",
            "official_policy": "enhanced_preferred",
            "preferred_format": "geojson",
        }
        self.assertTrue(
            geodata_profile_changed(current, "729", "enhanced_preferred", "geojson")
        )
        self.assertFalse(
            geodata_profile_changed(current, "012", "enhanced_preferred", "geojson")
        )

    def test_official_policy_validation(self) -> None:
        self.assertEqual(validate_official_cod_policy("enhanced_only"), "enhanced_only")
        with self.assertRaises(ValueError):
            validate_official_cod_policy("any_hdx_dataset")

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

    @staticmethod
    def cod_dataset(iso3: str, cod_level: str, modified: str) -> dict:
        return {
            "id": f"id-{iso3}-{cod_level}",
            "name": f"cod-ab-{iso3.lower()}-{cod_level}",
            "title": f"{iso3} - Subnational Administrative Boundaries",
            "dataseries_name": OFFICIAL_COD_SERIES,
            "cod_level": cod_level,
            "groups": [{"name": iso3.lower()}],
            "metadata_modified": modified,
            "organization": {"title": "OCHA Field Information Services"},
            "license_id": "cc-by-igo",
            "resources": [],
        }

    def test_official_cod_metadata_requires_official_series_and_m49_iso3(self) -> None:
        dataset = self.cod_dataset("MLI", "cod-enhanced", "2026-08-01T12:00:00")
        self.assertEqual(official_cod_metadata(dataset)["m49_code"], "466")
        dataset["dataseries_name"] = "Community boundaries"
        self.assertIsNone(official_cod_metadata(dataset))

    def test_official_cod_metadata_accepts_canonical_hdx_slug_without_returned_series(self) -> None:
        dataset = self.cod_dataset("SDN", "cod-enhanced", "2026-06-24T09:15:51")
        dataset["name"] = "cod-ab-sdn"
        dataset.pop("dataseries_name")
        metadata = official_cod_metadata(dataset)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["m49_code"], "729")
        self.assertEqual(metadata["dataset_id"], "cod-ab-sdn")

    def test_missing_series_requires_exact_canonical_hdx_slug(self) -> None:
        dataset = self.cod_dataset("DZA", "cod-enhanced", "2026-06-24T09:15:51")
        dataset["name"] = "community-cod-ab-dza-copy"
        dataset.pop("dataseries_name")
        self.assertIsNone(official_cod_metadata(dataset))

    def test_official_cod_metadata_rejects_non_cod_level(self) -> None:
        dataset = self.cod_dataset("MLI", "unreviewed", "2026-08-01T12:00:00")
        self.assertIsNone(official_cod_metadata(dataset))

    def test_enhanced_preferred_selects_enhanced_dataset(self) -> None:
        datasets = [
            self.cod_dataset("MLI", "cod-standard", "2026-08-02T12:00:00"),
            self.cod_dataset("MLI", "cod-enhanced", "2026-08-01T12:00:00"),
        ]
        selected, missing = select_official_cod_datasets(datasets, "466", "enhanced_preferred")
        self.assertFalse(missing)
        self.assertEqual(selected[0]["_hdp_official"]["cod_level"], "cod-enhanced")

    def test_enhanced_only_does_not_fall_back_to_standard(self) -> None:
        datasets = [self.cod_dataset("MLI", "cod-standard", "2026-08-02T12:00:00")]
        selected, missing = select_official_cod_datasets(datasets, "466", "enhanced_only")
        self.assertFalse(selected)
        self.assertEqual(missing[0]["iso3166"], "MLI")


if __name__ == "__main__":
    unittest.main()
