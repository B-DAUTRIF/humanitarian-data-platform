# Humanitarian Data Platform 2.4.0

Application locale Windows pour rechercher des données humanitaires publiques, télécharger leurs ressources, les organiser par projets et automatiser les acquisitions géographiques.

## Nouveautés de la version 2.4.0

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
- **Scripts par projet** : création et modification de contenu Python, R, SQL ou autre. L'exécution est volontairement désactivée dans cette version.
- **Migration 1.5** : les acquisitions existantes rejoignent automatiquement le « Projet par défaut » ; `.env`, le volume PostgreSQL et `data/` sont conservés.

## Installation Windows

1. Téléchargez [`HumanitarianDataPlatform_Windows_v2.4.0.zip`](dist/v2.4.0/HumanitarianDataPlatform_Windows_v2.4.0.zip).
2. Décompressez l'archive.
3. Vérifiez l'empreinte :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v2.4.0.exe -Algorithm SHA256
   ```

4. Comparez-la au fichier `.exe.sha256`, puis lancez l'installateur.
5. Docker Desktop est nécessaire ; le module R reste facultatif.

L'application s'ouvre sur `http://localhost:8080` ou sur un port libre entre `18080` et `18279`. Elle reste liée à `127.0.0.1`.

Si les paramètres d'un projet affichent « `GITHUB_TOKEN absent : la création reste indisponible.` », utilisez le [correctif Windows automatisé](source/HDP_Configurer_GitHub_v2.4.0.cmd). Il configure le secret par saisie masquée, recrée uniquement l'API et vérifie le résultat sans révéler le jeton.

## Documentation

- [Guide utilisateur](docs/USER_GUIDE.md)
- [Installation et mise à niveau](docs/INSTALLATION.md)
- [Architecture, données et API](docs/ARCHITECTURE.md)
- [Migration depuis 1.5](docs/MIGRATION_V2.md)
- [Sécurité et confidentialité](docs/SECURITY.md)
- [Développement et validation](docs/DEVELOPMENT.md)
- [Dépannage](docs/TROUBLESHOOTING.md)
- [Inventaire des livrables et empreintes](docs/ARTIFACTS.md)
- [Journal des versions](CHANGELOG.md)
- [Prompt autonome de reconstruction de l’état v2.4.0](docs/PROMPT_RECONSTRUCTION_ETAT_ACTUEL_V2.4.0.md)
- [Notice détaillée PDF](dist/v2.4.0/Notice_detaillee_Humanitarian_Data_Platform_v2.4.0.pdf)

FastAPI publie aussi une documentation interactive locale sur `/docs` lorsque l'application tourne.

Le journal texte `CHANGELOG_HDP.log` est également embarqué dans l'installateur
et copié à la racine de l'application Windows.

## Sources prises en charge

| Source | Recherche | Ressources automatiques |
|---|---:|---:|
| HDX / CKAN | Oui | Oui, dont COD-AB/COD-PS officiels filtrés par intersection ONU M49 × HDX |
| ReliefWeb | Oui, avec `RELIEFWEB_APPNAME` pré-approuvé | Oui lorsque les métadonnées du rapport contiennent des fichiers |

Voir les documentations officielles de l'[Action API CKAN](https://docs.ckan.org/en/latest/api/) et de l'[API ReliefWeb V2](https://apidoc.reliefweb.int/). Les quotas, licences et conditions d'utilisation de chaque source restent applicables.

## Organisation du dépôt

```text
source/          code FastAPI, interface, installateur Win32 et tests
docs/            documentation Markdown consultable dans GitHub
dist/v2.4.0/     installateur, archives, empreintes, notice et prompt de reprise
dist/v2.3.2/     livrables historiques intacts
dist/v2.3.1/     livrables historiques intacts
dist/v2.0/       livrables historiques intacts
dist/v1.5/       livrables historiques intacts
tools/           génération de la notice PDF
```

## Sécurité et licence

HDP 2.4.0 est une application locale mono-utilisateur, sans authentification, et ne doit pas être exposée directement sur Internet. Les téléchargements refusent les URL non HTTP(S), les identifiants intégrés et les destinations réseau non publiques ; chaque projet impose des limites. Les groupements M49 sont statistiques et n'impliquent aucune position politique. Un dépôt GitHub public ne doit être créé qu'après vérification de son contenu et de sa licence.

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie et ajoutée.
