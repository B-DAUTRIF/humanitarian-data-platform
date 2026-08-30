from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from psycopg.types.json import Jsonb

from .v6_actions import action_status


AUTOMATIC_ACTION_TYPES = frozenset(
    {
        "notification",
        "classification",
        "hdp_task",
        "data_search",
        "data_refresh",
        "legacy_datagrid_search_and_due_refresh",
    }
)
DRAFT_ACTION_TYPES = frozenset({"email_draft", "spip_draft"})
EXECUTABLE_ACTION_TYPES = AUTOMATIC_ACTION_TYPES | DRAFT_ACTION_TYPES
TERMINAL_REQUEST_STATUSES = frozenset({"completed", "failed", "rejected", "cancelled"})


class ActionQueueError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ActionQueueError(f"{field}: objet attendu")
    return dict(value)


def _bounded_text(value: Any, default: str, *, maximum: int, field: str) -> str:
    text = default if value is None else str(value).strip()
    if not text or len(text) > maximum:
        raise ActionQueueError(f"{field}: texte requis de 1 à {maximum} caractères")
    return text


def _insert_idempotent(
    connection: Any,
    insert_query: str,
    insert_parameters: tuple[Any, ...],
    select_query: str,
    request_id: uuid.UUID,
) -> tuple[uuid.UUID, bool]:
    inserted = connection.execute(insert_query, insert_parameters).fetchone()
    if inserted:
        return inserted[0], False
    existing = connection.execute(select_query, (request_id,)).fetchone()
    if not existing:
        raise ActionQueueError("L'effet idempotent n'a pas pu être retrouvé")
    return existing[0], True


def recover_stale_action_requests(connection: Any, now: datetime, *, limit: int = 100) -> int:
    rows = connection.execute(
        """SELECT id,attempt_count,max_attempts,cancel_requested_at,project_id
           FROM action_requests
           WHERE status IN ('running','cancel_requested')
             AND lease_expires_at IS NOT NULL AND lease_expires_at <= %s
           ORDER BY lease_expires_at,id
           FOR UPDATE SKIP LOCKED LIMIT %s""",
        (now, limit),
    ).fetchall()
    for request_id, attempt_count, max_attempts, cancel_requested_at, project_id in rows:
        if cancel_requested_at is not None:
            status, error, next_attempt_at = "cancelled", "cancel_requested_before_lease_expiry", None
        elif int(attempt_count) < int(max_attempts):
            status, error, next_attempt_at = "queued", "worker_lease_expired", now
        else:
            status, error, next_attempt_at = "failed", "worker_lease_expired_max_attempts", None
        connection.execute(
            """UPDATE action_requests
               SET status=%s,next_attempt_at=%s,lease_owner=NULL,lease_expires_at=NULL,
                   completed_at=CASE WHEN %s IN ('failed','cancelled') THEN %s ELSE completed_at END,
                   cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END,
                   last_error=%s
               WHERE id=%s""",
            (status, next_attempt_at, status, now, status, now, error, request_id),
        )
        execution_status = "cancelled" if status == "cancelled" else "failed"
        connection.execute(
            """UPDATE action_executions
               SET status=%s,error=%s,finished_at=%s
               WHERE request_id=%s AND attempt_number=%s AND status='running'""",
            (execution_status, error, now, request_id, attempt_count),
        )
        _record_timeline(
            connection,
            {"id": request_id, "project_id": project_id, "worker_id": "lease-recovery"},
            "action.lease_expired",
            status,
            "Bail d'action expiré",
            {"attempt": int(attempt_count), "outcome": status, "error": error},
            now,
        )
    return len(rows)


