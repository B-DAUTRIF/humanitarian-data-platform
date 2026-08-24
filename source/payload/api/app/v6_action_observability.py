from __future__ import annotations

import uuid
from typing import Any


ACTION_REQUEST_KEYS = (
    "id",
    "evaluation_id",
    "action_type",
    "risk_level",
    "status",
    "parameters",
    "limits",
    "idempotency_key",
    "requested_at",
    "decided_at",
    "decided_by",
    "decision_reason",
    "attempt_count",
    "max_attempts",
    "next_attempt_at",
    "cancel_requested_at",
    "cancelled_at",
    "completed_at",
    "last_error",
    "last_execution_status",
    "last_started_at",
    "last_finished_at",
    "last_output_sha256",
    "last_result",
    "last_execution_error",
    "executions",
    "draft_id",
    "draft_channel",
    "draft_status",
    "draft_title",
    "draft_content_sha256",
    "draft_updated_at",
    "draft_decided_at",
    "draft_decided_by",
    "draft_decision_reason",
    "data_job_id",
    "data_job_status",
)


def list_project_action_requests(
    connection: Any,
    project_id: uuid.UUID,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    rows = connection.execute(
        """SELECT r.id,r.evaluation_id,r.action_type,r.risk_level,r.status,r.parameters,
                  r.limits,r.idempotency_key,r.requested_at,r.decided_at,r.decided_by,
                  r.decision_reason,r.attempt_count,r.max_attempts,r.next_attempt_at,
                  r.cancel_requested_at,r.cancelled_at,r.completed_at,r.last_error,
                  x.status,x.started_at,x.finished_at,x.output_sha256,x.result,x.error,
                  COALESCE((
                    SELECT jsonb_agg(jsonb_build_object(
                        'id',e.id,'attempt_number',e.attempt_number,'status',e.status,
                        'worker_id',e.worker_id,'started_at',e.started_at,
                        'finished_at',e.finished_at,'output_sha256',e.output_sha256,
                        'result',e.result,'error',e.error)
                        ORDER BY e.attempt_number)
                    FROM action_executions e WHERE e.request_id=r.id
                  ),'[]'::jsonb),
                  d.id,d.channel,d.status,
                  COALESCE(d.document->>'subject',d.document->>'title'),
                  d.content_sha256,d.updated_at,d.decided_at,d.decided_by,d.decision_reason,
                  j.id,j.status
           FROM action_requests r
           LEFT JOIN LATERAL (
                SELECT status,started_at,finished_at,output_sha256,result,error
                FROM action_executions WHERE request_id=r.id
                ORDER BY attempt_number DESC LIMIT 1
           ) x ON TRUE
           LEFT JOIN action_drafts d ON d.request_id=r.id
           LEFT JOIN automated_data_jobs j ON j.request_id=r.id
           WHERE r.project_id=%s AND (%s IS NULL OR r.status=%s)
           ORDER BY r.requested_at DESC,r.id LIMIT %s""",
        (project_id, status, status, limit),
    ).fetchall()
    return [dict(zip(ACTION_REQUEST_KEYS, row, strict=True)) for row in rows]
