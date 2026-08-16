# Point de reprise — HDP 3.0.0 itération 2

Date : 15 août 2026.

## État livré

- exécution Python/R versionnée, asynchrone, bornée et sans réseau ;
- veille RSS ReliefWeb officielle par projet ;
- chronologie Gantt ;
- import GeoJSON PostGIS, Leaflet local et exports QGIS/R ;
- politique GitHub à droits minimaux ;
- installateur Windows natif reconstruit avec 41 fichiers de payload ;
- 64 tests réussis, OpenAPI à 47 chemins et 63 opérations.

## Prochaines actions recommandées

1. Exécuter la recette Docker sur une base PostgreSQL/PostGIS neuve.
2. Rejouer la mise à niveau à partir d'une sauvegarde 2.5.0 représentative.
3. Tester l'EXE sous Windows 10 et 11 x64 avec Docker Desktop.
4. Vérifier le parcours navigateur complet : Python, R optionnel, RSS, Gantt,
   import GeoJSON, carte sans/avec tuiles et export QGIS/R.
5. Effectuer un audit de sécurité ciblé avant d'accepter du code non maîtrisé.

Ne pas publier sur GitHub sans une nouvelle autorisation explicite et sans
avoir choisi une licence pour HDP.
