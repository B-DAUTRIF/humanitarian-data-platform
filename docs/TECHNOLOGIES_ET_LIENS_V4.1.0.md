# Technologies, logiciels tiers et liens - HDP 4.1.0

La page **USER - Technologies & code** est le point d'entrée utilisateur vers
le code, les outils et la documentation. Son catalogue versionné contient
25 ressources, 13 catégories et 87 liens. Il est aussi disponible en JSON par
`GET /api/technologies`.

## Code et documentation HDP

- [Dossier Google Drive HDP 4.1.0](https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0)
- [Dépôt GitHub privé](https://github.com/B-DAUTRIF/humanitarian-data-platform)
- API locale : `/docs`
- contrat OpenAPI local : `/openapi.json`
- catalogue machine : `/api/technologies`

Le dossier Drive regroupe le code source, les archives, la notice, les
empreintes et l'installateur de la version livrée. Le dépôt GitHub n'est pas
rendu public par cette version.

## Socle applicatif

| Rôle | Technologie | Documentation | Code source / téléchargement |
|---|---|---|---|
| API | Python | [docs Python](https://docs.python.org/3/) | [Windows](https://www.python.org/downloads/windows/) |
| API typée | FastAPI | [documentation](https://fastapi.tiangolo.com/) | [GitHub](https://github.com/fastapi/fastapi) |
| Validation | Pydantic | [documentation](https://docs.pydantic.dev/latest/) | [GitHub](https://github.com/pydantic/pydantic) |
| HTTP asynchrone | HTTPX | [documentation](https://www.python-httpx.org/) | [GitHub](https://github.com/encode/httpx) |
| PostgreSQL | Psycopg 3 | [documentation](https://www.psycopg.org/psycopg3/docs/) | [GitHub](https://github.com/psycopg/psycopg) |
| Base | PostgreSQL 16 | [manuel](https://www.postgresql.org/docs/16/) | [téléchargements](https://www.postgresql.org/download/) |
| Spatial | PostGIS 3.4 | [manuel](https://postgis.net/docs/manual-3.4/) | [GitHub](https://github.com/postgis/postgis) |
| Conteneurs | Docker Desktop / Compose | [Docker Desktop](https://docs.docker.com/desktop/) | [installation Windows](https://docs.docker.com/desktop/setup/install/windows-install/) |
| Carte | Leaflet 1.9.4 | [référence](https://leafletjs.com/reference.html) | [GitHub](https://github.com/Leaflet/Leaflet) |
| Fond de carte | OpenStreetMap | [projet](https://www.openstreetmap.org/) | [politique de tuiles](https://operations.osmfoundation.org/policies/tiles/) |
| Interface | HTML / CSS / JavaScript | [MDN Web Docs](https://developer.mozilla.org/) | [Fetch API](https://developer.mozilla.org/docs/Web/API/Fetch_API) |

## Analyse, R et SIG

| Usage | Outil | Liens officiels |
|---|---|---|
| Analyse R | R | [projet](https://www.r-project.org/), [manuels](https://cran.r-project.org/manuals.html), [Windows](https://cran.r-project.org/bin/windows/base/) |
| API R optionnelle | plumber | [documentation](https://www.rplumber.io/), [code](https://github.com/rstudio/plumber) |
| IDE R | RStudio | [guide](https://docs.posit.co/ide/user/), [téléchargement](https://posit.co/download/rstudio-desktop/) |
| Distribution Python | Anaconda | [documentation](https://www.anaconda.com/docs/main), [téléchargement](https://www.anaconda.com/download) |
| Notebooks | JupyterLab | [documentation](https://jupyterlab.readthedocs.io/en/stable/), [installation](https://jupyter.org/install) |
| SIG | QGIS | [documentation](https://docs.qgis.org/latest/fr/docs/), [téléchargement](https://qgis.org/download/) |
| Python tabulaire | pandas | [documentation](https://pandas.pydata.org/docs/), [code](https://github.com/pandas-dev/pandas) |
| Python géospatial | GeoPandas / Shapely | [GeoPandas](https://geopandas.org/), [Shapely](https://shapely.readthedocs.io/) |
| R tabulaire | dplyr / readr | [dplyr](https://dplyr.tidyverse.org/), [readr](https://readr.tidyverse.org/) |
| R géospatial / HTTP | sf / httr2 | [sf](https://r-spatial.github.io/sf/), [httr2](https://httr2.r-lib.org/) |

## Standards, construction et sécurité

La page fournit aussi les documentations officielles d'OpenAPI, JSON Schema,
SDMX, CKAN, GeoJSON, ONU M49, HXL, Git, GitHub, Microsoft C/C++, l'API Win32,
SHA-256, CycloneDX et OWASP. Ces liens sont déclarés dans
`source/payload/api/app/technology_registry.py`, testés pour interdire les URL
non sécurisées et rendus par l'interface sans code distant.

Les liens vers un produit tiers n'impliquent ni partenariat ni obligation
d'installation. RStudio, Anaconda, JupyterLab et QGIS sont des outils conseillés
pour reprendre les exports ; le fonctionnement principal repose sur le payload
Docker livré.
