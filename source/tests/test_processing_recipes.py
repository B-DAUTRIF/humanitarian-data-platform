from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path


API_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(API_ROOT))

from app.processing_recipes import (  # noqa: E402
    RecipeError,
    generate_python_script,
    generate_r_script,
    operation_catalog,
    run_delimited_recipe,
    validate_recipe,
)


class ProcessingRecipeTest(unittest.TestCase):
    def test_recipe_validation_is_strict_and_versioned(self) -> None:
        recipe = validate_recipe(
            {
                "steps": [
                    {"operation": "filter", "column": "country", "operator": "eq", "value": "MLI"},
                    {"operation": "derive_rate", "numerator": "cases", "denominator": "population", "output": "incidence", "multiplier": 100000},
                ]
            }
        )
        self.assertEqual(recipe["version"], "4.0.0")
        self.assertEqual(recipe["steps"][1]["multiplier"], 100000.0)
        with self.assertRaises(RecipeError):
            validate_recipe({"steps": [{"operation": "shell", "command": "rm"}]})
        with self.assertRaises(RecipeError):
            validate_recipe({"unknown": True, "steps": [{"operation": "select", "columns": ["a"]}]})

    def test_streaming_filter_rate_and_deduplication(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "cases.csv", root / "derived.csv"
            source.write_text(
                "country,cases,population\nMLI,10,1000\nSEN,7,1000\nMLI,10,1000\n",
                encoding="utf-8",
            )
            report = run_delimited_recipe(
                source,
                output,
                {
                    "steps": [
                        {"operation": "filter", "column": "country", "operator": "eq", "value": "MLI"},
                        {"operation": "drop_duplicates", "columns": ["country", "cases", "population"]},
                        {"operation": "derive_rate", "numerator": "cases", "denominator": "population", "output": "incidence", "multiplier": 100000},
                    ]
                },
            )
            with output.open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows, [{"country": "MLI", "cases": "10", "population": "1000", "incidence": "1000"}])
            self.assertEqual(report["rows_read"], 3)
            self.assertEqual(report["rows_filtered"], 1)
            self.assertEqual(report["rows_duplicated"], 1)
            self.assertEqual(len(report["output_sha256"]), 64)

    def test_bounded_aggregation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "events.tsv", root / "summary.csv"
            source.write_text("area\tvalue\nA\t2\nA\t4\nB\t3\n", encoding="utf-8")
            report = run_delimited_recipe(
                source,
                output,
                {
                    "steps": [
                        {
                            "operation": "aggregate",
                            "group_by": ["area"],
                            "metrics": [
                                {"column": "*", "function": "count", "output": "records"},
                                {"column": "value", "function": "mean", "output": "mean_value"},
                            ],
                        }
                    ]
                },
            )
            self.assertEqual(report["rows_written"], 2)
            self.assertIn("A,2,3", output.read_text(encoding="utf-8"))

    def test_scripts_and_catalog_explain_reproducibility_boundary(self) -> None:
        recipe = {"steps": [{"operation": "select", "columns": ["iso3", "value"]}]}
        self.assertIn("run_delimited_recipe", generate_python_script(recipe))
        self.assertIn("write.csv", generate_r_script(recipe))
        catalog = operation_catalog()
        self.assertIn("derive_rate", catalog["operations"])
        self.assertIn("aggregate", catalog["bounded_state"])


if __name__ == "__main__":
    unittest.main()
