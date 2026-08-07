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
APP_VERSION = "2.0.0"
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATABASE_URL = os.environ["DATABASE_URL"]
R_SERVICE_URL = os.getenv("R_SERVICE_URL", "http://r-service:8001")
RELIEFWEB_APPNAME = os.getenv("RELIEFWEB_APPNAME", "").strip()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
DEFAULT_PROJECT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEFAULT_PREFERENCES: dict[str, Any] = {
    "auto_download": False,
    "max_download_bytes": 104_857_600,
    "max_resources_per_acquisition": 20,
    "allowed_formats": [],
}
SCHEDULER_POLL_SECONDS = 20

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
                        status TEXT NOT NULL,
                        error TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        deleted_at TIMESTAMPTZ
                    )
                    """
                )
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
            return existing[0], existing[1], existing[2]
        resource_id = uuid.uuid4()
        now = datetime.now(UTC)
        connection.execute(
            """
            INSERT INTO local_resources
                (id, project_id, acquisition_id, resource_key, source, dataset_id, resource_id,
                 title, url, format, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'queued', %s, %s)
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
    summary = {"queued": 0, "completed": 0, "skipped": 0, "failed": 0}
    cap = int(preferences["max_resources_per_acquisition"])
    candidates: list[tuple[str | None, dict[str, Any]]] = []
    for item in items:
        for resource in item.get("resources", []):
            if resource.get("url"):
                candidates.append((str(item.get("id")) if item.get("id") else None, resource))
    for dataset_id, resource in candidates[:cap]:
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
    summary["skipped"] += max(0, len(candidates) - cap)
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
    downloads = {"queued": 0, "completed": 0, "skipped": 0, "failed": 0}
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


async def scheduler_loop() -> None:
    while True:
        try:
            schedule = await asyncio.to_thread(claim_due_schedule)
            if schedule:
                await execute_claimed_schedule(schedule)
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
                   created_at, updated_at, deleted_at
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
