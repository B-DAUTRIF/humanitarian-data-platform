# Humanitarian Data Platform 3.0.0 — version finale

Application locale Windows pour rechercher des données humanitaires publiques, télécharger leurs ressources, les organiser par projets et automatiser les acquisitions géographiques.

## Fonctionnalités finales 3.0.0

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

## État de validation final

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

- **Paramètres API versionnés** : contrats distincts pour les 7 connecteurs,
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
- **Windows** : EXE 3.0.0 réellement compilé en PE32+ GUI x64 ; détection de
  mise à niveau, sauvegarde de `.env`, ASLR/NX et payload contrôlés. L'essai sur
  Windows avec Docker reste obligatoire.

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

1. Téléchargez `HumanitarianDataPlatform_Windows_v3.0.0.zip`.
2. Décompressez l'archive.
3. Vérifiez l'empreinte :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe -Algorithm SHA256
   ```

4. Comparez-la au fichier `.exe.sha256`, puis lancez l'installateur.
5. Docker Desktop est nécessaire ; le module R reste facultatif.

L'application s'ouvre sur `http://localhost:8080` ou sur un port libre entre `18080` et `18279`. Elle reste liée à `127.0.0.1`.

Si les paramètres d'un projet affichent « `GITHUB_TOKEN absent : la création reste indisponible.` », utilisez le [correctif Windows automatisé](source/HDP_Configurer_GitHub_v3.0.0.cmd). Il configure le secret par saisie masquée, recrée uniquement l'API et vérifie le résultat sans révéler le jeton.

## Documentation

- [Guide utilisateur](docs/USER_GUIDE.md)
- [Installation et mise à niveau](docs/INSTALLATION.md)
- [Architecture, données et API](docs/ARCHITECTURE.md)
- [Migration vers 3.0.0](docs/MIGRATION_V2.md)
- [Sécurité et confidentialité](docs/SECURITY.md)
- [Passerelle REST GitHub](docs/GITHUB_API.md)
- [Cahier des charges final](docs/CAHIER_DES_CHARGES_V3.0.0.md)
- [Référence API](docs/API_REFERENCE_V3.0.0.md)
- [Prompt global de production](HDP_Prompt_production_global_v3.0.0.txt)
- [Développement et validation](docs/DEVELOPMENT.md)
- [Dépannage](docs/TROUBLESHOOTING.md)
- [Inventaire des livrables et empreintes](docs/ARTIFACTS.md)
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

L'onglet « Sources sanitaires » référence aussi WHO Mortality Database, WHO
GLASS, WHO FluNet/FluID, WHO Global Health Estimates, UNAIDS AIDSinfo, IHME
GHDx, UNICEF MICS, UN World Population Prospects, Global.health, WorldPop et Our
World in Data. Ces portails ne sont pas présentés comme des API actives.

Voir les documentations officielles de l'[Action API CKAN](https://docs.ckan.org/en/latest/api/) et de l'[API ReliefWeb V2](https://apidoc.reliefweb.int/). Les quotas, licences et conditions d'utilisation de chaque source restent applicables.

## Organisation du dépôt

```text
source/          code FastAPI, interface, installateur Win32 et tests
docs/            documentation Markdown consultable dans GitHub
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

HDP 3.0.0 est une application locale mono-utilisateur, sans authentification, et ne doit pas être exposée directement sur Internet. Les téléchargements refusent les URL non HTTP(S), les identifiants intégrés et les destinations réseau non publiques ; chaque projet impose des limites. Les scripts exécutés doivent être considérés comme du code local de confiance, même si les runners sont sans réseau et bornés. Les groupements M49 sont statistiques et n'impliquent aucune position politique. Un dépôt GitHub public ne doit être créé qu'après vérification de son contenu et de sa licence.

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie et ajoutée.
