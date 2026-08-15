# Limites connues - HDP 4.0.0

- L’aperçu Leaflet importe GeoJSON en SRID 4326. GeoPackage, GeoParquet, KML et
  Shapefile ne sont pas convertis automatiquement.
- Le géocodage CSV/XLSX et les jointures spatiales guidées ne sont pas livrés.
- Le traitement guidé couvre CSV/TSV. Parquet/GeoParquet/Arrow demandent un
  script adapté.
- Les recettes guidées sont synchrones et non annulables depuis l’interface.
- Les sept connecteurs historiques passent du catalogue à une ressource, mais
  toutes les dimensions d’observation ne sont pas encore des champs guidés.
- IOM DTM et WHO DON sont des références non automatisées. WorldPop v2 est une
  API polygonale et n’est pas simulée comme catalogue.
- La planification par fichier utilise un intervalle en minutes ; calendrier,
  fuseaux, ETag, versions physiques et rétention restent à étendre.
- La vue SQL n’exporte pas encore directement CSV/JSON/GeoJSON et n’annule pas
  une requête depuis l’interface.
- Aucun mode multi-utilisateur, exposition réseau ou mise à jour automatique.
- L’installateur Windows 4.0.0 est construit par GitHub Actions sur un runner
  Windows x64. Il n’est ni signé Authenticode ni soumis à une recette manuelle
  sur Windows 10/11 dans cet environnement. L’EXE 3.0.0 historique n’est pas
  présenté comme un installateur 4.0.0.
- La licence doit être choisie par le propriétaire avant publication publique ;
  le dépôt reste privé jusque-là.
