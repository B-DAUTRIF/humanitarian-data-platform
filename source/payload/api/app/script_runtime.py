from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EXECUTABLE_LANGUAGES = {"python": "script.py", "r": "script.R"}
TERMINAL_STATUSES = {"completed", "failed", "timed_out"}
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 300
MIN_OUTPUT_BYTES = 1_024
MAX_OUTPUT_BYTES = 1_048_576


def script_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_execution_request(
    language: str,
    timeout_seconds: int,
    max_output_bytes: int,
    *,
    network_enabled: bool = False,
    allowed_hosts: list[str] | None = None,
) -> dict[str, Any]:
    """Validate the enforceable execution boundary.

    Iteration 2 deliberately implements only the strongest network policy:
    Docker starts the runners with ``network_mode: none``. An allowlist is not
    silently accepted because Docker cannot enforce a per-job egress allowlist
    without an additional proxy/firewall boundary.
    """

    if language not in EXECUTABLE_LANGUAGES:
        raise ValueError("Seuls les scripts Python et R peuvent être exécutés")
    if not MIN_TIMEOUT_SECONDS <= int(timeout_seconds) <= MAX_TIMEOUT_SECONDS:
        raise ValueError(
            f"Le délai doit être compris entre {MIN_TIMEOUT_SECONDS} et {MAX_TIMEOUT_SECONDS} secondes"
        )
    if not MIN_OUTPUT_BYTES <= int(max_output_bytes) <= MAX_OUTPUT_BYTES:
        raise ValueError(
            f"La sortie doit être comprise entre {MIN_OUTPUT_BYTES} et {MAX_OUTPUT_BYTES} octets"
        )
    normalized_hosts = sorted({str(host).strip().lower() for host in (allowed_hosts or []) if str(host).strip()})
    if network_enabled or normalized_hosts:
        raise ValueError(
            "Le réseau des exécutions est désactivé dans cette itération ; aucune allowlist n'est encore activable"
        )
    return {
        "language": language,
        "timeout_seconds": int(timeout_seconds),
        "max_output_bytes": int(max_output_bytes),
        "network_enabled": False,
        "allowed_hosts": [],
    }


def ensure_spool_layout(spool_root: Path) -> None:
    for relative in ("staging", "pending/python", "pending/r", "running/python", "running/r", "completed/python", "completed/r", "heartbeat"):
        directory = spool_root / relative
        directory.mkdir(parents=True, exist_ok=True)
        os.chmod(directory, 0o777)


def prepare_execution_job(
    spool_root: Path,
    execution_id: uuid.UUID,
    language: str,
    content: str,
    timeout_seconds: int,
    max_output_bytes: int,
) -> Path:
    settings = validate_execution_request(language, timeout_seconds, max_output_bytes)
    ensure_spool_layout(spool_root)
    staging_root = spool_root / "staging"
    temporary = Path(tempfile.mkdtemp(prefix=f"{execution_id}-", dir=staging_root))
    target = spool_root / "pending" / language / str(execution_id)
    try:
        script_name = EXECUTABLE_LANGUAGES[language]
        (temporary / script_name).write_text(content, encoding="utf-8", newline="\n")
        (temporary / "timeout_seconds").write_text(str(settings["timeout_seconds"]), encoding="ascii")
        (temporary / "max_output_bytes").write_text(str(settings["max_output_bytes"]), encoding="ascii")
        (temporary / "script.sha256").write_text(script_sha256(content), encoding="ascii")
        (temporary / "status.txt").write_text("queued", encoding="ascii")
        for path in temporary.iterdir():
            os.chmod(path, 0o644)
        os.chmod(temporary, 0o777)
        if target.exists():
            raise FileExistsError(f"Le travail {execution_id} existe déjà")
        os.replace(temporary, target)
        return target
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def locate_execution_job(spool_root: Path, execution_id: uuid.UUID, language: str) -> Path | None:
    for state in ("completed", "running", "pending"):
        candidate = spool_root / state / language / str(execution_id)
        if candidate.is_dir():
            return candidate
    return None


def _bounded_text(path: Path, maximum: int) -> str:
    if not path.exists():
        return ""
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        data = data[:maximum]
    return data.decode("utf-8", errors="replace")


def read_execution_result(
    spool_root: Path,
    execution_id: uuid.UUID,
    language: str,
    max_output_bytes: int,
) -> dict[str, Any] | None:
    job = locate_execution_job(spool_root, execution_id, language)
    if not job:
        return None
    status = _bounded_text(job / "status.txt", 32).strip() or "queued"
    result: dict[str, Any] = {"status": status, "job_path": str(job)}
    for key in ("started_at", "finished_at"):
        value = _bounded_text(job / f"{key}.txt", 64).strip()
        result[key] = value or None
    exit_code = _bounded_text(job / "exit_code.txt", 32).strip()
    result["exit_code"] = int(exit_code) if exit_code.lstrip("-").isdigit() else None
    if status in TERMINAL_STATUSES:
        result["stdout"] = _bounded_text(job / "stdout.txt", max_output_bytes)
        result["stderr"] = _bounded_text(job / "stderr.txt", max_output_bytes)
    return result


def heartbeat_status(spool_root: Path, language: str, *, stale_after_seconds: int = 30) -> dict[str, Any]:
    path = spool_root / "heartbeat" / f"{language}.txt"
    if not path.exists():
        return {"available": False, "last_seen_at": None}
    try:
        value = path.read_text(encoding="ascii").strip()
        seen = datetime.fromisoformat(value.replace("Z", "+00:00"))
        age = (datetime.now(UTC) - seen.astimezone(UTC)).total_seconds()
        return {"available": age <= stale_after_seconds, "last_seen_at": seen, "age_seconds": max(0, int(age))}
    except (OSError, ValueError):
        return {"available": False, "last_seen_at": None}


def write_execution_report(
    data_root: Path,
    project_id: uuid.UUID,
    execution_id: uuid.UUID,
    report: dict[str, Any],
) -> tuple[str, str]:
    relative = Path("projects") / str(project_id) / "executions" / str(execution_id) / "report.json"
    destination = data_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8")
    temporary = destination.with_suffix(".json.part")
    temporary.write_bytes(payload)
    os.replace(temporary, destination)
    return relative.as_posix(), hashlib.sha256(payload).hexdigest()