def claim_next_action_request(
    connection: Any,
    worker_id: str,
    now: datetime | None = None,
    *,
    lease_seconds: int = 120,
) -> dict[str, Any] | None:
    if not 5 <= lease_seconds <= 900:
        raise ActionQueueError("Le bail doit être compris entre 5 et 900 secondes")
    if not worker_id.strip() or len(worker_id) > 120:
        raise ActionQueueError("Identifiant de travailleur invalide")
    claimed_at = now or datetime.now(UTC)
    recover_stale_action_requests(connection, claimed_at)
    row = connection.execute(
        """SELECT r.id,r.project_id,r.evaluation_id,r.action_type,r.risk_level,r.parameters,
                  r.limits,r.idempotency_key,r.attempt_count,r.max_attempts,r.status
           FROM action_requests r
           WHERE r.status IN ('queued','approved')
             AND r.action_type=ANY(%s)
             AND r.cancel_requested_at IS NULL
             AND (r.next_attempt_at IS NULL OR r.next_attempt_at <= %s)
           ORDER BY r.requested_at,r.id
           FOR UPDATE SKIP LOCKED LIMIT 1""",
        (list(sorted(EXECUTABLE_ACTION_TYPES)), claimed_at),
    ).fetchone()
    if not row:
        return None
    request_id = row[0]
    attempt_number = int(row[8]) + 1
    lease_expires_at = claimed_at + timedelta(seconds=lease_seconds)
    execution_id = uuid.uuid4()
    request = {
        "id": request_id,
        "project_id": row[1],
        "evaluation_id": row[2],
        "action_type": row[3],
        "risk_level": row[4],
        "parameters": dict(row[5] or {}),
        "limits": dict(row[6] or {}),
        "idempotency_key": row[7],
        "attempt_number": attempt_number,
        "max_attempts": int(row[9]),
        "execution_id": execution_id,
        "worker_id": worker_id,
        "lease_expires_at": lease_expires_at,
        "approved_override": row[10] == "approved",
    }
    input_sha256 = _sha256(
        {
            "request_id": str(request_id),
            "action_type": row[3],
            "parameters": request["parameters"],
            "limits": request["limits"],
            "idempotency_key": row[7],
        }
    )
    connection.execute(
        """UPDATE action_requests
           SET status='running',attempt_count=%s,lease_owner=%s,lease_expires_at=%s,
               last_error=NULL
           WHERE id=%s""",
        (attempt_number, worker_id, lease_expires_at, request_id),
    )
    connection.execute(
        """INSERT INTO action_executions
           (id,request_id,attempt_number,status,input_sha256,result,started_at,worker_id)
           VALUES (%s,%s,%s,'running',%s,'{}'::jsonb,%s,%s)""",
        (execution_id, request_id, attempt_number, input_sha256, claimed_at, worker_id),
    )
    return request


