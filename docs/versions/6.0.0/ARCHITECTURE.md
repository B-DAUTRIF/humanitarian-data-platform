# HDP V6.0.0 — Architecture et documentation fonctionnelle

## Objet

HDP est une application locale client–serveur pour rechercher, télécharger, organiser et traiter des données humanitaires, sanitaires et épidémiologiques. La V6 consolide les fonctions accumulées par les versions antérieures et impose que le numéro 6.0.0 soit porté nativement par les sources, l'installateur, le backend et l'interface.

## Architecture

- Installateur Windows natif x86-64: `source/src/installer.c`, ressources `installer.rc`, build MSVC via `source/build-windows.ps1`.
- Orchestration locale: Docker Compose, PostgreSQL/PostGIS, API FastAPI, runner Python, services R/plumber et runner R optionnels.
- Backend: `source/payload/api/app/`.
- Interface principale: `source/payload/api/static/index.html`.
- Point d'entrée V6: `app.main_v6:app`, qui conserve le cœur historique et monte les modules V6.
- Inventaire API: `api_inventory.py` + catalogue compressé `api_inventory_parts/`.
- Client R V6: `clients-v6/R/`.

## Fonctions utilisateur

L'interface principale expose Recherche, Data Grid & SIGNALS, Sources sanitaires, Paramètres des sources, Inventaire API, Projets & préférences, Données locales, Flux RSS, Chronologie, Carte, Scripts, Notebooks, Planifications, Base SQL et USER · Technologies & code.

## Inventaire des API

L'onglet **Inventaire API** est la vue de référence pour l'exposition de tous les paramètres connus de chaque source. La vue dédiée `/api-inventory` fournit recherche textuelle et filtre par source. Les endpoints `/api-inventory/data`, `/api-inventory/sources` et `/api-inventory/source/{slug}` permettent aussi une exploitation programmatique.

Les paramètres sont distingués entre paramètres modifiables et informations en lecture seule. Une information en lecture seule doit rester visible à l'utilisateur, conformément à la règle d'exhaustivité de l'interface.

## Qualification

La livraison V6 ne doit être déclarée installable que si :

1. aucune substitution temporaire de 5.0.2 vers 6.0.0 n'est nécessaire au build ;
2. l'inventaire comporte exactement 2 057 paramètres, 10 sources et 440 opérations ;
3. l'onglet Inventaire API est présent dans l'interface principale ;
4. le backend démarre sur `app.main_v6:app` ;
5. l'EXE est un PE Windows GUI x86-64 portant la version 6.0.0 ;
6. les tests automatisés sont verts ;
7. les livrables et leurs SHA-256 sont publiés.
