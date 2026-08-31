from __future__ import annotations

import unittest

from app.provider_semantic_adapters import translate
from app.providers.dhs.descriptor import DHS_DESCRIPTOR
from app.providers.dhs.service import DHSService
from app.providers.gdacs.descriptor import GDACS_DESCRIPTOR
from app.providers.gdacs.service import GDACSService
from app.providers.un_sdg.descriptor import UN_SDG_DESCRIPTOR
from app.providers.un_sdg.service import UNSDGService
from app.providers.unhcr.descriptor import UNHCR_DESCRIPTOR
from app.providers.unhcr.service import UNHCRService
from app.providers.unicef_sdmx.descriptor import UNICEF_SDMX_DESCRIPTOR
from app.providers.unicef_sdmx.service import UNICEFSDMXService
from app.providers.who_gho.descriptor import WHO_GHO_DESCRIPTOR
from app.providers.who_gho.service import WHOGHOService
from app.semantic_router import build_semantic_intent


SETTINGS = {
    "timeout_seconds": 10,
    "connect_timeout_seconds": 5,
    "retry_count": 0,
    "backoff_seconds": 0,
    "max_response_bytes": 1_000_000,
    "user_agent": "HDP-test",
    "accept_language": "en",
}


class SixProviderContractTests(unittest.TestCase):
    def test_descriptors_are_unique_and_documented(self):
        descriptors = [DHS_DESCRIPTOR, GDACS_DESCRIPTOR, UN_SDG_DESCRIPTOR, UNHCR_DESCRIPTOR, UNICEF_SDMX_DESCRIPTOR, WHO_GHO_DESCRIPTOR]
        self.assertEqual(len({d.provider_id for d in descriptors}), 6)
        for descriptor in descriptors:
            self.assertTrue(descriptor.operations)
            self.assertTrue(descriptor.evidence)
            self.assertTrue(descriptor.metadata.get("parameter_contracts") is not None)
            self.assertTrue(descriptor.metadata.get("scope_note"))

    def test_unknown_parameters_are_rejected(self):
        for service, operation in [
            (DHSService(SETTINGS), "list_indicators"),
            (GDACSService(SETTINGS), "search_events"),
            (UNSDGService(SETTINGS), "list_indicators"),
            (UNHCRService(SETTINGS), "population"),
            (UNICEFSDMXService(SETTINGS), "list_dataflows"),
            (WHOGHOService(SETTINGS), "list_indicators"),
        ]:
            with self.subTest(service=service.descriptor.provider_id):
                with self.assertRaises(ValueError):
                    service.validate_parameters(operation, {"project_id": "rwanda"})

    def test_gdacs_codelist_is_enforced(self):
        service = GDACSService(SETTINGS)
        valid = service.validate_parameters("search_events", {"eventlist": ["EQ", "FL"]})
        self.assertEqual(valid["eventlist"], ["EQ", "FL"])
        with self.assertRaises(ValueError):
            service.validate_parameters("search_events", {"eventlist": ["NOT_A_HAZARD"]})

    def test_dhs_request_never_substitutes_iso3_as_country_id(self):
        service = DHSService(SETTINGS)
        spec = service.build_request("indicator_data", service.validate_parameters("indicator_data", {"countryIds": ["RW"], "indicatorIds": ["X"]}))
        self.assertEqual(spec["query_parameters"]["countryIds"], "RW")
        intent = build_semantic_intent(query="malaria", location="Rwanda")
        route = translate("dhs", intent, result_limit=10)
        self.assertTrue(route["executable"])
        self.assertEqual(route["native_parameters"]["iso3_lookup"], "RWA")
        self.assertNotIn("countryIds", route["native_parameters"])

    def test_un_sdg_uses_m49_for_verified_geography(self):
        intent = build_semantic_intent(query="malaria", location="Rwanda", date_from="2020-01-01", date_to="2024-12-31")
        route = translate("un-sdg", intent, result_limit=10)
        self.assertEqual(route["native_parameters"]["areaCode"], 646)
        self.assertEqual(route["native_parameters"]["timePeriodStart"], 2020)
        self.assertEqual(route["native_parameters"]["timePeriodEnd"], 2024)

    def test_unhcr_keeps_origin_and_asylum_roles_distinct(self):
        intent = build_semantic_intent(query="refugees", location="Rwanda")
        route = translate("unhcr", intent, result_limit=10)
        self.assertEqual(route["native_parameters"]["iso3"], "RWA")
        self.assertEqual(route["native_parameters"]["country_roles"], ["origin", "asylum"])
        self.assertEqual(route["native_parameters"]["cf_type"], "ISO")

    def test_unicef_semantic_geography_does_not_guess_dsd_key(self):
        intent = build_semantic_intent(query="nutrition", location="Rwanda")
        route = translate("unicef-sdmx", intent, result_limit=10)
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")

    def test_who_semantic_observation_geography_is_explicitly_blocked(self):
        intent = build_semantic_intent(query="malaria", location="Rwanda")
        route = translate("who-gho", intent, result_limit=10)
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "unsupported")

    def test_gdacs_geography_is_not_invented(self):
        intent = build_semantic_intent(query="earthquake", location="Rwanda")
        route = translate("gdacs", intent, result_limit=10)
        self.assertFalse(route["executable"])
        self.assertEqual(route["criteria"]["geography"], "blocked_missing_mapping")

    def test_native_request_shapes(self):
        dhs = DHSService(SETTINGS).build_request("indicator_data", DHSService(SETTINGS).validate_parameters("indicator_data", {"countryIds":["RW"], "indicatorIds":["X"], "surveyYears":[2020,2021]}))
        self.assertIn("/rest/dhs/data", dhs["url"])
        self.assertEqual(dhs["query_parameters"]["surveyYears"], "2020,2021")
        gdacs = GDACSService(SETTINGS).build_request("search_events", GDACSService(SETTINGS).validate_parameters("search_events", {"eventlist":["EQ"], "alertlevel":["green"]}))
        self.assertEqual(gdacs["query_parameters"]["eventlist"], "EQ")
        sdg = UNSDGService(SETTINGS).build_request("series_data", UNSDGService(SETTINGS).validate_parameters("series_data", {"seriesCode":"SI_POV_DAY1", "areaCode":646}))
        self.assertEqual(sdg["query_parameters"]["areaCode"], 646)
        unhcr = UNHCRService(SETTINGS).build_request("population", UNHCRService(SETTINGS).validate_parameters("population", {"coo":"RWA", "cf_type":"ISO"}))
        self.assertEqual(unhcr["query_parameters"]["coo"], "RWA")
        unicef = UNICEFSDMXService(SETTINGS).build_request("get_data", UNICEFSDMXService(SETTINGS).validate_parameters("get_data", {"agency":"UNICEF", "dataflow":"TEST", "version":"latest", "data_query":"A.B+C"}))
        self.assertIn("/data/UNICEF,TEST,latest/A.B+C", unicef["url"])
        who = WHOGHOService(SETTINGS).build_request("list_indicators", WHOGHOService(SETTINGS).validate_parameters("list_indicators", {"filter":"contains(IndicatorName,'malaria')", "top":25}))
        self.assertIn("$filter", who["query_parameters"])
        self.assertEqual(who["query_parameters"]["$top"], 25)


if __name__ == "__main__":
    unittest.main()
