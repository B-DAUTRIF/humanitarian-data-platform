# Revue de sécurité interne - HDP 4.1.0

## Protections vérifiées

- écoute locale sur `127.0.0.1` et services Compose non publiés ;
- liste blanche d'hôtes HTTPS par connecteur ;
- délais de connexion et de réponse bornés par source ;
- lecture en flux et taille de réponse maximale avant décodage JSON ;
- propriétés de configuration inconnues ou hors limite refusées ;
- secrets stockés dans `.env`, jamais renvoyés dans les schémas, exemples ou
  prévisualisations ;
- liens du catalogue limités à HTTPS ou aux routes locales ;
- runners Python/R sans réseau, sans privilège et sans invocation de shell ;
- import atomique, signatures de fichiers, SHA-256 et archives contrôlées ;
- requêtes SQL limitées aux vues de lecture du projet.

## Modèle d'exploitation

HDP est une application locale mono-utilisateur et non un serveur Internet
durci. Les scripts restent du code local de confiance et doivent être relus.
Les fichiers `.env`, `data/`, sauvegardes, URL signées et jetons ne doivent pas
être placés dans GitHub ou un dossier Drive partagé au-delà des personnes
autorisées.

## Points externes

La signature Authenticode, la recette Windows réelle, les tests d'intrusion et
la revue de la politique d'accès au dossier Drive nécessitent une intervention
hors de la chaîne de tests locale.
