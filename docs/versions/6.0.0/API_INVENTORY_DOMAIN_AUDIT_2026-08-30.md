# HDP V6.0.0 — Audit documentaire des domaines de paramètres

Date d'audit : 2026-08-30

## Objet

Cet audit complète `API_INVENTORY.csv` et `API_INVENTORY.md` en ciblant le problème qui restait insuffisamment couvert : pour un paramètre connu, quelles sont ses valeurs admissibles, sa grammaire, son catalogue de référence ou son mécanisme officiel de découverte ?

Aucune fonctionnalité de routage sémantique n'est implémentée ici. Le livrable est documentaire et inventorial. Les informations ajoutées sont également disponibles sous forme machine dans `API_PARAMETER_DOMAINS.json`.

## Méthode et règle anti-hallucination

Les sources ont été auditées dans l'ordre suivant : documentation officielle du fournisseur, OpenAPI/Swagger lorsque disponible, endpoint de métadonnées/codelists/documentation structurée, puis exemples officiels. Une valeur n'est classée `static_enum` que si elle est explicitement définie par le fournisseur ou par son schéma machine. Les exemples isolés ne sont pas transformés en listes exhaustives. Lorsqu'une liste est dynamique ou potentiellement volumineuse, l'inventaire enregistre le mécanisme de découverte au lieu de recopier une liste figée.

## Résultat global

L'hypothèse de travail est confirmée : pour les dix sources V6, une part importante des modalités manquantes est récupérable à partir de documentations ou de catalogues machine. La meilleure stratégie n'est cependant pas de stocker toutes les modalités en dur. Il faut distinguer les domaines statiques (enum), les vocabulaires contrôlés dynamiques, les catalogues de référence, les grammaires de requête, les plages numériques, les dates/périodes et les identifiants opaques.

Le fichier `API_PARAMETER_DOMAINS.json` formalise ces catégories pour les paramètres les plus structurants et indique, pour chaque source, la stratégie d'acquisition des modalités.

## Audit par source

### HDX / CKAN

La documentation officielle HDX/CKAN confirme que `q` est la requête texte, `fq` un filtre Solr, `start` l'offset et `rows` la taille de page. Ces paramètres ne sont donc pas des variables catégorielles à énumérer. Les dimensions sémantiques comme la localisation doivent être résolues à partir des métadonnées du catalogue et non transformées arbitrairement en enum statique.

Conclusion : domaine principalement `grammar` + `dynamic_catalog`.

### ReliefWeb

La documentation des paramètres définit explicitement `query[value]`, `query[fields]`, `query[operator]`, `filter`, `facets`, `limit`, `offset`, `sort`, `profile`, `preset` et `fields`. `query[operator]` est un enum `AND|OR` avec `OR` par défaut. `profile` documente `minimal`, `full`, `list`. Les tables de champs fournissent le vocabulaire des champs et des identifiants structurés comme `country.id`, `country.iso3`, `language.code`, `theme.id`, `source.type.id`, `type.code`.

Conclusion : ReliefWeb est très favorable au routeur sémantique, mais les valeurs métier doivent être récupérées depuis les ressources/index du fournisseur plutôt que figées.

### WHO Global Health Observatory

La documentation GHO décrit explicitement un catalogue des dimensions (`/api/Dimension`), un endpoint de valeurs de dimension (`/api/DIMENSION/{dimension}/DimensionValues`), le catalogue des indicateurs (`/api/Indicator`) et une liste de régions. Les filtres sont des expressions OData. Les dates peuvent être filtrées via `TimeDimensionBegin` et `TimeDimensionEnd`.

Conclusion : c'est l'un des meilleurs cas pour un dictionnaire local synchronisé. Les modalités sont officiellement découvrables.

### World Bank Health Indicators

La documentation V2 définit les périodes (année, mois, trimestre, intervalle), `mrv`, `mrnev`, `gapfill`, `frequency`, `source`, `footnote`, `page` et `per_page`. Les fréquences documentées sont `Y`, `Q`, `M`; `gapfill` est `Y/N`. La Banque mondiale expose en outre des catalogues de pays, régions, niveaux de revenu, types de prêt, sources, indicateurs et métadonnées. Les pays possèdent notamment ISO2, ISO3 et codes Banque mondiale.

Conclusion : excellente source pour construire des mappings géographiques et thématiques sans recopier manuellement les modalités.

### UNICEF Data Warehouse / SDMX

La documentation SDMX explique que chaque dataflow est structuré par une DSD et que les valeurs admissibles de chaque dimension sont définies dans des Codelists. Le dataflow, la DSD et les codelists sont donc les sources officielles des modalités. `dataQuery` est une clé multidimensionnelle SDMX et ne doit pas être assimilée à une simple liste de choix.

Conclusion : le futur catalogue HDP doit ingérer ou mettre en cache les DSD/codelists, pas tenter de constituer manuellement un dictionnaire UNICEF unique.

