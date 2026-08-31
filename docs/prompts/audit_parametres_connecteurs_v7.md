# AUDIT SYSTÉMATIQUE PARAMÈTRE-PAR-PARAMÈTRE DES CONNECTEURS HDP V7

Statut : protocole normatif HDP V7. Ce document complète `dev_connecteurs.md` et le prompt maître V7.

## Objectif

Auditer, corriger, tester et qualifier chaque connecteur avec la granularité minimale :

`FOURNISSEUR → API → ENDPOINT → OPÉRATION → PARAMÈTRE → VALEUR/TYPE → REQUÊTE NATIVE → RÉPONSE → NORMALISATION → INTERFACE HDP → TEST → PREUVE`.

Application immédiate : ReliefWeb, World Bank Health/WDI, HDX/CKAN, HDX HAPI et les fonctions COD effectivement exécutées par HDP. Un connecteur n'est jamais qualifié uniquement parce qu'une requête générique fonctionne.

## Anti-hallucination et statuts

Pour toute capacité distinguer : DOCUMENTÉ PAR LE FOURNISSEUR ; OBSERVÉ DANS L'API RÉELLE ; IMPLÉMENTÉ DANS HDP ; EXPOSÉ DANS L'INTERFACE ; TESTÉ ; QUALIFIÉ ; PARTIELLEMENT QUALIFIÉ ; BLOQUÉ ; NON IMPLÉMENTÉ ; À VÉRIFIER.

Ne jamais inventer un paramètre, une valeur ou une nomenclature. `Rwanda` ne devient `RWA`, `RW`, `646`, UUID ou identifiant fournisseur que par une transformation documentée et testée. En absence de preuve utiliser `BLOCKED_MISSING_MAPPING`.

## Recueil documentaire

Pour chaque fournisseur conserver les preuves officielles : documentation générale, endpoints, OpenAPI/Swagger/SDMX/CKAN, schémas, paramètres, nomenclatures, valeurs autorisées, pagination, filtres, tris, plein texte, géographie, temporalité, formats, authentification, quotas, erreurs, versions, dépréciations et exemples. Enregistrer URL, date de vérification et version lorsqu'elle existe.

## Matrice obligatoire

Chaque ligne de matrice porte au minimum : fournisseur, API, version, endpoint, méthode, opération HDP, paramètre natif, emplacement path/query/body/header, type, cardinalité, obligatoire/conditionnel, valeur par défaut, domaine, min/max, nomenclature, sémantique, compatibilités/incompatibilités, pagination, limites, concept canonique HDP, transformation HDP→fournisseur, preuve, composant UI, validation UI, validation backend, requête native visible, provenance, test déterministe, test live, statut et dette.

Aucun paramètre documenté pertinent ne disparaît silencieusement. Un paramètre volontairement non exposé reçoit une justification (`NON_PERTINENT_PUBLIC`, `SECURITY_RESTRICTED`, `EXPERIMENTAL`, `BLOCKED`, etc.).

## Tests par type

Chaîne : valide, vide, espaces, Unicode, accents, caractères spéciaux, casse, longueur limite et valeur inconnue. Numérique : minimum, maximum, nominal, zéro, négatif lorsque pertinent, dépassement et mauvais type. Booléen : représentations réellement admises. Enum/listes : modalités, invalide, vide et multi-valeurs. Dates : valeur, intervalle, ordre inversé, format invalide et bornes. Géographie : nom, ISO2, ISO3, M49, identifiant fournisseur, pays, territoire, agrégat et inconnu. UUID : aucun texte métier ne peut être sérialisé dans un identifiant technique.

## Binding UI → payload

Pour chaque champ vérifier :

`COMPOSANT UI → ID HTML → VARIABLE JS → CHAMP JSON → MODÈLE PYDANTIC → CONCEPT HDP → TRADUCTION FOURNISSEUR`.

Tester mauvais champ, permutation, champ masqué sérialisé, autocomplétion, valeur résiduelle, défaut incorrect, conversion implicite, confusion texte/UUID, pays/projet, date/limite, checkbox, multi-sélection et booléen/chaîne. Chaque défaut découvert produit un test de non-régression.

## Modes Simple / Avancé / Expert

Simple expose les concepts métier et utilise des valeurs techniques déterministes. Avancé expose les paramètres fournisseur qualifiés avec type, aide, défaut, domaine et documentation. Expert expose paramètres HDP/natifs, transformation, endpoint, méthode, requête native, Query Plan, complétude, provenance, erreurs et empreintes.

## Audit sémantique

Pipeline obligatoire : `INTENTION → CONCEPT HDP → NOMENCLATURE → CAPACITÉ FOURNISSEUR → MAPPING VÉRIFIÉ → VALEUR FOURNISSEUR → PARAMÈTRE NATIF → REQUÊTE → RÉPONSE → NORMALISATION → PROVENANCE`.

## Tests unitaires et cycles

Chaque paramètre qualifiable doit couvrir valeur valide, invalide, limite, sérialisation, traduction, requête générée, normalisation, provenance, erreur et non-contamination. Les fonctionnalités critiques sont soumises à 10 cycles déterministes test/debug/audit. Un cycle non exécuté n'est jamais PASS.

