from __future__ import annotations

import json
from typing import Any, Iterable
from urllib.parse import urlencode


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return " ".join(filter(None, (_text(item) for item in value.values())))
    if isinstance(value, list):
        return " ".join(filter(None, (_text(item) for item in value)))
    return str(value)


def _matches(query: str, *values: Any) -> bool:
    if not query.strip():
        return True
    haystack = " ".join(_text(value) for value in values).casefold()
    return all(token in haystack for token in query.casefold().split())


def _first(row: dict[str, Any], names: Iterable[str]) -> Any:
    for name in names:
        value = row.get(name)
        if value not in (None, "", []):
            return value
    return None


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "results", "result"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict):
            for nested_key in ("data", "items", "results"):
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    return [row for row in nested if isinstance(row, dict)]
    return []


def _description(row: dict[str, Any], names: tuple[str, ...]) -> str:
    parts: list[str] = []
    for name in names:
        value = row.get(name)
        if value in (None, "", []):
            continue
        label = name.replace("_", " ")
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        parts.append(f"{label}: {rendered}")
    return "; ".join(parts)[:2000]


def parse_hapi_rows(
    payload: Any,
    parameters: dict[str, Any],
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    endpoint = str(parameters.get("endpoint") or "HAPI")
    endpoint_label = endpoint.rsplit("/", 1)[-1].replace("-", " ").title()
    items: list[dict[str, Any]] = []
    for index, row in enumerate(_rows(payload)):
        location = _first(
            row,
            (
                "location_name",
                "admin2_name",
                "admin1_name",
                "provider_admin2_name",
                "provider_admin1_name",
                "operation_name",
                "location_code",
            ),
        )
        indicator = _first(
            row,
            ("indicator_name", "sector_name", "population_group", "category", "commodity_name"),
        )
        if not _matches(query, endpoint, location, indicator, row):
            continue
        row_id = _first(row, ("id", "record_id", "event_id", "resource_hdx_id"))
        date_value = _first(
            row,
            (
                "reference_period_end",
                "reference_period_start",
                "reporting_period_end",
                "reporting_period_start",
                "date",
                "year",
            ),
        )
        title_parts = [endpoint_label, _text(indicator), _text(location)]
        items.append(
            {
                "id": str(row_id or f"{endpoint}:{index}"),
                "title": " — ".join(filter(None, title_parts)),
                "description": _description(
                    row,
                    (
                        "value",
                        "population",
                        "population_status",
                        "sector_name",
                        "provider_name",
                        "source_name",
                    ),
                ),
                "date": str(date_value) if date_value is not None else None,
                "url": "https://hapi.humdata.org/",
                "source": "HDX Humanitarian API (HAPI)",
                "organization": _first(row, ("provider_name", "source_name", "organisation_name")),
                "geographic_scope": _text(location),
                "resources": [],
            }
        )
        if len(items) >= limit:
            break
    return items


def parse_unhcr_population(
    payload: Any,
    parameters: dict[str, Any],
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    resource_query: dict[str, Any] = {
        "limit": parameters.get("result_limit", limit),
        "page": parameters.get("page", 1),
        "yearFrom": parameters.get("year_from"),
        "yearTo": parameters.get("year_to"),
        "cf_type": "ISO",
    }
    if parameters.get("country_of_origin"):
        resource_query["coo"] = parameters["country_of_origin"]
    if parameters.get("country_of_asylum"):
        resource_query["coa"] = parameters["country_of_asylum"]
    resource_url = (
        "https://api.unhcr.org/population/v1/population/?"
        + urlencode({key: value for key, value in resource_query.items() if value not in (None, "")})
    )
    items: list[dict[str, Any]] = []
    for index, row in enumerate(_rows(payload)):
        origin = _first(row, ("coo_name", "origin_name", "coo", "origin"))
        asylum = _first(row, ("coa_name", "asylum_name", "coa", "asylum"))
        year = _first(row, ("year", "Year"))
        if not _matches(query, origin, asylum, year, row):
            continue
        row_id = _first(row, ("id", "population_id")) or f"{year}:{origin}:{asylum}:{index}"
        description = _description(
            row,
            (
                "refugees",
                "asylum_seekers",
                "returned_refugees",
                "idps",
                "returned_idps",
                "stateless",
                "ooc",
                "oip",
            ),
        )
        items.append(
            {
                "id": str(row_id),
                "title": f"Population déplacée {year or ''} — {_text(origin) or 'origine non précisée'} → {_text(asylum) or 'asile non précisé'}",
                "description": description,
                "date": f"{int(year):04d}-12-31" if str(year or "").isdigit() else None,
                "url": "https://www.unhcr.org/refugee-statistics/",
                "source": "UNHCR Refugee Statistics",
                "organization": "UNHCR",
                "geographic_scope": " → ".join(
                    filter(None, (_text(origin), _text(asylum)))
                ),
                "resources": [
                    {
                        "id": f"unhcr-population-{index}",
                        "name": "Extraction UNHCR (JSON)",
                        "url": resource_url,
                        "format": "json",
                    }
                ],
            }
        )
        if len(items) >= limit:
            break
    return items


def parse_gdacs_events(
    payload: Any,
    query: str,
    limit: int,
    *,
    resource_url: str,
) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("features"), list):
        features = payload["features"]
    else:
        features = _rows(payload)
    items: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else feature
        name = _first(properties, ("name", "eventname", "eventName", "description"))
        country = _first(properties, ("country", "countryname", "iso3", "countrycode"))
        event_type = _first(properties, ("eventtype", "eventType", "type"))
        alert = _first(properties, ("alertlevel", "alertLevel", "alertscore"))
        if not _matches(query, name, country, event_type, alert, properties):
            continue
        event_id = _first(properties, ("eventid", "eventId", "id")) or index
        episode_id = _first(properties, ("episodeid", "episodeId"))
        page_url = _first(properties, ("url", "reporturl", "link", "href"))
        if isinstance(page_url, dict):
            page_url = _first(page_url, ("report", "details", "url"))
        date_value = _first(properties, ("fromdate", "fromDate", "todate", "toDate", "date"))
        item_resources: list[dict[str, Any]] = []
        if index == 0:
            item_resources.append(
                {
                    "id": "gdacs-search-geojson",
                    "name": "Résultats GDACS (GeoJSON)",
                    "url": resource_url,
                    "format": "geojson",
                }
            )
        items.append(
            {
                "id": f"{event_type or 'event'}:{event_id}:{episode_id or ''}",
                "title": " — ".join(filter(None, (_text(event_type), _text(name), _text(country)))),
                "description": _description(
                    properties,
                    ("alertlevel", "severity", "population", "description", "fromdate", "todate"),
                ),
                "date": str(date_value) if date_value is not None else None,
                "url": str(page_url or "https://www.gdacs.org/"),
                "source": "GDACS",
                "organization": "European Commission / United Nations",
                "geographic_scope": _text(country),
                "resources": item_resources,
            }
        )
        if len(items) >= limit:
            break
    return items
