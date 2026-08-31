from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://unstats.un.org/SDGAPI/swagger/",
    "https://unstats.un.org/SDGAPI/swagger/v1/swagger.json",
    "https://unstats.un.org/sdgs/metadata/",
)

PARAMETER_CONTRACTS = {
    "list_indicators": [],
    "geoarea_series": [
        {"name":"areaCode","type":"integer","required":True,"minimum":1,"maximum":999,"location":"path","ui_level":"simple","description":"UN M49 numeric area code used by the UNSD SDG API."},
    ],
    "series_data": [
        {"name":"seriesCode","type":"string","required":True,"min_length":1,"max_length":120,"location":"query","ui_level":"simple","description":"SDG series code from the provider catalogue."},
        {"name":"areaCode","type":"integer","minimum":1,"maximum":999,"location":"query","ui_level":"simple","description":"UN M49 area code."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Page."},
        {"name":"pageSize","type":"integer","default":100,"minimum":1,"maximum":1000,"location":"query","ui_level":"advanced","description":"Rows requested per page."},
        {"name":"timePeriodStart","type":"integer","minimum":1900,"maximum":2100,"location":"query","ui_level":"simple","description":"First time period/year."},
        {"name":"timePeriodEnd","type":"integer","minimum":1900,"maximum":2100,"location":"query","ui_level":"simple","description":"Last time period/year."},
    ],
}

UN_SDG_DESCRIPTOR = ProviderDescriptor(
    provider_id="un-sdg",
    name="UN Statistics Division — SDG API",
    api_version="v1",
    base_url="https://unstats.un.org/SDGAPI/v1/sdg",
    content_types=("indicators","geoarea_series","series_data"),
    operations=(
        ProviderOperationDescriptor("list_indicators", "indicators", ("GET",)),
        ProviderOperationDescriptor("geoarea_series", "geoarea_series", ("GET",)),
        ProviderOperationDescriptor("series_data", "series_data", ("GET",)),
    ),
    parameters=tuple(sorted({row["name"] for rows in PARAMETER_CONTRACTS.values() for row in rows})),
    configuration=(ProviderConfigField("api_version", "string", ConfigVisibility.INTERNAL, required=True, default="v1", project_override=False, description="Qualified UNSD SDG API version."),),
    capabilities=(
        ProviderCapability("indicator_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("geoarea_series_catalogue", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("series_observations", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("m49_geography_translation", "hdp_verified", OFFICIAL_EVIDENCE),
        ProviderCapability("year_filtering", "native", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"series_page_size_max":1000, "semantic_series_candidates":5},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"series_data",
        "nomenclatures":{"geography":"UN M49 -> areaCode", "series":"provider indicator/GeoArea catalogue"},
        "known_documented_not_yet_qualified":["the broader Swagger surface outside Indicator/List, GeoArea/{areaCode}/List and Series/Data"],
        "scope_note":"The UNSD Swagger exposes many additional analytical operations. They remain documented-but-unqualified rather than being silently presented as implemented.",
    },
)
