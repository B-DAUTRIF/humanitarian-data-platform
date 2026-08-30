from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from psycopg.types.json import Jsonb


TERMINAL_DATA_JOB_STATUSES = frozenset({"completed", "partial", "failed", "cancelled"})
SOURCE_ID = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?$")
SECRET_MARKERS = ("password", "secret", "token", "api_key", "authorization", "cookie")
ESTIMATE_KEYS = frozenset({"estimated_requests", "estimated_bytes", "estimated_duration_seconds"})
PARAMETER_KEYS = frozenset({"source", "sources", "query", "result_limit", "source_parameters"}) | ESTIMATE_KEYS


class DataJobError(ValueError):
    pass


def _contains_sensitive_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(marker in str(key).casefold() for marker in SECRET_MARKERS)
            or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def validate_data_job_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, Mapping):
        raise DataJobError("data_job.parameters: objet attendu")
    unknown = sorted(set(parameters) - PARAMETER_KEYS)
    if unknown:
        raise DataJobError(f"data_job.parameters: champs inconnus: {unknown}")
    if _contains_sensitive_key(parameters):
        raise DataJobError("data_job.parameters: aucun secret n'est autorisé")
    singular = parameters.get("source")
    plural = parameters.get("sources")
    if singular is not None and plural is not None:
        raise DataJobError("data_job.parameters: utiliser source ou sources, pas les deux")
    raw_sources = [singular] if singular is not None else plural
    if not isinstance(raw_sources, list) or not 1 <= len(raw_sources) <= 10:
        raise DataJobError("data_job.parameters.sources: une à dix sources explicites sont requises")
    sources: list[str] = []
    for item in raw_sources:
        source = str(item).strip().casefold() if isinstance(item, str) else ""
        if not SOURCE_ID.fullmatch(source):
            raise DataJobError("data_job.parameters.sources: identifiant de source invalide")
        if source not in sources:
            sources.append(source)
    query = parameters.get("query")
    if not isinstance(query, str) or not 2 <= len(query.strip()) <= 500:
        raise DataJobError("data_job.parameters.query: texte requis de 2 à 500 caractères")
    result_limit = parameters.get("result_limit", 25)
    if type(result_limit) is not int or not 1 <= result_limit <= 100:
        raise DataJobError("data_job.parameters.result_limit: entier requis de 1 à 100")
    raw_source_parameters = parameters.get("source_parameters", {})
    if not isinstance(raw_source_parameters, Mapping):
        raise DataJobError("data_job.parameters.source_parameters: objet attendu")
    unexpected_sources = sorted(set(raw_source_parameters) - set(sources))
    if unexpected_sources:
        raise DataJobError(
            f"data_job.parameters.source_parameters: sources non sélectionnées: {unexpected_sources}"
        )
    source_parameters: dict[str, dict[str, Any]] = {}
    for source in sources:
        values = raw_source_parameters.get(source, {})
        if not isinstance(values, Mapping):
            raise DataJobError(f"data_job.parameters.source_parameters.{source}: objet attendu")
        source_parameters[source] = dict(values)
    return {
        "sources": sources,
        "query": query.strip(),
        "result_limit": result_limit,
        "source_parameters": source_parameters,
    }


def _record_timeline(
    connection: Any,
    job_id: uuid.UUID,
    project_id: uuid.UUID,
    event_type: str,
    status: str,
    summary: str,
    details: Mapping[str, Any],
    actor: str,
    occurred_at: datetime,
) -> None:
    connection.execute(
        """INSERT INTO application_timeline
           (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
           VALUES (%s,%s,'project',%s,'automated_data_job',%s,%s,%s,%s,%s,%s)""",
        (
            uuid.uuid4(), project_id, event_type, str(job_id), status, summary,
            Jsonb(dict(details)), actor, occurred_at,
        ),
    )


