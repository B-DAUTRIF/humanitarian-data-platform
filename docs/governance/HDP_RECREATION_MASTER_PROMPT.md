# HDP — Prompt général canonique de recréation

Version de gouvernance : 2026-08-31 — V7 en développement.

## Mission
Reconstruire HDP comme plateforme modulaire de recherche, acquisition, provenance, analyse et export de données humanitaires/sanitaires. La fidélité aux API sources prime sur une uniformisation artificielle, sans sacrifier les contrats communs HDP, la robustesse multisource, les projets, les jobs, l'installation Windows ni le déploiement Linux.

## Architecture normative
Flux commun : `User intent -> Semantic Core -> QueryPlan -> ProviderOperation -> Provider-native model -> ProviderService -> HTTP/API -> RawArtifact immutable -> versioned normalization -> HDP record -> analysis/export`.

Trois couches sont obligatoires : (1) contrat commun HDP, (2) modèle de capacités par fournisseur, (3) contrat natif fournisseur. Une capacité native propre à un fournisseur ne doit jamais être inventée pour les autres.

Le Provider Core expose un `ProviderDescriptor` comprenant au minimum identity, contract/version, operations, content types, parameters, fields, capabilities, vocabularies, mappings, configuration schema, UI schema, runtime limits et evidence. Les composants strictement fournisseur restent isolés sous `providers/<provider>/`; les composants ne deviennent génériques qu'après démonstration d'un besoin partagé par au moins deux fournisseurs.

Tous les points d'entrée (UI Simple/Avancé/Expert, routeur sémantique, projet, scheduler/job, API, clients R/Python) convergent vers le même ProviderService. Le routeur ne fabrique jamais directement une URL fournisseur.

## Stockage et provenance
PostgreSQL contient les métadonnées, relations, capacités, états, mappings et références d'artefacts. JSONB conserve les particularités fournisseur quand le relationnel n'apporte pas de bénéfice. Les gros payloads sont des RawArtifacts immuables stockés par référence/hash, jamais écrasés. Toute normalisation et tout mapping sont versionnés et traçables.

Préférer des tables génériques `provider_*` (schema versions, fields, capabilities, vocabularies, vocabulary values, raw artifacts, normalizations, schema drift) aux duplications `providername_*`, sauf besoin réellement spécifique et justifié.

