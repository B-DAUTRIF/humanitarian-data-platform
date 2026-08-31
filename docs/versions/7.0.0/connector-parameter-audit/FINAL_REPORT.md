# HDP V7 — audit systématique paramètre par paramètre

Date de campagne : 2026-08-31

## Périmètre

Cette campagne applique le protocole canonique `docs/prompts/audit_parametres_connecteurs_v7.md` à ReliefWeb V2, World Bank Indicators API v2 et aux contrats HDX réellement présents dans HDP : HDX/CKAN `package_search`, HDX HAPI v2 et le sous-système COD officiel. Le regroupement « HDX » ne vaut jamais contrat API unique.

## Méthode

Granularité : `fournisseur → API → endpoint → opération → paramètre → type/valeur → requête native → réponse → normalisation → UI → client → test → preuve → statut`.

Chaque paramètre est rapproché de la documentation fournisseur, du descriptor lorsqu'il existe, du `source_registry`, du backend, de l'UI, des clients Python/R, des tests déterministes et des tests live disponibles. Les capacités documentées mais absentes restent explicitement `NOT_IMPLEMENTED/NOT_QUALIFIED`; elles ne sont pas transformées artificiellement en échecs de fonctionnalités que HDP n'affirme pas encore fournir.

## Défauts corrigés pendant l'audit

1. ReliefWeb spécialisé : une collection paginée vide était retournée `empty_valid`. Correction : une réponse bornée sans élément est `partial` tant qu'une preuve exhaustive d'absence n'existe pas.
2. World Bank spécialisé : observations, métadonnées et catalogues paginés pouvaient également présenter un tableau vide comme `empty_valid`. Correction identique : `partial` pour les réponses bornées vides.
3. World Bank `format` : le descriptor et l'UI exposaient `format=json`, mais le modèle de requête spécialisé ne le sérialisait pas. Le modèle valide maintenant explicitement le seul format qualifié `json`; le service de référence reste propriétaire de la sérialisation native et continue d'imposer JSON.

## État documentaire constaté avant CI

### ReliefWeb

Le descriptor spécialisé recense les paramètres natifs de haut niveau `appname`, `query`, `filter`, `facets`, `limit`, `offset`, `sort`, `profile`, `preset`, `fields`, `slim`, `verbose`. Le modèle natif HDP couvre aussi les structures imbriquées `query.*`, `filter.*`, `facets.*` et `fields.include/exclude`. La campagne doit encore confirmer ces mappings dans les 10 cycles CI et, pour le live, conserver tout refus fournisseur comme erreur et non comme zéro résultat.

### World Bank

Le contrat normalisé qualifié est JSON. Les paramètres d'observation audités sont `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `format`, `language`. Pays souverains et agrégats World Bank restent distincts. Les formats alternatifs/SDMX documentés ne sont pas requalifiés par cette campagne.

### HDX / CKAN

Le runtime HDP expose actuellement `q` via `query`, `rows` via `result_limit`, `start`, `fq` et `sort`. Les autres paramètres documentés de `package_search` sont inventoriés séparément. Les drapeaux d'inclusion de jeux privés/brouillons/supprimés sont hors contrat du lecteur public HDX tant qu'une politique d'autorisation n'est pas implémentée. Les facettes et `fq_list` documentés restent dette d'implémentation explicite et ne sont pas déclarés qualifiés.

### HDX HAPI

Le registre HDP v2 expose un sous-domaine, `location_code`, `admin_level`, `offset` et la limite commune ; `app_identifier` provient de l'environnement et `output_format` est fixé à JSON dans le chemin actuel. Les paramètres propres à chaque endpoint HAPI doivent être inventoriés dynamiquement depuis l'OpenAPI live et ne sont jamais déduits des autres endpoints.

### HDX COD

COD est traité comme sous-système géographique officiel séparé, avec `cod_families`, `m49_scope_code`, `official_policy`, `preferred_format`, `refresh_interval_minutes` et `auto_download`. Ses paramètres ne sont pas assimilés aux paramètres CKAN/HAPI.

## Test de non-contamination

La campagne introduit des régressions permanentes : `location="Rwanda"` ne peut pas devenir `project_id`; `project_id` est rejeté par les schémas paramètres fournisseur ; changer `result_limit` ne modifie pas implicitement l'offset/pagination ; changer `date_from` ne modifie pas `date_to`; modifier un filtre CKAN ou une géographie HAPI conserve les autres paramètres indépendants.

## Qualification

Statut au moment de la création de ce rapport : **À VÉRIFIER — CI NON ENCORE EXÉCUTÉE SUR LE COMMIT FINAL DE CAMPAGNE**.

Le verdict sera mis à jour uniquement après observation des workflows GitHub Actions et des artefacts machine-readable. Aucun test non exécuté n'est compté PASS.
