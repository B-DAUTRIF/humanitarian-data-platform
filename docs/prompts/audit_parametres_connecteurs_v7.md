# PROMPT — AUDIT SYSTÉMATIQUE PARAMÈTRE-PAR-PARAMÈTRE DES CONNECTEURS HDP V7

## 1. OBJECTIF

Auditer, corriger, tester et qualifier systématiquement chaque connecteur de données intégré à HDP V7, avec une granularité minimale égale à :

**FOURNISSEUR → API → ENDPOINT → OPÉRATION → PARAMÈTRE → VALEUR/TYPE → REQUÊTE NATIVE → RÉPONSE → NORMALISATION → INTERFACE HDP → TEST → PREUVE**

Appliquer immédiatement cette procédure aux connecteurs :

- ReliefWeb ;
- World Bank Health / WDI ;
- HDX, y compris les API HDX effectivement utilisées par HDP ;

puis utiliser cette procédure comme standard obligatoire pour tout nouveau connecteur.

L'audit ne doit jamais considérer un connecteur comme correctement intégré uniquement parce qu'une requête générique fonctionne.

La qualification doit être effectuée **paramètre par paramètre, combinaison pertinente par combinaison pertinente et opération par opération**.

---

## 2. PRINCIPE ANTI-HALLUCINATION

Pour chaque information concernant une API fournisseur, distinguer explicitement :

- DOCUMENTÉ PAR LE FOURNISSEUR ;
- OBSERVÉ DANS L'API RÉELLE ;
- IMPLÉMENTÉ DANS HDP ;
- EXPOSÉ DANS L'INTERFACE ;
- TESTÉ ;
- QUALIFIÉ ;
- PARTIELLEMENT QUALIFIÉ ;
- BLOQUÉ ;
- NON IMPLÉMENTÉ ;
- À VÉRIFIER.

Ne jamais déduire l'existence, le nom, le type ou la sémantique d'un paramètre à partir d'un autre fournisseur.

Ne jamais inventer une correspondance de nomenclature.

Une valeur HDP telle que :

`Rwanda`

ne doit jamais être transformée arbitrairement en :

`RWA`, `RW`, `646`, un UUID, un identifiant HDX, World Bank ou ReliefWeb

sans contrat de transformation vérifié.

---

## 3. INVENTAIRE DOCUMENTAIRE OBLIGATOIRE

Pour chaque fournisseur, rechercher prioritairement les sources officielles : documentation générale, endpoints, OpenAPI/Swagger, schémas JSON/XML/SDMX, paramètres, nomenclatures, valeurs autorisées, pagination, filtres, tris, recherche plein texte, géographie, temporalité, formats, authentification, quotas, erreurs, versionnement, dépréciations et exemples officiels.

Enregistrer les URL, dates de consultation et versions lorsque celles-ci sont disponibles. Une documentation historique ou obsolète ne doit pas être utilisée silencieusement comme contrat actuel.

---

## 4. MATRICE EXHAUSTIVE DES PARAMÈTRES

Construire pour chaque opération une matrice comprenant au minimum : fournisseur, API, version, endpoint, méthode, opération HDP, paramètre natif, emplacement path/query/body/header, type natif, cardinalité, caractère obligatoire, défaut fournisseur, valeurs autorisées, minimum/maximum, nomenclature, sémantique, compatibilités, incompatibilités, pagination, limitations, paramètre canonique HDP, transformation HDP→fournisseur, preuve de transformation, composant UI, validation UI, validation backend, visibilité de la requête native, provenance, test déterministe, test live, statut et dette.

Aucun paramètre documenté et pertinent pour HDP ne doit disparaître silencieusement.

---

## 5. AUDIT DES TYPES — OBLIGATOIRE

Tester systématiquement chaque paramètre selon son type.

### Chaîne de caractères
Tester valeur valide, chaîne vide, espaces, accents, Unicode, caractères spéciaux, casse, longueur limite et valeur inconnue.

### Numérique
Tester minimum, maximum, valeur nominale, zéro, négatif si pertinent, dépassement et type erroné.

### Booléen
Tester les représentations réellement autorisées par le fournisseur.

### Liste / enum
Tester modalités importantes, valeur invalide, liste vide et multi-sélection si supportée.

### Date
Tester date valide, début, fin, intervalle, date unique, ordre inversé, format invalide et bornes fournisseur.

### Géographie
Tester nom humain, ISO2, ISO3, M49, identifiant fournisseur, agrégat régional, pays, région et valeur inconnue. Ne jamais confondre un agrégat World Bank avec un pays ISO3.

### UUID / identifiant technique
Un UUID de projet HDP est un identifiant technique. Une géographie, un mot-clé, un code fournisseur ou une valeur utilisateur ne doit jamais pouvoir être sérialisé accidentellement dans ce champ.

---

## 6. AUDIT DU BINDING UI → PAYLOAD

Pour chaque champ vérifier explicitement :

`COMPOSANT UI → ID HTML → VARIABLE JS → CHAMP JSON → MODÈLE PYDANTIC → PARAMÈTRE CANONIQUE → TRADUCTION FOURNISSEUR`

