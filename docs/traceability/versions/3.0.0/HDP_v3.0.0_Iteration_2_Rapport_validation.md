# HDP 3.0.0 — rapport de validation de l'itération 2

Validation exécutée le 15 août 2026 dans l'environnement de construction Linux.

## Résultat

| Contrôle | Résultat |
|---|---|
| Tests Python | 64/64 réussis |
| Compilation Python | `compileall` réussi |
| JavaScript inline | 1 bloc analysé avec succès par Node.js |
| Contrat OpenAPI | 47 chemins, 63 opérations |
| Docker Compose | YAML valide ; 5 services ; runners Python/R sans réseau |
| Runner C | GCC C17, `-Wall -Wextra -Werror`, réussi |
| Runner fonctionnel | job Python réussi ; boucle infinie arrêtée avec `timed_out` |
| Ressources web locales | page et Leaflet 1.9.4 servis localement, HTTP 200 |
| Payload natif | 41 fichiers restitués octet pour octet |
| Installateur | PE32+ GUI x86-64, Windows 6.0+, ASLR/NX/High Entropy VA |

## Installateur généré

- Fichier : `HumanitarianDataPlatform_Setup_Native_GUI_v3.0.0.exe`
- Taille : 3 595 264 octets
- SHA-256 : `d1da72a9b1f3697805866de3c72b4f1be57b049607c28544f1c58049519bcc8c`
- Payload : 41 fichiers

## Couverture ajoutée

- validation des langages et rejet de toute politique réseau activable ;
- spool atomique, statut récupérable et rapport d'exécution ;
- registre RSS ReliefWeb, requêtes bornées, RSS/Atom et refus DTD/entités ;
- GeoJSON borné et archive d'export QGIS/R ;
- propriétés de sécurité Compose et absence de shell dans le runner ;
- construction/démarrage des runners par l'installateur natif ;
- présence des routes, vues et ressources Leaflet locales de l'itération 2.

## Limites de recette

Docker n'est pas installé dans l'environnement de validation. Les migrations
sur une instance PostgreSQL/PostGIS réelle, la construction des images et le
parcours navigateur avec données réelles n'ont donc pas été exécutés ici.
L'installateur est réellement compilé, mais n'a pas été lancé sous Windows
10/11 avec Docker Desktop. Ces deux recettes restent obligatoires avant une
qualification finale de production.

Les appels réels aux sources distantes et à GitHub n'ont pas été déclenchés.
Aucun dépôt GitHub n'a été créé ou publié.
