# HDP V7 — matrice systématique des paramètres

Source générée : `tools/v7_systematic_parameter_audit.py`.

Verdict déterministe : **PASS_WITH_EXPLICIT_DEBT**  
Lignes : **82** · contrôles de binding : **34**.

| Fournisseur | Paramètre | HDP | Registre | Spécialisé | Statut |
|---|---|---|---|---|---|
| reliefweb | `appname` | `appname` | absent | present | AUDITABLE |
| reliefweb | `query.value` | `query` | present | present | AUDITABLE |
| reliefweb | `query.fields` | `query_fields` | absent | present | AUDITABLE |
| reliefweb | `query.operator` | `query_operator` | absent | present | AUDITABLE |
| reliefweb | `filter.field` | `filter` | absent | present | AUDITABLE |
| reliefweb | `filter.value` | `filter` | absent | present | AUDITABLE |
| reliefweb | `filter.operator` | `filter` | absent | present | AUDITABLE |
| reliefweb | `filter.negate` | `filter` | absent | present | AUDITABLE |
| reliefweb | `filter.conditions` | `filter` | absent | present | AUDITABLE |
| reliefweb | `facets.field` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.name` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.limit` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.sort` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.filter` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.interval` | `facets` | absent | present | AUDITABLE |
| reliefweb | `facets.scope` | `facets` | absent | present | AUDITABLE |
| reliefweb | `limit` | `result_limit` | present | present | AUDITABLE |
| reliefweb | `offset` | `offset` | present | present | AUDITABLE |
| reliefweb | `sort` | `sort` | present | present | AUDITABLE |
| reliefweb | `profile` | `profile` | present | present | AUDITABLE |
| reliefweb | `preset` | `preset` | present | present | AUDITABLE |
| reliefweb | `fields.include` | `fields_include` | absent | present | AUDITABLE |
| reliefweb | `fields.exclude` | `fields_exclude` | absent | present | AUDITABLE |
| reliefweb | `slim` | `slim` | absent | present | AUDITABLE |
| reliefweb | `verbose` | `verbose` | absent | present | AUDITABLE |
| reliefweb | `content_type` | `content_type` | absent | present | AUDITABLE |
| reliefweb | `fields/profile only` | `fields_include/fields_exclude/profile` | absent | present | AUDITABLE |
| world-bank-health | `source` | `source` | present | present | AUDITABLE |
| world-bank-health | `country` | `country` | present | present | AUDITABLE |
| world-bank-health | `indicator` | `indicator` | present | present | AUDITABLE |
| world-bank-health | `date` | `date` | present | present | AUDITABLE |
| world-bank-health | `page` | `page` | present | present | AUDITABLE |
| world-bank-health | `per_page` | `per_page` | present | present | AUDITABLE |
| world-bank-health | `mrv` | `mrv` | present | present | AUDITABLE |
| world-bank-health | `mrnev` | `mrnev` | present | present | AUDITABLE |
| world-bank-health | `gapfill` | `gapfill` | present | present | AUDITABLE |
| world-bank-health | `frequency` | `frequency` | present | present | AUDITABLE |
| world-bank-health | `footnote` | `footnote` | present | present | AUDITABLE |
| world-bank-health | `format` | `format` | present | present | AUDITABLE |
| world-bank-health | `language` | `language` | present | present | AUDITABLE |
| world-bank-health | `operation` | `indicators` | absent | present | AUDITABLE |
| world-bank-health | `operation` | `countries` | absent | present | AUDITABLE |
| world-bank-health | `operation` | `topics` | absent | present | AUDITABLE |
| world-bank-health | `operation` | `sources` | absent | present | AUDITABLE |
| world-bank-health | `operation` | `metadata` | absent | present | AUDITABLE |
| world-bank-health | `operation` | `indicator_metadata` | absent | present | AUDITABLE |
| hdx | `q` | `query` | present | registry-path | AUDITABLE |
| hdx | `fq` | `fq` | present | registry-path | AUDITABLE |
| hdx | `sort` | `sort` | present | registry-path | AUDITABLE |
| hdx | `rows` | `result_limit` | present | registry-path | AUDITABLE |
| hdx | `start` | `start` | present | registry-path | AUDITABLE |
| hdx | `facet` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `facet.mincount` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `facet.limit` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `facet.field` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `include_drafts` |  | not-required | registry-path | NOT_EXPOSED_BY_DESIGN |
| hdx | `include_deleted` |  | not-required | registry-path | NOT_EXPOSED_BY_DESIGN |
| hdx | `include_private` |  | not-required | registry-path | NOT_EXPOSED_BY_DESIGN |
| hdx | `use_default_schema` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `qf` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `wt` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `bf` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `boost` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `tie` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `defType` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx | `mm` |  | not-required | registry-path | DOCUMENTED_NOT_EXPOSED |
| hdx-hapi | `app_identifier` | `HDX_HAPI_APP_IDENTIFIER` | not-required | registry-path | AUDITABLE |
| hdx-hapi | `output_format` |  | not-required | registry-path | QUALIFIED_JSON_ONLY |
| hdx-hapi | `limit` | `result_limit` | present | registry-path | AUDITABLE |
| hdx-hapi | `offset` | `offset` | present | registry-path | AUDITABLE |
| hdx-hapi | `location_code` | `location_code` | present | registry-path | AUDITABLE |
| hdx-hapi | `admin_level` | `admin_level` | present | registry-path | AUDITABLE |
| hdx-hapi | `sector_name` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `admin1_code` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `admin1_name` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `admin2_code` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `org_name` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `age_range_code` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `gender_code` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `resource_hdx_id` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `update_date_min` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |
| hdx-hapi | `update_date_max` |  | not-required | registry-path | ENDPOINT_FILTER_NOT_EXPOSED |

## Capacités World Bank documentées hors chemin normalisé principal

La documentation officielle V2 décrit également `ctrycode`, `scale`, `format=jsonP` avec `prefix`, `format=jsonstat`, `downloadformat=csv|xml|excel` et `dataformat=list|table`. `ctrycode` et `scale` font l'objet de sondes live dans le protocole. Les formats alternatifs, JSONP, téléchargements et `dataformat` restent **DOCUMENTÉS MAIS NON QUALIFIÉS DANS LE CHEMIN NORMALISÉ HDP** ; ils ne doivent donc pas être présentés comme absents ni comme qualifiés.

## Dette explicite

Les facettes CKAN publiques et options Solr avancées non exposées restent visibles comme dette. `include_drafts`, `include_deleted` et `include_private` sont volontairement exclus du catalogue HDX public. Les filtres HAPI spécifiques aux sous-endpoints restent `ENDPOINT_FILTER_NOT_EXPOSED` tant qu'un contrat fournisseur courant et exploitable n'a pas permis leur qualification exhaustive. L'absence de `HDX_HAPI_APP_IDENTIFIER` rend les sondes HAPI live `BLOCKED`, jamais `empty_valid`.
