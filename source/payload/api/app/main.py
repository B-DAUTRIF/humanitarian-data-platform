from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import re
import time
import uuid
from contextlib import suppress
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import httpx
import psycopg
from fastapi import FastAPI, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from .federated_search import filter_catalog_items, unified_federated_items
from .health_sources import (
    SOURCE_PATTERN,
    parse_dhs_indicators,
    parse_un_sdg_indicators,
    parse_unicef_dataflows,
    parse_who_indicators,
    parse_world_bank_indicators,
    source_catalog,
)
from .humanitarian_sources import (
    parse_gdacs_events,
    parse_hapi_rows,
    parse_unhcr_population,
)
from .local_library import (
    normalize_update_frequency,
    script_language,
    validate_upload_content,
    validate_upload_category,
)
from .migrations import apply_migrations
from .map_utils import export_bundle, load_geojson, safe_layer_name
from .project_integrations import (
    OFFICIAL_COD_CATALOG_QUERIES,
    OFFICIAL_COD_FAMILIES,
    UN_M49_SOURCE,
    geodata_profile_changed,
    github_repository_endpoint,
    m49_scope,
    official_cod_availability,
    official_cod_family_catalog,
    select_cod_resources,
    select_official_cod_datasets,
    un_m49_catalog,
    validate_cod_families,
    validate_github_owner,
    validate_hdx_dataset_id,
    validate_m49_country_code,
    validate_official_cod_policy,
    validate_repository_name,
)
from .processing_recipes import (
    RecipeError,
    generate_python_script,
    generate_r_script,
    operation_catalog,
    run_delimited_recipe,
    validate_recipe,
)
from .scheduler_utils import MIN_INTERVAL_MINUTES, next_run_at, validate_interval
from .rss_registry import MAX_RSS_BYTES, build_rss_url, parse_rss, rss_catalog, rss_definition
from .security import (
    confined_path,
    resource_key,
    safe_filename,
    safe_query_fragment,
    sha256_file,
    validate_public_url,
)
from .source_registry import (
    CONNECTORS,
    connector_definition,
    merge_values,
    request_preview,
    validate_values,
)
from .sql_workspace import ALLOWED_SQL_RELATIONS, validate_readonly_sql
from .script_runtime import (
    TERMINAL_STATUSES,
    ensure_spool_layout,
    heartbeat_status,
    prepare_execution_job,
    read_execution_result,
    script_sha256,
    validate_execution_request,
    write_execution_report,
)


APP_NAME = "Humanitarian Data Platform"
APP_VERSION = "4.0.0"
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
EXECUTION_SPOOL_DIR = Path(os.getenv("EXECUTION_SPOOL_DIR", "/app/execution_spool"))
DATABASE_URL = os.environ["DATABASE_URL"]
R_SERVICE_URL = os.getenv("R_SERVICE_URL", "http://r-service:8001")
RELIEFWEB_APPNAME = os.getenv("RELIEFWEB_APPNAME", "").strip()
HDX_HAPI_APP_IDENTIFIER = os.getenv("HDX_HAPI_APP_IDENTIFIER", "").strip()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
HDP_TILE_URL = os.getenv(
    "HDP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
).strip()
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
COD_CATALOG_CACHE_SECONDS = 1_800
MAX_UPLOAD_BYTES = min(
    max(int(os.getenv("HDP_MAX_UPLOAD_BYTES", "536870912")), 1_048_576),
    2_147_483_648,
)
cod_catalog_cache: dict[str, tuple[float, dict[str, Any], list[dict[str, Any]]]] = {}

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Acquisition, téléchargement et gestion locale de ressources humanitaires par projets.",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
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
    cod_families: list[str] = Field(default_factory=lambda: ["cod-ab"], min_length=1, max_length=3)
    m49_scope_code: str = Field(pattern=r"^\d{3}$")
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


class ExecutionSettingsUpdate(BaseModel):
    python_enabled: bool = True
    r_enabled: bool = False
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_output_bytes: int = Field(default=262_144, ge=1_024, le=1_048_576)
    network_enabled: bool = False
    allowed_hosts: list[str] = Field(default_factory=list, max_length=50)


class ScriptExecutionCreate(BaseModel):
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    max_output_bytes: int | None = Field(default=None, ge=1_024, le=1_048_576)
    network_enabled: bool = False
    allowed_hosts: list[str] = Field(default_factory=list, max_length=50)


class RssSubscriptionCreate(BaseModel):
    registry_id: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    query: str = Field(default="", max_length=200)
    language: str = Field(default="en", pattern="^(en|fr|es)$")
    interval_minutes: int = Field(default=360, ge=15, le=43_200)
    enabled: bool = True


class RssSubscriptionPatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    query: str | None = Field(default=None, max_length=200)
    language: str | None = Field(default=None, pattern="^(en|fr|es)$")
    interval_minutes: int | None = Field(default=None, ge=15, le=43_200)
    enabled: bool | None = None


class ScheduleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    source: str = Field(pattern=SOURCE_PATTERN)
    query: str = Field(min_length=2, max_length=200)
    result_limit: int = Field(default=25, ge=1, le=100)
    auto_download: bool = False
    interval_minutes: int = Field(default=1440, ge=MIN_INTERVAL_MINUTES, le=43_200)
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)


class SchedulePatch(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    source: str | None = Field(default=None, pattern=SOURCE_PATTERN)
    query: str | None = Field(default=None, min_length=2, max_length=200)
    result_limit: int | None = Field(default=None, ge=1, le=100)
    auto_download: bool | None = None
    interval_minutes: int | None = Field(default=None, ge=MIN_INTERVAL_MINUTES, le=43_200)
    enabled: bool | None = None
    parameters: dict[str, Any] | None = None


class SourceGlobalSettingsUpdate(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class ProjectSourceSettingsUpdate(BaseModel):
    enabled: bool = True
    parameters: dict[str, Any] = Field(default_factory=dict)
    schedule_defaults: dict[str, Any] = Field(default_factory=dict)


class AcquisitionCreate(BaseModel):
    project_id: uuid.UUID
    source: str = Field(pattern=SOURCE_PATTERN)
    parameters: dict[str, Any] = Field(default_factory=dict)
    auto_download: bool | None = None


class FederatedSearchCreate(BaseModel):
    sources: list[str] = Field(min_length=2, max_length=20)
    query: str = Field(min_length=2, max_length=200)
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    location: str = Field(default="", max_length=160)
    result_limit_per_source: int = Field(default=25, ge=1, le=100)
    auto_download: bool | None = None
    source_parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)


class ResourceRefreshScheduleCreate(BaseModel):
    interval_minutes: int = Field(default=1440, ge=MIN_INTERVAL_MINUTES, le=43_200)
    enabled: bool = True


class ResourceRefreshSchedulePatch(BaseModel):
    interval_minutes: int | None = Field(
        default=None, ge=MIN_INTERVAL_MINUTES, le=43_200
    )
    enabled: bool | None = None


class SqlQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=20_000)
    max_rows: int = Field(default=200, ge=1, le=1000)


class ProcessingRunCreate(BaseModel):
    resource_id: uuid.UUID
    name: str = Field(min_length=2, max_length=120)
    output_title: str = Field(min_length=2, max_length=160)
    recipe: dict[str, Any]
    script_language: str = Field(default="python", pattern="^(python|r)$")
    delimiter: str | None = Field(default=None, max_length=1)
    max_rows: int = Field(default=5_000_000, ge=1, le=20_000_000)


class SourceParametersPreview(BaseModel):
    parameters: dict[str, Any] = Field(default_factory=dict)


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
    parameters: dict[str, Any]


def database_connection(*, autocommit: bool = True) -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit)


