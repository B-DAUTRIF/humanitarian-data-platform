from __future__ import annotations

import sys
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.providers.base.contracts import ConfigVisibility, resolve_provider_configuration
from app.providers.reliefweb.descriptor import RELIEFWEB_DESCRIPTOR
from app.providers.reliefweb.service import normalize_items


class ProviderReliefWebArchitectureTests(unittest.TestCase):
    def test_descriptor_has_all_documented_content_types(self):
        self.assertEqual(len(RELIEFWEB_DESCRIPTOR.content_types), 9)
        self.assertIn("reports", RELIEFWEB_DESCRIPTOR.content_types)
        self.assertIn("references", RELIEFWEB_DESCRIPTOR.content_types)

    def test_appname_is_public_and_project_overrides_global(self):
        app = next(x for x in RELIEFWEB_DESCRIPTOR.configuration if x.name == "appname")
        self.assertEqual(app.visibility, ConfigVisibility.PUBLIC)
        effective = resolve_provider_configuration(RELIEFWEB_DESCRIPTOR, global_settings={"appname":"global"}, project_settings={"appname":"project"})
        self.assertEqual(effective["appname"]["value"], "project")
        self.assertEqual(effective["appname"]["origin"], "project")

    def test_default_appname(self):
        effective = resolve_provider_configuration(RELIEFWEB_DESCRIPTOR)
        self.assertEqual(effective["appname"]["value"], "HDP_plateforme")
        self.assertEqual(effective["appname"]["origin"], "default")

    def test_normalization_preserves_native(self):
        raw = {"data":[{"id":123,"href":"https://api.reliefweb.int/v2/reports/123","score":2.5,"fields":{"title":"T","date":{"created":"2026-01-01T00:00:00+00:00"}}}]}
        item = normalize_items(raw, "reports")[0]
        self.assertEqual(item["reliefweb_id"], 123)
        self.assertEqual(item["content_type"], "reports")
        self.assertEqual(item["_native"]["id"], 123)

    def test_limits_are_descriptor_metadata(self):
        self.assertEqual(RELIEFWEB_DESCRIPTOR.runtime_limits["max_page_size"], 1000)
        self.assertEqual(RELIEFWEB_DESCRIPTOR.runtime_limits["documented_daily_request_quota"], 1000)

if __name__ == "__main__": unittest.main()
