from __future__ import annotations

import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.federated_search import (  # noqa: E402
    filter_catalog_items,
    normalized_text,
    parse_catalog_date,
    unified_federated_items,
    validate_common_criteria,
)


class FederatedSearchHelpersTest(unittest.TestCase):
    def test_text_filter_is_case_and_accent_insensitive(self) -> None:
        self.assertEqual(normalized_text("Côte d’Ivoire"), normalized_text("COTE D’IVOIRE"))

    def test_dates_and_location_are_inclusive(self) -> None:
        items = [
            {
                "id": "kept",
                "title": "Épidémie au Sénégal",
                "date": "2026-08-15T12:30:00Z",
                "geographic_scope": "Sénégal",
            },
            {
                "id": "too-old",
                "title": "Archive Sénégal",
                "date": "2026-08-01",
                "geographic_scope": "Sénégal",
            },
            {
                "id": "wrong-place",
                "title": "Épidémie",
                "date": "2026-08-15",
                "geographic_scope": "Mali",
            },
            {"id": "undated", "title": "Sénégal", "geographic_scope": "Sénégal"},
        ]
        filtered = filter_catalog_items(
            items,
            date_from="2026-08-15",
            date_to="2026-08-15",
            location="senegal",
        )
        self.assertEqual([item["id"] for item in filtered], ["kept"])

    def test_invalid_range_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "antérieure"):
            validate_common_criteria("2026-08-16", "2026-08-15", "")

    def test_unified_items_keep_connector_and_sort_recent_first(self) -> None:
        unified = unified_federated_items(
            [
                ("hdx", [{"id": "old", "title": "A", "date": "2025-01-01"}]),
                ("who-gho", [{"id": "new", "title": "B", "date": "2026-01-01"}]),
            ]
        )
        self.assertEqual([item["id"] for item in unified], ["new", "old"])
        self.assertEqual(unified[0]["connector_id"], "who-gho")
        self.assertEqual(parse_catalog_date("2026-01-01T01:02:03Z").isoformat(), "2026-01-01")


if __name__ == "__main__":
    unittest.main()
