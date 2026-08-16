# Plan de finalisation HDP 4.0.0

Dernière mise à jour : 2026-08-15 14:23 CEST  
Branche de travail distante : `codex/finalize-hdp-v4`  
Socle fonctionnel : HDP 3.0.0, commit GitHub `6eff2065fadc8070be398ecce7560c6d2db44084`

## Objectif de sortie

Produire une version 4.0.0 installable, documentée et vérifiée de Humanitarian
Data Platform, avec recherche multisource, import et gestion des fichiers locaux,
cartographie, planification par fichier, accès SQL borné et traitements
reproductibles Python/R. Les archives historiques restent immuables.

## Règle de reprise entre sessions

Chaque lot doit se terminer par :

1. des tests automatisés et une compilation statique réussis ;
2. une mise à jour de `HDP_v4.0.0_Point_de_reprise.md` ;
3. une mise à jour de la TODO et du journal de travail ;
4. un commit local explicite ;
5. un point de reprise publié sur `codex/finalize-hdp-v4`.

La version n'est dite finale qu'après génération des manifestes et empreintes,
reconstruction des archives depuis une arborescence propre et qualification des
limites qui ne peuvent pas être levées dans l'environnement de construction.

## Lots de réalisation

| Lot | TODO principale | Résultat attendu | État |
|---|---|---|---|
| 0 — Audit et reprise | HDP-044 | Base testée, branche, journal et plan de reprise | Terminé |
| 1 — Contrats de données | HDP-037, 041, 043 | Capacités versionnées, lignée brut/normalisé/dérivé, formats massifs | Terminé pour le périmètre CSV/TSV ; Parquet/GeoParquet reste au backlog |
| 2 — Recherche | HDP-028, 029, 036, 038 | Champs propres aux sources et recherche parallèle avec résultats unifiés | Terminé pour le parcours v4 ; annulation/progression temps réel à étendre |
| 3 — Bibliothèque locale | HDP-030, 031, 033, 034 | Import de données/scripts/documents, carte et planification depuis chaque fichier | Terminé pour GeoJSON et planification par intervalle |
| 4 — SQL et traitements | HDP-035, 042 | Espace SQL en lecture seule et recettes Python/R reproductibles | Terminé pour le périmètre CSV/TSV borné |
| 5 — Connecteurs | HDP-039, 040 | HAPI, UNHCR, IOM DTM, GDACS et sources sanitaires prioritaires | Partiel — HAPI, UNHCR et GDACS actifs ; IOM/WHO DON référencés |
| 6 — Interface finale | HDP-032, 036 | Accueil lié au titre, parcours cohérent recherche → donnée → traitement | Terminé pour le parcours principal |
| 7 — Qualification | HDP-044 | Tests, sécurité, sauvegarde/restauration, documentation, prompt global | Terminé localement ; recette Windows/Docker externe |
| 8 — Livraison | HDP-044 | EXE/archives, manifestes, SHA-256, dépôt et rapport final | En cours — archive portable, sans EXE 4.0.0 |

## Checkpoint fonctionnel 1 — 15 août 2026

- recherche fédérée concurrente sur au moins deux connecteurs, avec opération
  parente, acquisitions indépendantes et statut complet/partiel/échoué ;
- critères communs dates/localisation filtrés sur le modèle normalisé et contrat
  de capacité indiquant le mode d'application ;
- champs propres aux sources rendus directement dans le panneau Recherche ;
- import multipart borné de données, scripts et documents, SHA-256 en flux et
  ajout automatique des scripts UTF-8 à leur bibliothèque ;
- périodicité visible et planification par ressource, automatique pour une
  origine API et sous forme d'échéance de remplacement pour un import local ;
- fichiers géographiques locaux visibles dans Carte, avec import GeoJSON ;
- page d'accueil descriptive ouverte par le titre du site ;
- espace SQL PostgreSQL/PostGIS en lecture seule sur cinq vues limitées au
  projet, requêtes bornées et journal d'audit par empreinte ;