Tester mauvais champ, permutation, champ masqué encore sérialisé, autocomplétion, valeur résiduelle, défaut incorrect, conversion implicite, confusion texte/UUID, pays/projet, date/limite, checkbox, liste multiple et booléen transformé en chaîne.

Un test de non-régression doit être créé pour chaque défaut réellement découvert.

---

## 7. MODES SIMPLE / AVANCÉ / EXPERT

Simple n'expose que les concepts nécessaires et utilise des valeurs techniques sûres. Avancé expose les capacités structurées avec aide, défauts et domaines. Expert expose paramètre HDP, valeur canonique, transformation, paramètre et valeur fournisseur, endpoint, méthode, requête native, Query Plan, complétude, provenance, erreurs et empreintes sans jamais exposer les secrets. Les trois modes doivent produire des requêtes sémantiquement cohérentes.

---

## 8. AUDIT SÉMANTIQUE

Pour chaque paramètre canonique :

`INTENTION UTILISATEUR → CONCEPT HDP → NOMENCLATURE → CAPACITÉ FOURNISSEUR → MAPPING VÉRIFIÉ → VALEUR FOURNISSEUR → PARAMÈTRE NATIF → REQUÊTE → RÉPONSE`

Produire la preuve de chaque transformation non triviale. En absence de preuve, préférer `BLOCKED_MISSING_MAPPING` à une traduction supposée.

---

## 9. TESTS UNITAIRES PAR PARAMÈTRE

Chaque paramètre qualifiable doit couvrir : valeur valide, invalide, limite pertinente, sérialisation, traduction fournisseur, requête générée, normalisation, provenance, comportement d'erreur et absence de confusion avec les autres paramètres.

Pour les fonctionnalités critiques, exécuter **10 cycles déterministes de test/debug/audit**. Un cycle non exécuté n'est jamais PASS.

---

## 10. TESTS DE COMBINAISONS

Construire une couverture pairwise/combinatoire pertinente : thème+géographie, thème+dates, géographie+dates, thème+géographie+dates, pagination+filtres, limite+pagination, plusieurs indicateurs, plusieurs pays, booléens+filtres, paramètres fournisseur+paramètres projet. Documenter la stratégie de couverture.

---

## 11. TESTS LIVE

Séparer strictement tests déterministes et tests live fournisseur. Chaque test suit :

`TEST → PRÉCONDITION → ACTION → REQUÊTE NATIVE → ATTENDU → OBSERVÉ → PREUVE → STATUT`

Statuts : PASS / FAIL / BLOCKED / NOT TESTED.

---

## 12. ANTI-FAUX-ZÉRO

Interdire `empty_valid` lorsque recherche bornée, pagination incomplète, échantillonnage, post-filtrage, mapping géographique/thématique incertain, erreur fournisseur, refus d'authentification, timeout, schéma modifié ou requête non qualifiée. Utiliser un statut explicite approprié (`partial`, `bounded`, `provider_error`, `authentication_error`, `timeout`, `schema_drift`, `blocked_missing_mapping`, etc.).

---

## 13. NOMENCLATURES GÉOGRAPHIQUES

Auditer :

`VALEUR UTILISATEUR → CONCEPT GÉOGRAPHIQUE HDP → ISO2 → ISO3 → M49 → IDENTIFIANT FOURNISSEUR`

avec preuve et provenance. Tester Rwanda, noms composés, caractères particuliers, agrégats, territoires et valeurs inexistantes. Les identifiants fournisseur restent distincts des identifiants canoniques HDP.

---

## 14. EXPOSITION EXHAUSTIVE

Comparer automatiquement :

`PARAMÈTRES DOCUMENTÉS ↔ DESCRIPTOR ↔ SOURCE_REGISTRY ↔ BACKEND ↔ UI ↔ CLIENT PYTHON ↔ CLIENT R ↔ TESTS ↔ DOCUMENTATION`

Toute différence doit être classée : volontairement non exposé, non pertinent, expérimental, non implémenté, bloqué, dette technique ou anomalie.

---

## 15. CLIENTS PYTHON ET R

Pour chaque paramètre qualifié accessible à l'utilisateur, vérifier API HDP, UI, client Python et client R ; fournir des exemples reproductibles équivalents. Ne jamais déclarer les clients complets si la fonctionnalité n'y existe pas.

---

## 16. DOCUMENTATION UTILISATEUR

Chaque paramètre exposé doit fournir nom lisible, nom natif, description, type, défaut, valeurs autorisées, exemple, impact, documentation fournisseur, niveau Simple/Avancé/Expert et statut de qualification.

---

## 17. CONTRÔLE DE SCHÉMA ET DRIFT

Enregistrer version API, schéma, champs, types, nomenclatures et date de vérification lorsque possible. Toute modification incompatible doit produire `SCHEMA_DRIFT` et ne doit pas être absorbée silencieusement.

---

## 18. RELIEFWEB

Auditer tous les paramètres documentés des endpoints utilisés, particulièrement appname/application, query, filtres, fields, facets, sort, pagination, offset/limit, profiles, geography, dates, formats et opérateurs. Ne déclarer qualifiées que les capacités acceptées dans les tests live. HTTP 403 reste une erreur fournisseur/authentification, jamais un résultat vide.

