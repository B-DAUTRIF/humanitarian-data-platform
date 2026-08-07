# Prompt autonome de reconstruction — Humanitarian Data Platform 2.3.2

Copiez intégralement le bloc ci-dessous dans une nouvelle instance GPT disposant d’un environnement de développement et, si possible, d’un accès autorisé à GitHub.

---

## PROMPT À COPIER

Tu reprends la maintenance et la livraison de **Humanitarian Data Platform (HDP) 2.3.2**, application locale Windows 10/11 x64. Ton objectif est de retrouver fidèlement l’état fonctionnel, documentaire et distribuable décrit ci-dessous, puis de poursuivre le projet sans régression et sans inventer de validation.

### 1. Source d’autorité et état GitHub

Le dépôt privé de référence est :

`B-DAUTRIF/humanitarian-data-platform`

URL : <https://github.com/B-DAUTRIF/humanitarian-data-platform>

Branche de référence : `main`.

Le commit de livraison est le commit de `main` qui contient ce document et le
message `fix: repair official COD-AB discovery and stale scope status v2.3.2`. Si `main` a
évolué, considère le commit courant et ses documents comme prioritaires ; ne
reviens jamais automatiquement à un SHA historique.

Commence obligatoirement par :

1. vérifier que tu consultes le bon dépôt et la bonne branche ;
2. lire `README.md`, puis tous les fichiers de `docs/` ;
3. lire `dist/v2.3.2/MANIFESTE_HumanitarianDataPlatform_v2.3.2.txt` et `dist/v2.3.2/SHA256SUMS.txt` ;
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
- un profil géographique fondé sur ONU M49 et limité aux COD‑AB officiels OCHA/HDX ;
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

Une exécution v1.5 a été validée sur Windows 11 avec Docker Desktop, WSL 2 et le port 18080. Cette recette historique ne doit pas être présentée comme une recette automatique de la v2.3.2.

#### Version 2.0

La v2.0 a ajouté :

- les projets ;
- les préférences de téléchargement par projet ;
- la gestion des ressources locales ;
- les scripts stockés par projet, sans aucune exécution ;
- les planifications persistantes ReliefWeb ou HDX ;
- la migration des acquisitions anciennes vers le « Projet par défaut ».

#### Version 2.3.0

La v2.3.0 a ajouté :

- la configuration et la création confirmée d’un dépôt GitHub par projet ;
- le téléchargement manuel ou automatique d’un jeu géographique HDX ;
- les formats GeoJSON, GeoPackage, Shapefile et File Geodatabase ;
- la persistance de l’état, de la prochaine échéance et de la dernière acquisition géographique.

#### Version 2.3.1

La v2.3.1 a remplacé le modèle géographique 2.3.0 :

- nomenclature hiérarchique ONU M49 embarquée : monde, régions, sous-régions,
  régions intermédiaires, pays et zones ;
- suppression de la saisie libre d’un identifiant HDX dans le profil géographique ;
- série officielle unique `COD - Subnational Administrative Boundaries` ;
- niveaux admissibles `cod-enhanced` et `cod-standard` ;
- politiques `enhanced_only` et `enhanced_preferred` ;
- provenance M49, ISO3, niveau COD, éditeur, licence et date HDX ;
- report explicite `deferred` au-delà du quota d’un passage ;
- migration sûre et sans déduction arbitraire d’une ancienne portée locale.

#### Version 2.3.2

La v2.3.2 corrige deux régressions observées en exploitation :

- `package_search` cherche les identifiants canoniques `cod-ab-*` portant un
  niveau `cod-enhanced` ou `cod-standard` ;
- l'admissibilité exige ensuite le nom exact `cod-ab-<iso3>` et un unique groupe
  ISO3 présent dans ONU M49 ;
- cette identité canonique est acceptée lorsque CKAN indexe la série officielle
  mais n'expose pas `dataseries_name` dans le JSON retourné ;
