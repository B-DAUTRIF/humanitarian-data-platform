from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


ENGINE_VERSION = "4.0.0"
MAX_RECIPE_STEPS = 20
MAX_COLUMNS = 500
MAX_GROUPS = 100_000
MAX_DEDUPLICATION_KEYS = 2_000_000
COLUMN_PATTERN = re.compile(r"^[^\x00-\x1f]{1,200}$")
FILTER_OPERATORS = {"eq", "ne", "contains", "gt", "gte", "lt", "lte", "in", "is_empty", "not_empty"}
CAST_TYPES = {"string", "integer", "float", "date"}


class RecipeError(ValueError):
    pass


def operation_catalog() -> dict[str, Any]:
    return {
        "engine_version": ENGINE_VERSION,
        "input_formats": ["csv", "tsv"],
        "output_format": "csv",
        "streaming": ["select", "rename", "filter", "fill_missing", "recode", "cast", "derive_rate"],
        "bounded_state": ["drop_duplicates", "aggregate"],
        "operations": {
            "select": {"required": ["columns"]},
            "rename": {"required": ["mapping"]},
            "filter": {"required": ["column", "operator"], "operators": sorted(FILTER_OPERATORS)},
            "fill_missing": {"required": ["column", "value"]},
            "recode": {"required": ["column", "mapping"]},
            "cast": {"required": ["column", "type"], "types": sorted(CAST_TYPES)},
            "derive_rate": {"required": ["numerator", "denominator", "output", "multiplier"]},
            "drop_duplicates": {"required": ["columns"]},
            "aggregate": {"required": ["group_by", "metrics"], "must_be_last": True},
        },
        "templates": [
            {"id": "clean", "name": "Nettoyage tabulaire", "operations": ["fill_missing", "recode", "cast", "drop_duplicates"]},
            {"id": "incidence", "name": "Incidence pour une population", "operation": "derive_rate", "default_multiplier": 100000},
            {"id": "case_fatality", "name": "Létalité en pourcentage", "operation": "derive_rate", "default_multiplier": 100},
            {"id": "coverage", "name": "Couverture en pourcentage", "operation": "derive_rate", "default_multiplier": 100},
            {"id": "grouped_summary", "name": "Résumé par groupe", "operation": "aggregate"},
        ],
        "limits": {
            "steps": MAX_RECIPE_STEPS,
            "columns": MAX_COLUMNS,
            "groups": MAX_GROUPS,
            "deduplication_keys": MAX_DEDUPLICATION_KEYS,
        },
    }


def _column(value: Any, label: str = "colonne") -> str:
    name = str(value or "").strip()
    if not COLUMN_PATTERN.fullmatch(name):
        raise RecipeError(f"{label} invalide")
    return name


def _columns(value: Any, label: str = "colonnes") -> list[str]:
    if not isinstance(value, list) or not value or len(value) > MAX_COLUMNS:
        raise RecipeError(f"{label} doit contenir entre 1 et {MAX_COLUMNS} noms")
    result = [_column(item, label) for item in value]
    if len(result) != len(set(result)):
        raise RecipeError(f"{label} contient des doublons")
    return result


