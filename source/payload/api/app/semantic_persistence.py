from __future__ import annotations

"""Persistence boundary for semantic plans and source executions."""

import uuid
from datetime import UTC, datetime
from typing import Any

from psycopg.types.json import Jsonb


def start_semantic_search(
    request: dict[str, Any],
    plan: dict[str, Any],
    *,
    project_id: uuid.UUID | str | None = None,
) -> str | None:
    """Persist the immutable semantic request/plan envelope when DB is available."""
    try:
        from .main import database_connection

        search_id = uuid.uuid4()
        normalized_project_id = uuid.UUID(str(project_id)) if project_id else None
        with database_connection() as connection:
            connection.execute(
                """INSERT INTO semantic_searches
                (id, project_id, query_fingerprint, contract_version, request_json,
                 intent_json, plan_json, status, source_count, started_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,'running',%s,%s)""",
                (
                    search_id,
                    normalized_project_id,
                    plan["query_fingerprint"],
                    plan["contract_version"],
                    Jsonb(request),
                    Jsonb(plan["intent"]),
                    Jsonb(plan),
                    len(plan["routes"]),
                    datetime.now(UTC),
                ),
            )
        return str(search_id)
    except Exception:
        # Semantic execution remains available if provenance persistence is temporarily
        # unavailable; the API reports persistence_recorded=False instead of faking it.
        return None


def finish_semantic_search(
    search_id: str | None,
    status: str,
    result_snapshot_hash: str,
    item_count: int,
    executions: list[dict[str, Any]],
) -> bool:
    if not search_id:
        return False
    try:
        from .main import database_connection

        now = datetime.now(UTC)
        with database_connection() as connection:
            connection.execute(
                "UPDATE semantic_searches SET status=%s,result_snapshot_hash=%s,item_count=%s,finished_at=%s WHERE id=%s",
                (status, result_snapshot_hash, item_count, now, uuid.UUID(search_id)),
            )
            for execution in executions:
                connection.execute(
                    """INSERT INTO semantic_source_executions
                    (id,semantic_search_id,source_id,operation,status,completeness,
                     native_request,criteria,item_count,response_hash,error,started_at,finished_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (semantic_search_id,source_id) DO UPDATE SET
                    status=EXCLUDED.status, completeness=EXCLUDED.completeness,
                    native_request=EXCLUDED.native_request, criteria=EXCLUDED.criteria,
                    item_count=EXCLUDED.item_count, response_hash=EXCLUDED.response_hash,
                    error=EXCLUDED.error, finished_at=EXCLUDED.finished_at""",
                    (
                        uuid.uuid4(),
                        uuid.UUID(search_id),
                        execution["source"],
                        execution["route"].get("operation", "unknown"),
                        execution["status"],
                        execution.get("completeness", "unknown"),
                        Jsonb(execution.get("native_request") or {}),
                        Jsonb(execution["route"].get("criteria") or {}),
                        execution.get("item_count", 0),
                        execution.get("response_hash"),
                        execution.get("error"),
                        now,
                        now,
                    ),
                )
        return True
    except Exception:
        return False
