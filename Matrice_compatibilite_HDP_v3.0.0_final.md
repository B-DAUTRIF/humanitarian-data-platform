# Matrice de compatibilité — Humanitarian Data Platform 3.0.0

| Origine / cible | Garantie | Traitement |
|---|---|---|
| Installation neuve → 3.0.0 | ciblée | création de `.env`, `data/` et du volume stable |
| 2.5.0 → 3.0.0 | **garantie ciblée** | migrations idempotentes, conservation des données et variables inconnues |
| 2.4.x → 3.0.0 | non garantie directement | passer d'abord par 2.5.0 et sauvegarder |
| 2.3.x → 3.0.0 | non garantie directement | passer d'abord par 2.5.0 et sauvegarder |
| 2.0 / 1.5 → 3.0.0 | non garantie directement | reprise contrôlée ou migrations intermédiaires |

## Plateformes

| Élément | Cible finale | Validation présente |
|---|---|---|
| Windows | Windows 10/11 x64 | format PE validé ; recette système à réaliser |
| Docker Desktop | version compatible WSL 2 | configuration statique validée ; moteur absent |
| PostgreSQL/PostGIS | 16 / 3.4 | migration et schéma testés statiquement ; service non démarré |
| Python API | 3.12 | compilation, tests et OpenAPI réussis |
| R/plumber | profil facultatif `analytics` | configuration présente ; service non démarré |
| Navigateurs | moteur moderne sur poste local | HTML/JavaScript analysés, aucun CDN Leaflet |

## Invariants de mise à niveau

- nom de projet Compose `humanitarian-data-platform` conservé ;
- volume `postgres_data` conservé ;
- aucune commande `down -v`, purge ou réinitialisation destructrice ;
- sauvegarde `.env.backup-before-v3.0.0` avant réécriture ;
- variables `.env` inconnues, secrets existants et répertoire `data/` préservés ;
- migrations transactionnelles, idempotentes et enregistrées.
