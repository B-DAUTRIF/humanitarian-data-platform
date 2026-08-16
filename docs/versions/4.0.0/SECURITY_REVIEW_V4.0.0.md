# Revue de sécurité interne - HDP 4.0.0

Date : 15 août 2026. Cette revue est une auto-évaluation technique, pas un audit
indépendant ni une certification.

## Contrôles vérifiés

- services HTTP publiés uniquement sur `127.0.0.1` ; PostgreSQL non publié ;
- runners Python/R sans réseau, non privilégiés, en lecture seule, capacités
  supprimées, limites CPU/mémoire/PID/temps/sortie ;
- URL de téléchargement limitées à HTTP(S), sans identifiants et vers des
  adresses IP publiques ;
- noms et chemins confinés sous `DATA_DIR`, SHA-256 et écriture atomique ;
- validation extension + signature/structure, archives sans extraction, liens,
  macros et exécutables refusés ;
- HAPI et ReliefWeb injectent leurs identifiants côté serveur ;
- SQL sur vues de projet, fonctions/relations autorisées, transaction
  `READ ONLY`, délai et limite de lignes, audit par empreinte ;
- carte : SHA-256 contrôlé, GeoJSON borné et propriétés par DOM sûr ;
- sauvegarde de `.env`, variables inconnues préservées et aucune commande
  `docker compose down -v`.

## Risques résiduels

- modèle local mono-utilisateur, sans authentification ni TLS ;
- scripts considérés comme code local de confiance malgré l’isolation ;
- dépendance aux schémas, quotas, licences et disponibilités externes ;
- absence d’antivirus embarqué ; documents stockés mais non rendus ;
- validation SQL défensive sans rôle PostgreSQL applicatif séparé ;
- traitements guidés synchrones pouvant occuper un worker près des limites ;
- audit indépendant, test d’intrusion et recette Windows non réalisés ici.

## Rotation des secrets

Arrêtez l’application, sauvegardez `.env`, remplacez individuellement
`POSTGRES_PASSWORD`, `RELIEFWEB_APPNAME`, `HDX_HAPI_APP_IDENTIFIER` ou
`GITHUB_TOKEN`, recréez les services concernés et contrôlez leur santé. La
rotation PostgreSQL exige de synchroniser le rôle et `DATABASE_URL`. Ne placez
jamais `.env`, une URL signée ou un jeton dans GitHub ou une archive publique.