### UN Global SDG Indicators Database

Le Swagger officiel fournit de nombreux paramètres et schémas. L'audit confirme notamment l'existence de vocabulaires pour objectifs, cibles, indicateurs et pays. Un paramètre documenté `dataPointType` possède les valeurs 1, 2, 3 avec signification explicite. `natureOfData` documente au moins `All`, `C`, `CNA`; ces exemples ne sont pas déclarés exhaustifs dans cet audit sans validation du schéma complet.

Conclusion : utiliser le Swagger et les catalogues SDG comme autorités de domaine.

### DHS Program Indicator Data

La documentation officielle confirme l'accès à des données agrégées et l'usage de paramètres tels que `countryIds`, `indicatorIds`, `surveyYears` et `breakdown`. Les interfaces et exemples officiels montrent que pays, années, indicateurs et groupes/caractéristiques sont des vocabulaires sélectionnables. Les listes doivent être obtenues depuis les catalogues DHS correspondants plutôt que construites depuis les seuls exemples.

Conclusion : le problème de `countryIds`/`indicatorIds` peut être résolu par synchronisation des catalogues DHS.

### HDX Humanitarian API (HAPI)

L'inventaire V6 existant avait chargé avec succès l'OpenAPI HAPI et en avait extrait 359 paramètres. Lors de cet audit documentaire, une tentative de relecture directe de `https://hapi.humdata.org/openapi.json` a retourné HTTP 403 depuis l'environnement d'audit. Il serait donc incorrect de prétendre à une nouvelle extraction complète. Le fichier de domaines conserve uniquement les stratégies sûres : contraintes/enums depuis l'OpenAPI déjà chargé, catalogue de localisations pour `location_code`, et contraintes fournisseur pour `admin_level`.

Conclusion : source exploitable, mais le cache de spécification doit être versionné et l'échec de rafraîchissement visible.

### UNHCR Refugee Statistics

La documentation officielle est particulièrement précise. `coo` et `coa` acceptent les codes pays/territoires UNHCR et peuvent utiliser ISO3 lorsque `cf_type=ISO`. `yearFrom`, `yearTo` et `year` définissent la dimension temporelle. `download`, `coo_all`, `coa_all` et `ptype_show` sont booléens. Pour les données démographiques, `columns` documente explicitement `refugees`, `asylum_seekers`, `idps`, `oip`, `stateless`, `ooc`.

Conclusion : plusieurs modalités manquantes peuvent être intégrées immédiatement de façon déterministe, tandis que la liste des pays/régions doit rester un catalogue dynamique.

### GDACS

Le Swagger officiel OAS 3.0 expose les opérations et schémas. Le guide officiel donne des exemples de recherche avec `eventlist`, `fromdate`, `todate` et `alertlevel`. Les exemples confirment notamment `EQ`, `TC`, `FL` et les niveaux `red`, `orange`, `green`. Ils ne suffisent pas à déclarer une liste complète de tous les types d'événements ; l'inventaire machine doit donc prendre le Swagger comme autorité. L'endpoint administratif `gadm0byiso3` confirme l'intérêt d'un mapping ISO3 pour les recherches géographiques.

Conclusion : combinaison `provider_schema` + vocabulaires contrôlés + ISO3.

## Impact sur l'inventaire V6

L'inventaire doit désormais être lu en deux couches complémentaires :

1. `API_INVENTORY.csv` / `API_INVENTORY.md` : paramètres, types, emplacements, support HDP, contraintes et UI ;
2. `API_PARAMETER_DOMAINS.json` : nature du domaine, enum lorsqu'il est réellement statique, endpoint/codelist de découverte lorsqu'il est dynamique, stratégie de résolution et provenance documentaire.

Cette séparation est volontaire : recopier des milliers de pays, indicateurs, dimensions ou codes dans chaque ligne de l'inventaire rendrait celui-ci rapidement périmé et très difficile à maintenir.

## Lacunes restant ouvertes

L'audit ne permet pas de déclarer tous les domaines exhaustivement fermés. Restent notamment à synchroniser automatiquement les codelists et catalogues volumineux, à conserver leur date/version de récupération, à vérifier les contraintes HAPI lors d'un prochain accès réussi à l'OpenAPI, et à distinguer plus finement `filtrable nativement`, `traduit par HDP`, `filtré après récupération` et `informatif seulement`.

## Décision recommandée

Le catalogue local HDP devra être un cache versionné des référentiels officiels, pas une copie manuelle monolithique. Pour chaque modalité, les futures métadonnées minimales devraient être : source, concept HDP éventuel, paramètre natif, code fournisseur, libellé fournisseur, synonymes/alias, langue, identifiants standards (ISO/M49 lorsque pertinents), endpoint d'origine, date de récupération, version/ETag si disponible, statut du mapping sémantique et niveau de confiance.
