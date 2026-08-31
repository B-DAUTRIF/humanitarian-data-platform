from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://data.unicef.org/sdmx-api-documentation/",
    "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest",
    "https://sdmx.org/?page_id=5008",
)

STRUCTURAL = [
    {"name":"agency","type":"string","default":"all","min_length":1,"max_length":80,"location":"path","ui_level":"advanced","description":"SDMX agency identifier."},
    {"name":"dataflow","type":"string","default":"all","min_length":1,"max_length":120,"location":"path","ui_level":"simple","description":"Dataflow identifier."},
    {"name":"version","type":"string","default":"latest","min_length":1,"max_length":40,"location":"path","ui_level":"advanced","description":"Dataflow version."},
    {"name":"format","type":"string","default":"sdmx-json","enum":["sdmx-json"],"location":"query","ui_level":"expert","description":"Qualified HDP structural/data response format."},
]

PARAMETER_CONTRACTS = {
    "list_dataflows": STRUCTURAL + [
        {"name":"detail","type":"string","default":"full","enum":["allstubs","referencestubs","referencepartial","allcompletestubs","full"],"location":"query","ui_level":"advanced","description":"SDMX structural detail."},
        {"name":"references","type":"string","default":"none","max_length":80,"location":"query","ui_level":"advanced","description":"SDMX reference expansion."},
    ],
    "get_data": STRUCTURAL + [
        {"name":"data_query","type":"string","default":"all","min_length":1,"max_length":2000,"location":"path","ui_level":"simple","description":"SDMX key: dimensions separated by '.', multiple values in a dimension separated by '+'. Dimension order must come from the selected dataflow/DSD; HDP never guesses it."},
    ],
}

UNICEF_SDMX_DESCRIPTOR = ProviderDescriptor(
    provider_id="unicef-sdmx",
    name="UNICEF Data — SDMX API",
    api_version="public SDMX REST",
    base_url="https://sdmx.data.unicef.org/ws/public/sdmxapi/rest",
    content_types=("dataflows","data"),
    operations=(
        ProviderOperationDescriptor("list_dataflows", "dataflows", ("GET",)),
        ProviderOperationDescriptor("get_data", "data", ("GET",)),
    ),
    parameters=tuple(sorted({row["name"] for rows in PARAMETER_CONTRACTS.values() for row in rows})),
    configuration=(ProviderConfigField("format", "string", ConfigVisibility.PUBLIC, required=True, default="sdmx-json", project_override=True, description="Qualified HDP SDMX format."),),
    capabilities=(
        ProviderCapability("dataflow_discovery", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("sdmx_key_query", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("dataflow_dsd_codelist_resolution", "documented_dynamic", OFFICIAL_EVIDENCE),
        ProviderCapability("no_guessed_dimension_order", "hdp_verified", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"qualified_format":"sdmx-json", "semantic_data_query":"blocked_without_dataflow_dsd_mapping"},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"list_dataflows",
        "nomenclatures":{"pipeline":"dataflow -> DSD -> dimensions -> codelists", "data_query_separator":".", "multi_value_separator":"+"},
        "known_documented_not_yet_qualified":["generic geography/time semantic routing without a selected DSD", "XML/CSV normalization parity", "all SDMX structural resources beyond dataflow discovery"],
        "scope_note":"Native Expert get_data is supported when the user supplies an explicit dataflow and DSD-ordered key. Semantic geography/time stays blocked until those dimensions are verified for the selected dataflow.",
    },
)
