from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel


APP_NAME = "Humanitarian Data Platform"
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
DATABASE_URL = os.environ["DATABASE_URL"]
R_SERVICE_URL = os.getenv("R_SERVICE_URL", "http://r-service:8001")
RELIEFWEB_APPNAME = os.getenv("RELIEFWEB_APPNAME", "").strip()
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title=APP_NAME, version="1.5.0")


class SearchResponse(BaseModel):
    acquisition_id: str
    source: str
    query: str
    retrieved_at: datetime
    sha256: str
    item_count: int
    raw_path: str
    items: list[dict[str, Any]]


def database_connection() -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=True)


def initialize_database() -> None:
    last_error: Exception | None = None
    for _ in range(30):
        try:
            with database_connection() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS acquisitions (
                        id UUID PRIMARY KEY,
                        source TEXT NOT NULL,
                        query TEXT NOT NULL,
                        retrieved_at TIMESTAMPTZ NOT NULL,
                        sha256 CHAR(64) NOT NULL,
                        item_count INTEGER NOT NULL,
                        raw_path TEXT NOT NULL
                    )
                    """
                )
                connection.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            return
        except Exception as exc:  # Docker may still be completing startup.
            last_error = exc
            time.sleep(2)
    raise RuntimeError("Database unavailable after startup retries") from last_error


@app.on_event("startup")
def startup() -> None:
    DATA_DIR.joinpath("raw").mkdir(parents=True, exist_ok=True)
    initialize_database()


def safe_query_fragment(query: str) -> str:
    fragment = re.sub(r"[^a-zA-Z0-9_-]+", "-", query.strip()).strip("-")
    return fragment[:50] or "query"


def persist_raw(source: str, query: str, payload: dict[str, Any], item_count: int) -> dict[str, Any]:
    retrieved_at = datetime.now(UTC)
    acquisition_id = uuid.uuid4()
    raw_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw_bytes).hexdigest()
    relative = Path("raw") / source / f"{retrieved_at:%Y%m%dT%H%M%SZ}_{safe_query_fragment(query)}_{acquisition_id}.json"
    destination = DATA_DIR / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw_bytes)

    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO acquisitions (id, source, query, retrieved_at, sha256, item_count, raw_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (acquisition_id, source, query, retrieved_at, digest, item_count, str(relative)),
        )

    return {
        "acquisition_id": str(acquisition_id),
        "retrieved_at": retrieved_at,
        "sha256": digest,
        "raw_path": str(relative),
    }


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
        "profile": "list",
    }
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        response = await client.get("https://api.reliefweb.int/v2/reports", params=params)
        response.raise_for_status()
        payload = response.json()
    items = [
        {
            "id": row.get("id"),
            "title": row.get("fields", {}).get("title"),
            "date": row.get("fields", {}).get("date", {}).get("created"),
            "url": row.get("fields", {}).get("url_alias") or row.get("href"),
            "source": "ReliefWeb",
        }
        for row in payload.get("data", [])
    ]
    return payload, items


async def search_hdx(query: str, limit: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    params = {"q": query, "rows": limit}
    async with httpx.AsyncClient(timeout=40, follow_redirects=True) as client:
        response = await client.get("https://data.humdata.org/api/3/action/package_search", params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload.get("result", {}).get("results", [])
    items = [
        {
            "id": row.get("id"),
            "title": row.get("title") or row.get("name"),
            "date": row.get("metadata_modified"),
            "url": f"https://data.humdata.org/dataset/{row.get('name')}",
            "source": "HDX/CKAN",
        }
        for row in results
    ]
    return payload, items


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    with database_connection() as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok", "application": APP_NAME, "version": "1.5.0"}


@app.get("/api/sources")
def sources() -> list[dict[str, str]]:
    return [
        {"id": "reliefweb", "name": "ReliefWeb", "access": "Public API"},
        {"id": "hdx", "name": "HDX / CKAN", "access": "Public API"},
    ]


@app.get("/api/search", response_model=SearchResponse)
async def search(
    source: str = Query(pattern="^(reliefweb|hdx)$"),
    query: str = Query(min_length=2, max_length=200),
    limit: int = Query(default=25, ge=1, le=100),
) -> SearchResponse:
    try:
        if source == "reliefweb":
            payload, items = await search_reliefweb(query, limit)
        else:
            payload, items = await search_hdx(query, limit)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Source distante indisponible: {exc}") from exc

    provenance = persist_raw(source, query, payload, len(items))
    return SearchResponse(source=source, query=query, item_count=len(items), items=items, **provenance)


@app.get("/api/acquisitions")
def acquisitions(limit: int = Query(default=50, ge=1, le=200)) -> list[dict[str, Any]]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, source, query, retrieved_at, sha256, item_count, raw_path
            FROM acquisitions ORDER BY retrieved_at DESC LIMIT %s
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "id": str(row[0]),
            "source": row[1],
            "query": row[2],
            "retrieved_at": row[3],
            "sha256": row[4],
            "item_count": row[5],
            "raw_path": row[6],
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
