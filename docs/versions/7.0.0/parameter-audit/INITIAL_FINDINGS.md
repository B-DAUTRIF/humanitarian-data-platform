# HDP V7 — audit systématique des paramètres : constats initiaux

Commit de base audité : `d0948e8337f4f1bd0dec762f67f8d27a2eb6136a`.

Ce rapport applique `docs/prompts/audit_parametres_connecteurs_v7.md`. Il distingue les paramètres documentés des paramètres réellement exposés/qualifiés dans HDP ; une absence d'exposition n'est jamais transformée en affirmation d'absence de capacité fournisseur.

## ReliefWeb V2

Le service spécialisé ReliefWeb constitue le chemin de référence et son descripteur inventorie les paramètres natifs de premier niveau `appname`, `query`, `filter`, `facets`, `limit`, `offset`, `sort`, `profile`, `preset`, `fields`, `slim`, `verbose`. L'UI spécialisée expose les structures simples et avancées nécessaires : query fields/operator, filtres récursifs JSON, facettes JSON, projections de champs, slim/verbose et les neuf types de contenu.

Le `source_registry.py` générique reste volontairement plus étroit (`offset`, `profile`, `preset`, `sort` en plus des champs communs). Cela n'est acceptable que parce que le chemin spécialisé expose le contrat natif ; la matrice automatisée doit continuer à signaler toute divergence entre registre générique et descripteur spécialisé.

Point critique permanent : `project_id` est un identifiant technique HDP et ne doit jamais recevoir une valeur géographique. La correction issue de l'incident `project_id="rwanda"` est incluse dans la base de cet audit.

## World Bank Health / WDI

Le registre et le service spécialisé couvrent le chemin JSON qualifié : `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `format=json`, `language`, plus catalogues indicateurs/pays/topics/sources et métadonnées.

La validation géographique utilise le catalogue fournisseur versionné quand il est disponible ; la liste statique d'agrégats n'est qu'un garde-fou de repli. Les agrégats ne sont jamais interprétés comme des pays souverains ISO3.

Dette/point à qualifier : la documentation fournisseur décrit `gapfill` et `frequency` dans le contexte de MRV. HDP sérialise aujourd'hui ces paramètres indépendamment. Les tests live doivent établir le comportement effectivement accepté et la documentation HDP doit conserver la relation de compatibilité au lieu de l'ignorer.

Les formats XML/JSON-stat/download et SDMX restent documentés mais hors chemin normalisé qualifié tant qu'une qualification dédiée n'est pas exécutée.

## HDX / CKAN

Le connecteur `hdx` utilise CKAN `package_search`. Les paramètres actuellement exposés sont `q` via `query`, `rows` via `result_limit`, `start`, `fq` et `sort`.

La documentation CKAN décrit aussi la facettisation (`facet`, `facet.mincount`, `facet.limit`, `facet.field`) et plusieurs options avancées Solr/dismax. Ces capacités sont inventoriées par l'audit comme `DOCUMENTED_NOT_EXPOSED` et ne doivent pas être déclarées qualifiées. Les options `include_drafts`, `include_deleted` et `include_private` sont classées `NOT_EXPOSED_BY_DESIGN` dans le contexte du catalogue HDX public : elles touchent à des données non publiques ou supprimées et ne sont pas ajoutées silencieusement à l'UI publique.

## HDX HAPI v2

HAPI est traité comme un contrat distinct de CKAN. HDP expose actuellement l'endpoint, `location_code`, `admin_level`, `offset`, la limite commune et l'identifiant d'application via configuration. La sortie normalisée est JSON.

La documentation HAPI montre que les filtres disponibles dépendent du sous-endpoint (par exemple `sector_name`, `admin1_code`, `admin1_name`, `admin2_code`, `org_name`, `age_range_code`, `gender_code`, filtres de ressources et dates de mise à jour). Ces paramètres sont inventoriés comme dette `ENDPOINT_FILTER_NOT_EXPOSED` tant qu'un contrat machine-readable courant/sandbox n'a pas été interrogé et que leur exposition n'a pas été individualisée par endpoint.

Si `HDX_HAPI_APP_IDENTIFIER` n'est pas disponible dans l'environnement de qualification, l'audit live HAPI doit être `BLOCKED`, jamais PASS et jamais « aucune donnée ».

## Stratégie de qualification

Le script `tools/v7_systematic_parameter_audit.py` génère JSON, CSV et Markdown, contrôle la couverture registre/descripteur et exécute des tests de binding indépendants. Le workflow `HDP V7 systematic parameter audit` le rejoue dix fois, puis exécute les régressions sémantiques/connecteurs, l'audit release-readiness, une qualification live séparée et un rebuild Windows 2025.

Le verdict final ne sera fixé qu'après observation des résultats CI du commit final. Les dettes explicitement inventoriées ne sont pas considérées comme PASS par défaut.