# Todo-list active — Humanitarian Data Platform V6.0.0

Dernière mise à jour : 30 août 2026  
Branche de qualification : `main`  
Version cible : **6.0.0**  
Statut : **candidat de qualification — ne pas déclarer qualifié avant fermeture de la matrice V6**.

La matrice normative est `docs/V6_FUNCTIONAL_VALIDATION_MATRIX.md`. Une case n'est terminée qu'après test reproductible, correction des anomalies, retest ciblé et non-régression.

## Lots V6 actifs

- [x] **HDP6-010 — Registre et inventaire des sources** : dix connecteurs, contrats versionnés, provenance documentaire et inventaire exhaustif.
- [x] **HDP6-020 — Paramétrage des sources** : critères communs et paramètres fournisseurs visibles ; seuls les champs effectivement câblés sont éditables.
- [ ] **HDP6-030 — Recherche/acquisition E2E** : fermer les preuves UI → API HDP → fournisseur → ressource → provenance.
- [ ] **HDP6-040 — Projets et bibliothèque** : terminer la recette CRUD, isolation, upload, récupération et association des ressources.
- [ ] **HDP6-070 — Traitements scientifiques** : qualifier clients Python/R, scripts, notebooks et recettes de traitement.
- [ ] **HDP6-080 — Épidémiologie et surveillance** : séries temporelles, taux/incidence, jobs périodiques, règles, signaux et alertes.
- [ ] **HDP6-090 — Intégrations** : GitHub, mail/RSS et SPIP avec scénarios nominaux et négatifs reproductibles.
- [ ] **HDP6-100 — Sécurité et exploitation** : passkey, SQL read-only, logs, provenance, intégrité, sauvegarde/restauration et timeline.
- [ ] **HDP6-110 — Windows** : build PE x64, exécution installateur, raccourci, lancement et scénario de mise à niveau sans perte.
- [ ] **HDP6-120 — Documentation et livrables** : USER/API/UML/reconstruction, archive complète et empreintes.
- [ ] **HDP6-130 — Gate final V6** : Linux + PostgreSQL + Windows + E2E métier verts sur le même HEAD et matrice V6 sans `A_TESTER`, `PARTIEL` ou `BLOQUE`.

## Règle de correction

Pour toute anomalie : enregistrer le test en échec, classer sa gravité, corriger le produit ou le test lorsqu'il est objectivement obsolète, réexécuter le test ciblé, puis toute la non-régression concernée. Aucun contournement par suppression de test ou assertion artificielle n'est admis.

## Historique

Les todo-lists des versions antérieures restent archivées sous `docs/traceability/`. La qualification 5.0.2 demeure un jalon historique ; elle ne doit plus servir de description de l'état fonctionnel de la V6.
