# Guide utilisateur 2.3

## Projet actif

Le sélecteur en haut de l'interface détermine le projet actif. Toutes les recherches, ressources, préférences, scripts et planifications affichés appartiennent à ce projet.

Créez un projet dans **Projets & préférences**, puis décrivez son objectif. Le « Projet par défaut » accueille les acquisitions anciennes et ne peut pas être archivé.

## Recherche et téléchargement automatique

Dans **Recherche** :

1. choisissez HDX/CKAN ou ReliefWeb ;
2. saisissez les mots-clés et le nombre maximal de résultats ;
3. activez, si besoin, le téléchargement automatique ;
4. lancez l'acquisition.

La réponse JSON est toujours archivée avec son empreinte. Si le téléchargement est actif, les ressources présentes dans les métadonnées sont traitées dans l'ordre, jusqu'à la limite du projet. Un fichier trop grand, un format exclu ou une destination réseau privée est ignoré ou signalé en erreur sans annuler la provenance de l'acquisition.

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

## Jeu géographique HDX

Le profil par défaut vise `cod-ab-global`, le jeu global de limites administratives communes COD-AB publié sur HDX. Choisissez :

- un format : GeoJSON, GeoPackage, Shapefile ou File Geodatabase ;
- une portée maximale : terrain, local, national, régional ou monde ;
- un intervalle d'actualisation entre 60 minutes et 30 jours ;
- la synchronisation automatique, ou **Synchroniser maintenant**.

Chaque passage archive la réponse `package_show` de HDX, le profil choisi et son empreinte SHA-256. Les ressources au format préféré sont ensuite téléchargées avec les garde-fous du projet. L'échelle est une classification opérationnelle HDP : elle n'altère pas et ne complète pas la couverture géographique réellement publiée par HDX.

## Données locales

La rubrique **Données locales** présente les compteurs, la taille totale et chaque ressource.

- **Télécharger** remet le fichier local au navigateur.
- **Vérifier SHA-256** recalcule l'empreinte sans charger tout le fichier en mémoire.
- **Supprimer localement** demande confirmation, efface le fichier et marque la ressource `deleted`. L'acquisition et la ligne de provenance restent en base.

## Scripts

Un script possède un nom, un langage, une description et un contenu. Il peut être créé, modifié ou archivé dans son projet. HDP 2.3 n'exécute aucun script : n'utilisez pas cette bibliothèque comme moteur de traitement.

## Planifications

Une planification enregistre une source, une requête, une limite de résultats, un intervalle et l'option de téléchargement. L'intervalle minimal est de 15 minutes.

- **Exécuter maintenant** attend l'acquisition et affiche son résultat.
- **Suspendre/Réactiver** modifie l'état sans perdre la définition.
- **Archiver** désactive la planification et conserve son historique.

ReliefWeb nécessite toujours un appname valide. Respectez les quotas : un intervalle minimal techniquement accepté peut être inadapté à une requête large.
