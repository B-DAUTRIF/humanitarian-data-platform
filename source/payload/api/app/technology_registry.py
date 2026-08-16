from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import urlparse


CATALOG_VERSION = "5.0.0"
VERIFIED_AT = "2026-08-15"
GITHUB_REPOSITORY_URL = "https://github.com/B-DAUTRIF/humanitarian-data-platform"
GOOGLE_DRIVE_FOLDER_URL = (
    "https://drive.google.com/drive/folders/15rAjpoEWVnZfUzdmBaBOnO3sUeVZX7C0"
)


def resource(
    resource_id: str,
    name: str,
    category: str,
    purpose: str,
    links: list[tuple[str, str]],
    *,
    status: str = "used",
) -> dict[str, Any]:
    return {
        "id": resource_id,
        "name": name,
        "category": category,
        "purpose": purpose,
        "status": status,
        "links": [{"label": label, "url": url} for label, url in links],
    }


_RESOURCES: tuple[dict[str, Any], ...] = (
    resource(
        "hdp-code",
        "Code et livrables HDP",
        "Code du projet",
        "Sources, archives, documentation, installateur et empreintes de la version courante.",
        [
            ("Dossier Google Drive HDP 5.0.0", GOOGLE_DRIVE_FOLDER_URL),
            ("Dépôt GitHub privé", GITHUB_REPOSITORY_URL),
            ("Sources sur GitHub", f"{GITHUB_REPOSITORY_URL}/tree/main/source"),
            ("Tests sur GitHub", f"{GITHUB_REPOSITORY_URL}/tree/main/source/tests"),
            ("Documentation interactive locale", "/docs"),
            ("Contrat OpenAPI local", "/openapi.json"),
        ],
    ),
    resource(
        "python",
        "Python",
        "API et traitement",
        "Langage principal de l’API, des connecteurs, des traitements et des tests.",
        [
            ("Documentation", "https://docs.python.org/3/"),
            ("Téléchargements Windows", "https://www.python.org/downloads/windows/"),
            ("Tutoriel", "https://docs.python.org/3/tutorial/"),
        ],
    ),
    resource(
        "fastapi",
        "FastAPI",
        "API et traitement",
        "API HTTP typée, validation des requêtes et documentation OpenAPI.",
        [
            ("Documentation", "https://fastapi.tiangolo.com/"),
            ("Tutoriel", "https://fastapi.tiangolo.com/tutorial/"),
            ("Code source", "https://github.com/fastapi/fastapi"),
        ],
    ),
    resource(
        "pydantic",
        "Pydantic",
        "API et traitement",
        "Validation des modèles d’entrée et des limites applicatives.",
        [
            ("Documentation", "https://docs.pydantic.dev/latest/"),
            ("Modèles", "https://docs.pydantic.dev/latest/concepts/models/"),
            ("Code source", "https://github.com/pydantic/pydantic"),
        ],
    ),
    resource(
        "httpx",
        "HTTPX",
        "API et traitement",
        "Client HTTPS asynchrone des connecteurs avec délais et limites de réponse.",
        [
            ("Documentation", "https://www.python-httpx.org/"),
            ("API asynchrone", "https://www.python-httpx.org/async/"),
            ("Code source", "https://github.com/encode/httpx"),
        ],
    ),
    resource(
        "psycopg",
        "Psycopg 3",
        "API et traitement",
        "Pilote PostgreSQL utilisé par l’API FastAPI.",
        [
            ("Documentation", "https://www.psycopg.org/psycopg3/docs/"),
            ("Transactions", "https://www.psycopg.org/psycopg3/docs/basic/transactions.html"),
            ("Code source", "https://github.com/psycopg/psycopg"),
        ],
    ),
    resource(
        "postgresql",
        "PostgreSQL 16",
        "Base de données",
        "Persistance transactionnelle des projets, paramètres, acquisitions et audits.",
        [
            ("Documentation", "https://www.postgresql.org/docs/16/"),
            ("SQL", "https://www.postgresql.org/docs/16/sql.html"),
            ("Téléchargements", "https://www.postgresql.org/download/"),
        ],
    ),
    resource(
        "postgis",
        "PostGIS 3.4",
        "Base de données",
        "Extension spatiale de PostgreSQL pour les couches et géométries.",
        [
            ("Documentation", "https://postgis.net/documentation/"),
            ("Manuel 3.4", "https://postgis.net/docs/manual-3.4/"),
            ("Code source", "https://github.com/postgis/postgis"),
        ],
    ),
    resource(
        "docker",
        "Docker Desktop et Compose",
        "Conteneurs et exploitation",
        "Installation locale reproductible et isolation des services HDP.",
        [
            ("Docker Desktop", "https://docs.docker.com/desktop/"),
            ("Installation Windows", "https://docs.docker.com/desktop/setup/install/windows-install/"),
            ("Docker Compose", "https://docs.docker.com/compose/"),
            ("Référence Compose", "https://docs.docker.com/reference/compose-file/"),
        ],
    ),
    resource(
        "leaflet",
        "Leaflet 1.9.4",
        "Interface et cartographie",
        "Carte interactive locale servie avec les ressources statiques de l’application.",
        [
            ("Documentation", "https://leafletjs.com/reference.html"),
            ("Tutoriels", "https://leafletjs.com/examples.html"),
            ("Code source", "https://github.com/Leaflet/Leaflet"),
        ],
    ),
    resource(
        "openstreetmap",
        "OpenStreetMap",
        "Interface et cartographie",
        "Fond cartographique par défaut configurable par HDP_TILE_URL.",
        [
            ("Projet", "https://www.openstreetmap.org/"),
            ("Politique des tuiles", "https://operations.osmfoundation.org/policies/tiles/"),
            ("Copyright", "https://www.openstreetmap.org/copyright"),
        ],
    ),
    resource(
        "web-platform",
        "HTML, CSS et JavaScript",
        "Interface et cartographie",
        "Interface web locale sans framework frontal externe.",
        [
            ("HTML MDN", "https://developer.mozilla.org/docs/Web/HTML"),
            ("CSS MDN", "https://developer.mozilla.org/docs/Web/CSS"),
            ("JavaScript MDN", "https://developer.mozilla.org/docs/Web/JavaScript"),
            ("Fetch API", "https://developer.mozilla.org/docs/Web/API/Fetch_API"),
        ],
    ),
    resource(
        "r",
        "R",
        "Analyse statistique",
        "Langage d’analyse optionnel, scripts utilisateurs et service analytique.",
        [
            ("Projet R", "https://www.r-project.org/"),
            ("Manuels", "https://cran.r-project.org/manuals.html"),
            ("Téléchargement Windows", "https://cran.r-project.org/bin/windows/base/"),
        ],
    ),
    resource(
        "plumber",
        "plumber",
        "Analyse statistique",
        "Exposition optionnelle de fonctions R sous forme d’API locale.",
        [
            ("Documentation", "https://www.rplumber.io/"),
            ("Référence", "https://www.rplumber.io/reference/"),
            ("Code source", "https://github.com/rstudio/plumber"),
        ],
    ),
    resource(
        "rstudio",
        "RStudio IDE",
        "IDE et notebooks",
        "IDE conseillé pour reprendre les scripts R exportés par HDP.",
        [
            ("Guide utilisateur", "https://docs.posit.co/ide/user/"),
            ("Téléchargement", "https://posit.co/download/rstudio-desktop/"),
            ("Articles", "https://posit.co/resources/articles/"),
        ],
        status="recommended",
    ),
    resource(
        "anaconda",
        "Anaconda",
        "IDE et notebooks",
        "Distribution Python optionnelle pour l’analyse scientifique locale.",
        [
            ("Documentation", "https://www.anaconda.com/docs/main"),
            ("Téléchargement", "https://www.anaconda.com/download"),
            ("Environnements conda", "https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html"),
        ],
        status="recommended",
    ),
    resource(
        "jupyterlab",
        "JupyterLab",
        "IDE et notebooks",
        "Notebooks Python/R optionnels pour explorer les exports HDP.",
        [
            ("Documentation", "https://jupyterlab.readthedocs.io/en/stable/"),
            ("Installation", "https://jupyter.org/install"),
            ("Code source", "https://github.com/jupyterlab/jupyterlab"),
        ],
        status="recommended",
    ),
    resource(
        "qgis",
        "QGIS",
        "SIG et géodonnées",
        "SIG conseillé pour les exports GeoJSON, GeoPackage et PostGIS.",
        [
            ("Ressources", "https://qgis.org/resources/hub/"),
            ("Documentation", "https://docs.qgis.org/latest/fr/docs/"),
            ("Téléchargement", "https://qgis.org/download/"),
        ],
        status="recommended",
    ),
    resource(
        "python-data",
        "pandas, GeoPandas et Shapely",
        "Bibliothèques d’analyse",
        "Manipulation tabulaire et géospatiale dans les scripts Python.",
        [
            ("pandas", "https://pandas.pydata.org/docs/"),
            ("GeoPandas", "https://geopandas.org/en/stable/docs.html"),
            ("Shapely", "https://shapely.readthedocs.io/en/stable/"),
        ],
        status="recommended",
    ),
    resource(
        "r-data",
        "dplyr, readr, sf et httr2",
        "Bibliothèques d’analyse",
        "Traitement, import, géodonnées et appels API dans les scripts R.",
        [
            ("dplyr", "https://dplyr.tidyverse.org/"),
            ("readr", "https://readr.tidyverse.org/"),
            ("sf", "https://r-spatial.github.io/sf/"),
            ("httr2", "https://httr2.r-lib.org/"),
        ],
        status="recommended",
    ),
    resource(
        "git-github",
        "Git et GitHub",
        "Développement et versions",
        "Historique du code, fonctions REST bornées, CI et publication contrôlée.",
        [
            ("Documentation Git", "https://git-scm.com/doc"),
            ("Téléchargement Git", "https://git-scm.com/download/win"),
            ("GitHub REST API", "https://docs.github.com/en/rest"),
            ("GitHub Actions", "https://docs.github.com/en/actions"),
            ("Jetons d’accès", "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens"),
        ],
    ),
    resource(
        "windows-build",
        "MSVC, MinGW-w64, PowerShell et WinGet",
        "Construction Windows",
        "Compilation et installation de l’exécutable Windows natif.",
        [
            ("Build Tools Visual Studio", "https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022"),
            ("MinGW-w64", "https://www.mingw-w64.org/"),
            ("PowerShell", "https://learn.microsoft.com/powershell/"),
            ("WinGet", "https://learn.microsoft.com/windows/package-manager/winget/"),
        ],
    ),
    resource(
        "api-standards",
        "OpenAPI, JSON Schema et SDMX",
        "Standards et interopérabilité",
        "Contrats d’API, schémas de configuration et échanges statistiques.",
        [
            ("OpenAPI", "https://spec.openapis.org/oas/latest.html"),
            ("JSON Schema", "https://json-schema.org/specification"),
            ("SDMX", "https://sdmx.org/?page_id=5008"),
            ("CKAN API", "https://docs.ckan.org/en/latest/api/"),
        ],
    ),
    resource(
        "geo-standards",
        "GeoJSON, PostGIS, ONU M49 et HXL",
        "Standards et interopérabilité",
        "Géométries, nomenclatures territoriales et vocabulaire humanitaire.",
        [
            ("GeoJSON RFC 7946", "https://www.rfc-editor.org/rfc/rfc7946"),
            ("ONU M49", "https://unstats.un.org/unsd/methodology/m49/"),
            ("HXL", "https://hxlstandard.org/standard/1-1final/"),
            ("PostGIS", "https://postgis.net/documentation/"),
        ],
    ),
    resource(
        "integrity-security",
        "SHA-256, CycloneDX et OWASP",
        "Sécurité et traçabilité",
        "Empreintes, inventaire logiciel et contrôles de sécurité applicatifs.",
        [
            ("NIST SHA", "https://csrc.nist.gov/projects/hash-functions"),
            ("CycloneDX", "https://cyclonedx.org/docs/1.6/json/"),
            ("OWASP SSRF", "https://owasp.org/www-community/attacks/Server_Side_Request_Forgery"),
            ("OWASP ASVS", "https://owasp.org/www-project-application-security-verification-standard/"),
        ],
    ),
)


def technology_catalog() -> dict[str, Any]:
    items = deepcopy(list(_RESOURCES))
    for item in items:
        for link in item["links"]:
            parsed = urlparse(link["url"])
            if not (link["url"].startswith("/") or parsed.scheme == "https"):
                raise ValueError(f"Lien non sécurisé dans le registre : {link['url']}")
    categories = sorted({item["category"] for item in items})
    return {
        "version": CATALOG_VERSION,
        "verified_at": VERIFIED_AT,
        "github_repository_url": GITHUB_REPOSITORY_URL,
        "google_drive_folder_url": GOOGLE_DRIVE_FOLDER_URL,
        "resource_count": len(items),
        "link_count": sum(len(item["links"]) for item in items),
        "categories": categories,
        "items": items,
    }
