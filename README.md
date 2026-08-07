# Humanitarian Data Platform 2.0

Application locale Windows pour rechercher des données humanitaires publiques, télécharger leurs ressources, les organiser par projets et automatiser les acquisitions.

## Nouveautés de la version 2.0

- **Projets** : chaque projet possède ses acquisitions, ressources, préférences, scripts et planifications.
- **Téléchargement automatique** : option par recherche ou planification, avec limites de taille, de quantité et de formats.
- **Planificateur persistant** : exécutions périodiques à partir de 15 minutes et historique conservé dans PostgreSQL.
- **Données locales** : inventaire, téléchargement depuis l'interface, contrôle SHA-256 et suppression du fichier avec conservation de la trace.
- **Scripts par projet** : création et modification de contenu Python, R, SQL ou autre. L'exécution est volontairement désactivée dans cette version.
- **Migration 1.5** : les acquisitions existantes rejoignent automatiquement le « Projet par défaut » ; `.env`, le volume PostgreSQL et `data/` sont conservés.

## Installation Windows

1. Téléchargez [`HumanitarianDataPlatform_Windows_v2.0.zip`](dist/v2.0/HumanitarianDataPlatform_Windows_v2.0.zip).
2. Décompressez l'archive.
3. Vérifiez l'empreinte :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v2.0.exe -Algorithm SHA256
   ```

4. Comparez-la au fichier `.exe.sha256`, puis lancez l'installateur.
5. Docker Desktop est nécessaire ; le module R reste facultatif.

L'application s'ouvre sur `http://localhost:8080` ou sur un port libre entre `18080` et `18279`. Elle reste liée à `127.0.0.1`.

## Documentation

- [Guide utilisateur](docs/USER_GUIDE.md)
- [Installation et mise à niveau](docs/INSTALLATION.md)
- [Architecture, données et API](docs/ARCHITECTURE.md)
- [Migration depuis 1.5](docs/MIGRATION_V2.md)
- [Sécurité et confidentialité](docs/SECURITY.md)
- [Développement et validation](docs/DEVELOPMENT.md)
- [Dépannage](docs/TROUBLESHOOTING.md)
- [Inventaire des livrables et empreintes](docs/ARTIFACTS.md)
- [Notice détaillée PDF](dist/v2.0/Notice_detaillee_Humanitarian_Data_Platform_v2.0.pdf)

FastAPI publie aussi une documentation interactive locale sur `/docs` lorsque l'application tourne.

## Sources prises en charge

| Source | Recherche | Ressources automatiques |
|---|---:|---:|
| HDX / CKAN | Oui | Oui, à partir des URL de ressources CKAN |
| ReliefWeb | Oui, avec `RELIEFWEB_APPNAME` pré-approuvé | Oui lorsque les métadonnées du rapport contiennent des fichiers |

Voir les documentations officielles de l'[Action API CKAN](https://docs.ckan.org/en/latest/api/) et de l'[API ReliefWeb V2](https://apidoc.reliefweb.int/). Les quotas, licences et conditions d'utilisation de chaque source restent applicables.

## Organisation du dépôt

```text
source/          code FastAPI, interface, installateur Win32 et tests
docs/            documentation Markdown consultable dans GitHub
dist/v2.0/       installateur, archives, empreintes, notices et prompt de reprise
dist/v1.5/       livrables historiques intacts
tools/           génération de la notice PDF
```

## Sécurité et licence

HDP 2.0 est une application locale mono-utilisateur, sans authentification, et ne doit pas être exposée directement sur Internet. Les téléchargements refusent les URL non HTTP(S), les identifiants intégrés et les destinations réseau non publiques ; chaque projet impose des limites.

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie et ajoutée.
