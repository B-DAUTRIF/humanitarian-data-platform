# Humanitarian Data Platform — V6.0.0

La branche `main` porte désormais la **V6.0.0 qualifiée par CI Windows** de HDP.

## Télécharger la V6

Le build Windows qualifié est produit par le workflow **HDP V6 full Windows installer**. Le run de référence final pour la V6.0.0 est le run GitHub Actions `33296150213`, associé au commit `f60effc443efa539f32ff48d0b60c8e2c4d65002` et conclu avec succès.

- Artefact GitHub Actions : `HumanitarianDataPlatform-V6-complet`
- Installateur contenu dans l’artefact : `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0.exe`
- SHA-256 de l’EXE : `18c8eaaa40608d23d3f00d06b666f2be47f7817d749906115c8ec7b414e0e256`
- Archive complète : `HumanitarianDataPlatform_Archive_complete_v6.0.0.zip`
- SHA-256 de l’archive complète : `597dde200a02b3e954aba696e5c95adb20c7acb92897eff20ae769048e92818c`

Accès au run : https://github.com/B-DAUTRIF/humanitarian-data-platform/actions/runs/33296150213

> L’installateur est un exécutable Windows GUI x86-64 (PE32+) construit sur `windows-2025` avec MSVC. Il n’est pas signé Authenticode : Windows peut donc afficher une confirmation de sécurité.

## Inventaire exhaustif des paramètres API

La V6 embarque un inventaire canonique contrôlé par CI :

- **2 057 paramètres** ;
- **10 sources** ;
- **440 opérations API** cataloguées.

L’inventaire est exposé directement dans l’application :

- interface utilisateur : `/api-inventory` ;
- données filtrables : `/api-inventory/data` ;
- liste et statistiques des sources : `/api-inventory/sources` ;
- schéma détaillé d’une source : `/api-inventory/source/{slug}`.

L’interface permet la recherche textuelle, le filtrage par source et expose notamment la source, l’opération, la méthode HTTP, l’endpoint, le paramètre, son emplacement, son type, son caractère obligatoire, le contrôle UI recommandé, la classe d’accès et sa description. Les paramètres en lecture seule restent visibles comme information.

Le workflow Windows bloque la publication si l’inventaire n’atteint pas exactement les seuils canoniques ci-dessus ou si le routeur d’inventaire n’est pas monté dans `main_v6.py`.

## Architecture V6

Le backend V6 conserve l’application historique et monte les modules V6 sans dupliquer le cœur : synchronisation GitHub et inventaire API. Le Dockerfile démarre `app.main_v6:app`. La livraison complète contient également les clients R V6, les sources de l’installateur, le payload Docker, la documentation et les fichiers de traçabilité.

## Versions précédentes

Les distributions antérieures restent archivées sous `dist/` et `docs/versions/`. La V5.0.2 demeure disponible pour retour arrière, mais **n’est plus la version courante de `main`**.

## Installation

Sous Windows 10/11 x64 : télécharger l’artefact du run qualifié, extraire `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0.exe`, vérifier son SHA-256, puis lancer l’installateur. Docker Desktop et Compose v2 restent nécessaires au fonctionnement complet de la pile.
