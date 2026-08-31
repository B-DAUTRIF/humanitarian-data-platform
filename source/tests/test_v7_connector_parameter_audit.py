from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.providers.reliefweb.api import _bounded_status as reliefweb_bounded_status
from app.providers.world_bank_health.api import WorldBankObservationRequest, _bounded_status as world_bank_bounded_status
from app.providers.world_bank_health.service import build_observation_request
from app.reliefweb_v2 import build_payload
from app.source_registry import connector_definition, request_preview, validate_values


class ConnectorParameterAuditTests(unittest.TestCase):
    def test_bounded_empty_never_claims_empty_valid(self) -> None:
        self.assertEqual(reliefweb_bounded_status([]), "partial")
        self.assertEqual(world_bank_bounded_status([]), "partial")
        self.assertEqual(reliefweb_bounded_status([{"id": "1"}]), "success")
        self.assertEqual(world_bank_bounded_status([{"id": "1"}]), "success")

    def test_world_bank_format_is_explicitly_json_only(self) -> None:
        payload = WorldBankObservationRequest(indicator="SP.POP.TOTL", format="json")
        self.assertEqual(payload.format, "json")
        with self.assertRaises(Exception):
            WorldBankObservationRequest(indicator="SP.POP.TOTL", format="xml")
        native = build_observation_request(country="RWA", indicator="SP.POP.TOTL")
        self.assertEqual(native["query_parameters"]["format"], "json")

    def test_reliefweb_parameter_independence(self) -> None:
        base = build_payload({"query": "cholera", "limit": 25, "offset": 0})
        changed = build_payload({"query": "cholera", "limit": 50, "offset": 0})
        self.assertEqual(changed["query"], base["query"])
        self.assertEqual(changed["offset"], base["offset"])
        self.assertEqual(changed["limit"], 50)

    def test_hdx_ckan_parameter_independence(self) -> None:
        base = connector_definition("hdx")["project_defaults"]
        p0 = request_preview("hdx", base)
        changed = deepcopy(base)
        changed["fq"] = "organization:ocha"
        p1 = request_preview("hdx", changed)
        self.assertEqual(p1["query_parameters"]["fq"], "organization:ocha")
        for name in ("q", "rows", "start", "sort"):
            self.assertEqual(p0["query_parameters"][name], p1["query_parameters"][name])

    def test_hapi_parameter_independence(self) -> None:
        base = connector_definition("hdx-hapi")["project_defaults"]
        p0 = request_preview("hdx-hapi", base)
        changed = deepcopy(base)
        changed["location_code"] = "RWA"
        p1 = request_preview("hdx-hapi", changed)
        self.assertEqual(p1["query_parameters"]["location_code"], "RWA")
        for name in ("limit", "offset", "admin_level", "output_format", "app_identifier"):
            self.assertEqual(p0["query_parameters"][name], p1["query_parameters"][name])

    def test_provider_schemas_reject_project_id_contamination(self) -> None:
        for source in ("hdx", "reliefweb", "world-bank-health", "hdx-hapi"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    validate_values(source, {"project_id": "rwanda"}, scope="project", partial=True)

    def test_date_from_does_not_mutate_date_to(self) -> None:
        values = connector_definition("world-bank-health")["project_defaults"]
        original_end = values["date_to"]
        changed = deepcopy(values)
        changed["date_from"] = "2020-01-01"
        self.assertEqual(changed["date_to"], original_end)

    def test_documented_hdx_contract_gaps_stay_visible(self) -> None:
        props = connector_definition("hdx")["project_schema"]["properties"]
        self.assertIn("fq", props)
        self.assertIn("sort", props)
        # These CKAN capabilities are documented but are not silently presented as qualified HDP fields.
        self.assertNotIn("facet.field", props)
        self.assertNotIn("fq_list", props)


if __name__ == "__main__":
    unittest.main()
