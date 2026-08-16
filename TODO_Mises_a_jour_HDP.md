# Todo-list active — Humanitarian Data Platform

Dernière mise à jour : 16 août 2026
Branche de livraison : `main`
Dernière livraison installable qualifiée : **5.0.2** — commit source `cfb42bbb9813f108a5087ad443c2a2d3fa561a06`
Branche de travail : [`develop/5.2`](https://github.com/B-DAUTRIF/humanitarian-data-platform/tree/develop/5.2) — état initial `d0257a402a958439f6f28e6b3de2290112bfbbfc`

## Dépôt et traçabilité

- [x] placer la livraison qualifiée 5.0.2 sur `main` ;
- [x] conserver la ligne de travail 5.2 sur une branche distincte ;
- [x] classer la documentation technique par version ;
- [x] archiver les états, décisions, journaux et anciennes todo-lists ;
- [x] retirer de `source/` et de la racine les copies historiques déjà conservées dans `dist/` ;
- [x] intégrer sur `main` l’EXE et l’archive complète issus du workflow Windows 5.0.2 ;
- [ ] créer une release et un tag GitHub `v5.0.2` lorsque le flux de publication des releases est disponible ;
- [ ] choisir une licence HDP avant tout passage du dépôt en public.

## Qualification 5.0.2 encore externe

- [ ] confirmer manuellement l’installation et une mutation depuis l’interface sur Windows 10/11 avec Docker Desktop ;
- [ ] signer l’EXE avec Authenticode si un certificat éditeur est fourni ;
- [ ] réaliser un test de charge, un test d’intrusion indépendant et une revue métier santé publique ;
- [ ] synchroniser, si nécessaire, le dossier `wiki/` vers le Wiki GitHub séparé.

## Prochaine mission 5.2 proposée

- [ ] exposer les identifiants internes de métadonnées requis par les plans d’agrégation ;
- [ ] rendre les actions SIGNALS idempotentes et appliquer réellement `lookback_hours` ;
- [ ] corriger la sémantique de disponibilité des agrégations ;
- [ ] ajouter les tests d’intégration de bout en bout ;
- [ ] réconcilier README, API, UML, Wiki et todo-list avec les preuves obtenues ;
- [ ] conserver la confirmation explicite avant toute exécution Python ou R.

La todo-list complète antérieure est archivée sous [`docs/traceability/work/5.2/TODO_before_main_alignment.md`](docs/traceability/work/5.2/TODO_before_main_alignment.md).
