from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable
from urllib.parse import quote

from .source_registry import enrich_source_catalog


SEARCHABLE_SOURCE_IDS = (
    "hdx",
    "reliefweb",
    "who-gho",
    "world-bank-health",
    "unicef-sdmx",
    "un-sdg",
    "dhs",
    "hdx-hapi",
    "unhcr",
    "gdacs",
)
SOURCE_PATTERN = "^(" + "|".join(SEARCHABLE_SOURCE_IDS) + ")$"


_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "hdx",
        "name": "HDX / CKAN",
        "organization": "OCHA",
        "category": "Humanitaire et santé",
        "geographic_scope": "Monde",
        "domains": ["urgences", "épidémies", "services de santé", "COD"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API CKAN publique",
        "portal_url": "https://data.humdata.org/",
        "api_url": "https://data.humdata.org/api/3/action/package_search",
        "documentation_url": "https://data.humdata.org/about/api",
        "notes": "Recherche de jeux et téléchargement des ressources publiées ; licences propres à chaque jeu.",
    },
    {
        "id": "reliefweb",
        "name": "ReliefWeb",
        "organization": "OCHA",
        "category": "Veille humanitaire",
        "geographic_scope": "Monde",
        "domains": ["épidémies", "urgences sanitaires", "rapports"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": True,
        "access": "API avec appname pré-approuvé",
        "portal_url": "https://reliefweb.int/",
        "api_url": "https://api.reliefweb.int/v2/reports",
        "documentation_url": "https://apidoc.reliefweb.int/",
        "notes": "RELIEFWEB_APPNAME doit être configuré dans .env ; seuls les fichiers référencés sont téléchargeables.",
    },
    {
        "id": "who-gho",
        "name": "WHO Global Health Observatory",
        "organization": "Organisation mondiale de la Santé",
        "category": "Indicateurs sanitaires",
        "geographic_scope": "194 États membres",
        "domains": ["mortalité", "morbidité", "systèmes de santé", "facteurs de risque"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API OData publique",
        "portal_url": "https://www.who.int/data/gho",
        "api_url": "https://ghoapi.azureedge.net/api",
        "documentation_url": "https://www.who.int/data/gho/info/gho-odata-api",
        "notes": "Recherche dans le catalogue d'indicateurs GHO ; les observations de l'indicateur sont proposées en JSON.",
    },
    {
        "id": "world-bank-health",
        "name": "World Bank Health Indicators",
        "organization": "Banque mondiale",
        "category": "Indicateurs sanitaires et développement",
        "geographic_scope": "Monde",
        "domains": ["santé", "nutrition", "population", "dépenses", "environnement"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "Indicators API v2 publique",
        "portal_url": "https://data.worldbank.org/topic/health",
        "api_url": "https://api.worldbank.org/v2/source/2/indicator",
        "documentation_url": "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation",
        "notes": "Recherche dans les métadonnées WDI ; téléchargement CSV/ZIP par indicateur.",
    },
    {
        "id": "unicef-sdmx",
        "name": "UNICEF Data Warehouse (SDMX)",
        "organization": "UNICEF",
        "category": "Santé de la mère et de l'enfant",
        "geographic_scope": "Monde",
        "domains": ["enfance", "nutrition", "vaccination", "WASH", "mortalité"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API SDMX publique",
        "portal_url": "https://data.unicef.org/",
        "api_url": "https://sdmx.data.unicef.org/ws/public/sdmxapi/rest",
        "documentation_url": "https://data.unicef.org/sdmx-api-documentation/",
        "notes": "Recherche dans les flux SDMX publiés ; les données du flux sont proposées en CSV.",
    },
    {
        "id": "un-sdg",
        "name": "UN Global SDG Indicators Database",
        "organization": "Division de statistique des Nations Unies",
        "category": "Indicateurs ODD",
        "geographic_scope": "Monde",
        "domains": ["santé ODD 3", "nutrition", "WASH", "inégalités", "déterminants"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API publique",
        "portal_url": "https://unstats.un.org/sdgs/dataportal",
        "api_url": "https://unstats.un.org/SDGAPI/v1/sdg",
        "documentation_url": "https://unstats.un.org/sdgapi/swagger/",
        "notes": "Recherche dans la liste officielle des indicateurs ODD ; extraction JSON des séries par indicateur.",
    },
    {
        "id": "dhs",
        "name": "DHS Program Indicator Data",
        "organization": "The DHS Program",
        "category": "Enquêtes démographiques et sanitaires",
        "geographic_scope": "Pays à revenu faible et intermédiaire",
        "domains": ["santé reproductive", "mortalité", "nutrition", "paludisme", "VIH"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API d'indicateurs publique ; microdonnées sur inscription",
        "portal_url": "https://dhsprogram.com/data/",
        "api_url": "https://api.dhsprogram.com/rest/dhs",
        "documentation_url": "https://api.dhsprogram.com/",
        "notes": "Le connecteur utilise les indicateurs agrégés ouverts. L'accès aux microdonnées DHS reste soumis à inscription et approbation.",
    },
    {
        "id": "hdx-hapi",
        "name": "HDX Humanitarian API (HAPI)",
        "organization": "OCHA Centre for Humanitarian Data",
        "category": "Indicateurs humanitaires normalisés",
        "geographic_scope": "Opérations humanitaires couvertes par HAPI",
        "domains": ["déplacements", "besoins", "financement", "sécurité alimentaire", "conflits", "population"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": False,
        "requires_auth": True,
        "access": "API publique avec identifiant d’application",
        "portal_url": "https://hapi.humdata.org/",
        "api_url": "https://hapi.humdata.org/api/v2",
        "documentation_url": "https://hdx-hapi.readthedocs.io/",
        "notes": "HAPI harmonise plusieurs domaines humanitaires. HDX_HAPI_APP_IDENTIFIER doit être configuré ; la fréquence dépend du sous-domaine.",
    },
    {
        "id": "unhcr",
        "name": "UNHCR Refugee Statistics",
        "organization": "UNHCR",
        "category": "Déplacements forcés",
        "geographic_scope": "Monde",
        "domains": ["réfugiés", "demandeurs d’asile", "déplacés internes", "apatridie", "retours"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API publique Refugee Data Finder",
        "portal_url": "https://www.unhcr.org/refugee-statistics/",
        "api_url": "https://api.unhcr.org/population/v1/population/",
        "documentation_url": "https://api.unhcr.org/docs/refugee-statistics.html",
        "notes": "Séries annuelles agrégées par pays d’origine et pays d’asile ; ne contient pas de données individuelles.",
    },
    {
        "id": "gdacs",
        "name": "GDACS",
        "organization": "Commission européenne / Nations Unies",
        "category": "Alertes et événements de catastrophe",
        "geographic_scope": "Monde",
        "domains": ["séismes", "inondations", "cyclones", "tsunamis", "volcans", "sécheresses", "feux"],
        "mode": "live_api",
        "searchable": True,
        "schedule_supported": True,
        "downloadable": True,
        "requires_auth": False,
        "access": "API GeoJSON publique",
        "portal_url": "https://www.gdacs.org/",
        "api_url": "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH",
        "documentation_url": "https://www.gdacs.org/gdacsapi/swagger/index.html",
        "notes": "Événements et niveaux d’alerte en temps quasi réel. HDP ne doit pas servir de canal d’alerte vitale.",
    },
    {
        "id": "who-mortality",
        "name": "WHO Mortality Database",
        "organization": "Organisation mondiale de la Santé",
        "category": "Mortalité par cause",
        "geographic_scope": "Monde",
        "domains": ["causes de décès", "mortalité", "CIM"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et exports officiels",
        "portal_url": "https://www.who.int/data/data-collection-tools/who-mortality-database",
        "api_url": None,
        "documentation_url": "https://www.who.int/data/data-collection-tools/who-mortality-database",
        "notes": "Référencée dans HDP ; aucun connecteur API public stable n'est affirmé.",
    },
    {
        "id": "who-don",
        "name": "WHO Disease Outbreak News",
        "organization": "Organisation mondiale de la Santé",
        "category": "Veille sur les flambées épidémiques",
        "geographic_scope": "Monde",
        "domains": ["flambées", "épidémies", "risques sanitaires", "situation reports"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail officiel",
        "portal_url": "https://www.who.int/emergencies/disease-outbreak-news",
        "api_url": None,
        "documentation_url": "https://www.who.int/emergencies/disease-outbreak-news",
        "notes": "Référencée sans scraping : aucune API publique stable n’est affirmée par HDP.",
    },
    {
        "id": "iom-dtm",
        "name": "IOM Displacement Tracking Matrix",
        "organization": "Organisation internationale pour les migrations",
        "category": "Mobilité et déplacements",
        "geographic_scope": "Pays et crises couverts par DTM",
        "domains": ["déplacements", "mobilité", "sites", "flux", "besoins multisectoriels"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": True,
        "access": "Portail ; API 3.0 sur clé d’abonnement",
        "portal_url": "https://dtm.iom.int/",
        "api_url": None,
        "documentation_url": "https://dtm.iom.int/data-and-analysis",
        "notes": "Le catalogue est référencé. Le connecteur reste désactivé tant qu’une clé et un contrat d’API 3.0 vérifié ne sont pas configurés.",
    },
    {
        "id": "who-glass",
        "name": "WHO GLASS",
        "organization": "Organisation mondiale de la Santé",
        "category": "Résistance aux antimicrobiens",
        "geographic_scope": "Monde",
        "domains": ["AMR", "usage des antimicrobiens", "surveillance"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Tableaux de bord et téléchargements officiels",
        "portal_url": "https://www.who.int/initiatives/glass",
        "api_url": None,
        "documentation_url": "https://www.who.int/initiatives/glass",
        "notes": "Référencée dans HDP ; l'automatisation est désactivée faute d'API publique stable documentée.",
    },
    {
        "id": "who-flunet",
        "name": "WHO FluNet / FluID",
        "organization": "Organisation mondiale de la Santé",
        "category": "Surveillance de la grippe",
        "geographic_scope": "Monde",
        "domains": ["grippe", "virologie", "syndromes respiratoires"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portails et exports CSV officiels",
        "portal_url": "https://www.who.int/tools/flunet",
        "api_url": None,
        "documentation_url": "https://www.who.int/teams/global-influenza-programme/surveillance-and-monitoring/influenza-surveillance-outputs",
        "notes": "Les exports officiels sont accessibles depuis le portail ; HDP ne dépend pas d'une URL de fichier susceptible de changer.",
    },
    {
        "id": "who-ghe",
        "name": "WHO Global Health Estimates",
        "organization": "Organisation mondiale de la Santé",
        "category": "Charge de morbidité",
        "geographic_scope": "Monde",
        "domains": ["mortalité", "DALY", "espérance de vie", "causes"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et fichiers officiels",
        "portal_url": "https://www.who.int/data/global-health-estimates",
        "api_url": None,
        "documentation_url": "https://www.who.int/data/global-health-estimates",
        "notes": "Source de référence distincte du catalogue GHO interrogeable.",
    },
    {
        "id": "unaids",
        "name": "UNAIDS AIDSinfo",
        "organization": "ONUSIDA",
        "category": "VIH/sida",
        "geographic_scope": "Monde",
        "domains": ["VIH", "traitement", "prévalence", "incidence", "financement"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et jeux téléchargeables",
        "portal_url": "https://aidsinfo.unaids.org/",
        "api_url": None,
        "documentation_url": "https://www.unaids.org/en/topic/data",
        "notes": "Référencée dans HDP ; les fichiers doivent être sélectionnés depuis le portail officiel.",
    },
    {
        "id": "ihme-ghdx",
        "name": "IHME Global Health Data Exchange",
        "organization": "Institute for Health Metrics and Evaluation",
        "category": "Catalogue de données sanitaires",
        "geographic_scope": "Monde",
        "domains": ["GBD", "mortalité", "morbidité", "enquêtes", "systèmes de santé"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": True,
        "access": "Catalogue ; conditions variables selon le jeu",
        "portal_url": "https://ghdx.healthdata.org/",
        "api_url": None,
        "documentation_url": "https://ghdx.healthdata.org/global-health-data-exchange",
        "notes": "HDP référence le catalogue ; certains téléchargements nécessitent un compte ou une acceptation de conditions.",
    },
    {
        "id": "unicef-mics",
        "name": "UNICEF Multiple Indicator Cluster Surveys",
        "organization": "UNICEF",
        "category": "Enquêtes ménages",
        "geographic_scope": "Plus de 100 pays",
        "domains": ["enfance", "santé maternelle", "nutrition", "WASH", "protection"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": True,
        "access": "Catalogue ; microdonnées sur inscription",
        "portal_url": "https://mics.unicef.org/surveys",
        "api_url": None,
        "documentation_url": "https://mics.unicef.org/",
        "notes": "Les résultats publiés sont consultables ; les microdonnées suivent la procédure d'accès MICS.",
    },
    {
        "id": "un-wpp",
        "name": "UN World Population Prospects",
        "organization": "Division de la population des Nations Unies",
        "category": "Démographie",
        "geographic_scope": "Monde",
        "domains": ["population", "fécondité", "mortalité", "migration", "projections"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et fichiers officiels",
        "portal_url": "https://population.un.org/wpp/",
        "api_url": None,
        "documentation_url": "https://population.un.org/wpp/",
        "notes": "Référentiel mondial de dénominateurs démographiques et projections.",
    },
    {
        "id": "global-health",
        "name": "Global.health",
        "organization": "Global.health",
        "category": "Données épidémiologiques ouvertes",
        "geographic_scope": "Monde",
        "domains": ["épidémies", "cas désagrégés", "agents pathogènes"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et jeux ouverts selon l'événement",
        "portal_url": "https://global.health/",
        "api_url": None,
        "documentation_url": "https://global.health/",
        "notes": "La disponibilité et le schéma varient selon l'événement ; aucun connecteur générique n'est activé.",
    },
    {
        "id": "worldpop",
        "name": "WorldPop Data Portal",
        "organization": "WorldPop, University of Southampton",
        "category": "Population et dénominateurs spatiaux",
        "geographic_scope": "Monde",
        "domains": ["population maillée", "démographie", "accessibilité", "vaccination"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail de données géospatiales",
        "portal_url": "https://hub.worldpop.org/",
        "api_url": None,
        "documentation_url": "https://www.worldpop.org/",
        "notes": "Source complémentaire pour les dénominateurs et analyses spatiales de santé.",
    },
    {
        "id": "owid-health",
        "name": "Our World in Data — Health",
        "organization": "Global Change Data Lab",
        "category": "Séries harmonisées et visualisations",
        "geographic_scope": "Monde",
        "domains": ["maladies", "mortalité", "vaccination", "facteurs de risque"],
        "mode": "reference_portal",
        "searchable": False,
        "schedule_supported": False,
        "downloadable": False,
        "requires_auth": False,
        "access": "Portail et téléchargements par graphique",
        "portal_url": "https://ourworldindata.org/health-meta",
        "api_url": None,
        "documentation_url": "https://docs.owid.io/projects/etl/api/",
        "notes": "Agrégateur secondaire utile pour l'exploration ; vérifier la source primaire et la licence de chaque série.",
    },
)


def source_catalog() -> list[dict[str, Any]]:
    return enrich_source_catalog(deepcopy(list(_SOURCES)))


def source_by_id(source_id: str) -> dict[str, Any]:
    for source in _SOURCES:
        if source["id"] == source_id:
            return deepcopy(source)
    raise ValueError(f"Source inconnue : {source_id}")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("fr", "en", "FR", "EN", "value", "label", "name"):
            text = _text(value.get(key))
            if text:
                return text
        return " ".join(filter(None, (_text(item) for item in value.values())))
    if isinstance(value, list):
        return " ".join(filter(None, (_text(item) for item in value)))
    return "" if value is None else str(value)


def _matches(query: str, *values: Any) -> bool:
    haystack = " ".join(_text(value) for value in values).casefold()
    return all(token in haystack for token in query.casefold().split())


def _take_matching(rows: Iterable[dict[str, Any]], query: str, limit: int, fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [row for row in rows if _matches(query, *(row.get(field) for field in fields))][:limit]


def parse_who_indicators(payload: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]:
    rows = [row for row in payload.get("value", []) if isinstance(row, dict)]
    matches = _take_matching(
        rows,
        query,
        limit,
        ("IndicatorCode", "IndicatorName", "Definition", "SourceDesc", "Language"),
    )
    return [
        {
            "id": row.get("IndicatorCode"),
            "title": row.get("IndicatorName") or row.get("IndicatorCode"),
            "description": row.get("Definition") or row.get("SourceDesc"),
            "date": None,
            "url": f"https://ghoapi.azureedge.net/api/{quote(str(row.get('IndicatorCode')), safe='')}",
            "source": "WHO Global Health Observatory",
            "resources": [
                {
                    "id": str(row.get("IndicatorCode")),
                    "name": f"Observations GHO — {row.get('IndicatorCode')}",
                    "url": f"https://ghoapi.azureedge.net/api/{quote(str(row.get('IndicatorCode')), safe='')}?$format=json",
                    "format": "json",
                }
            ],
        }
        for row in matches
        if row.get("IndicatorCode")
    ]


def parse_world_bank_indicators(payload: Any, query: str, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list):
        rows = [row for row in payload[1] if isinstance(row, dict)]
    matches = _take_matching(
        rows,
        query,
        limit,
        ("id", "name", "sourceNote", "sourceOrganization", "topics"),
    )
    items: list[dict[str, Any]] = []
    for row in matches:
        indicator_id = str(row.get("id") or "").strip()
        if not indicator_id:
            continue
        items.append(
            {
                "id": indicator_id,
                "title": row.get("name") or indicator_id,
                "description": row.get("sourceNote") or row.get("sourceOrganization"),
                "date": None,
                "url": f"https://data.worldbank.org/indicator/{quote(indicator_id, safe='.')}",
                "source": "World Bank Health Indicators",
                "resources": [
                    {
                        "id": indicator_id,
                        "name": f"Séries CSV — {indicator_id}",
                        "url": f"https://api.worldbank.org/v2/en/indicator/{quote(indicator_id, safe='.')}?downloadformat=csv",
                        "format": "zip",
                    }
                ],
            }
        )
    return items


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def parse_unicef_dataflows(payload: Any, query: str, limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in _walk_dicts(payload):
        dataflow_id = str(row.get("id") or "").strip()
        agency_id = str(row.get("agencyID") or row.get("agencyId") or "").strip()
        version = str(row.get("version") or "latest").strip()
        name = _text(row.get("name") or row.get("names"))
        if not dataflow_id or not agency_id or not name:
            continue
        key = (agency_id, dataflow_id, version)
        if key in seen or not _matches(query, dataflow_id, name, agency_id):
            continue
        seen.add(key)
        candidates.append(
            {
                "id": dataflow_id,
                "title": name,
                "description": f"Flux SDMX {agency_id}, version {version}",
                "date": None,
                "url": f"https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/dataflow/{quote(agency_id, safe='')}/{quote(dataflow_id, safe='')}/{quote(version, safe='')}",
                "source": "UNICEF Data Warehouse (SDMX)",
                "resources": [
                    {
                        "id": f"{agency_id}:{dataflow_id}:{version}",
                        "name": f"Données SDMX CSV — {dataflow_id}",
                        "url": f"https://sdmx.data.unicef.org/ws/public/sdmxapi/rest/data/{quote(agency_id, safe='')},{quote(dataflow_id, safe='')},{quote(version, safe='')}/?format=csvfile",
                        "format": "csv",
                    }
                ],
            }
        )
        if len(candidates) >= limit:
            break
    return candidates


def parse_un_sdg_indicators(payload: Any, query: str, limit: int) -> list[dict[str, Any]]:
    rows = [
        row
        for row in _walk_dicts(payload)
        if any(key in row for key in ("code", "Code", "indicatorCode", "indicator"))
        and any(key in row for key in ("description", "Description", "name", "label"))
    ]
    matches = [
        row
        for row in rows
        if _matches(
            query,
            row.get("code") or row.get("Code") or row.get("indicatorCode") or row.get("indicator"),
            row.get("description") or row.get("Description") or row.get("name") or row.get("label"),
        )
    ][:limit]
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in matches:
        code = str(row.get("code") or row.get("Code") or row.get("indicatorCode") or row.get("indicator") or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        title = _text(row.get("description") or row.get("Description") or row.get("name") or row.get("label"))
        items.append(
            {
                "id": code,
                "title": f"{code} — {title}",
                "description": "Indicateur du cadre mondial des Objectifs de développement durable",
                "date": None,
                "url": f"https://unstats.un.org/sdgs/metadata/?Text=&Goal=&Target=&Indicator={quote(code, safe='.')}",
                "source": "UN Global SDG Indicators Database",
                "resources": [
                    {
                        "id": code,
                        "name": f"Données ODD JSON — {code}",
                        "url": f"https://unstats.un.org/SDGAPI/v1/sdg/Indicator/Data?indicator={quote(code, safe='.')}",
                        "format": "json",
                    }
                ],
            }
        )
    return items


def parse_dhs_indicators(payload: Any, query: str, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        raw = payload.get("Data") or payload.get("data") or payload.get("Indicators") or []
        if isinstance(raw, list):
            rows = [row for row in raw if isinstance(row, dict)]
    elif isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
    matches = [
        row
        for row in rows
        if _matches(
            query,
            row.get("IndicatorId") or row.get("IndicatorID") or row.get("id"),
            row.get("Label") or row.get("label") or row.get("Indicator") or row.get("name"),
            row.get("Definition") or row.get("definition") or row.get("Description"),
        )
    ][:limit]
    items: list[dict[str, Any]] = []
    for row in matches:
        indicator_id = str(row.get("IndicatorId") or row.get("IndicatorID") or row.get("id") or "").strip()
        if not indicator_id:
            continue
        label = row.get("Label") or row.get("label") or row.get("Indicator") or row.get("name") or indicator_id
        items.append(
            {
                "id": indicator_id,
                "title": label,
                "description": row.get("Definition") or row.get("definition") or row.get("Description"),
                "date": None,
                "url": "https://dhsprogram.com/data/",
                "source": "DHS Program Indicator Data",
                "resources": [
                    {
                        "id": indicator_id,
                        "name": f"Données DHS JSON — {indicator_id}",
                        "url": f"https://api.dhsprogram.com/rest/dhs/data?indicatorIds={quote(indicator_id, safe='')}&f=json",
                        "format": "json",
                    }
                ],
            }
        )
    return items