def initialize_database() -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with database_connection(autocommit=False) as connection:
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
                        cod_families JSONB NOT NULL DEFAULT '["cod-ab"]'::jsonb,
                        official_policy TEXT NOT NULL DEFAULT 'enhanced_preferred',
                        migration_required BOOLEAN NOT NULL DEFAULT TRUE,
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
                    ADD COLUMN IF NOT EXISTS cod_families JSONB NOT NULL DEFAULT '["cod-ab"]'::jsonb
                    """
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
                    "ALTER TABLE project_geodata_settings ALTER COLUMN m49_scope_code DROP DEFAULT"
                )
                connection.execute(
                    "ALTER TABLE project_geodata_settings ALTER COLUMN migration_required SET DEFAULT TRUE"
                )
                country_codes = [
                    str(entity["code"])
                    for entity in un_m49_catalog()
                    if int(entity["type"]) == 4 and entity.get("iso3")
                ]
                connection.execute(
                    """
                    UPDATE project_geodata_settings
                    SET migration_required = TRUE, auto_download = FALSE,
                        last_status = 'migration_required',
                        last_error = 'Choisissez un pays ou une zone dans la liste ONU M49 × HDX COD.'
                    WHERE m49_scope_code IS NULL OR NOT (m49_scope_code = ANY(%s))
                    """,
                    (country_codes,),
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
                        cod_family TEXT,
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
                    "cod_family TEXT",
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
                apply_migrations(connection, now)
                connection.execute(
                    """
                    INSERT INTO project_execution_settings (project_id, updated_at)
                    SELECT id, %s FROM projects
                    ON CONFLICT (project_id) DO NOTHING
                    """,
                    (now,),
                )
                legacy_scripts = connection.execute(
                    """
                    SELECT s.id, s.project_id, s.name, s.language, s.description,
                           s.content, s.created_at
                    FROM project_scripts s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM script_versions v WHERE v.script_id = s.id
                    )
                    """
                ).fetchall()
                for script in legacy_scripts:
                    connection.execute(
                        """
                        INSERT INTO script_versions
                            (id, script_id, project_id, version_number, name, language,
                             description, content, content_sha256, created_at)
                        VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            uuid.uuid4(), script[0], script[1], script[2], script[3],
                            script[4], script[5], script_sha256(script[5]), script[6],
                        ),
                    )
                for source in source_catalog():
                    connection.execute(
                        """
                        INSERT INTO source_global_settings (source_id, settings, updated_at)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (source_id) DO NOTHING
                        """,
                        (source["id"], Jsonb(source["global_defaults"]), now),
                    )
                    if source["searchable"]:
                        connection.execute(
                            """
                            INSERT INTO project_source_settings
                                (project_id, source_id, enabled, parameters, schedule_defaults, updated_at)
                            SELECT id, %s, TRUE, %s, '{}'::jsonb, %s FROM projects
                            ON CONFLICT (project_id, source_id) DO NOTHING
                            """,
                            (source["id"], Jsonb(source["project_defaults"]), now),
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
    DATA_DIR.joinpath("uploads").mkdir(parents=True, exist_ok=True)
    ensure_spool_layout(EXECUTION_SPOOL_DIR)
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


def source_metadata(source_id: str) -> dict[str, Any]:
    for source in source_catalog():
        if source["id"] == source_id:
            return source
    raise HTTPException(status_code=404, detail="Source inconnue")


def source_secret_configured(source: dict[str, Any]) -> bool:
    variable = source.get("secret_environment_variable")
    return bool(variable and os.getenv(str(variable), "").strip())


def get_source_global_settings(source_id: str) -> dict[str, Any]:
    source = source_metadata(source_id)
    with database_connection() as connection:
        row = connection.execute(
            "SELECT settings, updated_at FROM source_global_settings WHERE source_id = %s",
            (source_id,),
        ).fetchone()
    stored = row[0] if row else source["global_defaults"]
    try:
        settings = merge_values(source_id, stored, scope="global")
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Configuration source invalide : {exc}") from exc
    return {
        "source_id": source_id,
        "settings": settings,
        "updated_at": row[1] if row else None,
        "secret_environment_variable": source.get("secret_environment_variable"),
        "secret_configured": source_secret_configured(source),
    }


def validate_schedule_defaults(values: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(values, dict):
        raise ValueError("Les valeurs de planification doivent former un objet")
    allowed = {"interval_minutes", "enabled", "auto_download"}
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"Paramètres de planification inconnus : {', '.join(unknown)}")
    result = {
        "interval_minutes": 1440,
        "enabled": True,
        "auto_download": False,
        **values,
    }
    if type(result["interval_minutes"]) is not int:
        raise ValueError("interval_minutes doit être un entier")
    result["interval_minutes"] = validate_interval(result["interval_minutes"])
    for name in ("enabled", "auto_download"):
        if type(result[name]) is not bool:
            raise ValueError(f"{name} doit être booléen")
    return result


def get_project_source_settings(project_id: uuid.UUID, source_id: str) -> dict[str, Any]:
    ensure_project(project_id)
    source = source_metadata(source_id)
    if not source["searchable"]:
        raise HTTPException(status_code=422, detail="Cette source est un portail de référence")
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT enabled, parameters, schedule_defaults, updated_at
            FROM project_source_settings WHERE project_id = %s AND source_id = %s
            """,
            (project_id, source_id),
        ).fetchone()
    try:
        parameters = merge_values(
            source_id, row[1] if row else source["project_defaults"], scope="project"
        )
        schedule_defaults = validate_schedule_defaults(row[2] if row else {})
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Configuration projet invalide : {exc}") from exc
    return {
        "project_id": str(project_id),
        "source_id": source_id,
        "enabled": bool(row[0]) if row else True,
        "parameters": parameters,
        "schedule_defaults": schedule_defaults,
        "updated_at": row[3] if row else None,
    }


def github_token_policy() -> dict[str, Any]:
    token_kind = "none"
    if GITHUB_TOKEN.startswith("github_pat_"):
        token_kind = "fine_grained"
    elif GITHUB_TOKEN.startswith(("ghp_", "gho_", "ghu_", "ghs_", "ghr_")):
        token_kind = "classic_or_app"
    elif GITHUB_TOKEN:
        token_kind = "unknown"
    return {
        "configured": bool(GITHUB_TOKEN),
        "detected_kind": token_kind,
        "recommended_kind": "fine_grained",
        "required_permission": "Administration du dépôt : écriture",
        "resource_owner_constraint": "un seul compte utilisateur ou une seule organisation",
        "expiration_recommended": True,
        "documentation_url": "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
    }


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
            "token_policy": github_token_policy(),
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
        "token_policy": github_token_policy(),
    }


def get_geodata_settings(project_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT auto_download, preferred_format, refresh_interval_minutes,
                   next_sync_at, last_sync_at, last_status, last_error,
                   last_acquisition_id, updated_at, m49_scope_code,
                   official_policy, migration_required, cod_families
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
            "m49_scope_code": None,
            "official_policy": "enhanced_preferred",
            "migration_required": True,
            "cod_families": ["cod-ab"],
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
        "cod_families",
    ]
    values = list(row)
    if values[7]:
        values[7] = str(values[7])
    return dict(zip(keys, values))


def persist_raw(
    project_id: uuid.UUID,
    source: str,
    query: str,
    payload: Any,
    item_count: int,
    schedule_id: uuid.UUID | None,
    parameters: dict[str, Any] | None = None,
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
                (id, project_id, schedule_id, source, query, retrieved_at, sha256,
                 item_count, raw_path, parameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                Jsonb(parameters or {}),
            ),
        )
        connection.execute(
            """
            INSERT INTO data_artifacts
                (id, project_id, stage, acquisition_id, path, sha256,
                 media_type, metadata, created_at)
            VALUES (%s, %s, 'raw', %s, %s, %s, 'application/json', %s, %s)
            """,
            (
                uuid.uuid4(),
                project_id,
                acquisition_id,
                str(relative),
                digest,
                Jsonb({"source": source, "query": query, "item_count": item_count}),
                retrieved_at,
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


async def request_connector_json(
    source: str,
    parameters: dict[str, Any],
    global_settings: dict[str, Any],
) -> Any:
    preview = request_preview(source, parameters)
    query_parameters = dict(preview["query_parameters"])
    if source == "reliefweb":
        if not RELIEFWEB_APPNAME:
            raise HTTPException(
                status_code=503,
                detail=(
                    "ReliefWeb exige un appname pré-approuvé. Ajoutez RELIEFWEB_APPNAME "
                    "dans le fichier .env puis redémarrez l'application."
                ),
            )
        query_parameters["appname"] = RELIEFWEB_APPNAME
    if source == "hdx-hapi":
        if not HDX_HAPI_APP_IDENTIFIER:
            raise HTTPException(
                status_code=503,
                detail=(
                    "HAPI exige un identifiant d’application. Ajoutez "
                    "HDX_HAPI_APP_IDENTIFIER dans le fichier .env puis redémarrez "
                    "l’application."
                ),
            )
        query_parameters["app_identifier"] = HDX_HAPI_APP_IDENTIFIER
    timeout = httpx.Timeout(float(global_settings["timeout_seconds"]), connect=20)
    retries = int(global_settings["retry_count"])
    backoff = int(global_settings["backoff_seconds"])
    last_error: httpx.HTTPError | None = None
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(preview["url"], params=query_parameters)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            last_error = exc
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retryable = status is None or status == 429 or status >= 500
            if attempt >= retries or not retryable:
                raise
            await asyncio.sleep(backoff * (2**attempt))
    raise RuntimeError("Échec du connecteur sans erreur HTTP") from last_error


def normalize_hdx_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not payload.get("success"):
        raise ValueError("Réponse CKAN signalée en échec")
    items = []
    for row in payload.get("result", {}).get("results", []):
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
        organization = row.get("organization") or {}
        items.append(
            {
                "id": row.get("id"),
                "title": row.get("title") or row.get("name"),
                "date": row.get("metadata_modified"),
                "url": f"https://data.humdata.org/dataset/{row.get('name')}",
                "source": "HDX/CKAN",
                "organization": organization.get("title") or organization.get("name"),
                "license": row.get("license_id") or row.get("license_title"),
                "geographic_scope": ", ".join(
                    filter(None, (group.get("title") or group.get("name") for group in row.get("groups", [])))
                ),
                "resources": resources,
            }
        )
    return items


def normalize_reliefweb_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for row in payload.get("data", []):
        fields = row.get("fields", {})
        sources = fields.get("source") or []
        countries = fields.get("country") or []
        items.append(
            {
                "id": row.get("id"),
                "title": fields.get("title"),
                "date": fields.get("date", {}).get("created"),
                "url": fields.get("url_alias") or row.get("href"),
                "source": "ReliefWeb",
                "organization": ", ".join(
                    filter(None, (item.get("name") for item in sources if isinstance(item, dict)))
                ),
                "geographic_scope": ", ".join(
                    filter(None, (item.get("name") for item in countries if isinstance(item, dict)))
                ),
                "resources": reliefweb_files(fields),
            }
        )
    return items


async def search_remote_source(
    source: str,
    parameters: dict[str, Any],
    global_settings: dict[str, Any],
) -> tuple[Any, list[dict[str, Any]]]:
    values = validate_values(source, parameters, scope="project")
    payload = await request_connector_json(source, values, global_settings)
    query = values["query"]
    limit = values["result_limit"]
    if source == "hdx":
        return payload, normalize_hdx_items(payload)
    if source == "reliefweb":
        return payload, normalize_reliefweb_items(payload)
    if source == "who-gho":
        return payload, parse_who_indicators(payload, query, limit)
    if source == "world-bank-health":
        return payload, parse_world_bank_indicators(payload, query, limit)
    if source == "unicef-sdmx":
        return payload, parse_unicef_dataflows(payload, query, limit)
    if source == "un-sdg":
        return payload, parse_un_sdg_indicators(payload, query, limit)
    if source == "dhs":
        return payload, parse_dhs_indicators(payload, query, limit)
    if source == "hdx-hapi":
        return payload, parse_hapi_rows(payload, values, query, limit)
    if source == "unhcr":
        return payload, parse_unhcr_population(payload, values, query, limit)
    if source == "gdacs":
        preview = request_preview(source, values)
        return payload, parse_gdacs_events(
            payload,
            query,
            limit,
            resource_url=preview["display_url"],
        )
    raise ValueError(f"Source non interrogeable : {source}")


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


async def fetch_hdx_official_cod_catalog(
    family: str, *, use_cache: bool = True
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if family not in OFFICIAL_COD_CATALOG_QUERIES:
        raise ValueError(f"Catalogue HDX indisponible pour {family}")
    cached = cod_catalog_cache.get(family)
    if use_cache and cached and time.monotonic() - cached[0] < COD_CATALOG_CACHE_SECONDS:
        return cached[1], cached[2]
    params = {
        "q": OFFICIAL_COD_CATALOG_QUERIES[family],
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
    catalog = [dataset for dataset in datasets if isinstance(dataset, dict)]
    cod_catalog_cache[family] = (time.monotonic(), payload, catalog)
    return payload, catalog


def format_allowed(resource_format: str | None, allowed: list[str]) -> bool:
    if not allowed:
        return True
    normalized = (resource_format or "").strip().lower().lstrip(".")
    return normalized in {item.strip().lower().lstrip(".") for item in allowed if item.strip()}


def optional_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


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
    parent = resource.get("_hdp_parent")
    if not isinstance(parent, dict):
        parent = {}
    library_metadata = {
        key: value
        for key, value in parent.items()
        if key not in {"resources"} and value not in (None, "", [], {})
    }
    published_at = optional_datetime(parent.get("date"))
    subject = parent.get("subject") or parent.get("title")
    geographic_scope = parent.get("geographic_scope")
    organization = parent.get("organization")
    resource_type = resource.get("format") or parent.get("type")
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
            connection.execute(
                """
                UPDATE local_resources
                SET subject = %s, published_at = %s, geographic_scope = %s,
                    resource_type = %s, organization = %s, metadata = %s,
                    updated_at = %s
                WHERE id = %s
                """,
                (
                    subject,
                    published_at,
                    geographic_scope,
                    resource_type,
                    organization,
                    Jsonb(library_metadata),
                    datetime.now(UTC),
                    existing[0],
                ),
            )
            if existing[2] != "completed":
                connection.execute(
                    """
                    UPDATE local_resources
                    SET acquisition_id = %s, source = %s, dataset_id = %s,
                        m49_code = %s, iso3_code = %s, cod_level = %s,
                        cod_family = %s, publisher = %s, license_id = %s, dataset_modified_at = %s,
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
                        official.get("cod_family"),
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
                 cod_family, dataset_modified_at, subject, published_at, geographic_scope,
                 resource_type, organization, metadata, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, 'queued', %s, %s)
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
                official.get("cod_family"),
                official.get("metadata_modified"),
                subject,
                published_at,
                geographic_scope,
                resource_type,
                organization,
                Jsonb(library_metadata),
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
                candidates.append(
                    (
                        str(item.get("id")) if item.get("id") else None,
                        {**resource, "_hdp_parent": item},
                    )
                )
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
    parameters: dict[str, Any] | None = None,
) -> SearchResponse:
    ensure_project(project_id)
    project_settings = get_project_source_settings(project_id, source)
    if not project_settings["enabled"]:
        raise HTTPException(status_code=409, detail="Cette source est désactivée pour le projet")
    submitted = {**project_settings["parameters"], **(parameters or {})}
    submitted.update({"query": query, "result_limit": limit, "auto_download": auto_download})
    try:
        validated = validate_values(source, submitted, scope="project")
        if len(validated["query"]) < 2:
            raise ValueError("query est trop court pour exécuter une acquisition")
        global_configuration = get_source_global_settings(source)
        global_settings = global_configuration["settings"]
        if not global_settings["enabled"]:
            raise HTTPException(status_code=409, detail="Ce connecteur est désactivé globalement")
        payload, items = await search_remote_source(source, validated, global_settings)
        items = filter_catalog_items(
            items,
            date_from=validated.get("date_from", ""),
            date_to=validated.get("date_to", ""),
            location=validated.get("location", ""),
        )[: validated["result_limit"]]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Source distante indisponible: {exc}") from exc

    provenance = persist_raw(
        project_id, source, validated["query"], payload, len(items), schedule_id, validated
    )
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
        query=validated["query"],
        item_count=len(items),
        items=items,
        downloads=downloads,
        parameters=validated,
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
    try:
        scope_code = validate_m49_country_code(str(profile["m49_scope_code"]))
        policy = validate_official_cod_policy(str(profile["official_policy"]))
        selected_families = validate_cod_families(list(profile.get("cod_families") or ["cod-ab"]))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    preferred_format = str(profile["preferred_format"])
    try:
        fetched = await asyncio.gather(
            *(fetch_hdx_official_cod_catalog(family) for family in selected_families)
        )
    except httpx.HTTPError as exc:
        finish_geodata_sync(project_id, "failed", error=f"Source HDX indisponible: {exc}"[:2000])
        raise HTTPException(status_code=502, detail=f"Source HDX indisponible: {exc}") from exc

    hdx_payloads = {
        family: result[0] for family, result in zip(selected_families, fetched)
    }
    catalogs = {family: result[1] for family, result in zip(selected_families, fetched)}
    candidates_by_family: dict[str, list[dict[str, Any]]] = {}
    missing_by_family: dict[str, list[dict[str, Any]]] = {}
    for family in selected_families:
        candidates, missing = select_official_cod_datasets(
            catalogs[family], scope_code, policy, family
        )
        candidates_by_family[family] = candidates
        if missing:
            missing_by_family[family] = missing

    # The geographic list represents an intersection: do not silently download a partial family set.
    datasets = [] if missing_by_family else [
        dataset
        for family in selected_families
        for dataset in candidates_by_family[family]
    ]
    items: list[dict[str, Any]] = []
    no_matching_resources: list[dict[str, Any]] = []
    for dataset in datasets:
        official = dict(dataset["_hdp_official"])
        family = str(official["cod_family"])
        selected = []
        for resource in select_cod_resources(
            dataset.get("resources", []), family, preferred_format
        ):
            annotated = dict(resource)
            annotated["_hdp_official"] = official
            selected.append(annotated)
        if not selected:
            no_matching_resources.append(official)
        items.append(
            {
                "id": official["dataset_id"],
                "title": dataset.get("title") or official["dataset_id"],
                "date": dataset.get("metadata_modified"),
                "url": f"https://data.humdata.org/dataset/{official['dataset_id']}",
                "source": f"HDX/CKAN — {OFFICIAL_COD_FAMILIES[family]['label']} officiel",
                "official": official,
                "resources": selected,
            }
        )

    scope = m49_scope(scope_code)
    archived_payload = {
        "hdx_catalog_responses": hdx_payloads,
        "hdp_geographic_profile": {
            "profile": "ONU M49 × familles COD officielles OCHA/HDX",
            "m49_scope": scope,
            "cod_families": selected_families,
            "official_policy": policy,
            "preferred_format": preferred_format,
            "official_data_series": {
                family: OFFICIAL_COD_FAMILIES[family]["data_series"]
                for family in selected_families
            },
            "accepted_cod_levels": ["cod-enhanced"]
            if policy == "enhanced_only"
            else ["cod-enhanced", "cod-standard"],
            "un_m49_source": UN_M49_SOURCE,
            "selected_datasets": [item["official"] for item in items],
            "candidate_datasets_by_family": {
                family: [dataset["_hdp_official"] for dataset in candidates]
                for family, candidates in candidates_by_family.items()
            },
            "missing_m49_entities_by_family": missing_by_family,
            "datasets_without_matching_resource": no_matching_resources,
        },
    }
    provenance = persist_raw(
        project_id,
        "hdx-geodata",
        f"m49-{scope_code}-{'-'.join(selected_families)}-{policy}-{preferred_format}",
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
    for family, missing in missing_by_family.items():
        examples = ", ".join(str(entity["name"]) for entity in missing[:5])
        suffix = "…" if len(missing) > 5 else ""
        warnings.append(
            f"Aucun {OFFICIAL_COD_FAMILIES[family]['label']} officiel admissible pour "
            f"{len(missing)} pays ou zone(s) M49 : {examples}{suffix}"
        )
    if no_matching_resources:
        ab_count = sum(item["cod_family"] == "cod-ab" for item in no_matching_resources)
        ps_count = sum(item["cod_family"] == "cod-ps" for item in no_matching_resources)
        details = []
        if ab_count:
            details.append(f"{ab_count} COD-AB sans format {preferred_format}")
        if ps_count:
            details.append(f"{ps_count} COD-PS sans ressource CSV/XLSX")
        warnings.append(
            "Ressource compatible absente : " + ", ".join(details) + "."
        )

    if missing_by_family:
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
        "cod_families": selected_families,
        "official_policy": policy,
        "preferred_format": preferred_format,
        "acquisition_id": str(acquisition_id),
        "raw_path": provenance["raw_path"],
        "sha256": provenance["sha256"],
        "dataset_count": len(datasets),
        "dataset_counts": {
            family: len(candidates_by_family[family]) if not missing_by_family else 0
            for family in selected_families
        },
        "missing_dataset_count": len(missing_by_family),
        "resource_count": resource_count,
        "downloads": downloads,
        "status": status,
        "warning": warning,
    }


