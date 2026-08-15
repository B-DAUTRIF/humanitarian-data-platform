from __future__ import annotations

import unicodedata
from datetime import UTC, date, datetime
from typing import Any, Iterable


def normalized_text(value: Any) -> str:
    """Return a case- and accent-insensitive representation for catalog filters."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in text if not unicodedata.combining(character)).casefold()


def parse_catalog_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC).date() if value.tzinfo else value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(candidate[:10])
        except ValueError:
            return None


def validate_common_criteria(
    date_from: str = "",
    date_to: str = "",
    location: str = "",
) -> dict[str, str]:
    start = date.fromisoformat(date_from) if date_from else None
    end = date.fromisoformat(date_to) if date_to else None
    if start and end and start > end:
        raise ValueError("date_from doit être antérieure ou égale à date_to")
    cleaned_location = location.strip()
    if len(cleaned_location) > 160:
        raise ValueError("location est trop long")
    return {
        "date_from": start.isoformat() if start else "",
        "date_to": end.isoformat() if end else "",
        "location": cleaned_location,
    }


def filter_catalog_items(
    items: Iterable[dict[str, Any]],
    *,
    date_from: str = "",
    date_to: str = "",
    location: str = "",
) -> list[dict[str, Any]]:
    criteria = validate_common_criteria(date_from, date_to, location)
    start = date.fromisoformat(criteria["date_from"]) if criteria["date_from"] else None
    end = date.fromisoformat(criteria["date_to"]) if criteria["date_to"] else None
    location_query = normalized_text(criteria["location"])
    filtered: list[dict[str, Any]] = []
    for item in items:
        item_date = parse_catalog_date(item.get("date"))
        if start and (item_date is None or item_date < start):
            continue
        if end and (item_date is None or item_date > end):
            continue
        if location_query:
            haystack = normalized_text(
                " ".join(
                    str(item.get(key) or "")
                    for key in ("geographic_scope", "location", "country", "title")
                )
            )
            if location_query not in haystack:
                continue
        filtered.append(item)
    return filtered


def unified_federated_items(
    source_results: Iterable[tuple[str, Iterable[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    unified = [
        {**item, "connector_id": source_id}
        for source_id, items in source_results
        for item in items
    ]
    unified.sort(
        key=lambda item: (
            parse_catalog_date(item.get("date")) or date.min,
            normalized_text(item.get("title")),
        ),
        reverse=True,
    )
    return unified
