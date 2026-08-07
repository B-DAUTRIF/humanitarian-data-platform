# Humanitarian Data Platform 2.4.0

Application locale pour organiser des acquisitions humanitaires par projets.

## Démarrage

1. Lancez Docker Desktop.
2. Double-cliquez sur `start-hdp.cmd`.
3. L'interface s'ouvre sur le port `HDP_PORT` enregistré dans `.env`.

Le fichier `.env` peut aussi définir `GITHUB_TOKEN` pour permettre la création confirmée d'un dépôt depuis les paramètres d'un projet. Ce secret n'est jamais exposé par l'API.

Le service est lié exclusivement à `127.0.0.1`. PostgreSQL/PostGIS n'est pas exposé sur Windows.

La version 2.4.0 présente les familles officielles sous forme de liste. COD-AB
et COD-PS sont sélectionnables ; COD-CS est visible mais désactivé tant que son
registre vérifié est vide ; COD-HP est indiqué comme retiré. La liste de pays ou
zones est recalculée sur l'intersection ONU M49 × groupes HDX des familles
sélectionnées.

## Fonctionnalités

- projets isolant préférences, acquisitions, ressources, scripts et planifications ;
- recherche ReliefWeb et HDX/CKAN avec archivage JSON et empreinte SHA-256 ;
- téléchargement optionnel des ressources avec limites de taille, de quantité et de formats ;
- planificateur persistant, intervalle minimal de 15 minutes et historique des exécutions ;
- gestion locale : inventaire, téléchargement, vérification SHA-256 et suppression avec conservation de la provenance ;
- stockage et modification de scripts par projet, sans exécution automatique.
- pays ou zone choisi dans la liste commune ONU M49 × HDX COD ;
- téléchargements COD-AB et COD-PS officiels, avec provenance de la famille ;
- affichage explicite de COD-CS indisponible et COD-HP retiré.

Les données sont écrites dans `data/raw/<projet>` et `data/projects/<projet>/resources`. Les métadonnées sont conservées dans PostgreSQL.

ReliefWeb exige un `appname` pré-approuvé. Sans cet identifiant, HDX reste utilisable. Les quotas et conditions des sources restent applicables.

## Mise à niveau depuis 1.5

Le schéma est migré au démarrage. Les acquisitions existantes rejoignent le « Projet par défaut ». Le volume PostgreSQL, `.env` et les fichiers existants sont conservés.

## Arrêt

Exécutez `stop-hdp.cmd`. Les volumes et fichiers locaux restent intacts.

## Module géographique officiel

HDP interroge les identifiants canoniques `cod-ab-*` et `cod-ps-*`, puis vérifie
leur unique groupe ISO3 contre ONU M49. COD-AB exige `cod-enhanced` ou
`cod-standard` et utilise le format géospatial choisi ; COD-PS utilise les
ressources CSV/XLSX. Si une famille manque, aucun sous-ensemble n'est téléchargé.
Les codes M49, ISO3, famille, niveau publié, éditeur, licence et date des
métadonnées sont archivés avec chaque ressource.

## Limite de sécurité

HDP 2.4.0 est une application locale, non un serveur Internet durci. Les scripts sont gérés comme contenu uniquement : aucune route ne les exécute. Les groupements M49 sont statistiques et n'impliquent aucune prise de position politique.
