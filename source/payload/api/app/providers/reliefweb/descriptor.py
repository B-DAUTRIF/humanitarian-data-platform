from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

CONTENT_TYPES = ("reports", "disasters", "countries", "jobs", "training", "sources", "blog", "book", "references")
OFFICIAL_EVIDENCE = (
    "https://apidoc.reliefweb.int/",
    "https://apidoc.reliefweb.int/endpoints",
    "https://apidoc.reliefweb.int/parameters",
    "https://apidoc.reliefweb.int/fields-tables",
    "https://apidoc.reliefweb.int/presets",
    "https://apidoc.reliefweb.int/result-structure",
    "https://apidoc.reliefweb.int/faq",
)

RELIEFWEB_DESCRIPTOR = ProviderDescriptor(
    provider_id="reliefweb",
    name="ReliefWeb API",
    api_version="v2",
    base_url="https://api.reliefweb.int/v2",
    content_types=CONTENT_TYPES,
    operations=tuple(
        ProviderOperationDescriptor(name=f"list_{kind}", content_type=kind, methods=("GET", "POST"), collection=True, item=False)
        for kind in CONTENT_TYPES
    ) + tuple(
        ProviderOperationDescriptor(name=f"get_{kind}", content_type=kind, methods=("GET",), collection=False, item=True)
        for kind in CONTENT_TYPES
    ),
    parameters=("appname", "query", "filter", "facets", "limit", "offset", "sort", "profile", "preset", "fields", "slim", "verbose"),
    configuration=(
        ProviderConfigField(name="appname", type="string", visibility=ConfigVisibility.PUBLIC, required=True, default="HDP_plateforme", project_override=True, execution_override=False, description="Pre-approved ReliefWeb application identifier."),
    ),
    capabilities=(
        ProviderCapability("full_text_query", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("field_scoped_query", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("advanced_lucene_query", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("exact_field_query", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("query_boost", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("recursive_filters", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("filter_negation", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("facets", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("facet_scopes", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("pagination", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("sorting", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("profiles", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("presets", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("field_projection", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("verbose_interpretation", "native", OFFICIAL_EVIDENCE),
    ),
    runtime_limits={"max_page_size": 1000, "documented_daily_request_quota": 1000, "interactive_default_limit": 25, "supports_exhaustive_acquisition": True},
    evidence=OFFICIAL_EVIDENCE,
    metadata={"evidence_status": "DOCUMENTED", "publishing_api_separate": True, "field_tables_are_content_type_specific": True},
)
