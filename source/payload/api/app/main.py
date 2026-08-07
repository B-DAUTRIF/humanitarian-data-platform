from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .project_integrations import (
    OFFICIAL_COD_SERIES,
    UN_M49_SOURCE,
    github_repository_endpoint,
    m49_scope,
    select_geodata_resources,
    select_official_cod_datasets,
    un_m49_catalog,
    validate_github_owner,
    validate_hdx_dataset_id,
    validate_m49_code,
    validate_official_cod_policy,
    validate_repository_name,
)
from .scheduler_utils import MIN_INTERVAL_MINUTES, next_run_at, validate_interval
from .security import (
    confined_path,
    resource_key,
    safe_filename,
    safe_query_fragment,
    sha256_file,
    validate_public_url,
)


APP_NAME = "Humanitarian Data Platform"
APP_VERSION = "2.3.1"
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATABASE_URL = os.environ["DATABASE_URL"]
R_SERVICE_URL = os.getenv("R_SERVICE_URL", "http://r-service:8001")
RELIEFWEB_APPNAME = os.getenv("RELIEFWEB_APPNAME", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DEFAULT_PROJECT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEFAULT_PREFERENCES: dict[str, Any] = {
    "auto_download": False,
    "max_download_bytes": 104_857_600,
    "max_resources_per_acquisition": 20,
    "allowed_formats": [],
}
SCHEDULER_POLL_SECONDS = 20
DEFAULT_GEODATA_INTERVAL_MINUTES = 10_080

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Acquisition, téléchargement et gestion locale de ressources humanitaires par projets.",
)
scheduler_task: asyncio.Task[None] | None = None


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=1000)


class ProjectPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class PreferencesUpdate(BaseModel):
    auto_download: bool = False
    max_download_bytes: int = Field(default=104_857_600, ge=1_048_576, le=2_147_483_648)
    max_resources_per_acquisition: int = Field(default=20, ge=1, le=100)
    allowed_formats: list[str] = Field(default_factory=list, max_length=50)


class GitHubSettingsUpdate(BaseModel):
    owner: str = Field(default="", max_length=39)
    repository_name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    visibility: str = Field(default="private", pattern="^(private|public)$")


class GeodataSettingsUpdate(BaseModel):
    auto_download: bool = False
    m49_scope_code: str = Field(default="001", pattern=r"^\d{3}$")
    official_policy: str = Field(
        default="enhanced_preferred", pattern="^(enhanced_only|enhanced_preferred)$"
    )
    preferred_format: str = Field(
        default="geojson", pattern="^(geojson|geopackage|shapefile|geodatabase)$"
    )
    refresh_interval_minutes: int = Field(default=10_080, ge=60, le=43_200)


class ScriptCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    language: str = Field(pattern="^(python|r|sql|shell|other)$")
    content: str = Field(default="", max_length=500_000)
    description: str = Field(default="", max_length=1000)


class ScriptPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    language: str | None = Field(default=None, pattern="^(python|r|sql|shell|other)$")
    content: str | None = Field(default=None, max_length=500_000)
    description: str | None = Field(default=None, max_length=1000)


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    source: str = Field(pattern="^(reliefweb|hdx)$")
    query: str = Field(min_length=2, max_length=200)
    result_limit: int = Field(default=25, ge=1, le=100)
    auto_download: bool = False
    interval_minutes: int = Field(default=1440, ge=MIN_INTERVAL_MINUTES, le=43_200)
    enabled: bool = True


class SchedulePatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    source: str | None = Field(default=None, pattern="^(reliefweb|hdx)$")
    query: str | None = Field(default=None, min_length=2, max_length=200)
    result_limit: int | None = Field(default=None, ge=1, le=100)
    auto_download: bool | None = None
    interval_minutes: int | None = Field(default=None, ge=MIN_INTERVAL_MINUTES, le=43_200)
    enabled: bool | None = None


class SearchResponse(BaseModel):
    acquisition_id: str
    project_id: str
    source: str
    query: str
    retrieved_at: datetime
    sha256: str
    item_count: int
    raw_path: str
    items: list[dict[str, Any]]
    downloads: dict[str, int]


def database_connection(*, autocommit: bool = True) -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit)


