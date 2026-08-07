# Prompt autonome de reconstruction — Humanitarian Data Platform 2.3

Copiez intégralement le bloc ci-dessous dans une nouvelle instance GPT disposant d’un environnement de développement et, si possible, d’un accès autorisé à GitHub.

---

## PROMPT À COPIER

Tu reprends la maintenance et la livraison de **Humanitarian Data Platform (HDP) 2.3.0**, application locale Windows 10/11 x64. Ton objectif est de retrouver fidèlement l’état fonctionnel, documentaire et distribuable décrit ci-dessous, puis de poursuivre le projet sans régression et sans inventer de validation.

### 1. Source d’autorité et état GitHub

Le dépôt privé de référence est :

`B-DAUTRIF/humanitarian-data-platform`

URL : <https://github.com/B-DAUTRIF/humanitarian-data-platform>

Branche de référence : `main`.

Le commit de livraison du code et des artefacts v2.3 est :

`c4f74f8dcf3370aa03221882e61794ce057049e8`

Message : `feat: deliver project GitHub and HDX geodata v2.3`.

Commence obligatoirement par :

1. vérifier que tu consultes le bon dépôt et la bonne branche ;
2. lire `README.md`, puis tous les fichiers de `docs/` ;
3. lire `dist/v2.3/MANIFESTE_HumanitarianDataPlatform_v2.3.txt` et `dist/v2.3/SHA256SUMS.txt` ;
4. inspecter `git status`, le dernier commit et l’arbre réel ;
5. considérer le code du dépôt comme prioritaire sur ce prompt si une évolution ultérieure documentée existe ;
6. ne jamais écraser silencieusement des changements déjà présents.

Si le dépôt privé n’est pas accessible, demande à l’utilisateur de connecter GitHub ou d’effectuer la connexion manuellement dans le navigateur de ChatGPT. Ne demande jamais de mot de passe, de jeton ou de secret dans la conversation.

### 2. Résultat produit attendu

HDP doit fournir :

- un installateur graphique Windows natif x64 au format `.exe` ;
- l’analyse de l’environnement Windows et la proposition explicite d’installation de logiciels tiers ;
- Docker Desktop requis, Git et Visual Studio Code facultatifs ;
- un module R/plumber facultatif, séparé du cœur Python ;
- une interface web locale ouverte dans le navigateur après installation ;
- une API FastAPI utilisant PostgreSQL/PostGIS ;
- l’acquisition de métadonnées publiques ReliefWeb et HDX/CKAN ;
- l’archivage traçable des réponses brutes avec UUID, date UTC et SHA‑256 ;
- le téléchargement contrôlé des ressources référencées ;
- une organisation complète par projets ;
- des paramètres GitHub propres à chaque projet ;
- un profil géographique HDX COD‑AB propre à chaque projet ;
- les sources, l’EXE, trois ZIP, la documentation GitHub, une notice PDF, un diagnostic, un manifeste, un prompt de reprise et toutes les empreintes.

### 3. Historique fonctionnel à préserver

#### Version 1.5

La v1.5 a stabilisé :

- l’installateur natif Win32 après abandon de HTA ;
- l’interface d’installation non bloquante ;
- les contrôles Docker/WSL bornés ;
- l’installation optionnelle de Git et Visual Studio Code ;
- le module R optionnel ;
- la sélection automatique du port Windows ;
- l’utilisation de `8080`, sinon du premier port libre entre `18080` et `18279` ;
- la persistance de ce port dans `.env` sous `HDP_PORT` ;
- la liaison exclusive à `127.0.0.1`.

Une exécution v1.5 a été validée sur Windows 11 avec Docker Desktop, WSL 2 et le port 18080. Cette recette historique ne doit pas être présentée comme une recette automatique de la v2.3.

#### Version 2.0

La v2.0 a ajouté :

- les projets ;
- les préférences de téléchargement par projet ;
- la gestion des ressources locales ;
- les scripts stockés par projet, sans aucune exécution ;
- les planifications persistantes ReliefWeb ou HDX ;
- la migration des acquisitions anciennes vers le « Projet par défaut ».

#### Version 2.3

La v2.3 ajoute :

