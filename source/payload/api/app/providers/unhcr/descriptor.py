from __future__ import annotations

from ..base.contracts import ConfigVisibility, ProviderCapability, ProviderConfigField, ProviderDescriptor, ProviderOperationDescriptor

OFFICIAL_EVIDENCE = (
    "https://api.unhcr.org/docs/refugee-statistics.html",
    "https://www.unhcr.org/refugee-statistics/insights/explainers/forcibly-displaced-api.html",
    "https://www.unhcr.org/refugee-statistics/",
)

POPULATION_PARAMS = [
    {"name":"limit","type":"integer","default":25,"minimum":1,"maximum":1000,"location":"query","ui_level":"advanced","description":"Rows per response."},
    {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Result page."},
    {"name":"yearFrom","type":"integer","minimum":1951,"maximum":2100,"location":"query","ui_level":"simple","description":"First year of the interval."},
    {"name":"yearTo","type":"integer","minimum":1951,"maximum":2100,"location":"query","ui_level":"simple","description":"Last year of the interval."},
    {"name":"year","type":"integer","minimum":1951,"maximum":2100,"location":"query","ui_level":"advanced","description":"Single year when the operation supports it."},
    {"name":"coo","type":"string","default":"","max_length":400,"location":"query","ui_level":"simple","description":"Country of origin code(s). With cf_type=ISO, ISO3 is used by the provider."},
    {"name":"coa","type":"string","default":"","max_length":400,"location":"query","ui_level":"simple","description":"Country of asylum code(s). With cf_type=ISO, ISO3 is used by the provider."},
    {"name":"coo_all","type":"boolean","default":False,"location":"query","ui_level":"expert","description":"Provider all-origins switch."},
    {"name":"coa_all","type":"boolean","default":False,"location":"query","ui_level":"expert","description":"Provider all-asylum-countries switch."},
    {"name":"cf_type","type":"string","default":"ISO","enum":["ISO","id"],"location":"query","ui_level":"advanced","description":"Country filter identifier type. Semantic HDP routing qualifies ISO."},
    {"name":"download","type":"boolean","default":False,"location":"query","ui_level":"expert","description":"Provider download response switch; HDP native JSON path keeps this false by default."},
]

PARAMETER_CONTRACTS = {
    "population": list(POPULATION_PARAMS),
    "demographics": list(POPULATION_PARAMS) + [
        {"name":"columns","type":"string","default":"","max_length":500,"location":"query","ui_level":"expert","description":"Demographic columns requested when supported by the provider operation."},
        {"name":"ptype_show","type":"boolean","default":False,"location":"query","ui_level":"expert","description":"Include population type labels where supported."},
    ],
    "asylum_applications": list(POPULATION_PARAMS),
    "asylum_decisions": list(POPULATION_PARAMS),
    "solutions": list(POPULATION_PARAMS),
    "countries": [
        {"name":"limit","type":"integer","default":500,"minimum":1,"maximum":1000,"location":"query","ui_level":"advanced","description":"Rows requested."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Page."},
        {"name":"region","type":"string","default":"","max_length":120,"location":"query","ui_level":"advanced","description":"Region filter documented by UNHCR."},
        {"name":"unhcr_region","type":"string","default":"","max_length":120,"location":"query","ui_level":"advanced","description":"UNHCR region filter."},
    ],
    "regions": [
        {"name":"limit","type":"integer","default":500,"minimum":1,"maximum":1000,"location":"query","ui_level":"advanced","description":"Rows requested."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Page."},
    ],
    "years": [
        {"name":"limit","type":"integer","default":500,"minimum":1,"maximum":1000,"location":"query","ui_level":"advanced","description":"Rows requested."},
        {"name":"page","type":"integer","default":1,"minimum":1,"maximum":10000,"location":"query","ui_level":"advanced","description":"Page."},
    ],
}

UNHCR_DESCRIPTOR = ProviderDescriptor(
    provider_id="unhcr",
    name="UNHCR Refugee Statistics API",
    api_version="v1",
    base_url="https://api.unhcr.org/population/v1",
    content_types=("population","demographics","asylum_applications","asylum_decisions","solutions","countries","regions","years"),
    operations=tuple(ProviderOperationDescriptor(name, name, ("GET",)) for name in PARAMETER_CONTRACTS),
    parameters=tuple(sorted({row["name"] for rows in PARAMETER_CONTRACTS.values() for row in rows})),
    configuration=(ProviderConfigField("cf_type", "string", ConfigVisibility.PUBLIC, required=True, default="ISO", project_override=True, description="Country filter type used by qualified HDP semantic routing."),),
    capabilities=(
        ProviderCapability("population_statistics", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("demographics", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("asylum_statistics", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("solutions", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("country_region_year_vocabularies", "native", OFFICIAL_EVIDENCE),
        ProviderCapability("origin_asylum_role_separation", "hdp_verified", OFFICIAL_EVIDENCE),
    ),
    evidence=OFFICIAL_EVIDENCE,
    runtime_limits={"semantic_cf_type":"ISO", "semantic_geography_roles":["origin","asylum"]},
    metadata={
        "evidence_status":"DOCUMENTED",
        "parameter_contracts":PARAMETER_CONTRACTS,
        "semantic_operation":"population",
        "nomenclatures":{"countries":"/population/v1/countries/", "regions":"/population/v1/regions/", "years":"/population/v1/years/"},
        "known_documented_not_yet_qualified":["provider endpoints or optional filters not represented in the published v1 operation set above"],
        "scope_note":"Generic geography is intentionally executed as separate country-of-origin and country-of-asylum requests so population roles are never silently conflated.",
    },
)
