# HDP V7 — traçage diagnostic utilisateur

## Objectif

Le module `app.v7_trace` produit un journal JSON Lines corrélé destiné aux recettes Windows et au diagnostic reproductible. Il ne transforme jamais une erreur fournisseur en résultat vide valide.

## Événements enregistrés

- démarrage runtime et migrations ;
- début/fin/exception de chaque requête HTTP reçue par HDP ;
- méthode, chemin, paramètres de requête, statut HTTP, durée, type/longueur de réponse ;
- début/fin/exception de chaque exécution sémantique fournisseur ;
- source, opération, critères, paramètres canoniques, paramètres natifs, géographie canonique, état projet ;
- requête native retournée par le service fournisseur, HTTP status lorsqu'il est disponible, nombre de résultats et durée ;
- type et message d'exception lorsqu'une exécution échoue.

Chaque requête reçoit un `trace_id` propagé dans l'en-tête de réponse `X-HDP-Trace-ID`, ce qui permet de relier interface, routeur et fournisseur.

## Protection des secrets

Avant écriture, le logger masque les champs dont le nom indique un secret : token, password, cookie, authorization, app_identifier, appname, api key, CSRF ou credential. Les paramètres sensibles présents dans une URL sont également remplacés par `***REDACTED***`. Les valeurs et collections excessivement longues sont tronquées.

Les corps complets de réponses fournisseur ne sont pas inscrits dans le log diagnostic. La provenance native et le type du payload sont conservés, ce qui limite le risque de recopier des données personnelles ou des volumes importants.

## Emplacement

Dans l'installation Docker standard :

`<HDP>/source/payload/data/logs/trace/HDP_TRACE_YYYYMMDD.jsonl`

Le chemin interne du conteneur est `/app/data/logs/trace/`. Il est persistant car `/app/data` est monté sur le répertoire `source/payload/data` de l'installation.

## Export utilisateur

Dans HDP :

- `GET /api/trace/status` : état et taille du journal courant ;
- `GET /api/trace/export` : téléchargement du journal JSONL courant ;
- un lien **Exporter log diagnostic** est ajouté au bandeau de l'interface V7.

Pour un retour de recette, transmettre le fichier `HDP_TRACE_YYYYMMDD.jsonl` produit immédiatement après avoir reproduit le problème. Le `trace_id` visible dans les réponses permet de cibler une exécution précise.

## Limites

Ce module capture les opérations transitant par le runtime API HDP et les exécutions fournisseurs du routeur sémantique. Les journaux propres à Docker, PostgreSQL, au runner Python/R et à Windows restent des flux distincts ; ils peuvent être joints en complément lors d'un incident d'installation ou d'infrastructure.