- la configuration et la création confirmée d’un dépôt GitHub par projet ;
- le téléchargement manuel ou automatique d’un jeu géographique HDX ;
- le profil par défaut `cod-ab-global` ;
- les formats GeoJSON, GeoPackage, Shapefile et File Geodatabase ;
- une amplitude d’échelle maximale ordonnée de terrain à monde ;
- la persistance de l’état, de la prochaine échéance et de la dernière acquisition géographique.

### 4. Architecture technique exacte

#### Installateur

- langage : C ;
- interface : Win32 native ;
- cible : `x86_64-windows-gnu` ;
- sous-système : Windows GUI ;
- compilation : Zig ;
- version : `2.3.0` ;
- classe principale : `HDP_NATIVE_INSTALLER_23` ;
- manifeste Windows avec DPI et chemins longs ;
- payload embarqué dans `source/src/payload_generated.h` ;
- payload produit par `source/scripts/generate_payload.mjs` ;
- aucune console obligatoire pour l’utilisateur ;
- journal d’installation conservé sous `%LOCALAPPDATA%\HumanitarianDataPlatform\logs`.

#### Application

- Python 3.12 ;
- FastAPI et Uvicorn ;
- `httpx` pour les sources, GitHub et les téléchargements ;
- PostgreSQL 16 avec PostGIS 3.4 ;
- R/plumber facultatif via le profil Compose `analytics` ;
- interface autonome HTML/CSS/JavaScript servie par FastAPI ;
- Docker Compose pour l’orchestration.

#### Frontières réseau

- seul le service FastAPI est publié sur Windows ;
- la publication doit rester `127.0.0.1:${HDP_PORT}:8080` ;
- PostgreSQL et R restent dans le réseau Compose interne ;
- HDP est une application locale mono-utilisateur ;
- elle n’a ni authentification applicative, ni TLS local, ni séparation de rôles ;
- elle ne doit jamais être exposée directement à Internet ou au LAN.

### 5. Emplacements Windows

Conserver exactement ces emplacements par défaut :

- application : `%USERPROFILE%\HumanitarianDataPlatform` ;
- configuration : `%USERPROFILE%\HumanitarianDataPlatform\.env` ;
- métadonnées brutes : `%USERPROFILE%\HumanitarianDataPlatform\data\raw` ;
- ressources : `%USERPROFILE%\HumanitarianDataPlatform\data\projects` ;
- journaux installateur : `%LOCALAPPDATA%\HumanitarianDataPlatform\logs` ;
- diagnostic produit : `Bureau\HDP_Debug_v2.3_*.log`.

Les scripts Windows sont :

- `start-hdp.cmd` ;
- `start-hdp-with-r.cmd` ;
- `stop-hdp.cmd`.

L’arrêt normal ne doit jamais supprimer un volume ou les données.

### 6. Configuration et secrets

Le fichier `.env` contient ou peut contenir :

```dotenv
POSTGRES_PASSWORD=<secret aléatoire>
RELIEFWEB_APPNAME=<appname pré-approuvé facultatif>
GITHUB_TOKEN=<jeton facultatif>
HDP_PORT=<port local>
```

Règles impératives :

- générer un mot de passe PostgreSQL aléatoire lors d’une nouvelle installation ;
- préserver les valeurs existantes pendant une mise à niveau ;
- ne jamais afficher ou journaliser `POSTGRES_PASSWORD` ;
- ne jamais afficher ou journaliser `GITHUB_TOKEN` ;
- ne jamais renvoyer `GITHUB_TOKEN` dans une réponse API ;
- ne jamais stocker `GITHUB_TOKEN` dans une table de projet ;
- l’installeur utilise un champ masqué `ES_PASSWORD` pour GitHub ;
- un champ GitHub vide pendant la mise à niveau conserve la valeur existante ;
- le diagnostic ne copie depuis `.env` que `HDP_PORT` ;
- ne jamais publier `.env` dans GitHub ou dans une archive.

### 7. Modèle par projets

Le projet actif détermine toutes les listes et opérations affichées.

Tables principales :

- `projects` ;
- `project_preferences` ;
- `project_github_settings` ;
- `project_geodata_settings` ;
- `project_scripts` ;
- `schedules` ;
- `schedule_runs` ;
- `acquisitions` ;
- `local_resources`.

Le « Projet par défaut » utilise l’UUID stable :

`00000000-0000-4000-8000-000000000001`

