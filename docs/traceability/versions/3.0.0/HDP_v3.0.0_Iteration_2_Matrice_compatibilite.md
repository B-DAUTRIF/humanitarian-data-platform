# HDP 3.0.0 — matrice de compatibilité de l'itération 2

| Origine | État | Portée |
|---|---|---|
| Installation neuve 3.0.0 | Contrats validés | Sources, migrations idempotentes, payload et installateur compilés ; recette Windows/Docker à faire |
| 3.0.0 itération 1 | Compatible | Ajout non destructif des migrations `002` à `004`, création de la version 1 des scripts existants |
| 2.5.0 | Garantie structurelle | `.env`, `data/`, volume PostgreSQL et acquisitions conservés par le chemin ciblé ; recette réelle Windows/Docker à faire |
| 2.4.x | Chemin historique conservé | Qualification finale exige une sauvegarde ou fixture représentative |
| 2.3.x | Chemin historique conservé | Profils monde/région suspendus jusqu'au choix M49 explicite |
| 2.0 / 1.5 | Chemin historique conservé | Non déclaré garanti sans fixtures représentatives |
| Retour vers une version antérieure | Non pris en charge | Restaurer ensemble PostgreSQL, `.env` et `data/` depuis une sauvegarde cohérente |

Les migrations de l'itération 2 ajoutent uniquement des tables, colonnes et
index. Elles ne contiennent ni `DROP`, ni `TRUNCATE`, ni suppression de volume.
