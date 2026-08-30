from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_provider_execution import execute_un_sdg_native, execute_world_bank_native  # noqa: E402

SETTINGS = {"timeout_seconds": 20, "connect_timeout_seconds": 5, "retry_count": 0, "backoff_seconds": 1, "user_agent": "HDP-test", "accept_language": "en"}


class SemanticProviderExecutionTest(unittest.TestCase):
    def test_world_bank_catalog_then_native_observation(self) -> None:
        route = {"parameters": {"query": "malaria", "result_limit": 10}, "native_parameters": {"country": "RWA", "date": "2020:2025", "indicator_search": "malaria"}}
        catalog = [{"page": 1}, [{"id": "SH.MLR.INCD.P3", "name": "Incidence of malaria", "unit": "per 1,000 population at risk"}]]
        observations = [{"page": 1}, [{"indicator": {"value": "Incidence of malaria"}, "country": {"value": "Rwanda"}, "countryiso3code": "RWA", "date": "2023", "value": 48.2}]]
        fake = AsyncMock(side_effect=[(catalog, "catalog-url"), (observations, "obs-url")])
        with patch("app.semantic_provider_execution._get_json", fake):
            _, items, request = asyncio.run(execute_world_bank_native(route, SETTINGS))
        self.assertEqual(items[0]["indicator_code"], "SH.MLR.INCD.P3")
        self.assertEqual(items[0]["geographic_scope"], "Rwanda")
        self.assertEqual(request["observation_requests"], ["obs-url"])

    def test_un_sdg_m49_series_resolution_then_observations(self) -> None:
        route = {"parameters": {"query": "malaria", "result_limit": 10}, "native_parameters": {"areaCode": 646, "timePeriodStart": 2020, "timePeriodEnd": 2025, "series_search": "malaria"}}
        catalog = {"goals": [{"series": [{"seriesCode": "SH_MLR_INCD", "seriesDescription": "Malaria incidence"}]}]}
        observations = {"data": [{"seriesCode": "SH_MLR_INCD", "geoAreaCode": 646, "geoAreaName": "Rwanda", "timePeriod": 2023, "value": 42.1, "units": "PER_1000"}]}
        fake = AsyncMock(side_effect=[(catalog, "catalog-url"), (observations, "obs-url")])
        with patch("app.semantic_provider_execution._get_json", fake):
            _, items, request = asyncio.run(execute_un_sdg_native(route, SETTINGS))
        self.assertEqual(items[0]["series_code"], "SH_MLR_INCD")
        self.assertEqual(items[0]["geographic_scope"], "Rwanda")
        self.assertEqual(request["observation_requests"], ["obs-url"])


if __name__ == "__main__":
    unittest.main()