def _create_effect(
    connection: Any,
    request: Mapping[str, Any],
    triggering_event_id: uuid.UUID | None,
    now: datetime,
) -> dict[str, Any]:
    request_id = request["id"]
    project_id = request["project_id"]
    action_type = str(request["action_type"])
    parameters = _mapping(request.get("parameters", {}), "parameters")
    effect_id = uuid.uuid5(request_id, action_type)
    if action_type == "notification":
        severity = str(parameters.get("severity", "info")).casefold()
        if severity not in {"info", "warning", "critical"}:
            raise ActionQueueError("notification.severity: valeur invalide")
        title = _bounded_text(parameters.get("title"), "Notification HDP", maximum=200, field="notification.title")
        body = str(parameters.get("body", ""))[:4000]
        stored_id, repeated = _insert_idempotent(
            connection,
            """INSERT INTO internal_notifications
               (id,project_id,request_id,title,body,severity,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (request_id) DO NOTHING RETURNING id""",
            (effect_id, project_id, request_id, title, body, severity, now),
            "SELECT id FROM internal_notifications WHERE request_id=%s",
            request_id,
        )
        return {"effect_type": "internal_notification", "effect_id": str(stored_id), "idempotent_replay": repeated}
    if action_type == "hdp_task":
        priority = str(parameters.get("priority", "normal")).casefold()
        if priority not in {"low", "normal", "high", "urgent"}:
            raise ActionQueueError("hdp_task.priority: valeur invalide")
        title = _bounded_text(parameters.get("title"), "Tâche HDP", maximum=200, field="hdp_task.title")
        description = str(parameters.get("description", ""))[:10_000]
        stored_id, repeated = _insert_idempotent(
            connection,
            """INSERT INTO project_tasks
               (id,project_id,request_id,title,description,priority,status,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,'open',%s,%s)
               ON CONFLICT (request_id) DO NOTHING RETURNING id""",
            (effect_id, project_id, request_id, title, description, priority, now, now),
            "SELECT id FROM project_tasks WHERE request_id=%s",
            request_id,
        )
        return {"effect_type": "project_task", "effect_id": str(stored_id), "idempotent_replay": repeated}
    if action_type == "classification":
        if triggering_event_id is None:
            raise ActionQueueError("classification: aucun signal déclencheur disponible")
        labels = parameters.get("labels", [])
        if not isinstance(labels, list) or len(labels) > 100 or any(not isinstance(item, str) or not item.strip() or len(item) > 120 for item in labels):
            raise ActionQueueError("classification.labels: liste invalide")
        normalized_labels = sorted({item.strip() for item in labels})
        stored_id, repeated = _insert_idempotent(
            connection,
            """INSERT INTO signal_classifications
               (id,project_id,request_id,signal_event_id,labels,created_at)
               VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (request_id) DO NOTHING RETURNING id""",
            (effect_id, project_id, request_id, triggering_event_id, Jsonb(normalized_labels), now),
            "SELECT id FROM signal_classifications WHERE request_id=%s",
            request_id,
        )
        return {"effect_type": "signal_classification", "effect_id": str(stored_id), "idempotent_replay": repeated}
    if action_type in {"data_search", "data_refresh", "legacy_datagrid_search_and_due_refresh"}:
        stored_id, repeated = _insert_idempotent(
            connection,
            """INSERT INTO automated_data_jobs
               (id,project_id,request_id,job_type,parameters,status,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,'queued',%s,%s)
               ON CONFLICT (request_id) DO NOTHING RETURNING id""",
            (effect_id, project_id, request_id, action_type, Jsonb(parameters), now, now),
            "SELECT id FROM automated_data_jobs WHERE request_id=%s",
            request_id,
        )
        return {"effect_type": "automated_data_job", "effect_id": str(stored_id), "job_status": "queued", "idempotent_replay": repeated}
    if action_type in DRAFT_ACTION_TYPES:
        channel = "email" if action_type == "email_draft" else "spip"
        document = _mapping(parameters.get("document", {}), f"{action_type}.document")
        content_sha256 = _sha256(document)
        stored_id, repeated = _insert_idempotent(
            connection,
            """INSERT INTO action_drafts
               (id,project_id,request_id,channel,status,document,content_sha256,created_at,updated_at)
               VALUES (%s,%s,%s,%s,'draft',%s,%s,%s,%s)
               ON CONFLICT (request_id) DO NOTHING RETURNING id""",
            (effect_id, project_id, request_id, channel, Jsonb(document), content_sha256, now, now),
            "SELECT id FROM action_drafts WHERE request_id=%s",
            request_id,
        )
        return {"effect_type": f"{channel}_draft", "effect_id": str(stored_id), "status": "draft", "content_sha256": content_sha256, "idempotent_replay": repeated}
    raise ActionQueueError(f"Aucun exécuteur autorisé pour {action_type}")


