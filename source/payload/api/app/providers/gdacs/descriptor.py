from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://www.gdacs.org/gdacsapi/swagger/index.html",
    "https://www.gdacs.org/Documents/2025/GDACS_API_quickstart_v2.pdf",
    "https://www.gdacs.org/",
)

PARAMETER_CONTRACTS = {
    "search_events": [
        {"name":"eventlist","type":"array[string]","default":[],"enum_values":["EQ","FL","TC","TS","VO","DR","WF"],"max_items":7,"location":"query","ui_level":"simple","description":"GDACS event type codes. Values are serialized with ';'."},
        {"name":"fromdate","type":"string","default":"","max_length":10,"location":"query","ui_level":"simple","description":"Start date YYYY-MM-DD."},
        {"name":"todate","type":"string","default":"","max_length":10,"location":"query","ui_level":"simple","description":"End date YYYY-MM-DD."},
        {"name":"alertlevel","type":"array[string]","default":["green","orange","red"],"max_items":3,"location":"query","ui_level":"advanced","description":"GDACS alert colours, serialized with ';'."},
    ]
}

GDACS_DESCRIPTOR = ProviderDescriptor(
    provider_id="gdacs",
    name="GDACS — Global Disaster Alert and Coordination System",
    api_version="GDACS API / SEARCH",
    base_url="https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
    content_types=("events", "geojson"),
    operations=(ProviderOperationDescriptor("search_events", "events", ("GET",)),),
    parameters=("eventlist", "fromdate", "todate", "alertlevel"),
    configuration=(
        ProviderConfigField("response_profile", "string", ConfigVisibility.PUBLIC, required=True, default="geojson", project_override=False, description="Qualified GDACS search response profile."),
    ),
    capabilities=(
        ProviderCapability("multi_hazard_event_search", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("date_range", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("event_type_filter", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("alert_level_filter", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("geospatial_event_response", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("analysis_only_not_life_safety_alerting", "hdp_policy", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"qualified_operation":"SEARCH", "alerting_policy":"analysis_only"},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"search_events",
        "nomenclatures":{"event_types":["EQ","FL","TC","TS","VO","DR","WF"], "alert_levels":["green","orange","red"]},
        "known_documented_not_yet_qualified":["event sub-level resources and additional Swagger operations outside SEARCH", "bulk KML feeds"],
        "scope_note":"HDP uses GDACS as analytical context. It must not replace official emergency warning channels.",
    },
)
