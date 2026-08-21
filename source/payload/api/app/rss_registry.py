from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any
from urllib.parse import urlencode, urlparse

try:
    from defusedxml import ElementTree
except ModuleNotFoundError:  # The production image installs defusedxml; pure tests retain the explicit guards below.
    from xml.etree import ElementTree


MAX_RSS_BYTES = 2 * 1024 * 1024
MAX_RSS_ITEMS = 200
RSS_REGISTRY_VERSION = "6.0.0-20260821"
RSS_REGISTRY_SCOPE = (
    "flux RSS/Atom sanitaires, épidémiologiques ou d'alertes publiés et documentés "
    "par des organisations internationales/régionales et agences publiques de référence"
)


def _feed(
    identifier: str,
    name: str,
    organization: str,
    base_url: str,
    portal_url: str,
    *,
    region: str,
    themes: list[str],
    languages: list[str],
    frequency: str,
    verified_at: str,
    evidence_url: str,
    license_name: str,
    supports_query: bool = False,
) -> dict[str, Any]:
    hostname = urlparse(base_url).hostname
    if not hostname:
        raise ValueError("Flux officiel sans hôte")
    return {
        "id": identifier,
        "name": name,
        "organization": organization,
        "base_url": base_url,
        "portal_url": portal_url,
        "allowed_hosts": [hostname],
        "region": region,
        "themes": themes,
        "languages": languages,
        "protocol": "RSS/Atom over HTTPS",
        "license": license_name,
        "declared_frequency": frequency,
        "state": "documented",
        "evidence_url": evidence_url,
        "verified_at": verified_at,
        "registry_version": RSS_REGISTRY_VERSION,
        "supports_query": supports_query,
    }

