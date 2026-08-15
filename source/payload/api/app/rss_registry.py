from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import urlencode

try:
    from defusedxml import ElementTree
except ModuleNotFoundError:  # The production image installs defusedxml; pure tests retain the explicit guards below.
    from xml.etree import ElementTree


MAX_RSS_BYTES = 2 * 1024 * 1024
MAX_RSS_ITEMS = 200

_REGISTRY: dict[str, dict[str, Any]] = {
    "reliefweb-reports": {
        "id": "reliefweb-reports",
        "name": "ReliefWeb — rapports et mises à jour",
        "organization": "OCHA / ReliefWeb",
        "base_url": "https://reliefweb.int/updates/rss.xml",
        "portal_url": "https://reliefweb.int/rss",
        "allowed_hosts": ["reliefweb.int", "www.reliefweb.int"],
        "verified_at": "2026-08-15",
    },
    "reliefweb-disasters": {
        "id": "reliefweb-disasters",
        "name": "ReliefWeb — catastrophes",
        "organization": "OCHA / ReliefWeb",
        "base_url": "https://reliefweb.int/disasters/rss.xml",
        "portal_url": "https://reliefweb.int/rss",
        "allowed_hosts": ["reliefweb.int", "www.reliefweb.int"],
        "verified_at": "2026-08-15",
    },
    "reliefweb-jobs": {
        "id": "reliefweb-jobs",
        "name": "ReliefWeb — emplois humanitaires",
        "organization": "OCHA / ReliefWeb",
        "base_url": "https://reliefweb.int/jobs/rss.xml",
        "portal_url": "https://reliefweb.int/rss",
        "allowed_hosts": ["reliefweb.int", "www.reliefweb.int"],
        "verified_at": "2026-08-15",
    },
    "reliefweb-training": {
        "id": "reliefweb-training",
        "name": "ReliefWeb — formations",
        "organization": "OCHA / ReliefWeb",
        "base_url": "https://reliefweb.int/training/rss.xml",
        "portal_url": "https://reliefweb.int/rss",
        "allowed_hosts": ["reliefweb.int", "www.reliefweb.int"],
        "verified_at": "2026-08-15",
    },
}


def rss_catalog() -> list[dict[str, Any]]:
    return [deepcopy(_REGISTRY[key]) for key in sorted(_REGISTRY)]


def rss_definition(registry_id: str) -> dict[str, Any]:
    try:
        return deepcopy(_REGISTRY[registry_id])
    except KeyError as exc:
        raise ValueError("Flux RSS absent du registre officiel vérifié") from exc


def build_rss_url(registry_id: str, query: str = "", language: str = "en") -> str:
    definition = rss_definition(registry_id)
    if language not in {"en", "fr", "es"}:
        raise ValueError("La langue RSS doit être en, fr ou es")
    cleaned = " ".join(str(query).split())[:200]
    parameters: dict[str, str] = {"lang": language}
    if cleaned:
        parameters["search"] = cleaned
    return f"{definition['base_url']}?{urlencode(parameters)}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _child_text(node: Any, names: set[str]) -> str:
    for child in list(node):
        if _local_name(str(child.tag)) in names:
            if child.text:
                return str(child.text).strip()
            href = child.attrib.get("href")
            if href:
                return str(href).strip()
    return ""


def _clean_summary(value: str) -> str:
    without_tags = re.sub(r"<[^>]{0,500}>", " ", value)
    return " ".join(unescape(without_tags).split())[:4000]


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_rss(payload: bytes, *, limit: int = MAX_RSS_ITEMS) -> list[dict[str, Any]]:
    if len(payload) > MAX_RSS_BYTES:
        raise ValueError("Le flux RSS dépasse la limite de 2 Mio")
    upper = payload[:4096].upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("Les DTD et entités XML sont interdites")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("Le flux RSS/XML est invalide") from exc
    items = [node for node in root.iter() if _local_name(str(node.tag)) in {"item", "entry"}]
    normalized: list[dict[str, Any]] = []
    for node in items[: max(1, min(int(limit), MAX_RSS_ITEMS))]:
        title = _child_text(node, {"title"})[:1000] or "Sans titre"
        link = _child_text(node, {"link"})[:2000]
        published_raw = _child_text(node, {"pubdate", "published", "updated", "date"})
        published_at = _parse_date(published_raw)
        summary = _clean_summary(_child_text(node, {"description", "summary", "content", "encoded"}))
        external_id = _child_text(node, {"guid", "id"})[:1000]
        if not external_id:
            external_id = hashlib.sha256(
                f"{title}\n{link}\n{published_raw}".encode("utf-8")
            ).hexdigest()
        normalized.append(
            {
                "external_id": external_id,
                "title": title,
                "url": link,
                "summary": summary,
                "published_at": published_at,
                "raw": {
                    "published": published_raw[:200],
                    "format": _local_name(str(node.tag)),
                },
            }
        )
    return normalized
