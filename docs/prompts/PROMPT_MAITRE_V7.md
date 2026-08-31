# PROMPT MAÎTRE V7 — HDP

Statut : document normatif de reconstruction, développement, audit et qualification HDP V7.

## 1. Mission

Reconstruire, développer, auditer, tester et qualifier Humanitarian Data Platform V7 sans inventer l'état du dépôt ni la capacité d'un fournisseur. Toute conclusion doit être attachée à un commit Git exact et à des preuves reproductibles.

## 2. Ordre des sources de vérité

En cas de divergence : dépôt Git → code exécuté → migrations/schéma → tests → résultats → GitHub Actions → artefacts → configuration → documentation de version → rapports → spécifications → historique/conversations.

Ne jamais confondre branche, RC, release, `main` et version qualifiée.

## 3. Statuts obligatoires

Utiliser : `IMPLÉMENTÉ ET QUALIFIÉ`, `IMPLÉMENTÉ MAIS NON QUALIFIÉ`, `PARTIELLEMENT IMPLÉMENTÉ`, `SPÉCIFIÉ / PLANIFIÉ`, `EXPÉRIMENTAL`, `LEGACY / COMPATIBILITÉ`, `DÉPRÉCIÉ`, `BLOQUÉ`, `À VÉRIFIER`, `ABSENT`.

Tests : PASS / FAIL / BLOCKED / NOT TESTED. Un test non exécuté n'est jamais PASS.

## 4. Pipeline sémantique canonique

`USER INTENT → HDP CANONICAL CONCEPT → NOMENCLATURE → PROVIDER CAPABILITY → VERIFIED TRANSLATION → PROVIDER VALUE → NATIVE PARAMETER → NATIVE REQUEST → RESPONSE → NORMALIZATION → PROVENANCE → UI/EXPORT/CLIENTS`.

Aucune conversion géographique ou fournisseur n'est devinée. Rwanda, RWA, RW, 646 et tout identifiant fournisseur sont des représentations distinctes jusqu'à preuve de mapping.

## 5. Invariant P0 anti-faux-zéro

Une recherche bornée, échantillonnée, partielle, post-filtrée, à mapping incertain ou victime d'une erreur fournisseur ne peut jamais être interprétée comme preuve universelle d'absence. HTTP 4xx/5xx, timeout, authentication failure et schema drift ne sont jamais `empty_valid`.

## 6. Architecture cible

HDP V7 est un monolithe modulaire : FastAPI/Python pour acquisition et sémantique, PostgreSQL/PostGIS pour métadonnées/provenance, stockage fichiers pour raw/export, R comme couche analytique optionnelle, SPIP comme couche éditoriale/publication uniquement. Les services fournisseurs dédiés constituent les implémentations de référence ; le routeur sémantique délègue au service spécialisé lorsqu'il existe.

## 7. Interface

Modes Simple / Avancé / Expert. Chaque capacité fournisseur qualifiée reste accessible en Expert. Les composants UI sont typés : booléen→case, enum→liste, multi-enum→multi-sélection, nombre→champ numérique, date/période→contrôle temporel, géographie→nomenclature/carte/liste, texte→champ, structure complexe→éditeur spécialisé validé.

Le mode Expert doit exposer Query Plan, traduction canonique/native, requête native, complétude, provenance, erreurs, empreintes et scripts Python/R reproductibles.

## 8. Développement des connecteurs

Le document `docs/prompts/dev_connecteurs.md` est obligatoire pour toute création/refonte de connecteur.

**Le document `docs/prompts/audit_parametres_connecteurs_v7.md` est un gate obligatoire et indissociable de ce prompt maître.** Tout nouveau connecteur et toute modification d'un connecteur existant doivent être audités paramètre-par-paramètre selon ce protocole avant qualification.

En particulier :

- l'inventaire documentaire/API doit précéder l'implémentation ;
- chaque paramètre doit disposer d'un statut et d'une preuve ;
- `DOCUMENTATION ↔ DESCRIPTOR ↔ REGISTRY ↔ BACKEND ↔ UI ↔ PYTHON ↔ R ↔ TESTS ↔ DOC` doit être comparé ;
- les tests de non-contamination entre paramètres sont obligatoires ;
- 10 cycles déterministes sont requis pour les fonctionnalités critiques ;
- les tests live sont séparés et leurs blocages restent visibles ;
- HDX/CKAN, HDX HAPI et COD sont des contrats distincts ;
- la qualification d'un paramètre n'implique jamais automatiquement celle de tout le connecteur.

## 9. Matrice API minimale

`SOURCE → API → ENDPOINT → OPÉRATION → PARAMÈTRE → TYPE → CARDINALITÉ → VALEURS → OBLIGATOIRE → ENTRÉE/SORTIE → CONCEPT HDP → TRANSFORMATION → COMPOSANT UI → TEST → PREUVE → STATUT`.

## 10. Clients Python/R

Toute capacité utilisateur qualifiée doit être vérifiée dans l'API HDP, l'UI, le client Python et le client R ou explicitement déclarée hors couverture. Les exemples/vignettes doivent être reproductibles et ne jamais contenir de secret.

## 11. Qualification globale

Format obligatoire : `TEST → PRÉCONDITION → ACTION → ATTENDU → OBSERVÉ → PREUVE → STATUT`.

Tracer : `REQUIREMENT ↔ MODULE ↔ FILE ↔ CLASS/FUNCTION ↔ API ↔ TABLE ↔ TEST ↔ DOC ↔ STATUS`.

La qualification inclut selon le périmètre : compilation, tests Python, tests PostgreSQL/PostGIS, sécurité, migrations, routeur sémantique, connecteurs, UI, clients R/Python, provenance, jobs, automations, installation Windows et validation de l'artefact PE32+ x64 + SHA-256.

## 12. Windows

Un installateur est un véritable `.exe` Windows, jamais une archive renommée. La CI Windows doit vérifier au minimum signature MZ/PE, architecture x64, métadonnées de version et SHA-256. Une réussite Linux ne qualifie pas le build Windows.

## 13. GitHub et promotion

`main` doit représenter la dernière livraison installable qualifiée uniquement lorsque les critères de promotion sont réellement satisfaits. Une branche de test, une RC et une qualification pour test utilisateur restent distinctes d'une release stable.

Ne jamais promouvoir parce qu'un sous-connecteur est vert si les gates applicatifs requis ne le sont pas.

## 14. Verdict final

Employer exactement l'un des verdicts :

- `QUALIFIÉ POUR RELEASE`
- `QUALIFIÉ POUR TEST UTILISATEUR`
- `QUALIFICATION PARTIELLE`
- `NON QUALIFIÉ`

Le verdict doit découler des preuves observées, pas d'une intention.

## 15. Livrables permanents

Conserver dans le dépôt : code, migrations, tests, workflows, matrices JSON/CSV/Markdown, rapports par connecteur, logs de qualification, documentation technique/utilisateur, clients/vignettes, prompts normatifs, manifestes d'artefacts et empreintes cryptographiques.

Ce prompt maître ne peut être considéré complet sans l'application du protocole `audit_parametres_connecteurs_v7.md` aux connecteurs concernés.