- un jeu dont le nom n'est pas canonique reste refusé en l'absence de la série ;
- tout changement de périmètre M49, politique COD ou format efface l'ancien
  statut, l'ancienne erreur et l'ancienne acquisition, puis passe à
  `sync_required` ;
- si l'automatisation est active, le profil modifié devient immédiatement
  éligible ;
- les cas Soudan (`729`, `SDN`, `cod-ab-sdn`) et Algérie (`012`, `DZA`,
  `cod-ab-dza`) ont été vérifiés contre le catalogue HDX réel.

### 4. Architecture technique exacte

#### Installateur

- langage : C ;
- interface : Win32 native ;
- cible : `x86_64-windows-gnu` ;
- sous-système : Windows GUI ;
- compilation : Zig ;
- version : `2.3.2` ;
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
- diagnostic produit : `Bureau\HDP_Debug_v2.3.2_*.log`.

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
- profil géographique officiel avec `package_search`, identité canonique et validation locale ;
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

### 10. Profil géographique ONU M49 et COD‑AB officiel

Table `project_geodata_settings` :

- `project_id` ;
- `auto_download` ;
- `preferred_format` ;
- `m49_scope_code` ;
- `official_policy` ;
- `migration_required` ;
- `refresh_interval_minutes` ;
- `next_sync_at` ;
- `last_sync_at` ;
- `last_status` ;
- `last_error` ;
- `last_acquisition_id` ;
- `updated_at`.

Valeurs par défaut :

- `auto_download=false` ;
- `preferred_format=geojson` ;
- `m49_scope_code=001` ;
- `official_policy=enhanced_preferred` ;
- `migration_required=false` ;
- `refresh_interval_minutes=10080`.

Routes :

- `GET /api/un-m49/entities` ;
- `GET /api/projects/{project_id}/geodata` ;
- `PUT /api/projects/{project_id}/geodata` ;
- `POST /api/projects/{project_id}/geodata/sync`.

Flux de synchronisation :

1. valider que `m49_scope_code` appartient à l’instantané embarqué ;
2. appeler `package_search` avec
   `name:cod-ab-* AND cod_level:(cod-enhanced OR cod-standard)` ;
3. exiger localement un niveau COD admissible, un unique groupe ISO3 présent
   dans M49 et soit la série exacte, soit le nom canonique exact
   `cod-ab-<iso3>` ;
4. développer un groupement M49 vers ses pays ou zones descendants ;
5. préférer `cod-enhanced`, ou exiger ce niveau selon la politique ;
6. archiver la réponse CKAN, la source M49, la décision, les jeux retenus, les
   entités sans jeu et les formats manquants ;
7. sélectionner le format d’après le champ, le nom et l’extension ;
8. associer M49, ISO3, niveau COD, éditeur, licence et date à la ressource locale ;
9. réutiliser le pipeline commun de téléchargement sécurisé ;
10. produire `completed`, `partial`, `failed`, `no_official_dataset` ou
    `no_matching_resource`, puis persister l’état ;
11. en automatique, avancer la prochaine échéance avant l’appel distant.

Lors d'un `PUT` qui change le périmètre, la politique ou le format, remettre
`last_sync_at`, `last_error` et `last_acquisition_id` à `null`, fixer
`last_status=sync_required` et avancer `next_sync_at` à maintenant si
`auto_download=true`. Un changement de territoire ne doit jamais conserver le
message d'un ancien pays.

Formats reconnus :

- `geojson` ;
- `geopackage` ;
- `shapefile` ;
- `geodatabase`.

Respecter les licences et restrictions indiquées sur chaque fiche HDX.

### 11. Nomenclature ONU M49

Le fichier `source/payload/api/app/un_m49_snapshot.json` est un instantané daté
du 7 août 2026 de la norme statistique M49 de la Division de statistique des
Nations Unies. Il contient 278 entités, dont 248 pays ou zones dotés d’un ISO3.

