# Guide utilisateur - HDP 3.0.0 final

## Projet actif

Le sélecteur en haut de l'interface détermine le projet actif. Toutes les recherches, ressources, préférences, scripts et planifications affichés appartiennent à ce projet.

Créez un projet dans **Projets & préférences**, puis décrivez son objectif. Le « Projet par défaut » accueille les acquisitions anciennes et ne peut pas être archivé.

## Recherche et téléchargement automatique

Dans **Recherche** :

1. choisissez HDX/CKAN, ReliefWeb, WHO/GHO, World Bank Health Indicators,
   UNICEF/SDMX, UN/SDG ou DHS ;
2. saisissez les mots-clés et le nombre maximal de résultats ;
3. activez, si besoin, le téléchargement automatique ;
4. lancez l'acquisition.

La réponse JSON est toujours archivée avec son empreinte. Si le téléchargement est actif, les ressources présentes dans les métadonnées sont traitées dans l'ordre, jusqu'à la limite du projet. Un fichier trop grand, un format exclu ou une destination réseau privée est ignoré ou signalé en erreur sans annuler la provenance de l'acquisition.

## Sources sanitaires

L'onglet **Sources sanitaires** inventorie 18 sources mondiales. La pastille
**API active** signifie que la recherche et la planification sont intégrées à
HDP. La pastille **Référence** ouvre un portail officiel sans prétendre qu'une
API publique stable est disponible. La fiche indique aussi les domaines, les
modalités d'accès et la nécessité éventuelle d'un compte.

Les cinq nouveaux connecteurs recherchent des indicateurs ou flux, pas des
microdonnées individuelles. Pour DHS et MICS, une inscription distincte reste
nécessaire lorsque l'utilisateur souhaite accéder aux microdonnées.

## Paramètres des sources

La rubrique **Paramètres des sources** sépare deux périmètres :

- les réglages globaux du connecteur : activation, délai maximal, nouvelles
  tentatives et délai initial de reprise ;
- les réglages du projet actif : activation de la source, paramètres propres à
  son API, limite, téléchargement et valeurs par défaut de planification.

Choisissez une source : le formulaire est construit depuis son contrat versionné.
**Prévisualiser la requête** valide les valeurs, enregistre le modèle du projet
et affiche l'URL et la commande assainies sans appeler le service distant. Un
secret éventuel est désigné par son nom de variable, jamais par sa valeur.

## Bibliothèque locale

La rubrique **Données locales** filtre les ressources par source, format, sujet,
organisme et localisation. Les nouvelles acquisitions conservent aussi la date
de publication et les métadonnées normalisées disponibles. Les lignes plus
anciennes restent visibles même si ces nouveaux champs sont vides.

## Préférences

Chaque projet définit :

- activation du téléchargement automatique par défaut ;
- taille maximale de chaque fichier, de 1 Mio à 2 Gio ;
- nombre maximal de ressources par acquisition, de 1 à 100 ;
- formats autorisés, par exemple `csv, json, geojson` ; une liste vide accepte tous les formats.

## Dépôt GitHub du projet

Dans **Projets & préférences**, renseignez le compte ou l'organisation, le nom du dépôt, sa description et sa visibilité. Enregistrez les paramètres, puis choisissez **Créer le dépôt**. Une confirmation explicite précède toujours l'appel GitHub.

Le champ compte peut rester vide pour utiliser le compte associé à `GITHUB_TOKEN`. Pour une organisation, le jeton doit autoriser la création de dépôts dans cette organisation. HDP initialise le dépôt avec un README GitHub, mais n'y publie ni fichiers locaux, ni ressources, ni scripts du projet.

Le jeton n'est pas un paramètre de projet : il est lu depuis `.env`, masqué dans l'installeur et absent des réponses API et des journaux HDP.

La passerelle REST GitHub complémentaire écoute localement sur
`http://127.0.0.1:8091`. Ses fonctions de lecture sont disponibles lorsque le
service est démarré. La création d'issues et le déclenchement de workflows
restent désactivés tant que `GITHUB_API_WRITE_ENABLED` n'est pas explicitement
défini à `true`. Voir [Passerelle REST GitHub](GITHUB_API.md).

## Géodonnées ONU M49 et HDX

Le module présente quatre familles sous forme de liste :

- **COD-AB**, sélectionnable, pour les limites administratives ;
- **COD-PS**, sélectionnable, pour les statistiques de population infranationales ;
- **COD-CS**, visible mais désactivé tant que le registre vérifié embarqué est vide ;
- **COD-HP**, visible mais désactivé, car cette famille a été retirée par OCHA.

