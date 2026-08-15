# Humanitarian Data Platform 4.0.0

Application locale pour rechercher, télécharger, importer, organiser, planifier,
traiter et cartographier des données humanitaires et de santé publique.

## Fonctionnalités 4.0.0

- **Recherche fédérée** : une requête sur plusieurs des dix connecteurs actifs,
  critères communs, champs propres à chaque API et résultats partiels traçables.
- **Bibliothèque locale** : import atomique de données, scripts et documents,
  contrôle du contenu et SHA-256, périodicité et planification par fichier.
- **Traitements reproductibles** : recettes CSV/TSV guidées, profilage en flux,
  résultat dérivé, lignée et génération de scripts Python/R.
- **Carte multi-couches et SQL** : GeoJSON vérifié dans PostGIS/Leaflet et vues
  du projet consultables en lecture seule sans exposer la connexion.

- **Exécution Python/R bornée** : versions immuables, rapports SHA-256, délai et
  sortie limités, runners sans privilège et sans réseau ; R reste facultatif.
- **Veille RSS officielle** : registre borné aux quatre flux ReliefWeb vérifiés,
  abonnements par projet, lecture immédiate ou planifiée, déduplication et
  parsing XML durci.
- **Chronologie Gantt** : acquisitions, planifications et exécutions de scripts
  sont réunies dans une vue temporelle du projet.
- **Cartographie locale** : import GeoJSON dans PostGIS, rendu Leaflet local et
  exports prêts pour QGIS et R. Les tuiles OpenStreetMap ne sont chargées
  qu'après action explicite.
- **GitHub à droits minimaux** : politique de jeton affichée sans exposer le
  secret et recommandation d'un jeton finement granulé avec permission
  d'administration du dépôt uniquement lorsque la création est utilisée.
- **Passerelle REST GitHub locale** : lecture des dépôts, branches, commits,
  issues, pull requests, releases, workflows, contenus et quotas ; création
  d'issues et déclenchement de workflows verrouillés par défaut.

Leaflet 1.9.4 est embarqué : ouvrir l'interface ne provoque aucun chargement de
code depuis un CDN.

## Validation historique du socle 3.0.0

- 68 tests Python réussis ;
- API principale : 47 chemins et 63 opérations OpenAPI ;
- passerelle GitHub : 11 chemins et 12 opérations OpenAPI ;
- JavaScript inline et Compose/YAML analysés avec succès ;
- runner C17 compilé strictement et essayé sur une exécution isolée ;
- 39 fichiers du payload reconstruits octet pour octet ;
- installateur PE32+ GUI x64 avec ASLR, NX et haute entropie.

La recette Windows 10/11 avec Docker Desktop reste à exécuter sur une machine
Windows réelle ; elle n'est pas confondue avec les validations locales ci-dessus.

## Paramétrage des sources et bibliothèque

- **Paramètres API versionnés** : contrats distincts pour les 10 connecteurs,
  validés côté serveur et rendus dynamiquement dans l'interface.
- **Deux niveaux de configuration** : activation/délai/reprises globalement,
  paramètres, limites et planification par projet et par source.
- **Prévisualisation sûre** : URL et commande assainies affichées avant appel ;
  aucun secret n'est retourné.
- **Provenance enrichie** : paramètres effectifs archivés avec les acquisitions
  et planifications ; bibliothèque filtrable par source, format, sujet,
  organisme, localisation et dates.
- **Mise à niveau** : migrations idempotentes enregistrées et conservation des
  variables inconnues de `.env`, des fichiers et du volume PostgreSQL.
- **Windows** : le code de l’installateur cible 4.0.0 et préserve `.env`, mais
  aucun EXE 4.0.0 n’est revendiqué dans ce gel Linux. Le portable Compose est le
  livrable Windows 4.0.0 jusqu’à recompilation et recette sur Windows x64.

## Socle conservé de la version 2.5.0

- **Sources sanitaires mondiales** : catalogue intégré de 18 sources avec
  organisme, couverture, domaines, accès et liens officiels.
- **Cinq nouveaux connecteurs** : WHO Global Health Observatory, World Bank
  Health Indicators, UNICEF Data Warehouse (SDMX), UN Global SDG Indicators et
  DHS Program Indicator Data rejoignent HDX et ReliefWeb.