def recover_stale_data_jobs(connection: Any, now: datetime, *, limit: int = 100) -> int:
    rows = connection.execute(
        """SELECT j.id,j.project_id,j.attempt_count,j.max_attempts,j.cancel_requested_at,
                  EXISTS(SELECT 1 FROM acquisitions a WHERE a.automated_data_job_id=j.id)
           FROM automated_data_jobs j
           WHERE j.status='running' AND j.lease_expires_at IS NOT NULL
             AND j.lease_expires_at<=%s
           ORDER BY j.lease_expires_at,j.id
           FOR UPDATE OF j SKIP LOCKED LIMIT %s""",
        (now, limit),
    ).fetchall()
    for job_id, project_id, attempts, maximum, cancel_requested_at, has_acquisition in rows:
        if cancel_requested_at is not None:
            status, error, next_attempt_at = "cancelled", "cancel_requested_before_lease_expiry", None
        elif has_acquisition:
            status, error, next_attempt_at = "partial", "worker_lease_expired_after_acquisition", None
        elif int(attempts) < int(maximum):
            status, error, next_attempt_at = "queued", "worker_lease_expired", now
        else:
            status, error, next_attempt_at = "failed", "worker_lease_expired_max_attempts", None
        connection.execute(
            """UPDATE automated_data_jobs
               SET status=%s,next_attempt_at=%s,lease_owner=NULL,lease_expires_at=NULL,
                   error=%s,updated_at=%s,
                   finished_at=CASE WHEN %s IN ('partial','failed','cancelled') THEN %s ELSE NULL END,
                   cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END
               WHERE id=%s""",
            (status, next_attempt_at, error, now, status, now, status, now, job_id),
        )
        _record_timeline(
            connection, job_id, project_id, "data_job.lease_expired", status,
            "Bail de travail de données expiré",
            {"attempt": int(attempts), "outcome": status, "error": error},
            "data-job-lease-recovery", now,
        )
    return len(rows)


def claim_next_data_job(
    connection: Any,
    worker_id: str,
    now: datetime | None = None,
    *,
    lease_seconds: int = 900,
) -> dict[str, Any] | None:
    if not worker_id.strip() or len(worker_id) > 120:
        raise DataJobError("Identifiant de travailleur de données invalide")
    if not 30 <= lease_seconds <= 1800:
        raise DataJobError("Le bail de données doit être compris entre 30 et 1800 secondes")
    claimed_at = now or datetime.now(UTC)
    recover_stale_data_jobs(connection, claimed_at)
    row = connection.execute(
        """SELECT id,project_id,request_id,job_type,parameters,attempt_count,max_attempts
           FROM automated_data_jobs
           WHERE status='queued' AND cancel_requested_at IS NULL
             AND (next_attempt_at IS NULL OR next_attempt_at<=%s)
           ORDER BY created_at,id FOR UPDATE SKIP LOCKED LIMIT 1""",
        (claimed_at,),
    ).fetchone()
    if not row:
        return None
    attempt = int(row[5]) + 1
    lease_expires_at = claimed_at + timedelta(seconds=lease_seconds)
    connection.execute(
        """UPDATE automated_data_jobs
           SET status='running',attempt_count=%s,lease_owner=%s,lease_expires_at=%s,
               next_attempt_at=NULL,error=NULL,started_at=COALESCE(started_at,%s),updated_at=%s
           WHERE id=%s""",
        (attempt, worker_id, lease_expires_at, claimed_at, claimed_at, row[0]),
    )
    _record_timeline(
        connection, row[0], row[1], "data_job.claimed", "running",
        "Travail de données réclamé",
        {"job_type": row[3], "attempt": attempt, "lease_expires_at": lease_expires_at.isoformat()},
        worker_id, claimed_at,
    )
    return {
        "id": row[0], "project_id": row[1], "request_id": row[2], "job_type": row[3],
        "parameters": dict(row[4] or {}), "attempt_count": attempt,
        "max_attempts": int(row[6]), "worker_id": worker_id,
    }


def initialize_data_job_sources(
    connection: Any,
    job: Mapping[str, Any],
    sources: list[str],
    now: datetime | None = None,
) -> None:
    updated_at = now or datetime.now(UTC)
    for source in sources:
        connection.execute(
            """INSERT INTO automated_data_job_results
               (job_id,source_id,status,updated_at)
               VALUES (%s,%s,'queued',%s)
               ON CONFLICT (job_id,source_id) DO NOTHING""",
            (job["id"], source, updated_at),
        )


