# Humanitarian Data Platform V5

HDP V5 est une application locale de recherche, d’acquisition, de qualification et de traitement de données humanitaires. La V5 ajoute l’exploitation de la notion HDX Data Grid, les métadonnées au niveau jeu/fichier, une chaîne SIGNALS déclenchée par des événements, une surveillance syndromique et un espace notebook compatible Jupyter.

## Installer

- Windows x64 : télécharger `HumanitarianDataPlatform_Setup_Native_GUI_v5.0.1.exe`, vérifier son fichier `.sha256`, puis exécuter l’installateur. Docker Desktop avec Compose v2 reste le moteur Linux embarqué.
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
- [Prompt de reconstruction V5](HDP_Prompt_production_global_v5.0.1.txt)
- [Wiki versionné dans le dépôt](wiki/Home.md)
- [Dépôt GitHub](https://github.com/B-DAUTRIF/humanitarian-data-platform)
- [Wiki V5 versionné sur GitHub](https://github.com/B-DAUTRIF/humanitarian-data-platform/tree/main/wiki)

Références externes : [HDX Data Grids](https://data.humdata.org/dashboards/overview-of-data-grids), [HDX Signals](https://docs.humdata.org/about/hdx-signals), [prompts HDX Signals](https://docs.humdata.org/about/hdx-signals/prompts), [Jupyter](https://jupyter.org/documentation), [ONU M49](https://unstats.un.org/unsd/methodology/m49/).

## Développement et validation

```bash
PYTHONPATH=/tmp/hdp-v5-pglast python3 -B -m unittest discover -s source/tests -v
gcc -std=c17 -O2 -Wall -Wextra -Werror source/payload/runner/runner.c -o /tmp/hdp-runner-v5
node tools/check_inline_javascript.mjs source/payload/api/static/index.html
```

La recette Windows CI produit l’EXE PE32+ et l’archive complète. Une signature Authenticode nécessite un certificat de signature fourni séparément.

## Limites de responsabilité

HDP fournit un indice technique de complétude des métadonnées, pas une certification éditoriale. Un score syndromique n’est ni un diagnostic ni une alerte officielle. Toute diffusion opérationnelle exige une revue humaine des preuves, des licences et des incertitudes.
