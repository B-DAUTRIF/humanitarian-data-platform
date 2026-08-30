from __future__ import annotations

"""Persistent jobs, exports and reproducibility for HDP V7 semantic searches."""

import asyncio
import csv
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from psycopg.types.json import Jsonb

from .v6_semantic_api import SemanticSearchRequest, semantic_search

router = APIRouter(prefix="/api/semantic/jobs", tags=["semantic-router-jobs"])
_TASKS: dict[uuid.UUID, asyncio.Task[None]] = {}


def _connection():
    from .main import database_connection
    return database_connection()


def recover_abandoned_semantic_jobs() -> int:
    """Never present work interrupted by a service restart as successful."""
    with _connection() as connection:
        cursor = connection.execute(
            """UPDATE semantic_jobs SET status='failed', progress=0,
               error='Exécution interrompue par un redémarrage du service HDP.',
               finished_at=now() WHERE status IN ('queued','running')"""
        )
        return int(cursor.rowcount or 0)


def _job_row(job_id: uuid.UUID) -> dict[str, Any]:
    with _connection() as connection:
        row = connection.execute(
            """SELECT id, project_id, status, progress, cancel_requested, result_json,
                      error, created_at, started_at, finished_at
               FROM semantic_jobs WHERE id=%s""",
            (job_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job sémantique introuvable")
    keys = ("id", "project_id", "status", "progress", "cancel_requested", "result", "error", "created_at", "started_at", "finished_at")
    result = dict(zip(keys, row, strict=True))
    result["id"], result["project_id"] = str(result["id"]), str(result["project_id"])
    return result


def _update(job_id: uuid.UUID, **values: Any) -> None:
    allowed = {"status", "progress", "cancel_requested", "result_json", "error", "started_at", "finished_at"}
    if not values or set(values) - allowed:
        raise ValueError("Invalid semantic job update")
    assignments, params = [], []
    for key, value in values.items():
        assignments.append(f"{key}=%s")
        params.append(Jsonb(value) if key == "result_json" and value is not None else value)
    params.append(job_id)
    with _connection() as connection:
        connection.execute(f"UPDATE semantic_jobs SET {', '.join(assignments)} WHERE id=%s", tuple(params))


def _cancel_requested(job_id: uuid.UUID) -> bool:
    with _connection() as connection:
        row = connection.execute("SELECT cancel_requested FROM semantic_jobs WHERE id=%s", (job_id,)).fetchone()
    return bool(row and row[0])


async def _run(job_id: uuid.UUID, payload: SemanticSearchRequest) -> None:
    try:
        if _cancel_requested(job_id):
            _update(job_id, status="cancelled", progress=0, finished_at=datetime.now(UTC))
            return
        _update(job_id, status="running", progress=5, started_at=datetime.now(UTC), error=None)
        result = await semantic_search(payload)
        if _cancel_requested(job_id):
            _update(job_id, status="cancelled", progress=100, result_json=result, finished_at=datetime.now(UTC))
            return
        state = "completed" if result.get("status") == "success" else "partial"
        _update(job_id, status=state, progress=100, result_json=result, finished_at=datetime.now(UTC))
    except asyncio.CancelledError:
        _update(job_id, status="cancelled", progress=100, finished_at=datetime.now(UTC))
        raise
    except Exception as exc:
        _update(job_id, status="failed", progress=100, error=f"{type(exc).__name__}: {exc}", finished_at=datetime.now(UTC))
    finally:
        _TASKS.pop(job_id, None)


def _repro_script(payload: SemanticSearchRequest, language: str) -> str:
    body = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2)
    if language == "python":
        return f'''# Reproduction HDP V7 — aucun secret incorporé\nimport os, httpx\npayload = {body}\nbase = os.getenv("HDP_URL", "http://localhost:8080").rstrip("/")\ntoken = os.getenv("HDP_LOCAL_TOKEN", "")\nheaders = {{"Accept": "application/json"}}\nif token:\n    headers.update({{"Authorization": f"Bearer {{token}}", "X-HDP-CSRF": "1"}})\nr = httpx.post(base + "/api/semantic/search", json=payload, headers=headers, timeout=120)\nr.raise_for_status()\nresult = r.json()\nprint(result["query_fingerprint"], result["status"], result["item_count"])\n'''
    if language == "r":
        r_body = body.replace("\\", "\\\\").replace("'", "\\'")
        return f'''# Reproduction HDP V7 — aucun secret incorporé\nlibrary(httr2)\nlibrary(jsonlite)\npayload <- fromJSON('{r_body}', simplifyVector = FALSE)\nbase <- sub('/$', '', Sys.getenv('HDP_URL', 'http://localhost:8080'))\ntoken <- Sys.getenv('HDP_LOCAL_TOKEN', '')\nreq <- request(paste0(base, '/api/semantic/search')) |> req_headers(Accept='application/json') |> req_body_json(payload, auto_unbox=TRUE)\nif (nzchar(token)) req <- req |> req_headers(Authorization=paste('Bearer', token), `X-HDP-CSRF`='1')\nres <- req_perform(req) |> resp_body_json(simplifyVector=FALSE)\ncat(res$query_fingerprint, res$status, res$item_count, '\\n')\n'''
    raise HTTPException(status_code=422, detail="Langage de reproduction attendu: python ou r")


@router.post("/reproducibility/{language}")
def reproducibility_script(language: str, payload: SemanticSearchRequest) -> Response:
    script = _repro_script(payload, language.casefold())
    media = "text/x-python" if language.casefold() == "python" else "text/x-r"
    return Response(content=script, media_type=media, headers={"Content-Disposition": f'attachment; filename="hdp_semantic_reproduce.{"py" if language.casefold()=="python" else "R"}"'})


@router.post("")
async def create_semantic_job(payload: SemanticSearchRequest) -> dict[str, Any]:
    from .main import ensure_project
    ensure_project(payload.project_id)
    job_id = uuid.uuid4()
    with _connection() as connection:
        connection.execute(
            """INSERT INTO semantic_jobs (id, project_id, request_json, status, progress, created_at)
               VALUES (%s,%s,%s,'queued',0,%s)""",
            (job_id, payload.project_id, Jsonb(payload.model_dump(mode="json")), datetime.now(UTC)),
        )
    _TASKS[job_id] = asyncio.create_task(_run(job_id, payload), name=f"semantic-job-{job_id}")
    return {"job_id": str(job_id), "status": "queued", "project_id": str(payload.project_id)}


@router.get("/{job_id}")
def get_semantic_job(job_id: uuid.UUID) -> dict[str, Any]:
    return _job_row(job_id)


@router.post("/{job_id}/cancel")
def cancel_semantic_job(job_id: uuid.UUID) -> dict[str, Any]:
    job = _job_row(job_id)
    if job["status"] in {"completed", "partial", "failed", "cancelled"}:
        return job
    _update(job_id, cancel_requested=True)
    task = _TASKS.get(job_id)
    if task and not task.done():
        task.cancel()
    return {**_job_row(job_id), "cancel_requested": True}


@router.get("/{job_id}/export/{format_name}")
def export_semantic_job(job_id: uuid.UUID, format_name: str) -> Response:
    job = _job_row(job_id)
    result = job.get("result")
    if not isinstance(result, dict):
        raise HTTPException(status_code=409, detail="Le job ne possède pas encore de résultat exportable")
    fmt = format_name.casefold()
    filename = f"hdp-semantic-{job_id}.{fmt}"
    if fmt == "json":
        return Response(json.dumps(result, ensure_ascii=False, indent=2, default=str), media_type="application/json", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    items = result.get("items") if isinstance(result.get("items"), list) else []
    if fmt == "csv":
        fields = sorted({str(key) for item in items if isinstance(item, dict) for key in item})
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            if isinstance(item, dict):
                writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in item.items()})
        return Response(stream.getvalue(), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    if fmt == "geojson":
        features = []
        for item in items:
            if isinstance(item, dict) and isinstance(item.get("geometry"), dict):
                properties = {key: value for key, value in item.items() if key != "geometry"}
                features.append({"type": "Feature", "geometry": item["geometry"], "properties": properties})
        if not features:
            raise HTTPException(status_code=422, detail="Aucune géométrie native disponible; HDP refuse d'inventer une géométrie")
        collection = {"type": "FeatureCollection", "features": features}
        return Response(json.dumps(collection, ensure_ascii=False, default=str), media_type="application/geo+json", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    raise HTTPException(status_code=422, detail="Format d'export attendu: json, csv ou geojson")
