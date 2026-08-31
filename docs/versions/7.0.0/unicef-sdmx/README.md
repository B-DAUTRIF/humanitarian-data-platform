# UNICEF SDMX — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Documentation officielle : UNICEF SDMX API. Endpoint de base : `https://sdmx.data.unicef.org/ws/public/sdmxapi/rest`. Le modèle officiel repose sur dataflow → DSD → dimensions → codelists. HDP ne déduit jamais l'ordre des dimensions d'une clé SDMX.

Opérations de ce lot : `list_dataflows` et `get_data`. Paramètres : `agency`, `dataflow`, `version`, `format`, puis `detail`/`references` pour la structure et `data_query` pour les données. Une clé `data_query` sépare les dimensions par `.` et les valeurs multiples par `+`.

Formats documentés UNICEF/SDMX plus larges que le périmètre actuel : le chemin normalisé qualifié est `sdmx-json`; XML/CSV restent documentés mais non qualifiés ici.

## B. Architecture

Package `app/providers/unicef_sdmx/`; descriptor → service de référence → API/UI spécialisée. Le service s'occupe de l'URL SDMX et de la normalisation, le routeur sémantique lui délègue la découverte de dataflows.

La géographie ou le temps ne sont pas injectés dans une clé générique : sans dataflow + DSD vérifiés, le routeur retourne `BLOCKED_MISSING_MAPPING`.

## C. Matrice fonctionnelle

|Opération|Paramètre|Type|Obligatoire/defaut|UI|
|---|---|---|---|---|
|list_dataflows|agency|string|all|Avancé|
|list_dataflows|dataflow|string|all|Simple|
|list_dataflows|version|string|latest|Avancé|
|list_dataflows|format|enum|sdmx-json|Expert|
|list_dataflows|detail|enum|full|Avancé|
|list_dataflows|references|string|none|Avancé|
|get_data|agency,dataflow,version|string|oui/defaults|Simple-Avancé|
|get_data|data_query|string clé SDMX|all|Simple|
|get_data|format|enum|sdmx-json|Expert|

## D-E. UI, clients et normalisation

UI Simple/Avancé/Expert, documentation officielle et requête native visibles. Clients : `unicef_sdmx_query()` Python, `hdp_unicef_sdmx_v7()` R. Les dataflows sont normalisés avec compatibilité HDP; les données conservent la structure native quand aucune normalisation métier DSD-spécifique n'est vérifiée.

## F-G. Qualification

Dix cycles déterministes contrôlent notamment l'absence de clé DSD inventée. La sentinelle live interroge le catalogue dataflow. Les erreurs externes sont `BLOCKED`.

Statut avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ** sur le périmètre déclaré ; **PARTIELLEMENT IMPLÉMENTÉ** au regard de toute la surface SDMX UNICEF.

## H-I. Intégration/traçabilité

Code : `providers/unicef_sdmx/`; routeur sémantique : découverte seulement sans mapping DSD; clients/tests/audits communs au lot. Dette explicite : résolution automatique dataflow→DSD→codelists pour permettre une traduction sémantique géographie/temps sûre.

## J. Évaluation métier

UNICEF SDMX est une source **analytique et de référence** à forte valeur santé/enfance/démographie. Sa comparabilité dépend du dataflow, des dimensions et codelists; la reproductibilité exige donc de conserver dataflow, version, clé SDMX et structure associée.
