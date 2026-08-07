# Humanitarian Data Platform 2.3.2

Application locale Windows pour rechercher des données humanitaires publiques, télécharger leurs ressources, les organiser par projets et automatiser les acquisitions géographiques.

## Nouveautés de la version 2.3.2

- **Compatibilité avec le catalogue HDX actuel** : les COD-AB canoniques
  `cod-ab-<iso3>` restent reconnus lorsque l'API CKAN indexe la série officielle
  sans renvoyer le champ `dataseries_name` dans le résultat.
- **État géographique cohérent** : changer de périmètre, de politique COD ou de
  format efface le résultat de l'ancien profil et affiche « synchronisation
  requise » jusqu'au prochain passage.
- **Dépôt GitHub par projet** : paramètres distincts (propriétaire, nom, description et visibilité) et création réelle après confirmation. Le jeton reste global dans `.env` et n'est jamais exposé par l'API.
- **Périmètre officiel ONU M49** : choix hiérarchique du monde, d'une région, sous-région, région intermédiaire, pays ou zone.
- **COD-AB officiels uniquement** : plus d'identifiant HDX libre dans le module géographique. Seule la série OCHA/HDX `COD - Subnational Administrative Boundaries` est admissible, avec niveau amélioré ou standard officiel en repli.
- **Provenance géographique** : code M49, ISO3, niveau COD, éditeur, licence et date des métadonnées sont archivés avec la ressource.
- **Reprise progressive** : les ressources déjà téléchargées ne consomment plus le quota du passage ; les suivantes sont reportées proprement.
- **Socle 2.0 conservé** : projets, ressources locales, préférences, scripts non exécutables et planifications restent isolés par projet.

- **Projets** : chaque projet possède ses acquisitions, ressources, préférences, scripts et planifications.
- **Téléchargement automatique** : option par recherche ou planification, avec limites de taille, de quantité et de formats.
- **Planificateur persistant** : exécutions périodiques à partir de 15 minutes et historique conservé dans PostgreSQL.
- **Données locales** : inventaire, téléchargement depuis l'interface, contrôle SHA-256 et suppression du fichier avec conservation de la trace.
- **Scripts par projet** : création et modification de contenu Python, R, SQL ou autre. L'exécution est volontairement désactivée dans cette version.
- **Migration 1.5** : les acquisitions existantes rejoignent automatiquement le « Projet par défaut » ; `.env`, le volume PostgreSQL et `data/` sont conservés.

## Installation Windows

1. Téléchargez [`HumanitarianDataPlatform_Windows_v2.3.2.zip`](dist/v2.3.2/HumanitarianDataPlatform_Windows_v2.3.2.zip).
2. Décompressez l'archive.
3. Vérifiez l'empreinte :

   ```powershell
   Get-FileHash .\HumanitarianDataPlatform_Setup_Native_GUI_v2.3.2.exe -Algorithm SHA256
   ```

4. Comparez-la au fichier `.exe.sha256`, puis lancez l'installateur.
5. Docker Desktop est nécessaire ; le module R reste facultatif.

L'application s'ouvre sur `http://localhost:8080` ou sur un port libre entre `18080` et `18279`. Elle reste liée à `127.0.0.1`.

Si les paramètres d'un projet affichent « `GITHUB_TOKEN absent : la création reste indisponible.` », utilisez le [correctif Windows automatisé](source/HDP_Configurer_GitHub_v2.3.2.cmd). Il configure le secret par saisie masquée, recrée uniquement l'API et vérifie le résultat sans révéler le jeton.

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
- [Prompt autonome de reconstruction de l’état v2.3.2](docs/PROMPT_RECONSTRUCTION_ETAT_ACTUEL_V2.3.2.md)
- [Notice détaillée PDF](dist/v2.3.2/Notice_detaillee_Humanitarian_Data_Platform_v2.3.2.pdf)

FastAPI publie aussi une documentation interactive locale sur `/docs` lorsque l'application tourne.

Le journal texte `CHANGELOG_HDP.log` est également embarqué dans l'installateur
et copié à la racine de l'application Windows.

## Sources prises en charge

| Source | Recherche | Ressources automatiques |
|---|---:|---:|
| HDX / CKAN | Oui | Oui, dont COD-AB officiels filtrés par périmètre ONU M49 |
| ReliefWeb | Oui, avec `RELIEFWEB_APPNAME` pré-approuvé | Oui lorsque les métadonnées du rapport contiennent des fichiers |

Voir les documentations officielles de l'[Action API CKAN](https://docs.ckan.org/en/latest/api/) et de l'[API ReliefWeb V2](https://apidoc.reliefweb.int/). Les quotas, licences et conditions d'utilisation de chaque source restent applicables.

## Organisation du dépôt

```text
source/          code FastAPI, interface, installateur Win32 et tests
docs/            documentation Markdown consultable dans GitHub
dist/v2.3.2/     installateur, archives, empreintes, notice et prompt de reprise
dist/v2.3.1/     livrables historiques intacts
dist/v2.0/       livrables historiques intacts
dist/v1.5/       livrables historiques intacts
tools/           génération de la notice PDF
```

## Sécurité et licence

HDP 2.3.2 est une application locale mono-utilisateur, sans authentification, et ne doit pas être exposée directement sur Internet. Les téléchargements refusent les URL non HTTP(S), les identifiants intégrés et les destinations réseau non publiques ; chaque projet impose des limites. Les groupements M49 sont statistiques et n'impliquent aucune position politique. Un dépôt GitHub public ne doit être créé qu'après vérification de son contenu et de sa licence.

Aucune licence HDP explicite n'est incluse. Le dépôt doit rester privé tant qu'une licence n'a pas été choisie et ajoutée.
