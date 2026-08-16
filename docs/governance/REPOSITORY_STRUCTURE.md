# Structure canonique du dépôt HDP

## Principe

La branche `main` contient uniquement la dernière livraison installable qualifiée, sa source courante, sa documentation, les index actifs et les archives historiques classées. Une version de travail non qualifiée utilise une branche dédiée.

## Arborescence

```text
README.md                         entrée utilisateur de la livraison courante
VERSION                           version installable qualifiée de main
CHANGELOG.md                      historique chronologique
TODO_Mises_a_jour_HDP.md          actions actives uniquement
HDP_STATE.json                    état machine lisible de main et de la ligne de travail
source/                           source nécessaire à la livraison courante
dist/<version>/                   distributions immuables et preuves associées
docs/versions/<version>/          documentation technique versionnée
docs/traceability/                décisions, états, journaux et reprises archivés
docs/governance/                  règles, structure et audits du dépôt
wiki/                             source du Wiki versionné
```

## Règles anti-doublons

1. Un binaire ou script historique déjà présent dans `dist/<version>/` n’est pas conservé une seconde fois à la racine ou dans `source/`.
2. Les distributions restent immuables, même lorsqu’elles contiennent leur propre copie documentaire ou source.
3. Une documentation lisible hors archive est classée une seule fois dans `docs/versions/<version>/`.
4. Les fichiers actifs non versionnés restent limités à `README.md`, `VERSION`, `CHANGELOG.md`, `TODO_Mises_a_jour_HDP.md` et `HDP_STATE.json`.
5. Un déplacement Git ne supprime pas l’historique : tout ancien chemin reste récupérable dans les commits précédents.
6. Aucun force-push n’est autorisé pour une opération d’organisation.

## Cycle de mise à jour

Avant chaque publication : vérifier le parent de `main`, exécuter les validations applicables, produire les empreintes, mettre à jour la documentation de version, archiver les états remplacés, publier par commit descendant et relire le commit distant.
