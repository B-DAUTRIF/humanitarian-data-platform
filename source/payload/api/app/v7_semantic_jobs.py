from __future__ import annotations

"""Persistent, cancellable background execution for HDP V7 semantic searches."""

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from .v6_semantic_api import SemanticSearchRequest, semantic_search

router = APIRouter(prefix="/api/semantic/jobs", tags=["semantic-router-jobs"])
_TASKS: dict[uuid.UUID, asyncio.Task[None]] = {}


def _connection():
    from .main import database_connection

    return database_connection()


def recover_abandoned_semantic_jobs() -> int:
    """Mark jobs left active by a previous process as failed, never as completed."""
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE semantic_jobs
            SET status='failed', progress=0,
                error='Exécution interrompue par un redémarrage du service HDP.',
                finished_at=now()
            WHERE status IN ('queued','running')
            """
        )
        return int(cursor.rowcount or 0)


def _job_row(job_id: uuid.UUID) -> dict[str, Any]:
    with _connection() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, status, progress, cancel_requested, result_json,
                   error, created_at, started_at, finished_at
            FROM semantic_jobs WHERE id=%s
            """,
            (job_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Job sémantique introuvable")
    keys = (
        "id", "project_id", "status", "progress", "cancel_requested", "result",
        "error", "created_at", "started_at", "finished_at",
    )
    result = dict(zip(keys, row, strict=True))
    result["id"] = str(result["id"])
    result["project_id"] = str(result["project_id"])
    return result


def _update(job_id: uuid.UUID, **values: Any) -> None:
    allowed = {
        "status", "progress", "cancel_requested", "result_json", "error",
        "started_at", "finished_at",
    }
    if not values or set(values) - allowed:
        raise ValueError("Invalid semantic job update")
    assignments = []
    params: list[Any] = []
    for key, value in values.items():
        assignments.append(f"{key}=%s")
        params.append(Jsonb(value) if key == "result_json" and value is not None else value)
    params.append(job_id)
    with _connection() as connection:
        connection.execute(
            f"UPDATE semantic_jobs SET {', '.join(assignments)} WHERE id=%s",
            tuple(params),
        )


def _cancel_requested(job_id: uuid.UUID) -> bool:
    with _connection() as connection:
        row = connection.execute(
            "SELECT cancel_requested FROM semantic_jobs WHERE id=%s", (job_id,)
        ).fetchone()
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
        _update(
            job_id,
            status="failed",
            progress=100,
            error=f"{type(exc).__name__}: {exc}",
            finished_at=datetime.now(UTC),
        )
    finally:
        _TASKS.pop(job_id, None)


@router.post("")
async def create_semantic_job(payload: SemanticSearchRequest) -> dict[str, Any]:
    from .main import ensure_project

    ensure_project(payload.project_id)
    job_id = uuid.uuid4()
    request_json = payload.model_dump(mode="json")
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO semantic_jobs
                (id, project_id, request_json, status, progress, created_at)
            VALUES (%s,%s,%s,'queued',0,%s)
            """,
            (job_id, payload.project_id, Jsonb(request_json), datetime.now(UTC)),
        )
    task = asyncio.create_task(_run(job_id, payload), name=f"semantic-job-{job_id}")
    _TASKS[job_id] = task
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
