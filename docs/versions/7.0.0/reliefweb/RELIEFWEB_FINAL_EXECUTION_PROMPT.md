# Prompt final d'exécution — Connecteur ReliefWeb V2 dans HDP

Ce prompt spécialise `docs/governance/HDP_RECREATION_MASTER_PROMPT.md` et ne peut déroger à ses invariants.

## Objectif
Finaliser le connecteur ReliefWeb avec fidélité maximale à l'API V2 officielle tout en préservant le fonctionnement global de HDP. Ne jamais créer un second Semantic Core, job engine, système de provenance, cache ou modèle projets.

## Phase A — inventaire vérifié
Rechercher prioritairement dans la documentation officielle ReliefWeb/OCHA. Inventorier endpoints, méthodes, content types, collection/item, paramètres, champs/sous-champs, types, cardinalités, searchable/exact/filterable/facetable/sortable, valeurs contrôlées, profiles, presets, limites, pagination, résultats, erreurs, taxonomies/references et Publishing API séparée. Chaque entrée garde URL, date de consultation, preuve et statut `DOCUMENTED|LIVE_VERIFIED|INFERRED|UNVERIFIED|CONFLICTING_DOCUMENTATION`.

Produire Markdown + JSON + CSV + matrices endpoints/fields/features. L'inventaire est également consommable par le logiciel via ProviderDescriptor.

## Phase B — Provider Core cohérent
Créer/compléter les contrats génériques ProviderDescriptor/Operation/Field/Config/Capability uniquement lorsqu'ils sont réellement génériques. ReliefWeb reste isolé sous `providers/reliefweb/`. Flux obligatoire : `SearchIntent -> QueryPlan -> ProviderOperation -> ReliefWebQuery -> ReliefWeb serializer -> ProviderService -> HTTP`.

## Phase C — configuration
ReliefWeb appname : `project -> global -> HDP_plateforme`. La configuration effective et son origine sont visibles et fingerprintées. `appname` est public ; les vrais secrets restent exclus. Un 403 n'est jamais transformé en zéro résultat.

## Phase D — fonctionnalités natives
Supporter fidèlement les content types officiels, collection GET/POST, item GET, query/value/fields/operator, syntaxe avancée, exact, boosts, filtres récursifs, negate, facettes/filter/interval/scope, limit/offset, sort, profiles minimal/list/full, presets analysis/latest/minimal, fields include/exclude, slim, verbose. Le choix GET/POST doit être déterministe et testable.

## Phase E — metadata/taxonomies
Les tables officielles de champs alimentent un descripteur machine-readable. `references` est traité selon son contrat réellement documenté/observé, sans inventer un field model. Cache via ProviderMetadataCache générique avec hash/date/TTL/evidence.

## Phase F — stockage
Réutiliser les settings globaux/projet HDP existants. Ajouter seulement les tables provider_* nécessaires : versions de schéma, catalogue de champs/capacités, vocabulaires/valeurs, raw artifacts immuables, normalisations versionnées, schema drift. Les gros payloads restent dans le stockage d'artefacts.

## Phase G — UI
Interface hybride descriptor-driven + composants HDP. Simple : texte, contenu, géographie, dates, thème/source, limite, tri. Avancé : champs, AND/OR, exact/boost, filtres récursifs, facettes/scopes, taxonomies, fields, profiles/presets, pagination. Expert : modèle HDP + modèle ReliefWeb + méthode/URL/payload/HTTP/native/normalized/provenance/fingerprint/hash/warnings, sans secrets.

## Phase H — routeur, projets, jobs et clients
Tous les points d'entrée utilisent le même ProviderService. Les acquisitions exhaustives utilisent les jobs HDP ; les recherches interactives restent bornées. Étendre clients Python et R aux descriptor/search/item/native/normalized/facets/pagination/provenance/export sans réimplémenter ReliefWeb côté client.

## Phase I — qualité et cinq cycles
Cycle 1 documentation/descriptor ; cycle 2 query/client/config ; cycle 3 storage/provenance/drift ; cycle 4 UI/clients/jobs ; cycle 5 intégration multisource/CI/build. Chaque cycle exécute G1 ReliefWeb, G2 Semantic Core, G3 autres fournisseurs, G4 application complète. Toute régression globale annule le cycle.

Tests déterministes + intégration + live pour toutes les capacités annoncées. Une panne ReliefWeb doit rester isolée et donner `partial` en multisource si les autres réussissent.

## Critère de sortie
Publier quatre métriques distinctes : documentaire, implémentation, qualification, live. Ne déclarer FINALIZED que si 100 % des éléments inventoriés ont un état explicite et chaque élément IMPLEMENTED possède ses tests requis, avec tous les gates obligatoires verts. Sinon utiliser un statut honnête et documenter le blocage, sa preuve, sa conséquence et le correctif attendu.