Il reçoit les acquisitions historiques sans projet et ne peut pas être archivé.

L’archivage d’un autre projet :

- est logique ;
- désactive ses planifications ;
- désactive sa synchronisation géographique ;
- ne supprime ni ses fichiers, ni ses acquisitions, ni son historique.

### 8. Acquisition ReliefWeb et HDX

#### ReliefWeb

- action sur l’API V2 des rapports ;
- profil `full` ;
- nécessite `RELIEFWEB_APPNAME` pré-approuvé ;
- si absent, renvoyer une erreur 503 explicite sans empêcher l’usage de HDX.

#### HDX/CKAN

- recherche avec `package_search` ;
- profil géographique avec `package_show` ;
- contrôler `success` même si HTTP vaut 200 ;
- conserver la réponse complète ;
- sérialiser en UTF‑8 avec ordre déterministe ;
- produire UUID, horodatage UTC et SHA‑256.

### 9. Dépôt GitHub par projet

Table `project_github_settings` :

- `project_id` ;
- `owner` ;
- `repository_name` ;
- `description` ;
- `visibility` ;
- `repository_url` ;
- `repository_full_name` ;
- `created_at` ;
- `updated_at`.

Le secret GitHub reste global dans l’environnement.

Routes :

- `GET /api/projects/{project_id}/github` ;
- `PUT /api/projects/{project_id}/github` ;
- `POST /api/projects/{project_id}/github/repository`.

Flux de création :

1. l’interface enregistre les paramètres ;
2. elle demande une confirmation explicite contenant le nom et la visibilité ;
3. l’API refuse l’opération si `GITHUB_TOKEN` est absent ;
4. l’API appelle `GET https://api.github.com/user` ;
5. si `owner` est vide ou identique au login, utiliser `POST /user/repos` ;
6. sinon utiliser `POST /orgs/{owner}/repos` ;
7. envoyer le nom, la description, `private`, `auto_init=true` et `has_issues=true` ;
8. mémoriser l’URL et le nom complet retournés ;
9. bloquer une seconde création si une URL est déjà associée.

Règles :

- visibilité privée par défaut ;
- aucune suppression distante proposée ;
- aucun téléversement automatique des ressources, scripts ou données du projet ;
- un dépôt public ne doit être choisi qu’après validation de la licence et du contenu ;
- messages d’erreur GitHub bornés et sans jeton.

### 10. Profil géographique HDX COD‑AB

Table `project_geodata_settings` :

- `project_id` ;
- `auto_download` ;
- `dataset_id` ;
- `preferred_format` ;
- `max_scale` ;
- `refresh_interval_minutes` ;
- `next_sync_at` ;
- `last_sync_at` ;
- `last_status` ;
- `last_error` ;
- `last_acquisition_id` ;
- `updated_at`.

Valeurs par défaut :

- `auto_download=false` ;
- `dataset_id=cod-ab-global` ;
- `preferred_format=geojson` ;
- `max_scale=world` ;
- `refresh_interval_minutes=10080`.

Routes :

- `GET /api/geographic-scales` ;
- `GET /api/projects/{project_id}/geodata` ;
- `PUT /api/projects/{project_id}/geodata` ;
- `POST /api/projects/{project_id}/geodata/sync`.

Flux de synchronisation :

1. valider l’identifiant HDX ;
2. appeler `package_show` ;
3. archiver la réponse complète et un objet `hdp_geographic_profile` ;
4. enregistrer la source sous `hdx-geodata` ;
5. sélectionner le format d’après le champ format, le nom et l’extension ;
6. réutiliser le pipeline commun de téléchargement sécurisé ;
7. conserver l’acquisition même si aucun format ne correspond ;
8. produire alors `no_matching_resource` ;
9. persister le dernier statut, l’erreur et l’acquisition ;
10. en automatique, avancer la prochaine échéance avant l’appel distant.

Formats reconnus :

- `geojson` ;
- `geopackage` ;
- `shapefile` ;
- `geodatabase`.

Le jeu par défaut est le catalogue global COD‑AB :

<https://data.humdata.org/dataset/cod-ab-global>

Respecter les licences et restrictions indiquées sur chaque fiche HDX.

### 11. Amplitude d’échelle

Le catalogue ordonné est :