def _rss_subscription(subscription_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, registry_id, name, query, language, interval_minutes,
                   enabled, next_fetch_at, last_fetch_at, last_status, last_error,
                   etag, last_modified, created_at, updated_at
            FROM rss_subscriptions WHERE id = %s AND archived_at IS NULL
            """,
            (subscription_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Abonnement RSS introuvable")
    keys = [
        "id", "project_id", "registry_id", "name", "query", "language",
        "interval_minutes", "enabled", "next_fetch_at", "last_fetch_at",
        "last_status", "last_error", "etag", "last_modified", "created_at", "updated_at",
    ]
    result = dict(zip(keys, row))
    result["id"] = str(result["id"])
    result["project_id"] = str(result["project_id"])
    result["feed"] = rss_definition(result["registry_id"])
    result["feed_url"] = build_rss_url(result["registry_id"], result["query"], result["language"])
    return result


async def fetch_rss_subscription(subscription_id: uuid.UUID) -> dict[str, Any]:
    subscription = _rss_subscription(subscription_id)
    definition = subscription["feed"]
    current_url = subscription["feed_url"]
    conditional_headers = {"User-Agent": f"HDP/{APP_VERSION} RSS"}
    if subscription.get("etag"):
        conditional_headers["If-None-Match"] = str(subscription["etag"])
    if subscription.get("last_modified"):
        conditional_headers["If-Modified-Since"] = str(subscription["last_modified"])
    now = datetime.now(UTC)
    following_fetch = next_run_at(now, int(subscription["interval_minutes"]))
    try:
        payload = b""
        response_headers: dict[str, str] = {}
        status_code = 0
        async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
            for redirect_count in range(4):
                parsed = urlparse(current_url)
                if parsed.hostname not in set(definition["allowed_hosts"]):
                    raise ValueError("Redirection RSS vers un hôte non autorisé")
                validate_public_url(current_url)
                async with client.stream("GET", current_url, headers=conditional_headers) as response:
                    status_code = response.status_code
                    response_headers = dict(response.headers)
                    if status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location or redirect_count >= 3:
                            raise ValueError("Chaîne de redirection RSS invalide")
                        current_url = urljoin(current_url, location)
                        continue
                    if status_code == 304:
                        break
                    response.raise_for_status()
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_RSS_BYTES:
                            raise ValueError("Le flux RSS dépasse la limite de 2 Mio")
                        chunks.append(chunk)
                    payload = b"".join(chunks)
                    break
        if status_code == 304:
            with database_connection() as connection:
                connection.execute(
                    """
                    UPDATE rss_subscriptions
                    SET last_fetch_at = %s, last_status = 'not_modified', last_error = NULL,
                        next_fetch_at = %s, updated_at = %s WHERE id = %s
                    """,
                    (now, following_fetch, now, subscription_id),
                )
            return {**_rss_subscription(subscription_id), "new_items": 0}
        items = parse_rss(payload)
        inserted = 0
        with database_connection(autocommit=False) as connection:
            for item in items:
                result = connection.execute(
                    """
                    INSERT INTO rss_items
                        (id, subscription_id, external_id, title, url, summary,
                         published_at, raw, first_seen_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (subscription_id, external_id) DO NOTHING
                    """,
                    (
                        uuid.uuid4(), subscription_id, item["external_id"], item["title"],
                        item["url"], item["summary"], item["published_at"],
                        Jsonb(item["raw"]), now,
                    ),
                )
                inserted += int(result.rowcount or 0)
            connection.execute(
                """
                UPDATE rss_subscriptions
                SET last_fetch_at = %s, last_status = 'completed', last_error = NULL,
                    etag = %s, last_modified = %s, next_fetch_at = %s,
                    updated_at = %s WHERE id = %s
                """,
                (
                    now, response_headers.get("etag"), response_headers.get("last-modified"),
                    following_fetch, now, subscription_id,
                ),
            )
            connection.commit()
        return {**_rss_subscription(subscription_id), "new_items": inserted, "item_count": len(items)}
    except Exception as exc:
        with database_connection() as connection:
            connection.execute(
                """
                UPDATE rss_subscriptions
                SET last_fetch_at = %s, last_status = 'failed', last_error = %s,
                    next_fetch_at = %s, updated_at = %s
                WHERE id = %s
                """,
                (now, str(exc)[:2000], following_fetch, now, subscription_id),
            )
        raise


def claim_due_rss() -> uuid.UUID | None:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            """
            SELECT r.id, r.interval_minutes
            FROM rss_subscriptions r
            JOIN projects p ON p.id = r.project_id
            WHERE r.enabled = TRUE AND r.archived_at IS NULL AND r.next_fetch_at <= %s
                  AND p.archived_at IS NULL
            ORDER BY r.next_fetch_at ASC FOR UPDATE OF r SKIP LOCKED LIMIT 1
            """,
            (now,),
        ).fetchone()
        if not row:
            connection.commit()
            return None
        connection.execute(
            """
            UPDATE rss_subscriptions
            SET next_fetch_at = %s, last_status = 'running', last_error = NULL, updated_at = %s
            WHERE id = %s
            """,
            (next_run_at(now, int(row[1])), now, row[0]),
        )
        connection.commit()
    return row[0]


@app.get("/api/rss/catalog")
def rss_feed_catalog() -> list[dict[str, Any]]:
    return rss_catalog()


@app.get("/api/projects/{project_id}/rss/subscriptions")
def rss_subscriptions(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id FROM rss_subscriptions
            WHERE project_id = %s AND archived_at IS NULL ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [_rss_subscription(row[0]) for row in rows]


@app.post("/api/projects/{project_id}/rss/subscriptions", status_code=201)
def create_rss_subscription(
    project_id: uuid.UUID, payload: RssSubscriptionCreate
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        rss_definition(payload.registry_id)
        build_rss_url(payload.registry_id, payload.query, payload.language)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    subscription_id, now = uuid.uuid4(), datetime.now(UTC)
    first_fetch = now if payload.enabled else next_run_at(now, payload.interval_minutes)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO rss_subscriptions
                (id, project_id, registry_id, name, query, language, interval_minutes,
                 enabled, next_fetch_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                subscription_id, project_id, payload.registry_id, payload.name.strip(),
                " ".join(payload.query.split()), payload.language, payload.interval_minutes,
                payload.enabled, first_fetch, now, now,
            ),
        )
    return _rss_subscription(subscription_id)


@app.patch("/api/rss/subscriptions/{subscription_id}")
def update_rss_subscription(
    subscription_id: uuid.UUID, payload: RssSubscriptionPatch
) -> dict[str, Any]:
    current = _rss_subscription(subscription_id)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return current
    candidate_query = updates.get("query", current["query"])
    candidate_language = updates.get("language", current["language"])
    try:
        build_rss_url(current["registry_id"], candidate_query, candidate_language)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    assignments: list[str] = []
    parameters: list[Any] = []
    for key in ("name", "query", "language", "interval_minutes", "enabled"):
        if key in updates:
            assignments.append(f"{key} = %s")
            value = " ".join(updates[key].split()) if key in {"name", "query"} else updates[key]
            parameters.append(value)
    now = datetime.now(UTC)
    if "interval_minutes" in updates or updates.get("enabled") is True:
        interval = int(updates.get("interval_minutes", current["interval_minutes"]))
        assignments.append("next_fetch_at = %s")
        parameters.append(next_run_at(now, interval))
    assignments.append("updated_at = %s")
    parameters.extend([now, subscription_id])
    with database_connection() as connection:
        connection.execute(
            f"UPDATE rss_subscriptions SET {', '.join(assignments)} WHERE id = %s AND archived_at IS NULL",  # noqa: S608
            parameters,
        )
    return _rss_subscription(subscription_id)


@app.post("/api/rss/subscriptions/{subscription_id}/fetch")
async def fetch_rss_now(subscription_id: uuid.UUID) -> dict[str, Any]:
    try:
        return await fetch_rss_subscription(subscription_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Lecture RSS impossible : {str(exc)[:500]}") from exc


@app.delete("/api/rss/subscriptions/{subscription_id}", status_code=204)
def archive_rss_subscription(subscription_id: uuid.UUID) -> Response:
    now = datetime.now(UTC)
    with database_connection() as connection:
        result = connection.execute(
            """
            UPDATE rss_subscriptions SET enabled = FALSE, archived_at = %s, updated_at = %s
            WHERE id = %s AND archived_at IS NULL
            """,
            (now, now, subscription_id),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Abonnement RSS introuvable")
    return Response(status_code=204)


@app.get("/api/projects/{project_id}/rss/items")
def rss_items(
    project_id: uuid.UUID,
    subscription_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    parameters: list[Any] = [project_id]
    condition = ""
    if subscription_id:
        condition = "AND i.subscription_id = %s"
        parameters.append(subscription_id)
    parameters.append(limit)
    with database_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT i.id, i.subscription_id, s.name, i.title, i.url, i.summary,
                   i.published_at, i.first_seen_at
            FROM rss_items i
            JOIN rss_subscriptions s ON s.id = i.subscription_id
            WHERE s.project_id = %s {condition}
            ORDER BY COALESCE(i.published_at, i.first_seen_at) DESC LIMIT %s
            """,  # noqa: S608
            parameters,
        ).fetchall()
    return [
        {
            "id": str(row[0]), "subscription_id": str(row[1]), "subscription_name": row[2],
            "title": row[3], "url": row[4], "summary": row[5],
            "published_at": row[6], "first_seen_at": row[7],
        }
        for row in rows
    ]


def claim_due_schedule() -> dict[str, Any] | None:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            """
            SELECT id, project_id, source, query, result_limit, auto_download,
                   interval_minutes, parameters
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
        "parameters": row[7],
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
            schedule.get("parameters"),
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
                   g.preferred_format, g.refresh_interval_minutes, g.migration_required,
                   g.cod_families
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
        "cod_families": row[6],
    }


async def execute_claimed_geodata(settings: dict[str, Any]) -> None:
    try:
        await execute_geodata_sync(settings["project_id"], settings)
    except Exception as exc:  # Keep the persistent scheduler alive and record the failure.
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        finish_geodata_sync(settings["project_id"], "failed", error=str(detail)[:2000])


def claim_due_resource_refresh() -> dict[str, Any] | None:
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        row = connection.execute(
            """
            SELECT r.id, r.project_id, r.resource_id, r.mode, r.interval_minutes,
                   lr.source, a.query, a.parameters
            FROM resource_refresh_schedules r
            JOIN local_resources lr ON lr.id = r.resource_id
            JOIN acquisitions a ON a.id = lr.acquisition_id
            WHERE r.enabled = TRUE AND r.archived_at IS NULL
                  AND r.next_run_at <= %s AND lr.deleted_at IS NULL
            ORDER BY r.next_run_at ASC FOR UPDATE OF r SKIP LOCKED LIMIT 1
            """,
            (now,),
        ).fetchone()
        if not row:
            connection.commit()
            return None
        run_id = uuid.uuid4()
        connection.execute(
            """
            UPDATE resource_refresh_schedules
            SET next_run_at = %s, last_status = 'running', last_error = NULL,
                updated_at = %s
            WHERE id = %s
            """,
            (next_run_at(now, row[4]), now, row[0]),
        )
        connection.execute(
            """
            INSERT INTO resource_refresh_runs
                (id, refresh_schedule_id, started_at, status)
            VALUES (%s, %s, %s, 'running')
            """,
            (run_id, row[0], now),
        )
        connection.commit()
    return {
        "run_id": run_id,
        "id": row[0],
        "project_id": row[1],
        "resource_id": row[2],
        "mode": row[3],
        "source": row[5],
        "query": row[6],
        "parameters": row[7] or {},
    }


def finish_resource_refresh(
    schedule_id: uuid.UUID,
    run_id: uuid.UUID,
    status: str,
    *,
    acquisition_id: uuid.UUID | None = None,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE resource_refresh_runs
            SET acquisition_id = %s, finished_at = %s, status = %s, error = %s
            WHERE id = %s
            """,
            (acquisition_id, now, status, error, run_id),
        )
        connection.execute(
            """
            UPDATE resource_refresh_schedules
            SET last_run_at = %s, last_status = %s, last_error = %s, updated_at = %s
            WHERE id = %s
            """,
            (now, status, error, now, schedule_id),
        )


