# ReliefWeb V2 — inventaire contractuel HDP

Consultation: 2026-08-31. Statut: DOCUMENTÉ sauf mention contraire.

## Sources officielles
- https://apidoc.reliefweb.int/ — version V2, API de lecture, GET/POST, JSON, OpenAPI 3.1.
- https://apidoc.reliefweb.int/endpoints — endpoints, listes/items.
- https://apidoc.reliefweb.int/parameters — paramètres natifs.
- https://apidoc.reliefweb.int/fields-tables — champs et capacités.
- https://apidoc.reliefweb.int/result-structure — enveloppe et erreurs.
- https://apidoc.reliefweb.int/presets — presets par type.
- https://apidoc.reliefweb.int/faq — Lucene, exact, boosts et pratiques.
- https://apidoc.reliefweb.int/publishing — API de publication séparée.

## Contrat général
Base: `https://api.reliefweb.int/v2/{content_type}[/{id}]?appname={appname}`. L'API de distribution est read-only. `appname` est obligatoire et pré-approuvé depuis le 1er novembre 2025. Quotas documentés: 1000 entrées maximum/appel et 1000 appels/jour. HDP utilise `HDP_plateforme` comme défaut global, surchargeable par projet.

## 9 types de contenu
`reports`, `disasters`, `countries`, `jobs`, `training`, `sources`, `blog`, `book`, `references`.
Listes: GET ou POST, tous paramètres. Items: GET seulement, `fields` et `profile` seulement.

## Paramètres de liste exhaustifs documentés
| Paramètre | Type/structure | Contraintes / domaine | UI HDP |
|---|---|---|---|
| appname | string URL | obligatoire | global + surcharge projet |
| query.value | string | obligatoire si query | texte/Lucene |
| query.fields | string[] | champs recherchables, boost `^N` | multi-select + poids |
| query.operator | enum | AND, OR; OR défaut | radio |
| filter.field | string | champ filtrable | sélecteur piloté schéma |
| filter.value | scalar/list/range | selon champ | contrôle typé |
| filter.operator | enum | AND/OR | radio |
| filter.conditions | filter[] | récursif | arbre de filtres |
| filter.negate | bool | négation | checkbox |
| facets[].field | string | champ facetable/date/status | select |
| facets[].name | string | alias | texte |
| facets[].limit | integer | défaut 10, hors dates | numérique |
| facets[].sort | enum | count/value : asc/desc | select |
| facets[].filter | filter | filtre récursif | arbre |
| facets[].interval | enum | year/month/week/day | select date |
| facets[].scope | enum | default/query/global | select |
| limit | integer | 0..1000, défaut 10 | numérique |
| offset | integer | >=0, défaut 0 | pagination |
| sort[] | string[] | `{field}:asc|desc`, priorité par ordre | liste ordonnée |
| profile | enum | minimal/full/list; minimal défaut | select |
| preset | enum | minimal/latest/analysis | select |
| fields.include | string[] | champs de sortie | multi-select |
| fields.exclude | string[] | champs de sortie | multi-select |
| slim | int switch | 1 retire hypermedia | checkbox |
| verbose | int switch | 1 ajoute `details` | expert/debug |

Query avancée documentée: phrases entre guillemets, AND/OR/NOT dans `value`, `field:term`, parenthèses, `.exact` pour champs exacts, boosts `field^N`. Pour requêtes complexes, POST JSON est préféré.

## Résultat
Enveloppe: `href`, `time`, `links` (self/next/previous/collection selon contexte), `totalCount`, `count`, `data`; chaque item expose `id`, `fields`, et en liste `score`, `href`. `verbose=1` ajoute `details`. HDP doit conserver le payload brut et une normalisation distincte.

## Champs / taxonomie
La table officielle des champs est l'autorité et doit être synchronisée plutôt que dupliquée à la main. Capacités à conserver par champ: type, conteneur/sous-champ, exact, sortable, searchable/not_searchable, multi, format (notamment markdown), content types et capacité de facette indiquée par la documentation actuelle. Exemples structurants: body/body-html; career_categories; city; content_type; country(id,iso3,name,primary,shortname); cost; current; date.changed/closing/created/end/event/original/registration/start; description/html; disaster(id,name,glide,type.*); disaster_type; disclaimer; experience; feature; featured; file(description,filename,id,mimetype,preview.*,url); format(id,name); fts_id; source(longname,name,shortname,spanish_name,type.*); status; theme(id,name); title; training_language(id,name,code); type(code,id,name,primary); url; url_alias. Le fichier machine-readable HDP doit être régénérable depuis la documentation/OpenAPI et les réponses `references`.

## Nomenclatures
`references` est l'endpoint de taxonomie. Les termes contrôlés (pays, formats, thèmes, langues, types, catégories de carrière, expérience, types de source, etc.) doivent être découverts/synchronisés dynamiquement, avec cache, horodatage, provenance et identifiant ReliefWeb. Les catastrophes évoluent et doivent être résolues dynamiquement (nom/GLIDE). Aucun vocabulaire dynamique ne doit être figé comme vérité permanente dans le code.

## Presets
`minimal`: filtres de statut raisonnables par défaut; `latest`: tri récent (ou id pour pays/sources); `analysis`: inclut notamment catastrophes archivées et jobs/training expirés. Les définitions exactes par content type doivent rester exposées comme métadonnées et non être réinterprétées silencieusement.

## Publishing API — périmètre séparé
API d'écriture distincte, organisations approuvées, clé API + provider ID, PUT, HTTP 202, UUIDv5, trusted URLs, revue éditoriale. Schémas canoniques: report.json, job.json, training.json. Ce sous-système ne doit PAS être activé dans le connecteur de lecture sans credentials et autorisation explicites.

## Règles HDP
1. Jamais convertir erreur/configuration/429/timeout/schema drift en zéro résultat.
2. `appname`: projet > global `HDP_plateforme` > configuration_error.
3. Les filtres ReliefWeb natifs restent natifs; pas de post-filter quand un filtre natif vérifié existe.
4. Réponse native + normalisée + provenance + fingerprint.
5. Simple = intention; Avancé = paramètres structurés; Expert = requête native, payload, réponse, détails.
6. Une capacité non testée n'est pas qualifiée.
