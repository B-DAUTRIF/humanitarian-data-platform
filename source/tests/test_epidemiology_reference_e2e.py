from __future__ import annotations

import sys
import unittest
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.epidemiology import (  # noqa: E402
    EpidemiologyError,
    harmonize_observations,
    incidence_per_100k,
    merge_observations,
    observations_geojson,
    threshold_alert,
    weekly_series,
)


POPULATION = 2_000_000
RETRIEVED = "2026-03-31T12:00:00Z"


def observation(external_id: str, day: str, cases: int, source: str, *, lat: float, lon: float) -> dict:
    return {
        "external_id": external_id,
        "date": day,
        "location": "Mozambique",
        "cases": cases,
        "population": POPULATION,
        "source": source,
        "source_url": f"https://example.invalid/{source}/{external_id}",
        "retrieved_at": RETRIEVED,
        "latitude": lat,
        "longitude": lon,
    }


class EpidemiologyReferenceE2ETest(unittest.TestCase):
    def test_cholera_surveillance_round_trip(self) -> None:
        first_acquisition = [
            observation("who-001", "2026-03-02", 10, "who-gho", lat=-25.97, lon=32.58),
            observation("hapi-001", "2026-03-05", 15, "hdx-hapi", lat=-25.97, lon=32.58),
            observation("who-002", "2026-03-09", 80, "who-gho", lat=-15.12, lon=39.26),
        ]
        normalized = harmonize_observations(first_acquisition)
        self.assertEqual(len(normalized), 3)
        self.assertTrue(all(row["source_url"].startswith("https://") for row in normalized))
        self.assertTrue(all(row["retrieved_at"] == RETRIEVED for row in normalized))

        first_weeks = weekly_series(normalized)
        self.assertEqual(
            [(row["week_start"], row["cases"]) for row in first_weeks],
            [("2026-03-02", 25), ("2026-03-09", 80)],
        )
        self.assertAlmostEqual(first_weeks[0]["incidence_per_100k"], 1.25)
        self.assertAlmostEqual(first_weeks[1]["incidence_per_100k"], 4.0)
        self.assertEqual(threshold_alert(first_weeks, incidence_threshold=5.0), [])

        second_acquisition = [
            observation("who-002", "2026-03-09", 90, "who-gho", lat=-15.12, lon=39.26),
            observation("rw-001", "2026-03-12", 30, "reliefweb", lat=-15.12, lon=39.26),
        ]
        refreshed = merge_observations(normalized, second_acquisition)
        self.assertEqual(len(refreshed), 4, "same source/external_id must be updated, not duplicated")
        updated = next(row for row in refreshed if row["external_id"] == "who-002")
        self.assertEqual(updated["cases"], 90)

        weeks = weekly_series(refreshed)
        self.assertEqual(
            [(row["week_start"], row["cases"]) for row in weeks],
            [("2026-03-02", 25), ("2026-03-09", 120)],
        )
        self.assertAlmostEqual(weeks[1]["incidence_per_100k"], 6.0)
        self.assertEqual(weeks[1]["sources"], ["reliefweb", "who-gho"])

        alerts = threshold_alert(weeks, incidence_threshold=5.0)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["week_start"], "2026-03-09")
        self.assertEqual(alerts[0]["cases"], 120)
        self.assertAlmostEqual(alerts[0]["incidence_per_100k"], 6.0)
        self.assertEqual(alerts[0]["kind"], "epidemiology.incidence_threshold")

        geojson = observations_geojson(refreshed)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 4)
        self.assertEqual(
            {feature["properties"]["source"] for feature in geojson["features"]},
            {"who-gho", "hdx-hapi", "reliefweb"},
        )
        self.assertTrue(
            all(feature["properties"]["source_url"] for feature in geojson["features"]),
            "map export must preserve source provenance",
        )

    def test_incidence_formula_is_exact_for_reference_values(self) -> None:
        self.assertEqual(incidence_per_100k(120, 2_000_000), 6.0)
        self.assertEqual(incidence_per_100k(25, 2_000_000), 1.25)
        with self.assertRaises(EpidemiologyError):
            incidence_per_100k(1, 0)
        with self.assertRaises(EpidemiologyError):
            incidence_per_100k(-1, 1000)

    def test_harmonization_rejects_invalid_surveillance_records(self) -> None:
        invalid = observation("bad", "2026-03-03", -1, "who-gho", lat=0, lon=0)
        with self.assertRaises(EpidemiologyError):
            harmonize_observations([invalid])
        conflicting = [
            observation("a", "2026-03-02", 1, "who-gho", lat=0, lon=0),
            {**observation("b", "2026-03-03", 1, "hdx-hapi", lat=0, lon=0), "population": 1_900_000},
        ]
        with self.assertRaises(EpidemiologyError):
            weekly_series(conflicting)


if __name__ == "__main__":
    unittest.main()