def initialize_database() -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with database_connection() as connection:
                connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id UUID PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        archived_at TIMESTAMPTZ
                    )
                    """
                )
                now = datetime.now(UTC)
                connection.execute(
                    """
                    INSERT INTO projects (id, name, description, created_at, updated_at)
                    VALUES (%s, 'Projet par défaut', 'Données migrées depuis HDP 1.5', %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (DEFAULT_PROJECT_ID, now, now),
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS project_preferences (
                        project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                        preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO project_preferences (project_id, preferences, updated_at)
                    VALUES (%s, %s, %s) ON CONFLICT (project_id) DO NOTHING
                    """,
                    (DEFAULT_PROJECT_ID, Jsonb(DEFAULT_PREFERENCES), now),
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS project_github_settings (
                        project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                        owner TEXT NOT NULL DEFAULT '',
                        repository_name TEXT NOT NULL DEFAULT '',
                        description TEXT NOT NULL DEFAULT '',
                        visibility TEXT NOT NULL DEFAULT 'private',
                        repository_url TEXT,
                        repository_full_name TEXT,
                        created_at TIMESTAMPTZ,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                connection.execute(
                    """
                    INSERT INTO project_github_settings (project_id, updated_at)
                    SELECT id, %s FROM projects
                    ON CONFLICT (project_id) DO NOTHING
                    """,
                    (now,),
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS project_geodata_settings (
                        project_id UUID PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
                        auto_download BOOLEAN NOT NULL DEFAULT FALSE,
                        dataset_id TEXT NOT NULL DEFAULT 'cod-ab-global',
                        preferred_format TEXT NOT NULL DEFAULT 'geojson',
                        max_scale TEXT NOT NULL DEFAULT 'world',
                        m49_scope_code TEXT,
                        official_policy TEXT NOT NULL DEFAULT 'enhanced_preferred',
                        migration_required BOOLEAN NOT NULL DEFAULT FALSE,
                        refresh_interval_minutes INTEGER NOT NULL DEFAULT 10080,
                        next_sync_at TIMESTAMPTZ NOT NULL,
                        last_sync_at TIMESTAMPTZ,
                        last_status TEXT,
                        last_error TEXT,
                        last_acquisition_id UUID,
                        updated_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                connection.execute(
                    "ALTER TABLE project_geodata_settings ADD COLUMN IF NOT EXISTS m49_scope_code TEXT"
                )
                connection.execute(
                    """
                    ALTER TABLE project_geodata_settings
                    ADD COLUMN IF NOT EXISTS official_policy TEXT NOT NULL DEFAULT 'enhanced_preferred'
                    """
                )
                connection.execute(
                    """
                    ALTER TABLE project_geodata_settings
                    ADD COLUMN IF NOT EXISTS migration_required BOOLEAN NOT NULL DEFAULT FALSE
                    """
                )
                connection.execute(
                    """
                    UPDATE project_geodata_settings
                    SET m49_scope_code = '001', migration_required = FALSE
                    WHERE m49_scope_code IS NULL AND max_scale = 'world'
                    """
                )
                connection.execute(
                    """
                    UPDATE project_geodata_settings
                    SET migration_required = TRUE, auto_download = FALSE,
                        last_status = 'migration_required',
                        last_error = 'Sélectionnez un territoire ONU M49 pour remplacer l''ancienne échelle HDP.'
                    WHERE m49_scope_code IS NULL
                    """
                )
                connection.execute(
                    "ALTER TABLE project_geodata_settings ALTER COLUMN m49_scope_code SET DEFAULT '001'"
                )
                connection.execute(
                    """
                    INSERT INTO project_geodata_settings (project_id, next_sync_at, updated_at)
                    SELECT id, %s, %s FROM projects
                    ON CONFLICT (project_id) DO NOTHING
                    """,
                    (next_run_at(now, DEFAULT_GEODATA_INTERVAL_MINUTES), now),
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS project_scripts (
                        id UUID PRIMARY KEY,
                        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        language TEXT NOT NULL,
                        content TEXT NOT NULL DEFAULT '',
                        description TEXT NOT NULL DEFAULT '',
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        archived_at TIMESTAMPTZ
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schedules (
                        id UUID PRIMARY KEY,
                        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        name TEXT NOT NULL,
                        source TEXT NOT NULL,
                        query TEXT NOT NULL,
                        result_limit INTEGER NOT NULL,
                        auto_download BOOLEAN NOT NULL DEFAULT FALSE,
                        interval_minutes INTEGER NOT NULL,
                        enabled BOOLEAN NOT NULL DEFAULT TRUE,
                        next_run_at TIMESTAMPTZ NOT NULL,
                        last_run_at TIMESTAMPTZ,
                        last_status TEXT,
                        last_error TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        archived_at TIMESTAMPTZ
                    )
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS acquisitions (
                        id UUID PRIMARY KEY,
                        project_id UUID,
                        schedule_id UUID,
                        source TEXT NOT NULL,
                        query TEXT NOT NULL,
                        retrieved_at TIMESTAMPTZ NOT NULL,
                        sha256 CHAR(64) NOT NULL,
                        item_count INTEGER NOT NULL,
                        raw_path TEXT NOT NULL
                    )
                    """
                )
                connection.execute("ALTER TABLE acquisitions ADD COLUMN IF NOT EXISTS project_id UUID")
                connection.execute("ALTER TABLE acquisitions ADD COLUMN IF NOT EXISTS schedule_id UUID")
                connection.execute(
                    "UPDATE acquisitions SET project_id = %s WHERE project_id IS NULL",
                    (DEFAULT_PROJECT_ID,),
                )
                connection.execute("ALTER TABLE acquisitions ALTER COLUMN project_id SET NOT NULL")
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS local_resources (
                        id UUID PRIMARY KEY,
                        project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        acquisition_id UUID NOT NULL REFERENCES acquisitions(id) ON DELETE CASCADE,
                        resource_key TEXT NOT NULL,
                        source TEXT NOT NULL,
                        dataset_id TEXT,
                        resource_id TEXT,
                        title TEXT NOT NULL,
                        url TEXT NOT NULL,
                        format TEXT,
                        filename TEXT,
                        local_path TEXT,
                        sha256 CHAR(64),
                        size_bytes BIGINT,
                        content_type TEXT,
                        m49_code TEXT,
                        iso3_code TEXT,
                        cod_level TEXT,
                        publisher TEXT,
                        license_id TEXT,
                        dataset_modified_at TEXT,
                        status TEXT NOT NULL,
                        error TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        deleted_at TIMESTAMPTZ
                    )
                    """
                )
                for column in (
                    "m49_code TEXT",
                    "iso3_code TEXT",
                    "cod_level TEXT",
                    "publisher TEXT",
                    "license_id TEXT",
                    "dataset_modified_at TEXT",
                ):
                    connection.execute(f"ALTER TABLE local_resources ADD COLUMN IF NOT EXISTS {column}")
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS local_resources_project_idx
                    ON local_resources(project_id, updated_at DESC)
                    """
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schedule_runs (
                        id UUID PRIMARY KEY,
                        schedule_id UUID NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                        acquisition_id UUID,
                        started_at TIMESTAMPTZ NOT NULL,
                        finished_at TIMESTAMPTZ,
                        status TEXT NOT NULL,
                        error TEXT
                    )
                    """
                )
            return
        except Exception as exc:  # Docker may still be completing startup.
            last_error = exc
            time.sleep(2)
    raise RuntimeError("Database unavailable after startup retries") from last_error


@app.on_event("startup")
async def startup() -> None:
    global scheduler_task
    DATA_DIR.joinpath("raw").mkdir(parents=True, exist_ok=True)
    DATA_DIR.joinpath("projects").mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(initialize_database)
    scheduler_task = asyncio.create_task(scheduler_loop(), name="hdp-scheduler")


@app.on_event("shutdown")
async def shutdown() -> None:
    global scheduler_task
    if scheduler_task:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
        scheduler_task = None


def ensure_project(project_id: uuid.UUID) -> None:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM projects WHERE id = %s AND archived_at IS NULL", (project_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Projet introuvable ou archivé")


def get_preferences(project_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT preferences FROM project_preferences WHERE project_id = %s", (project_id,)
        ).fetchone()
    stored = row[0] if row else {}
    return {**DEFAULT_PREFERENCES, **stored}


def get_github_settings(project_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT owner, repository_name, description, visibility, repository_url,
                   repository_full_name, created_at, updated_at
            FROM project_github_settings WHERE project_id = %s
            """,
            (project_id,),
        ).fetchone()
    if not row:
        return {
            "owner": "",
            "repository_name": "",
            "description": "",
            "visibility": "private",
            "repository_url": None,
            "repository_full_name": None,
            "created_at": None,
            "updated_at": None,
            "token_configured": bool(GITHUB_TOKEN),
        }
    return {
        "owner": row[0],
        "repository_name": row[1],
        "description": row[2],
        "visibility": row[3],
        "repository_url": row[4],
        "repository_full_name": row[5],
        "created_at": row[6],
        "updated_at": row[7],
        "token_configured": bool(GITHUB_TOKEN),
    }