1. `terrain` — site, camp, quartier ou voisinage immédiat ;
2. `local` — commune, district ou niveau administratif détaillé ;
3. `national` — pays et principaux niveaux administratifs ;
4. `regional` — ensemble de pays ou région humanitaire ;
5. `world` — couverture mondiale maximale.

Règle essentielle : cette échelle est une **classification opérationnelle HDP**. Elle n’est pas une norme officielle HDX. Elle documente une portée maximale d’usage et ne doit jamais :

- découper automatiquement les géométries ;
- inventer une couverture absente ;
- généraliser ou simplifier les objets ;
- reprojeter les données ;
- étendre une ressource locale à une couverture mondiale.

### 12. Téléchargement sécurisé

Conserver l’ensemble des garde-fous :

- HTTP ou HTTPS seulement ;
- refus des identifiants incorporés dans l’URL ;
- résolution DNS avant téléchargement ;
- refus des IP privées, locales, réservées ou non globales ;
- revalidation à chaque redirection ;
- six redirections au maximum ;
- noms de fichiers neutralisés ;
- chemins confinés sous `data/` ;
- taille maximale contrôlée par `Content-Length` puis pendant le flux ;
- nombre maximal de ressources par acquisition ;
- formats autorisés par projet ;
- écriture temporaire `.part` ;
- calcul SHA‑256 progressif ;
- renommage final seulement après réussite ;
- états `queued`, `downloading`, `completed`, `failed`, `deleted` ;
- déduplication par clé de ressource et URL.

Ces protections réduisent le risque SSRF et l’épuisement du stockage, mais ne remplacent pas une isolation réseau, un antivirus ou une validation métier.

### 13. Données locales

La rubrique doit permettre :

- l’inventaire par projet ;
- le résumé du stockage ;
- le téléchargement vers le navigateur ;
- le recalcul SHA‑256 en flux ;
- la suppression locale après confirmation.

La suppression efface le fichier mais conserve la ligne et la provenance avec le statut `deleted`.

### 14. Scripts

Un script possède :

- nom ;
- langage `python`, `r`, `sql`, `shell` ou `other` ;
- description ;
- contenu ;
- projet ;
- dates ;
- archivage logique.

Il n’existe **aucune route d’exécution**. N’ajoute jamais une exécution de script sans conception explicite de l’isolation, des autorisations, des quotas, de la journalisation et du confinement.

### 15. Planificateur

Les planifications générales comprennent :

- source ReliefWeb ou HDX ;
- requête ;
- limite de résultats ;
- option de téléchargement ;
- intervalle ;
- activation ;
- exécution immédiate ;
- historique `schedule_runs`.

Contraintes :

- intervalle général de 15 minutes à 30 jours ;
- intervalle géographique de 60 minutes à 30 jours ;
- boucle toutes les 20 secondes ;
- transaction avec `FOR UPDATE SKIP LOCKED` ;
- prochaine échéance avancée avant l’appel ;
- erreur persistée sans arrêter définitivement la boucle ;
- architecture conçue pour un seul processus Uvicorn.

### 16. Interface web

Rubriques visibles :

- Recherche ;
- Projets & préférences ;
- Données locales ;
- Scripts ;
- Planifications.

Dans les paramètres du projet, afficher trois cartes :

1. préférences générales ;
2. dépôt GitHub ;
3. jeu géographique HDX.

L’interface doit :

- afficher la version 2.3 ;
- rester utilisable sur écran étroit ;
- demander confirmation avant la création GitHub ;
- demander confirmation avant une suppression locale ;
- expliquer que le jeton n’est pas stocké dans le projet ;
- expliquer que l’échelle HDP ne transforme pas les géométries ;
- afficher les derniers statuts et erreurs sans exposer de secret.

### 17. Migration

La migration au démarrage est idempotente :

- créer PostGIS si nécessaire ;
- créer les tables manquantes ;
- ajouter `project_id` et `schedule_id` aux acquisitions anciennes ;
- créer le Projet par défaut ;
- rattacher les acquisitions sans projet ;
- rendre `project_id` non nul ;
- créer `project_github_settings` ;
- créer `project_geodata_settings` ;
- ajouter une ligne de paramètres pour chaque projet existant ;
- laisser la synchronisation géographique automatique désactivée par défaut.

