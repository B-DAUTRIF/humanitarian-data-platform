# Guide utilisateur - Humanitarian Data Platform 4.1.0

HDP est une application locale pour rechercher, télécharger, organiser,
vérifier, traiter et cartographier des données humanitaires et sanitaires. Elle
reste liée à `127.0.0.1` et ne doit pas être exposée directement à Internet.

## Nouveau parcours centré sur la source

1. Ouvrir **Paramètres des sources** et sélectionner un connecteur.
2. Régler son délai, ses reprises, sa limite de réponse, son identifiant HTTP et
   sa langue, indépendamment des neuf autres connecteurs.
3. Lire la fiche technique : protocole, formats, authentification, fraîcheur,
   conditions d'utilisation, outils Python/R et liens officiels.
4. Sélectionner le projet et renseigner les dimensions propres à la source.
5. Prévisualiser la requête et reprendre, si nécessaire, l'exemple cURL,
   Python `httpx` ou R `httr2`.
6. Enregistrer puis lancer une recherche ou une planification.

Les identifiants ReliefWeb et HAPI doivent être placés dans `.env`. L'interface
n'en affiche que l'état configuré/absent.

## Technologies et code

Le menu **USER - Technologies & code** regroupe les 25 technologies et
ressources du projet, 87 liens officiels et les accès directs au code :

- [dossier Drive HDP 4.1.0](https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0) ;
- [dépôt GitHub privé](https://github.com/B-DAUTRIF/humanitarian-data-platform) ;
- documentation FastAPI locale `/docs` et OpenAPI `/openapi.json`.

La page distingue les composants utilisés, les logiciels conseillés et les
standards de référence. Aucun script tiers n'est chargé depuis cette page.

## Travail par projet

Après configuration, créer ou sélectionner un projet, lancer une recherche
fédérée, puis enregistrer ou importer les ressources. Les fichiers sont écrits
atomiquement, contrôlés par type et empreinte SHA-256. Les recettes CSV/TSV
génèrent un résultat dérivé, un rapport et un script Python ou R. Les couches
GeoJSON vérifiées peuvent être importées dans PostGIS et affichées avec Leaflet.

Le module SQL n'autorise que la lecture bornée des vues `hdp_*` du projet. Les
scripts Python/R restent du code local de confiance malgré l'isolation des
runners ; les vérifier avant exécution.

## Sauvegarde et mise à niveau

Exécuter `backup-hdp.ps1` avant une mise à niveau. La restauration exige la
confirmation `RESTORE-HDP`, crée une sauvegarde de sécurité et conserve les
anciens `.env` et `data/`. HDP 4.1.0 accepte les sauvegardes 4.0.0 et 4.1.0.
Ne jamais utiliser `docker compose down -v` si le volume PostgreSQL doit être
conservé.

## Limite de responsabilité

Les quotas, licences et conditions de chaque producteur restent applicables.
GDACS est utilisé à des fins d'analyse et ne remplace pas un canal officiel
d'alerte. HDP ne valide pas une décision clinique, épidémiologique ou
opérationnelle.