def get_geodata_settings(project_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT auto_download, preferred_format, refresh_interval_minutes,
                   next_sync_at, last_sync_at, last_status, last_error,
                   last_acquisition_id, updated_at, m49_scope_code,
                   official_policy, migration_required
            FROM project_geodata_settings WHERE project_id = %s
            """,
            (project_id,),
        ).fetchone()
    if not row:
        now = datetime.now(UTC)
        return {
            "auto_download": False,
            "preferred_format": "geojson",
            "refresh_interval_minutes": DEFAULT_GEODATA_INTERVAL_MINUTES,
            "next_sync_at": next_run_at(now, DEFAULT_GEODATA_INTERVAL_MINUTES),
            "last_sync_at": None,
            "last_status": None,
            "last_error": None,
            "last_acquisition_id": None,
            "updated_at": now,
            "m49_scope_code": "001",
            "official_policy": "enhanced_preferred",
            "migration_required": False,
        }
    keys = [
        "auto_download",
        "preferred_format",
        "refresh_interval_minutes",
        "next_sync_at",
        "last_sync_at",
        "last_status",
        "last_error",
        "last_acquisition_id",
        "updated_at",
        "m49_scope_code",
        "official_policy",
        "migration_required",
    ]
    values = list(row)
    if values[7]:
        values[7] = str(values[7])
    return dict(zip(keys, values))


def persist_raw(
    project_id: uuid.UUID,
    source: str,
    query: str,
    payload: dict[str, Any],
    item_count: int,
    schedule_id: uuid.UUID | None,
) -> dict[str, Any]:
    retrieved_at = datetime.now(UTC)
    acquisition_id = uuid.uuid4()
    raw_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    relative = (
        Path("raw")
        / str(project_id)
        / source
        / f"{retrieved_at:%Y%m%dT%H%M%SZ}_{safe_query_fragment(query)}_{acquisition_id}.json"
    )
    destination = confined_path(DATA_DIR, str(relative))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw_bytes)

    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO acquisitions
                (id, project_id, schedule_id, source, query, retrieved_at, sha256, item_count, raw_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                acquisition_id,
                project_id,
                schedule_id,
                source,
                query,
                retrieved_at,
                digest,
                item_count,
                str(relative),
            ),
        )
    return {
        "acquisition_id": str(acquisition_id),
        "retrieved_at": retrieved_at,
        "sha256": digest,
        "raw_path": str(relative),
    }


def reliefweb_files(fields: dict[str, Any]) -> list[dict[str, Any]]:
    raw = fields.get("file") or fields.get("files") or []
    if isinstance(raw, dict):
        raw = [raw]
    resources: list[dict[str, Any]] = []
    for index, item in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("href")
        if url:
            resources.append(
                {
                    "id": str(item.get("id") or index),
                    "name": item.get("filename") or item.get("name") or "Fichier ReliefWeb",
                    "url": url,
                    "format": item.get("mimetype") or Path(urlparse(url).path).suffix.lstrip("."),
                }
            )
    return resources


async def search_reliefweb(query: str, limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not RELIEFWEB_APPNAME:
        raise HTTPException(
            status_code=503,
            detail=(
                "ReliefWeb exige un appname pré-approuvé. Ajoutez RELIEFWEB_APPNAME "
                "dans le fichier .env puis redémarrez l'application."
            ),
        )
    params = {
        "appname": RELIEFWEB_APPNAME,
        "query[value]": query,
        "limit": limit,
        "profile": "full",
    }
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        response = await client.get("https://api.reliefweb.int/v2/reports", params=params)
        response.raise_for_status()
        payload = response.json()
    items = []
    for row in payload.get("data", []):
        fields = row.get("fields", {})
        items.append(
            {
                "id": row.get("id"),
                "title": fields.get("title"),
                "date": fields.get("date", {}).get("created"),
                "url": fields.get("url_alias") or row.get("href"),
                "source": "ReliefWeb",
                "resources": reliefweb_files(fields),
            }
        )
    return payload, items


async def search_hdx(query: str, limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    params = {"q": query, "rows": limit}
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        response = await client.get("https://data.humdata.org/api/3/action/package_search", params=params)
        response.raise_for_status()
        payload = response.json()
    if not payload.get("success"):
        raise httpx.HTTPStatusError("Réponse CKAN signalée en échec", request=response.request, response=response)
    results = payload.get("result", {}).get("results", [])
    items = []
    for row in results:
        resources = [
            {
                "id": resource.get("id"),
                "name": resource.get("name") or resource.get("description") or "Ressource HDX",
                "url": resource.get("url"),
                "format": resource.get("format"),
            }
            for resource in row.get("resources", [])
            if resource.get("url")
        ]
        items.append(
            {
                "id": row.get("id"),
                "title": row.get("title") or row.get("name"),
                "date": row.get("metadata_modified"),
                "url": f"https://data.humdata.org/dataset/{row.get('name')}",
                "source": "HDX/CKAN",
                "resources": resources,
            }
        )
    return payload, items


async def fetch_hdx_dataset(dataset_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    params = {"id": validate_hdx_dataset_id(dataset_id)}
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        response = await client.get(
            "https://data.humdata.org/api/3/action/package_show", params=params
        )
        response.raise_for_status()
        payload = response.json()
    if not payload.get("success") or not isinstance(payload.get("result"), dict):
        raise httpx.HTTPStatusError(
            "Réponse CKAN signalée en échec", request=response.request, response=response
        )
    return payload, payload["result"]


async def fetch_hdx_official_cod_catalog() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    params = {
        "fq": f'dataseries_name:"{OFFICIAL_COD_SERIES}"',
        "rows": 1000,
        "sort": "metadata_modified desc",
    }
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.get(
            "https://data.humdata.org/api/3/action/package_search", params=params
        )
        response.raise_for_status()
        payload = response.json()
    result = payload.get("result")
    if not payload.get("success") or not isinstance(result, dict):
        raise httpx.HTTPStatusError(
            "Réponse CKAN signalée en échec", request=response.request, response=response
        )
    datasets = result.get("results")
    if not isinstance(datasets, list):
        raise httpx.HTTPStatusError(
            "Catalogue CKAN invalide", request=response.request, response=response
        )
    return payload, [dataset for dataset in datasets if isinstance(dataset, dict)]


def format_allowed(resource_format: str | None, allowed: list[str]) -> bool:
    if not allowed:
        return True
    normalized = (resource_format or "").strip().lower().lstrip(".")
    return normalized in {item.strip().lower().lstrip(".") for item in allowed if item.strip()}


def reserve_resource(
    project_id: uuid.UUID,
    acquisition_id: uuid.UUID,
    source: str,
    dataset_id: str | None,
    resource: dict[str, Any],
) -> tuple[uuid.UUID, str | None, str]:
    url = str(resource["url"])
    key = resource_key(resource.get("id"), url)
    official = resource.get("_hdp_official")
    if not isinstance(official, dict):
        official = {}
    with database_connection() as connection:
        existing = connection.execute(
            """
            SELECT id, local_path, status FROM local_resources
            WHERE project_id = %s AND resource_key = %s AND url = %s AND deleted_at IS NULL
            ORDER BY updated_at DESC LIMIT 1
            """,
            (project_id, key, url),
        ).fetchone()
        if existing:
            if existing[2] != "completed":
                connection.execute(
                    """
                    UPDATE local_resources
                    SET acquisition_id = %s, source = %s, dataset_id = %s,
                        m49_code = %s, iso3_code = %s, cod_level = %s,
                        publisher = %s, license_id = %s, dataset_modified_at = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (
                        acquisition_id,
                        source,
                        dataset_id,
                        official.get("m49_code"),
                        official.get("iso3"),
                        official.get("cod_level"),
                        official.get("publisher"),
                        official.get("license_id"),
                        official.get("metadata_modified"),
                        datetime.now(UTC),
                        existing[0],
                    ),
                )
            return existing[0], existing[1], existing[2]
        resource_id = uuid.uuid4()
        now = datetime.now(UTC)
        connection.execute(
            """
            INSERT INTO local_resources
                (id, project_id, acquisition_id, resource_key, source, dataset_id, resource_id,
                 title, url, format, m49_code, iso3_code, cod_level, publisher, license_id,
                 dataset_modified_at, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    'queued', %s, %s)
            """,
            (
                resource_id,
                project_id,
                acquisition_id,
                key,
                source,
                dataset_id,
                resource.get("id"),
                resource.get("name") or "Ressource",
                url,
                resource.get("format"),
                official.get("m49_code"),
                official.get("iso3"),
                official.get("cod_level"),
                official.get("publisher"),
                official.get("license_id"),
                official.get("metadata_modified"),
                now,
                now,
            ),
        )
    return resource_id, None, "queued"


