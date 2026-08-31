from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://api.dhsprogram.com/",
    "https://api.dhsprogram.com/rest/dhs/countries/fields",
    "https://dhsprogram.com/pubs/pdf/DHSG1/Guide_to_DHS_Statistics_DHS-8.pdf",
)

PARAMETER_CONTRACTS = {
    "list_indicators": [
        {"name":"f","type":"string","default":"json","enum":["json"],"location":"query","ui_level":"advanced","description":"Output format qualified by HDP for the aggregate API."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Result page."},
        {"name":"perpage","type":"integer","default":5000,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Number of indicator catalogue rows requested."},
    ],
    "indicator_data": [
        {"name":"f","type":"string","default":"json","enum":["json"],"location":"query","ui_level":"advanced","description":"Output format."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Result page."},
        {"name":"perpage","type":"integer","default":100,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Rows requested per page."},
        {"name":"countryIds","type":"array[string]","default":[],"max_items":100,"location":"query","ui_level":"simple","description":"DHS-specific country codes. HDP resolves ISO3 through the official countries catalogue; ISO3 is never substituted directly."},
        {"name":"indicatorIds","type":"array[string]","default":[],"max_items":100,"location":"query","ui_level":"simple","description":"DHS indicator identifiers from the official indicator catalogue."},
        {"name":"surveyYears","type":"array[integer]","default":[],"max_items":100,"location":"query","ui_level":"advanced","description":"Survey years."},
        {"name":"breakdown","type":"string","default":"","max_length":80,"location":"query","ui_level":"advanced","description":"DHS breakdown selector when supported by the selected indicator query; e.g. national in provider examples."},
    ],
    "list_countries": [
        {"name":"f","type":"string","default":"json","enum":["json"],"location":"query","ui_level":"advanced","description":"Output format."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Result page."},
        {"name":"perpage","type":"integer","default":500,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Countries requested per page."},
    ],
    "list_surveys": [
        {"name":"f","type":"string","default":"json","enum":["json"],"location":"query","ui_level":"advanced","description":"Output format."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Result page."},
        {"name":"perpage","type":"integer","default":500,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Surveys requested per page."},
    ],
}

DHS_DESCRIPTOR = ProviderDescriptor(
    provider_id="dhs",
    name="The DHS Program — Aggregate Indicator API",
    api_version="public REST aggregate API",
    base_url="https://api.dhsprogram.com/rest/dhs",
    content_types=("indicator_catalogue", "indicator_data", "countries", "surveys"),
    operations=(
        ProviderOperationDescriptor("list_indicators", "indicator_catalogue", ("GET",)),
        ProviderOperationDescriptor("indicator_data", "indicator_data", ("GET",)),
        ProviderOperationDescriptor("list_countries", "countries", ("GET",)),
        ProviderOperationDescriptor("list_surveys", "surveys", ("GET",)),
    ),
    parameters=tuple(sorted({row["name"] for rows in PARAMETER_CONTRACTS.values() for row in rows})),
    configuration=(
        ProviderConfigField("format", "string", ConfigVisibility.PUBLIC, required=True, default="json", project_override=True, description="HDP qualified aggregate API output format."),
    ),
    capabilities=(
        ProviderCapability("aggregate_indicator_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("aggregate_indicator_data", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("country_catalogue_with_iso3", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("iso3_to_dhs_country_resolution", "hdp_verified", OFFICIAL_EVIDENCE),
        ProviderCapability("survey_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("no_microdata_access", "hdp_policy", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"qualified_format":"json", "microdata":False, "catalogue_default_perpage":5000},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"indicator_data",
        "nomenclatures":{"country":"provider countries catalogue; ISO3_countryCode -> DHS_countryCode", "indicator":"provider indicators catalogue"},
        "known_documented_not_yet_qualified":["survey characteristics", "publications", "datasets", "geometry", "tags", "data updates", "advanced query surface outside declared operations"],
        "scope_note":"HDP intentionally uses only aggregated indicator data. Individual DHS microdata remain outside this connector and require the provider's separate access process.",
    },
)
