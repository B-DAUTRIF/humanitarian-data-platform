# Humanitarian Data Platform 1.5.0

Socle local client-serveur pour rechercher, acquérir et archiver des données humanitaires publiques.

## Démarrage

1. Lancez Docker Desktop.
2. Double-cliquez sur `start-hdp.cmd`.
3. L'interface s'ouvre sur le port local enregistré dans `.env` (`HDP_PORT`). L'installateur utilise 8080 s'il est disponible, sinon il choisit automatiquement un port libre entre 18080 et 18279.

Le service reste lié exclusivement à `127.0.0.1` : il n'est pas exposé au réseau local.

## Services

- API et interface : FastAPI/Python ;
- base : PostgreSQL/PostGIS, non exposée sur Windows ;
- analyses : R/plumber ;
- sources MVP : ReliefWeb et HDX/CKAN.

Depuis novembre 2025, ReliefWeb exige un `appname` pré-approuvé. L'installateur peut l'enregistrer dans `.env`. Sans cet identifiant, HDX reste utilisable et l'API explique comment activer ReliefWeb.

Les réponses brutes sont écrites sous `data/raw` avec une empreinte SHA-256. Les métadonnées de provenance sont enregistrées dans PostgreSQL.

Le module R est facultatif au premier démarrage car son image dépasse 300 Mo. S'il a été sélectionné dans l'installateur, `start-hdp-with-r.cmd` démarre également ce service analytique. Le cœur Python/PostGIS fonctionne sans lui.

## Arrêt

Exécutez `stop-hdp.cmd`. Les données PostgreSQL et les fichiers bruts sont conservés.

## Limites

Cette version est un socle local de développement. Elle n'est pas un déploiement serveur de production durci. Les conditions d'utilisation et quotas des sources distantes restent applicables.