def update_resource(resource_id: uuid.UUID, status: str, **values: Any) -> None:
    allowed = {"filename", "local_path", "sha256", "size_bytes", "content_type", "error", "deleted_at"}
    assignments = ["status = %s", "updated_at = %s"]
    parameters: list[Any] = [status, datetime.now(UTC)]
    for key, value in values.items():
        if key in allowed:
            assignments.append(f"{key} = %s")
            parameters.append(value)
    parameters.append(resource_id)
    with database_connection() as connection:
        connection.execute(
            f"UPDATE local_resources SET {', '.join(assignments)} WHERE id = %s",  # noqa: S608
            parameters,
        )


def filename_from_response(url: str, response: httpx.Response, fallback: str) -> str:
    disposition = response.headers.get("content-disposition", "")
    match = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", disposition, flags=re.IGNORECASE)
    candidate = unquote(match.group(1).strip()) if match else Path(urlparse(url).path).name
    return safe_filename(candidate, fallback)


async def download_one(
    resource_id: uuid.UUID,
    project_id: uuid.UUID,
    acquisition_id: uuid.UUID,
    resource: dict[str, Any],
    max_bytes: int,
) -> str:
    current_url = validate_public_url(str(resource["url"]))
    update_resource(resource_id, "downloading", error=None)
    timeout = httpx.Timeout(120, connect=20)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for _ in range(6):
            async with client.stream("GET", current_url, headers={"User-Agent": f"HDP/{APP_VERSION}"}) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise ValueError("Redirection sans destination")
                    current_url = validate_public_url(urljoin(current_url, location))
                    continue
                response.raise_for_status()
                declared = response.headers.get("content-length")
                if declared and int(declared) > max_bytes:
                    raise ValueError(f"Ressource supérieure à la limite de {max_bytes} octets")
                filename = filename_from_response(current_url, response, f"{resource_id}.bin")
                relative = Path("projects") / str(project_id) / "resources" / str(acquisition_id) / f"{resource_id}_{filename}"
                destination = confined_path(DATA_DIR, str(relative))
                destination.parent.mkdir(parents=True, exist_ok=True)
                partial = destination.with_suffix(destination.suffix + ".part")
                digest = hashlib.sha256()
                total = 0
                try:
                    with partial.open("wb") as stream:
                        async for chunk in response.aiter_bytes(65_536):
                            total += len(chunk)
                            if total > max_bytes:
                                raise ValueError(f"Ressource supérieure à la limite de {max_bytes} octets")
                            digest.update(chunk)
                            stream.write(chunk)
                    partial.replace(destination)
                except Exception:
                    partial.unlink(missing_ok=True)
                    raise
                update_resource(
                    resource_id,
                    "completed",
                    filename=filename,
                    local_path=str(relative),
                    sha256=digest.hexdigest(),
                    size_bytes=total,
                    content_type=response.headers.get("content-type", "").split(";")[0],
                    error=None,
                )
                return "completed"
        raise ValueError("Trop de redirections HTTP")


