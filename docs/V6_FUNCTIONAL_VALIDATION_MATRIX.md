# HDP V6 — Matrice de validation fonctionnelle

Version cible : **6.0.0**  
Règle de release : une fonctionnalité n'est `VALIDEE` que si son implémentation, son exposition utilisateur et son test applicable sont démontrés. Une présence de code seule ne vaut pas validation.

Plateformes Windows officiellement supportées et bloquantes : **Windows 10 x64 build 19044+** et **Windows 11 x64 build 22000+**. Windows Server 2025 reste un environnement CI complémentaire et ne peut pas remplacer une recette exécutée sur un véritable poste/runner Windows 10 ou Windows 11.

Statuts : `A_TESTER`, `PARTIEL`, `VALIDE`, `BLOQUE`.

| ID | Domaine | Fonctionnalité V6 arrêtée | Preuve attendue | Test de référence | Statut initial |
|---|---|---|---|---|---|
| V6-001 | Sources/API | Registre central des sources | 10 connecteurs V6, version, docs, capacités | `test_source_registry.py` | PARTIEL |
| V6-002 | Sources/API | Inventaire exhaustif opérations/paramètres | inventaire généré + comptages + source/operation/parameter | audit inventaire V6 | PARTIEL |
| V6-003 | UI Sources | Contrôles natifs adaptés aux types | enum/select, bool/checkbox, nombre, texte, readonly | audit UI + E2E navigateur | PARTIEL |
| V6-004 | Sources/API | Paramètres UI réellement câblés aux requêtes | valeur UI -> requête HDP -> requête externe | E2E source parameter wiring | A_TESTER |
| V6-005 | Recherche | Recherche fédérée multisource | requête commune, fusion, tri, provenance | `test_federated_search.py` | PARTIEL |
| V6-006 | Recherche | Filtres mots-clés/date/lieu/fichier | critères validés et appliqués | `test_epidemiologist_use_case.py` | PARTIEL |
| V6-007 | Géographie | COD AB/HP/CS + M49 | sélection territoire, ressource officielle, métadonnées | test COD/M49 | A_TESTER |
| V6-008 | Carte | Visualisation géographique | GeoJSON chargé et rendu dans CARTE | E2E navigateur | A_TESTER |
| V6-009 | Données | Téléchargement réel | réponse distante -> fichier local exploitable | E2E réseau contrôlé | A_TESTER |
| V6-010 | Données | Bibliothèque/import local | upload, métadonnées, récupération | test API + E2E UI | A_TESTER |
| V6-011 | Données | Provenance/intégrité | source, URL, date, hash/trace | tests provenance/intégrité | PARTIEL |
| V6-012 | Projets | CRUD projets | création, lecture, modification, suppression | test API + UI | A_TESTER |
| V6-013 | Projets | Ressources/préférences/scripts/jobs par projet | isolation entre projets | test isolation projet | A_TESTER |
| V6-014 | GitHub | Association/synchronisation par projet/utilisateur | configuration, synchro, erreurs explicites | test contractuel GitHub | PARTIEL |
| V6-015 | Python | Client Python complet | recherche/téléchargement/projet + erreurs | tests client Python | PARTIEL |
| V6-016 | R | Client R complet | recherche/téléchargement/projet + erreurs | test R | A_TESTER |
| V6-017 | Scripts | Éditeur de scripts intégré | créer/éditer/exécuter/associer | E2E UI | A_TESTER |
| V6-018 | Notebooks | Exemples/notebooks scientifiques | notebook ouvrable et reproductible | smoke test notebook | A_TESTER |
| V6-019 | Traitement | Recettes R/Python | dataset -> transformation -> sortie | `test_processing_recipes.py` + E2E | PARTIEL |
| V6-020 | Épidémiologie | Série temporelle | dates harmonisées + agrégation | test métier | A_TESTER |
| V6-021 | Épidémiologie | Taux/incidence avec dénominateur | numérateur/dénominateur/unité/période | test métier | A_TESTER |
| V6-022 | Surveillance | Actualisation périodique | job planifié -> nouvelle acquisition | test scheduler/data-job | A_TESTER |
| V6-023 | Surveillance | Règle/signal/alerte | donnée -> seuil -> signal -> action | test règles/actions | A_TESTER |
| V6-024 | Timeline | Historique des opérations | événements ordonnés et attribués | test timeline | A_TESTER |
| V6-025 | Backup | Sauvegarde/restauration | backup puis restauration équivalente | test round-trip | A_TESTER |
| V6-026 | Sécurité | Auth/passkey | contrôle d'accès et scénarios négatifs | tests sécurité/auth | PARTIEL |
| V6-027 | SQL | Accès SQL contrôlé/read-only | lecture autorisée, écriture refusée | test SQL sécurité | A_TESTER |
| V6-028 | Mail | Mail features/ingestion | ingestion -> événement/ressource | test mail | A_TESTER |
| V6-029 | SPIP | Bridge/plugin SPIP | échange contractuel et erreur maîtrisée | test SPIP | A_TESTER |
| V6-030 | Logs | Logs app/install/LOG-Huma | horodatage, diagnostic, absence de secrets | test logs | A_TESTER |
| V6-031 | Windows | Installateur EXE x64 V6 | build PE/version/composants | workflow Windows V6 | PARTIEL |
| V6-032 | Windows | Installation réelle + raccourci | exécution installateur, fichiers, .lnk, lancement | test Windows installé | A_TESTER |
| V6-033 | Architecture | FastAPI/PostGIS/Docker Compose/R | services configurables et démarrables | CI Compose + services | PARTIEL |
| V6-034 | API HDP | OpenAPI/routes V6 | routes documentées et cohérentes | audit backend/OpenAPI | PARTIEL |
| V6-035 | UI | Navigation complète Simple/Avancé/Expert | vues accessibles sans erreur | E2E navigateur | A_TESTER |
| V6-036 | Documentation | USER + API + code + UML + reconstruction | livrables présents/versionnés | audit documentation | A_TESTER |
| V6-037 | Livrables | archive complète + clients + docs + tests | archive reproductible et contrôlée | workflow release | PARTIEL |
| V6-038 | Compatibilité | migration/compatibilité versions précédentes | scénario upgrade sans perte | test migration | A_TESTER |
| V6-039 | E2E métier | Cas épidémiologiste complet | signal -> API -> dataset -> analyse -> carte -> job -> alerte | recette E2E épidémiologique | PARTIEL |
| V6-040 | Release | Toutes les portes fonctionnelles vertes sur le même HEAD | CI Linux + Windows + E2E + matrice sans A_TESTER/BLOQUE | gate release V6 | BLOQUE |
| V6-041 | Compatibilité OS | Windows 10 x64 build 19044+ | compilation ciblée Win10 + installation/upgrade/lancement/désinstallation sur vrai Windows 10 x64 | `windows10_compatibility_gate.ps1` + `windows10_full_e2e.ps1` | BLOQUE |
| V6-042 | Compatibilité OS | Windows 11 x64 build 22000+ | même installateur Win10+ + installation/upgrade/lancement/désinstallation sur vrai Windows 11 x64 | `windows11_full_e2e.ps1` | BLOQUE |

## Boucle obligatoire

Pour chaque ligne :
1. exécuter le test ;
2. enregistrer la preuve ;
3. si échec, classer BLOCKER/MAJOR/MEDIUM/MINOR ;
4. corriger le produit ou le test si le test est fautif ;
5. réexécuter le test concerné ;
6. exécuter les tests de non-régression ;
7. ne passer à `VALIDE` qu'après preuve reproductible ;
8. après toute modification, requalifier le HEAD final.

## Critère de sortie V6

La V6 est qualifiée seulement lorsque **V6-001 à V6-042 sont `VALIDE`**, que la CI générale, la qualification Windows Server complémentaire, la recette réelle Windows 10 x64 et la recette réelle Windows 11 x64 sont vertes sur le **même commit**, et que le parcours épidémiologique E2E est réussi sans anomalie BLOCKER ou MAJOR ouverte.