async def execute_claimed_resource_refresh(schedule: dict[str, Any]) -> None:
    if schedule["mode"] == "manual_replacement":
        finish_resource_refresh(schedule["id"], schedule["run_id"], "awaiting_upload")
        return
    parameters = dict(schedule.get("parameters") or {})
    query = str(parameters.get("query") or schedule["query"] or "")
    limit = int(parameters.get("result_limit") or 25)
    try:
        result = await execute_acquisition(
            schedule["project_id"],
            schedule["source"],
            query,
            limit,
            True,
            parameters=parameters,
        )
        finish_resource_refresh(
            schedule["id"],
            schedule["run_id"],
            "completed",
            acquisition_id=uuid.UUID(result.acquisition_id),
        )
    except Exception as exc:  # Keep other refresh schedules operational.
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        finish_resource_refresh(
            schedule["id"], schedule["run_id"], "failed", error=str(detail)[:2000]
        )


async def scheduler_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(collect_pending_executions)
            schedule = await asyncio.to_thread(claim_due_schedule)
            if schedule:
                await execute_claimed_schedule(schedule)
                continue
            resource_refresh = await asyncio.to_thread(claim_due_resource_refresh)
            if resource_refresh:
                await execute_claimed_resource_refresh(resource_refresh)
                continue
            geodata = await asyncio.to_thread(claim_due_geodata)
            if geodata:
                await execute_claimed_geodata(geodata)
                continue
            rss_subscription_id = await asyncio.to_thread(claim_due_rss)
            if rss_subscription_id:
                try:
                    await fetch_rss_subscription(rss_subscription_id)
                except Exception:
                    pass
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
        "runners": {
            "python": heartbeat_status(EXECUTION_SPOOL_DIR, "python"),
            "r": heartbeat_status(EXECUTION_SPOOL_DIR, "r"),
        },
    }


@app.get("/api/projects/{project_id}/sql/schema")
def sql_schema(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT table_name, column_name, data_type, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ANY(%s)
            ORDER BY table_name, ordinal_position
            """,
            (list(sorted(ALLOWED_SQL_RELATIONS)),),
        ).fetchall()
    views: dict[str, list[dict[str, str]]] = {}
    for table_name, column_name, data_type, _ in rows:
        views.setdefault(table_name, []).append(
            {"name": column_name, "type": data_type}
        )
    return {
        "engine": "PostgreSQL/PostGIS",
        "access": "read_only",
        "project_id": str(project_id),
        "max_rows": 1000,
        "statement_timeout_ms": 5000,
        "views": views,
        "examples": [
            "SELECT source, count(*) AS resources FROM hdp_resources GROUP BY source ORDER BY resources DESC",
            "SELECT stage, count(*) AS artifacts FROM hdp_artifacts GROUP BY stage",
            "SELECT * FROM hdp_acquisitions ORDER BY retrieved_at DESC LIMIT 20",
        ],
    }


def record_sql_audit(
    project_id: uuid.UUID,
    query: str,
    status: str,
    row_count: int,
    duration_ms: int,
    error: str | None = None,
) -> None:
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO sql_query_audit
                (id, project_id, query_sha256, status, row_count,
                 duration_ms, error, executed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                uuid.uuid4(),
                project_id,
                hashlib.sha256(query.encode("utf-8")).hexdigest(),
                status,
                row_count,
                duration_ms,
                error,
                datetime.now(UTC),
            ),
        )


@app.post("/api/projects/{project_id}/sql/query")
def execute_sql_query(
    project_id: uuid.UUID,
    payload: SqlQueryRequest,
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        query = validate_readonly_sql(payload.query)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    started = time.perf_counter()
    try:
        with database_connection(autocommit=False) as connection:
            connection.execute("SET TRANSACTION READ ONLY")
            connection.execute("SET LOCAL statement_timeout = '5000ms'")
            connection.execute("SELECT set_config('hdp.project_id', %s, TRUE)", (str(project_id),))
            cursor = connection.execute(query)  # noqa: S608 - strict read-only validator and DB transaction
            columns = [description.name for description in (cursor.description or [])]
            rows = cursor.fetchmany(payload.max_rows + 1)
        truncated = len(rows) > payload.max_rows
        rows = rows[: payload.max_rows]
        duration_ms = int((time.perf_counter() - started) * 1000)
        record_sql_audit(project_id, query, "completed", len(rows), duration_ms)
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
            "duration_ms": duration_ms,
            "project_id": str(project_id),
        }
    except psycopg.Error as exc:
        duration_ms = int((time.perf_counter() - started) * 1000)
        error = str(exc).splitlines()[0][:500]
        record_sql_audit(project_id, query, "failed", 0, duration_ms, error)
        raise HTTPException(status_code=422, detail=f"Requête SQL refusée ou invalide : {error}") from exc


@app.get("/api/sources")
def sources() -> list[dict[str, Any]]:
    return source_catalog()


@app.get("/api/source-settings")
def source_settings() -> list[dict[str, Any]]:
    return [
        {**source, "configuration": get_source_global_settings(source["id"])}
        for source in source_catalog()
    ]


@app.get("/api/source-settings/{source_id}")
def source_setting(source_id: str) -> dict[str, Any]:
    source = source_metadata(source_id)
    return {**source, "configuration": get_source_global_settings(source_id)}


@app.put("/api/source-settings/{source_id}")
def update_source_setting(
    source_id: str, payload: SourceGlobalSettingsUpdate
) -> dict[str, Any]:
    source_metadata(source_id)
    try:
        settings = validate_values(source_id, payload.settings, scope="global")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO source_global_settings (source_id, settings, updated_at)
            VALUES (%s, %s, %s)
            ON CONFLICT (source_id) DO UPDATE
            SET settings = EXCLUDED.settings, updated_at = EXCLUDED.updated_at
            """,
            (source_id, Jsonb(settings), now),
        )
    return get_source_global_settings(source_id)


@app.get("/api/projects/{project_id}/sources")
def project_sources(project_id: uuid.UUID) -> list[dict[str, Any]]:
    return [
        get_project_source_settings(project_id, source["id"])
        for source in source_catalog()
        if source["searchable"]
    ]


@app.get("/api/projects/{project_id}/sources/{source_id}")
def project_source(project_id: uuid.UUID, source_id: str) -> dict[str, Any]:
    return get_project_source_settings(project_id, source_id)


@app.put("/api/projects/{project_id}/sources/{source_id}")
def update_project_source(
    project_id: uuid.UUID,
    source_id: str,
    payload: ProjectSourceSettingsUpdate,
) -> dict[str, Any]:
    ensure_project(project_id)
    source = source_metadata(source_id)
    if not source["searchable"]:
        raise HTTPException(status_code=422, detail="Cette source est un portail de référence")
    try:
        parameters = validate_values(source_id, payload.parameters, scope="project")
        schedule_defaults = validate_schedule_defaults(payload.schedule_defaults)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_source_settings
                (project_id, source_id, enabled, parameters, schedule_defaults, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (project_id, source_id) DO UPDATE
            SET enabled = EXCLUDED.enabled, parameters = EXCLUDED.parameters,
                schedule_defaults = EXCLUDED.schedule_defaults,
                updated_at = EXCLUDED.updated_at
            """,
            (
                project_id,
                source_id,
                payload.enabled,
                Jsonb(parameters),
                Jsonb(schedule_defaults),
                now,
            ),
        )
    return get_project_source_settings(project_id, source_id)


@app.post("/api/projects/{project_id}/sources/{source_id}/preview")
def preview_project_source(
    project_id: uuid.UUID,
    source_id: str,
    payload: SourceParametersPreview,
) -> dict[str, Any]:
    stored = get_project_source_settings(project_id, source_id)
    if not stored["enabled"]:
        raise HTTPException(status_code=409, detail="Cette source est désactivée pour le projet")
    try:
        parameters = validate_values(
            source_id, {**stored["parameters"], **payload.parameters}, scope="project"
        )
        preview = request_preview(source_id, parameters)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "project_id": str(project_id),
        "source_id": source_id,
        "parameters": parameters,
        "request": preview,
    }


@app.get("/api/un-m49/entities")
def un_m49_entities() -> dict[str, Any]:
    return {"source": UN_M49_SOURCE, "entities": un_m49_catalog()}


@app.get("/api/cod/families")
def cod_families() -> dict[str, Any]:
    return {
        "families": official_cod_family_catalog(),
        "official_reference": "https://knowledge.base.unocha.org/wiki/spaces/imtoolbox/pages/42045911/Common+Operational+Datasets+CODs",
    }


@app.get("/api/cod/availability")
async def cod_availability(
    families: list[str] = Query(default=["cod-ab"]),
) -> dict[str, Any]:
    try:
        selected = validate_cod_families(families)
        fetched = await asyncio.gather(
            *(fetch_hdx_official_cod_catalog(family) for family in selected)
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Catalogue HDX indisponible : {exc}") from exc
    availability = official_cod_availability(
        {family: result[1] for family, result in zip(selected, fetched)}, selected
    )
    return {
        **availability,
        "fetched_at": datetime.now(UTC),
        "m49_source": UN_M49_SOURCE,
        "hdx_source": "https://data.humdata.org/event/cod",
    }


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
        connection.execute(
            "INSERT INTO project_execution_settings (project_id, updated_at) VALUES (%s, %s)",
            (project_id, now),
        )
        for source in source_catalog():
            if source["searchable"]:
                connection.execute(
                    """
                    INSERT INTO project_source_settings
                        (project_id, source_id, enabled, parameters, schedule_defaults, updated_at)
                    VALUES (%s, %s, TRUE, %s, '{}'::jsonb, %s)
                    """,
                    (project_id, source["id"], Jsonb(source["project_defaults"]), now),
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
        connection.execute(
            "UPDATE rss_subscriptions SET enabled = FALSE, archived_at = %s, updated_at = %s WHERE project_id = %s AND archived_at IS NULL",
            (now, now, project_id),
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
        "X-GitHub-Api-Version": "2026-03-10",
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
    settings["official_families"] = official_cod_family_catalog()
    return settings


@app.put("/api/projects/{project_id}/geodata")
def update_project_geodata(
    project_id: uuid.UUID, payload: GeodataSettingsUpdate
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        scope_code = validate_m49_country_code(payload.m49_scope_code)
        selected_families = validate_cod_families(payload.cod_families)
        official_policy = validate_official_cod_policy(payload.official_policy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scope = m49_scope(scope_code)
    legacy_scale = "national"
    now = datetime.now(UTC)
    current = get_geodata_settings(project_id)
    profile_changed = geodata_profile_changed(
        current, scope_code, official_policy, payload.preferred_format, selected_families
    )
    next_sync = current["next_sync_at"]
    if payload.auto_download and (not current["auto_download"] or profile_changed):
        next_sync = now
    elif payload.refresh_interval_minutes != current["refresh_interval_minutes"]:
        next_sync = next_run_at(now, payload.refresh_interval_minutes)
    last_sync_at = None if profile_changed else current["last_sync_at"]
    last_status = "sync_required" if profile_changed else current["last_status"]
    last_error = None if profile_changed else current["last_error"]
    last_acquisition_id = (
        None
        if profile_changed or not current["last_acquisition_id"]
        else uuid.UUID(str(current["last_acquisition_id"]))
    )
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_geodata_settings
                (project_id, auto_download, dataset_id, preferred_format, max_scale,
                 m49_scope_code, official_policy, migration_required,
                 cod_families, refresh_interval_minutes, next_sync_at, last_sync_at, last_status,
                 last_error, last_acquisition_id, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s, %s,
                    %s, %s, %s, %s, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                auto_download = EXCLUDED.auto_download,
                dataset_id = EXCLUDED.dataset_id,
                preferred_format = EXCLUDED.preferred_format,
                max_scale = EXCLUDED.max_scale,
                m49_scope_code = EXCLUDED.m49_scope_code,
                official_policy = EXCLUDED.official_policy,
                migration_required = FALSE,
                cod_families = EXCLUDED.cod_families,
                refresh_interval_minutes = EXCLUDED.refresh_interval_minutes,
                next_sync_at = EXCLUDED.next_sync_at,
                last_sync_at = EXCLUDED.last_sync_at,
                last_status = EXCLUDED.last_status,
                last_error = EXCLUDED.last_error,
                last_acquisition_id = EXCLUDED.last_acquisition_id,
                updated_at = EXCLUDED.updated_at
            """,
            (
                project_id,
                payload.auto_download,
                "official-" + "+".join(selected_families) + "-catalog",
                payload.preferred_format,
                legacy_scale,
                scope_code,
                official_policy,
                Jsonb(selected_families),
                payload.refresh_interval_minutes,
                next_sync,
                last_sync_at,
                last_status,
                last_error,
                last_acquisition_id,
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
    source: str = Query(pattern=SOURCE_PATTERN),
    query: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=25, ge=1, le=100),
    auto_download: bool | None = None,
) -> SearchResponse:
    preferences = get_preferences(project_id)
    should_download = preferences["auto_download"] if auto_download is None else auto_download
    return await execute_acquisition(project_id, source, query, limit, should_download)


