# Guide général HDP V5

## Parcours fonctionnel

1. Créer ou sélectionner un projet.
2. Configurer les sources et le périmètre ONU M49.
3. Ouvrir **Data Grid & SIGNALS** pour rechercher les métadonnées HDX ou créer une règle de surveillance.
4. Examiner la description individuelle de chaque jeu et fichier : structure, format, dates, localisation, périodicité, échéance attendue et fiabilité technique.
5. Générer un plan d’agrégation ; lever tous les contrôles bloquants avant d’exécuter une recette.
6. Traiter un CSV/TSV par une recette reproductible ou créer un notebook Jupyter-compatible.
7. Vérifier la lignée, les rapports, les empreintes et les résultats SQL en lecture seule.

## Data Grid et métadonnées

La grille fonctionnelle HDP sert à formuler le besoin et mesurer la couverture. HDP ne prétend jamais qu’un jeu appartient officiellement à une catégorie sans métadonnée explicite publiée par HDX. Les inférences locales portent la mention `hdp_candidate`.

La recherche combine texte, localisation, période, formats et dimensions. Une fiche est conservée pour le jeu et pour chaque fichier. La fiabilité est un indicateur transparent de complétude/fraîcheur ; elle ne remplace pas l’évaluation du producteur, de la méthodologie ou de la licence.

L’agrégation commence par un contrat : granularité géographique, pas de temps, valeurs manquantes, unités, licences et provenance. HDP refuse de présenter un assemblage comme prêt tant que les mappings nécessaires sont absents.

## SIGNALS

Une règle comporte des zones, thèmes, seuils de gravité/confiance, une fenêtre temporelle et les dimensions Data Grid attendues. Un événement est dédupliqué par projet, source et identifiant externe. Une correspondance déclenche une recherche HDX et peut avancer la planification des ressources uniquement si leur `expected_update_at` est atteint.

Le snapshot syndromique agrège le nombre de signaux et la somme `gravité × confiance`, tout en conservant la liste des preuves. Il est non diagnostique et doit être interprété par une personne compétente.

Les patrons de prompts appliquent quatre principes : rester dans les preuves fournies, conserver les contradictions, expliciter l’incertitude et retourner une structure vérifiable. Aucun script n’est exécuté automatiquement sur le seul surgissement d’un signal.

## Notebook Jupyter-compatible

Un notebook respecte `nbformat 4.5`, possède un noyau `python3` ou `ir` et des révisions immuables SHA-256. Avant exécution, le navigateur calcule l’empreinte de la cellule et l’utilisateur confirme le code exact. Le runner exécute sans réseau, sous une identité de job distincte, avec limites de temps, sortie, fichiers et processus.

## Liens extérieurs

La page **USER · Technologies & code** présente les liens officiels dans des panneaux repliables afin de rester détaillée sans alourdir la navigation principale. Elle regroupe documentation HDP, GitHub/Wiki, nomenclatures et logiciels tiers.
