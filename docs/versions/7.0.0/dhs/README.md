# DHS — dossier connecteur HDP V7

## A. Audit API et nomenclatures

Périmètre implémenté : API publique agrégée `https://api.dhsprogram.com/rest/dhs`. Preuves officielles : portail API, endpoint officiel des champs pays et Guide to DHS Statistics DHS-8. L'API agrégée ne donne pas accès aux microdonnées individuelles : HDP ne contourne pas la procédure d'accès DHS aux microdonnées.

Opérations HDP spécialisées : `list_indicators`, `indicator_data`, `list_countries`, `list_surveys`. Capacités documentées mais non qualifiées dans ce lot : survey characteristics, publications, datasets, geometry, tags, data updates et surface avancée non déclarée.

Nomenclature géographique : `list_countries` fournit notamment `DHS_countryCode` et `ISO3_countryCode`. La traduction sémantique est donc `M49/ISO3 HDP → ISO3_countryCode du catalogue officiel → DHS_countryCode`. ISO3 n'est jamais injecté directement dans `countryIds`.

## B. Architecture

Package : `app/providers/dhs/`. `DHS_DESCRIPTOR` est le contrat documentaire, `DHSService` l'implémentation fournisseur unique pour l'API spécialisée et le routeur sémantique, `api.py` expose `/api/providers/dhs/*`. Le service commun impose GET, timeout, retry, limite de réponse, validation stricte et provenance de requête native.

Pipeline sémantique : intention → géographie HDP vérifiée → catalogue DHS countries → DHS_countryCode → catalogue indicateurs → indicatorIds → surveyYears → `/data` → normalisation → provenance.

## C. Matrice fonctionnelle

|Opération|Paramètre|Type|Cardinalité|Obligatoire|Sémantique/UI|
|---|---|---|---|---|---|
|list_indicators|f|string enum json|1|non|Expert|
|list_indicators|page|integer|1|non|Avancé|
|list_indicators|perpage|integer|1|non|Avancé|
|indicator_data|countryIds|array[string]|0..100|non|Simple, codes DHS vérifiés|
|indicator_data|indicatorIds|array[string]|0..100|non|Simple, catalogue indicateurs|
|indicator_data|surveyYears|array[integer]|0..100|non|Avancé, années d'enquête|
|indicator_data|breakdown|string|0..1|non|Avancé|
|indicator_data|page/perpage/f|integer/integer/enum|1|non|Avancé/Expert|
|list_countries|page/perpage/f|integer/integer/enum|1|non|Avancé/Expert|
|list_surveys|page/perpage/f|integer/integer/enum|1|non|Avancé/Expert|

## D. UI et clients

L'UI spécialisée `/api/providers/dhs/ui` est générée depuis le contrat et propose Simple/Avancé/Expert, documentation officielle, projet optionnel et affichage de la requête native. Clients : `dhs_query()` en Python et `hdp_dhs_v7()` en R.

## E. Normalisation/provenance

Le catalogue indicateurs conserve le normaliseur historique qualifié pour compatibilité. Les autres réponses conservent `_native`; la réponse API spécialisée retourne `native_response` et `native_request`. La géographie sémantique conserve la ligne du catalogue ayant produit le mapping.

## F-G. Qualification

Protocole : dix cycles réellement exécutés par `tools/v7_six_connectors_10cycle_qualification.py`, puis sentinelle live non destructive `list_countries`. Un fournisseur indisponible est `BLOCKED`, jamais `empty_valid`.

Statut de ce document avant inspection du head final : **IMPLÉMENTÉ MAIS NON QUALIFIÉ**.

## H. Intégration HDP

API native, routeur sémantique, configuration projet, Python/R et régression générale sont inclus dans la CI dédiée. Les tests vérifient notamment que `Rwanda → RWA` reste une intention géographique et que seul le catalogue DHS peut produire `DHS_countryCode`.

## I. Traçabilité

Code : `descriptor.py`, `service.py`, `api.py`; tests : `test_v7_six_provider_services.py`; audits : outils `v7_six_connectors_*`; branche : `feat/v7-six-connectors-qualified`.

## J. Évaluation métier

DHS est surtout une source **analytique/contextuelle** à forte valeur épidémiologique et de santé publique, avec profondeur historique et indicateurs standardisés. Elle n'est pas une source de surveillance temps réel. Les délais d'enquête, la représentativité et les définitions d'indicateurs doivent être conservés dans l'interprétation.