def begin_data_job_source(
    connection: Any,
    job: Mapping[str, Any],
    source: str,
    now: datetime | None = None,
    *,
    lease_seconds: int = 900,
) -> dict[str, Any]:
    started_at = now or datetime.now(UTC)
    row = connection.execute(
        """SELECT r.status,r.attempt_count,COALESCE(r.acquisition_id,a.id),r.result,
                  j.status,j.cancel_requested_at,a.retrieved_at,a.sha256,a.item_count,a.raw_path
           FROM automated_data_job_results r
           JOIN automated_data_jobs j ON j.id=r.job_id
           LEFT JOIN acquisitions a
             ON a.automated_data_job_id=r.job_id AND a.automated_data_job_source=r.source_id
           WHERE r.job_id=%s AND r.source_id=%s FOR UPDATE OF r,j""",
        (job["id"], source),
    ).fetchone()
    if not row:
        raise DataJobError("Résultat de source introuvable")
    if row[0] == "completed" or row[2] is not None:
        recovered_result = dict(row[3] or {})
        if row[2] is not None and not recovered_result:
            recovered_result = {
                "acquisition_id": str(row[2]),
                "retrieved_at": row[6].isoformat() if row[6] else None,
                "sha256": row[7],
                "item_count": row[8],
                "raw_path": row[9],
                "recovered_after_interruption": True,
            }
            connection.execute(
                """UPDATE automated_data_job_results
                   SET status='completed',acquisition_id=%s,result=%s,error=NULL,
                       finished_at=%s,updated_at=%s
                   WHERE job_id=%s AND source_id=%s""",
                (row[2], Jsonb(recovered_result), started_at, started_at, job["id"], source),
            )
        return {
            "execute": False, "status": "completed", "acquisition_id": row[2],
            "result": recovered_result,
        }
    if row[4] != "running" or row[5] is not None:
        return {"execute": False, "status": "cancelled", "acquisition_id": None, "result": {}}
    connection.execute(
        """UPDATE automated_data_job_results
           SET status='running',attempt_count=attempt_count+1,error=NULL,
               started_at=COALESCE(started_at,%s),finished_at=NULL,updated_at=%s
           WHERE job_id=%s AND source_id=%s""",
        (started_at, started_at, job["id"], source),
    )
    connection.execute(
        """UPDATE automated_data_jobs SET lease_expires_at=%s,updated_at=%s WHERE id=%s""",
        (started_at + timedelta(seconds=lease_seconds), started_at, job["id"]),
    )
    return {"execute": True, "status": "running", "acquisition_id": None, "result": {}}


def finish_data_job_source(
    connection: Any,
    job: Mapping[str, Any],
    source: str,
    status: str,
    result: Mapping[str, Any] | None = None,
    *,
    acquisition_id: uuid.UUID | None = None,
    error: str | None = None,
    now: datetime | None = None,
) -> None:
    if status not in {"completed", "failed", "cancelled"}:
        raise DataJobError("Statut final de source invalide")
    finished_at = now or datetime.now(UTC)
    clean_error = str(error).replace("\x00", "")[:2000] if error else None
    connection.execute(
        """UPDATE automated_data_job_results
           SET status=%s,acquisition_id=COALESCE(%s,acquisition_id),result=%s,error=%s,
               finished_at=%s,updated_at=%s
           WHERE job_id=%s AND source_id=%s""",
        (
            status, acquisition_id, Jsonb(dict(result or {})), clean_error,
            finished_at, finished_at, job["id"], source,
        ),
    )


def data_job_cancel_requested(connection: Any, job_id: uuid.UUID) -> bool:
    row = connection.execute(
        "SELECT status,cancel_requested_at FROM automated_data_jobs WHERE id=%s",
        (job_id,),
    ).fetchone()
    return not row or row[0] != "running" or row[1] is not None


def finalize_data_job(connection: Any, job: Mapping[str, Any], now: datetime | None = None) -> dict[str, Any]:
    finished_at = now or datetime.now(UTC)
    rows = connection.execute(
        """SELECT source_id,status,acquisition_id,result,error
           FROM automated_data_job_results WHERE job_id=%s ORDER BY source_id""",
        (job["id"],),
    ).fetchall()
    if not rows:
        raise DataJobError("Aucun résultat de source à finaliser")
    statuses = [row[1] for row in rows]
    if all(status == "completed" for status in statuses):
        final_status = "completed"
    elif all(status == "cancelled" for status in statuses):
        final_status = "cancelled"
    elif any(status == "completed" for status in statuses):
        final_status = "partial"
    elif any(status == "failed" for status in statuses):
        final_status = "failed"
    else:
        final_status = "cancelled"
    sources = {
        row[0]: {
            "status": row[1],
            "acquisition_id": str(row[2]) if row[2] else None,
            "result": dict(row[3] or {}),
            "error": row[4],
        }
        for row in rows
    }
    summary = {status: statuses.count(status) for status in ("completed", "failed", "cancelled")}
    aggregate = {"sources": sources, "summary": summary}
    errors = "; ".join(f"{row[0]}: {row[4]}" for row in rows if row[4])[:2000] or None
    connection.execute(
        """UPDATE automated_data_jobs
           SET status=%s,result=%s,error=%s,lease_owner=NULL,lease_expires_at=NULL,
               finished_at=%s,cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END,
               updated_at=%s WHERE id=%s""",
        (
            final_status, Jsonb(aggregate), errors, finished_at,
            final_status, finished_at, finished_at, job["id"],
        ),
    )
    _record_timeline(
        connection, job["id"], job["project_id"], "data_job.finished", final_status,
        "Travail de données terminé", summary, job["worker_id"], finished_at,
    )
    return {"job_id": str(job["id"]), "status": final_status, **aggregate}