def execute_claimed_action_request(
    connection: Any,
    request: Mapping[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    finished_at = now or datetime.now(UTC)
    row = connection.execute(
        """SELECT r.status,r.project_id,r.action_type,r.parameters,r.limits,r.attempt_count,
                  r.lease_owner,e.triggering_event_id,
                  COALESCE(p.automatic_request_limit,100),
                  COALESCE(p.automatic_download_bytes,104857600),
                  COALESCE(p.automatic_duration_seconds,300)
           FROM action_requests r
           JOIN rule_evaluations e ON e.id=r.evaluation_id
           LEFT JOIN project_data_policies p ON p.project_id=r.project_id
           WHERE r.id=%s FOR UPDATE OF r""",
        (request["id"],),
    ).fetchone()
    if not row:
        raise ActionQueueError("Demande d'action introuvable")
    if row[5] != request["attempt_number"] or row[6] != request["worker_id"]:
        raise ActionQueueError("Le bail de la demande n'appartient plus à ce travailleur")
    if row[0] == "cancel_requested":
        connection.execute(
            """UPDATE action_requests SET status='cancelled',cancelled_at=%s,completed_at=%s,
                      lease_owner=NULL,lease_expires_at=NULL,last_error=NULL WHERE id=%s""",
            (finished_at, finished_at, request["id"]),
        )
        connection.execute(
            """UPDATE action_executions SET status='cancelled',error='cancel_requested',finished_at=%s
               WHERE id=%s AND status='running'""",
            (finished_at, request["execution_id"]),
        )
        _record_timeline(connection, request, "action.cancelled", "cancelled", "Action annulée", {"attempt": row[5]}, finished_at)
        return {"request_id": str(request["id"]), "status": "cancelled"}
    if row[0] != "running":
        raise ActionQueueError(f"État non exécutable: {row[0]}")
    current_status, reason = action_status(
        {"type": row[2], "parameters": dict(row[3] or {}), "limits": dict(row[4] or {})},
        int(row[8]),
        int(row[9]),
        int(row[10]),
    )
    if current_status == "pending_approval" and not request.get("approved_override", False):
        connection.execute(
            """UPDATE action_requests SET status='pending_approval',decision_reason=%s,
                      lease_owner=NULL,lease_expires_at=NULL,last_error=NULL WHERE id=%s""",
            (reason, request["id"]),
        )
        connection.execute(
            """UPDATE action_executions SET status='blocked',error=%s,finished_at=%s
               WHERE id=%s AND status='running'""",
            (reason, finished_at, request["execution_id"]),
        )
        _record_timeline(connection, request, "action.pending_approval", "blocked", "Action suspendue avant effet", {"reason": reason}, finished_at)
        return {"request_id": str(request["id"]), "status": "pending_approval", "reason": reason}
    effective_request = {**request, "project_id": row[1], "action_type": row[2], "parameters": dict(row[3] or {}), "limits": dict(row[4] or {})}
    result = _create_effect(connection, effective_request, row[7], finished_at)
    output_sha256 = _sha256(result)
    connection.execute(
        """UPDATE action_requests SET status='completed',completed_at=%s,
                  lease_owner=NULL,lease_expires_at=NULL,last_error=NULL WHERE id=%s""",
        (finished_at, request["id"]),
    )
    connection.execute(
        """UPDATE action_executions SET status='completed',output_sha256=%s,result=%s,
                  finished_at=%s WHERE id=%s AND status='running'""",
        (output_sha256, Jsonb(result), finished_at, request["execution_id"]),
    )
    _record_timeline(connection, request, "action.completed", "completed", "Action interne exécutée", {**result, "output_sha256": output_sha256}, finished_at)
    return {
        "request_id": str(request["id"]),
        **result,
        "output_sha256": output_sha256,
        "status": "completed",
    }


def _record_timeline(
    connection: Any,
    request: Mapping[str, Any],
    event_type: str,
    status: str,
    summary: str,
    details: Mapping[str, Any],
    occurred_at: datetime,
) -> None:
    connection.execute(
        """INSERT INTO application_timeline
           (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
           VALUES (%s,%s,'project',%s,'action_request',%s,%s,%s,%s,%s,%s)""",
        (
            uuid.uuid4(),
            request["project_id"],
            event_type,
            str(request["id"]),
            status,
            summary,
            Jsonb(dict(details)),
            request.get("worker_id", "local-operator"),
            occurred_at,
        ),
    )


def mark_action_request_failed(
    connection: Any,
    request: Mapping[str, Any],
    error: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    failed_at = now or datetime.now(UTC)
    row = connection.execute(
        """SELECT status,attempt_count,max_attempts,cancel_requested_at,project_id
           FROM action_requests WHERE id=%s FOR UPDATE""",
        (request["id"],),
    ).fetchone()
    if not row:
        raise ActionQueueError("Demande d'action introuvable après échec")
    if row[0] not in {"running", "cancel_requested"}:
        return {"request_id": str(request["id"]), "status": row[0], "ignored": True}
    clean_error = str(error).replace("\x00", "")[:2000] or "action_failed"
    if row[3] is not None or row[0] == "cancel_requested":
        status, next_attempt_at = "cancelled", None
    elif int(row[1]) < int(row[2]):
        status = "queued"
        next_attempt_at = failed_at + timedelta(seconds=min(300, 2 ** max(0, int(row[1]) - 1)))
    else:
        status, next_attempt_at = "failed", None
    connection.execute(
        """UPDATE action_requests SET status=%s,next_attempt_at=%s,last_error=%s,
                  lease_owner=NULL,lease_expires_at=NULL,
                  completed_at=CASE WHEN %s IN ('failed','cancelled') THEN %s ELSE completed_at END,
                  cancelled_at=CASE WHEN %s='cancelled' THEN %s ELSE cancelled_at END
           WHERE id=%s""",
        (status, next_attempt_at, clean_error, status, failed_at, status, failed_at, request["id"]),
    )
    execution_status = "cancelled" if status == "cancelled" else "failed"
    connection.execute(
        """UPDATE action_executions SET status=%s,error=%s,finished_at=%s
           WHERE id=%s AND status='running'""",
        (execution_status, clean_error, failed_at, request["execution_id"]),
    )
    retry = status == "queued"
    _record_timeline(
        connection,
        {**request, "project_id": row[4]},
        "action.retry_scheduled" if retry else f"action.{status}",
        "queued" if retry else status,
        "Nouvelle tentative d'action planifiée" if retry else "Action non exécutée",
        {
            "error": clean_error,
            "attempt": int(row[1]),
            "next_attempt_at": next_attempt_at.isoformat() if next_attempt_at else None,
        },
        failed_at,
    )
    return {"request_id": str(request["id"]), "status": status, "next_attempt_at": next_attempt_at, "error": clean_error}


def decide_action_request(
    connection: Any,
    request_id: uuid.UUID,
    decision: str,
    actor: str,
    reason: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    decided_at = now or datetime.now(UTC)
    if decision not in {"approve", "reject"}:
        raise ActionQueueError("Décision invalide")
    row = connection.execute(
        "SELECT project_id,status,action_type FROM action_requests WHERE id=%s FOR UPDATE",
        (request_id,),
    ).fetchone()
    if not row:
        raise ActionQueueError("Demande d'action introuvable")
    if row[1] != "pending_approval":
        raise ActionQueueError(f"La demande n'attend pas de décision: {row[1]}")
    status = "approved" if decision == "approve" else "rejected"
    connection.execute(
        """UPDATE action_requests SET status=%s,decided_at=%s,decided_by=%s,
                  decision_reason=%s,completed_at=CASE WHEN %s='rejected' THEN %s ELSE NULL END,
                  next_attempt_at=CASE WHEN %s='approved' THEN %s ELSE NULL END
           WHERE id=%s""",
        (status, decided_at, actor, reason, status, decided_at, status, decided_at, request_id),
    )
    request = {"id": request_id, "project_id": row[0], "worker_id": actor}
    _record_timeline(connection, request, f"action.{status}", status, f"Action {status}", {"action_type": row[2], "reason": reason}, decided_at)
    return {"id": str(request_id), "status": status, "action_type": row[2]}


def cancel_action_request(
    connection: Any,
    request_id: uuid.UUID,
    actor: str,
    reason: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    cancelled_at = now or datetime.now(UTC)
    row = connection.execute(
        "SELECT project_id,status FROM action_requests WHERE id=%s FOR UPDATE",
        (request_id,),
    ).fetchone()
    if not row:
        raise ActionQueueError("Demande d'action introuvable")
    if row[1] in TERMINAL_REQUEST_STATUSES:
        return {"id": str(request_id), "status": row[1], "changed": False}
    if row[1] in {"running", "cancel_requested"}:
        status = "cancel_requested"
        connection.execute(
            """UPDATE action_requests SET status='cancel_requested',cancel_requested_at=COALESCE(cancel_requested_at,%s),
                      decided_by=%s,decision_reason=%s WHERE id=%s""",
            (cancelled_at, actor, reason, request_id),
        )
    else:
        status = "cancelled"
        connection.execute(
            """UPDATE action_requests SET status='cancelled',cancel_requested_at=%s,cancelled_at=%s,
                      completed_at=%s,decided_by=%s,decision_reason=%s,
                      lease_owner=NULL,lease_expires_at=NULL,next_attempt_at=NULL WHERE id=%s""",
            (cancelled_at, cancelled_at, cancelled_at, actor, reason, request_id),
        )
    request = {"id": request_id, "project_id": row[0], "worker_id": actor}
    _record_timeline(connection, request, f"action.{status}", status, "Annulation d'action demandée", {"previous_status": row[1], "reason": reason}, cancelled_at)
    return {"id": str(request_id), "status": status, "changed": True}