def validate_recipe(recipe: Any) -> dict[str, Any]:
    if not isinstance(recipe, dict):
        raise RecipeError("La recette doit être un objet JSON")
    unknown = set(recipe) - {"version", "steps"}
    if unknown:
        raise RecipeError(f"Champs de recette inconnus : {', '.join(sorted(unknown))}")
    steps = recipe.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_RECIPE_STEPS:
        raise RecipeError(f"La recette doit contenir entre 1 et {MAX_RECIPE_STEPS} étapes")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(steps):
        if not isinstance(raw, dict):
            raise RecipeError(f"Étape {index + 1} invalide")
        operation = str(raw.get("operation") or "").strip()
        if operation not in operation_catalog()["operations"]:
            raise RecipeError(f"Opération non autorisée à l’étape {index + 1}: {operation}")
        step: dict[str, Any] = {"operation": operation}
        if operation in {"select", "drop_duplicates"}:
            step["columns"] = _columns(raw.get("columns"))
        elif operation == "rename":
            mapping = raw.get("mapping")
            if not isinstance(mapping, dict) or not mapping or len(mapping) > MAX_COLUMNS:
                raise RecipeError("rename.mapping doit être un objet non vide et borné")
            step["mapping"] = {_column(key): _column(value) for key, value in mapping.items()}
        elif operation == "filter":
            step["column"] = _column(raw.get("column"))
            operator = str(raw.get("operator") or "")
            if operator not in FILTER_OPERATORS:
                raise RecipeError("Opérateur de filtre non autorisé")
            step["operator"] = operator
            value = raw.get("value", "")
            if operator == "in":
                if not isinstance(value, list) or len(value) > 1000:
                    raise RecipeError("Le filtre in exige une liste de 1000 valeurs au maximum")
                step["value"] = [str(item) for item in value]
            else:
                step["value"] = str(value)
        elif operation in {"fill_missing", "recode", "cast"}:
            step["column"] = _column(raw.get("column"))
            if operation == "fill_missing":
                step["value"] = str(raw.get("value", ""))
            elif operation == "recode":
                mapping = raw.get("mapping")
                if not isinstance(mapping, dict) or len(mapping) > 1000:
                    raise RecipeError("recode.mapping doit être un objet de 1000 valeurs au maximum")
                step["mapping"] = {str(key): str(value) for key, value in mapping.items()}
            else:
                target_type = str(raw.get("type") or "")
                if target_type not in CAST_TYPES:
                    raise RecipeError("Type de conversion non autorisé")
                step["type"] = target_type
        elif operation == "derive_rate":
            step.update(
                {
                    "numerator": _column(raw.get("numerator"), "numérateur"),
                    "denominator": _column(raw.get("denominator"), "dénominateur"),
                    "output": _column(raw.get("output"), "colonne de résultat"),
                }
            )
            multiplier = raw.get("multiplier", 1)
            if type(multiplier) not in {int, float} or not math.isfinite(float(multiplier)) or not 0 < float(multiplier) <= 1_000_000:
                raise RecipeError("Multiplicateur de taux invalide")
            step["multiplier"] = float(multiplier)
        elif operation == "aggregate":
            if index != len(steps) - 1:
                raise RecipeError("aggregate doit être la dernière étape")
            step["group_by"] = _columns(raw.get("group_by"), "clés de groupe")
            metrics = raw.get("metrics")
            if not isinstance(metrics, list) or not 1 <= len(metrics) <= 100:
                raise RecipeError("aggregate.metrics doit contenir entre 1 et 100 métriques")
            normalized_metrics: list[dict[str, str]] = []
            outputs: set[str] = set()
            for metric in metrics:
                if not isinstance(metric, dict):
                    raise RecipeError("Métrique d’agrégation invalide")
                function = str(metric.get("function") or "")
                if function not in {"count", "sum", "mean", "min", "max"}:
                    raise RecipeError("Fonction d’agrégation non autorisée")
                column = "*" if function == "count" and metric.get("column") in (None, "", "*") else _column(metric.get("column"))
                output = _column(metric.get("output"), "sortie de métrique")
                if output in outputs:
                    raise RecipeError("Deux métriques ne peuvent pas avoir la même sortie")
                outputs.add(output)
                normalized_metrics.append({"column": column, "function": function, "output": output})
            step["metrics"] = normalized_metrics
        normalized.append(step)
    return {"version": ENGINE_VERSION, "steps": normalized}


def _number(value: Any, *, column: str) -> float:
    text = str(value or "").strip().replace("\u00a0", "").replace(",", ".")
    if not text:
        raise RecipeError(f"Valeur numérique manquante dans {column}")
    try:
        number = float(text)
    except ValueError as exc:
        raise RecipeError(f"Valeur non numérique dans {column}: {text[:80]}") from exc
    if not math.isfinite(number):
        raise RecipeError(f"Valeur non finie dans {column}")
    return number