---

## 19. WORLD BANK

Auditer source, indicator, country, date, page, per_page, MRV, MRNEV, gapfill, frequency, footnote, language, format, metadata, topics, sources, agrégats, multi-country et multi-indicator. Distinguer impérativement pays et agrégats World Bank. Les capacités documentées mais non qualifiées (SDMX/formats alternatifs) restent explicitement hors périmètre qualifié.

---

## 20. HDX

Ne jamais traiter HDX comme une API unique. Auditer indépendamment les contrats effectivement intégrés : HDX/CKAN, HDX HAPI, COD et tout autre service HDX réellement présent. Ne jamais transférer automatiquement une capacité CKAN vers HAPI ou inversement.

---

## 21. TEST DE NON-CONTAMINATION ENTRE PARAMÈTRES

Pour chaque paramètre `P_i`, modifier uniquement `P_i` et vérifier que les autres `P_j` restent inchangés. Cas obligatoires : `location="Rwanda"` ne modifie jamais `project_id`; `project_id=<UUID>` ne modifie jamais location; `result_limit=50` ne modifie pas la pagination fournisseur sans règle documentée; `date_from` ne remplace jamais `date_to`. Cette famille est obligatoire après l'incident UUID/Rwanda.

---

## 22. TRAÇABILITÉ

`REQUIREMENT ↔ SOURCE ↔ ENDPOINT ↔ PARAMETER ↔ DESCRIPTOR ↔ REGISTRY ↔ UI ↔ BACKEND ↔ CLIENT PYTHON ↔ CLIENT R ↔ TEST ↔ DOCUMENTATION ↔ EVIDENCE ↔ STATUS`

La matrice doit être générée dans le dépôt.

---

## 23. CI GITHUB

Les gates empêchent la promotion en cas de corruption `project_id`, mauvais binding UI, paramètres documentés perdus sans justification, mapping non vérifié, faux `empty_valid`, régression connecteur, incompatibilité Windows ou échec clients Python/R qualifiés.

---

## 24. LOG GITHUB

Pour chaque anomalie conserver date, connecteur, endpoint, paramètre, symptôme, cause, reproduction, correction, commit, test, résultat et dette. `project_id = "rwanda"` est le cas de référence des contaminations inter-paramètres.

---

## 25. RAPPORT PAR CONNECTEUR

Pour ReliefWeb, World Bank et chaque contrat HDX produire inventaire documentaire/API, matrice exhaustive, mapping HDP, couverture UI/backend/Python/R, résultats déterministes/live, anomalies, corrections, limites, dette, évaluation métier et verdict.

---

## 26. VERDICT PAR PARAMÈTRE

Statuts : IMPLÉMENTÉ ET QUALIFIÉ ; IMPLÉMENTÉ MAIS NON QUALIFIÉ ; PARTIELLEMENT IMPLÉMENTÉ ; SPÉCIFIÉ / PLANIFIÉ ; EXPÉRIMENTAL ; LEGACY / COMPATIBILITÉ ; DÉPRÉCIÉ ; BLOQUÉ ; À VÉRIFIER ; ABSENT. Le statut global est dérivé de la matrice détaillée.

---

## 27. PROMOTION

La qualification d'un connecteur ne qualifie ni tous ses paramètres ni HDP entier. Les tests déterministes ne remplacent pas le live requis ; Linux ne remplace pas Windows. Ne promouvoir stable/main que lorsque les gates prévus sont réellement PASS.

---

## 28. ORDRE D'EXÉCUTION

A. ReliefWeb : documentation → paramètres → binding → tests unitaires → 10 cycles → combinaisons → live → UI → Python/R → rapport.

B. World Bank Health : même procédure.

C. HDX : séparer d'abord les services puis appliquer le protocole à chacun.

Enfin, réaliser l'audit transversal ReliefWeb ↔ World Bank ↔ HDX.

---

## 29. AUDIT TRANSVERSAL FINAL

Construire :

`CONCEPT HDP | RELIEFWEB | WORLD BANK | HDX | TYPE HDP | NOMENCLATURE | TRANSFORMATION | PREUVE`

pour query, geography, date_from, date_to, pagination, limit, sort, fields, format, language, project_id et source configuration. Vérifier qu'un concept commun ne masque jamais des sémantiques fournisseur différentes.

---

## 30. CRITÈRE FINAL

L'objectif n'est pas seulement « la requête fonctionne » mais :

> **Chaque paramètre exposé par HDP possède une origine documentée, un type vérifié, une sémantique explicite, une liaison UI correcte, une traduction fournisseur vérifiée, une requête native inspectable, une provenance conservée, des tests reproductibles et un statut de qualification démontrable.**

Tout écart reste visible. Aucune fonctionnalité n'est qualifiée sans preuve d'exécution. Livrables finaux : rapport global, rapports ReliefWeb/World Bank/HDX, matrices CSV/JSON/Markdown, tests, logs GitHub, commits, résultats CI, anomalies corrigées/restantes, dette et verdict exact.
