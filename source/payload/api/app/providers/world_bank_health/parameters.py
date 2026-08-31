from __future__ import annotations

"""Canonical World Bank Indicators API v2 parameter documentation for HDP V7.

This module deliberately separates:
- provider-documented native parameters;
- the subset implemented by the World Bank reference service;
- the subset exposed by the HDP project/UI contract;
- semantic-router translations.

A documented provider capability is never treated as qualified merely because it is
listed here. `qualification` is the auditable status of the HDP implementation.
"""

from typing import Any

OFFICIAL_PARAMETER_EVIDENCE = {
    "about": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation",
    "basic": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
    "countries": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries",
    "indicators": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries",
    "aggregates": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898614-aggregate-api-queries",
    "topics": "https://datahelpdesk.worldbank.org/knowledgebase/articles/898611-topic-api-queries",
    "metadata": "https://datahelpdesk.worldbank.org/knowledgebase/articles/1886695-metadata-api-queries",
    "v2_enhancements": "https://datahelpdesk.worldbank.org/knowledgebase/articles/1886674-new-features-and-enhancements-in-the-v2-api",
}


def _p(
    name: str,
    *,
    location: str,
    value_type: str,
    operations: tuple[str, ...],
    semantics: str,
    hdp_field: str | None = None,
    default: Any = None,
    allowed: tuple[Any, ...] = (),
    constraints: str = "",
    interaction: str = "",
    semantic_role: str = "",
    ui: str = "",
    qualification: str = "IMPLÉMENTÉ ET QUALIFIÉ",
    evidence: str = "basic",
) -> dict[str, Any]:
    return {
        "native_name": name,
        "location": location,
        "type": value_type,
        "operations": list(operations),
        "semantics": semantics,
        "hdp_field": hdp_field,
        "default": default,
        "allowed_values": list(allowed),
        "constraints": constraints,
        "interaction": interaction,
        "semantic_role": semantic_role,
        "ui": ui,
        "qualification": qualification,
        "evidence": OFFICIAL_PARAMETER_EVIDENCE[evidence],
    }