def _cast(value: str, target_type: str, column: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if target_type == "string":
        return text
    if target_type == "integer":
        number = _number(text, column=column)
        if not number.is_integer():
            raise RecipeError(f"Valeur non entière dans {column}: {text[:80]}")
        return str(int(number))
    if target_type == "float":
        return format(_number(text, column=column), ".15g")
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        except ValueError as exc:
            raise RecipeError(f"Date ISO invalide dans {column}: {text[:80]}") from exc


def _passes(value: str, operator: str, expected: Any) -> bool:
    if operator == "is_empty":
        return not value.strip()
    if operator == "not_empty":
        return bool(value.strip())
    if operator == "eq":
        return value == str(expected)
    if operator == "ne":
        return value != str(expected)
    if operator == "contains":
        return str(expected).casefold() in value.casefold()
    if operator == "in":
        return value in set(expected)
    left, right = _number(value, column="filtre"), _number(expected, column="filtre")
    return {"gt": left > right, "gte": left >= right, "lt": left < right, "lte": left <= right}[operator]


def _output_columns(input_columns: list[str], steps: list[dict[str, Any]]) -> list[str]:
    columns = list(input_columns)
    for step in steps:
        operation = step["operation"]
        if operation == "select":
            missing = set(step["columns"]) - set(columns)
            if missing:
                raise RecipeError(f"Colonnes absentes : {', '.join(sorted(missing))}")
            columns = list(step["columns"])
        elif operation == "rename":
            missing = set(step["mapping"]) - set(columns)
            if missing:
                raise RecipeError(f"Colonnes à renommer absentes : {', '.join(sorted(missing))}")
            columns = [step["mapping"].get(column, column) for column in columns]
            if len(columns) != len(set(columns)):
                raise RecipeError("Le renommage crée des colonnes en double")
        elif operation == "derive_rate":
            if step["output"] not in columns:
                columns.append(step["output"])
        elif operation == "aggregate":
            columns = list(step["group_by"]) + [metric["output"] for metric in step["metrics"]]
    return columns


def _transform_row(row: dict[str, str], steps: list[dict[str, Any]]) -> dict[str, str] | None:
    current = dict(row)
    for step in steps:
        operation = step["operation"]
        if operation == "aggregate" or operation == "drop_duplicates":
            continue
        if operation == "select":
            current = {column: current.get(column, "") for column in step["columns"]}
        elif operation == "rename":
            current = {step["mapping"].get(column, column): value for column, value in current.items()}
        elif operation == "filter":
            if step["column"] not in current:
                raise RecipeError(f"Colonne de filtre absente : {step['column']}")
            if not _passes(current.get(step["column"], ""), step["operator"], step["value"]):
                return None
        elif operation == "fill_missing":
            if not current.get(step["column"], "").strip():
                current[step["column"]] = step["value"]
        elif operation == "recode":
            value = current.get(step["column"], "")
            current[step["column"]] = step["mapping"].get(value, value)
        elif operation == "cast":
            current[step["column"]] = _cast(current.get(step["column"], ""), step["type"], step["column"])
        elif operation == "derive_rate":
            denominator = _number(current.get(step["denominator"], ""), column=step["denominator"])
            current[step["output"]] = "" if denominator == 0 else format(
                _number(current.get(step["numerator"], ""), column=step["numerator"])
                / denominator
                * step["multiplier"],
                ".15g",
            )
    return current


def profile_delimited(path: Path, *, delimiter: str, max_rows: int) -> dict[str, Any]:
    missing: defaultdict[str, int] = defaultdict(int)
    samples: defaultdict[str, set[str]] = defaultdict(set)
    row_count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        columns = list(reader.fieldnames or [])
        if not columns or len(columns) > MAX_COLUMNS:
            raise RecipeError("En-tête absent ou nombre de colonnes excessif")
        for row in reader:
            row_count += 1
            if row_count > max_rows:
                raise RecipeError(f"Le fichier dépasse la limite de {max_rows} lignes")
            for column in columns:
                value = str(row.get(column) or "").strip()
                if not value:
                    missing[column] += 1
                elif len(samples[column]) < 100:
                    samples[column].add(value[:200])
    return {
        "row_count": row_count,
        "columns": [
            {
                "name": column,
                "missing": missing[column],
                "distinct_sample": len(samples[column]),
                "sample_values": sorted(samples[column])[:5],
            }
            for column in columns
        ],
    }


def run_delimited_recipe(
    input_path: Path,
    output_path: Path,
    recipe: Any,
    *,
    delimiter: str | None = None,
    max_rows: int = 5_000_000,
) -> dict[str, Any]:
    normalized = validate_recipe(recipe)
    if delimiter is None:
        delimiter = "\t" if input_path.suffix.casefold() == ".tsv" else ","
    if delimiter not in {",", "\t", ";", "|"}:
        raise RecipeError("Séparateur non autorisé")
    profile = profile_delimited(input_path, delimiter=delimiter, max_rows=max_rows)
    input_columns = [column["name"] for column in profile["columns"]]
    output_columns = _output_columns(input_columns, normalized["steps"])
    aggregate_step = next((step for step in normalized["steps"] if step["operation"] == "aggregate"), None)
    deduplicate_steps = [step for step in normalized["steps"] if step["operation"] == "drop_duplicates"]
    seen: list[set[tuple[str, ...]]] = [set() for _ in deduplicate_steps]
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    rows_read = rows_written = rows_filtered = rows_duplicated = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".part")
    try:
        with input_path.open("r", encoding="utf-8-sig", newline="") as source, temporary.open(
            "x", encoding="utf-8", newline=""
        ) as destination:
            reader = csv.DictReader(source, delimiter=delimiter)
            writer = csv.DictWriter(destination, fieldnames=output_columns, extrasaction="ignore")
            writer.writeheader()
            for raw in reader:
                rows_read += 1
                if rows_read > max_rows:
                    raise RecipeError(f"Le fichier dépasse la limite de {max_rows} lignes")
                row = _transform_row({key: str(value or "") for key, value in raw.items()}, normalized["steps"])
                if row is None:
                    rows_filtered += 1
                    continue
                duplicate = False
                for state, step in zip(seen, deduplicate_steps):
                    key = tuple(row.get(column, "") for column in step["columns"])
                    if key in state:
                        duplicate = True
                        break
                    if len(state) >= MAX_DEDUPLICATION_KEYS:
                        raise RecipeError("Limite de clés de déduplication atteinte")
                    state.add(key)
                if duplicate:
                    rows_duplicated += 1
                    continue
                if aggregate_step:
                    group_key = tuple(row.get(column, "") for column in aggregate_step["group_by"])
                    if group_key not in groups:
                        if len(groups) >= MAX_GROUPS:
                            raise RecipeError("Limite de groupes atteinte")
                        groups[group_key] = [
                            {"count": 0, "sum": 0.0, "min": None, "max": None}
                            for _ in aggregate_step["metrics"]
                        ]
                    for state, metric in zip(groups[group_key], aggregate_step["metrics"]):
                        state["count"] += 1
                        if metric["function"] != "count":
                            number = _number(row.get(metric["column"], ""), column=metric["column"])
                            state["sum"] += number
                            state["min"] = number if state["min"] is None else min(state["min"], number)
                            state["max"] = number if state["max"] is None else max(state["max"], number)
                    continue
                writer.writerow({column: row.get(column, "") for column in output_columns})
                rows_written += 1
            if aggregate_step:
                for group_key, states in groups.items():
                    output = dict(zip(aggregate_step["group_by"], group_key))
                    for state, metric in zip(states, aggregate_step["metrics"]):
                        function = metric["function"]
                        value = state["count"] if function == "count" else state["sum"] if function == "sum" else state[function] if function in {"min", "max"} else state["sum"] / state["count"]
                        output[metric["output"]] = format(value, ".15g") if isinstance(value, float) else str(value)
                    writer.writerow(output)
                    rows_written += 1
        os.replace(temporary, output_path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    digest = hashlib.sha256()
    with output_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "engine_version": ENGINE_VERSION,
        "recipe": normalized,
        "input_profile": profile,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "rows_filtered": rows_filtered,
        "rows_duplicated": rows_duplicated,
        "output_columns": output_columns,
        "output_size_bytes": output_path.stat().st_size,
        "output_sha256": digest.hexdigest(),
    }