async def download_resources(
    project_id: uuid.UUID,
    acquisition_id: uuid.UUID,
    source: str,
    items: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> dict[str, int]:
    summary = {"queued": 0, "completed": 0, "skipped": 0, "failed": 0, "deferred": 0}
    cap = int(preferences["max_resources_per_acquisition"])
    candidates: list[tuple[str | None, dict[str, Any]]] = []
    for item in items:
        for resource in item.get("resources", []):
            if resource.get("url"):
                candidates.append((str(item.get("id")) if item.get("id") else None, resource))
    attempted = 0
    for dataset_id, resource in candidates:
        if not format_allowed(resource.get("format"), preferences.get("allowed_formats", [])):
            summary["skipped"] += 1
            continue
        resource_db_id, local_path, status = reserve_resource(
            project_id, acquisition_id, source, dataset_id, resource
        )
        if status == "completed" and local_path:
            try:
                if confined_path(DATA_DIR, local_path).is_file():
                    summary["skipped"] += 1
                    continue
            except ValueError:
                pass
        if attempted >= cap:
            summary["deferred"] += 1
            continue
        attempted += 1
        summary["queued"] += 1
        try:
            await download_one(
                resource_db_id,
                project_id,
                acquisition_id,
                resource,
                int(preferences["max_download_bytes"]),
            )
            summary["completed"] += 1
        except (httpx.HTTPError, OSError, ValueError) as exc:
            update_resource(resource_db_id, "failed", error=str(exc)[:1000])
            summary["failed"] += 1
    return summary


async def execute_acquisition(
    project_id: uuid.UUID,
    source: str,
    query: str,
    limit: int,
    auto_download: bool,
    schedule_id: uuid.UUID | None = None,
) -> SearchResponse:
    ensure_project(project_id)
    try:
        if source == "reliefweb":
            payload, items = await search_reliefweb(query, limit)
        else:
            payload, items = await search_hdx(query, limit)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Source distante indisponible: {exc}") from exc

    provenance = persist_raw(project_id, source, query, payload, len(items), schedule_id)
    downloads = {"queued": 0, "completed": 0, "skipped": 0, "failed": 0, "deferred": 0}
    if auto_download:
        downloads = await download_resources(
            project_id,
            uuid.UUID(provenance["acquisition_id"]),
            source,
            items,
            get_preferences(project_id),
        )
    return SearchResponse(
        project_id=str(project_id),
        source=source,
        query=query,
        item_count=len(items),
        items=items,
        downloads=downloads,
        **provenance,
    )


def finish_geodata_sync(
    project_id: uuid.UUID,
    status: str,
    acquisition_id: uuid.UUID | None = None,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE project_geodata_settings
            SET last_sync_at = %s, last_status = %s, last_error = %s,
                last_acquisition_id = %s, updated_at = %s
            WHERE project_id = %s
            """,
            (now, status, error, acquisition_id, now, project_id),
        )


async def execute_geodata_sync(
    project_id: uuid.UUID, settings: dict[str, Any] | None = None
) -> dict[str, Any]:
    ensure_project(project_id)
    profile = settings or get_geodata_settings(project_id)
    if profile.get("migration_required"):
        raise HTTPException(
            status_code=409,
            detail="Sélectionnez et enregistrez un territoire ONU M49 avant la synchronisation.",
        )
    scope_code = validate_m49_code(str(profile["m49_scope_code"]))
    policy = validate_official_cod_policy(str(profile["official_policy"]))
    preferred_format = str(profile["preferred_format"])
    try:
        hdx_payload, catalog = await fetch_hdx_official_cod_catalog()
    except httpx.HTTPError as exc:
        finish_geodata_sync(project_id, "failed", error=f"Source HDX indisponible: {exc}"[:2000])
        raise HTTPException(status_code=502, detail=f"Source HDX indisponible: {exc}") from exc

    datasets, missing = select_official_cod_datasets(catalog, scope_code, policy)
    items: list[dict[str, Any]] = []
    no_matching_format: list[dict[str, Any]] = []
    for dataset in datasets:
        official = dict(dataset["_hdp_official"])
        selected = []
        for resource in select_geodata_resources(dataset.get("resources", []), preferred_format):
            annotated = dict(resource)
            annotated["_hdp_official"] = official
            selected.append(annotated)
        if not selected:
            no_matching_format.append(official)
        items.append(
            {
                "id": official["dataset_id"],
                "title": dataset.get("title") or official["dataset_id"],
                "date": dataset.get("metadata_modified"),
                "url": f"https://data.humdata.org/dataset/{official['dataset_id']}",
                "source": "HDX/CKAN — COD-AB officiel",
                "official": official,
                "resources": selected,
            }
        )

    scope = m49_scope(scope_code)
    archived_payload = {
        "hdx_catalog_response": hdx_payload,
        "hdp_geographic_profile": {
            "profile": "ONU M49 + COD-AB officiel OCHA/HDX",
            "m49_scope": scope,
            "official_policy": policy,
            "preferred_format": preferred_format,
            "official_data_series": OFFICIAL_COD_SERIES,
            "accepted_cod_levels": ["cod-enhanced"]
            if policy == "enhanced_only"
            else ["cod-enhanced", "cod-standard"],
            "un_m49_source": UN_M49_SOURCE,
            "selected_datasets": [item["official"] for item in items],
            "missing_m49_entities": missing,
            "datasets_without_preferred_format": no_matching_format,
        },
    }
    provenance = persist_raw(
        project_id,
        "hdx-geodata",
        f"m49-{scope_code}-{policy}-{preferred_format}",
        archived_payload,
        len(datasets),
        None,
    )
    acquisition_id = uuid.UUID(provenance["acquisition_id"])
    downloads = {"queued": 0, "completed": 0, "skipped": 0, "failed": 0, "deferred": 0}
    warnings: list[str] = []
    resource_count = sum(len(item["resources"]) for item in items)
    if resource_count:
        preferences = get_preferences(project_id)
        preferences["allowed_formats"] = []
        downloads = await download_resources(
            project_id, acquisition_id, "hdx-geodata", items, preferences
        )
        if downloads["failed"]:
            warnings.append(f"{downloads['failed']} téléchargement(s) ont échoué.")
        if downloads["deferred"]:
            warnings.append(
                f"{downloads['deferred']} ressource(s) reportée(s) au prochain passage par la limite du projet."
            )
    if missing:
        examples = ", ".join(str(entity["name"]) for entity in missing[:5])
        suffix = "…" if len(missing) > 5 else ""
        warnings.append(
            f"Aucun COD-AB officiel admissible pour {len(missing)} pays ou zone(s) M49 : {examples}{suffix}"
        )
    if no_matching_format:
        warnings.append(
            f"{len(no_matching_format)} jeu(x) officiel(s) ne publient pas le format {preferred_format}."
        )

    if not datasets:
        status = "no_official_dataset"
    elif not resource_count:
        status = "no_matching_resource"
    elif downloads["failed"] and not downloads["completed"] and not downloads["skipped"]:
        status = "failed"
    elif warnings:
        status = "partial"
    else:
        status = "completed"

    warning = " ".join(warnings) or None
    finish_geodata_sync(project_id, status, acquisition_id, warning)
    return {
        "project_id": str(project_id),
        "m49_scope": scope,
        "official_policy": policy,
        "preferred_format": preferred_format,
        "acquisition_id": str(acquisition_id),
        "raw_path": provenance["raw_path"],
        "sha256": provenance["sha256"],
        "dataset_count": len(datasets),
        "missing_dataset_count": len(missing),
        "resource_count": resource_count,
        "downloads": downloads,
        "status": status,
        "warning": warning,
    }


def claim_due_schedule() -> dict[str, Any] | None:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            """
            SELECT id, project_id, source, query, result_limit, auto_download, interval_minutes
            FROM schedules
            WHERE enabled = TRUE AND archived_at IS NULL AND next_run_at <= %s
            ORDER BY next_run_at ASC FOR UPDATE SKIP LOCKED LIMIT 1
            """,
            (now,),
        ).fetchone()
        if not row:
            connection.commit()
            return None
        run_id = uuid.uuid4()
        connection.execute(
            "UPDATE schedules SET next_run_at = %s, last_status = 'running', updated_at = %s WHERE id = %s",
            (next_run_at(now, row[6]), now, row[0]),
        )
        connection.execute(
            "INSERT INTO schedule_runs (id, schedule_id, started_at, status) VALUES (%s, %s, %s, 'running')",
            (run_id, row[0], now),
        )
        connection.commit()
    return {
        "run_id": run_id,
        "id": row[0],
        "project_id": row[1],
        "source": row[2],
        "query": row[3],
        "result_limit": row[4],
        "auto_download": row[5],
    }


def finish_schedule_run(
    schedule_id: uuid.UUID,
    run_id: uuid.UUID,
    status: str,
    acquisition_id: uuid.UUID | None = None,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE schedule_runs SET acquisition_id = %s, finished_at = %s, status = %s, error = %s
            WHERE id = %s
            """,
            (acquisition_id, now, status, error, run_id),
        )
        connection.execute(
            """
            UPDATE schedules SET last_run_at = %s, last_status = %s, last_error = %s, updated_at = %s
            WHERE id = %s
            """,
            (now, status, error, now, schedule_id),
        )


async def execute_claimed_schedule(schedule: dict[str, Any]) -> None:
    try:
        result = await execute_acquisition(
            schedule["project_id"],
            schedule["source"],
            schedule["query"],
            schedule["result_limit"],
            schedule["auto_download"],
            schedule["id"],
        )
        finish_schedule_run(
            schedule["id"], schedule["run_id"], "completed", uuid.UUID(result.acquisition_id)
        )
    except Exception as exc:  # Keep the persistent scheduler alive and record the failure.
        finish_schedule_run(schedule["id"], schedule["run_id"], "failed", error=str(exc)[:2000])


def claim_due_geodata() -> dict[str, Any] | None:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            """
            SELECT g.project_id, g.m49_scope_code, g.official_policy,
                   g.preferred_format, g.refresh_interval_minutes, g.migration_required
            FROM project_geodata_settings g
            JOIN projects p ON p.id = g.project_id
            WHERE g.auto_download = TRUE AND g.migration_required = FALSE
                  AND g.next_sync_at <= %s AND p.archived_at IS NULL
            ORDER BY g.next_sync_at ASC FOR UPDATE OF g SKIP LOCKED LIMIT 1
            """,
            (now,),
        ).fetchone()
        if not row:
            connection.commit()
            return None
        connection.execute(
            """
            UPDATE project_geodata_settings
            SET next_sync_at = %s, last_status = 'running', last_error = NULL, updated_at = %s
            WHERE project_id = %s
            """,
            (next_run_at(now, row[4]), now, row[0]),
        )
        connection.commit()
    return {
        "project_id": row[0],
        "m49_scope_code": row[1],
        "official_policy": row[2],
        "preferred_format": row[3],
        "refresh_interval_minutes": row[4],
        "migration_required": row[5],
    }


async def execute_claimed_geodata(settings: dict[str, Any]) -> None:
    try:
        await execute_geodata_sync(settings["project_id"], settings)
    except Exception as exc:  # Keep the persistent scheduler alive and record the failure.
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        finish_geodata_sync(settings["project_id"], "failed", error=str(detail)[:2000])


async def scheduler_loop() -> None:
    while True:
        try:
            schedule = await asyncio.to_thread(claim_due_schedule)
            if schedule:
                await execute_claimed_schedule(schedule)
                continue
            geodata = await asyncio.to_thread(claim_due_geodata)
            if geodata:
                await execute_claimed_geodata(geodata)
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            # A transient database failure must not permanently stop future schedules.
            pass
        await asyncio.sleep(SCHEDULER_POLL_SECONDS)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, Any]:
    with database_connection() as connection:
        connection.execute("SELECT 1").fetchone()
    return {
        "status": "ok",
        "application": APP_NAME,
        "version": APP_VERSION,
        "scheduler": "running" if scheduler_task and not scheduler_task.done() else "stopped",
    }