WORLD_BANK_PARAMETER_DOCUMENTATION: dict[str, dict[str, Any]] = {
    "country": _p(
        "country", location="path", value_type="string/list",
        operations=("get_observations", "list_countries"),
        semantics="Country/economy identifier. Multiple values use ';'. HDP semantic country routing accepts only provider-verified sovereign ISO3 identifiers; World Bank aggregate identifiers remain a distinct semantic type.",
        hdp_field="country", default="all", constraints="ISO3 verified against provider country catalogue for semantic sovereign-country routing; ';' for multiple values.",
        semantic_role="location → canonical geography → verified ISO3 → World Bank country path", ui="text + verified geography vocabulary", evidence="countries",
    ),
    "indicator": _p(
        "indicator", location="path", value_type="string/list",
        operations=("get_observations", "list_indicators", "get_metadata"),
        semantics="Indicator/series code. Multiple indicator codes can be separated by ';' when a source is supplied.",
        hdp_field="indicator", constraints="At least one code for observations; provider documents a maximum of 60 indicators and URL length limits.",
        semantic_role="query/theme → indicator catalogue discovery → selected verified indicator code(s)", ui="catalogue search + code text", evidence="basic",
    ),
    "source": _p(
        "source", location="query/path", value_type="integer", operations=("get_observations", "list_indicators", "list_sources", "get_metadata"),
        semantics="World Bank data-source identifier. Source 2 is World Development Indicators (WDI).", hdp_field="source", default=2,
        semantic_role="project/provider configuration; semantic health profile defaults to source 2", ui="numeric/list", evidence="basic",
    ),
    "date": _p(
        "date", location="query", value_type="period/range", operations=("get_observations",),
        semantics="Scopes observations by year, month or quarter; ':' expresses a range.", hdp_field="date", default="",
        constraints="Current HDP observation model qualifies YYYY or YYYY:YYYY.", semantic_role="date_from/date_to → year or year-range", ui="year/range text", evidence="basic",
    ),
    "page": _p(
        "page", location="query", value_type="integer", operations=("catalogues", "get_observations", "get_metadata"),
        semantics="Result page number.", hdp_field="page", default=1, constraints=">=1", semantic_role="pagination", ui="number", evidence="basic",
    ),
    "per_page": _p(
        "per_page", location="query", value_type="integer", operations=("catalogues", "get_observations", "get_metadata"),
        semantics="Number of results returned per page; provider documentation states default 50.", hdp_field="per_page", default=50,
        constraints="HDP validates 1..50000; endpoint/provider practical limits remain provider-dependent.", semantic_role="result_limit is not silently equated to exhaustive pagination", ui="number", evidence="basic",
    ),
    "mrv": _p(
        "mrv", location="query", value_type="integer", operations=("get_observations",),
        semantics="Fetch the N most recent values.", hdp_field="mrv", default=None, constraints=">=1 when supplied",
        interaction="Works with gapfill and frequency.", semantic_role="advanced provider-native filter", ui="optional number", evidence="basic",
    ),
    "mrnev": _p(
        "mrnev", location="query", value_type="integer", operations=("get_observations",),
        semantics="Fetch the N most recent non-empty values.", hdp_field="mrnev", default=None, constraints=">=1 when supplied",
        semantic_role="advanced provider-native filter", ui="optional number", evidence="basic",
    ),
    "gapfill": _p(
        "gapfill", location="query", value_type="enum/bool", operations=("get_observations",),
        semantics="Backtracks to an available period when the requested recent value is unavailable.", hdp_field="gapfill", default=False, allowed=("Y", "N"),
        interaction="Provider documents gapfill as operating with MRV; HDP serializes true as Y and omits false.", semantic_role="advanced provider-native filter", ui="checkbox/select", evidence="basic",
    ),
    "frequency": _p(
        "frequency", location="query", value_type="enum", operations=("get_observations",),
        semantics="Select yearly, quarterly or monthly high-frequency values.", hdp_field="frequency", default="", allowed=("Y", "Q", "M"),
        interaction="Provider documents frequency as working with MRV.", semantic_role="advanced provider-native filter", ui="select", evidence="basic",
    ),
    "footnote": _p(
        "footnote", location="query", value_type="enum/bool", operations=("get_observations",),
        semantics="Requests observation footnote detail.", hdp_field="footnote", default=False, allowed=("y",),
        semantic_role="advanced provider-native output enrichment", ui="checkbox/select", evidence="basic",
    ),
    "format": _p(
        "format", location="query", value_type="enum", operations=("all"),
        semantics="Response representation. Provider default is XML; format=json requests JSON.", hdp_field="format", default="json", allowed=("json",),
        constraints="HDP V7 reference normalization is qualified only for JSON; XML is provider-documented but not qualified by this connector path.", semantic_role="fixed qualified representation", ui="select (json only)", evidence="basic",
    ),
    "language": _p(
        "language", location="path", value_type="language-code", operations=("catalogues", "get_observations", "get_metadata"),
        semantics="Localized API path prefix when supported by the provider.", hdp_field="language", default="en", allowed=("en", "fr", "es", "ar", "zh"),
        constraints="This list is the HDP-qualified subset, not a claim that the provider supports only these languages.", semantic_role="project/provider presentation option", ui="select", evidence="basic",
    ),
    "topic": _p(
        "topic", location="query/path", value_type="integer/list", operations=("list_indicators", "list_topics"),
        semantics="Filters indicators by World Bank topic; topic resources also accept specific topic IDs.", hdp_field=None,
        semantic_role="catalogue discovery candidate", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="topics",
    ),
    "incomeLevel": _p(
        "incomeLevel", location="query/path", value_type="string/list", operations=("list_countries",),
        semantics="Filters countries/economies by World Bank income-level classification.", hdp_field=None,
        semantic_role="catalogue filter, not a substitute for sovereign geography mapping", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="basic",
    ),
    "region": _p(
        "region", location="query/path", value_type="string/list", operations=("list_countries",),
        semantics="Filters the country/economy catalogue by World Bank region identifier.", hdp_field=None,
        semantic_role="catalogue filter", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="countries",
    ),
    "lendingType": _p(
        "lendingType", location="query/path", value_type="string/list", operations=("list_countries",),
        semantics="Filters the country/economy catalogue by World Bank lending type.", hdp_field=None,
        semantic_role="catalogue filter", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="countries",
    ),
    "downloadformat": _p(
        "downloadformat", location="query", value_type="enum", operations=("downloads", "metadata"),
        semantics="Requests downloadable provider representations such as Excel/CSV where supported.", hdp_field=None,
        interaction="May work with dataformat for indicator downloads.", semantic_role="download/export path", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="v2_enhancements",
    ),
    "dataformat": _p(
        "dataformat", location="query", value_type="enum", operations=("downloads",),
        semantics="Controls indicator download layout as table or list.", hdp_field=None, allowed=("table", "list"),
        interaction="Provider documents this with downloadformat.", semantic_role="download/export layout", ui="not exposed", qualification="SPÉCIFIÉ / PLANIFIÉ", evidence="v2_enhancements",
    ),
    "concept": _p(
        "concept", location="path", value_type="string/list", operations=("get_metadata",),
        semantics="Metadata dimension/concept, for example Country, Series or Time.", hdp_field=None,
        semantic_role="metadata exploration", ui="not exposed", qualification="PARTIELLEMENT IMPLÉMENTÉ", evidence="metadata",
    ),
    "metatype": _p(
        "metatype", location="path", value_type="string/list", operations=("get_metadata",),
        semantics="Metadata type belonging to a World Bank metadata concept.", hdp_field=None,
        semantic_role="metadata exploration", ui="not exposed", qualification="PARTIELLEMENT IMPLÉMENTÉ", evidence="metadata",
    ),
    "search": _p(
        "search", location="path", value_type="string", operations=("get_metadata",),
        semantics="Keyword search in the World Bank Metadata API.", hdp_field="query", constraints="HDP exposes this through the specialized metadata operation.",
        semantic_role="metadata keyword discovery", ui="text", qualification="IMPLÉMENTÉ ET QUALIFIÉ", evidence="metadata",
    ),
}


