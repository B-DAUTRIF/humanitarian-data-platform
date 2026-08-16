# Traçabilité HDP

- `versions/<version>/` : décisions, matrices, rapports de validation et points de reprise ;
- `logs/<date>/` : journaux de développement datés ;
- `work/<version>/` : état complet d’une ligne de travail séparée de `main`.

Les fichiers sont conservés dans Git et ne doivent pas être réécrits après archivage. Une correction crée une nouvelle version ou un nouveau document daté.

Lorsqu’une décision, un rapport ou un journal est déjà présent à l’identique dans `dist/<version>/`, la distribution reste la copie canonique et aucun doublon n’est créé dans ce dossier.
