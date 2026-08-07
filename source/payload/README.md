# Humanitarian Data Platform 2.3.1

Application locale pour organiser des acquisitions humanitaires par projets.

## Démarrage

1. Lancez Docker Desktop.
2. Double-cliquez sur `start-hdp.cmd`.
3. L'interface s'ouvre sur le port `HDP_PORT` enregistré dans `.env`.

Le fichier `.env` peut aussi définir `GITHUB_TOKEN` pour permettre la création confirmée d'un dépôt depuis les paramètres d'un projet. Ce secret n'est jamais exposé par l'API.

Le service est lié exclusivement à `127.0.0.1`. PostgreSQL/PostGIS n'est pas exposé sur Windows.

## Fonctionnalités

- projets isolant préférences, acquisitions, ressources, scripts et planifications ;
- recherche ReliefWeb et HDX/CKAN avec archivage JSON et empreinte SHA-256 ;
- téléchargement optionnel des ressources avec limites de taille, de quantité et de formats ;
- planificateur persistant, intervalle minimal de 15 minutes et historique des exécutions ;
- gestion locale : inventaire, téléchargement, vérification SHA-256 et suppression avec conservation de la provenance ;
- stockage et modification de scripts par projet, sans exécution automatique.
- périmètre géographique choisi dans la nomenclature officielle ONU M49 ;
- téléchargement limité aux COD-AB officiels OCHA/HDX, avec provenance complète.

Les données sont écrites dans `data/raw/<projet>` et `data/projects/<projet>/resources`. Les métadonnées sont conservées dans PostgreSQL.

ReliefWeb exige un `appname` pré-approuvé. Sans cet identifiant, HDX reste utilisable. Les quotas et conditions des sources restent applicables.

## Mise à niveau depuis 1.5

Le schéma est migré au démarrage. Les acquisitions existantes rejoignent le « Projet par défaut ». Le volume PostgreSQL, `.env` et les fichiers existants sont conservés.

## Arrêt

Exécutez `stop-hdp.cmd`. Les volumes et fichiers locaux restent intacts.

## Module géographique officiel

La saisie libre d'un identifiant HDX n'est pas proposée dans ce module. HDP
interroge uniquement la série `COD - Subnational Administrative Boundaries` et
accepte les niveaux `cod-enhanced`, ou `cod-standard` lorsque la politique du
projet l'autorise. Les codes M49, ISO3, éditeur, licence et date des métadonnées
sont archivés avec chaque ressource.

## Limite de sécurité

HDP 2.3.1 est une application locale, non un serveur Internet durci. Les scripts sont gérés comme contenu uniquement : aucune route ne les exécute. Les groupements M49 sont statistiques et n'impliquent aucune prise de position politique.