Types : `0` monde, `1` région, `2` sous-région, `3` région intermédiaire,
`4` pays ou zone. Les affectations à des groupements sont statistiques et
n’impliquent aucune position politique. Le fichier `THIRD_PARTY_NOTICES.md`
documente la source et l’intermédiaire `un-m49` 2.2.0 sous licence MIT.

Ne remplace pas M49 par une géométrie, ne déduis pas un territoire depuis
l’ancienne échelle 2.3.0 et n’admets pas un jeu seulement parce que son titre
contient le mot « boundaries ».

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
- les ressources déjà complètes ne consomment pas ce nombre maximal ;
- les ressources au-delà de la limite sont comptées `deferred`, pas `failed` ;
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
3. géodonnées officielles ONU M49 / HDX.

L’interface doit :

- afficher la version 2.3.2 ;
- rester utilisable sur écran étroit ;
- demander confirmation avant la création GitHub ;
- demander confirmation avant une suppression locale ;
- expliquer que le jeton n’est pas stocké dans le projet ;
- afficher une sélection hiérarchique M49 et la politique COD officielle ;
- expliquer la portée statistique des groupements M49 ;
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
- ajouter les colonnes M49/COD de façon idempotente ;
- convertir seulement `max_scale=world` en M49 `001` ;
- marquer toute autre ancienne portée `migration_required`, désactiver son
  automatisation et exiger un choix M49 explicite.

Préserver impérativement :

- `.env` ;
- `data/` ;
- le volume PostgreSQL ;
- les réponses brutes ;
- les ressources ;
- les livrables historiques `dist/v1.5`, `dist/v2.0` et `dist/v2.3`.

Ne jamais utiliser `docker compose down -v`, Docker Clean/Purge ou Reset to factory defaults comme dépannage initial.

### 18. Routes principales

Vérifier au minimum :

```text
GET /api/health
GET /api/sources
GET /api/un-m49/entities
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
dist/v2.3.2/
source/
  build.sh
  HDP_Diagnostic_v2.3.2.cmd
  HDP_Configurer_GitHub_v2.3.2.cmd
  HumanitarianDataPlatform_Setup_README_v2.3.2.txt
  payload/
    CHANGELOG_HDP.log
    THIRD_PARTY_NOTICES.md
    compose.yaml
    api/
      app/main.py
      app/project_integrations.py
      app/un_m49_snapshot.json
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
tools/generate_notice_v232.py
```

### 20. Livrables v2.3.2 et empreintes

Dossier : `dist/v2.3.2`.

Fichiers principaux :

- `HumanitarianDataPlatform_Setup_Native_GUI_v2.3.2.exe` ;
- `HumanitarianDataPlatform_Setup_Native_GUI_v2.3.2.exe.sha256` ;
- `HumanitarianDataPlatform_Windows_v2.3.2.zip` ;
- `HumanitarianDataPlatform_Source_v2.3.2.zip` ;
- `HumanitarianDataPlatform_Archive_complete_v2.3.2.zip` ;
- `HumanitarianDataPlatform_Archive_complete_v2.3.2.zip.sha256` ;
- `HumanitarianDataPlatform_Setup_README_v2.3.2.txt` ;
- `CHANGELOG_HDP_v2.3.2.log` ;
- `HDP_Configurer_GitHub_v2.3.2.cmd` ;
- `HDP_Diagnostic_v2.3.2.cmd` ;
- `Notice_detaillee_Humanitarian_Data_Platform_v2.3.2.pdf` ;
- `HDP_Prompt_exhaustif_reprise_GPT_Plus_v2.3.2.txt` ;
- `MANIFESTE_HumanitarianDataPlatform_v2.3.2.txt` ;
- `SHA256SUMS.txt`.

Empreintes de référence :

