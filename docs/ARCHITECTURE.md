# Architecture, données et API

## Vue d'ensemble

```mermaid
flowchart TD
    U["Interface web locale"] --> A["FastAPI 2.4.0"]
    A --> P["PostgreSQL + PostGIS"]
    A --> F["JSON et ressources locales"]
    A --> X["ReliefWeb et HDX/CKAN"]
    A --> S["Planificateur persistant"]
    A --> G["API GitHub"]
    A -. facultatif .-> R["R / plumber"]
```

Docker Compose orchestre l'API, PostgreSQL/PostGIS et le service R facultatif. Seul le port HTTP de l'API est publié sur `127.0.0.1`. PostgreSQL et R restent dans le réseau interne Compose.

## Modèle par projets

| Entité | Rôle | Suppression |
|---|---|---|
| `projects` | Conteneur fonctionnel | Archivage logique ; le projet par défaut est protégé |
| `project_preferences` | Limites et téléchargement automatique par défaut | Suit le projet |
| `project_github_settings` | Propriétaire, dépôt, description, visibilité et URL créée ; aucun jeton | Suit le projet |
| `project_geodata_settings` | Familles COD, pays/zone M49, politique, format et cycle | Automatisation désactivée à l'archivage |
| `acquisitions` | Provenance de chaque réponse distante | Conservée |
| `local_resources` | URL, empreinte et provenance famille/M49/ISO3/COD/licence | Fichier supprimé, ligne marquée `deleted` |
| `project_scripts` | Contenu de scripts par projet | Archivage logique ; aucune exécution |
| `schedules` | Définition périodique d'une acquisition | Désactivation et archivage logique |
| `schedule_runs` | Historique des passages | Conservé avec statut et erreur éventuelle |

Le projet par défaut utilise l'UUID stable `00000000-0000-4000-8000-000000000001`. Le démarrage crée les nouvelles tables de façon idempotente, ajoute `project_id` et `schedule_id` à l'historique v1.5, puis rattache les lignes sans projet.

## Intégrations de projet 2.4.0

La création GitHub utilise `POST /user/repos` lorsque le propriétaire est vide ou correspond au compte du jeton, sinon `POST /orgs/{org}/repos`. Le dépôt est privé par défaut et initialisé avec un README. `GITHUB_TOKEN` demeure une variable d'environnement globale ; il ne transite jamais dans les modèles de réponse.

Le profil appelle `package_search` pour les catalogues canoniques `cod-ab-*` et
`cod-ps-*`. Chaque jeu doit correspondre à la série officielle ou à
l'identifiant exact `<famille>-<iso3>`, avec un unique groupe ISO3 connu de ONU
M49. COD-AB exige `cod-enhanced` ou `cod-standard`; COD-PS accepte l'absence de
ce champ, qui n'est pas publié uniformément pour cette série.

`GET /api/cod/availability` calcule l'intersection des ISO3 valides pour les
familles sélectionnées, la convertit en pays ou zones M49 et met les catalogues
en cache pendant 30 minutes. Au 7 août 2026, la même règle retourne 163 pays ou
zones COD-AB, 146 COD-PS et 143 dans leur intersection. COD-CS utilise un
registre versionné, actuellement vide et donc non sélectionnable. COD-HP est
explicitement retiré et ne peut pas être ajouté au profil.

Lorsqu'une famille, un pays, une politique COD ou un format change, le dernier résultat
est invalidé (`sync_required`) avant toute nouvelle synchronisation. L'interface
ne peut ainsi pas associer l'erreur d'un ancien pays au nouveau périmètre.

Les réponses CKAN complètes, le pays M49, les familles, les jeux retenus, les
absences et les formats manquants sont archivés sous `hdx-geodata`. Si une
famille sélectionnée manque, aucun sous-ensemble n'est téléchargé. Une ressource
déjà complète ne consomme pas le quota ; les suivantes obtiennent le compte
`deferred` et sont reprises lors d'un passage ultérieur.

## Flux d'acquisition et de téléchargement

1. L'API valide le projet, la source, la requête et la limite.
2. Elle appelle ReliefWeb V2 ou l'Action API CKAN de HDX.
3. La réponse brute est sérialisée en UTF-8, archivée et hachée en SHA-256.
4. Une ligne `acquisitions` conserve la provenance.
5. Si le téléchargement est actif, l'API extrait les ressources référencées.
6. Elle applique les préférences : nombre maximal, taille maximale et formats autorisés.
7. Chaque URL et chaque redirection doivent viser une adresse IP publique.
8. Le fichier est écrit sous forme `.part`, contrôlé pendant le flux, puis renommé atomiquement.
9. Le chemin relatif, la taille, le type de contenu et l'empreinte SHA-256 sont enregistrés.

