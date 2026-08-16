# Humanitarian Data Platform — livraison qualifiée 5.0.2

La branche `main` représente la **dernière livraison installable qualifiée** de HDP. La version publiée ici est **5.0.2**.

La ligne de travail **5.2** est conservée séparément sur [`develop/5.2`](https://github.com/B-DAUTRIF/humanitarian-data-platform/tree/develop/5.2). Elle ne doit pas être confondue avec une livraison installable.

## Télécharger la livraison qualifiée

| Livrable | SHA-256 |
|---|---|
| [Installateur Windows x64 5.0.2](dist/v5.0.2/HumanitarianDataPlatform_Setup_Native_GUI_v5.0.2.exe) | `0077049d4ec410a0594fa2743b0d6149c7b2c3ae4b08859bce1c219b9fe2814a` |
| [Archive complète 5.0.2](dist/v5.0.2/HumanitarianDataPlatform_Archive_complete_v5.0.2.zip) | `89e27edd1f5bdbf75bad70a66495843a8d777e3c73957cec534b56119d4345dc` |

Les fichiers `.sha256` correspondants se trouvent dans le même dossier. La provenance et les limites de qualification sont consignées dans [`dist/v5.0.2/PROVENANCE.json`](dist/v5.0.2/PROVENANCE.json) et [`docs/versions/5.0.2/QUALIFICATION.md`](docs/versions/5.0.2/QUALIFICATION.md).

## Organisation du dépôt

- `source/` : source courante nécessaire à la livraison 5.0.2 ;
- `dist/` : distributions immuables classées par version ;
- `docs/versions/` : documentation technique classée par version ;
- `docs/traceability/` : décisions, états, journaux et points de reprise archivés ;
- `docs/governance/` : règles de publication, structure et audits du dépôt ;
- `wiki/` : sources du Wiki correspondant à la génération V5.

L’index documentaire se trouve dans [`docs/README.md`](docs/README.md). Les règles complètes sont décrites dans [`docs/governance/REPOSITORY_STRUCTURE.md`](docs/governance/REPOSITORY_STRUCTURE.md).

## Installation

Sous Windows 10/11 x64, vérifier l’empreinte puis lancer l’EXE. Docker Desktop et Compose v2 restent nécessaires. Une mise à niveau depuis 5.0.0 ou 5.0.1 conserve `.env`, `data/` et le volume PostgreSQL ; ne pas exécuter `docker compose down -v`.

Le dépôt reste privé tant qu’aucune licence HDP explicite n’a été choisie. L’installateur n’est pas signé Authenticode et la confirmation manuelle sur le poste Windows utilisateur reste une qualification distincte.
