# Journal des versions

## 2.3.1 — 7 août 2026

- Remplacement de l'échelle opérationnelle « terrain → monde » par la nomenclature
  officielle ONU M49 embarquée et hiérarchisée.
- Suppression de l'identifiant HDX libre dans le module géographique.
- Limitation stricte aux jeux OCHA/HDX de la série officielle
  `COD - Subnational Administrative Boundaries`, marqués `cod-enhanced` ou
  `cod-standard`.
- Ajout des politiques « amélioré uniquement » et « amélioré avec standard en
  repli ».
- Archivage de la provenance : code M49, ISO3, niveau COD, éditeur, licence et
  date des métadonnées.
- Migration sûre : les anciens profils monde deviennent M49 `001`; les profils
  plus étroits sont suspendus jusqu'au choix explicite d'un territoire M49.
- Correction de la limite d'acquisition : les fichiers déjà présents ne
  consomment plus le quota et les ressources restantes sont reportées, pas
  assimilées à des échecs.

## 2.3.0 — 7 août 2026

- Paramètres GitHub par projet et création de dépôt.
- Profil géographique HDX, synchronisation planifiée et téléchargement local.
- Correctif Windows de configuration sûre de `GITHUB_TOKEN`.

Les journaux détaillés historiques restent également inclus dans leurs archives
de remise respectives sous `dist/`.