_REGISTRY: dict[str, dict[str, Any]] = {
    item["id"]: item
    for item in (
        _feed(
            "reliefweb-reports", "ReliefWeb — rapports et mises à jour", "OCHA / ReliefWeb",
            "https://reliefweb.int/updates/rss.xml", "https://reliefweb.int/rss",
            region="Monde", themes=["humanitaire", "santé", "épidémies"], languages=["en", "fr", "es"],
            frequency="continue", verified_at="2026-08-15", evidence_url="https://reliefweb.int/rss",
            license_name="Conditions ReliefWeb et source", supports_query=True,
        ),
        _feed(
            "reliefweb-disasters", "ReliefWeb — catastrophes", "OCHA / ReliefWeb",
            "https://reliefweb.int/disasters/rss.xml", "https://reliefweb.int/rss",
            region="Monde", themes=["catastrophes", "urgences"], languages=["en", "fr", "es"],
            frequency="continue", verified_at="2026-08-15", evidence_url="https://reliefweb.int/rss",
            license_name="Conditions ReliefWeb et source", supports_query=True,
        ),
        _feed(
            "reliefweb-jobs", "ReliefWeb — emplois humanitaires", "OCHA / ReliefWeb",
            "https://reliefweb.int/jobs/rss.xml", "https://reliefweb.int/rss",
            region="Monde", themes=["ressources humaines humanitaires"], languages=["en", "fr", "es"],
            frequency="continue", verified_at="2026-08-15", evidence_url="https://reliefweb.int/rss",
            license_name="Conditions ReliefWeb et source", supports_query=True,
        ),
        _feed(
            "reliefweb-training", "ReliefWeb — formations", "OCHA / ReliefWeb",
            "https://reliefweb.int/training/rss.xml", "https://reliefweb.int/rss",
            region="Monde", themes=["formation humanitaire", "santé"], languages=["en", "fr", "es"],
            frequency="continue", verified_at="2026-08-15", evidence_url="https://reliefweb.int/rss",
            license_name="Conditions ReliefWeb et source", supports_query=True,
        ),
        _feed(
            "who-afro-emergencies", "OMS Afrique — urgences et flambées", "OMS / Bureau Afrique",
            "https://www.afro.who.int/rss/emergencies.xml", "https://www.afro.who.int/rss-feeds",
            region="Afrique", themes=["urgences sanitaires", "flambées épidémiques"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://www.afro.who.int/rss-feeds",
            license_name="Conditions et copyright OMS",
        ),
        _feed(
            "ecdc-epidemiological-updates", "ECDC — mises à jour épidémiologiques", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/1310/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["épidémiologie", "maladies transmissibles"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "ecdc-cdtr", "ECDC — menaces transmissibles (CDTR)", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/1505/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["veille épidémique", "menaces sanitaires"], languages=["en"],
            frequency="hebdomadaire", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "ecdc-risk-assessments", "ECDC — évaluations de risque", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/1295/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["risque sanitaire", "épidémiologie"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "ecdc-avian-influenza", "ECDC — influenza aviaire", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/323/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["influenza aviaire", "zoonoses"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "ecdc-mpox", "ECDC — mpox", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/2794/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["mpox"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "ecdc-west-nile", "ECDC — virus West Nile", "ECDC",
            "https://www.ecdc.europa.eu/en/taxonomy/term/197/feed", "https://www.ecdc.europa.eu/en/rss-feeds",
            region="UE/EEE et monde", themes=["West Nile", "maladies vectorielles"], languages=["en"],
            frequency="saisonnière", verified_at="2026-08-21", evidence_url="https://www.ecdc.europa.eu/en/rss-feeds",
            license_name="Politique de réutilisation ECDC/UE",
        ),
        _feed(
            "cdc-travel-notices", "CDC — avis sanitaires aux voyageurs", "CDC",
            "https://wwwnc.cdc.gov/travel/rss/notices.xml", "https://wwwnc.cdc.gov/travel/page/rss",
            region="Monde", themes=["risques sanitaires", "voyages", "flambées"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://wwwnc.cdc.gov/travel/page/rss",
            license_name="Politique de syndication CDC",
        ),
        _feed(
            "cdc-eid-ahead", "CDC EID — articles avant publication", "CDC / Emerging Infectious Diseases",
            "https://wwwnc.cdc.gov/eid/rss/ahead-of-print.xml", "https://wwwnc.cdc.gov/eid/page/rss-feeds",
            region="Monde", themes=["maladies infectieuses émergentes", "recherche"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://wwwnc.cdc.gov/eid/page/rss-feeds",
            license_name="Conditions CDC/EID",
        ),
        _feed(
            "cdc-eid-expedited", "CDC EID — articles accélérés", "CDC / Emerging Infectious Diseases",
            "https://wwwnc.cdc.gov/eid/rss/expedited.xml", "https://wwwnc.cdc.gov/eid/page/rss-feeds",
            region="Monde", themes=["maladies infectieuses émergentes", "alertes scientifiques"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://wwwnc.cdc.gov/eid/page/rss-feeds",
            license_name="Conditions CDC/EID",
        ),
        _feed(
            "cdc-newsroom", "CDC — salle de presse", "CDC",
            "https://tools.cdc.gov/api/v2/resources/media/132608.rss", "https://tools.cdc.gov/medialibrary/index.html",
            region="États-Unis et monde", themes=["santé publique", "alertes", "épidémies"], languages=["en"],
            frequency="à publication", verified_at="2026-08-21", evidence_url="https://tools.cdc.gov/medialibrary/index.html",
            license_name="Politique de syndication CDC",
        ),
    )
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
    return build_rss_url_from_definition(definition, query, language)


def build_rss_url_from_definition(definition: dict[str, Any], query: str = "", language: str = "en") -> str:
    if language not in {"en", "fr", "es"}:
        raise ValueError("La langue RSS doit être en, fr ou es")
    cleaned = " ".join(str(query).split())[:200]
    if not definition.get("supports_query"):
        if cleaned:
            raise ValueError("Ce flux ne prend pas en charge les paramètres de recherche")
        return str(definition["base_url"])
    parameters: dict[str, str] = {"lang": language}
    if cleaned:
        parameters["search"] = cleaned
    return f"{definition['base_url']}?{urlencode(parameters)}"


def validate_feed_definition(definition: dict[str, Any]) -> dict[str, Any]:
    required = {
        "id", "name", "organization", "base_url", "portal_url", "region", "themes",
        "languages", "license", "declared_frequency", "evidence_url", "verified_at",
    }
    missing = sorted(required - set(definition))
    if missing:
        raise ValueError(f"Métadonnées du flux absentes: {missing}")
    base = urlparse(str(definition["base_url"]))
    evidence = urlparse(str(definition["evidence_url"]))
    if base.scheme != "https" or not base.hostname or base.username or base.password:
        raise ValueError("Le flux doit utiliser une URL HTTPS sans identifiants")
    if evidence.scheme != "https" or not evidence.hostname:
        raise ValueError("La preuve documentaire doit utiliser HTTPS")
    allowed_hosts = sorted(set(definition.get("allowed_hosts", [base.hostname])))
    if base.hostname not in allowed_hosts or any(
        not isinstance(host, str) or not re.fullmatch(r"[A-Za-z0-9.-]{1,253}", host)
        for host in allowed_hosts
    ):
        raise ValueError("Liste d'hôtes RSS incohérente")
    normalized = deepcopy(definition)
    normalized.update(
        {
            "allowed_hosts": allowed_hosts,
            "protocol": "RSS/Atom over HTTPS",
            "state": str(definition.get("state", "draft")),
            "registry_version": str(definition.get("registry_version", RSS_REGISTRY_VERSION)),
            "supports_query": bool(definition.get("supports_query", False)),
        }
    )
    return normalized


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
    if _local_name(str(root.tag)) not in {"rss", "feed", "rdf"}:
        raise ValueError("La racine XML n'est ni RSS, Atom, ni RDF")
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


def rss_schema_signature(payload: bytes) -> str:
    if len(payload) > MAX_RSS_BYTES:
        raise ValueError("Le flux RSS dépasse la limite de 2 Mio")
    upper = payload[:4096].upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("Les DTD et entités XML sont interdites")
    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        raise ValueError("Le flux RSS/XML est invalide") from exc
    item_shapes = sorted(
        {
            tuple(sorted(_local_name(str(child.tag)) for child in list(node)))
            for node in root.iter()
            if _local_name(str(node.tag)) in {"item", "entry"}
        }
    )
    descriptor = {"root": _local_name(str(root.tag)), "item_shapes": item_shapes}
    return hashlib.sha256(repr(descriptor).encode("utf-8")).hexdigest()