Préserver impérativement :

- `.env` ;
- `data/` ;
- le volume PostgreSQL ;
- les réponses brutes ;
- les ressources ;
- les livrables historiques `dist/v1.5` et `dist/v2.0`.

Ne jamais utiliser `docker compose down -v`, Docker Clean/Purge ou Reset to factory defaults comme dépannage initial.

### 18. Routes principales

Vérifier au minimum :

```text
GET /api/health
GET /api/sources
GET /api/geographic-scales
GET/POST /api/projects
PATCH/DELETE /api/projects/{id}
GET/PUT /api/projects/{id}/preferences
GET/PUT /api/projects/{id}/github
POST /api/projects/{id}/github/repository
GET/PUT /api/projects/{id}/geodata
POST /api/projects/{id}/geodata/sync
GET /api/search
GET /api/acquisitions
GET /api/resources
GET /api/resources/{id}/file
POST /api/resources/{id}/verify
DELETE /api/resources/{id}
GET/POST /api/projects/{id}/scripts
PATCH/DELETE /api/scripts/{id}
GET/POST /api/projects/{id}/schedules
PATCH/DELETE /api/schedules/{id}
POST /api/schedules/{id}/run
GET /api/schedules/{id}/runs
GET /docs
GET /openapi.json
```

### 19. Arborescence importante

```text
README.md
docs/
dist/v1.5/
dist/v2.0/
dist/v2.3/
source/
  build.sh
  HDP_Diagnostic_v2.3.cmd
  HumanitarianDataPlatform_Setup_README_v2.3.txt
  payload/
    compose.yaml
    api/
      app/main.py
      app/project_integrations.py
      app/scheduler_utils.py
      app/security.py
      static/index.html
    r-service/
  scripts/generate_payload.mjs
  src/installer.c
  src/installer.manifest
  src/installer.rc
  src/payload_generated.h
  tests/payload_roundtrip.c
  tests/test_v23_helpers.py
tools/generate_notice_v23.py
```

### 20. Livrables v2.3 et empreintes

Dossier : `dist/v2.3`.

Fichiers principaux :

- `HumanitarianDataPlatform_Setup_Native_GUI_v2.3.exe` ;
- `HumanitarianDataPlatform_Setup_Native_GUI_v2.3.exe.sha256` ;
- `HumanitarianDataPlatform_Windows_v2.3.zip` ;
- `HumanitarianDataPlatform_Source_v2.3.zip` ;
- `HumanitarianDataPlatform_Archive_complete_v2.3.zip` ;
- `HumanitarianDataPlatform_Archive_complete_v2.3.zip.sha256` ;
- `HumanitarianDataPlatform_Setup_README_v2.3.txt` ;
- `HDP_Diagnostic_v2.3.cmd` ;
- `Notice_detaillee_Humanitarian_Data_Platform_v2.3.pdf` ;
- `HDP_Prompt_exhaustif_reprise_GPT_Plus_v2.3.txt` ;
- `MANIFESTE_HumanitarianDataPlatform_v2.3.txt` ;
- `SHA256SUMS.txt`.

Empreintes de référence :

```text
EXE
cc44cb5d252cb069d58521bc127d743f38f01d27e2256c8c5946c5f8478c4523

ZIP Windows
1ca7723d6954b44fef275036ea21b25909c450b3f6e635713da2474de1b791a8

ZIP sources
8d4533312c21e3c110dc9a5a9a0af7bb71f58746123a8a92bee8e27ef6fc4e20

Archive complète
1f00bd8216ced092b13e536501a944376f3304b3a22914fbd52133b1702e1c2c

Notice PDF
e879efcd0dcf58783bc9a5236108e2a3d17c3914d3cb64f1e0420a6061d77c1e
```

La notice PDF compte 22 pages A4.

Ne modifie pas silencieusement ces artefacts signés. Si le code change, incrémente la version ou reconstruis explicitement tous les fichiers concernés, puis recalcule les empreintes et actualise le manifeste.

### 21. Validations réellement effectuées pour la v2.3

Les validations disponibles sont :

