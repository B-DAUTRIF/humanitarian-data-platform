# ReliefWeb V2 — Rapport de qualification par cas d'usage

Date: 2026-08-31
Branche: `feat/v7-reliefweb-implementation`
Protocole: `docs/governance/HDP_RECREATION_MASTER_PROMPT.md` — protocole canonique de qualification des connecteurs.

## Résumé exécutif

Le harnais déterministe `tools/v7_reliefweb_use_case_qualification.py` a inventorié 33 fonctionnalités/domaines testables du connecteur ReliefWeb actuel. Pour chaque fonctionnalité, exactement 5 cas ont été construits, soit 165 cas. Chaque cas a subi 5 cycles de vérification (test, diagnostic, retest/stabilité et régression), soit 825 cycles. Tous les 165 cas déterministes ont réussi. Aucun changement artificiel du code n'a été effectué lorsqu'un cas était déjà conforme.

Le connecteur n'est cependant PAS qualifié en production/live : le test fournisseur obligatoire reçoit HTTP 403 pour `appname=HDP_plateforme` sur `/v2/reports`. Ce blocage fournisseur/configuration est volontairement conservé comme gate rouge. Statut global : `PARTIALLY_IMPLEMENTED / BLOCKED_LIVE`.

## Inventaire des cas d'usage couverts

Les familles couvertes par le harnais sont : recherche thématique libre ; recherche limitée à des champs ; AND/OR ; recherche exacte ; syntaxe avancée/Lucene et boosts transmis nativement ; filtres simples ; filtres multi-valeurs ; filtres récursifs ; négation ; plages de dates/nombres ; facettes ; filtres de facette ; scopes ; intervalles temporels ; tri ; pagination ; profiles ; presets ; projection include/exclude ; slim ; verbose ; priorité appname projet/global/défaut ; erreurs de validation ; opérations sur chacun des 9 content types (`reports`, `disasters`, `countries`, `jobs`, `training`, `sources`, `blog`, `book`, `references`) ; normalisation de réponses natives.

Les usages métier représentés comprennent notamment recherche de rapports malaria/choléra/sécurité alimentaire, combinaison pays/thème, filtrage temporel, exclusion, exploration par source/pays/thème/format, consultation de listes et objets individuels, emplois et formations, métadonnées pays/catastrophes/sources, taxonomie `references`, inspection et personnalisation des réponses.

## Résultats automatisés observés en CI

- 33 fonctionnalités/domaines ;
- 5 cas par fonctionnalité ;
- 165 cas déterministes ;
- 5 cycles par cas ;
- 825 cycles exécutés ;
- 165 cas réussis ;
- 0 défaut déterministe restant dans ce périmètre ;
- suite `unittest` globale du job : 59 tests, tous réussis ;
- client Python : 8 tests, tous réussis ;
- audit offline V7 : `ready` ;
- sentinel multisource : réussi et a continué à produire des résultats World Bank/UN-SDG malgré des fournisseurs bloqués ou en erreur ;
- build Windows générique sur le même head : réussi ;
- gate ReliefWeb live : échec HTTP 403, donc le job `HDP V7 full qualification` reste rouge et le build V7 qualifié dépendant de ce gate n'est pas produit par ce workflow.

## Cycles de test/debug/correction

Pour chaque cas, les cinq cycles sont enregistrés dans la sortie JSON générée par le harnais. Le protocole interdit de modifier le code lorsqu'aucun défaut HDP n'est démontré. Les 165 cas ont donc suivi cinq cycles de stabilité/régression sans correction artificielle.

Le défaut live observé est distinct : `HDP_plateforme` est correctement résolu comme appname public et transmis, mais ReliefWeb répond 403. Le comportement HDP attendu est de remonter une erreur de configuration/fournisseur, pas de convertir l'échec en tableau vide ni de contourner le contrôle. Aucune correction locale n'est justifiée tant que la cause fournisseur (approbation/orthographe/politique d'accès) n'est pas établie.

## Évaluation du connecteur

### Fidélité API — 88/100
Le modèle natif couvre les mécanismes majeurs documentés : 9 content types, list/item, GET/POST, query, filtres récursifs, facettes, pagination, tri, profiles, presets, projection, slim et verbose. La note reste inférieure à 100 car l'inventaire champ-par-champ et la qualification live exhaustive des taxonomies ne sont pas encore terminés.

### Couverture fonctionnelle — 82/100
Le noyau de requête et le ProviderService sont riches. Restent notamment à achever l'acquisition exhaustive via jobs communs, la synchronisation complète des champs/taxonomies, la persistance RawArtifact sur tous les chemins et certaines fonctions avancées de l'UI.

### Robustesse — 86/100
Les validations, la limite de profondeur des filtres, la classification 403/429 et la non-conversion des erreurs en résultats vides sont positives. La qualification réelle contre le fournisseur est toutefois bloquée.

### Tests — 91/100
La nouvelle matrice apporte 165 cas et 825 cycles déterministes, en plus des suites existantes. La couverture live reste insuffisante à cause du 403.

### Interface — 72/100
Les modes Simple/Avancé/Expert existent et exposent une partie importante du contrat. La génération/validation intégrale depuis l'inventaire des champs et les contrôles spécialisés par type nécessitent encore une qualification UI approfondie.

### Intégration HDP — 88/100
Le connecteur passe par Provider Core/ProviderService et la panne ReliefWeb n'empêche pas les autres fournisseurs du sentinel multisource de réussir. Les gates G2/G3 restent néanmoins à considérer au niveau de la qualification complète V7.

### R/Python — 78/100
Les clients existent et les tests Python sont verts. Une matrice ReliefWeb dédiée R/Python pour toutes les familles fonctionnelles doit encore être étendue.

### Provenance/reproductibilité — 84/100
L'appname public est distingué des secrets et affecte le fingerprint ; les objets natifs sont conservés lors de la normalisation. Le stockage effectif des RawArtifacts et la chaîne complète de provenance doivent encore être câblés partout.

### Maintenabilité — 90/100
Le découpage Provider Core + package ReliefWeb limite la contamination du cœur HDP et permet la réutilisation des invariants sans imposer le modèle ReliefWeb aux autres sources.

Note indicative globale (moyenne arithmétique non pondérée des neuf dimensions) : **84,3/100**. Cette note mesure l'état d'ingénierie actuel, pas une qualification production.

## Bloqueurs et travaux restant obligatoires

1. Résoudre ou faire confirmer par ReliefWeb le HTTP 403 de `HDP_plateforme`, puis relancer tous les tests live.
2. Compléter l'inventaire exhaustif champ-par-champ à partir des tables officielles et le rendre consommable par le ProviderDescriptor/UI.
3. Qualifier les taxonomies et `references` dynamiquement.
4. Finaliser RawArtifact/persistance/provenance sur tous les chemins.
5. Implémenter et tester l'acquisition paginée exhaustive via les jobs HDP.
6. Étendre la matrice aux tests UI E2E et aux méthodes R/Python ReliefWeb dédiées.
7. Relancer G1, G2, G3 et G4, puis Windows 10/11 réel ou VM avant toute qualification stable.

## Conclusion

Le connecteur ReliefWeb est techniquement bien structuré et son contrat déterministe est désormais fortement testé. Il ne doit toutefois pas être présenté comme `QUALIFIED` ou `FINALIZED` tant que l'accès live avec l'appname approuvé n'est pas démontré et que les inventaires/chemins exhaustifs restant ouverts ne sont pas qualifiés.
