# Configuration individualisée des sources - HDP 4.1.0

HDP 4.1.0 remplace le contrat global uniforme par dix contrats indépendants.
Chaque source conserve les réglages HTTP communs, ajoute ses contraintes fixes
et propose ses paramètres métier au niveau du projet. Les formulaires de
l'interface sont générés depuis les mêmes schémas JSON que ceux validés par
l'API : une valeur inconnue, hors limite ou mal formée est refusée côté serveur.

## Réglages HTTP communs, isolés par source

`enabled`, `timeout_seconds`, `retry_count`, `backoff_seconds`,
`connect_timeout_seconds`, `max_response_bytes`, `user_agent` et
`accept_language` sont stockés séparément pour chaque connecteur. Modifier le
délai de GDACS ne change donc plus celui de WHO GHO ou d'UNICEF.

La taille de réponse est contrôlée pendant la lecture du flux, avant le décodage
JSON. Les hôtes restent limités par une liste blanche HTTPS. Les identifiants
ReliefWeb et HAPI restent exclusivement dans `.env` ; le nom de leur variable
est visible, jamais leur valeur.

## Contrats par source

| Source | Paramètres globaux propres | Paramètres projet propres | Protocole / formats |
|---|---|---|---|
| HDX / CKAN | version CKAN 3, action `package_search` | départ, `fq`, tri | CKAN Action API ; JSON, CSV, GeoJSON, XLSX, ZIP |
| ReliefWeb | ressource `reports`, origine de l'appname | décalage, profil, preset, tri | API v2 JSON ; PDF et pièces jointes référencées |
| WHO GHO | profil OData JSON, catalogue `Indicator` | décalage et taille du catalogue | OData JSON ; export CSV via HDP |
| World Bank Health | source WDI 2, API v2 | page, taille, langue | Indicators API ; JSON, XML, CSV/ZIP |
| UNICEF SDMX | contexte public, ressource `dataflow` | agence, flux, version, détail, références | SDMX REST ; SDMX-JSON, CSV |
| UN SDG | API v1, catalogue `Indicator/List` | critères communs stricts | UNSD SDG API ; JSON, CSV dérivé |
| DHS | agrégats uniquement, ressource `indicators` | page, pays, indicateurs, années, ventilation | DHS API ; JSON agrégé |
| HDX HAPI | API v2, origine de l'identifiant | sous-domaine, code de lieu, niveau admin, décalage | HAPI v2 ; JSON normalisé |
| UNHCR | API v1, référentiel ISO | page, années, pays d'origine et d'asile | Refugee Statistics API ; JSON agrégé |
| GDACS | réponse GeoJSON, usage analytique | types d'événement, niveaux d'alerte | API GDACS ; GeoJSON / JSON |

Les contraintes fixes apparaissent en lecture seule. Elles documentent le
contrat réellement implémenté sans laisser l'utilisateur construire une
combinaison que le connecteur ne sait pas exécuter.

## Utilisation dans l'interface

1. Ouvrir **Paramètres des sources**.
2. Choisir une source dans **Configuration globale** et régler son transport.
3. Choisir un projet et la même source dans **Configuration du projet**.
4. Utiliser **Prévisualiser** avant d'enregistrer une recherche ou une
   planification.
5. Vérifier l'URL, la commande cURL et les exemples Python/R affichés.

Chaque fiche rappelle le protocole, les formats, l'authentification, la
fraîcheur, les conditions d'utilisation, les outils Python/R adaptés et les
liens officiels. La prévisualisation utilise des placeholders pour les secrets.

## Compatibilité 4.0.0

Les anciennes valeurs globales sont fusionnées avec les nouvelles valeurs par
défaut à la lecture. Les paramètres historiques ne sont pas supprimés, les
migrations restent idempotentes, et `.env`, `data/` ainsi que le volume
PostgreSQL sont conservés lors d'une mise à niveau.

## Références officielles principales

- [CKAN Action API](https://docs.ckan.org/en/latest/api/)
- [ReliefWeb API v2](https://apidoc.reliefweb.int/)
- [WHO GHO OData API](https://www.who.int/data/gho/info/gho-odata-api)
- [World Bank Indicators API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392)
- [UNICEF SDMX API](https://data.unicef.org/resources/resource-type/datasets/)
- [UN SDG API](https://unstats.un.org/SDGAPI/swagger/)
- [DHS Program API](https://api.dhsprogram.com/)
- [HDX HAPI](https://hdx-hapi.readthedocs.io/)
- [UNHCR Refugee Statistics API](https://api.unhcr.org/docs/refugee-statistics.html)
- [GDACS API](https://www.gdacs.org/gdacsapi/swagger/index.html)
