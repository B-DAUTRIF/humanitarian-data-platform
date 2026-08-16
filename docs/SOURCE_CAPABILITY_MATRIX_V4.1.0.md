# Matrice des sources - HDP 4.1.0

Vérification documentaire : 15 août 2026. `Natif` signifie que le critère est
transmis à l'API ; `local` qu'il est appliqué après normalisation. Les détails
de tous les champs figurent dans `CONFIGURATION_SOURCES_V4.1.0.md`.

| Source | Mots-clés | Dates | Géographie | Authentification | Fraîcheur indicative |
|---|---|---|---|---|---|
| HDX/CKAN | natif | local | local | publique | métadonnée du jeu |
| ReliefWeb | natif | local | local | appname requis | continue |
| WHO GHO | catalogue natif | local | local | publique | variable |
| World Bank Health | catalogue local | local | local | publique | variable |
| UNICEF SDMX | flux local | local | dimensions SDMX | publique | variable |
| UN SDG | indicateur local | local | local | publique | variable |
| DHS | indicateur local | années natives | pays natifs | agrégats publics | par enquête |
| HDX HAPI v2 | local | sous-domaine/local | code natif | identifiant requis | hebdo. à annuel |
| UNHCR | local | année native | origine/asile natifs | publique | annuelle |
| GDACS | local | natif | local | publique | quasi temps réel |

HDP ne présente jamais un post-filtre local comme une capacité native. Les
portails sans contrat public stable restent des références manuelles : aucune
simulation de connecteur et aucun scraping ne sont effectués.

Références : [CKAN](https://docs.ckan.org/en/latest/api/),
[ReliefWeb](https://apidoc.reliefweb.int/),
[WHO GHO](https://www.who.int/data/gho/info/gho-odata-api),
[World Bank](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392),
[UN SDG](https://unstats.un.org/SDGAPI/swagger/),
[HDX HAPI](https://hdx-hapi.readthedocs.io/),
[UNHCR](https://api.unhcr.org/docs/refugee-statistics.html) et
[GDACS](https://www.gdacs.org/gdacsapi/swagger/index.html).
