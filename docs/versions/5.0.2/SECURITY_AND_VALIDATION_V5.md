# Sécurité et validation - HDP V5

## P0 résolus dans le round V5

- SQL : les littéraux ne sont plus altérés ; l’analyse AST bloque les fonctions citées ou non citées hors liste positive ; exécution par `hdp_reader`.
- API locale : contrôle Host, session locale, origine et CSRF ; la recherche avec effet de bord est uniquement POST.
- SSRF : résolution publique, connexion épinglée, vérification du pair et revalidation des redirections.
- Runners : dossiers non publics, paramètres en fichiers réguliers, UID de job, groupe de processus, limites globales de sortie et purge.
- Sauvegarde/restauration : aucune sauvegarde de secrets, empreinte externe obligatoire, manifeste et entrées contrôlés avant extraction.
- Rafraîchissement : une nouvelle acquisition crée une nouvelle version de ressource au lieu de réutiliser silencieusement le fichier terminé.
- Architecture : suppression du service GitHub déployé en doublon ; API non-root, système de fichiers en lecture seule et limites Compose.

## Validation reproductible

- compilation C avec `-Wall -Wextra -Werror` ;
- tests unitaires et contrats Python ;
- analyse de syntaxe Python et JavaScript inline ;
- validation statique des routes V5 et régressions SQL ;
- build Windows réalisé dans GitHub Actions sur un runner Windows ;
- archives et exécutables accompagnés de SHA-256.

## Réserves

L’environnement courant ne remplace pas un test Windows réel, une signature Authenticode, un test de charge ou un test d’intrusion indépendant. Les signaux et agrégations nécessitent une validation métier humaine.