Les combinaisons comprennent au minimum thème+géographie, thème+dates, géographie+dates, thème+géographie+dates, pagination+filtres, limite+pagination, multi-indicateur, multi-pays, booléens+filtres et paramètres projet+fournisseur. Une stratégie pairwise est admise si elle est documentée.

## Live et anti-faux-zéro

Séparer déterministe et live. Format : `TEST → PRÉCONDITION → ACTION → REQUÊTE NATIVE → ATTENDU → OBSERVÉ → PREUVE → STATUT`, avec PASS/FAIL/BLOCKED/NOT TESTED.

`empty_valid` est interdit si la preuve d'absence est insuffisante : collecte bornée, pagination incomplète, échantillonnage, post-filtrage, mapping incertain, erreur fournisseur, authentification, timeout, schema drift ou requête non qualifiée. Utiliser `partial`, `provider_error`, `authentication_error`, `timeout`, `schema_drift`, `blocked_missing_mapping`, etc.

## Géographie

Auditer `VALEUR UTILISATEUR → CONCEPT HDP → ISO2 → ISO3 → M49 → IDENTIFIANT FOURNISSEUR`. Tester Rwanda, nom composé, caractères particuliers, agrégat, territoire et valeur inexistante. Les agrégats World Bank ne sont jamais assimilés à des ISO3 souverains.

## Couverture exhaustive

Comparer automatiquement : `DOCUMENTATION ↔ DESCRIPTOR ↔ SOURCE_REGISTRY ↔ BACKEND ↔ UI ↔ PYTHON ↔ R ↔ TESTS ↔ DOC`. Tout écart est classé et justifié.

## ReliefWeb

Auditer les 9 content types et les paramètres documentés : `appname`, `query` (`value`, `fields`, `operator`), `filter` (`field`, `value`, `operator`, `negate`, `conditions`), `facets` (`field`, `name`, `limit`, `sort`, `filter`, `interval`, `scope`), `limit`, `offset`, `sort`, `profile`, `preset`, `fields` (`include`, `exclude`), `slim`, `verbose`. Les items n'acceptent que `fields` et `profile`. HTTP 403 reste une erreur d'autorisation, jamais zéro donnée.

## World Bank

Auditer `source`, `country`, `indicator`, `date`, `page`, `per_page`, `mrv`, `mrnev`, `gapfill`, `frequency`, `footnote`, `format`, `language`, métadonnées, topics, sources, agrégats, multi-country et multi-indicator. Distinguer strictement pays et agrégats. Les formats/SDMX non qualifiés restent explicitement hors périmètre.

## HDX

Ne jamais fusionner les sémantiques HDX/CKAN et HDX HAPI. Pour CKAN `package_search`, auditer au minimum `q`, `fq`, `sort`, `rows`, `start`, `facet`, `facet.mincount`, `facet.limit`, `facet.field`, ainsi que les options publiques/avancées documentées. Pour HAPI v2, auditer les paramètres communs (`app_identifier`, `output_format`, `limit`, `offset`) puis chaque filtre de chaque endpoint via le contrat courant/sandbox ; `location_code` est ISO3/p-code au niveau pays selon la documentation HAPI. COD est audité séparément selon les opérations réellement présentes.

## Non-contamination

Pour chaque paramètre P_i, modifier seulement P_i et vérifier que les P_j restent inchangés. Cas obligatoires : `location=Rwanda` ne modifie pas `project_id`; UUID projet ne modifie pas location; `result_limit` ne modifie pas une pagination native sans règle ; `date_from` ne remplace pas `date_to`.

## Traçabilité / CI

Chaîne : `REQUIREMENT ↔ SOURCE ↔ ENDPOINT ↔ PARAMETER ↔ DESCRIPTOR ↔ REGISTRY ↔ UI ↔ BACKEND ↔ PYTHON ↔ R ↔ TEST ↔ DOCUMENTATION ↔ EVIDENCE ↔ STATUS`.

La CI bloque sur corruption de `project_id`, binding UI incorrect, perte inexpliquée de paramètre, mapping non vérifié, faux zéro, régression connecteur, incompatibilité Windows ou échec client qualifié.

## Rapports et verdict

Produire pour ReliefWeb, World Bank, HDX/CKAN et HDX HAPI : inventaire documentaire/API, matrice paramètres/mapping/couverture, résultats déterministes/live, anomalies, corrections, limites, dette, évaluation métier et verdict. Statuts de paramètres : `IMPLÉMENTÉ ET QUALIFIÉ`, `IMPLÉMENTÉ MAIS NON QUALIFIÉ`, `PARTIELLEMENT IMPLÉMENTÉ`, `SPÉCIFIÉ / PLANIFIÉ`, `EXPÉRIMENTAL`, `LEGACY / COMPATIBILITÉ`, `DÉPRÉCIÉ`, `BLOQUÉ`, `À VÉRIFIER`, `ABSENT`.

La qualification d'un paramètre n'implique pas celle de l'endpoint, du connecteur ou de HDP. Linux ne remplace pas Windows et déterministe ne remplace pas live.

## Critère final

Chaque paramètre exposé par HDP doit avoir une origine documentée, un type vérifié, une sémantique explicite, un binding UI correct, une traduction fournisseur vérifiée, une requête native inspectable, une provenance conservée, des tests reproductibles et un statut démontrable. Tout écart reste visible.