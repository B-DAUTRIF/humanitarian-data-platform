# Humanitarian Data Platform 2.0.0

Application locale pour organiser des acquisitions humanitaires par projets.

## Démarrage

1. Lancez Docker Desktop.
2. Double-cliquez sur `start-hdp.cmd`.
3. L'interface s'ouvre sur le port `HDP_PORT` enregistré dans `.env`.

Le service est lié exclusivement à `127.0.0.1`. PostgreSQL/PostGIS n'est pas exposé sur Windows.

## Fonctionnalités

- projets isolant préférences, acquisitions, ressources, scripts et planifications ;
- recherche ReliefWeb et HDX/CKAN avec archivage JSON et empreinte SHA-256 ;
- téléchargement optionnel des ressources avec limites de taille, de quantité et de formats ;
- planificateur persistant, intervalle minimal de 15 minutes et historique des exécutions ;
- gestion locale : inventaire, téléchargement, vérification SHA-256 et suppression avec conservation de la provenance ;
- stockage et modification de scripts par projet, sans exécution automatique.

Les données sont écrites dans `data/raw/<projet>` et `data/projects/<projet>/resources`. Les métadonnées sont conservées dans PostgreSQL.

ReliefWeb exige un `appname` pré-approuvé. Sans cet identifiant, HDX reste utilisable. Les quotas et conditions des sources restent applicables.

## Mise à niveau depuis 1.5

Le schéma est migré au démarrage. Les acquisitions existantes rejoignent le « Projet par défaut ». Le volume PostgreSQL, `.env` et les fichiers existants sont conservés.

## Arrêt

Exécutez `stop-hdp.cmd`. Les volumes et fichiers locaux restent intacts.

## Limite de sécurité

HDP 2.0 est une application locale, non un serveur Internet durci. Les scripts sont gérés comme contenu uniquement : aucune route ne les exécute.
