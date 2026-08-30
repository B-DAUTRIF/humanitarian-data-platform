# HDP V6.0.0 — Inventaire des paramètres API

Cet inventaire est généré sans flux compressé opaque. Il combine les schémas de configuration réellement utilisés par HDP, les paramètres natifs documentés des opérations de recherche/acquisition et, lorsqu'elle est disponible au moment de la construction, la spécification OpenAPI/Swagger du fournisseur.

Les paramètres `supported=false` restent visibles dans l'interface comme informations classées. Ils ne sont jamais présentés comme fonctionnels tant qu'un adaptateur et ses tests ne les prennent pas en charge.

**Total : 1020 entrées · 10 sources.**

## État des spécifications machine

| Source | État | URL | Paramètres extraits |
|---|---|---|---:|
| HDX / CKAN | n/a |  | 0 |
| ReliefWeb | n/a |  | 0 |
| WHO Global Health Observatory | n/a |  | 0 |
| World Bank Health Indicators | n/a |  | 0 |
| UNICEF Data Warehouse (SDMX) | n/a |  | 0 |
| UN Global SDG Indicators Database | loaded | https://unstats.un.org/SDGAPI/swagger/v1/swagger.json | 191 |
| DHS Program Indicator Data | not_found |  | 0 |
| HDX Humanitarian API (HAPI) | loaded | https://hapi.humdata.org/openapi.json | 359 |
| UNHCR Refugee Statistics | not_found |  | 0 |
| GDACS | loaded | https://www.gdacs.org/gdacsapi/swagger/v1/swagger.json | 229 |

## HDX / CKAN

26 entrées cataloguées, dont 22 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | catalog_action | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | ckan_api_version | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://data.humdata.org/api/3/action/package_search | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | fq | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | sort | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://data.humdata.org/api/3/action/package_search | start | interface projet | integer | champ numérique | oui | source_registry:project |
| package_search | GET | /api/3/action/package_search | fq | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | fq_list | query | array | information en lecture seule | information | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | q | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | qf | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | rows | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | sort | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| package_search | GET | /api/3/action/package_search | start | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |

## ReliefWeb

33 entrées cataloguées, dont 25 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | application_identifier_source | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | resource_type | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.reliefweb.int/v2/reports | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | offset | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | preset | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | profile | interface projet | string | liste de sélection | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.reliefweb.int/v2/reports | sort | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| reports | GET/POST | /v2/reports | appname | query | string | secret / variable d’environnement | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | facets | query/body | array/object | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | fields[exclude] | query/body | array | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | fields[include] | query/body | array | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | filter | query/body | object | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | limit | query/body | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | offset | query/body | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | preset | query/body | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | profile | query/body | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | query[fields] | query/body | array | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | query[operator] | query/body | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | query[value] | query/body | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| reports | GET/POST | /v2/reports | sort[] | query/body | array/string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |

## WHO Global Health Observatory

26 entrées cataloguées, dont 20 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | indicator_catalog | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | protocol_profile | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://ghoapi.azureedge.net/api/Indicator | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| OData query | GET | /api/{entity} | $count | query | boolean | information en lecture seule | information | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $expand | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $filter | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $format | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $orderby | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $select | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $skip | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| OData query | GET | /api/{entity} | $top | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | catalog_top | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://ghoapi.azureedge.net/api/Indicator | skip | interface projet | integer | champ numérique | oui | source_registry:project |

## World Bank Health Indicators

33 entrées cataloguées, dont 25 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | api_version | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | indicator_source_id | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.worldbank.org/v2/source/2/indicator | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Indicator data | GET | /v2/country/{country}/indicator/{indicator} | country | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Indicator data | GET | /v2/country/{country}/indicator/{indicator} | indicator | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{language}/{resource} | language | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | date | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | downloadformat | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | footnote | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | format | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | frequency | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | gapfill | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | mrnev | query | integer | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | mrv | query | integer | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | page | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | per_page | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| Indicators API v2 | GET | /v2/{resource} | source | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | catalog_page_size | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | language | interface projet | string | liste de sélection | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | page | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.worldbank.org/v2/source/2/indicator | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |

## UNICEF Data Warehouse (SDMX)