@app.get("/api/sources")
def sources() -> list[dict[str, str]]:
    return [
        {"id": "reliefweb", "name": "ReliefWeb", "access": "API avec appname pré-approuvé"},
        {"id": "hdx", "name": "HDX / CKAN", "access": "API publique"},
    ]


@app.get("/api/un-m49/entities")
def un_m49_entities() -> dict[str, Any]:
    return {"source": UN_M49_SOURCE, "entities": un_m49_catalog()}


@app.get("/api/projects")
def projects() -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.id, p.name, p.description, p.created_at, p.updated_at,
                   (SELECT COUNT(*) FROM acquisitions a WHERE a.project_id = p.id),
                   (SELECT COUNT(*) FROM local_resources r WHERE r.project_id = p.id AND r.deleted_at IS NULL),
                   (SELECT COALESCE(SUM(r.size_bytes), 0) FROM local_resources r
                    WHERE r.project_id = p.id AND r.deleted_at IS NULL AND r.status = 'completed')
            FROM projects p
            WHERE p.archived_at IS NULL
            ORDER BY p.created_at ASC
            """
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "acquisition_count": row[5],
            "resource_count": row[6],
            "storage_bytes": row[7],
        }
        for row in rows
    ]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate) -> dict[str, Any]:
    project_id = uuid.uuid4()
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (id, name, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (project_id, payload.name.strip(), payload.description.strip(), now, now),
        )
        connection.execute(
            "INSERT INTO project_preferences (project_id, preferences, updated_at) VALUES (%s, %s, %s)",
            (project_id, Jsonb(DEFAULT_PREFERENCES), now),
        )
        connection.execute(
            "INSERT INTO project_github_settings (project_id, updated_at) VALUES (%s, %s)",
            (project_id, now),
        )
        connection.execute(
            """
            INSERT INTO project_geodata_settings (project_id, next_sync_at, updated_at)
            VALUES (%s, %s, %s)
            """,
            (project_id, next_run_at(now, DEFAULT_GEODATA_INTERVAL_MINUTES), now),
        )
    return {"id": str(project_id), "name": payload.name.strip(), "description": payload.description.strip()}


@app.patch("/api/projects/{project_id}")
def update_project(project_id: uuid.UUID, payload: ProjectPatch) -> dict[str, str]:
    ensure_project(project_id)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return {"status": "unchanged"}
    assignments, parameters = [], []
    for key in ("name", "description"):
        if key in updates:
            assignments.append(f"{key} = %s")
            parameters.append(updates[key].strip())
    assignments.append("updated_at = %s")
    parameters.extend([datetime.now(UTC), project_id])
    with database_connection() as connection:
        connection.execute(
            f"UPDATE projects SET {', '.join(assignments)} WHERE id = %s", parameters  # noqa: S608
        )
    return {"status": "updated"}


@app.delete("/api/projects/{project_id}", status_code=204)
def archive_project(project_id: uuid.UUID) -> Response:
    if project_id == DEFAULT_PROJECT_ID:
        raise HTTPException(status_code=409, detail="Le projet par défaut ne peut pas être archivé")
    ensure_project(project_id)
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            "UPDATE projects SET archived_at = %s, updated_at = %s WHERE id = %s", (now, now, project_id)
        )
        connection.execute(
            "UPDATE schedules SET enabled = FALSE, archived_at = %s, updated_at = %s WHERE project_id = %s",
            (now, now, project_id),
        )
        connection.execute(
            "UPDATE project_geodata_settings SET auto_download = FALSE, updated_at = %s WHERE project_id = %s",
            (now, project_id),
        )
    return Response(status_code=204)


@app.get("/api/projects/{project_id}/preferences")
def project_preferences(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    return get_preferences(project_id)


@app.put("/api/projects/{project_id}/preferences")
def update_preferences(project_id: uuid.UUID, payload: PreferencesUpdate) -> dict[str, Any]:
    ensure_project(project_id)
    values = payload.model_dump()
    values["allowed_formats"] = sorted(
        {item.strip().lower().lstrip(".") for item in values["allowed_formats"] if item.strip()}
    )
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_preferences (project_id, preferences, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET preferences = EXCLUDED.preferences, updated_at = EXCLUDED.updated_at
            """,
            (project_id, Jsonb(values), datetime.now(UTC)),
        )
    return values


