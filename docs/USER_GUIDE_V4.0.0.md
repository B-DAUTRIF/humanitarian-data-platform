# Guide utilisateur - Humanitarian Data Platform 4.0.0

## À quoi sert HDP ?

Humanitarian Data Platform (HDP) est une application locale pour rechercher,
télécharger, organiser, vérifier, traiter et cartographier des données de santé
publique et d’action humanitaire. Les éléments sont séparés par projet et
conservés avec leur provenance et leur empreinte SHA-256.

HDP est une application mono-utilisateur liée à `127.0.0.1`. Ne publiez pas son
port sur un réseau et ne l’exposez pas directement à Internet.

## Parcours recommandé

1. Ouvrez le titre **Humanitarian Data Platform** pour revenir à l’accueil.
2. Créez ou sélectionnez un projet.
3. Dans **Recherche**, cochez au moins deux sources, saisissez des mots-clés et,
   si nécessaire, une période et une localisation.
4. Dépliez les champs propres à chaque source. L’interface indique leur contrat
   et l’API conserve les paramètres effectifs.
5. Lancez la recherche. Une erreur d’une source ne supprime pas les résultats
   déjà obtenus sur les autres.
6. Téléchargez les ressources compatibles ou importez vos propres fichiers dans
   **Données locales**.
7. Vérifiez l’empreinte d’un fichier et configurez sa mise à jour depuis sa
   fiche. Pour un import local sans URL distante, HDP crée une échéance de
   remplacement manuel.
8. Dans **Scripts**, choisissez un CSV/TSV et une recette guidée. Adaptez les
   noms de colonnes, puis créez un jeu dérivé. HDP conserve l’original, le
   rapport, la recette, la lignée et un script Python ou R.
9. Dans **Carte**, importez les GeoJSON vérifiés, affichez plusieurs couches et
   exportez un paquet GeoJSON/QGIS/R. Le fond OpenStreetMap n’est activé qu’à
   votre demande.
10. Dans **Base SQL**, interrogez uniquement les vues `hdp_*` du projet avec
    une requête de lecture bornée.

## Sources actives

Les dix connecteurs actifs sont HDX/CKAN, ReliefWeb, WHO GHO, World Bank Health,
UNICEF SDMX, UN SDG, DHS, HDX HAPI, UNHCR Refugee Statistics et GDACS. HAPI
requiert `HDX_HAPI_APP_IDENTIFIER`; ReliefWeb requiert un
`RELIEFWEB_APPNAME` pré-approuvé. Ces valeurs restent dans `.env` et ne sont
jamais renvoyées par l’API.

IOM DTM, WHO Disease Outbreak News, WHO Mortality, GLASS, FluNet, GHE, UNAIDS,
IHME GHDx, MICS, WorldPop et d’autres catalogues sont présentés comme portails
de référence lorsque HDP ne dispose pas d’un contrat public stable et testé.

## Import depuis l’ordinateur

HDP sépare les catégories suivantes :

- données : CSV, TSV, JSON/JSONL, GeoJSON, XLSX, Parquet/GeoParquet,
  Arrow/Feather, GeoPackage et ZIP contrôlé ;
- scripts : Python, R, SQL et carnet Jupyter en stockage ;
- documents : texte/Markdown, PDF, DOCX/ODT/PPTX et images autorisées.

Le serveur reçoit les fichiers en flux, limite leur taille, nettoie le nom,
écrit d’abord un fichier `.part`, vérifie la signature ou la structure, refuse
les macros, exécutables, liens et chemins dangereux dans les archives, puis
publie atomiquement le fichier. Un script importé n’est jamais exécuté
automatiquement.

## Traitements guidés

Le moteur 4.0.0 accepte CSV et TSV. Il sait sélectionner ou renommer des
colonnes, filtrer, remplir des valeurs manquantes, recoder, typer, calculer un
taux, dédupliquer et agréger. Les opérations simples sont effectuées en flux ;
les clés de déduplication et groupes d’agrégation ont des limites explicites.

Les modèles incidence, létalité et couverture n’inventent aucun dénominateur :
vous devez désigner les colonnes et vérifier les unités, périodes et populations.
Une division par zéro produit une valeur vide. Les analyses d’enquête pondérée,
la standardisation sur l’âge et les intervalles de confiance nécessitent un
script métier documenté et les variables méthodologiques appropriées.

## Carte

L’aperçu intégré accepte GeoJSON `Feature` ou `FeatureCollection` en SRID 4326,
jusqu’à 20 Mio, 5 000 entités et 64 Kio de propriétés par entité. GeoPackage,
GeoParquet et ZIP sont conservés et téléchargeables, mais doivent être convertis
explicitement en GeoJSON pour Leaflet. Supprimer une couche PostGIS ne supprime
jamais son fichier source.

## Base SQL

Le navigateur ne reçoit aucune chaîne de connexion. L’API impose une transaction
`READ ONLY`, un délai de cinq secondes, une limite de lignes et les vues
`hdp_acquisitions`, `hdp_resources`, `hdp_schedules`, `hdp_artifacts`,
`hdp_federated_searches` et `hdp_processing_runs`. DDL, DML, commandes de
session, requêtes multiples, fichiers et fonctions dangereuses sont refusés.

## Sauvegarde et restauration

Exécutez `backup-hdp.ps1` depuis le dossier installé. La sauvegarde contient la
base, `data/` et `.env` : elle contient donc des secrets et doit rester hors du
dépôt. La restauration exige la valeur explicite `RESTORE-HDP`, crée d’abord une
sauvegarde de sécurité et conserve les anciens `.env` et `data/` sous un nom
daté. Voir `BACKUP_RESTORE_V4.0.0.md`.

## Limites importantes

- aucune authentification multi-utilisateur ni exposition réseau ;
- aucun contournement des comptes, licences ou quotas des sources ;
- l’accès au catalogue ne garantit pas que chaque source propose toutes ses
  observations avec les mêmes dimensions ;
- l’EXE Windows 4.0.0 doit être recompilé et qualifié sur Windows x64 avant de
  pouvoir être déclaré signé et validé ;
- HDP aide à travailler avec des données, mais ne valide pas une décision
  clinique, épidémiologique ou opérationnelle.

