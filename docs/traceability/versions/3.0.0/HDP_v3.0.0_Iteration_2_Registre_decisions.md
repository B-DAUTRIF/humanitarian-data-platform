# HDP 3.0.0 — registre de décisions de l'itération 2

| Décision | Choix retenu |
|---|---|
| Déploiement | Local mono-utilisateur, API liée à `127.0.0.1`, sans authentification/TLS |
| Exécution | Python et R uniquement ; SQL/shell/autre stockés sans exécution |
| Réseau des jobs | Toujours désactivé ; allowlist refusée tant qu'elle n'est pas réellement imposable |
| Isolation | Conteneurs non privilégiés, sans réseau, limites de ressources ; scripts de confiance uniquement |
| R | Facultatif via le profil Compose `analytics` |
| RSS | Quatre flux officiels ReliefWeb seulement, registre vérifié le 15 août 2026 |
| Carte | GeoJSON → PostGIS ; Leaflet 1.9.4 embarqué ; fond OSM opt-in |
| Interopérabilité | Export GeoJSON accompagné de scripts QGIS et R |
| Chronologie | Vue Gantt des acquisitions, planifications et exécutions |
| GitHub | Jeton finement granulé recommandé ; création seulement après confirmation ; aucune publication automatique |
| Compatibilité | 2.5.0 ciblée ; versions plus anciennes non garanties sans fixtures |

Le dépôt doit rester privé tant qu'aucune licence HDP explicite n'a été choisie.