@app.post("/api/acquisitions", response_model=SearchResponse, status_code=201)
async def create_acquisition(payload: AcquisitionCreate) -> SearchResponse:
    stored = get_project_source_settings(payload.project_id, payload.source)
    try:
        parameters = validate_values(
            payload.source,
            {**stored["parameters"], **payload.parameters},
            scope="project",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    preferences = get_preferences(payload.project_id)
    should_download = (
        payload.auto_download
        if payload.auto_download is not None
        else payload.parameters.get("auto_download", preferences["auto_download"])
    )
    return await execute_acquisition(
        payload.project_id,
        payload.source,
        parameters["query"],
        parameters["result_limit"],
        bool(should_download),
        parameters=parameters,
    )


@app.post("/api/projects/{project_id}/federated-search", status_code=201)
async def create_federated_search(
    project_id: uuid.UUID,
    payload: FederatedSearchCreate,
) -> dict[str, Any]:
    ensure_project(project_id)
    sources = list(dict.fromkeys(payload.sources))
    if len(sources) < 2:
        raise HTTPException(status_code=422, detail="Sélectionnez au moins deux sources distinctes")
    unknown_sources = sorted(set(sources) - set(CONNECTORS))
    if unknown_sources:
        raise HTTPException(
            status_code=422,
            detail=f"Sources non interrogeables : {', '.join(unknown_sources)}",
        )
    unknown_parameter_sources = sorted(set(payload.source_parameters) - set(sources))
    if unknown_parameter_sources:
        raise HTTPException(
            status_code=422,
            detail=(
                "Paramètres fournis pour des sources non sélectionnées : "
                + ", ".join(unknown_parameter_sources)
            ),
        )
    try:
        parsed_start = date.fromisoformat(payload.date_from) if payload.date_from else None
        parsed_end = date.fromisoformat(payload.date_to) if payload.date_to else None
        if parsed_start and parsed_end:
            if parsed_start > parsed_end:
                raise HTTPException(
                    status_code=422,
                    detail="date_from doit être antérieure ou égale à date_to",
                )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Date ISO 8601 invalide") from exc

    search_id = uuid.uuid4()
    started_at = datetime.now(UTC)
    criteria = {
        "query": payload.query,
        "date_from": payload.date_from,
        "date_to": payload.date_to,
        "location": payload.location.strip(),
        "result_limit_per_source": payload.result_limit_per_source,
        "auto_download": payload.auto_download,
    }
    should_download = (
        get_preferences(project_id)["auto_download"]
        if payload.auto_download is None
        else payload.auto_download
    )
    criteria["auto_download"] = should_download
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO federated_searches
                (id, project_id, query, criteria, sources, status, started_at)
            VALUES (%s, %s, %s, %s, %s, 'running', %s)
            """,
            (
                search_id,
                project_id,
                payload.query,
                Jsonb(criteria),
                Jsonb(sources),
                started_at,
            ),
        )

    async def run_source(source_id: str) -> tuple[str, SearchResponse | None, str | None]:
        source_parameters = dict(payload.source_parameters.get(source_id) or {})
        source_parameters.update(
            {
                "query": payload.query,
                "date_from": payload.date_from,
                "date_to": payload.date_to,
                "location": payload.location,
                "result_limit": payload.result_limit_per_source,
            }
        )
        try:
            result = await execute_acquisition(
                project_id,
                source_id,
                payload.query,
                payload.result_limit_per_source,
                bool(should_download),
                parameters=source_parameters,
            )
            return source_id, result, None
        except HTTPException as exc:
            return source_id, None, str(exc.detail)[:1000]
        except Exception:
            return source_id, None, "Erreur interne inattendue du connecteur"

    executions = await asyncio.gather(*(run_source(source_id) for source_id in sources))
    successes = [(source_id, result) for source_id, result, _ in executions if result]
    status = "completed" if len(successes) == len(sources) else "partial" if successes else "failed"
    finished_at = datetime.now(UTC)
    with database_connection() as connection:
        for source_id, result, error in executions:
            connection.execute(
                """
                INSERT INTO federated_search_members
                    (search_id, source_id, acquisition_id, status, item_count, error)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    search_id,
                    source_id,
                    uuid.UUID(result.acquisition_id) if result else None,
                    "completed" if result else "failed",
                    result.item_count if result else 0,
                    error,
                ),
            )
        connection.execute(
            """
            UPDATE federated_searches
            SET status = %s, finished_at = %s
            WHERE id = %s
            """,
            (status, finished_at, search_id),
        )

    unified_items = unified_federated_items(
        (source_id, result.items) for source_id, result in successes if result
    )
    return {
        "id": str(search_id),
        "project_id": str(project_id),
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "criteria": criteria,
        "sources": [
            {
                "source_id": source_id,
                "status": "completed" if result else "failed",
                "acquisition_id": result.acquisition_id if result else None,
                "item_count": result.item_count if result else 0,
                "downloads": result.downloads if result else None,
                "error": error,
            }
            for source_id, result, error in executions
        ],
        "item_count": len(unified_items),
        "items": unified_items,
    }