SEMANTIC_PARAMETER_MAPPING: dict[str, dict[str, Any]] = {
    "query": {
        "canonical_concept": "keywords/theme",
        "world_bank_translation": "Discover indicator codes from the source catalogue, then query observations for selected matches.",
        "native_targets": ["indicator path", "metadata search path"],
        "verification": "indicator catalogue/provider metadata",
        "on_missing_mapping": "BLOCKED_MISSING_MAPPING or bounded catalogue result; never invent an indicator code",
    },
    "location": {
        "canonical_concept": "geography",
        "world_bank_translation": "Resolve name/ISO/M49 through HDP nomenclature, then verify World Bank country catalogue and emit sovereign ISO3.",
        "native_targets": ["country path"],
        "verification": "World Bank country catalogue + HDP geography mapping evidence",
        "on_missing_mapping": "BLOCKED_MISSING_MAPPING; aggregates are not silently treated as countries",
    },
    "date_from/date_to": {
        "canonical_concept": "time interval",
        "world_bank_translation": "Convert ISO dates to supported World Bank year or year-range for the current qualified observation route.",
        "native_targets": ["date"],
        "verification": "deterministic serialization tests",
        "on_missing_mapping": "unsupported/partial rather than guessed provider period",
    },
    "result_limit": {
        "canonical_concept": "bounded user result count",
        "world_bank_translation": "Bound catalogue/observation retrieval and final normalized output without claiming exhaustiveness.",
        "native_targets": ["per_page", "catalogue page size", "HDP output slice"],
        "verification": "anti-false-zero/completeness tests",
        "on_missing_mapping": "bounded completeness",
    },
    "project_id": {
        "canonical_concept": "HDP project context",
        "world_bank_translation": "Never sent to World Bank. Used only to resolve enabled state and provider configuration overrides.",
        "native_targets": [],
        "verification": "UUID/Pydantic + non-contamination tests",
        "on_missing_mapping": "validation_error",
    },
}


def parameter_documentation() -> dict[str, Any]:
    rows = list(WORLD_BANK_PARAMETER_DOCUMENTATION.values())
    return {
        "provider": "world-bank-health",
        "api": "World Bank Indicators API",
        "api_version": "v2",
        "evidence": OFFICIAL_PARAMETER_EVIDENCE,
        "parameters": WORLD_BANK_PARAMETER_DOCUMENTATION,
        "counts": {
            "documented_in_hdp_matrix": len(rows),
            "implemented_and_qualified": sum(row["qualification"] == "IMPLÉMENTÉ ET QUALIFIÉ" for row in rows),
            "partial": sum(row["qualification"] == "PARTIELLEMENT IMPLÉMENTÉ" for row in rows),
            "planned": sum(row["qualification"] == "SPÉCIFIÉ / PLANIFIÉ" for row in rows),
        },
        "semantic_mapping": SEMANTIC_PARAMETER_MAPPING,
        "qualification_rule": "Documentation fournisseur != qualification HDP; only executed evidence can produce an implemented/qualified status.",
    }
