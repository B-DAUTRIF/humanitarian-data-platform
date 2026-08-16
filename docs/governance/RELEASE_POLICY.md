# Politique de branches et de publication HDP

## `main`

`main` représente la dernière livraison installable qualifiée. Son fichier `VERSION`, son README, les sources, la documentation de version et les livrables de `dist/<version>/` doivent être cohérents.

Au 16 août 2026, `main` correspond à **5.0.2**.

## Développement

Une évolution non qualifiée utilise `develop/<version>` ou une branche fonctionnelle dérivée. La ligne **5.2** est conservée sur `develop/5.2` à partir du commit `d0257a402a958439f6f28e6b3de2290112bfbbfc`.

## Qualification minimale

- tests et contrôles annoncés réellement exécutés ;
- build Windows et archive complète accompagnés de SHA-256 ;
- migrations et préservation de `.env`, `data/` et PostgreSQL documentées ;
- documentation, UML, changelog, prompt et manifeste cohérents ;
- absence de secrets ;
- limites externes explicites ;
- publication par descendant du `main` observé, sans force-push ;
- relecture distante et contrôle des workflows après publication.

Une branche de travail ne devient `main` qu’après satisfaction des critères de livraison. Les numéros d’artefacts existants ne sont jamais renommés pour simuler une nouvelle qualification.
