# Guide utilisateur 2.0

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

## Données locales

La rubrique **Données locales** présente les compteurs, la taille totale et chaque ressource.

- **Télécharger** remet le fichier local au navigateur.
- **Vérifier SHA-256** recalcule l'empreinte sans charger tout le fichier en mémoire.
- **Supprimer localement** demande confirmation, efface le fichier et marque la ressource `deleted`. L'acquisition et la ligne de provenance restent en base.

## Scripts

Un script possède un nom, un langage, une description et un contenu. Il peut être créé, modifié ou archivé dans son projet. HDP 2.0 n'exécute aucun script : n'utilisez pas cette bibliothèque comme moteur de traitement.

## Planifications

Une planification enregistre une source, une requête, une limite de résultats, un intervalle et l'option de téléchargement. L'intervalle minimal est de 15 minutes.

- **Exécuter maintenant** attend l'acquisition et affiche son résultat.
- **Suspendre/Réactiver** modifie l'état sans perdre la définition.
- **Archiver** désactive la planification et conserve son historique.

ReliefWeb nécessite toujours un appname valide. Respectez les quotas : un intervalle minimal techniquement accepté peut être inadapté à une requête large.
