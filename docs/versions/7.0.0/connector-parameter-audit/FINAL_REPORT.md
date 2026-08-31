# HDP V7 — audit systématique paramètre par paramètre

Date de campagne : 2026-08-31

## Périmètre

Cette campagne applique le protocole canonique `docs/prompts/audit_parametres_connecteurs_v7.md` à ReliefWeb V2, World Bank Indicators API v2 et aux contrats HDX réellement présents dans HDP : HDX/CKAN `package_search`, HDX HAPI v2 et le sous-système COD officiel. Le regroupement « HDX » ne vaut jamais contrat API unique.

## Méthode

Granularité : `fournisseur → API → endpoint → opération → paramètre → type/valeur → requête native → réponse → normalisation → UI → client → test → preuve → statut`.

Chaque paramètre est rapproché de la documentation fournisseur, du descriptor lorsqu'il existe, du `source_registry`, du backend, de l'UI, des clients Python/R, des tests déterministes et des tests live disponibles. Les capacités documentées mais absentes restent explicitement `NOT_IMPLEMENTED/NOT_QUALIFIED`; elles ne sont pas transformées artificiellement en fonctionnalités qualifiées.

## Défauts corrigés pendant l'audit

1. ReliefWeb spécialisé : une collection paginée vide était retournée `empty_valid`. Correction : une réponse bornée sans élément est `partial` tant qu'une preuve exhaustive d'absence n'existe pas.
2. World Bank spécialisé : observations, métadonnées et catalogues paginés pouvaient également présenter un tableau vide comme `empty_valid`. Correction identique : `partial` pour les réponses bornées vides.
3. World Bank `format` : le descriptor et l'UI exposaient `format=json`, mais le modèle de requête spécialisé ne le sérialisait pas. Le modèle valide maintenant explicitement le seul format qualifié `json`; le service de référence reste propriétaire de la sérialisation native et continue d'imposer JSON.
4. HAPI : le workflow pouvait rester vert grâce à `continue-on-error` même si l'inventaire OpenAPI était bloqué. Ce masquage a été supprimé. L'exécution live et le verdict de couverture sont désormais deux champs distincts : un inventaire réussi peut conclure `QUALIFICATION PARTIELLE` lorsque des paramètres d'endpoints configurés restent non implémentés.

## ReliefWeb

Le descriptor spécialisé recense les paramètres natifs de haut niveau `appname`, `query`, `filter`, `facets`, `limit`, `offset`, `sort`, `profile`, `preset`, `fields`, `slim`, `verbose`. Le modèle natif HDP couvre aussi les structures imbriquées `query.*`, `filter.*`, `facets.*` et `fields.include/exclude`. Les régressions déterministes et les cycles paramétriques ont été exécutés avec succès sur le head précédent de la PR ; ils doivent être rejoués sur chaque nouveau head avant qualification finale.

## World Bank

Le contrat normalisé qualifié est JSON. Les paramètres d'observation audités sont `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `format`, `language`. Pays souverains et agrégats World Bank restent distincts. Les formats alternatifs/SDMX documentés ne sont pas requalifiés par cette campagne.

## HDX / CKAN

Le runtime HDP expose actuellement `q` via `query`, `rows` via `result_limit`, `start`, `fq` et `sort`. Les paramètres documentés `fq_list` et les facettes restent une dette d'implémentation explicite. Les drapeaux d'inclusion de jeux privés/brouillons/supprimés restent hors contrat du lecteur public tant qu'une politique d'autorisation n'est pas implémentée. Ces absences ne sont pas déclarées qualifiées.

## HDX HAPI

Le registre HDP v2 expose un sous-domaine, `location_code`, `admin_level`, `offset` et la limite commune ; `app_identifier` provient de l'environnement et `output_format` est fixé à JSON dans le chemin actuel.

Preuve live observée sur le run GitHub Actions `33391735192` : HTTP 200 sur l'OpenAPI HAPI, OpenAPI 3.1.0, version HAPI 0.9.14, 359 lignes paramétriques inventoriées, 126 lignes classées implémentées, 233 non implémentées, 217 lignes rattachées à des endpoints configurés, zéro échec de contrat sur les contrôles alors présents. Cette preuve démontre le bon fonctionnement de l'inventaire ; elle ne démontre pas une couverture exhaustive des paramètres HAPI.

Le script et le workflow ont ensuite été renforcés : `execution_status=PASS` signifie seulement que l'inventaire et les contrôles exécutés passent ; `qualification_verdict=QUALIFICATION PARTIELLE` est obligatoire dès qu'un paramètre d'un endpoint configuré reste `NOT_IMPLEMENTED`. Un blocage réseau/OpenAPI fait maintenant échouer le job au lieu d'être masqué.

## HDX COD

COD est traité comme sous-système géographique officiel séparé, avec `cod_families`, `m49_scope_code`, `official_policy`, `preferred_format`, `refresh_interval_minutes` et `auto_download`. Ses paramètres ne sont pas assimilés aux paramètres CKAN/HAPI.

## Test de non-contamination

La campagne introduit des régressions permanentes : `location="Rwanda"` ne peut pas devenir `project_id`; `project_id` est rejeté par les schémas paramètres fournisseur ; changer `result_limit` ne modifie pas implicitement l'offset/pagination ; changer `date_from` ne modifie pas `date_to`; modifier un filtre CKAN ou une géographie HAPI conserve les autres paramètres indépendants.

## Preuves CI déjà observées

Sur le head `521c5cf98eab0de462f49f91ff10f016df75d214`, les workflows `HDP V7 connector parameter audit`, `HDP V7 full qualification`, `HDP V7 global 10-cycle audit`, `HDP validation`, `HDP Windows installer` et `HDP V7 World Bank Health qualification` ont tous terminé avec succès. Le job HAPI live a produit l'inventaire chiffré ci-dessus. Ces résultats restent des preuves attachées à ce SHA et ne sont jamais transférés automatiquement à un head ultérieur.

## Qualification

Verdict de campagne : **QUALIFICATION PARTIELLE**.

ReliefWeb et World Bank disposent d'une couverture paramétrique déterministe avancée. HDX/CKAN reste partiellement exposé et HAPI comporte un volume important de paramètres OpenAPI non implémentés, y compris sur des endpoints configurés. La PR ne doit donc pas être présentée comme qualification exhaustive de toutes les capacités HDX.

Avant fusion, le head final doit repasser les gates déterministes, l'inventaire HAPI live non masqué, les régressions V7 et les gates Windows. La promotion de `main` reste séparée et soumise au gate d'acceptation Windows sur machine cible.
