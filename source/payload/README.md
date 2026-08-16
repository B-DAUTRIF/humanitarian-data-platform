# Humanitarian Data Platform 5.0.1

## Version 5.0.1

Chaque source possède désormais ses propres réglages globaux et projet, sa
fiche technique, ses liens officiels et une prévisualisation cURL/Python/R sans
secret. La page **USER - Technologies & code** ouvre le code et 87 ressources
officielles classées par rôle. Les paramètres et données 4.0.0 sont conservés.

Application locale pour organiser des acquisitions humanitaires par projets.

## Démarrage

1. Lancez Docker Desktop.
2. Double-cliquez sur `start-hdp.cmd`.
3. L'interface s'ouvre sur le port `HDP_PORT` enregistré dans `.env`.

Le fichier `.env` peut aussi définir `RELIEFWEB_APPNAME`,
`HDX_HAPI_APP_IDENTIFIER` et `GITHUB_TOKEN`. Ces secrets ne sont jamais exposés
par l'API.

Le service est lié exclusivement à `127.0.0.1`. PostgreSQL/PostGIS n'est pas exposé sur Windows.

La version 4.0.0 conserve les familles officielles sous forme de liste. COD-AB
et COD-PS sont sélectionnables ; COD-CS est visible mais désactivé tant que son
registre vérifié est vide ; COD-HP est indiqué comme retiré. La liste de pays ou
zones est recalculée sur l'intersection ONU M49 × groupes HDX des familles
sélectionnées.

## Fonctionnalités

- registre versionné des paramètres pour les 10 connecteurs API actifs ;
- recherche fédérée parallèle avec dates, localisation et paramètres propres ;
- import atomique de données, scripts et documents avec contrôle de contenu ;
- périodicité et planification directement depuis chaque fichier ;
- recettes CSV/TSV, résultats dérivés, lignée et scripts Python/R ;
- carte multi-couches et vues SQL du projet en lecture seule ;
- réglages globaux (activation, délai, reprises) et modèles distincts par projet ;
- prévisualisation locale de la commande et du lien officiel avant toute requête ;
- bibliothèque filtrable par source, format, sujet, organisme et localisation ;
- projets isolant préférences, acquisitions, ressources, scripts et planifications ;
- recherche ReliefWeb et HDX/CKAN avec archivage JSON et empreinte SHA-256 ;
- recherche directe des catalogues OMS/GHO, Banque mondiale/WDI, UNICEF/SDMX,
  ONU/ODD et DHS, sans identifiant supplémentaire ;
- catalogue intégré de 18 sources mondiales distinguant 7 connecteurs API actifs
  de 11 portails de référence, avec domaines, accès, inscription et liens officiels ;
- téléchargement optionnel des ressources avec limites de taille, de quantité et de formats ;
- planificateur persistant, intervalle minimal de 15 minutes et historique des exécutions ;
- gestion locale : inventaire, téléchargement, vérification SHA-256 et suppression avec conservation de la provenance ;
- versions immuables et exécution Python/R dans des runners distincts sans réseau ;
- veille RSS officielle ReliefWeb par projet ;
- chronologie Gantt des opérations ;
- import GeoJSON PostGIS, Leaflet embarqué et exports QGIS/R ;
- passerelle REST GitHub locale : lectures classiques, écritures verrouillées ;
- pays ou zone choisi dans la liste commune ONU M49 × HDX COD ;
- téléchargements COD-AB et COD-PS officiels, avec provenance de la famille ;
- affichage explicite de COD-CS indisponible et COD-HP retiré.

Les données sont écrites dans `data/raw/<projet>` et `data/projects/<projet>/resources`. Les métadonnées sont conservées dans PostgreSQL.

ReliefWeb exige un `appname` pré-approuvé. Sans cet identifiant, HDX et les cinq
connecteurs sanitaires publics restent utilisables. DHS n'exige pas de compte
pour ses indicateurs agrégés, mais l'accès à ses microdonnées est une procédure
distincte sur inscription. Les quotas, licences et conditions de chaque source
restent applicables.

## Sources épidémiologiques et sanitaires

Les sources interrogeables dans « Recherche » et « Planifications » sont : HDX,
ReliefWeb, WHO Global Health Observatory, World Bank Health Indicators, UNICEF
Data Warehouse (SDMX), UN Global SDG Indicators Database et DHS Program
Indicator Data. Les réponses distantes brutes sont archivées avant normalisation.

L'onglet « Sources sanitaires » référence aussi WHO Mortality Database, WHO
GLASS, WHO FluNet/FluID, WHO Global Health Estimates, UNAIDS AIDSinfo, IHME
GHDx, UNICEF MICS, UN World Population Prospects, Global.health, WorldPop et Our
World in Data. Ces entrées ouvrent leur portail officiel : HDP ne présente pas
comme automatisable une API publique stable qui n'est pas documentée.

## Mise à niveau et compatibilité

Le schéma est migré au démarrage par migrations idempotentes. Les acquisitions anciennes rejoignent le « Projet par défaut ». Le volume PostgreSQL, toutes les lignes inconnues de `.env` et les fichiers existants sont conservés. La compatibilité garantie à ce jalon porte sur la structure 2.5.0 ; les versions plus anciennes restent prises en charge par le chemin historique, mais devront être qualifiées à partir de fixtures ou d'archives représentatives avant d'être déclarées garanties.

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

HDP 5.0.1 est une application locale, non un serveur Internet durci. Seuls les
scripts Python/R locaux et de confiance doivent être exécutés. Les runners sont
non privilégiés, sans réseau et bornés, mais ne constituent pas une isolation
multi-utilisateur.
