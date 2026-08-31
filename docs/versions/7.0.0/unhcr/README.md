# UNHCR — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Documentation officielle : UNHCR Refugee Statistics API v1 et portail Refugee Data Finder. Opérations déclarées : `population`, `demographics`, `asylum_applications`, `asylum_decisions`, `solutions`, `countries`, `regions`, `years`.

Paramètres de population audités : `limit`, `page`, `yearFrom`, `yearTo`, `year`, `coo`, `coa`, `coo_all`, `coa_all`, `cf_type`, `download`; démographie ajoute `columns` et `ptype_show`. Le catalogue countries expose les identifiants/noms/régions; la sémantique HDP utilise `cf_type=ISO` lorsque le fournisseur accepte ISO3.

## B. Architecture

Package `app/providers/unhcr/`; `UNHCR_DESCRIPTOR` documente opérations/paramètres, `UNHCRService` est le service de référence, `api.py` expose l'API/UI spécialisée. Le routeur sémantique délègue au même service.

Une géographie générique n'est jamais fusionnée : HDP lance deux requêtes distinctes, `coo=<ISO3>` puis `coa=<ISO3>`, et marque chaque résultat `geography_role=origin|asylum`.

## C. Matrice fonctionnelle

|Famille|Paramètres principaux|Types/UI|
|---|---|---|
|population/asile/solutions|limit,page|integer / Avancé|
|population/asile/solutions|yearFrom,yearTo,year|integer année / Simple-Avancé|
|population/asile/solutions|coo,coa|string code / Simple|
|population/asile/solutions|coo_all,coa_all,download|boolean / Expert|
|population/asile/solutions|cf_type|enum ISO/id / Avancé|
|demographics|columns|texte / Expert|
|demographics|ptype_show|boolean / Expert|
|countries|limit,page,region,unhcr_region|mixte / Avancé|
|regions/years|limit,page|integer / Avancé|

## D-E. UI, clients et provenance

UI Simple/Avancé/Expert générée depuis le contrat. Clients : `unhcr_query()` Python, `hdp_unhcr_v7()` R. La réponse native et les requêtes par rôle sont conservées. Le normaliseur population reste compatible avec le format historique HDP et les autres opérations gardent `_native`.

## F-G. Qualification

Dix cycles déterministes vérifient notamment la séparation origin/asylum et `cf_type=ISO`. La sentinelle live interroge `countries`. Erreur fournisseur = `BLOCKED`, jamais zéro valide.

Statut avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ**.

## H-I. Intégration/traçabilité

Code : `providers/unhcr/`; tests : `test_v7_six_provider_services.py`; audits : `v7_six_connectors_*`; routeur sémantique et clients Python/R inclus dans la CI dédiée.

## J. Évaluation métier

UNHCR est une source majeure de **données humanitaires analytiques et de référence** sur déplacements forcés. L'interprétation exige de préserver le rôle géographique (origine vs asile), les catégories de population, l'année et les définitions statistiques; ce n'est pas une source clinique ni une surveillance syndromique temps réel.