def complete_data_job_attempt(
    connection: Any,
    job: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    completed_at = now or datetime.now(UTC)
    job_row = connection.execute(
        "SELECT cancel_requested_at FROM automated_data_jobs WHERE id=%s FOR UPDATE",
        (job["id"],),
    ).fetchone()
    if not job_row:
        raise DataJobError("Travail de données introuvable à la finalisation")
    if job_row[0] is not None:
        connection.execute(
            """UPDATE automated_data_job_results
               SET status='cancelled',error=COALESCE(error,'cancel_requested'),
                   finished_at=%s,updated_at=%s
               WHERE job_id=%s AND status IN ('queued','running')""",
            (completed_at, completed_at, job["id"]),
        )
        return finalize_data_job(connection, job, completed_at)
    failed_rows = connection.execute(
        """SELECT source_id,error FROM automated_data_job_results
           WHERE job_id=%s AND status='failed' ORDER BY source_id""",
        (job["id"],),
    ).fetchall()
    if failed_rows and int(job["attempt_count"]) < int(job["max_attempts"]):
        error = "; ".join(f"{row[0]}: {row[1] or 'source_failed'}" for row in failed_rows)
        return mark_data_job_failed(connection, job, error, completed_at)
    return finalize_data_job(connection, job, completed_at)


def mark_data_job_failed(
    connection: Any,
    job: Mapping[str, Any],
    error: str,
    now: datetime | None = None,
    *,
    permanent: bool = False,
) -> dict[str, Any]:
    failed_at = now or datetime.now(UTC)
    row = connection.execute(
        """SELECT status,attempt_count,max_attempts,cancel_requested_at,project_id
           FROM automated_data_jobs WHERE id=%s FOR UPDATE""",
        (job["id"],),
    ).fetchone()
    if not row:
        raise DataJobError("Travail de données introuvable après échec")
    if row[0] in TERMINAL_DATA_JOB_STATUSES:
        return {"job_id": str(job["id"]), "status": row[0], "unchanged": True}
    clean_error = str(error).replace("\x00", "")[:2000] or "data_job_failed"
    if row[3] is not None:
        status, next_attempt_at = "cancelled", None
    elif not permanent and int(row[1]) < int(row[2]):
        status = "queued"
        next_attempt_at = failed_at + timedelta(seconds=min(300, 2 ** max(0, int(row[1]) - 1)))
    else:
        status, next_attempt_at = "failed", None
    connection.execute(
        """UPDATE automated_data_jobs
           SET status=%s,next_attempt_at=%s,error=%s,lease_owner=NULL,lease_expires_at=NULL,
               finished_at=CASE WHEN %s IN ('failed','cancelled') THEN %s ELSE NULL END,
               cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END,
               updated_at=%s WHERE id=%s""",
        (
            status, next_attempt_at, clean_error, status, failed_at,
            status, failed_at, failed_at, job["id"],
        ),
    )
    _record_timeline(
        connection, job["id"], row[4],
        "data_job.retry_scheduled" if status == "queued" else f"data_job.{status}",
        status, "Travail de données non exécuté",
        {"error": clean_error, "attempt": int(row[1]), "next_attempt_at": next_attempt_at.isoformat() if next_attempt_at else None},
        job.get("worker_id", "data-job-worker"), failed_at,
    )
    return {
        "job_id": str(job["id"]), "status": status, "error": clean_error,
        "next_attempt_at": next_attempt_at,
    }


def cancel_data_job(
    connection: Any,
    job_id: uuid.UUID,
    actor: str,
    reason: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    cancelled_at = now or datetime.now(UTC)
    row = connection.execute(
        """SELECT project_id,status FROM automated_data_jobs WHERE id=%s FOR UPDATE""",
        (job_id,),
    ).fetchone()
    if not row:
        raise DataJobError("Travail de données introuvable")
    if row[1] in TERMINAL_DATA_JOB_STATUSES:
        return {"job_id": str(job_id), "status": row[1], "unchanged": True}
    clean_reason = str(reason).replace("\x00", "")[:2000]
    if row[1] == "queued":
        status = "cancelled"
        connection.execute(
            """UPDATE automated_data_jobs
               SET status='cancelled',cancel_requested_at=%s,cancelled_at=%s,finished_at=%s,
                   error=%s,updated_at=%s WHERE id=%s""",
            (cancelled_at, cancelled_at, cancelled_at, clean_reason, cancelled_at, job_id),
        )
    else:
        status = "running"
        connection.execute(
            """UPDATE automated_data_jobs
               SET cancel_requested_at=%s,error=%s,updated_at=%s WHERE id=%s""",
            (cancelled_at, clean_reason, cancelled_at, job_id),
        )
    _record_timeline(
        connection, job_id, row[0], "data_job.cancel_requested", status,
        "Annulation du travail de données demandée", {"reason": clean_reason}, actor, cancelled_at,
    )
    return {"job_id": str(job_id), "status": status, "cancel_requested": True}
