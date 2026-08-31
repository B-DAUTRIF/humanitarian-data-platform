# UN SDG — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Source officielle : Swagger UNSD SDG API v1 et métadonnées ODD. Le Swagger complet est plus large que le périmètre HDP déclaré. Ce lot implémente explicitement `Indicator/List`, `GeoArea/{areaCode}/List` et `Series/Data`; les autres opérations restent documentées mais non qualifiées.

Nomenclatures : géographie = ONU M49, transmise comme `areaCode`; séries = codes du catalogue fournisseur. HDP ne fabrique aucun identifiant de série.

## B. Architecture

Package `app/providers/un_sdg/`. `UN_SDG_DESCRIPTOR` porte les contrats, `UNSDGService` construit/exécute les appels et normalise catalogue/observations, `api.py` expose `/api/providers/un-sdg/*`. Le routeur sémantique délègue au même service.

Pipeline : intention → résolution ONU M49 → `areaCode` → catalogue des séries disponibles → recherche de code série → `Series/Data` → période → normalisation/provenance.

## C. Matrice fonctionnelle

|Opération|Paramètre|Type|Obligatoire|UI|
|---|---|---|---|---|
|list_indicators|—|—|—|Simple|
|geoarea_series|areaCode|integer M49|oui|Simple|
|series_data|seriesCode|string|oui|Simple|
|series_data|areaCode|integer M49|non|Simple|
|series_data|page|integer|non|Avancé|
|series_data|pageSize|integer 1..1000|non|Avancé|
|series_data|timePeriodStart|integer année|non|Simple|
|series_data|timePeriodEnd|integer année|non|Simple|

## D-E. UI, clients, normalisation

UI typée Simple/Avancé/Expert avec documentation et requête native. Clients : `un_sdg_query()` Python, `hdp_un_sdg_v7()` R. Les observations normalisées conservent série, zone, période, valeur, unité et `_native`.

## F-G. Qualification

Dix cycles déterministes incluent le contrôle `Rwanda → M49 646 → areaCode=646`, sans substitution arbitraire. La sentinelle live interroge le catalogue d'indicateurs. Les échecs fournisseur sont `BLOCKED`.

Statut avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ**.

## H-I. Intégration et traçabilité

Code : `providers/un_sdg/`; routeur : `provider_semantic_adapters.py` et `semantic_provider_execution.py`; tests/audits communs au lot six connecteurs. Le périmètre Swagger non implémenté est explicitement conservé comme dette et n'est pas masqué.

## J. Évaluation métier

UN SDG fournit surtout des **données analytiques et de référence** internationales, très pertinentes pour contexte populationnel, sanitaire et développement. La fréquence varie selon indicateur; ce n'est généralement pas une surveillance temps réel.