def generate_python_script(recipe: Any) -> str:
    normalized = validate_recipe(recipe)
    rendered = json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True)
    return f'''#!/usr/bin/env python3
"""Recette HDP {ENGINE_VERSION}. Utilisation: python script.py input.csv output.csv"""
from pathlib import Path
import json
import sys

# Cette recette versionnée est exécutable dans l’environnement source HDP.
from app.processing_recipes import run_delimited_recipe

RECIPE = json.loads(r\'''{rendered}\''')
if len(sys.argv) != 3:
    raise SystemExit("Utilisation: python script.py input.csv output.csv")
report = run_delimited_recipe(Path(sys.argv[1]), Path(sys.argv[2]), RECIPE)
print(json.dumps(report, ensure_ascii=False, indent=2))
'''


def generate_r_script(recipe: Any) -> str:
    normalized = validate_recipe(recipe)
    rendered = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return f'''#!/usr/bin/env Rscript
# Recette HDP {ENGINE_VERSION}. Reproduction dans un environnement R avec jsonlite.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Utilisation: Rscript script.R input.csv output.csv")
if (!requireNamespace("jsonlite", quietly = TRUE)) stop("Le paquet jsonlite est requis")
recipe <- jsonlite::fromJSON('{rendered.replace("'", "\\'")}', simplifyVector = FALSE)
data <- read.csv(args[[1]], check.names = FALSE, stringsAsFactors = FALSE)
for (step in recipe$steps) {{
  op <- step$operation
  if (op == "select") data <- data[unlist(step$columns)]
  else if (op == "rename") {{ for (old in names(step$mapping)) names(data)[names(data) == old] <- step$mapping[[old]] }}
  else if (op == "filter") {{
    value <- data[[step$column]]; expected <- step$value
    keep <- switch(step$operator, eq=value == expected, ne=value != expected,
      contains=grepl(expected, value, fixed=TRUE, ignore.case=TRUE),
      gt=as.numeric(value) > as.numeric(expected), gte=as.numeric(value) >= as.numeric(expected),
      lt=as.numeric(value) < as.numeric(expected), lte=as.numeric(value) <= as.numeric(expected),
      `in`=value %in% unlist(expected), is_empty=is.na(value) | trimws(value) == "",
      not_empty=!is.na(value) & trimws(value) != "")
    data <- data[keep, , drop=FALSE]
  }} else if (op == "fill_missing") {{ i <- is.na(data[[step$column]]) | trimws(data[[step$column]]) == ""; data[[step$column]][i] <- step$value }}
  else if (op == "recode") {{ for (old in names(step$mapping)) data[[step$column]][data[[step$column]] == old] <- step$mapping[[old]] }}
  else if (op == "cast") {{ data[[step$column]] <- switch(step$type, string=as.character(data[[step$column]]), integer=as.integer(data[[step$column]]), float=as.numeric(data[[step$column]]), date=as.Date(data[[step$column]])) }}
  else if (op == "derive_rate") data[[step$output]] <- as.numeric(data[[step$numerator]]) / as.numeric(data[[step$denominator]]) * step$multiplier
  else if (op == "drop_duplicates") data <- data[!duplicated(data[unlist(step$columns)]), , drop=FALSE]
  else stop(paste("Opération à reproduire avec le moteur HDP Python:", op))
}}
write.csv(data, args[[2]], row.names = FALSE, na = "")
'''
