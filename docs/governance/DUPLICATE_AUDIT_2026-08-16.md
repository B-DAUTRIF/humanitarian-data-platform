# Audit des doublons — 16 août 2026

## État initial

- 297 fichiers Git ;
- 17 972 262 octets référencés dans l’arborescence ;
- 34 groupes de blobs identiques, représentant 68 chemins ;
- principaux doublons : anciens EXE et scripts présents à la fois dans `source/` et `dist/`, documentation présente à la racine ou dans `docs/` et dans une distribution historique.

## Traitement

- conservation intégrale de `dist/` comme archive de distributions immuables ;
- retrait des copies historiques de `source/` lorsqu’un blob identique existe déjà dans `dist/` ;
- suppression des prompts racine déjà présents à l’identique dans `dist/` ;
- déplacement des documents techniques vers `docs/versions/<version>/` ;
- déplacement des décisions, rapports, points de reprise et journaux vers `docs/traceability/` ;
- séparation de la todo-list active et de son état complet archivé ;
- conservation de 5.2 sur `develop/5.2` et réalignement de `main` sur 5.0.2.

## Doublons intentionnels

Une distribution peut contenir une copie figée de ses sources ou documents tandis qu’une version lisible reste indexée dans `docs/versions/`. Git stocke les blobs identiques une seule fois par SHA ; ces occurrences ont des rôles différents et ne constituent pas un gaspillage de stockage Git.

Après application de la réorganisation simulée :

- 280 fichiers référencés ;
- 0 groupe de blobs dupliqués ;
- 19 903 205 octets référencés ;
- 52 déplacements, 34 suppressions et 22 ajouts ou remplacements.

Toute future copie hors de `dist/` doit être justifiée dans ce document ou supprimée.
