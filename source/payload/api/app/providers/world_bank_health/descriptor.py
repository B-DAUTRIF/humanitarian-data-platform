from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/898599-indicator-api-queries",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/898614-aggregate-api-queries",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/898611-topic-api-queries",
    "https://datahelpdesk.worldbank.org/knowledgebase/articles/1886695-metadata-api-queries",
)

FEATURES = (
    "indicator_catalogue", "indicator_keyword_discovery", "wdi_source_2", "indicator_code_selection",
    "country_iso3", "multi_country", "single_indicator", "multi_indicator", "year_range", "single_year",
    "pagination", "page_size", "most_recent_values", "most_recent_non_empty", "gapfill", "frequency",
    "footnotes", "json_format", "language", "topic_catalogue", "country_metadata", "aggregate_separation",
    "normalization", "native_provenance", "invalid_geography_rejection", "provider_error_not_empty",
    "bounded_result_not_absence",
)

WORLD_BANK_HEALTH_DESCRIPTOR = ProviderDescriptor(
    provider_id="world-bank-health",
    name="World Bank Health / WDI Indicators API",
    api_version="v2",
    base_url="https://api.worldbank.org/v2",
    content_types=("indicators", "observations", "countries", "topics", "sources", "metadata"),
    operations=(
        ProviderOperationDescriptor("list_indicators", "indicators", ("GET",)),
        ProviderOperationDescriptor("get_observations", "observations", ("GET",)),
        ProviderOperationDescriptor("list_countries", "countries", ("GET",)),
        ProviderOperationDescriptor("list_topics", "topics", ("GET",)),
        ProviderOperationDescriptor("list_sources", "sources", ("GET",)),
        ProviderOperationDescriptor("get_metadata", "metadata", ("GET",)),
    ),
    parameters=("source", "country", "indicator", "date", "page", "per_page", "mrv", "mrnev", "gapfill", "frequency", "footnote", "format", "language"),
    configuration=(
        ProviderConfigField("source", "integer", ConfigVisibility.PUBLIC, required=True, default=2, project_override=True, description="World Bank source identifier; source 2 is WDI."),
        ProviderConfigField("format", "string", ConfigVisibility.PUBLIC, required=True, default="json", project_override=True, description="HDP V7 normalization path is qualified for JSON."),
    ),
    capabilities=tuple(ProviderCapability(name, "native" if name not in {"indicator_keyword_discovery", "normalization", "provider_error_not_empty", "bounded_result_not_absence", "aggregate_separation"} else "hdp_verified", OFFICIAL_EVIDENCE) for name in FEATURES),
    runtime_limits={"interactive_default_limit": 25, "qualified_format": "json", "health_profile_source": 2},
    evidence=OFFICIAL_EVIDENCE,
    metadata={"evidence_status": "DOCUMENTED", "country_codes": "ISO3166 alpha2/alpha3 plus provider aggregate identifiers", "aggregate_codes_are_not_sovereign_countries": True, "feature_count": len(FEATURES)},
)