```text
data/raw/<project_uuid>/<source>/<horodatage>_<requete>_<acquisition_uuid>.json
data/projects/<project_uuid>/resources/<acquisition_uuid>/<resource_uuid>_<nom>
```

## Planificateur

Le planificateur est une tâche de fond de l'unique processus Uvicorn. Il interroge PostgreSQL toutes les 20 secondes. Une planification ou synchronisation géographique due est revendiquée dans une transaction avec `FOR UPDATE SKIP LOCKED`; son prochain passage est avancé avant l'appel distant. Le résultat et l'erreur éventuelle sont persistés.

L'intervalle est compris entre 15 minutes et 30 jours. Une erreur de base temporaire ne termine pas définitivement la boucle. L'architecture suppose un seul processus API ; déployer plusieurs workers nécessiterait un service de tâches dédié.

## API locale principale

| Méthode et route | Fonction |
|---|---|
| `GET /api/health` | Santé SQL, version et état du planificateur |
| `GET/POST /api/projects` | Liste et création des projets |
| `PATCH/DELETE /api/projects/{id}` | Modification ou archivage logique |
| `GET/PUT /api/projects/{id}/preferences` | Préférences de téléchargement |
| `GET/PUT /api/projects/{id}/github` | Paramètres GitHub sans secret |
| `POST /api/projects/{id}/github/repository` | Création confirmée du dépôt |
| `GET/PUT /api/projects/{id}/geodata` | Profil géographique et état de synchronisation |
| `POST /api/projects/{id}/geodata/sync` | Synchronisation HDX immédiate |
| `GET /api/cod/families` | Liste, état sélectionnable/retiré et registre COD-CS |
| `GET /api/cod/availability` | Intersection pays/zone ONU M49 × familles HDX |
| `GET /api/un-m49/entities` | Nomenclature hiérarchique M49 et source d'autorité |
| `GET /api/search` | Acquisition manuelle et téléchargement optionnel |
| `GET /api/acquisitions?project_id=...` | Historique du projet |
| `GET /api/resources?project_id=...` | Inventaire local |
| `GET /api/resources/{id}/file` | Téléchargement depuis le stockage local |
| `POST /api/resources/{id}/verify` | Recalcul SHA-256 en flux |
| `DELETE /api/resources/{id}` | Suppression locale avec trace conservée |
| `GET/POST /api/projects/{id}/scripts` | Bibliothèque de scripts |
| `PATCH/DELETE /api/scripts/{id}` | Modification ou archivage d'un script |
| `GET/POST /api/projects/{id}/schedules` | Liste et création des planifications |
| `PATCH/DELETE /api/schedules/{id}` | Modification ou archivage |
| `POST /api/schedules/{id}/run` | Exécution manuelle immédiate |
| `GET /api/schedules/{id}/runs` | Historique d'exécution |
| `GET /docs` | Swagger UI générée par FastAPI |

`GET /api/search` et `POST /api/schedules/{id}/run` ont des effets : ils créent une acquisition et peuvent télécharger des fichiers.

## Service R

Le profil `analytics` fournit toujours R/plumber avec `/health` et `/summary`. Il reste facultatif et séparé du planificateur Python.

## Références des sources distantes

- [CKAN Action API](https://docs.ckan.org/en/latest/api/) : actions `package_search`, réponses `success/result` et métadonnées de ressources ;
- [ONU M49](https://unstats.un.org/unsd/methodology/m49/overview/) : nomenclature statistique du monde, des régions, pays et zones ;
- [OCHA COD-AB](https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/2557378679/Administrative%2BBoundaries%2BCOD-AB) : limites administratives communes ;
- [OCHA Common Operational Datasets](https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/42045911/Common%2BOperational%2BDatasets%2BCODs) : familles COD actuelles et retrait de COD-HP ;
- [OCHA COD-CS](https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/2965897217/Country-specific%2BCODs%2BCOD-CS) : nature contextuelle des données spécifiques au pays ;
- [GitHub REST — repositories](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28) : création pour un utilisateur ou une organisation ;
- [ReliefWeb API V2](https://apidoc.reliefweb.int/) et [paramètres](https://apidoc.reliefweb.int/parameters) : appname, profils, requêtes, limites et quotas.
