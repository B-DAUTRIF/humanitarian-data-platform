# Cahier des charges final - Humanitarian Data Platform 3.0.0

## 1. Objet

Humanitarian Data Platform, ou HDP, est une application Windows locale destinée
à acquérir, organiser, vérifier, planifier, cartographier et traiter des données
humanitaires, épidémiologiques et sanitaires mondiales. L'installation est
effectuée par un exécutable graphique natif ; l'utilisation quotidienne se fait
dans le navigateur.

## 2. Périmètre garanti

- utilisateur unique sur un poste Windows 10/11 x64 ;
- interface et services liés à `127.0.0.1` ;
- Docker Desktop et WSL 2 comme socle d'exécution ;
- FastAPI/Python pour l'API principale ;
- PostgreSQL 16/PostGIS 3.4 pour les métadonnées et géométries ;
- R/plumber facultatif ;
- scripts Python et R uniquement, exécutés hors ligne ;
- compatibilité de mise à niveau ciblée depuis HDP 2.5.0.

Sont exclus : exposition Internet ou LAN, multi-utilisateur, authentification
centralisée, TLS public, exécution shell/SQL, traitement de code hostile,
stockage de secrets dans la base ou publication GitHub automatique de données.

## 3. Sources

### Connecteurs interrogeables et planifiables

1. HDX/CKAN ;
2. ReliefWeb API v2 ;
3. WHO Global Health Observatory ;
4. World Bank Health Indicators ;
5. UNICEF Data Warehouse/SDMX ;
6. UN Global SDG Indicators ;
7. DHS Program Indicator Data.

Chaque connecteur expose un contrat de paramètres versionné. HDP distingue les
réglages globaux des réglages propres à chaque projet. Les réponses distantes
brutes sont archivées avant normalisation, avec empreinte SHA-256.

### Références sanitaires

Le catalogue intégré distingue les API actives des portails sans API publique
stable ou dont l'accès varie selon les données : WHO Mortality, GLASS,
FluNet/FluID, Global Health Estimates, UNAIDS, IHME/GHDx, MICS, World Population
Prospects, Global.health, WorldPop et Our World in Data.

### Flux RSS

Le registre RSS est borné aux quatre flux officiels ReliefWeb : mises à jour,
catastrophes, emplois et formations. Les réponses sont limitées à 2 Mio,
analysées avec `defusedxml`, sans DTD/entité, et dédupliquées en base.

## 4. Fonctions attendues

### Projets

- créer, modifier et archiver logiquement un projet ;
- isoler préférences, acquisitions, ressources, scripts et planifications ;
- conserver un « Projet par défaut » stable pour la migration.

### Acquisitions et ressources

- rechercher les sept connecteurs ;
- prévisualiser les requêtes sans appel réseau et sans secret ;
- archiver le JSON brut et sa provenance ;
- télécharger facultativement les ressources ;
- appliquer taille, quantité et formats autorisés ;
- refuser URL privées/locales, identifiants intégrés et redirections non sûres ;
- écrire par fichier temporaire puis renommage atomique ;
- vérifier et exposer l'empreinte SHA-256 ;
- supprimer un fichier avec confirmation tout en conservant sa trace.

### Géodonnées

- proposer COD-AB et COD-PS officiels ;
- afficher COD-CS comme indisponible tant que le registre vérifié est vide ;
- signaler COD-HP comme retiré ;
- limiter la zone à l'intersection ONU M49 et groupes HDX canoniques ;
- effectuer une synchronisation atomique des familles sélectionnées ;
- importer un GeoJSON borné dans PostGIS SRID 4326 ;
- afficher les couches avec Leaflet 1.9.4 embarqué ;
- ne charger les tuiles OpenStreetMap qu'après action explicite ;
- exporter GeoJSON et scripts QGIS/R.

### Scripts

- créer une version immuable à chaque modification ;
- autoriser uniquement Python et R ;
- utiliser un runner par langage, sans shell et sans réseau ;
- limiter durée, sortie, processus, fichiers, mémoire et CPU ;
- conserver statut, sortie, erreurs, horodatages et rapport JSON SHA-256 ;
- considérer tous les scripts comme code local de confiance.

### Planification et chronologie

- planifier acquisitions, synchronisations géographiques et RSS ;
- intervalle minimal de 15 minutes ;
- revendiquer les travaux avec verrou transactionnel ;
- conserver l'historique ;
- afficher acquisitions, passages, scripts et échéances dans un Gantt.

### GitHub

- stocker le jeton uniquement dans `.env` ;
- créer un dépôt après confirmation explicite, privé par défaut ;
- recommander un jeton finement granulé à droits minimaux ;
- fournir une passerelle REST locale pour dépôt, branches, commits, issues,
  pull requests, releases, workflows, contenus et quotas ;
- désactiver par défaut la création d'issues et le dispatch de workflows.

## 5. Architecture Docker

| Service | Rôle | Exposition |
|---|---|---|
| `db` | PostgreSQL/PostGIS | interne |
| `api` | FastAPI, interface, planificateur | `127.0.0.1:8080` ou port choisi |
| `runner-python` | exécution Python hors ligne | aucune, `network_mode: none` |
| `github-api` | passerelle REST GitHub | `127.0.0.1:8091` |
| `r-service` | résumés R/plumber facultatifs | interne, profil `analytics` |
| `runner-r` | exécution R hors ligne | aucune, profil `analytics` |

Le nom Compose et le volume PostgreSQL historique doivent rester stables.

## 6. Installation et mise à niveau

L'installateur Win32 doit :

- rester graphique et réactif pendant les tâches longues ;
- détecter winget, Docker, Git et VS Code ;
- proposer les tiers sans sélection automatique ;
- choisir 8080 ou un port libre entre 18080 et 18279 ;
- préserver `.env`, ses variables inconnues, `data/` et le volume PostgreSQL ;
- créer `.env.backup-before-v3.0.0` avant réécriture ;
- construire les services requis et ouvrir le navigateur après santé positive ;
- créer les raccourcis Windows prévus ;
- ne jamais lancer de purge Docker ou `down -v`.

## 7. Sécurité et conformité

- aucun secret dans les réponses, journaux, archives ou dépôt ;
- validation des entrées et bornes explicites ;
- requêtes distantes limitées aux hôtes/URL prévus ;
- conteneurs d'exécution non privilégiés, capacités supprimées et lecture seule ;
- tuiles OSM opt-in avec attribution ;
- données humanitaires sensibles exclues sans évaluation dédiée ;
- dépôt privé tant qu'aucune licence HDP explicite n'est adoptée.

## 8. Critères d'acceptation

- suite Python intégralement réussie ;
- compilation de tous les modules Python ;
- JavaScript analysable ;
- YAML Compose valide ;
- contrats OpenAPI générables ;
- runner C compilé en C17 strict et testé sur succès/dépassement de délai ;
- payload reconstruit octet pour octet ;
- installateur PE32+ GUI x64 avec ASLR/NX ;
- archives ZIP intègres et sommes SHA-256 vérifiées ;
- aucune opération destructive ou secret versionné ;
- commit final descendant de `main`, publication non forcée et vérification du
  commit distant.

La recette finale Windows/Docker doit être consignée séparément lorsqu'elle ne
peut pas être exécutée dans l'environnement de construction.
