from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .main import EXECUTION_SPOOL_DIR, _execution_row, database_connection, get_execution_settings
from .script_runtime import prepare_execution_job, script_sha256, validate_execution_request
from .v5_features import get_notebook

router = APIRouter(tags=["HDP V6 notebooks"])


class NotebookCellExecution(BaseModel):
    confirmed_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    max_output_bytes: int | None = Field(default=None, ge=1024, le=1_048_576)


@router.post("/api/notebooks/{notebook_id}/cells/{cell_index}/executions", status_code=202)
def execute_notebook_cell_v6(
    notebook_id: uuid.UUID,
    cell_index: int,
    payload: NotebookCellExecution,
) -> dict[str, Any]:
    """Execute one immutable notebook cell through the same isolated runner as Scripts.

    The historical V5 route unpacked ``validate_execution_request`` as a tuple even
    though it returns a dictionary. V6 also enforces the project's Python/R enable
    flags and runner heartbeat before creating a persistent execution record.
    """
    notebook = get_notebook(notebook_id)
    cells = notebook["document"].get("cells", [])
    if cell_index < 0 or cell_index >= len(cells):
        raise HTTPException(status_code=422, detail="Cellule de code introuvable")
    cell = cells[cell_index]
    if not isinstance(cell, dict) or cell.get("cell_type") != "code":
        raise HTTPException(status_code=422, detail="Cellule de code introuvable")

    code = cell.get("source", "")
    if isinstance(code, list):
        code = "".join(str(item) for item in code)
    if not isinstance(code, str):
        raise HTTPException(status_code=422, detail="Contenu de cellule invalide")
    digest = script_sha256(code)
    if digest != payload.confirmed_sha256:
        raise HTTPException(
            status_code=409,
            detail="Le code a changé : confirmer son nouveau SHA-256",
        )

    language = "python" if notebook["kernel"] == "python3" else "r"
    project_id = uuid.UUID(notebook["project_id"])
    settings = get_execution_settings(project_id)
    if language == "python" and not settings["python_enabled"]:
        raise HTTPException(
            status_code=409,
            detail="Les exécutions Python sont désactivées pour ce projet",
        )
    if language == "r" and not settings["r_enabled"]:
        raise HTTPException(
            status_code=409,
            detail="Les exécutions R sont désactivées pour ce projet",
        )
    runner = settings["runners"][language]
    if not runner["available"]:
        detail = (
            "Le runner R optionnel n'est pas démarré avec le profil analytics"
            if language == "r"
            else "Le runner Python isolé n'est pas encore disponible"
        )
        raise HTTPException(status_code=503, detail=detail)

    timeout_seconds = payload.timeout_seconds or int(settings["timeout_seconds"])
    max_output_bytes = payload.max_output_bytes or int(settings["max_output_bytes"])
    try:
        validated = validate_execution_request(
            language,
            timeout_seconds,
            max_output_bytes,
            network_enabled=False,
            allowed_hosts=[],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    execution_id = uuid.uuid4()
    script_id = uuid.uuid4()
    version_id = uuid.uuid4()
    now = datetime.now(UTC)
    script_name = f"{notebook['name']} · cellule {cell_index}"

    try:
        with database_connection(autocommit=False) as connection:
            connection.execute(
                """
                INSERT INTO project_scripts
                    (id,project_id,name,language,content,description,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    script_id,
                    project_id,
                    script_name,
                    language,
                    code,
                    "Cellule Jupyter immuable exécutée par HDP V6",
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO script_versions
                    (id,script_id,project_id,version_number,name,language,description,
                     content,content_sha256,created_at)
                VALUES (%s,%s,%s,1,%s,%s,%s,%s,%s,%s)
                """,
                (
                    version_id,
                    script_id,
                    project_id,
                    script_name,
                    language,
                    "Cellule Jupyter immuable exécutée par HDP V6",
                    code,
                    digest,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO script_executions
                    (id,project_id,script_id,script_version_id,language,status,requested_at,
                     timeout_seconds,max_output_bytes,network_enabled)
                VALUES (%s,%s,%s,%s,%s,'queued',%s,%s,%s,FALSE)
                """,
                (
                    execution_id,
                    project_id,
                    script_id,
                    version_id,
                    language,
                    now,
                    validated["timeout_seconds"],
                    validated["max_output_bytes"],
                ),
            )
            connection.execute(
                """
                INSERT INTO notebook_cell_executions
                    (id,notebook_id,revision_id,cell_index,script_execution_id,
                     code_sha256,requested_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uuid.uuid4(),
                    notebook_id,
                    uuid.UUID(notebook["revision_id"]),
                    cell_index,
                    execution_id,
                    digest,
                    now,
                ),
            )
            connection.commit()
    except Exception:
        raise

    try:
        prepare_execution_job(
            EXECUTION_SPOOL_DIR,
            execution_id,
            language,
            code,
            validated["timeout_seconds"],
            validated["max_output_bytes"],
        )
    except Exception as exc:
        with database_connection() as connection:
            connection.execute(
                """
                UPDATE script_executions
                SET status='failed',finished_at=%s,error=%s
                WHERE id=%s
                """,
                (datetime.now(UTC), str(exc)[:2000], execution_id),
            )
        raise HTTPException(
            status_code=500,
            detail="Impossible de préparer l'exécution isolée du notebook",
        ) from exc

    result = _execution_row(execution_id)
    result.update(
        {
            "notebook_id": str(notebook_id),
            "notebook_revision": notebook["revision"],
            "cell_index": cell_index,
            "code_sha256": digest,
            "network": "disabled",
            "result_url": f"/api/executions/{execution_id}",
        }
    )
    return result