33 entrées cataloguées, dont 25 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | sdmx_context | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | structure_resource | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | agency | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | dataflow | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | detail | interface projet | string | liste de sélection | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | references | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://sdmx.data.unicef.org/ws/public/sdmxapi/rest | version | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| SDMX REST | GET | /* | detail | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| SDMX REST | GET | /* | format | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| SDMX REST | GET | /* | references | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| SDMX data | GET | /data/* | dimension_at_observation | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| SDMX data | GET | /data/* | endPeriod | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| SDMX data | GET | /data/* | firstNObservations | query | integer | information en lecture seule | information | provider documentation / curated V6 baseline |
| SDMX data | GET | /data/* | lastNObservations | query | integer | information en lecture seule | information | provider documentation / curated V6 baseline |
| SDMX data | GET | /data/* | startPeriod | query | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| data/dataflow | GET | /data/{agency},{dataflow},{version}/{dataQuery} | dataQuery | path | string | information en lecture seule | information | provider documentation / curated V6 baseline |
| dataflow | GET | /dataflow/{agency}/{dataflow}/{version}/ | agency | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| dataflow | GET | /dataflow/{agency}/{dataflow}/{version}/ | dataflow | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| dataflow | GET | /dataflow/{agency}/{dataflow}/{version}/ | version | path | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |

## UN Global SDG Indicators Database

210 entrées cataloguées, dont 14 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | api_version | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | catalog_resource | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Indicator/List | GET | /v1/sdg/Indicator/List | goal | query | array/string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicator/List | GET | /v1/sdg/Indicator/List | indicator | query | array/string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Indicator/List | GET | /v1/sdg/Indicator/List | target | query | array/string | information en lecture seule | information | provider documentation / curated V6 baseline |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| V1SdgCompareTrendsGetAreaBySeriesDisaggregationDimensionsPost | POST | /v1/sdg/CompareTrends/GetAreaBySeriesDisaggregationDimensions | methodologyType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetAreaBySeriesDisaggregationDimensionsPost | POST | /v1/sdg/CompareTrends/GetAreaBySeriesDisaggregationDimensions | series | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataMultiSeriesOneAreaPost | POST | /v1/sdg/CompareTrends/GetDataMultiSeriesOneArea | areaCode | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataMultiSeriesOneAreaPost | POST | /v1/sdg/CompareTrends/GetDataMultiSeriesOneArea | fromPeriod | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataMultiSeriesOneAreaPost | POST | /v1/sdg/CompareTrends/GetDataMultiSeriesOneArea | methodologyType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataMultiSeriesOneAreaPost | POST | /v1/sdg/CompareTrends/GetDataMultiSeriesOneArea | series | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataMultiSeriesOneAreaPost | POST | /v1/sdg/CompareTrends/GetDataMultiSeriesOneArea | toPeriod | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | areaCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | disaggregatedCategory | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | fromPeriod | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | methodologyType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | series | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetDataOneSeriesMultiAreaPost | POST | /v1/sdg/CompareTrends/GetDataOneSeriesMultiArea | toPeriod | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetSeriesDisaggregationDimensionsByAreaPost | POST | /v1/sdg/CompareTrends/GetSeriesDisaggregationDimensionsByArea | areaCode | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgCompareTrendsGetSeriesDisaggregationDimensionsByAreaPost | POST | /v1/sdg/CompareTrends/GetSeriesDisaggregationDimensionsByArea | methodologyType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCompareacrossgoalDataPost | POST | /v1/sdg/DataAvailability/GetCompareacrossgoalData | Goals | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCompareacrossgoalDataPost | POST | /v1/sdg/DataAvailability/GetCompareacrossgoalData | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCompareacrossgoalDataPost | POST | /v1/sdg/DataAvailability/GetCompareacrossgoalData | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCountriesAcrossGoalsPost | POST | /v1/sdg/DataAvailability/GetCountriesAcrossGoals | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCountriesAcrossGoalsPost | POST | /v1/sdg/DataAvailability/GetCountriesAcrossGoals | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetCountriesAcrossGoalsPost | POST | /v1/sdg/DataAvailability/GetCountriesAcrossGoals | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetGoalsDisaggregatedDataPost | POST | /v1/sdg/DataAvailability/GetGoalsDisaggregatedData | areaCode | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetGoalsDisaggregatedDataPost | POST | /v1/sdg/DataAvailability/GetGoalsDisaggregatedData | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetGoalsDisaggregatedDataPost | POST | /v1/sdg/DataAvailability/GetGoalsDisaggregatedData | disaggregationType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetGoalsDisaggregatedDataPost | POST | /v1/sdg/DataAvailability/GetGoalsDisaggregatedData | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetIndicatorsAllCountriesPost | POST | /v1/sdg/DataAvailability/GetIndicatorsAllCountries | countryId | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetIndicatorsAllCountriesPost | POST | /v1/sdg/DataAvailability/GetIndicatorsAllCountries | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetIndicatorsAllCountriesPost | POST | /v1/sdg/DataAvailability/GetIndicatorsAllCountries | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAggregationsForMapsPost | POST | /v1/sdg/DataAvailability/GetSeriesAggregationsForMaps | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAggregationsForMapsPost | POST | /v1/sdg/DataAvailability/GetSeriesAggregationsForMaps | goalId | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAggregationsForMapsPost | POST | /v1/sdg/DataAvailability/GetSeriesAggregationsForMaps | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAndDisAggregationsForGoalsPost | POST | /v1/sdg/DataAvailability/GetSeriesAndDisAggregationsForGoals | areaCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAndDisAggregationsForGoalsPost | POST | /v1/sdg/DataAvailability/GetSeriesAndDisAggregationsForGoals | dataPoints | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAndDisAggregationsForGoalsPost | POST | /v1/sdg/DataAvailability/GetSeriesAndDisAggregationsForGoals | disaggregationType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAndDisAggregationsForGoalsPost | POST | /v1/sdg/DataAvailability/GetSeriesAndDisAggregationsForGoals | goalId | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetSeriesAndDisAggregationsForGoalsPost | POST | /v1/sdg/DataAvailability/GetSeriesAndDisAggregationsForGoals | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetWorldbyGoalPost | POST | /v1/sdg/DataAvailability/GetWorldbyGoal | dataPointType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgDataAvailabilityGetWorldbyGoalPost | POST | /v1/sdg/DataAvailability/GetWorldbyGoal | natureOfData | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | email | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | feedbackDescription | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | feedbackPage | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | feedbackType | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | firstName | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgFeedbackAddFeedbackPost | POST | /v1/sdg/Feedback/AddFeedback | lastName | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGeoAreaByGeoAreaCodeListGet | GET | /v1/sdg/GeoArea/{GeoAreaCode}/List | geoAreaCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | releaseCode | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetGlobalDataBasePost | POST | /v1/sdg/GlobalAndRegional/GetGlobalDataBase | seriesCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetMultiSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetMultiSeries | areaCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetMultiSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetMultiSeries | indicators | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetMultiSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetMultiSeries | seriesCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetMultiSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetMultiSeries | years | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetSingleSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetSingleSeries | areaCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetSingleSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetSingleSeries | indicators | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetSingleSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetSingleSeries | seriesCode | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGlobalAndRegionalGetSingleSeriesPost | POST | /v1/sdg/GlobalAndRegional/GetSingleSeries | years | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalByGoalCodeAttributesGet | GET | /v1/sdg/Goal/{goalCode}/Attributes | goalCode | path | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalByGoalCodeDimensionsGet | GET | /v1/sdg/Goal/{goalCode}/Dimensions | goalCode | path | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalByGoalCodeGeoAreasGet | GET | /v1/sdg/Goal/{goalCode}/GeoAreas | goalCode | path | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalByGoalCodeTargetListGet | GET | /v1/sdg/Goal/{goalCode}/Target/List | goalCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalByGoalCodeTargetListGet | GET | /v1/sdg/Goal/{goalCode}/Target/List | includechildren | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataCSVPost | POST | /v1/sdg/Goal/DataCSV | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataCSVPost | POST | /v1/sdg/Goal/DataCSV | goal | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataCSVPost | POST | /v1/sdg/Goal/DataCSV | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataCSVPost | POST | /v1/sdg/Goal/DataCSV | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataExcelPost | POST | /v1/sdg/Goal/DataExcel | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataExcelPost | POST | /v1/sdg/Goal/DataExcel | goal | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataExcelPost | POST | /v1/sdg/Goal/DataExcel | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataExcelPost | POST | /v1/sdg/Goal/DataExcel | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | goal | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | timePeriod | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | timePeriodEnd | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalDataGet | GET | /v1/sdg/Goal/Data | timePeriodStart | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalListGet | GET | /v1/sdg/Goal/List | includechildren | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalPivotDataGet | GET | /v1/sdg/Goal/PivotData | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalPivotDataGet | GET | /v1/sdg/Goal/PivotData | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalPivotDataGet | GET | /v1/sdg/Goal/PivotData | goal | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalPivotDataGet | GET | /v1/sdg/Goal/PivotData | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgGoalPivotDataGet | GET | /v1/sdg/Goal/PivotData | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorByIndicatorCodeGeoAreasGet | GET | /v1/sdg/Indicator/{indicatorCode}/GeoAreas | indicatorcode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorByIndicatorCodeSeriesListGet | GET | /v1/sdg/Indicator/{indicatorCode}/Series/List | indicatorcode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | indicator | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | timePeriod | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | timePeriodEnd | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorDataGet | GET | /v1/sdg/Indicator/Data | timePeriodStart | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorPivotDataGet | GET | /v1/sdg/Indicator/PivotData | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorPivotDataGet | GET | /v1/sdg/Indicator/PivotData | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorPivotDataGet | GET | /v1/sdg/Indicator/PivotData | indicator | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorPivotDataGet | GET | /v1/sdg/Indicator/PivotData | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgIndicatorPivotDataGet | GET | /v1/sdg/Indicator/PivotData | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSDMXMetadataGetSDMXMetaDataPost | POST | /v1/sdg/SDMXMetadata/GetSDMXMetaData | conceptIds | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSDMXMetadataGetSDMXMetaDataPost | POST | /v1/sdg/SDMXMetadata/GetSDMXMetaData | serieses | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSDMXMetadataGetSDMXMetaDataPost | POST | /v1/sdg/SDMXMetadata/GetSDMXMetaData | sort | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySerieCodeListGet | GET | /v1/sdg/Series/{serieCode}/List | allreleases | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySerieCodeListGet | GET | /v1/sdg/Series/{serieCode}/List | serieCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySerieCodeListGet | GET | /v1/sdg/Series/{serieCode}/List | seriesCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeAttributesGet | GET | /v1/sdg/Series/{seriesCode}/Attributes | seriesCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeDimensionsGet | GET | /v1/sdg/Series/{seriesCode}/Dimensions | seriesCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeGeoAreaByGeoAreaCodeDataSliceGet | GET | /v1/sdg/Series/{seriesCode}/GeoArea/{geoAreaCode}/DataSlice | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeGeoAreaByGeoAreaCodeDataSliceGet | GET | /v1/sdg/Series/{seriesCode}/GeoArea/{geoAreaCode}/DataSlice | geoAreaCode | path | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeGeoAreaByGeoAreaCodeDataSliceGet | GET | /v1/sdg/Series/{seriesCode}/GeoArea/{geoAreaCode}/DataSlice | seriesCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeGeoAreaByGeoAreaCodeDataSliceGet | GET | /v1/sdg/Series/{seriesCode}/GeoArea/{geoAreaCode}/DataSlice | timePeriods | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesBySeriesCodeGeoAreasGet | GET | /v1/sdg/Series/{seriesCode}/GeoAreas | seriesCode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCSVPost | POST | /v1/sdg/Series/DataCSV | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCSVPost | POST | /v1/sdg/Series/DataCSV | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCSVPost | POST | /v1/sdg/Series/DataCSV | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCSVPost | POST | /v1/sdg/Series/DataCSV | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCountPost | POST | /v1/sdg/Series/DataCount | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCountPost | POST | /v1/sdg/Series/DataCount | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCountPost | POST | /v1/sdg/Series/DataCount | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataCountPost | POST | /v1/sdg/Series/DataCount | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataExcelPost | POST | /v1/sdg/Series/DataExcel | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataExcelPost | POST | /v1/sdg/Series/DataExcel | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataExcelPost | POST | /v1/sdg/Series/DataExcel | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataExcelPost | POST | /v1/sdg/Series/DataExcel | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | releaseCode | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | seriesCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | timePeriod | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | timePeriodEnd | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesDataGet | GET | /v1/sdg/Series/Data | timePeriodStart | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | comments | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | email | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | firstname | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | lastname | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataCSVPost | POST | /v1/sdg/Series/EmailDataCSV | usertype | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | comments | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | email | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | firstname | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | lastname | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesEmailDataExcelPost | POST | /v1/sdg/Series/EmailDataExcel | usertype | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesGeoAreaCodePost | POST | /v1/sdg/Series/GeoAreaCode | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesListGet | GET | /v1/sdg/Series/List | allreleases | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataExcelPost | POST | /v1/sdg/Series/PivotDataExcel | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataExcelPost | POST | /v1/sdg/Series/PivotDataExcel | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataExcelPost | POST | /v1/sdg/Series/PivotDataExcel | timePeriodEnd | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataExcelPost | POST | /v1/sdg/Series/PivotDataExcel | timePeriodStart | formData | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | releaseCode | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataGet | GET | /v1/sdg/Series/PivotData | seriesCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | areaCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | dimensions | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | page | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | pageSize | formData | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | releaseCode | formData | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesPivotDataPost | POST | /v1/sdg/Series/PivotData | seriesCode | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesTimePeriodsPost | POST | /v1/sdg/Series/TimePeriods | areaCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgSeriesTimePeriodsPost | POST | /v1/sdg/Series/TimePeriods | seriesCodes | formData | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetByTargetCodeGeoAreasGet | GET | /v1/sdg/Target/{targetCode}/GeoAreas | targetcode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetByTargetCodeIndicatorListGet | GET | /v1/sdg/Target/{targetCode}/Indicator/List | includechildren | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetByTargetCodeIndicatorListGet | GET | /v1/sdg/Target/{targetCode}/Indicator/List | targetcode | path | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | target | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | timePeriod | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | timePeriodEnd | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetDataGet | GET | /v1/sdg/Target/Data | timePeriodStart | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetListGet | GET | /v1/sdg/Target/List | includechildren | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetPivotDataGet | GET | /v1/sdg/Target/PivotData | areaCode | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetPivotDataGet | GET | /v1/sdg/Target/PivotData | dimensions | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetPivotDataGet | GET | /v1/sdg/Target/PivotData | page | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetPivotDataGet | GET | /v1/sdg/Target/PivotData | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgTargetPivotDataGet | GET | /v1/sdg/Target/PivotData | target | query | array | information en lecture seule | information | provider OpenAPI/Swagger |
| V1SdgUserEmailExistGet | GET | /v1/sdg/User/EmailExist | email | query | string | information en lecture seule | information | provider OpenAPI/Swagger |

## DHS Program Indicator Data

31 entrées cataloguées, dont 27 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | api_resource | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | data_scope | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.dhsprogram.com/rest/dhs/indicators | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | breakdown | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | catalog_page_size | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | country_ids | interface projet | array | liste / sélection multiple | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | indicator_ids | interface projet | array | liste / sélection multiple | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | page | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.dhsprogram.com/rest/dhs/indicators | survey_years | interface projet | array | liste / sélection multiple | oui | source_registry:project |
| data | GET | /rest/dhs/data | breakdown | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| data | GET | /rest/dhs/data | countryIds | query | array/string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| data | GET | /rest/dhs/data | indicatorIds | query | array/string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| data | GET | /rest/dhs/data | surveyIds | query | array/string | information en lecture seule | information | provider documentation / curated V6 baseline |
| data | GET | /rest/dhs/data | surveyType | query | array/string | information en lecture seule | information | provider documentation / curated V6 baseline |
| data | GET | /rest/dhs/data | surveyYears | query | array/integer | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| indicators | GET | /rest/dhs/indicators | f | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| indicators | GET | /rest/dhs/indicators | page | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| indicators | GET | /rest/dhs/indicators | perpage | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |

## HDX Humanitarian API (HAPI)

385 entrées cataloguées, dont 24 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | api_version | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | application_identifier_source | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://hapi.humdata.org/api/v2 | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| HAPI data | GET | /api/v2/{endpoint} | admin_level | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| HAPI data | GET | /api/v2/{endpoint} | app_identifier | query/header | string | secret / variable d’environnement | oui | provider documentation / curated V6 baseline |
| HAPI data | GET | /api/v2/{endpoint} | limit | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| HAPI data | GET | /api/v2/{endpoint} | location_code | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| HAPI data | GET | /api/v2/{endpoint} | offset | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| HAPI data | GET | /api/v2/{endpoint} | output_format | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | admin_level | interface projet | integer | liste de sélection | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | endpoint | interface projet | string | liste de sélection | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | location_code | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | offset | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://hapi.humdata.org/api/v2 | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | location_ref | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin1_api_v2_metadata_admin1_get | GET | /api/v2/metadata/admin1 | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | admin1_ref | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | location_ref | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_admin2_api_v2_metadata_admin2_get | GET | /api/v2/metadata/admin2 | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | event_type | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_conflict_event_api_v2_coordination_context_conflict_events_get | GET | /api/v2/coordination-context/conflict-events | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_currency_api_v2_metadata_currency_get | GET | /api/v2/metadata/currency | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_currency_api_v2_metadata_currency_get | GET | /api/v2/metadata/currency | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_currency_api_v2_metadata_currency_get | GET | /api/v2/metadata/currency | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_currency_api_v2_metadata_currency_get | GET | /api/v2/metadata/currency | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_currency_api_v2_metadata_currency_get | GET | /api/v2/metadata/currency | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | category | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | hapi_updated_date_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | hapi_updated_date_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_data_availability_api_v2_metadata_data_availability_get | GET | /api/v2/metadata/data-availability | subcategory | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | dataset_hdx_id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | dataset_hdx_stub | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | dataset_hdx_title | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | hdx_provider_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | hdx_provider_stub | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_dataset_api_v2_metadata_dataset_get | GET | /api/v2/metadata/dataset | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_encoded_identifier_api_v2_encode_app_identifier_get | GET | /api/v2/encode_app_identifier | application | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_encoded_identifier_api_v2_encode_app_identifier_get | GET | /api/v2/encode_app_identifier | email | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | commodity_category | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | commodity_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | commodity_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | market_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | market_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | price_flag | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | price_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | price_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | price_type | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_price_api_v2_food_security_nutrition_poverty_food_prices_market_monitor_get | GET | /api/v2/food-security-nutrition-poverty/food-prices-market-monitor | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | ipc_phase | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | ipc_type | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_food_security_api_v2_food_security_nutrition_poverty_food_security_get | GET | /api/v2/food-security-nutrition-poverty/food-security | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | appeal_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | appeal_type | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_funding_api_v2_coordination_context_funding_get | GET | /api/v2/coordination-context/funding | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | category | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | population_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | population_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | population_status | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | sector_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | sector_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_humanitarian_needs_api_v2_affected_people_humanitarian_needs_get | GET | /api/v2/affected-people/humanitarian-needs | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_idps_api_v2_affected_people_idps_get | GET | /api/v2/affected-people/idps | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_location_api_v2_metadata_location_get | GET | /api/v2/metadata/location | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | coping_capacity_risk_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | coping_capacity_risk_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | global_rank_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | global_rank_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | hazard_exposure_risk_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | hazard_exposure_risk_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | overall_risk_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | overall_risk_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | risk_class | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | vulnerability_risk_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_national_risk_api_v2_coordination_context_national_risk_get | GET | /api/v2/coordination-context/national-risk | vulnerability_risk_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | org_acronym | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | org_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | sector_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | sector_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_operational_presence_api_v2_coordination_context_operational_presence_get | GET | /api/v2/coordination-context/operational-presence | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | acronym | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | org_type_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | org_type_description | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_api_v2_metadata_org_get | GET | /api/v2/metadata/org | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | description | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_org_type_api_v2_metadata_org_type_get | GET | /api/v2/metadata/org-type | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | age_range | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | gender | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | population_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | population_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_population_api_v2_geography_infrastructure_baseline_population_get | GET | /api/v2/geography-infrastructure/baseline-population | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | mpi_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | mpi_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_poverty_rate_api_v2_food_security_nutrition_poverty_poverty_rate_get | GET | /api/v2/food-security-nutrition-poverty/poverty-rate | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | aggregation_period | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_rainfall_api_v2_climate_rainfall_get | GET | /api/v2/climate/rainfall | version | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | age_range | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | asylum_has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | asylum_in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | asylum_location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | asylum_location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | gender | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | origin_has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | origin_in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | origin_location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | origin_location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | population_group | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | population_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | population_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_refugees_api_v2_affected_people_refugees_persons_of_concern_get | GET | /api/v2/affected-people/refugees-persons-of-concern | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | dataset_hdx_id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | dataset_hdx_provider_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | dataset_hdx_provider_stub | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | dataset_hdx_stub | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | dataset_hdx_title | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | is_hxl | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | resource_hdx_id | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | update_date_max | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_resources_api_v2_metadata_resource_get | GET | /api/v2/metadata/resource | update_date_min | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | age_range | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | asylum_has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | asylum_in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | asylum_location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | asylum_location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | end_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | gender | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | max_age | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | min_age | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | origin_has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | origin_in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | origin_location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | origin_location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | population_group | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_returnees_api_v2_affected_people_returnees_get | GET | /api/v2/affected-people/returnees | start_date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_sector_api_v2_metadata_sector_get | GET | /api/v2/metadata/sector | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | category | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_commodities_api_v2_metadata_wfp_commodity_get | GET | /api/v2/metadata/wfp-commodity | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | admin1_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | admin1_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | admin2_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | admin2_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | admin_level | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | app_identifier | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | has_hrp | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | in_gho | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | location_code | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | location_name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | name | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | offset | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| get_wfp_market_api_v2_metadata_wfp_market_get | GET | /api/v2/metadata/wfp-market | output_format | query | string | information en lecture seule | information | provider OpenAPI/Swagger |

## UNHCR Refugee Statistics

28 entrées cataloguées, dont 26 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | api_version | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | country_reference | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://api.unhcr.org/population/v1/population/ | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | country_of_asylum | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | country_of_origin | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | page | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | year_from | interface projet | integer | champ numérique | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://api.unhcr.org/population/v1/population/ | year_to | interface projet | integer | champ numérique | oui | source_registry:project |
| population | GET | /population/v1/population/ | cf_type | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | coa | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | coo | query | string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | limit | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | page | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | yearFrom | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |
| population | GET | /population/v1/population/ | yearTo | query | integer | champ numérique | oui | provider documentation / curated V6 baseline |

## GDACS

215 entrées cataloguées, dont 20 directement prises en charge par HDP.

| Opération | Méthode | Endpoint | Paramètre | Emplacement | Type | UI | Pris en charge | Origine |
|---|---|---|---|---|---|---|---|---|
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | accept_language | configuration globale | string | liste de sélection | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | alerting_policy | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | backoff_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | connect_timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | enabled | configuration globale | boolean | case à cocher | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | max_response_bytes | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | response_profile | configuration globale | string | information en lecture seule | information | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | retry_count | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | timeout_seconds | configuration globale | integer | champ numérique | oui | source_registry:global |
| Configuration globale HDP | CONFIG | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | user_agent | configuration globale | string | champ texte / mots-clés | oui | source_registry:global |
| Download the document specified by oid | GET | /api/admin/Documents/download | oid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Download the document specified by oid | GET | /api/admin/Documents/download | type | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Documents by GDACS Eventkey | GET | /api/admin/Documents/getdocumentsbyevent | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Documents by GDACS Eventkey | GET | /api/admin/Documents/getdocumentsbyevent | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Documents by text | GET | /api/admin/Documents/getdocumentsbytext | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Documents by text | GET | /api/admin/Documents/getdocumentsbytext | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Documents by text | GET | /api/admin/Documents/getdocumentsbytext | textvalue | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat all collection data | GET | /api/Emdat/getemdatlist | PageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat all collection data | GET | /api/Emdat/getemdatlist | PageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat collection data by event key | GET | /api/Emdat/getemdatbyeventkey | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat collection data by event key | GET | /api/Emdat/getemdatbyeventkey | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat data by Iso3 | GET | /api/Emdat/getemdatbyiso3 | iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat data by Iso3 list | GET | /api/Emdat/getemdatbyiso3list | iso3list | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emdat data by disanter number | GET | /api/Emdat/getemdatbydisno | disno | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emmnews collection data by key eventtype,eventid specifying the limit object to return | GET | /api/Emm/getemmnewsbykey | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emmnews collection data by key eventtype,eventid specifying the limit object to return | GET | /api/Emm/getemmnewsbykey | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Emmnews collection data by key eventtype,eventid specifying the limit object to return | GET | /api/Emm/getemmnewsbykey | limit | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Event data specified by eventtype and eventid | GET | /api/Events/geteventdata | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Event data specified by eventtype and eventid | GET | /api/Events/geteventdata | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Event data specified by eventtype and eventid | GET | /api/Events/geteventdata | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get GTS data by key | GET | /api/Gts/getdatabykey | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get GTS data by key | GET | /api/Gts/getdatabykey | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get GTS data by period | GET | /api/Gts/getdatabyperiod | fromdate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get GTS data by period | GET | /api/Gts/getdatabyperiod | todate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 0 by Iso3 | GET | /api/Administrative/gadm0byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 1 by Iso3 | GET | /api/Administrative/gadm1byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 2 by GID.1 code of gadm level 1 | GET | /api/Administrative/gadm2bygid1 | Gid1 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 2 by Iso3 | GET | /api/Administrative/gadm2byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 3 by GID.1 code of gadm level 1 | GET | /api/Administrative/gadm3bygid1 | Gid1 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 3 by GID.2 code of gadm level 2 | GET | /api/Administrative/gadm3bygid2 | Gid2 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 3 by Iso3 | GET | /api/Administrative/gadm3byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 4 by GID.1 code of gadm level 1 | GET | /api/Administrative/gadm4bygid1 | Gid1 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 4 by GID.2 code of gadm level 2 | GET | /api/Administrative/gadm4bygid2 | Gid2 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 4 by GID.3 code of gadm level 3 | GET | /api/Administrative/gadm4bygid3 | Gid3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 4 by Iso3 | GET | /api/Administrative/gadm4byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 5 by GID.1 code of gadm level 1 | GET | /api/Administrative/gadm5bygid1 | Gid1 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 5 by GID.3 code of gadm level 2 | GET | /api/Administrative/gadm5bygid2 | Gid2 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 5 by GID.3 code of gadm level 3 | GET | /api/Administrative/gadm5bygid3 | Gid3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 5 by GID.4 code of gadm level 4 | GET | /api/Administrative/gadm5bygid4 | Gid4 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Gadm at level 5 by Iso3 | GET | /api/Administrative/gadm5byiso3 | Iso3 | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Nuclear Power Plant by event keys eventtype, eventid and source | GET | /api/Events/getnpp | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Nuclear Power Plant by event keys eventtype, eventid and source | GET | /api/Events/getnpp | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Nuclear Power Plant by event keys eventtype, eventid and source | GET | /api/Events/getnpp | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata | radiusKm | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata_area | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Seismic activity in a buffer having the radius specified around the volcano position in a period indicated | GET | /api/Volcano/getseismicdata_area | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Statistic EMM data by key eventtype,eventid | GET | /api/Emm/getemmnewsstatisticbykey | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Statistic EMM data by key eventtype,eventid | GET | /api/Emm/getemmnewsstatisticbykey | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Statistic EMM data by key eventtype,eventid | GET | /api/Emm/getemmnewsstatisticbykey | keywords | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get The News related to the event indicated by gdacs key | GET | /api/News/getnewsbygdacskey | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get The News related to the event indicated by gdacs key | GET | /api/News/getnewsbygdacskey | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mirova data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmirovadata | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mirova data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmirovadata | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mirova data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmirovadata | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mount data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmountdata | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mount data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmountdata | sourcecode | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mount data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmountdata | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volacano additional mount data for te volcano specified volcano position in a period indicated | GET | /api/VolcanoAdditional/getmountdata | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcano position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoinfo | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcano position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoinfo | radiusKm | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcano position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoinfo | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcano position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoinfo | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcanoes position and basic info in a specified radius | GET | /api/Volcano/getvolcanoesinfoinperiod | active | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcanoes position and basic info in a specified radius | GET | /api/Volcano/getvolcanoesinfoinperiod | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcanoes position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoesinfo | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcanoes position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoesinfo | radiusKm | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| Get Volcanoes position and related seismic activities in a specified radius in the period indicated | GET | /api/Volcano/getvolcanoesinfo | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episode specified by keywords eventtype,eventid,episodeid and source | GET | /api/Events/getepisodealertlevel | episodeid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episode specified by keywords eventtype,eventid,episodeid and source | GET | /api/Events/getepisodealertlevel | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episode specified by keywords eventtype,eventid,episodeid and source | GET | /api/Events/getepisodealertlevel | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episode specified by keywords eventtype,eventid,episodeid and source | GET | /api/Events/getepisodealertlevel | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episodes specified by keywords eventtype and eventid. | GET | /api/Events/geteventalertlevel | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of alertlevels calculated for episodes specified by keywords eventtype and eventid. | GET | /api/Events/geteventalertlevel | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of last 6 month events ordered by date descending and specifying the paging and the query filter based on eventid or alertlevel or eventtype | GET | /api/Events/geteventlist/allpaging | PageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of last 6 month events ordered by date descending and specifying the paging and the query filter based on eventid or alertlevel or eventtype | GET | /api/Events/geteventlist/allpaging | PageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a list of last 6 month events ordered by date descending and specifying the paging and the query filter based on eventid or alertlevel or eventtype | GET | /api/Events/geteventlist/allpaging | Query | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a tag Html events to show in Gdacs_App | GET | /api/Events/geteventdataapp | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a tag Html events to show in Gdacs_App | GET | /api/Events/geteventdataapp | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get a tag Html events to show in Gdacs_App | GET | /api/Events/geteventdataapp | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get affected locations by internal id related to Events that need impact analysis (Earthquake, Tropical Cyclones, Volcanoes, ForestFire) | GET | /api/Export/getaffectedlocations | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get events' list to show in the homepage's map by the eventtype specified in the parameter | GET | /api/Events/geteventlist/map | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the  AdaptiveCard  by parameters | GET | /api/AdaptiveCard/getevent/card | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the  AdaptiveCard  by parameters | GET | /api/AdaptiveCard/getevent/card | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the AOI information related to Eartquakes and Tropical Cyclones by internal id | GET | /api/Export/getaoi | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Copernicus AOIs by key | GET | /api/CopernicusActivation/getcopernicusaoi | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Copernicus AOIs by key | GET | /api/CopernicusActivation/getcopernicusaoi | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Copernicus Observed by key | GET | /api/CopernicusActivation/getcopernicusobserved | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Copernicus Observed by key | GET | /api/CopernicusActivation/getcopernicusobserved | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Earthquake Shakemap details by internal id | GET | /api/Shakemap/getdetails | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Earthquake Shakemap geomtery by keys eventid and shakeid | GET | /api/Shakemap/getgeometry | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Earthquake Shakemap geomtery by keys eventid and shakeid | GET | /api/Shakemap/getgeometry | shakeid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Event data in a format adapted to social environment | GET | /api/Events/getstructure/forsocial | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Event data in a format adapted to social environment | GET | /api/Events/getstructure/forsocial | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Flood GFM Observed by key | GET | /api/FloodGfm/getfloodgfmwmsbykeys/bydate | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Flood GFM Observed by key | GET | /api/FloodGfm/getfloodgfmwmsbykeys/bydate | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Flood GFM Observed by key | GET | /api/FloodGfm/getfloodgfmwmsbykeys/bydate | referencedate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Locations data Related to Earthquake with Tsunami or Tropical Cyclones with stormsurge (tsunami/stormsurge affected) by internal id | GET | /api/Export/getlocations | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Overall Flood GFM Observed by key | GET | /api/FloodGfm/getfloodgfmwmsbykeys/overall | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Overall Flood GFM Observed by key | GET | /api/FloodGfm/getfloodgfmwmsbykeys/overall | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Shakemap geomtry by key | GET | /api/Vaac/getgeometry | volcanoid | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Shakemap geomtry by key | GET | /api/Vaac/getgeometrypop | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Smithsonian Volcano news by volcanoid | GET | /api/VolcanoSmithNews/getsmithsonianbyvolcanoid | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Tropical Cyclone MODELS detail by internal id | GET | /api/Cyclonesurge/getdetails | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Tropical cyclone timeline by internal id | GET | /api/Export/gettimeline | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the Vaac Bulletin text by internal id | GET | /api/Vaac/getvaacbulletintext | idbulletin | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacbulletin | fromdate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacbulletin | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacbulletin | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacbulletin | todate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacbulletin | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacdata | fromdate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacdata | todate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the VaacDatafor volcanoid specified in the period indicated | GET | /api/Vaac/getvaacdata | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the all id referred to a specific event | GET | /api/Export/getids | key | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the all id referred to a specific event | GET | /api/Export/getids | output | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the all id referred to a specific event | GET | /api/Export/getids | value | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the episode information by keywords eventtype, eventid, episodeid and source | GET | /api/Events/getepisodedata | episodeid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the episode information by keywords eventtype, eventid, episodeid and source | GET | /api/Events/getepisodedata | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the episode information by keywords eventtype, eventid, episodeid and source | GET | /api/Events/getepisodedata | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the episode information by keywords eventtype, eventid, episodeid and source | GET | /api/Events/getepisodedata | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the eventdata for AdaptiveCard | GET | /api/AdaptiveCard/getevent/data | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the eventdata for AdaptiveCard | GET | /api/AdaptiveCard/getevent/data | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the events' list based on geometry match in the last days | GET | /api/Events/geteventlist/eventsbyarea | days | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the events' list based on geometry match in the last days | GET | /api/Events/geteventlist/eventsbyarea | geometryArea | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the events' list to show in archive page | GET | /api/Events/geteventlist/archive | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the geometry AOI for cyclone | GET | /api/Polygons/getgeometry/aoi | episodeid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the geometry AOI for cyclone | GET | /api/Polygons/getgeometry/aoi | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the geometry AOI for cyclone | GET | /api/Polygons/getgeometry/aoi | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the geometry AOI for cyclone | GET | /api/Polygons/getgeometry/aoi | polygontype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the geometry AOI for cyclone | GET | /api/Polygons/getgeometry/aoi | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the impact analysis by internal id related to Events that need impact analysis (Earthquake, Tropical Cyclones, Volcanoes, ForestFire) | GET | /api/Export/getimpact | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the infoproduct dat by event key | GET | /Api/InfoProduct/getinfoproduct | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the infoproduct dat by event key | GET | /Api/InfoProduct/getinfoproduct | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | episodeid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | eventid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | eventtype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | polygontype | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | showBaseGeometry | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | showPreliminary | query | boolean | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the polygons geometry by keys eventtype, eventid, episodeid, polygontype | GET | /api/Polygons/getgeometry | source | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the population affected analysis for Shakemap or Cyclones MODELS impact by internal id | GET | /api/Export/getpopdense | id | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the single Smithsonian Volcano news by volcanoid and date | GET | /api/VolcanoSmithNews/getsmithsonianbykey | date | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Get the single Smithsonian Volcano news by volcanoid and date | GET | /api/VolcanoSmithNews/getsmithsonianbykey | volcanoid | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | alert_levels | interface projet | array | liste / sélection multiple | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | auto_download | interface projet | boolean | case à cocher | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | date_from | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | date_to | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | event_types | interface projet | array | liste / sélection multiple | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | location | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | query | interface projet | string | champ texte / mots-clés | oui | source_registry:project |
| Recherche / paramètres projet HDP | GET | https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH | result_limit | interface projet | integer | champ numérique | oui | source_registry:project |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | alertlevel | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | country | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/card | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | alertlevel | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | country | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/AdaptiveCard/geteventlist/data | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | alertlevel | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | country | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | datemodified | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/latest | severity | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | alertlevel | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | caller | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | country | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | pageNumber | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | pageSize | query | integer | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | severity | query | number | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/search | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/statistic | alertlevel | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/statistic | country | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/statistic | eventlist | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/statistic | fromDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Search a list of events by parameter, it returns the first 100 elements, it is possible to obtain record by paging specifying the page size and page number. The records are ordered by todate desc | GET | /api/Events/geteventlist/statistic | toDate | query | string | information en lecture seule | information | provider OpenAPI/Swagger |
| Update Storage Repository used by AI volcano | POST | /api/azurecontent/StaticData/updaterepository | containername | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by AI volcano | POST | /api/azurecontent/StaticData/updaterepository | content | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by AI volcano | POST | /api/azurecontent/StaticData/updaterepository | contentByte | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by AI volcano | POST | /api/azurecontent/StaticData/updaterepository | filename | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepository | containername | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepository | content | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepository | contentByte | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepository | filename | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepositorysync | containername | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepositorysync | content | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepositorysync | contentByte | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| Update Storage Repository used by GDACS Contecxt data | POST | /api/azurecontent/StaticData/updategenericrepositorysync | filename | body | string | information en lecture seule | information | provider OpenAPI requestBody |
| geteventlist/SEARCH | GET | /gdacsapi/api/events/geteventlist/SEARCH | alertlevel | query | array/string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| geteventlist/SEARCH | GET | /gdacsapi/api/events/geteventlist/SEARCH | eventlist | query | array/string | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| geteventlist/SEARCH | GET | /gdacsapi/api/events/geteventlist/SEARCH | fromDate | query | date | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
| geteventlist/SEARCH | GET | /gdacsapi/api/events/geteventlist/SEARCH | toDate | query | date | champ texte / mots-clés | oui | provider documentation / curated V6 baseline |
