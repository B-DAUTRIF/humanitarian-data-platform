from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
import zipfile
from datetime import UTC, datetime
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.map_utils import export_bundle, load_geojson  # noqa: E402
from app.processing_recipes import (  # noqa: E402
    generate_python_script,
    generate_r_script,
    run_delimited_recipe,
)
from app.v6_rules import evaluate_rule  # noqa: E402


class EpidemiologyEndToEndTest(unittest.TestCase):
    """Deterministic epidemiology chain: surveillance table -> incidence -> map -> alert."""

    def test_cholera_mozambique_weekly_incidence_map_and_alert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "cholera_mozambique.csv"
            weekly = root / "weekly.csv"
            rates = root / "weekly_incidence.csv"

            raw.write_text(
                "week,district,cases,population,source,source_url,latitude,longitude\n"
                "2026-W10,Maputo,12,100000,who-gho,https://ghoapi.azureedge.net/api,-25.9692,32.5732\n"
                "2026-W10,Matola,8,100000,who-gho,https://ghoapi.azureedge.net/api,-25.9622,32.4589\n"
                "2026-W11,Maputo,30,100000,who-gho,https://ghoapi.azureedge.net/api,-25.9692,32.5732\n"
                "2026-W11,Matola,20,100000,who-gho,https://ghoapi.azureedge.net/api,-25.9622,32.4589\n",
                encoding="utf-8",
            )

            aggregate_recipe = {
                "steps": [
                    {
                        "operation": "aggregate",
                        "group_by": ["week", "source", "source_url"],
                        "metrics": [
                            {"column": "cases", "function": "sum", "output": "cases"},
                            {"column": "population", "function": "sum", "output": "population"},
                        ],
                    }
                ]
            }
            aggregate_report = run_delimited_recipe(raw, weekly, aggregate_recipe)
            self.assertEqual(aggregate_report["rows_read"], 4)
            self.assertEqual(aggregate_report["rows_written"], 2)

            incidence_recipe = {
                "steps": [
                    {
                        "operation": "derive_rate",
                        "numerator": "cases",
                        "denominator": "population",
                        "output": "incidence_per_100k",
                        "multiplier": 100000,
                    }
                ]
            }
            rate_report = run_delimited_recipe(weekly, rates, incidence_recipe)
            self.assertEqual(rate_report["rows_written"], 2)
            self.assertEqual(len(rate_report["output_sha256"]), 64)

            with rates.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            by_week = {row["week"]: row for row in rows}
            # W10: (12 + 8) / (100000 + 100000) * 100000 = 10.0
            self.assertAlmostEqual(float(by_week["2026-W10"]["incidence_per_100k"]), 10.0)
            # W11: (30 + 20) / (100000 + 100000) * 100000 = 25.0
            self.assertAlmostEqual(float(by_week["2026-W11"]["incidence_per_100k"]), 25.0)
            self.assertEqual(by_week["2026-W11"]["source"], "who-gho")
            self.assertTrue(by_week["2026-W11"]["source_url"].startswith("https://"))

            # Reproducible Python and R scripts are produced from the same validated rate recipe.
            python_script = generate_python_script(incidence_recipe)
            r_script = generate_r_script(incidence_recipe)
            self.assertIn("derive_rate", python_script)
            self.assertIn("incidence_per_100k", r_script)

            # Latest-week district points become a GeoJSON layer and an export bundle for R/QGIS.
            latest = [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [32.5732, -25.9692],
                    },
                    "properties": {
                        "district": "Maputo",
                        "week": "2026-W11",
                        "cases": 30,
                        "population": 100000,
                        "source": "who-gho",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [32.4589, -25.9622],
                    },
                    "properties": {
                        "district": "Matola",
                        "week": "2026-W11",
                        "cases": 20,
                        "population": 100000,
                        "source": "who-gho",
                    },
                },
            ]
            collection = {"type": "FeatureCollection", "features": latest}
            geojson = root / "cholera.geojson"
            geojson.write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(len(load_geojson(geojson)), 2)

            bundle = export_bundle(root / "cholera-map.zip", "Choléra Mozambique W11", collection)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                self.assertIn("import_R.R", names)
                self.assertIn("import_qgis.py", names)
                readme = archive.read("README.txt").decode("utf-8")
                self.assertIn("Humanitarian Data Platform 6.0.0", readme)
                self.assertNotIn("6.0.0-dev", readme)

            # Epidemiological threshold: alert at >=20 cases per 100,000 in the latest week.
            rule = {
                "type": "group",
                "operator": "AND",
                "children": [
                    {"type": "condition", "field": "disease", "op": "contains", "value": "cholera"},
                    {"type": "condition", "field": "location", "op": "eq", "value": "Mozambique"},
                    {"type": "condition", "field": "incidence_per_100k", "op": "gte", "value": 20},
                ],
            }
            event = {
                "id": "cholera-moz-2026-W11",
                "disease": "cholera",
                "location": "Mozambique",
                "incidence_per_100k": float(by_week["2026-W11"]["incidence_per_100k"]),
                "occurred_at": "2026-03-15T12:00:00Z",
                "provenance": {
                    "source": by_week["2026-W11"]["source"],
                    "source_url": by_week["2026-W11"]["source_url"],
                    "output_sha256": rate_report["output_sha256"],
                },
            }
            result = evaluate_rule(
                rule,
                event,
                [event],
                now=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
            )
            self.assertTrue(result["matched"])
            self.assertEqual(result["events_examined"], 1)
            self.assertEqual(len(result["rule_sha256"]), 64)

            below_threshold = {**event, "incidence_per_100k": 10.0}
            self.assertFalse(
                evaluate_rule(
                    rule,
                    below_threshold,
                    [below_threshold],
                    now=datetime(2026, 3, 15, 12, 0, tzinfo=UTC),
                )["matched"]
            )


if __name__ == "__main__":
    unittest.main()
