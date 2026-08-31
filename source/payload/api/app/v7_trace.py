from __future__ import annotations

import contextvars
import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

TRACE_ID = contextvars.ContextVar("hdp_trace_id", default="")
SENSITIVE_KEY_RE = re.compile(r"(token|secret|password|authorization|cookie|app_identifier|appname|api[_-]?key|csrf|credential)", re.I)
MAX_VALUE_CHARS = 4000
MAX_COLLECTION_ITEMS = 200
_LOCK = threading.Lock()


def _trace_dir() -> Path:
    root = Path(os.getenv("HDP_TRACE_DIR") or os.getenv("DATA_DIR") or "/app/data")
    path = root / "logs" / "trace"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _trace_path() -> Path:
    return _trace_dir() / f"HDP_TRACE_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _redact_url(value: str) -> str:
    try:
        parts = urlsplit(value)
        query = []
        for key, val in parse_qsl(parts.query, keep_blank_values=True):
            query.append((key, "***REDACTED***" if SENSITIVE_KEY_RE.search(key) else val))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), parts.fragment))
    except Exception:
        return value[:MAX_VALUE_CHARS]


def redact(value: Any, *, key: str = "") -> Any:
    if key and SENSITIVE_KEY_RE.search(key):
        return "***REDACTED***"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        text = _redact_url(value) if value.startswith(("http://", "https://")) else value
        return text if len(text) <= MAX_VALUE_CHARS else text[:MAX_VALUE_CHARS] + "…<truncated>"
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for index, (item_key, item_value) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                out["__truncated__"] = len(value) - MAX_COLLECTION_ITEMS
                break
            out[str(item_key)] = redact(item_value, key=str(item_key))
        return out
    if isinstance(value, (list, tuple, set)):
        seq = list(value)
        out = [redact(item) for item in seq[:MAX_COLLECTION_ITEMS]]
        if len(seq) > MAX_COLLECTION_ITEMS:
            out.append({"__truncated__": len(seq) - MAX_COLLECTION_ITEMS})
        return out
    return redact(str(value), key=key)


def trace_id() -> str:
    current = TRACE_ID.get()
    if current:
        return current
    current = uuid.uuid4().hex
    TRACE_ID.set(current)
    return current


def trace_event(event: str, **fields: Any) -> dict[str, Any]:
    record = {
        "timestamp_utc": _iso_now(),
        "event": event,
        "trace_id": trace_id(),
        "pid": os.getpid(),
        **redact(fields),
    }
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    with _LOCK:
        with _trace_path().open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
    return record


async def trace_http_middleware(request: Request, call_next):
    incoming = request.headers.get("X-HDP-Trace-ID", "").strip()
    token = TRACE_ID.set(incoming if re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", incoming) else uuid.uuid4().hex)
    started = time.perf_counter()
    query = {key: value for key, value in request.query_params.multi_items()}
    trace_event(
        "http.request.start",
        method=request.method,
        path=request.url.path,
        query=query,
        client_host=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        content_type=request.headers.get("content-type"),
        content_length=request.headers.get("content-length"),
    )
    try:
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        response.headers["X-HDP-Trace-ID"] = trace_id()
        trace_event(
            "http.request.finish",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            response_content_type=response.headers.get("content-type"),
            response_content_length=response.headers.get("content-length"),
        )
        return response
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        trace_event(
            "http.request.exception",
            method=request.method,
            path=request.url.path,
            elapsed_ms=elapsed_ms,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
        )
        raise
    finally:
        TRACE_ID.reset(token)


router = APIRouter(prefix="/api/trace", tags=["Trace"])


@router.get("/status")
def trace_status() -> dict[str, Any]:
    path = _trace_path()
    return {
        "enabled": True,
        "format": "jsonl",
        "directory": str(_trace_dir()),
        "current_file": path.name,
        "current_size_bytes": path.stat().st_size if path.exists() else 0,
        "redaction": "secrets/tokens/passwords/cookies/app identifiers are redacted",
    }


@router.get("/export")
def trace_export() -> FileResponse:
    path = _trace_path()
    if not path.exists():
        trace_event("trace.export.requested", note="created empty trace before export")
    return FileResponse(path, media_type="application/x-ndjson", filename=path.name)