```text
EXE
57d4c308273ccf378342743d3b1ca0394bde98ce27cee3b0f1319b8edf2ee954

ZIP Windows
d2971b95dbc94e00ace1246c268358c145a160420d3615de6149b9b11f25d52c

ZIP sources
c2ec2d903eb22936642ae0fb0619da16176da79f12737d84a539b188f939e682

Archive complète
Voir HumanitarianDataPlatform_Archive_complete_v2.3.2.zip.sha256 : son empreinte
ne peut pas être auto-incluse dans le prompt que contient cette même archive.

Notice PDF
a613e7b9cb3e54333affc62a0a413477c68042dac04c664d4df4711a6b21c44a
```

La notice PDF compte 22 pages A4.

Ne modifie pas silencieusement ces artefacts signés. Si le code change, incrémente la version ou reconstruis explicitement tous les fichiers concernés, puis recalcule les empreintes et actualise le manifeste.

### 21. Validations réellement effectuées pour la v2.3.2

Les validations disponibles sont :

- compilation syntaxique des modules Python ;
- 24 tests unitaires réussis ;
- validation syntaxique JavaScript avec Node.js ;
- analyse de `compose.yaml` avec PyYAML ;
- génération du payload ;
- reconstruction de 18 fichiers du payload et comparaison à l’identique ;
- compilation de l’installateur ;
- contrôle PE32+ GUI x86‑64, 7 sections ;
- contrôle `unzip -t` des trois ZIP ;
- contrôle `sha256sum -c` ;
- contrôle des livrables historiques v2.3.1, v2.3.0 et v2.0 ;
- interrogation directe du catalogue HDX : 166 candidats, Soudan et Algérie
  retenus avec leur ressource GeoJSON ;
- PDF de 22 pages rendu en PNG et inspecté visuellement ;
- arbre GitHub distant relu après publication.

Le moteur Docker était absent de l’environnement Linux de construction. Par conséquent, ne prétends pas que les éléments suivants ont été validés pour la v2.3.2 :

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
3. exécuter les 24 tests ;
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
- Le module géographique n’accepte aucune saisie libre de jeu HDX : M49 et le marquage COD officiel sont obligatoires.
- Si une permission, une connexion ou une décision utilisateur manque, arrête l’action externe et demande confirmation.

### 24. Sources officielles à consulter

- GitHub REST API — repositories : <https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28>
- ONU M49 : <https://unstats.un.org/unsd/methodology/m49/overview/>
- OCHA COD‑AB : <https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/2557378679/Administrative%2BBoundaries%2BCOD-AB>
- CKAN Action API : <https://docs.ckan.org/en/latest/api/>
- ReliefWeb API V2 : <https://apidoc.reliefweb.int/>

Utilise les documentations officielles si une API, une permission, un format ou une règle a pu évoluer. Une appartenance M49 n’est pas une prise de position politique et un marquage COD officiel ne dispense pas de vérifier la licence et l’adéquation du jeu.

### 25. Définition de « terminé »

Une reprise est terminée seulement si :

- le dépôt et sa version ont été identifiés ;
- le code réel a été inspecté ;
- les contraintes de sécurité sont conservées ;
- les données et secrets existants sont préservés ;
- les fonctions GitHub et le module M49/COD-AB officiel sont présents avec leurs confirmations et garde-fous ;
- l’installateur, le payload, la documentation et les artefacts sont cohérents ;
- les validations réellement disponibles sont exécutées ;
- les validations indisponibles sont explicitement signalées ;
- les empreintes correspondent aux fichiers ;
- la publication GitHub est relue à distance ;
- un rapport factuel fournit les liens, le commit, les tests et les limites.

Commence maintenant par inspecter le dépôt et produire un court état des lieux vérifiable avant toute modification.

## FIN DU PROMPT

---

Ce prompt décrit l’état de livraison v2.3.2 ; les archives historiques 2.3.1 et antérieures restent inchangées.