Choisissez ensuite :

- une ou plusieurs familles disponibles ;
- un pays ou une zone dans la liste commune à ONU M49 et aux groupes HDX
  canoniques de toutes ces familles ;
- une politique de qualité COD-AB : amélioré uniquement, ou amélioré avec
  standard officiel en repli ;
- le format géospatial COD-AB : GeoJSON, GeoPackage, Shapefile ou File Geodatabase ;
- un intervalle d'actualisation entre 60 minutes et 30 jours ;
- la synchronisation automatique, ou **Synchroniser maintenant**.

Chaque passage interroge `cod-ab-*` et/ou `cod-ps-*`, exige l'identifiant exact
`<famille>-<iso3>` ou la série officielle correspondante, puis vérifie l'unique
groupe ISO3 contre le pays M49 choisi. COD-AB utilise le format demandé ; COD-PS
retient ses ressources CSV/XLSX. Les codes M49, ISO3, famille, niveau COD publié,
éditeur et licence restent associés aux ressources locales.

Le profil est atomique : si le pays n'est plus admissible dans une famille,
HDP archive les réponses CKAN et le motif, mais ne télécharge pas uniquement les
autres familles. Choisissez une nouvelle option ou retirez explicitement la
famille devenue indisponible.

Après modification des familles, du pays, de la politique ou du format, le dernier état
devient « synchronisation requise ». L'ancienne erreur disparaît ; utilisez
ensuite **Synchroniser maintenant** ou laissez le planificateur exécuter le profil
si le téléchargement automatique est actif.

## Données locales

La rubrique **Données locales** présente les compteurs, la taille totale et chaque ressource.

- **Télécharger** remet le fichier local au navigateur.
- **Vérifier SHA-256** recalcule l'empreinte sans charger tout le fichier en mémoire.
- **Supprimer localement** demande confirmation, efface le fichier et marque la ressource `deleted`. L'acquisition et la ligne de provenance restent en base.

## Scripts

Un script possède un nom, un langage, une description et un contenu. Chaque
création ou modification produit une version immuable avec empreinte SHA-256.
Python est activé par défaut ; R doit être activé dans les paramètres du projet
et démarré avec `start-hdp-with-r.cmd`. SQL, shell et « autre » restent stockés
mais ne sont pas exécutables.

Le bouton **Exécuter** crée un job asynchrone et affiche son état, sa sortie et
son rapport JSON. Le délai est limité à 300 secondes et la sortie à 1 Mio. Le
réseau des runners est toujours désactivé dans cette itération : toute demande
d'activation ou d'allowlist est refusée. Exécutez uniquement du code local de
confiance ; les limites techniques ne constituent pas une sandbox multi-tenant.

## Veille RSS

L'onglet **Veille RSS** propose les flux officiels ReliefWeb « mises à jour »,
« catastrophes », « emplois » et « formations ». Un abonnement appartient au
projet actif, peut contenir une recherche et une langue, puis être lu
immédiatement ou toutes les 15 minutes à 30 jours. HDP borne la réponse à 2 Mio,
refuse les redirections hors du domaine autorisé et déduplique les éléments.

## Chronologie

L'onglet **Chronologie** affiche sous forme de Gantt les acquisitions, passages
de planification, exécutions Python/R et prochains passages du projet. Le
sélecteur permet de couvrir de 1 à 365 jours.

## Carte PostGIS

Une ressource locale GeoJSON complète peut être importée depuis **Données
locales**. L'onglet **Carte** affiche ensuite la couche PostGIS avec Leaflet et
permet de télécharger une archive contenant le GeoJSON, un script QGIS et un
script R. Leaflet est livré localement. Le fond de carte OpenStreetMap est
désactivé par défaut et ne contacte le serveur de tuiles qu'après clic sur
**Activer le fond OSM**.

## Planifications

Une planification enregistre une source, une requête, une limite de résultats, un intervalle et l'option de téléchargement. L'intervalle minimal est de 15 minutes.

- **Exécuter maintenant** attend l'acquisition et affiche son résultat.
- **Suspendre/Réactiver** modifie l'état sans perdre la définition.
- **Archiver** désactive la planification et conserve son historique.

ReliefWeb nécessite toujours un appname valide. Respectez les quotas : un intervalle minimal techniquement accepté peut être inadapté à une requête large, notamment lorsqu'un connecteur filtre localement un catalogue mondial.