@app.get("/api/projects/{project_id}/github")
def project_github(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    return get_github_settings(project_id)


@app.put("/api/projects/{project_id}/github")
def update_project_github(
    project_id: uuid.UUID, payload: GitHubSettingsUpdate
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        owner = validate_github_owner(payload.owner)
        repository_name = validate_repository_name(payload.repository_name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_github_settings
                (project_id, owner, repository_name, description, visibility, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                owner = EXCLUDED.owner,
                repository_name = EXCLUDED.repository_name,
                description = EXCLUDED.description,
                visibility = EXCLUDED.visibility,
                updated_at = EXCLUDED.updated_at
            """,
            (
                project_id,
                owner,
                repository_name,
                payload.description.strip(),
                payload.visibility,
                now,
            ),
        )
    return get_github_settings(project_id)


def github_error_detail(response: httpx.Response) -> str:
    try:
        message = str(response.json().get("message") or "")
    except (ValueError, AttributeError):
        message = ""
    return message[:500] or f"réponse HTTP {response.status_code}"


@app.post("/api/projects/{project_id}/github/repository", status_code=201)
async def create_github_repository(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    if not GITHUB_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Ajoutez GITHUB_TOKEN dans le fichier .env puis redémarrez l'application.",
        )
    settings = get_github_settings(project_id)
    if settings.get("repository_url"):
        raise HTTPException(status_code=409, detail="Un dépôt est déjà associé à ce projet.")
    try:
        repository_name = validate_repository_name(str(settings["repository_name"]))
        owner = validate_github_owner(str(settings["owner"]))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"HDP/{APP_VERSION}",
    }
    async with httpx.AsyncClient(timeout=40, follow_redirects=False, headers=headers) as client:
        user_response = await client.get("https://api.github.com/user")
        if user_response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"GitHub a refusé l'authentification : {github_error_detail(user_response)}",
            )
        authenticated_login = str(user_response.json().get("login") or "")
        if not authenticated_login:
            raise HTTPException(status_code=502, detail="GitHub n'a pas retourné d'identité utilisable.")
        endpoint = github_repository_endpoint(owner, authenticated_login)
        create_response = await client.post(
            endpoint,
            json={
                "name": repository_name,
                "description": str(settings["description"]),
                "private": settings["visibility"] == "private",
                "auto_init": True,
                "has_issues": True,
            },
        )
    if create_response.status_code >= 400:
        status_code = 409 if create_response.status_code == 422 else 502
        raise HTTPException(
            status_code=status_code,
            detail=f"Création du dépôt refusée par GitHub : {github_error_detail(create_response)}",
        )
    repository = create_response.json()
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE project_github_settings
            SET owner = %s, repository_url = %s, repository_full_name = %s,
                created_at = %s, updated_at = %s
            WHERE project_id = %s
            """,
            (
                str(repository.get("owner", {}).get("login") or owner or authenticated_login),
                str(repository.get("html_url") or ""),
                str(repository.get("full_name") or ""),
                now,
                now,
                project_id,
            ),
        )
    return {
        **get_github_settings(project_id),
        "message": "Dépôt créé et initialisé avec un README GitHub.",
    }


@app.get("/api/projects/{project_id}/geodata")
def project_geodata(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    settings = get_geodata_settings(project_id)
    settings["scope"] = (
        m49_scope(settings["m49_scope_code"]) if settings.get("m49_scope_code") else None
    )
    settings["m49_source"] = UN_M49_SOURCE
    settings["official_data_series"] = OFFICIAL_COD_SERIES
    return settings


@app.put("/api/projects/{project_id}/geodata")
def update_project_geodata(
    project_id: uuid.UUID, payload: GeodataSettingsUpdate
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        scope_code = validate_m49_code(payload.m49_scope_code)
        official_policy = validate_official_cod_policy(payload.official_policy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scope = m49_scope(scope_code)
    legacy_scale = "world" if scope_code == "001" else "national" if scope["type"] == 4 else "regional"
    now = datetime.now(UTC)
    current = get_geodata_settings(project_id)
    next_sync = current["next_sync_at"]
    if payload.auto_download and not current["auto_download"]:
        next_sync = now
    elif payload.refresh_interval_minutes != current["refresh_interval_minutes"]:
        next_sync = next_run_at(now, payload.refresh_interval_minutes)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_geodata_settings
                (project_id, auto_download, dataset_id, preferred_format, max_scale,
                 m49_scope_code, official_policy, migration_required,
                 refresh_interval_minutes, next_sync_at, updated_at)
            VALUES (%s, %s, 'official-cod-ab-catalog', %s, %s, %s, %s, FALSE, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                auto_download = EXCLUDED.auto_download,
                dataset_id = EXCLUDED.dataset_id,
                preferred_format = EXCLUDED.preferred_format,
                max_scale = EXCLUDED.max_scale,
                m49_scope_code = EXCLUDED.m49_scope_code,
                official_policy = EXCLUDED.official_policy,
                migration_required = FALSE,
                refresh_interval_minutes = EXCLUDED.refresh_interval_minutes,
                next_sync_at = EXCLUDED.next_sync_at,
                updated_at = EXCLUDED.updated_at
            """,
            (
                project_id,
                payload.auto_download,
                payload.preferred_format,
                legacy_scale,
                scope_code,
                official_policy,
                payload.refresh_interval_minutes,
                next_sync,
                now,
            ),
        )
    return project_geodata(project_id)


@app.post("/api/projects/{project_id}/geodata/sync")
async def sync_project_geodata(project_id: uuid.UUID) -> dict[str, Any]:
    return await execute_geodata_sync(project_id)


@app.get("/api/search", response_model=SearchResponse)
async def search(
    project_id: uuid.UUID,
    source: str = Query(pattern="^(reliefweb|hdx)$"),
    query: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=25, ge=1, le=100),
    auto_download: bool | None = None,
) -> SearchResponse:
    preferences = get_preferences(project_id)
    should_download = preferences["auto_download"] if auto_download is None else auto_download
    return await execute_acquisition(project_id, source, query, limit, should_download)


@app.get("/api/acquisitions")
def acquisitions(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, schedule_id, source, query, retrieved_at, sha256, item_count, raw_path
            FROM acquisitions WHERE project_id = %s ORDER BY retrieved_at DESC LIMIT %s
            """,
            (project_id, limit),
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "schedule_id": str(row[1]) if row[1] else None,
            "source": row[2],
            "query": row[3],
            "retrieved_at": row[4],
            "sha256": row[5],
            "item_count": row[6],
            "raw_path": row[7],
        }
        for row in rows
    ]


@app.get("/api/resources")
def resources(
    project_id: uuid.UUID,
    status: str | None = Query(default=None, pattern="^(queued|downloading|completed|failed|deleted)$"),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    where = "project_id = %s"
    parameters: list[Any] = [project_id]
    if status:
        where += " AND status = %s"
        parameters.append(status)
    else:
        where += " AND deleted_at IS NULL"
    parameters.append(limit)
    with database_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, acquisition_id, source, dataset_id, resource_id, title, url, format,
                   filename, local_path, sha256, size_bytes, content_type, status, error,
                   created_at, updated_at, deleted_at, m49_code, iso3_code, cod_level,
                   publisher, license_id, dataset_modified_at
            FROM local_resources WHERE {where} ORDER BY updated_at DESC LIMIT %s
            """,  # noqa: S608
            parameters,
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "acquisition_id": str(row[1]),
            "source": row[2],
            "dataset_id": row[3],
            "resource_id": row[4],
            "title": row[5],
            "url": row[6],
            "format": row[7],
            "filename": row[8],
            "local_path": row[9],
            "sha256": row[10],
            "size_bytes": row[11],
            "content_type": row[12],
            "status": row[13],
            "error": row[14],
            "created_at": row[15],
            "updated_at": row[16],
            "deleted_at": row[17],
            "m49_code": row[18],
            "iso3_code": row[19],
            "cod_level": row[20],
            "publisher": row[21],
            "license_id": row[22],
            "dataset_modified_at": row[23],
        }
        for row in rows
    ]


def resource_row(resource_id: uuid.UUID) -> tuple[Any, ...]:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT id, project_id, filename, local_path, sha256, size_bytes, status FROM local_resources WHERE id = %s",
            (resource_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ressource locale introuvable")
    return row


@app.get("/api/resources/{resource_id}/file")
def resource_file(resource_id: uuid.UUID) -> FileResponse:
    row = resource_row(resource_id)
    if row[6] != "completed" or not row[3]:
        raise HTTPException(status_code=409, detail="Le fichier n'est pas disponible localement")
    try:
        path = confined_path(DATA_DIR, row[3])
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Le fichier local a disparu")
    return FileResponse(path, filename=row[2] or path.name)


@app.post("/api/resources/{resource_id}/verify")
def verify_resource(resource_id: uuid.UUID) -> dict[str, Any]:
    row = resource_row(resource_id)
    if row[6] != "completed" or not row[3] or not row[4]:
        raise HTTPException(status_code=409, detail="Aucune empreinte locale vérifiable")
    try:
        path = confined_path(DATA_DIR, row[3])
        digest = sha256_file(path)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=404, detail=f"Fichier local inaccessible: {exc}") from exc
    return {"id": str(resource_id), "valid": digest == row[4], "expected": row[4], "actual": digest}


@app.delete("/api/resources/{resource_id}", status_code=204)
def delete_resource(resource_id: uuid.UUID) -> Response:
    row = resource_row(resource_id)
    if row[3]:
        try:
            confined_path(DATA_DIR, row[3]).unlink(missing_ok=True)
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=409, detail=f"Suppression refusée: {exc}") from exc
    now = datetime.now(UTC)
    update_resource(resource_id, "deleted", deleted_at=now, local_path=None)
    return Response(status_code=204)


@app.get("/api/projects/{project_id}/storage")
def storage(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(size_bytes), 0),
                   COUNT(*) FILTER (WHERE status = 'completed'),
                   COUNT(*) FILTER (WHERE status = 'failed')
            FROM local_resources WHERE project_id = %s AND deleted_at IS NULL
            """,
            (project_id,),
        ).fetchone()
    return {"resource_count": row[0], "size_bytes": row[1], "completed": row[2], "failed": row[3]}


@app.get("/api/projects/{project_id}/scripts")
def scripts(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, language, content, description, created_at, updated_at
            FROM project_scripts WHERE project_id = %s AND archived_at IS NULL ORDER BY updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [
        {
            "id": str(row[0]), "name": row[1], "language": row[2], "content": row[3],
            "description": row[4], "created_at": row[5], "updated_at": row[6],
            "execution": "disabled",
        }
        for row in rows
    ]


@app.post("/api/projects/{project_id}/scripts", status_code=201)
def create_script(project_id: uuid.UUID, payload: ScriptCreate) -> dict[str, str]:
    ensure_project(project_id)
    script_id, now = uuid.uuid4(), datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_scripts
                (id, project_id, name, language, content, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (script_id, project_id, payload.name.strip(), payload.language, payload.content, payload.description, now, now),
        )
    return {"id": str(script_id), "status": "created"}


@app.patch("/api/scripts/{script_id}")
def update_script(script_id: uuid.UUID, payload: ScriptPatch) -> dict[str, str]:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return {"status": "unchanged"}
    assignments, parameters = [], []
    for key in ("name", "language", "content", "description"):
        if key in updates:
            assignments.append(f"{key} = %s")
            parameters.append(updates[key])
    assignments.append("updated_at = %s")
    parameters.extend([datetime.now(UTC), script_id])
    with database_connection() as connection:
        result = connection.execute(
            f"UPDATE project_scripts SET {', '.join(assignments)} WHERE id = %s AND archived_at IS NULL",  # noqa: S608
            parameters,
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Script introuvable")
    return {"status": "updated"}


@app.delete("/api/scripts/{script_id}", status_code=204)
def archive_script(script_id: uuid.UUID) -> Response:
    now = datetime.now(UTC)
    with database_connection() as connection:
        result = connection.execute(
            "UPDATE project_scripts SET archived_at = %s, updated_at = %s WHERE id = %s AND archived_at IS NULL",
            (now, now, script_id),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Script introuvable")
    return Response(status_code=204)


@app.get("/api/projects/{project_id}/schedules")
def schedules(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, source, query, result_limit, auto_download, interval_minutes,
                   enabled, next_run_at, last_run_at, last_status, last_error, created_at, updated_at
            FROM schedules WHERE project_id = %s AND archived_at IS NULL ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    keys = [
        "id", "name", "source", "query", "result_limit", "auto_download", "interval_minutes",
        "enabled", "next_run_at", "last_run_at", "last_status", "last_error", "created_at", "updated_at",
    ]
    return [dict(zip(keys, (str(row[0]), *row[1:]))) for row in rows]


@app.post("/api/projects/{project_id}/schedules", status_code=201)
def create_schedule(project_id: uuid.UUID, payload: ScheduleCreate) -> dict[str, Any]:
    ensure_project(project_id)
    validate_interval(payload.interval_minutes)
    schedule_id, now = uuid.uuid4(), datetime.now(UTC)
    first_run = now if payload.enabled else next_run_at(now, payload.interval_minutes)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO schedules
                (id, project_id, name, source, query, result_limit, auto_download, interval_minutes,
                 enabled, next_run_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                schedule_id, project_id, payload.name.strip(), payload.source, payload.query.strip(),
                payload.result_limit, payload.auto_download, payload.interval_minutes, payload.enabled,
                first_run, now, now,
            ),
        )
    return {"id": str(schedule_id), "next_run_at": first_run, "status": "created"}


@app.patch("/api/schedules/{schedule_id}")
def update_schedule(schedule_id: uuid.UUID, payload: SchedulePatch) -> dict[str, str]:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return {"status": "unchanged"}
    if "interval_minutes" in updates:
        validate_interval(updates["interval_minutes"])
    assignments, parameters = [], []
    for key in ("name", "source", "query", "result_limit", "auto_download", "interval_minutes", "enabled"):
        if key in updates:
            assignments.append(f"{key} = %s")
            parameters.append(updates[key])
    now = datetime.now(UTC)
    if "interval_minutes" in updates or updates.get("enabled") is True:
        interval = updates.get("interval_minutes")
        if interval is None:
            with database_connection() as connection:
                row = connection.execute("SELECT interval_minutes FROM schedules WHERE id = %s", (schedule_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Planification introuvable")
            interval = row[0]
        assignments.append("next_run_at = %s")
        parameters.append(next_run_at(now, interval))
    assignments.append("updated_at = %s")
    parameters.extend([now, schedule_id])
    with database_connection() as connection:
        result = connection.execute(
            f"UPDATE schedules SET {', '.join(assignments)} WHERE id = %s AND archived_at IS NULL",  # noqa: S608
            parameters,
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Planification introuvable")
    return {"status": "updated"}


@app.post("/api/schedules/{schedule_id}/run")
async def run_schedule_now(schedule_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, source, query, result_limit, auto_download
            FROM schedules WHERE id = %s AND archived_at IS NULL
            """,
            (schedule_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planification introuvable")
        run_id, now = uuid.uuid4(), datetime.now(UTC)
        connection.execute(
            "INSERT INTO schedule_runs (id, schedule_id, started_at, status) VALUES (%s, %s, %s, 'running')",
            (run_id, schedule_id, now),
        )
    schedule = {
        "run_id": run_id, "id": row[0], "project_id": row[1], "source": row[2],
        "query": row[3], "result_limit": row[4], "auto_download": row[5],
    }
    await execute_claimed_schedule(schedule)
    with database_connection() as connection:
        result = connection.execute(
            "SELECT status, acquisition_id, error FROM schedule_runs WHERE id = %s", (run_id,)
        ).fetchone()
    return {
        "run_id": str(run_id), "status": result[0],
        "acquisition_id": str(result[1]) if result[1] else None, "error": result[2],
    }


@app.delete("/api/schedules/{schedule_id}", status_code=204)
def archive_schedule(schedule_id: uuid.UUID) -> Response:
    now = datetime.now(UTC)
    with database_connection() as connection:
        result = connection.execute(
            """
            UPDATE schedules SET enabled = FALSE, archived_at = %s, updated_at = %s
            WHERE id = %s AND archived_at IS NULL
            """,
            (now, now, schedule_id),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Planification introuvable")
    return Response(status_code=204)


@app.get("/api/schedules/{schedule_id}/runs")
def schedule_history(schedule_id: uuid.UUID, limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, acquisition_id, started_at, finished_at, status, error
            FROM schedule_runs WHERE schedule_id = %s ORDER BY started_at DESC LIMIT %s
            """,
            (schedule_id, limit),
        ).fetchall()
    return [
        {
            "id": str(row[0]), "acquisition_id": str(row[1]) if row[1] else None,
            "started_at": row[2], "finished_at": row[3], "status": row[4], "error": row[5],
        }
        for row in rows
    ]


@app.get("/api/analysis/status")
async def analysis_status() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{R_SERVICE_URL}/health")
            response.raise_for_status()
            return {"r_service": response.json()}
    except httpx.HTTPError:
        return {
            "r_service": {
                "status": "not_started",
                "message": "Le module R est optionnel et peut être installé en relançant l'installateur.",
            }
        }
