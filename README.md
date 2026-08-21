# Humanitarian Data Platform — version de développement 6.0.0

HDP est une application de recherche, d’acquisition, de qualification et de
traitement de données humanitaires et sanitaires publiques. La ligne 6.0.0
développe un moteur de règles ET/OU versionné, un catalogue exhaustif de
connecteurs, des équivalents fonctionnels et une politique de cache traçable.

> **État au 21 août 2026** — 6.0.0 est une version de développement non encore
> qualifiée. La dernière livraison installable qualifiée reste
> 5.0.2. Voir la [notice V6](docs/NOTICE_TECHNIQUE_FONCTIONNELLE_V6.md) et la
> [todo-list](TODO_Mises_a_jour_HDP.md).

## Installer

- Windows x64 : l'artefact de développement attendu est `HumanitarianDataPlatform_Setup_Native_GUI_v6.0.0-dev.exe`. Vérifier son `.sha256` ; son exécution sur Windows 10/11 avec Docker Desktop reste une recette de qualification distincte.
- Linux poste : dans `source/payload`, lancer `./install-linux.sh workstation`.
- Linux serveur dédié : lancer `./install-linux.sh server`, puis ouvrir HDP par tunnel SSH. Le port reste volontairement lié à `127.0.0.1`.

Les secrets `POSTGRES_PASSWORD`, `HDP_LOCAL_TOKEN` et `HDP_SQL_PASSWORD` sont générés séparément. Ne publiez jamais `.env`.

## V5 en bref

- recherche HDX Data Grid par besoin, dimension, localisation, période et format ;
- conservation et usage des descriptions, structures, types, dates, périodicités, géographies et indicateurs de fiabilité ;
- plans d’agrégation explicites avec contrôles de granularité, période, licence et provenance ;
- ingestion de signaux HDX/RSS/news/GDACS/webhook, déduplication et règles déterministes ;
- recherche Data Grid automatique sur signal et mise à jour des seuls fichiers arrivés à leur échéance attendue ;
- snapshots syndromiques globaux, thématiques ou localisés, sans diagnostic automatique ;
- notebooks `.ipynb` versionnés dans HDP, exécution Python/R cellule par cellule dans des runners sans réseau ;
- interface locale authentifiée, CSRF/Host contrôlés, téléchargements avec résolution IP épinglée ;
- requêtes SQL analysées par AST et exécutées par le rôle PostgreSQL non privilégié `hdp_reader` ;
- runners par job, sans réseau, limites CPU/fichiers/processus, purge après persistance ;
- sauvegarde/restauration V5 avec empreintes externes, manifeste interne et contrôle avant extraction.

## Documentation

- [Guide général V5](docs/HDP_V5_GUIDE.md)
- [Architecture et UML V5](docs/ARCHITECTURE_V5.md)
- [Référence API V5](docs/API_V5.md)
- [Sécurité et validation V5](docs/SECURITY_AND_VALIDATION_V5.md)
- [Installation V5](docs/INSTALLATION_V5.md)
- [Prompt de recréation V6](HDP_Prompt_recreation_global_v6.0.0.txt)
- [Prompt de reconstruction V5 historique](HDP_Prompt_production_global_v5.0.2.txt)
- [Rapport de conformité et évaluation V6](docs/RAPPORT_CONFORMITE_ET_EVALUATION_V6.md)
- [Wiki versionné dans le dépôt](wiki/Home.md)
- [Dépôt GitHub](https://github.com/B-DAUTRIF/humanitarian-data-platform)
- [Wiki V5 versionné sur GitHub](https://github.com/B-DAUTRIF/humanitarian-data-platform/tree/main/wiki)

Références externes : [HDX Data Grids](https://data.humdata.org/dashboards/overview-of-data-grids), [HDX Signals](https://docs.humdata.org/about/hdx-signals), [prompts HDX Signals](https://docs.humdata.org/about/hdx-signals/prompts), [Jupyter](https://jupyter.org/documentation), [ONU M49](https://unstats.un.org/unsd/methodology/m49/).

## Développement et validation

```bash
python3 -m pip install pglast==8.4
python3 tools/run_v6_quality_gate.py
```

Ce jalon est obligatoire après chaque nouvelle implémentation V6. Il ne remplace
pas les recettes Docker, Windows ou les appels réels propres au lot ; il les
signale séparément lorsqu'ils n'ont pas été exécutés.

Le dernier jalon local 6.0.0-dev est consigné dans `HDP_STATE.json`. Docker,
la recette d'installation Windows, le runtime SPIP/PHP et les appels réels aux
connecteurs ne sont pas qualifiés par le seul passage du jalon local.

La recette Windows CI produit l’EXE PE32+ et l’archive complète. Une signature Authenticode nécessite un certificat de signature fourni séparément.

## Limites de responsabilité

HDP fournit un indice technique de complétude des métadonnées, pas une certification éditoriale. Un score syndromique n’est ni un diagnostic ni une alerte officielle. Toute diffusion opérationnelle exige une revue humaine des preuves, des licences et des incertitudes.