- migrations idempotentes `4.0.0-001` à `4.0.0-003` ;
- 82 tests Python réussis, compilation Python et analyse JavaScript réussies.

## Checkpoint fonctionnel 2 — 15 août 2026

- portefeuille porté à dix connecteurs actifs avec trois contrats supplémentaires ;
- HDX HAPI v2 en statut expérimental avec identifiant d’application injecté
  uniquement côté serveur et paramètres propres au sous-domaine ;
- UNHCR Refugee Statistics normalisé en séries annuelles agrégées par origine
  et asile, avec extraction JSON reproductible ;
- GDACS normalisé depuis sa FeatureCollection et proposé comme ressource
  GeoJSON cartographiable ;
- IOM DTM 3.0 et WHO Disease Outbreak News conservés comme portails de
  référence tant qu’un contrat API public stable et vérifiable n’est pas
  configuré, sans scraping implicite ;
- 85 tests Python réussis et compilation complète des modules réussie.

## Checkpoint fonctionnel 3 — 15 août 2026

- moteur de recettes JSON 4.0.0 strict pour CSV/TSV : sélection, renommage,
  filtre, valeurs manquantes, recodage, typage, taux, déduplication bornée et
  agrégation bornée ;
- lecture/écriture en flux, rapport de profil de colonnes, limites explicites,
  écriture atomique et SHA-256 du résultat ;
- création d’une ressource dérivée immuable, d’un artefact `derived`, d’une
  arête de lignée et d’un script Python ou R versionné ;
- parcours « Traitement guidé » dans Scripts avec modèles santé publique et
  historique des traitements ;
- import utilisateur renforcé par fichier `.part`, validation des signatures,
  contrôle des archives, rejet des macros/exécutables et absence d’extraction ;
- carte multi-couches avec contrôle SHA-256 avant import et suppression de la
  couche PostGIS sans suppression du fichier source ;
- 90 tests Python, compilation Python et analyse JavaScript réussis.

## Checkpoint de gel 4 — 15 août 2026

- version applicative, registre, interface, installateur source et documentation
  alignés sur 4.0.0 ;
- workflow CI reproductible, analyse JavaScript et contrôles de sécurité
  statiques ajoutés ;
- SBOM CycloneDX 1.5 et notices tierces synchronisés ;
- scripts PowerShell et procédure de sauvegarde/restauration ajoutés ;
- prompt global de production, guide utilisateur, référence API, matrice des
  sources, revue de sécurité, limites connues et rapport de validation livrés ;
- notice PDF A4 de 27 pages rendue et inspectée ;
- 90 tests Python réussis, runner C17 compilé strictement, payload embarqué
  reconstruit et Compose validé comme YAML à 6 services ;
- absence assumée d'EXE 4.0.0 : l'archive portable Windows constitue le
  livrable exécutable par Docker Desktop dans ce gel.

## Critères transversaux

- aucune régression des 68 tests de la version 3.0.0 ;
- validation serveur de tous les paramètres et refus des champs inconnus ;
- accès réseau limité aux hôtes déclarés par chaque connecteur ;
- provenance complète et empreintes SHA-256 des ressources ;
- import borné en taille, nom de fichier assaini et détection de format ;
- SQL limité aux requêtes de lecture et au périmètre du projet ;
- exécutions Python/R sans privilège, bornées et reproductibles ;
- migration PostgreSQL idempotente et non destructive ;
- interface utilisable au clavier, erreurs explicites et actions longues suivies ;
- documentation utilisateur, administrateur, API et sécurité synchronisée avec le code.

## Limites externes à qualifier honnêtement

Les actions suivantes nécessitent des moyens externes et ne doivent jamais être
présentées comme accomplies sans preuve : recette sur Windows 10/11 réel avec
Docker Desktop, signature Authenticode par un certificat détenu par l'éditeur,
choix de la licence du projet et audit de sécurité indépendant.
