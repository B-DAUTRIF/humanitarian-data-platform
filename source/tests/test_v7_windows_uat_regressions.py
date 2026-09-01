from __future__ import annotations

import unittest


class WindowsUATRegressionTests(unittest.TestCase):
    def test_reliefweb_never_invents_unapproved_default_appname(self) -> None:
        from app.reliefweb_v2 import resolve_appname

        effective = resolve_appname({}, {})
        self.assertEqual(effective.value, "")
        self.assertEqual(effective.origin, "missing")

    def test_reliefweb_prefers_project_then_global_appname(self) -> None:
        from app.reliefweb_v2 import resolve_appname

        self.assertEqual(resolve_appname({"appname": "project-approved"}, {"appname": "global-approved"}).value, "project-approved")
        self.assertEqual(resolve_appname({}, {"appname": "global-approved"}).value, "global-approved")

    def test_dhs_duplicate_rows_with_same_provider_code_are_not_ambiguous(self) -> None:
        from app.providers.dhs.service import DHSService

        rows = [
            {"ISO3_countryCode": "RWA", "DHS_countryCode": "RW", "CountryName": "Rwanda"},
            {"ISO3_countryCode": "rwa", "DHS_countryCode": "RW", "CountryName": "Rwanda"},
        ]
        code, evidence = DHSService._verified_country_mapping(rows, "RWA")
        self.assertEqual(code, "RW")
        self.assertEqual(evidence["distinct_dhs_codes"], ["RW"])
        self.assertEqual(evidence["exact_match_count"], 2)

    def test_dhs_distinct_provider_codes_still_fail_closed(self) -> None:
        from app.providers.dhs.service import DHSService

        rows = [
            {"ISO3_countryCode": "RWA", "DHS_countryCode": "RW"},
            {"ISO3_countryCode": "RWA", "DHS_countryCode": "XX"},
        ]
        with self.assertRaisesRegex(ValueError, "not uniquely verified"):
            DHSService._verified_country_mapping(rows, "RWA")


if __name__ == "__main__":
    unittest.main()