@app.get("/api/projects/{project_id}/federated-searches")
def federated_search_history(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, query, criteria, sources, status, started_at, finished_at
            FROM federated_searches
            WHERE project_id = %s
            ORDER BY started_at DESC LIMIT %s
            """,
            (project_id, limit),
        ).fetchall()
        searches: list[dict[str, Any]] = []
        for row in rows:
            members = connection.execute(
                """
                SELECT source_id, acquisition_id, status, item_count, error
                FROM federated_search_members
                WHERE search_id = %s ORDER BY source_id
                """,
                (row[0],),
            ).fetchall()
            searches.append(
                {
                    "id": str(row[0]),
                    "query": row[1],
                    "criteria": row[2],
                    "sources": row[3],
                    "status": row[4],
                    "started_at": row[5],
                    "finished_at": row[6],
                    "members": [
                        {
                            "source_id": member[0],
                            "acquisition_id": str(member[1]) if member[1] else None,
                            "status": member[2],
                            "item_count": member[3],
                            "error": member[4],
                        }
                        for member in members
                    ],
                }
            )
    return searches


@app.get("/api/acquisitions")
def acquisitions(
    project_id: uuid.UUID,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, schedule_id, source, query, retrieved_at, sha256, item_count,
                   raw_path, parameters
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
            "parameters": row[8],
        }
        for row in rows
    ]


@app.post("/api/projects/{project_id}/uploads", status_code=201)
async def upload_project_file(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    category: str = Form(...),
    title: str = Form(default=""),
    geographic_scope: str = Form(default=""),
    update_frequency: str = Form(default=""),
) -> dict[str, Any]:
    ensure_project(project_id)
    original_filename = str(file.filename or "").strip()
    if not original_filename:
        raise HTTPException(status_code=422, detail="Le fichier doit avoir un nom")
    filename = safe_filename(original_filename)
    try:
        extension, geographic = validate_upload_category(filename, category)
        frequency = normalize_update_frequency(update_frequency)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    category = category.strip().lower()
    if len(title.strip()) > 200 or len(geographic_scope.strip()) > 200:
        raise HTTPException(status_code=422, detail="Titre ou localisation trop long")

    resource_id = uuid.uuid4()
    relative = Path("uploads") / str(project_id) / category / f"{resource_id}_{filename}"
    destination = confined_path(DATA_DIR, str(relative))
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    digest = hashlib.sha256()
    size_bytes = 0
    try:
        with temporary.open("xb") as stream:
            while chunk := await file.read(1024 * 1024):
                size_bytes += len(chunk)
                if size_bytes > MAX_UPLOAD_BYTES:
                    raise ValueError(
                        f"Le fichier dépasse la limite de {MAX_UPLOAD_BYTES} octets"
                    )
                digest.update(chunk)
                stream.write(chunk)
        validate_upload_content(temporary, extension, category)
        os.replace(temporary, destination)
    except (OSError, ValueError) as exc:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        status_code = 413 if isinstance(exc, ValueError) else 500
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    finally:
        await file.close()

    if size_bytes == 0:
        temporary.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Le fichier transmis est vide")
    now = datetime.now(UTC)
    sha256 = digest.hexdigest()
    metadata = {
        "category": category,
        "original_filename": original_filename,
        "geographic": geographic,
        "update_frequency": frequency,
        "uploaded_at": now.isoformat(),
    }
    try:
        provenance = persist_raw(
            project_id,
            "upload",
            filename,
            {
                "event": "local_file_uploaded",
                "filename": filename,
                "size_bytes": size_bytes,
                "sha256": sha256,
                "metadata": metadata,
            },
            1,
            None,
            {"category": category, "update_frequency": frequency},
        )
        acquisition_id = uuid.UUID(provenance["acquisition_id"])
        with database_connection() as connection:
            connection.execute(
                """
                INSERT INTO local_resources
                    (id, project_id, acquisition_id, resource_key, source, dataset_id,
                     resource_id, title, url, format, filename, local_path, sha256,
                     size_bytes, content_type, status, created_at, updated_at, subject,
                     geographic_scope, resource_type, organization, metadata, origin_kind,
                     update_frequency, original_filename, uploaded_at)
                VALUES (%s, %s, %s, %s, 'upload', NULL, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, 'completed', %s, %s, %s, %s, %s,
                        'Import utilisateur', %s, 'upload', %s, %s, %s)
                """,
                (
                    resource_id,
                    project_id,
                    acquisition_id,
                    resource_key(str(resource_id), f"upload://{resource_id}"),
                    str(resource_id),
                    title.strip() or filename,
                    f"upload://{resource_id}/{filename}",
                    extension,
                    filename,
                    str(relative),
                    sha256,
                    size_bytes,
                    file.content_type or "application/octet-stream",
                    now,
                    now,
                    title.strip() or filename,
                    geographic_scope.strip() or None,
                    category,
                    Jsonb(metadata),
                    frequency or None,
                    original_filename,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO data_artifacts
                    (id, project_id, stage, acquisition_id, resource_id,
                     parent_artifact_id, path, sha256, media_type, metadata, created_at)
                VALUES (%s, %s, 'raw', %s, %s,
                        (SELECT id FROM data_artifacts WHERE acquisition_id = %s
                         ORDER BY created_at ASC LIMIT 1),
                        %s, %s, %s, %s, %s)
                """,
                (
                    uuid.uuid4(),
                    project_id,
                    acquisition_id,
                    resource_id,
                    acquisition_id,
                    str(relative),
                    sha256,
                    file.content_type or "application/octet-stream",
                    Jsonb(metadata),
                    now,
                ),
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    imported_script: dict[str, str] | None = None
    warning: str | None = None
    language = script_language(filename) if category == "script" else None
    if language:
        if size_bytes > 500_000:
            warning = "Fichier conservé, mais trop volumineux pour la bibliothèque de scripts."
        else:
            try:
                content = destination.read_text(encoding="utf-8")
                imported_script = create_script(
                    project_id,
                    ScriptCreate(
                        name=(Path(filename).stem if len(Path(filename).stem) >= 2 else f"Script {Path(filename).stem}"),
                        language=language,
                        content=content,
                        description=f"Importé depuis {original_filename}",
                    ),
                )
                with database_connection() as connection:
                    connection.execute(
                        "UPDATE local_resources SET metadata = metadata || %s WHERE id = %s",
                        (Jsonb({"script_id": imported_script["id"]}), resource_id),
                    )
            except UnicodeDecodeError:
                warning = "Fichier conservé, mais son encodage n’est pas UTF-8."

    return {
        "id": str(resource_id),
        "project_id": str(project_id),
        "filename": filename,
        "category": category,
        "format": extension,
        "geographic": geographic,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "update_frequency": frequency or None,
        "script": imported_script,
        "warning": warning,
    }


@app.get("/api/resources")
def resources(
    project_id: uuid.UUID,
    status: str | None = Query(default=None, pattern="^(queued|downloading|completed|failed|deleted)$"),
    source: str | None = Query(default=None, max_length=80),
    resource_format: str | None = Query(default=None, max_length=80),
    subject: str | None = Query(default=None, max_length=200),
    organization: str | None = Query(default=None, max_length=200),
    geographic_scope: str | None = Query(default=None, max_length=200),
    acquired_from: datetime | None = None,
    acquired_to: datetime | None = None,
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
    for column, value in (
        ("source", source),
        ("format", resource_format),
        ("subject", subject),
        ("organization", organization),
        ("geographic_scope", geographic_scope),
    ):
        if value:
            where += f" AND {column} ILIKE %s"
            parameters.append(f"%{value.strip()}%")
    if acquired_from:
        where += " AND created_at >= %s"
        parameters.append(acquired_from)
    if acquired_to:
        where += " AND created_at <= %s"
        parameters.append(acquired_to)
    parameters.append(limit)
    with database_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, acquisition_id, source, dataset_id, resource_id, title, url, format,
                   filename, local_path, sha256, size_bytes, content_type, status, error,
                   created_at, updated_at, deleted_at, m49_code, iso3_code, cod_level,
                   publisher, license_id, dataset_modified_at, cod_family
                   , subject, published_at, geographic_scope, resource_type,
                   organization, metadata
                   , origin_kind, update_frequency, original_filename, uploaded_at
            FROM local_resources WHERE {where} ORDER BY updated_at DESC LIMIT %s
            """,  # noqa: S608
            parameters,
        ).fetchall()
        refresh_rows = connection.execute(
            """
            SELECT id, resource_id, mode, interval_minutes, enabled, next_run_at,
                   last_run_at, last_status, last_error, updated_at
            FROM resource_refresh_schedules
            WHERE project_id = %s AND archived_at IS NULL
            """,
            (project_id,),
        ).fetchall()
    refresh_by_resource = {
        str(row[1]): {
            "id": str(row[0]),
            "mode": row[2],
            "interval_minutes": row[3],
            "enabled": row[4],
            "next_run_at": row[5],
            "last_run_at": row[6],
            "last_status": row[7],
            "last_error": row[8],
            "updated_at": row[9],
        }
        for row in refresh_rows
    }
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
            "cod_family": row[24],
            "subject": row[25],
            "published_at": row[26],
            "geographic_scope": row[27],
            "resource_type": row[28],
            "organization": row[29],
            "metadata": row[30],
            "origin_kind": row[31],
            "update_frequency": row[32],
            "original_filename": row[33],
            "uploaded_at": row[34],
            "refresh_schedule": refresh_by_resource.get(str(row[0])),
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


@app.get("/api/processing/operations")
def processing_operations() -> dict[str, Any]:
    return operation_catalog()


@app.get("/api/projects/{project_id}/processing-runs")
def processing_runs(
    project_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT r.id, r.recipe_id, p.name, r.input_resource_id, source.title,
                   r.output_resource_id, output.title, r.status, r.rows_read,
                   r.rows_written, r.report, r.error, r.started_at, r.finished_at,
                   p.engine_version, p.definition_sha256, p.generated_script_id
            FROM processing_runs r
            JOIN processing_recipes p ON p.id = r.recipe_id
            JOIN local_resources source ON source.id = r.input_resource_id
            LEFT JOIN local_resources output ON output.id = r.output_resource_id
            WHERE r.project_id = %s
            ORDER BY r.started_at DESC LIMIT %s
            """,
            (project_id, limit),
        ).fetchall()
    keys = [
        "id", "recipe_id", "name", "input_resource_id", "input_title",
        "output_resource_id", "output_title", "status", "rows_read",
        "rows_written", "report", "error", "started_at", "finished_at",
        "engine_version", "definition_sha256", "generated_script_id",
    ]
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(zip(keys, row))
        for key in ("id", "recipe_id", "input_resource_id", "output_resource_id", "generated_script_id"):
            item[key] = str(item[key]) if item[key] else None
        result.append(item)
    return result


@app.post("/api/projects/{project_id}/processing-runs", status_code=201)
def create_processing_run(
    project_id: uuid.UUID,
    payload: ProcessingRunCreate,
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        recipe = validate_recipe(payload.recipe)
    except RecipeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if payload.delimiter is not None and payload.delimiter not in {",", "\t", ";", "|"}:
        raise HTTPException(status_code=422, detail="Séparateur non autorisé")
    with database_connection() as connection:
        source = connection.execute(
            """
            SELECT id, acquisition_id, title, format, filename, local_path, sha256,
                   status, deleted_at, metadata
            FROM local_resources
            WHERE id = %s AND project_id = %s
            """,
            (payload.resource_id, project_id),
        ).fetchone()
    if not source or source[8] is not None:
        raise HTTPException(status_code=404, detail="Ressource source introuvable")
    if source[7] != "completed" or not source[5] or not source[6]:
        raise HTTPException(status_code=409, detail="La ressource source n’est pas complète ou vérifiable")
    source_format = str(source[3] or Path(str(source[4] or "")).suffix.lstrip(".")).casefold()
    if source_format not in {"csv", "tsv"}:
        raise HTTPException(status_code=422, detail="Le moteur guidé accepte actuellement CSV et TSV")
    try:
        source_path = confined_path(DATA_DIR, str(source[5]))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not source_path.is_file():
        raise HTTPException(status_code=404, detail="Le fichier source local a disparu")
    actual_sha256 = sha256_file(source_path)
    if actual_sha256 != source[6]:
        raise HTTPException(status_code=409, detail="L’empreinte du fichier source ne correspond plus")

    recipe_id, run_id, now = uuid.uuid4(), uuid.uuid4(), datetime.now(UTC)
    recipe_bytes = json.dumps(recipe, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    recipe_sha256 = hashlib.sha256(recipe_bytes).hexdigest()
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO processing_recipes
                (id, project_id, name, engine_version, definition,
                 definition_sha256, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                recipe_id, project_id, payload.name.strip(), recipe["version"],
                Jsonb(recipe), recipe_sha256, now, now,
            ),
        )
        connection.execute(
            """
            INSERT INTO processing_runs
                (id, project_id, recipe_id, input_resource_id, status, started_at)
            VALUES (%s, %s, %s, %s, 'running', %s)
            """,
            (run_id, project_id, recipe_id, payload.resource_id, now),
        )

    try:
        generated = (
            generate_python_script(recipe)
            if payload.script_language == "python"
            else generate_r_script(recipe)
        )
        script = create_script(
            project_id,
            ScriptCreate(
                name=f"Recette — {payload.name.strip()}",
                language=payload.script_language,
                content=generated,
                description=(
                    f"Généré depuis la recette {recipe_id}; entrée {payload.resource_id}; "
                    f"SHA-256 {recipe_sha256}"
                ),
            ),
        )
        with database_connection() as connection:
            connection.execute(
                "UPDATE processing_recipes SET generated_script_id = %s, updated_at = %s WHERE id = %s",
                (uuid.UUID(script["id"]), datetime.now(UTC), recipe_id),
            )
    except Exception as exc:
        with database_connection() as connection:
            connection.execute(
                """
                UPDATE processing_runs
                SET status = 'failed', error = %s, finished_at = %s
                WHERE id = %s
                """,
                ("Impossible de générer le script reproductible", datetime.now(UTC), run_id),
            )
        raise HTTPException(
            status_code=500,
            detail="Impossible de générer le script reproductible",
        ) from exc

    output_name = safe_filename(payload.output_title.strip(), f"derived_{run_id}.csv")
    if not output_name.casefold().endswith(".csv"):
        output_name += ".csv"
    relative = Path("projects") / str(project_id) / "derived" / f"{run_id}_{output_name}"
    output_path = confined_path(DATA_DIR, str(relative))
    try:
        report = run_delimited_recipe(
            source_path,
            output_path,
            recipe,
            delimiter=payload.delimiter,
            max_rows=payload.max_rows,
        )
        manifest = {
            "event": "processing_recipe_completed",
            "run_id": str(run_id),
            "recipe_id": str(recipe_id),
            "recipe_sha256": recipe_sha256,
            "input_resource_id": str(payload.resource_id),
            "input_sha256": actual_sha256,
            "output_sha256": report["output_sha256"],
            "engine_version": recipe["version"],
            "recipe": recipe,
            "report": report,
        }
        provenance = persist_raw(
            project_id,
            "processing",
            payload.name.strip(),
            manifest,
            int(report["rows_written"]),
            None,
            {"recipe_id": str(recipe_id), "run_id": str(run_id)},
        )
        acquisition_id = uuid.UUID(provenance["acquisition_id"])
        output_resource_id = uuid.uuid4()
        derived_artifact_id = uuid.uuid4()
        finished_at = datetime.now(UTC)
        metadata = {
            "category": "data",
            "geographic": False,
            "processing_run_id": str(run_id),
            "recipe_id": str(recipe_id),
            "recipe_sha256": recipe_sha256,
            "input_resource_id": str(payload.resource_id),
            "input_sha256": actual_sha256,
            "engine_version": recipe["version"],
            "profile": report["input_profile"],
        }
        with database_connection(autocommit=False) as connection:
            parent = connection.execute(
                """
                SELECT id FROM data_artifacts
                WHERE resource_id = %s OR acquisition_id = %s
                ORDER BY CASE WHEN resource_id = %s THEN 0 ELSE 1 END, created_at DESC
                LIMIT 1
                """,
                (payload.resource_id, source[1], payload.resource_id),
            ).fetchone()
            parent_artifact_id = parent[0] if parent else None
            connection.execute(
                """
                INSERT INTO local_resources
                    (id, project_id, acquisition_id, resource_key, source, dataset_id,
                     resource_id, title, url, format, filename, local_path, sha256,
                     size_bytes, content_type, status, created_at, updated_at, subject,
                     geographic_scope, resource_type, organization, metadata, origin_kind,
                     update_frequency, original_filename, uploaded_at)
                VALUES (%s, %s, %s, %s, 'processing', %s, %s, %s, %s, 'csv', %s,
                        %s, %s, %s, 'text/csv', 'completed', %s, %s, %s, NULL,
                        'data', 'HDP Processing Engine', %s, 'derived', NULL, %s, NULL)
                """,
                (
                    output_resource_id, project_id, acquisition_id,
                    resource_key(str(run_id), f"derived://{run_id}/{output_name}"),
                    str(recipe_id), str(run_id), payload.output_title.strip(),
                    f"derived://{run_id}/{output_name}", output_name, str(relative),
                    report["output_sha256"], report["output_size_bytes"],
                    finished_at, finished_at, payload.output_title.strip(),
                    Jsonb(metadata), output_name,
                ),
            )
            connection.execute(
                """
                INSERT INTO data_artifacts
                    (id, project_id, stage, acquisition_id, resource_id,
                     parent_artifact_id, path, sha256, media_type, metadata, created_at)
                VALUES (%s, %s, 'derived', %s, %s, %s, %s, %s, 'text/csv', %s, %s)
                """,
                (
                    derived_artifact_id, project_id, acquisition_id, output_resource_id,
                    parent_artifact_id, str(relative), report["output_sha256"],
                    Jsonb({**metadata, "report": report}), finished_at,
                ),
            )
            if parent_artifact_id:
                connection.execute(
                    """
                    INSERT INTO lineage_edges
                        (id, project_id, parent_artifact_id, child_artifact_id,
                         relation, metadata, created_at)
                    VALUES (%s, %s, %s, %s, 'transformed_by_recipe', %s, %s)
                    """,
                    (
                        uuid.uuid4(), project_id, parent_artifact_id,
                        derived_artifact_id, Jsonb({"recipe_id": str(recipe_id)}),
                        finished_at,
                    ),
                )
            connection.execute(
                """
                UPDATE processing_runs
                SET output_resource_id = %s, status = 'completed', rows_read = %s,
                    rows_written = %s, report = %s, finished_at = %s
                WHERE id = %s
                """,
                (
                    output_resource_id, report["rows_read"], report["rows_written"],
                    Jsonb(report), finished_at, run_id,
                ),
            )
            connection.commit()
        return {
            "id": str(run_id),
            "recipe_id": str(recipe_id),
            "status": "completed",
            "input_resource_id": str(payload.resource_id),
            "output_resource_id": str(output_resource_id),
            "generated_script_id": script["id"],
            "recipe_sha256": recipe_sha256,
            "report": report,
        }
    except (RecipeError, OSError, UnicodeError, csv.Error) as exc:
        output_path.unlink(missing_ok=True)
        with database_connection() as connection:
            connection.execute(
                """
                UPDATE processing_runs
                SET status = 'failed', error = %s, finished_at = %s
                WHERE id = %s
                """,
                (str(exc)[:2000], datetime.now(UTC), run_id),
            )
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def get_resource_refresh_schedule(resource_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, resource_id, mode, interval_minutes, enabled,
                   next_run_at, last_run_at, last_status, last_error, created_at, updated_at
            FROM resource_refresh_schedules
            WHERE resource_id = %s AND archived_at IS NULL
            """,
            (resource_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Planification du fichier introuvable")
    keys = [
        "id", "project_id", "resource_id", "mode", "interval_minutes", "enabled",
        "next_run_at", "last_run_at", "last_status", "last_error", "created_at", "updated_at",
    ]
    result = dict(zip(keys, row))
    for key in ("id", "project_id", "resource_id"):
        result[key] = str(result[key])
    return result


@app.get("/api/resources/{resource_id}/refresh-schedule")
def resource_refresh_schedule(resource_id: uuid.UUID) -> dict[str, Any]:
    resource_row(resource_id)
    return get_resource_refresh_schedule(resource_id)


@app.post("/api/resources/{resource_id}/refresh-schedule", status_code=201)
def create_resource_refresh_schedule(
    resource_id: uuid.UUID,
    payload: ResourceRefreshScheduleCreate,
) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT lr.project_id, lr.source, lr.deleted_at, a.query, a.parameters
            FROM local_resources lr
            JOIN acquisitions a ON a.id = lr.acquisition_id
            WHERE lr.id = %s
            """,
            (resource_id,),
        ).fetchone()
    if not row or row[2]:
        raise HTTPException(status_code=404, detail="Ressource locale introuvable")
    mode = "source_acquisition" if row[1] in CONNECTORS else "manual_replacement"
    now = datetime.now(UTC)
    schedule_id = uuid.uuid4()
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO resource_refresh_schedules
                (id, project_id, resource_id, mode, interval_minutes, enabled,
                 next_run_at, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (resource_id) DO UPDATE SET
                mode = EXCLUDED.mode,
                interval_minutes = EXCLUDED.interval_minutes,
                enabled = EXCLUDED.enabled,
                next_run_at = EXCLUDED.next_run_at,
                updated_at = EXCLUDED.updated_at,
                archived_at = NULL
            """,
            (
                schedule_id,
                row[0],
                resource_id,
                mode,
                payload.interval_minutes,
                payload.enabled,
                next_run_at(now, payload.interval_minutes),
                now,
                now,
            ),
        )
        connection.execute(
            """
            UPDATE local_resources SET update_frequency = %s, updated_at = %s
            WHERE id = %s
            """,
            (f"Toutes les {payload.interval_minutes} minutes", now, resource_id),
        )
    return get_resource_refresh_schedule(resource_id)


@app.patch("/api/resources/{resource_id}/refresh-schedule")
def update_resource_refresh_schedule(
    resource_id: uuid.UUID,
    payload: ResourceRefreshSchedulePatch,
) -> dict[str, Any]:
    updates = payload.model_dump(exclude_none=True)
    current = get_resource_refresh_schedule(resource_id)
    if not updates:
        return current
    interval = int(updates.get("interval_minutes", current["interval_minutes"]))
    enabled = bool(updates.get("enabled", current["enabled"]))
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE resource_refresh_schedules
            SET interval_minutes = %s, enabled = %s, next_run_at = %s, updated_at = %s
            WHERE resource_id = %s AND archived_at IS NULL
            """,
            (interval, enabled, next_run_at(now, interval), now, resource_id),
        )
        connection.execute(
            "UPDATE local_resources SET update_frequency = %s, updated_at = %s WHERE id = %s",
            (f"Toutes les {interval} minutes", now, resource_id),
        )
    return get_resource_refresh_schedule(resource_id)


@app.delete("/api/resources/{resource_id}/refresh-schedule", status_code=204)
def archive_resource_refresh_schedule(resource_id: uuid.UUID) -> Response:
    now = datetime.now(UTC)
    with database_connection() as connection:
        result = connection.execute(
            """
            UPDATE resource_refresh_schedules
            SET enabled = FALSE, archived_at = %s, updated_at = %s
            WHERE resource_id = %s AND archived_at IS NULL
            """,
            (now, now, resource_id),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Planification du fichier introuvable")
    return Response(status_code=204)


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


def _map_layer_feature_collection(layer_id: uuid.UUID) -> tuple[dict[str, Any], dict[str, Any]]:
    with database_connection() as connection:
        layer = connection.execute(
            """
            SELECT id, project_id, name, feature_count, created_at, updated_at
            FROM map_layers WHERE id = %s
            """,
            (layer_id,),
        ).fetchone()
        if not layer:
            raise HTTPException(status_code=404, detail="Couche cartographique introuvable")
        rows = connection.execute(
            """
            SELECT id, properties, ST_AsGeoJSON(geom, 6)
            FROM map_features WHERE layer_id = %s ORDER BY created_at ASC LIMIT 5000
            """,
            (layer_id,),
        ).fetchall()
    metadata = {
        "id": str(layer[0]), "project_id": str(layer[1]), "name": layer[2],
        "feature_count": layer[3], "created_at": layer[4], "updated_at": layer[5],
    }
    features = [
        {
            "type": "Feature",
            "id": str(row[0]),
            "properties": row[1] or {},
            "geometry": json.loads(row[2]) if row[2] else None,
        }
        for row in rows
    ]
    return metadata, {"type": "FeatureCollection", "features": features}


@app.get("/api/map/config")
def map_config() -> dict[str, Any]:
    return {
        "leaflet_version": "1.9.4",
        "tile_url": HDP_TILE_URL,
        "tile_attribution": "© OpenStreetMap contributors",
        "tiles_opt_in": True,
        "usage_policy": "https://operations.osmfoundation.org/policies/tiles/",
    }


@app.get("/api/projects/{project_id}/map/layers")
def map_layers(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT l.id, l.resource_id, l.name, l.feature_count, l.created_at,
                   l.updated_at, r.filename, r.sha256
            FROM map_layers l
            LEFT JOIN local_resources r ON r.id = l.resource_id
            WHERE l.project_id = %s ORDER BY l.updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [
        {
            "id": str(row[0]), "resource_id": str(row[1]) if row[1] else None,
            "name": row[2], "feature_count": row[3], "created_at": row[4],
            "updated_at": row[5], "filename": row[6], "resource_sha256": row[7],
        }
        for row in rows
    ]


@app.post("/api/resources/{resource_id}/map/import", status_code=201)
def import_map_resource(resource_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT project_id, title, filename, local_path, status, format, sha256
            FROM local_resources WHERE id = %s AND deleted_at IS NULL
            """,
            (resource_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Ressource locale introuvable")
    if row[4] != "completed" or not row[3]:
        raise HTTPException(status_code=409, detail="La ressource doit être téléchargée et complète")
    try:
        path = confined_path(DATA_DIR, row[3])
        if not row[6] or sha256_file(path) != row[6]:
            raise ValueError("L’empreinte SHA-256 de la ressource ne correspond plus")
        features = load_geojson(path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    layer_name = safe_layer_name(row[2] or row[1])
    now = datetime.now(UTC)
    try:
        with database_connection(autocommit=False) as connection:
            existing = connection.execute(
                "SELECT id FROM map_layers WHERE project_id = %s AND resource_id = %s FOR UPDATE",
                (row[0], resource_id),
            ).fetchone()
            layer_id = existing[0] if existing else uuid.uuid4()
            if existing:
                connection.execute("DELETE FROM map_features WHERE layer_id = %s", (layer_id,))
                connection.execute(
                    "UPDATE map_layers SET name = %s, feature_count = 0, updated_at = %s WHERE id = %s",
                    (layer_name, now, layer_id),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO map_layers
                        (id, project_id, resource_id, name, feature_count, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, 0, %s, %s)
                    """,
                    (layer_id, row[0], resource_id, layer_name, now, now),
                )
            for feature in features:
                feature_id = uuid.uuid4()
                geometry = feature["geometry"]
                if geometry is None:
                    connection.execute(
                        """
                        INSERT INTO map_features (id, layer_id, properties, geom, created_at)
                        VALUES (%s, %s, %s, NULL, %s)
                        """,
                        (feature_id, layer_id, Jsonb(feature["properties"]), now),
                    )
                else:
                    connection.execute(
                        """
                        INSERT INTO map_features (id, layer_id, properties, geom, created_at)
                        VALUES (
                            %s, %s, %s,
                            ST_Force2D(ST_SetSRID(ST_MakeValid(ST_GeomFromGeoJSON(%s)), 4326)),
                            %s
                        )
                        """,
                        (
                            feature_id, layer_id, Jsonb(feature["properties"]),
                            json.dumps(geometry, ensure_ascii=False), now,
                        ),
                    )
            connection.execute(
                "UPDATE map_layers SET feature_count = %s, updated_at = %s WHERE id = %s",
                (len(features), now, layer_id),
            )
            connection.commit()
    except psycopg.Error as exc:
        raise HTTPException(status_code=422, detail="PostGIS a refusé une géométrie GeoJSON") from exc
    return {
        "id": str(layer_id), "project_id": str(row[0]), "resource_id": str(resource_id),
        "name": layer_name, "feature_count": len(features), "status": "imported",
    }


@app.get("/api/map/layers/{layer_id}/geojson")
def map_layer_geojson(layer_id: uuid.UUID) -> dict[str, Any]:
    _, feature_collection = _map_layer_feature_collection(layer_id)
    return feature_collection


@app.delete("/api/map/layers/{layer_id}", status_code=204)
def delete_map_layer(layer_id: uuid.UUID) -> Response:
    with database_connection() as connection:
        result = connection.execute("DELETE FROM map_layers WHERE id = %s", (layer_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Couche cartographique introuvable")
    return Response(status_code=204)


@app.get("/api/map/layers/{layer_id}/export")
def export_map_layer(layer_id: uuid.UUID) -> FileResponse:
    metadata, feature_collection = _map_layer_feature_collection(layer_id)
    project_id = uuid.UUID(metadata["project_id"])
    relative = Path("projects") / str(project_id) / "exports" / f"map_layer_{layer_id}.zip"
    destination = DATA_DIR / relative
    export_bundle(destination, metadata["name"], feature_collection)
    return FileResponse(
        destination,
        filename=f"HDP_map_layer_{layer_id}_QGIS_R.zip",
        media_type="application/zip",
    )


@app.get("/api/projects/{project_id}/timeline")
def project_timeline(
    project_id: uuid.UUID, days: int = Query(default=30, ge=1, le=365)
) -> dict[str, Any]:
    ensure_project(project_id)
    window_end = datetime.now(UTC)
    window_start = window_end - timedelta(days=days)
    events: list[dict[str, Any]] = []
    with database_connection() as connection:
        acquisitions_rows = connection.execute(
            """
            SELECT id, source, query, retrieved_at, item_count
            FROM acquisitions WHERE project_id = %s AND retrieved_at >= %s
            ORDER BY retrieved_at ASC
            """,
            (project_id, window_start),
        ).fetchall()
        schedule_rows = connection.execute(
            """
            SELECT r.id, s.name, r.started_at, COALESCE(r.finished_at, r.started_at), r.status
            FROM schedule_runs r JOIN schedules s ON s.id = r.schedule_id
            WHERE s.project_id = %s AND r.started_at >= %s ORDER BY r.started_at ASC
            """,
            (project_id, window_start),
        ).fetchall()
        execution_rows = connection.execute(
            """
            SELECT e.id, s.name, e.requested_at,
                   COALESCE(e.finished_at, e.started_at, e.requested_at), e.status
            FROM script_executions e JOIN project_scripts s ON s.id = e.script_id
            WHERE e.project_id = %s AND e.requested_at >= %s ORDER BY e.requested_at ASC
            """,
            (project_id, window_start),
        ).fetchall()
        future_rows = connection.execute(
            """
            SELECT id, name, next_run_at, enabled FROM schedules
            WHERE project_id = %s AND archived_at IS NULL AND next_run_at <= %s
            ORDER BY next_run_at ASC
            """,
            (project_id, window_end + timedelta(days=days)),
        ).fetchall()
    for row in acquisitions_rows:
        events.append({"id": str(row[0]), "kind": "acquisition", "title": f"{row[1]} — {row[2]}", "start": row[3], "end": row[3], "status": "completed", "detail": f"{row[4]} résultat(s)"})
    for row in schedule_rows:
        events.append({"id": str(row[0]), "kind": "schedule_run", "title": row[1], "start": row[2], "end": row[3], "status": row[4]})
    for row in execution_rows:
        events.append({"id": str(row[0]), "kind": "script", "title": row[1], "start": row[2], "end": row[3], "status": row[4]})
    for row in future_rows:
        events.append({"id": str(row[0]), "kind": "scheduled", "title": row[1], "start": row[2], "end": row[2], "status": "planned" if row[3] else "suspended"})
    return {"project_id": str(project_id), "window_start": window_start, "window_end": window_end, "events": events}


def get_execution_settings(project_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT python_enabled, r_enabled, timeout_seconds, max_output_bytes,
                   network_policy, allowed_hosts, updated_at
            FROM project_execution_settings WHERE project_id = %s
            """,
            (project_id,),
        ).fetchone()
    if not row:
        now = datetime.now(UTC)
        return {
            "python_enabled": True,
            "r_enabled": False,
            "timeout_seconds": 60,
            "max_output_bytes": 262_144,
            "network_policy": "disabled",
            "allowed_hosts": [],
            "updated_at": now,
            "runners": {
                "python": heartbeat_status(EXECUTION_SPOOL_DIR, "python"),
                "r": heartbeat_status(EXECUTION_SPOOL_DIR, "r"),
            },
        }
    return {
        "python_enabled": bool(row[0]),
        "r_enabled": bool(row[1]),
        "timeout_seconds": int(row[2]),
        "max_output_bytes": int(row[3]),
        "network_policy": row[4],
        "allowed_hosts": row[5] or [],
        "updated_at": row[6],
        "runners": {
            "python": heartbeat_status(EXECUTION_SPOOL_DIR, "python"),
            "r": heartbeat_status(EXECUTION_SPOOL_DIR, "r"),
        },
    }


def _execution_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def _execution_row(execution_id: uuid.UUID) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT e.id, e.project_id, e.script_id, e.script_version_id, e.language,
                   e.status, e.requested_at, e.started_at, e.finished_at,
                   e.timeout_seconds, e.max_output_bytes, e.network_enabled,
                   e.exit_code, e.stdout, e.stderr, e.stdout_sha256, e.stderr_sha256,
                   e.report_path, e.report_sha256, e.error, v.version_number, v.content_sha256,
                   v.name
            FROM script_executions e
            JOIN script_versions v ON v.id = e.script_version_id
            WHERE e.id = %s
            """,
            (execution_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Exécution introuvable")
    keys = [
        "id", "project_id", "script_id", "script_version_id", "language", "status",
        "requested_at", "started_at", "finished_at", "timeout_seconds",
        "max_output_bytes", "network_enabled", "exit_code", "stdout", "stderr",
        "stdout_sha256", "stderr_sha256", "report_path", "report_sha256", "error",
        "version_number", "content_sha256", "script_name",
    ]
    result = dict(zip(keys, row))
    for key in ("id", "project_id", "script_id", "script_version_id"):
        result[key] = str(result[key])
    result["network_policy"] = "disabled"
    return result


def collect_execution_result(execution_id: uuid.UUID) -> dict[str, Any]:
    current = _execution_row(execution_id)
    if current["status"] in TERMINAL_STATUSES:
        return current
    spool_result = read_execution_result(
        EXECUTION_SPOOL_DIR,
        execution_id,
        current["language"],
        int(current["max_output_bytes"]),
    )
    if not spool_result:
        return current
    status = spool_result["status"]
    started_at = _execution_timestamp(spool_result.get("started_at"))
    if status not in TERMINAL_STATUSES:
        if status == "running":
            with database_connection() as connection:
                connection.execute(
                    "UPDATE script_executions SET status = 'running', started_at = COALESCE(started_at, %s) WHERE id = %s",
                    (started_at or datetime.now(UTC), execution_id),
                )
        return _execution_row(execution_id)

    finished_at = _execution_timestamp(spool_result.get("finished_at")) or datetime.now(UTC)
    stdout = str(spool_result.get("stdout") or "")
    stderr = str(spool_result.get("stderr") or "")
    report = {
        "execution_id": str(execution_id),
        "project_id": current["project_id"],
        "script_id": current["script_id"],
        "script_name": current["script_name"],
        "script_version_id": current["script_version_id"],
        "version_number": current["version_number"],
        "content_sha256": current["content_sha256"],
        "language": current["language"],
        "status": status,
        "requested_at": current["requested_at"],
        "started_at": started_at,
        "finished_at": finished_at,
        "timeout_seconds": current["timeout_seconds"],
        "max_output_bytes": current["max_output_bytes"],
        "network_policy": "disabled",
        "exit_code": spool_result.get("exit_code"),
        "stdout": stdout,
        "stderr": stderr,
    }
    report_path, report_sha256 = write_execution_report(
        DATA_DIR, uuid.UUID(current["project_id"]), execution_id, report
    )
    stdout_sha256 = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
    stderr_sha256 = hashlib.sha256(stderr.encode("utf-8")).hexdigest()
    error = None
    if status != "completed":
        error = (stderr.strip() or "Le traitement n'a pas abouti")[:2000]
    with database_connection() as connection:
        connection.execute(
            """
            UPDATE script_executions
            SET status = %s, started_at = COALESCE(started_at, %s), finished_at = %s,
                exit_code = %s, stdout = %s, stderr = %s, stdout_sha256 = %s,
                stderr_sha256 = %s, report_path = %s, report_sha256 = %s, error = %s
            WHERE id = %s
            """,
            (
                status, started_at, finished_at, spool_result.get("exit_code"), stdout,
                stderr, stdout_sha256, stderr_sha256, report_path, report_sha256,
                error, execution_id,
            ),
        )
    return _execution_row(execution_id)


def collect_pending_executions() -> None:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id FROM script_executions
            WHERE status IN ('queued', 'running')
            ORDER BY requested_at ASC LIMIT 50
            """
        ).fetchall()
    for row in rows:
        collect_execution_result(row[0])


@app.get("/api/projects/{project_id}/execution-settings")
def project_execution_settings(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    return get_execution_settings(project_id)


@app.put("/api/projects/{project_id}/execution-settings")
def update_project_execution_settings(
    project_id: uuid.UUID, payload: ExecutionSettingsUpdate
) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        validate_execution_request(
            "python", payload.timeout_seconds, payload.max_output_bytes,
            network_enabled=payload.network_enabled, allowed_hosts=payload.allowed_hosts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_execution_settings
                (project_id, python_enabled, r_enabled, timeout_seconds, max_output_bytes,
                 network_policy, allowed_hosts, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'disabled', '[]'::jsonb, %s)
            ON CONFLICT (project_id) DO UPDATE SET
                python_enabled = EXCLUDED.python_enabled,
                r_enabled = EXCLUDED.r_enabled,
                timeout_seconds = EXCLUDED.timeout_seconds,
                max_output_bytes = EXCLUDED.max_output_bytes,
                network_policy = 'disabled', allowed_hosts = '[]'::jsonb,
                updated_at = EXCLUDED.updated_at
            """,
            (
                project_id, payload.python_enabled, payload.r_enabled,
                payload.timeout_seconds, payload.max_output_bytes, now,
            ),
        )
    return get_execution_settings(project_id)


@app.get("/api/projects/{project_id}/scripts")
def scripts(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT s.id, s.name, s.language, s.content, s.description, s.created_at,
                   s.updated_at, COALESCE(MAX(v.version_number), 0)
            FROM project_scripts s
            LEFT JOIN script_versions v ON v.script_id = s.id
            WHERE s.project_id = %s AND s.archived_at IS NULL
            GROUP BY s.id ORDER BY s.updated_at DESC
            """,
            (project_id,),
        ).fetchall()
    return [
        {
            "id": str(row[0]), "name": row[1], "language": row[2], "content": row[3],
            "description": row[4], "created_at": row[5], "updated_at": row[6],
            "version_number": row[7],
            "execution": "available" if row[2] in {"python", "r"} else "storage_only",
        }
        for row in rows
    ]


@app.post("/api/projects/{project_id}/scripts", status_code=201)
def create_script(project_id: uuid.UUID, payload: ScriptCreate) -> dict[str, str]:
    ensure_project(project_id)
    script_id, now = uuid.uuid4(), datetime.now(UTC)
    version_id = uuid.uuid4()
    with database_connection(autocommit=False) as connection:
        connection.execute(
            """
            INSERT INTO project_scripts
                (id, project_id, name, language, content, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (script_id, project_id, payload.name.strip(), payload.language, payload.content, payload.description, now, now),
        )
        connection.execute(
            """
            INSERT INTO script_versions
                (id, script_id, project_id, version_number, name, language,
                 description, content, content_sha256, created_at)
            VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id, script_id, project_id, payload.name.strip(), payload.language,
                payload.description, payload.content, script_sha256(payload.content), now,
            ),
        )
        connection.commit()
    return {"id": str(script_id), "version_id": str(version_id), "status": "created"}


@app.patch("/api/scripts/{script_id}")
def update_script(script_id: uuid.UUID, payload: ScriptPatch) -> dict[str, str]:
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return {"status": "unchanged"}
    now = datetime.now(UTC)
    with database_connection(autocommit=False) as connection:
        current = connection.execute(
            """
            SELECT project_id, name, language, content, description
            FROM project_scripts WHERE id = %s AND archived_at IS NULL FOR UPDATE
            """,
            (script_id,),
        ).fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Script introuvable")
        merged = {
            "name": updates.get("name", current[1]),
            "language": updates.get("language", current[2]),
            "content": updates.get("content", current[3]),
            "description": updates.get("description", current[4]),
        }
        connection.execute(
            """
            UPDATE project_scripts
            SET name = %s, language = %s, content = %s, description = %s, updated_at = %s
            WHERE id = %s
            """,
            (
                str(merged["name"]).strip(), merged["language"], merged["content"],
                merged["description"], now, script_id,
            ),
        )
        version_row = connection.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 FROM script_versions WHERE script_id = %s",
            (script_id,),
        ).fetchone()
        version_number = int(version_row[0])
        version_id = uuid.uuid4()
        connection.execute(
            """
            INSERT INTO script_versions
                (id, script_id, project_id, version_number, name, language,
                 description, content, content_sha256, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                version_id, script_id, current[0], version_number,
                str(merged["name"]).strip(), merged["language"], merged["description"],
                merged["content"], script_sha256(str(merged["content"])), now,
            ),
        )
        connection.commit()
    return {
        "status": "updated", "version_id": str(version_id),
        "version_number": str(version_number),
    }


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


@app.get("/api/scripts/{script_id}/versions")
def script_versions(script_id: uuid.UUID) -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, version_number, name, language, description, content_sha256, created_at
            FROM script_versions WHERE script_id = %s ORDER BY version_number DESC
            """,
            (script_id,),
        ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Script ou versions introuvables")
    return [
        {
            "id": str(row[0]), "version_number": row[1], "name": row[2],
            "language": row[3], "description": row[4], "content_sha256": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


@app.post("/api/scripts/{script_id}/executions", status_code=202)
def execute_script(script_id: uuid.UUID, payload: ScriptExecutionCreate) -> dict[str, Any]:
    with database_connection() as connection:
        row = connection.execute(
            """
            SELECT s.project_id, s.language, v.id, v.version_number, v.content,
                   v.content_sha256
            FROM project_scripts s
            JOIN script_versions v ON v.script_id = s.id
            WHERE s.id = %s AND s.archived_at IS NULL
            ORDER BY v.version_number DESC LIMIT 1
            """,
            (script_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Script introuvable")
    project_id, language = row[0], row[1]
    settings = get_execution_settings(project_id)
    if language == "python" and not settings["python_enabled"]:
        raise HTTPException(status_code=409, detail="Les exécutions Python sont désactivées pour ce projet")
    if language == "r" and not settings["r_enabled"]:
        raise HTTPException(status_code=409, detail="Les exécutions R sont désactivées pour ce projet")
    if language not in {"python", "r"}:
        raise HTTPException(status_code=422, detail="Seuls les scripts Python et R peuvent être exécutés")
    runner = settings["runners"][language]
    if not runner["available"]:
        message = "Le runner R optionnel n'est pas démarré avec le profil analytics" if language == "r" else "Le runner Python isolé n'est pas encore disponible"
        raise HTTPException(status_code=503, detail=message)
    timeout_seconds = payload.timeout_seconds or int(settings["timeout_seconds"])
    max_output_bytes = payload.max_output_bytes or int(settings["max_output_bytes"])
    try:
        validated = validate_execution_request(
            language, timeout_seconds, max_output_bytes,
            network_enabled=payload.network_enabled, allowed_hosts=payload.allowed_hosts,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    execution_id, now = uuid.uuid4(), datetime.now(UTC)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO script_executions
                (id, project_id, script_id, script_version_id, language, status,
                 requested_at, timeout_seconds, max_output_bytes, network_enabled)
            VALUES (%s, %s, %s, %s, %s, 'queued', %s, %s, %s, FALSE)
            """,
            (
                execution_id, project_id, script_id, row[2], language, now,
                validated["timeout_seconds"], validated["max_output_bytes"],
            ),
        )
    try:
        prepare_execution_job(
            EXECUTION_SPOOL_DIR, execution_id, language, row[4],
            validated["timeout_seconds"], validated["max_output_bytes"],
        )
    except Exception as exc:
        with database_connection() as connection:
            connection.execute(
                "UPDATE script_executions SET status = 'failed', finished_at = %s, error = %s WHERE id = %s",
                (datetime.now(UTC), str(exc)[:2000], execution_id),
            )
        raise HTTPException(status_code=500, detail="Impossible de préparer l'exécution isolée") from exc
    return _execution_row(execution_id)


@app.get("/api/executions/{execution_id}")
def execution(execution_id: uuid.UUID) -> dict[str, Any]:
    return collect_execution_result(execution_id)


@app.get("/api/scripts/{script_id}/executions")
def script_execution_history(
    script_id: uuid.UUID, limit: int = Query(default=50, ge=1, le=200)
) -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id FROM script_executions
            WHERE script_id = %s ORDER BY requested_at DESC LIMIT %s
            """,
            (script_id, limit),
        ).fetchall()
    return [collect_execution_result(row[0]) for row in rows]


@app.get("/api/executions/{execution_id}/report")
def execution_report(execution_id: uuid.UUID) -> FileResponse:
    result = collect_execution_result(execution_id)
    if not result.get("report_path"):
        raise HTTPException(status_code=409, detail="Le rapport n'est pas encore disponible")
    try:
        path = confined_path(DATA_DIR, str(result["report_path"]))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="Chemin de rapport invalide") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier de rapport absent")
    return FileResponse(path, filename=f"HDP_execution_{execution_id}.json", media_type="application/json")


@app.get("/api/projects/{project_id}/schedules")
def schedules(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, source, query, result_limit, auto_download, interval_minutes,
                   enabled, next_run_at, last_run_at, last_status, last_error, created_at,
                   updated_at, parameters
            FROM schedules WHERE project_id = %s AND archived_at IS NULL ORDER BY created_at DESC
            """,
            (project_id,),
        ).fetchall()
    keys = [
        "id", "name", "source", "query", "result_limit", "auto_download", "interval_minutes",
        "enabled", "next_run_at", "last_run_at", "last_status", "last_error", "created_at",
        "updated_at", "parameters",
    ]
    return [dict(zip(keys, (str(row[0]), *row[1:]))) for row in rows]


@app.post("/api/projects/{project_id}/schedules", status_code=201)
def create_schedule(project_id: uuid.UUID, payload: ScheduleCreate) -> dict[str, Any]:
    ensure_project(project_id)
    validate_interval(payload.interval_minutes)
    project_settings = get_project_source_settings(project_id, payload.source)
    try:
        parameters = validate_values(
            payload.source,
            {
                **project_settings["parameters"],
                **payload.parameters,
                "query": payload.query,
                "result_limit": payload.result_limit,
                "auto_download": payload.auto_download,
            },
            scope="project",
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    schedule_id, now = uuid.uuid4(), datetime.now(UTC)
    first_run = now if payload.enabled else next_run_at(now, payload.interval_minutes)
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO schedules
                (id, project_id, name, source, query, result_limit, auto_download, interval_minutes,
                 enabled, next_run_at, created_at, updated_at, parameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                schedule_id, project_id, payload.name.strip(), payload.source, payload.query.strip(),
                payload.result_limit, payload.auto_download, payload.interval_minutes, payload.enabled,
                first_run, now, now, Jsonb(parameters),
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
    if "parameters" in updates:
        source_id = updates.get("source")
        with database_connection() as connection:
            row = connection.execute(
                "SELECT source FROM schedules WHERE id = %s AND archived_at IS NULL", (schedule_id,)
            ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Planification introuvable")
        source_id = source_id or row[0]
        try:
            updates["parameters"] = validate_values(
                source_id, updates["parameters"], scope="project"
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    for key in ("name", "source", "query", "result_limit", "auto_download", "interval_minutes", "enabled", "parameters"):
        if key in updates:
            assignments.append(f"{key} = %s")
            parameters.append(Jsonb(updates[key]) if key == "parameters" else updates[key])
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
            SELECT id, project_id, source, query, result_limit, auto_download, parameters
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
        "parameters": row[6],
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
