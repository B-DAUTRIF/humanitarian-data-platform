from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.providers.base.contracts import resolve_provider_configuration
from app.providers.world_bank_health.descriptor import FEATURES, WORLD_BANK_HEALTH_DESCRIPTOR
from app.providers.world_bank_health.service import build_catalog_request, build_observation_request, filter_indicator_catalog, normalize_observations, validate_country_code


class ProviderWorldBankHealthArchitectureTests(unittest.TestCase):
    def test_descriptor_provider_and_api(self):
        self.assertEqual(WORLD_BANK_HEALTH_DESCRIPTOR.provider_id, "world-bank-health")
        self.assertEqual(WORLD_BANK_HEALTH_DESCRIPTOR.api_version, "v2")
        self.assertEqual(len(FEATURES), 27)

    def test_source_2_default_and_project_override(self):
        effective = resolve_provider_configuration(WORLD_BANK_HEALTH_DESCRIPTOR)
        self.assertEqual(effective["source"]["value"], 2)
        override = resolve_provider_configuration(WORLD_BANK_HEALTH_DESCRIPTOR, project_settings={"source": 3})
        self.assertEqual(override["source"]["value"], 3)
        self.assertEqual(override["source"]["origin"], "project")

    def test_iso3_validation_and_aggregate_separation(self):
        self.assertEqual(validate_country_code("rwa"), "RWA")
        self.assertEqual(validate_country_code("RWA;KEN"), "RWA;KEN")
        with self.assertRaises(ValueError): validate_country_code("SSA")
        with self.assertRaises(ValueError): validate_country_code("WLD")
        with self.assertRaises(ValueError): validate_country_code("Rwanda")

    def test_native_request_date_and_pagination(self):
        spec = build_observation_request(country="RWA", indicator="SH.MLR.INCD.P3", date="2020:2025", page=2, per_page=100)
        self.assertIn("/country/RWA/indicator/SH.MLR.INCD.P3", spec["url"])
        self.assertEqual(spec["query_parameters"]["date"], "2020:2025")
        self.assertEqual(spec["query_parameters"]["page"], 2)
        self.assertEqual(spec["query_parameters"]["per_page"], 100)

    def test_native_advanced_parameters(self):
        spec = build_observation_request(country="RWA", indicator="SH.MLR.INCD.P3", mrv=5, mrnev=2, gapfill=True, frequency="Y", footnote=True)
        q = spec["query_parameters"]
        self.assertEqual(q["mrv"], 5); self.assertEqual(q["mrnev"], 2)
        self.assertEqual(q["gapfill"], "Y"); self.assertEqual(q["frequency"], "Y"); self.assertEqual(q["footnote"], "y")

    def test_multiple_country_and_indicator(self):
        spec = build_observation_request(country="RWA;KEN", indicator="SH.MLR.INCD.P3;SH.MLR.NETS.ZS")
        self.assertIn("RWA;KEN", spec["url"])
        self.assertIn("SH.MLR.INCD.P3;SH.MLR.NETS.ZS", spec["url"])

    def test_localized_language_prefix(self):
        spec = build_observation_request(country="RWA", indicator="SH.MLR.INCD.P3", language="fr")
        self.assertIn("api.worldbank.org/fr/v2", spec["url"])

    def test_auxiliary_catalog_request_contracts(self):
        self.assertIn("/source/2/indicator", build_catalog_request("indicators")["url"])
        self.assertTrue(build_catalog_request("countries")["url"].endswith("/v2/country"))
        self.assertTrue(build_catalog_request("topics")["url"].endswith("/v2/topic"))
        self.assertTrue(build_catalog_request("sources")["url"].endswith("/v2/source"))
        self.assertIn("/sources/2/search/health", build_catalog_request("metadata", identifier="2", query="health")["url"])
        metadata = build_catalog_request("indicator_metadata", identifier="SH.MLR.INCD.P3")
        self.assertIn("/indicator/SH.MLR.INCD.P3", metadata["url"])
        self.assertEqual(metadata["query_parameters"]["source"], 2)

    def test_indicator_keyword_discovery(self):
        rows = [
            {"id":"SH.MLR.INCD.P3", "name":"Incidence of malaria", "sourceNote":"Malaria cases"},
            {"id":"SP.POP.TOTL", "name":"Population, total", "sourceNote":"Population"},
        ]
        matches = filter_indicator_catalog(rows, "malaria")
        self.assertEqual([row["id"] for row in matches], ["SH.MLR.INCD.P3"])

    def test_normalization_preserves_native(self):
        payload = [{"page":1}, [{"indicator":{"id":"X","value":"Test"},"country":{"id":"RW","value":"Rwanda"},"countryiso3code":"RWA","date":"2024","value":12.3,"obs_status":"","decimal":1}]]
        item = normalize_observations(payload, "https://example.test")[0]
        self.assertEqual(item["country_iso3"], "RWA")
        self.assertEqual(item["indicator_code"], "X")
        self.assertEqual(item["value"], 12.3)
        self.assertEqual(item["_native"]["date"], "2024")

    def test_invalid_frequency_is_rejected(self):
        with self.assertRaises(ValueError): build_observation_request(country="RWA", indicator="X", frequency="D")

    def test_invalid_catalog_operation_is_rejected(self):
        with self.assertRaises(ValueError): build_catalog_request("unknown")
        with self.assertRaises(ValueError): build_catalog_request("metadata")
        with self.assertRaises(ValueError): build_catalog_request("metadata", identifier="2")

    def test_json_is_qualified_format(self):
        spec = build_observation_request(country="RWA", indicator="X")
        self.assertEqual(spec["query_parameters"]["format"], "json")
        self.assertEqual(spec["qualified_format"], "json")

if __name__ == "__main__": unittest.main()
