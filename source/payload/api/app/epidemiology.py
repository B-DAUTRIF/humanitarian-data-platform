from __future__ import annotations

"""Pure epidemiological helpers used by HDP V6 surveillance workflows.

The functions in this module deliberately avoid network and database side effects. They
operate on normalized dictionaries so the same calculations can be reused by API jobs,
notebooks and deterministic acceptance tests.
"""

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterable


class EpidemiologyError(ValueError):
    """Raised when an epidemiological observation is invalid."""


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as exc:
        raise EpidemiologyError(f"Invalid observation date: {value!r}") from exc


def harmonize_observations(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate and normalize surveillance observations without losing provenance."""
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(records):
        observation_date = _as_date(raw.get("date"))
        try:
            cases = int(raw.get("cases"))
            population = int(raw.get("population"))
        except (TypeError, ValueError) as exc:
            raise EpidemiologyError(f"Observation {index}: cases/population must be integers") from exc
        if cases < 0:
            raise EpidemiologyError(f"Observation {index}: cases cannot be negative")
        if population <= 0:
            raise EpidemiologyError(f"Observation {index}: population must be positive")
        location = str(raw.get("location") or "").strip()
        source = str(raw.get("source") or "").strip()
        external_id = str(raw.get("external_id") or "").strip()
        if not location or not source or not external_id:
            raise EpidemiologyError(f"Observation {index}: location/source/external_id are required")
        row = {
            "external_id": external_id,
            "date": observation_date.isoformat(),
            "location": location,
            "cases": cases,
            "population": population,
            "source": source,
            "source_url": str(raw.get("source_url") or ""),
            "retrieved_at": str(raw.get("retrieved_at") or ""),
        }
        for name in ("latitude", "longitude"):
            value = raw.get(name)
            row[name] = None if value is None else float(value)
        normalized.append(row)
    return normalized


def merge_observations(
    previous: Iterable[dict[str, Any]], new: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Idempotently refresh observations, replacing an existing source/external ID."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for row in harmonize_observations(previous):
        merged[(row["source"], row["external_id"])] = row
    for row in harmonize_observations(new):
        merged[(row["source"], row["external_id"])] = row
    return sorted(merged.values(), key=lambda row: (row["date"], row["source"], row["external_id"]))


def weekly_series(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate cases by ISO-week Monday and location, preserving source lineage."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    sources: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in harmonize_observations(records):
        moment = _as_date(row["date"])
        monday = moment - timedelta(days=moment.weekday())
        key = (monday.isoformat(), row["location"])
        if key not in grouped:
            grouped[key] = {
                "week_start": monday.isoformat(),
                "location": row["location"],
                "cases": 0,
                "population": row["population"],
            }
        if grouped[key]["population"] != row["population"]:
            raise EpidemiologyError(
                f"Conflicting population denominators for {row['location']} / {monday.isoformat()}"
            )
        grouped[key]["cases"] += row["cases"]
        sources[key].add(row["source"])
    result = []
    for key in sorted(grouped):
        row = dict(grouped[key])
        row["incidence_per_100k"] = incidence_per_100k(row["cases"], row["population"])
        row["sources"] = sorted(sources[key])
        result.append(row)
    return result


def incidence_per_100k(cases: int, population: int) -> float:
    """Return incidence per 100,000 inhabitants with strict denominator validation."""
    if int(cases) < 0:
        raise EpidemiologyError("cases cannot be negative")
    if int(population) <= 0:
        raise EpidemiologyError("population must be positive")
    return int(cases) * 100_000.0 / int(population)


def threshold_alert(
    weekly_rows: Iterable[dict[str, Any]], *, incidence_threshold: float
) -> list[dict[str, Any]]:
    """Create deterministic surveillance signals when weekly incidence crosses a threshold."""
    if incidence_threshold < 0:
        raise EpidemiologyError("incidence threshold cannot be negative")
    alerts = []
    for row in weekly_rows:
        incidence = float(row["incidence_per_100k"])
        if incidence > incidence_threshold:
            alerts.append(
                {
                    "kind": "epidemiology.incidence_threshold",
                    "week_start": row["week_start"],
                    "location": row["location"],
                    "cases": int(row["cases"]),
                    "population": int(row["population"]),
                    "incidence_per_100k": incidence,
                    "threshold": float(incidence_threshold),
                    "sources": list(row.get("sources") or []),
                }
            )
    return alerts


def observations_geojson(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Export geocoded observations as a valid GeoJSON FeatureCollection."""
    features = []
    for row in harmonize_observations(records):
        if row["longitude"] is None or row["latitude"] is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]],
                },
                "properties": {
                    "external_id": row["external_id"],
                    "date": row["date"],
                    "location": row["location"],
                    "cases": row["cases"],
                    "population": row["population"],
                    "source": row["source"],
                    "source_url": row["source_url"],
                    "retrieved_at": row["retrieved_at"],
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}