- **Capacités explicites** : l'interface distingue 7 API interrogeables et
  planifiables de 11 portails de référence dont l'accès reste manuel, variable ou
  soumis à inscription.
- **Provenance inchangée** : la réponse distante originale est archivée avec son
  empreinte SHA-256 avant normalisation ; les téléchargements restent bornés par
  les préférences du projet.

- **Liste des téléchargements officiels** : COD-AB (limites administratives) et
  COD-PS (statistiques de population infranationales) sont sélectionnables par
  projet. COD-CS est visible mais désactivé tant que son registre vérifié est
  vide ; COD-HP est signalé comme retiré par OCHA.
- **Liste géographique contrôlée** : chaque option est un pays ou une zone à la
  fois dans ONU M49 et dans les groupes HDX canoniques de toutes les familles
  sélectionnées. Le 7 août 2026, HDP vérifie 163 options COD-AB, 146 COD-PS et
  143 dans leur intersection.
- **Synchronisation atomique** : HDP ne télécharge pas seulement une partie des
  familles demandées si le catalogue change. La réponse CKAN et la décision
  restent archivées pour diagnostic.
- **Formats adaptés** : format géospatial choisi pour COD-AB ; ressources
  CSV/XLSX pour COD-PS. La famille est conservée avec la provenance locale.
- **Dépôt GitHub par projet** : paramètres distincts (propriétaire, nom, description et visibilité) et création réelle après confirmation. Le jeton reste global dans `.env` et n'est jamais exposé par l'API.
- **Migration explicite** : un ancien profil déjà limité à un pays est conservé ;
  les anciens profils monde/région sont suspendus jusqu'au choix dans la nouvelle liste.
- **Reprise progressive** : les ressources déjà téléchargées ne consomment plus le quota du passage ; les suivantes sont reportées proprement.
- **Socle 2.0 conservé** : projets, ressources locales, préférences, scripts non exécutables et planifications restent isolés par projet.

- **Projets** : chaque projet possède ses acquisitions, ressources, préférences, scripts et planifications.
- **Téléchargement automatique** : option par recherche ou planification, avec limites de taille, de quantité et de formats.
- **Planificateur persistant** : exécutions périodiques à partir de 15 minutes et historique conservé dans PostgreSQL.
- **Données locales** : inventaire, téléchargement depuis l'interface, contrôle SHA-256 et suppression du fichier avec conservation de la trace.
- **Scripts par projet** : création et modification de contenu Python, R, SQL ou autre. Seuls Python et R sont exécutables ; les autres langages restent stockés.
- **Migration 1.5** : les acquisitions existantes rejoignent automatiquement le « Projet par défaut » ; `.env`, le volume PostgreSQL et `data/` sont conservés.

## Installation Windows

1. Téléchargez `HumanitarianDataPlatform_Windows_Portable_v4.0.0.zip`.
2. Décompressez l'archive.
3. Vérifiez l’empreinte du ZIP depuis `SHA256SUMS.txt`.
4. Créez `.env` à côté de `compose.yaml` avec au minimum un mot de passe
   PostgreSQL aléatoire.
5. Lancez `start-hdp.cmd` ; Docker Desktop est nécessaire et R reste facultatif.

L’EXE 3.0.0 conservé dans les archives historiques n’installe pas la version
4.0.0 et n’est pas inclus comme installateur final de ce gel.

Le véritable EXE 4.0.0 est construit sur un runner Windows x64 par le workflow
`HDP Windows installer`. Il est publié avec son empreinte SHA-256 comme artefact
GitHub Actions ; il reste non signé tant qu’aucun certificat Authenticode n’est
fourni.

L'application s'ouvre sur `http://localhost:8080` ou sur un port libre entre `18080` et `18279`. Elle reste liée à `127.0.0.1`.

Si les paramètres d'un projet affichent « `GITHUB_TOKEN absent : la création reste indisponible.` », utilisez le [correctif Windows automatisé](source/HDP_Configurer_GitHub_v3.0.0.cmd). Il configure le secret par saisie masquée, recrée uniquement l'API et vérifie le résultat sans révéler le jeton.

## Documentation