## Configuration
Résolution générique : `provider defaults -> HDP global settings -> project settings -> execution override` (ce dernier uniquement si le descripteur l'autorise). Chaque champ de configuration déclare sa visibilité `public|internal|secret`. Les secrets ne doivent jamais apparaître dans logs, provenance publique, fingerprint sérialisé ou UI Expert.

## UI
UI hybride : le ProviderDescriptor détermine données, validation, domaines et capacités ; des composants HDP conçus explicitement assurent l'ergonomie (KeywordSearch, GeographyPicker, DateRangePicker, FieldSelector, NestedFilterBuilder, FacetPanel, PaginationControl, NativeRequestInspector). Simple masque la complexité ; Avancé expose les capacités structurées ; Expert expose le contrat et les requêtes natives sans exposer les secrets.

## Sémantique et complétude
Chaque critère est classé `native_filter|translated_filter|post_filter|output_only|unsupported|blocked_missing_mapping`. Invariant P0 : `post_filter` sur un ensemble non exhaustif ne peut jamais conclure `empty_valid`. Une erreur fournisseur ne peut jamais devenir un résultat vide valide.

Une panne d'un fournisseur dans une recherche multisource doit produire un résultat global `partial` lorsque d'autres fournisseurs réussissent, jamais un échec global par défaut.

## Performance et jobs
Distinguer recherche interactive bornée, acquisition exhaustive asynchrone, synchronisation de nomenclatures/cache et analyse. Les opérations longues utilisent le système commun de jobs et de progression ; aucun fournisseur ne crée son propre ordonnanceur.

## Compatibilité
Le cœur fournisseur reste Python/FastAPI et doit préserver Windows 10/11 x64 + installateur, Docker/serveur Linux et PostgreSQL/PostGIS. R reste facultatif pour analyse/rapports et client. SPIP reste un consommateur éditorial facultatif en aval ; ni R ni SPIP ne se trouvent sur le chemin obligatoire d'acquisition.

## Qualification globale
Chaque cycle fournisseur exécute quatre gates : G1 connecteur ; G2 Semantic Core ; G3 autres connecteurs/multisource ; G4 application complète (projets/jobs/clients/build). Une amélioration locale qui casse HDP est un échec.

Mesurer séparément couverture documentaire, couverture d'implémentation, couverture de qualification et couverture live. Ne jamais annoncer 100 % sans matrice machine-readable.

## Protocole canonique de qualification de tout connecteur
Pour CHAQUE connecteur HDP, appliquer le protocole suivant. Il constitue le protocole de qualification permanent et doit être conservé lors de toute recréation de l'application.

1. Auditer d'abord la documentation officielle actuelle et construire un inventaire machine-readable des endpoints, opérations collection/item, méthodes HTTP, paramètres, champs, domaines/nomenclatures, recherche, filtres, facettes, pagination, tri, profils/presets, limites, erreurs, structure de réponse, configuration, provenance, UI et clients. Classer les preuves `DOCUMENTED|LIVE_VERIFIED|INFERRED|UNVERIFIED|CONFLICTING_DOCUMENTATION` et l'état HDP `NOT_IMPLEMENTED|PARTIAL|IMPLEMENTED|QUALIFIED|BLOCKED`.
2. Construire une taxonomie des cas d'usage métier réellement permis par le fournisseur. Ne jamais inventer un usage non supporté par le contrat natif.
3. Pour chaque fonctionnalité inventoriée, générer cinq cas distincts : nominal simple, nominal complexe, limite, négatif/vide légitime, erreur ou contrainte fournisseur. Chaque cas possède `case_id`, objectif métier, content type/opération, entrée, comportement natif attendu, comportement HDP attendu, complétude/statut attendu, preuve, résultat réel, pass/fail et defect_id.
4. Pour chaque cas, effectuer jusqu'à cinq cycles `TEST -> DIAGNOSTIC -> CORRECTION JUSTIFIÉE -> RETEST -> RÉGRESSION`. Une correction n'est réalisée que lorsqu'un défaut HDP est démontré. Si le cas est déjà conforme, les cycles suivants deviennent des contrôles de stabilité, robustesse et non-régression ; il est interdit de modifier artificiellement un code correct pour atteindre cinq changements.
5. Ajouter des tests transversaux combinatoires et négatifs : filtres combinés, pagination interrompue, vrai résultat vide, résultat non exhaustif, timeout, 4xx/403/404/429/5xx, schéma inattendu, Unicode, volumes importants, annulation/reprise de job et panne du fournisseur dans une recherche multisource. Préserver l'invariant `post_filter + non_exhaustive != empty_valid`.
6. Vérifier le chemin complet `UI -> ProviderService -> requête native -> réponse native -> RawArtifact -> normalisation -> provenance -> résultat`, dans les modes Simple/Avancé/Expert. Vérifier aussi les clients R/Python sans dupliquer la logique fournisseur.
7. Après chaque groupe significatif de corrections, exécuter G1 connecteur, G2 Semantic Core, G3 autres fournisseurs/multisource, G4 application complète/projets/jobs/clients/build. Une régression globale annule la réussite locale.
8. Maintenir inventaire des fonctionnalités, matrice des cas, matrice de tests, journal des cinq cycles, anomalies, corrections/commits, résultats live et couvertures documentaire/implémentée/testée/live.
9. Produire un rapport final avec périmètre, résultats, erreurs, performances, robustesse, fidélité API, qualité normalisation/provenance, ergonomie, maintenabilité et bloqueurs. Noter séparément sur 100 fidélité API, couverture fonctionnelle, robustesse, tests, interface, intégration HDP, R/Python, provenance/reproductibilité et maintenabilité. Toute note globale doit documenter son calcul.
10. Le statut final est exclusivement `QUALIFIED`, `QUALIFIED_WITH_KNOWN_LIMITATIONS`, `PARTIALLY_IMPLEMENTED` ou `BLOCKED`. `FINALIZED` n'est jamais déduit de tests déterministes seuls ; une capacité obligatoire non testable live reste explicitement non qualifiée.

Ce protocole est générique. Les détails propres à une API restent dans son package/descripteur et sa documentation de qualification ; ils ne deviennent jamais des règles universelles sans preuve d'un besoin partagé.

## ReliefWeb — contrat de référence individualisé
ReliefWeb V2 doit être transposé fidèlement sans devenir le modèle universel HDP. Inventorier et maintenir les 9 content types officiellement documentés (`reports`, `disasters`, `countries`, `jobs`, `training`, `sources`, `blog`, `book`, `references`), les endpoints collection/item, GET/POST, query, recherche avancée/Lucene, `.exact`, boosts, filtres récursifs AND/OR/négation, facettes et scopes, pagination, tris, profiles, presets, fields include/exclude, slim, verbose, résultats, champs et taxonomies/références.

Configuration ReliefWeb : valeur HDP demandée `HDP_plateforme`, surcharge projet autorisée, résolution `project -> global -> default`. Cette valeur est un identifiant public de l'application, pas un secret. Toutefois sa validité auprès du fournisseur doit être prouvée par test live ; HTTP 403 doit rester une erreur de configuration/fournisseur, jamais être masqué.

Architecture cible : `providers/reliefweb/{descriptor,query,client,metadata,normalize,semantic,ui,service}` avec compatibilité transitoire vers les anciens modules. L'ancien exécuteur limité à `/v2/reports` doit être éliminé comme chemin parallèle après migration vers le ProviderService.

Les réponses ReliefWeb natives sont conservées immuables avant normalisation. Le connecteur doit gérer les recherches collection, objets individuels, modes interactif/exhaustif, facettes, taxonomies et inspection Expert. L'API de publication ReliefWeb est un sous-système séparé, authentifié, et ne doit pas être confondue avec le connecteur de lecture.

## ReliefWeb — qualification obligatoire
Chaque fonctionnalité inventoriée possède `documentation_status`, `implementation_status`, `unit_test`, `integration_test`, `live_test`, `ui_test`, `status`, `notes`. Tests minimaux : chaque content type, item applicable, query, AND/OR, exact, boost, filtres simples/imbriqués/négation, facettes/scopes, tri, profiles/presets, fields, pagination, appname global/projet, réponses vides réelles, 4xx/403/429/5xx/timeout/schema drift et isolation multisource.

Appliquer le protocole canonique ci-dessus à ReliefWeb. Effectuer cinq cycles par cas sans imposer cinq modifications : `TEST -> DIAGNOSTIC -> CORRECTION SI DÉFAUT -> RETEST -> RÉGRESSION`. Le statut FINALIZED est interdit si un gate obligatoire échoue. Utiliser `QUALIFIED_WITH_KNOWN_LIMITATIONS`, `PARTIALLY_IMPLEMENTED` ou `BLOCKED` selon les preuves.

## Anti-hallucination
Chaque affirmation fournisseur est `DOCUMENTED|LIVE_VERIFIED|INFERRED|UNVERIFIED|CONFLICTING_DOCUMENTATION`. Les règles de production ne reposent jamais sur INFERRED/UNVERIFIED sans garde-fou. En cas de divergence documentation/API, conserver le conflit, tester, journaliser et éviter de fabriquer une règle.

## Git et livraison
Développer sur branche dédiée, commits atomiques, PR draft pendant qualification. Ne pas fusionner main sans autorisation explicite. Un EXE/archive n'est qualifié qu'après gates correspondants verts ; un artifact construit avant une modification fonctionnelle est superseded.

Ce fichier est le prompt général canonique de recréation : toute documentation ou prompt versionné doit rester cohérent avec ces invariants.