- compilation syntaxique des modules Python ;
- 14 tests unitaires réussis ;
- validation syntaxique JavaScript avec Node.js ;
- analyse de `compose.yaml` avec PyYAML ;
- génération du payload ;
- reconstruction de 15 fichiers du payload et comparaison à l’identique ;
- compilation de l’installateur ;
- contrôle PE32+ GUI x86‑64, 7 sections ;
- contrôle `unzip -t` des trois ZIP ;
- contrôle `sha256sum -c` ;
- contrôle des livrables historiques v2.0 ;
- PDF de 22 pages rendu en PNG et inspecté visuellement ;
- arbre GitHub distant relu après publication.

Le moteur Docker était absent de l’environnement Linux de construction. Par conséquent, ne prétends pas que les éléments suivants ont été validés pour la v2.3 :

- migration PostgreSQL/PostGIS en conteneur ;
- démarrage complet de Compose ;
- parcours navigateur Windows complet ;
- appel réel à GitHub depuis HDP ;
- synchronisation réelle HDX depuis HDP ;
- comportement SmartScreen ou installation sur une machine Windows de recette.

Ces vérifications restent à exécuter sur Windows avec Docker Desktop.

### 22. Procédure de vérification recommandée

Après toute modification :

1. exécuter `git status` et inspecter le diff ;
2. compiler tous les modules Python ;
3. exécuter les 14 tests ;
4. vérifier la syntaxe JavaScript ;
5. vérifier le YAML Compose ;
6. régénérer `payload_generated.h` si le payload change ;
7. refaire le roundtrip exact ;
8. reconstruire l’EXE Windows ;
9. contrôler le format PE ;
10. reconstruire les ZIP affectés ;
11. exécuter `unzip -t` ;
12. recalculer toutes les empreintes ;
13. mettre à jour le manifeste, la notice et la documentation ;
14. tester sous Windows/Docker lorsque cette validation est disponible ;
15. publier un commit intentionnel ;
16. relire les fichiers depuis GitHub après publication ;
17. produire un rapport distinguant compilation, tests unitaires, intégration Docker et recette Windows.

### 23. Règles de travail et d’exactitude

- N’invente aucune fonction, aucun résultat de test, aucune permission ou aucun succès distant.
- Toute affirmation de validation doit être accompagnée de la commande ou de l’artefact qui la démontre.
- Préserve les changements utilisateur non liés.
- Utilise des opérations Git non destructives.
- Ne supprime aucun volume, fichier de données ou secret sans demande explicite.
- Ne publie jamais de secret.
- Conserve le dépôt privé tant qu’aucune licence HDP explicite n’a été choisie.
- L’installateur n’est pas signé par certificat d’éditeur ; signale le risque SmartScreen.
- Respecte les quotas, licences et conditions d’utilisation de GitHub, HDX et ReliefWeb.
- Les scripts stockés restent non exécutables.
- La portée terrain → monde reste une métadonnée HDP, jamais une transformation géographique.
- Si une permission, une connexion ou une décision utilisateur manque, arrête l’action externe et demande confirmation.

### 24. Sources officielles à consulter

- GitHub REST API — repositories : <https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28>
- HDX COD‑AB Global : <https://data.humdata.org/dataset/cod-ab-global>
- CKAN Action API : <https://docs.ckan.org/en/latest/api/>
- ReliefWeb API V2 : <https://apidoc.reliefweb.int/>

Utilise les documentations officielles si une API, une permission, un format ou une règle a pu évoluer. Ne déduis pas une norme officielle HDX à partir de la classification interne de HDP.

### 25. Définition de « terminé »

Une reprise est terminée seulement si :

- le dépôt et sa version ont été identifiés ;
- le code réel a été inspecté ;
- les contraintes de sécurité sont conservées ;
- les données et secrets existants sont préservés ;
- les fonctions GitHub et HDX sont présentes avec leurs confirmations et garde-fous ;
- l’installateur, le payload, la documentation et les artefacts sont cohérents ;
- les validations réellement disponibles sont exécutées ;
- les validations indisponibles sont explicitement signalées ;
- les empreintes correspondent aux fichiers ;
- la publication GitHub est relue à distance ;
- un rapport factuel fournit les liens, le commit, les tests et les limites.

Commence maintenant par inspecter le dépôt et produire un court état des lieux vérifiable avant toute modification.

## FIN DU PROMPT

---

Ce prompt décrit l’état de livraison v2.3 sans modifier les archives déjà hachées dans `dist/v2.3`.