- [Guide utilisateur 4.0.0](docs/USER_GUIDE_V4.0.0.md)
- [Installation portable 4.0.0](docs/INSTALLATION_V4.0.0.md)
- [Architecture, données et API](docs/ARCHITECTURE.md)
- [Migration vers 3.0.0](docs/MIGRATION_V2.md)
- [Revue de sécurité 4.0.0](docs/SECURITY_REVIEW_V4.0.0.md)
- [Sauvegarde et restauration](docs/BACKUP_RESTORE_V4.0.0.md)
- [Limites connues](docs/KNOWN_LIMITATIONS_V4.0.0.md)
- [Passerelle REST GitHub](docs/GITHUB_API.md)
- [Cahier des charges final](docs/CAHIER_DES_CHARGES_V3.0.0.md)
- [Référence API 4.0.0](docs/API_REFERENCE_V4.0.0.md)
- [Matrice des sources](docs/SOURCE_CAPABILITY_MATRIX_V4.0.0.md)
- [Rapport de validation](docs/VALIDATION_REPORT_V4.0.0.md)
- [Prompt global de production](HDP_Prompt_production_global_v4.0.0.txt)
- [Développement et validation](docs/DEVELOPMENT.md)
- [Dépannage](docs/TROUBLESHOOTING.md)
- [Livrables et vérification 4.0.0](docs/ARTIFACTS_V4.0.0.md)
- [Inventaire historique des livrables](docs/ARTIFACTS.md)
- [Journal des versions](CHANGELOG.md)
- [Prompt historique de reconstruction de l’état v2.5.0](docs/PROMPT_RECONSTRUCTION_ETAT_ACTUEL_V2.5.0.md)

FastAPI publie aussi une documentation interactive locale sur `/docs` lorsque l'application tourne.

Le journal texte `CHANGELOG_HDP.log` est également embarqué dans l'installateur
et copié à la racine de l'application Windows.

## Sources prises en charge

| Source | Recherche / planification | Accès |
|---|---:|---|
| HDX / CKAN | Oui | API publique ; ressources et COD selon la licence du jeu |
| ReliefWeb | Oui | `RELIEFWEB_APPNAME` pré-approuvé requis |
| WHO Global Health Observatory | Oui | API OData publique |
| World Bank Health Indicators | Oui | Indicators API v2 publique |
| UNICEF Data Warehouse | Oui | API SDMX publique |
| UN Global SDG Indicators | Oui | API publique |
| DHS Program Indicator Data | Oui | Indicateurs agrégés publics ; microdonnées sur inscription |
| HDX HAPI v2 | Oui | `HDX_HAPI_APP_IDENTIFIER` requis ; API bêta |
| UNHCR Refugee Statistics | Oui | API publique, séries agrégées |
| GDACS | Oui | API GeoJSON publique |

L'onglet « Sources sanitaires » référence aussi WHO Mortality Database, WHO
GLASS, WHO FluNet/FluID, WHO Global Health Estimates, UNAIDS AIDSinfo, IHME
GHDx, UNICEF MICS, UN World Population Prospects, Global.health, WorldPop et Our
World in Data. Ces portails ne sont pas présentés comme des API actives.

Voir les documentations officielles de l'[Action API CKAN](https://docs.ckan.org/en/latest/api/) et de l'[API ReliefWeb V2](https://apidoc.reliefweb.int/). Les quotas, licences et conditions d'utilisation de chaque source restent applicables.

## Organisation du dépôt

```text
source/          code FastAPI, interface, installateur Win32 et tests
docs/            documentation Markdown consultable dans GitHub
dist/v4.0.0/     payload portable, sources, documentation et empreintes
dist/v3.0.0/     livrables finaux, installateur, documentation et empreintes
dist/v2.5.0/     installateur, archives, empreintes et prompt de reprise
dist/v2.4.0/     livrables historiques intacts
dist/v2.3.2/     livrables historiques intacts
dist/v2.3.1/     livrables historiques intacts
dist/v2.0/       livrables historiques intacts
dist/v1.5/       livrables historiques intacts
tools/           génération de la notice PDF
```

## Sécurité et licence

HDP 4.0.0 est une application locale mono-utilisateur, sans authentification,
et ne doit pas être exposée directement sur Internet. Les scripts exécutés
restent du code local de confiance malgré les runners isolés. Un dépôt GitHub
public ne doit être créé qu'après vérification du contenu et choix d’une licence.

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie et ajoutée.
