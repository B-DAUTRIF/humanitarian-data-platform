from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://www.who.int/data/gho/info/gho-odata-api",
    "https://ghoapi.azureedge.net/api/Indicator",
    "https://www.who.int/about/policies/publishing/data-policy",
)

COMMON_PAGING = [
    {"name":"top","native_name":"$top","type":"integer","default":100,"minimum":1,"maximum":5000,"location":"query","ui_level":"advanced","description":"OData maximum rows returned."},
    {"name":"skip","native_name":"$skip","type":"integer","default":0,"minimum":0,"maximum":100000,"location":"query","ui_level":"advanced","description":"OData row offset."},
    {"name":"format","native_name":"$format","type":"string","default":"json","enum":["json"],"location":"query","ui_level":"expert","description":"Qualified HDP response format."},
]

PARAMETER_CONTRACTS = {
    "list_dimensions": list(COMMON_PAGING),
    "dimension_values": [
        {"name":"dimension","type":"string","required":True,"min_length":1,"max_length":80,"location":"path","ui_level":"simple","description":"WHO GHO dimension code, obtained from the dimensions catalogue."},
        *COMMON_PAGING,
    ],
    "list_indicators": [
        {"name":"filter","native_name":"$filter","type":"string","default":"","max_length":1000,"location":"query","ui_level":"simple","description":"OData filter. WHO documentation demonstrates contains() and equality filters on IndicatorName."},
        *COMMON_PAGING,
    ],
    "indicator_data": [
        {"name":"indicator","type":"string","required":True,"min_length":1,"max_length":120,"location":"path","ui_level":"simple","description":"Indicator code from the WHO Indicator catalogue."},
        {"name":"filter","native_name":"$filter","type":"string","default":"","max_length":2000,"location":"query","ui_level":"simple","description":"OData filter over dimensions/time. WHO documents Dim filters and TimeDimensionBegin/End filtering."},
        *COMMON_PAGING,
    ],
}

WHO_GHO_DESCRIPTOR = ProviderDescriptor(
    provider_id="who-gho",
    name="WHO Global Health Observatory — OData API",
    api_version="legacy GHO OData public API",
    base_url="https://ghoapi.azureedge.net/api",
    content_types=("dimensions", "dimension_values", "indicators", "indicator_data"),
    operations=(
        ProviderOperationDescriptor("list_dimensions", "dimensions", ("GET",)),
        ProviderOperationDescriptor("dimension_values", "dimension_values", ("GET",)),
        ProviderOperationDescriptor("list_indicators", "indicators", ("GET",)),
        ProviderOperationDescriptor("indicator_data", "indicator_data", ("GET",)),
    ),
    parameters=tuple(sorted({row["name"] for rows in PARAMETER_CONTRACTS.values() for row in rows})),
    configuration=(
        ProviderConfigField("format", "string", ConfigVisibility.PUBLIC, required=True, default="json", project_override=True, description="Qualified JSON response format."),
    ),
    capabilities=(
        ProviderCapability("dimension_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("dimension_value_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("indicator_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("indicator_observations", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("odata_filtering", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("semantic_keyword_catalogue", "hdp_verified", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"qualified_format":"json", "semantic_observation_routing":"blocked_pending_post_2025_requalification"},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"list_indicators",
        "nomenclatures":{"dimensions":"/api/DIMENSION", "indicators":"/api/Indicator"},
        "known_documented_not_yet_qualified":["newer World Health Data Hub contracts outside the legacy GHO OData endpoint", "arbitrary OData query options beyond the declared surface"],
        "scope_note":"Keyword catalogue search is qualified. Semantic geography/time observation routing remains explicitly blocked until the newer WHO contract is requalified; native expert indicator_data remains available with explicit OData filters.",
    },
)
