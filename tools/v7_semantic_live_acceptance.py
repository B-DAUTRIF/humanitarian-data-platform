from __future__ import annotations

"""Non-destructive live sentinels for the HDP V7 semantic router."""

import asyncio
import json
import os
import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1] / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.semantic_provider_execution import execute_native_route  # noqa: E402
from app.semantic_router import build_execution_plan  # noqa: E402

SETTINGS = {"timeout_seconds": 40, "connect_timeout_seconds": 15, "retry_count": 1, "backoff_seconds": 1, "user_agent": "HDP/7.0.0-live-qualification", "accept_language": "en"}


async def run() -> int:
    request = {"query": "malaria", "location": "Rwanda", "date_from": "2020-01-01", "date_to": "2025-12-31", "result_limit": 25}
    sources = ["hdx", "reliefweb", "who-gho", "world-bank-health", "unicef-sdmx", "un-sdg", "dhs", "hdx-hapi", "unhcr", "gdacs"]
    plan = build_execution_plan(sources, **request)
    report = {"query_fingerprint": plan["query_fingerprint"], "sources": []}
    failures: list[str] = []
    for route in plan["routes"]:
        source = route["source"]
        if not route["executable"]:
            report["sources"].append({"source": source, "status": "blocked_as_planned", "criteria": route["criteria"], "warnings": route["warnings"]})
            continue
        if source == "reliefweb" and not os.getenv("RELIEFWEB_APPNAME", "").strip():
            report["sources"].append({"source": source, "status": "configuration_error", "reason": "RELIEFWEB_APPNAME missing"})
            continue
        if source == "hdx-hapi" and not os.getenv("HDX_HAPI_APP_IDENTIFIER", "").strip():
            report["sources"].append({"source": source, "status": "configuration_error", "reason": "HDX_HAPI_APP_IDENTIFIER missing"})
            continue
        try:
            native = await execute_native_route(route, SETTINGS)
            if native is None:
                report["sources"].append({"source": source, "status": "legacy_executor_required"})
                continue
            _, items, native_request = native
            report["sources"].append({"source": source, "status": "success", "item_count": len(items), "native_request": native_request})
            if source == "world-bank-health" and not items:
                failures.append("world-bank-health: expected a non-empty Rwanda malaria sentinel")
        except Exception as exc:
            report["sources"].append({"source": source, "status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
            if source == "world-bank-health":
                failures.append(f"world-bank-health provider error: {exc}")
    hdx_geo = build_execution_plan(["hdx"], query="RWANDA")["routes"][0]
    if hdx_geo["executable"] or hdx_geo["criteria"].get("geography") != "blocked_missing_mapping":
        failures.append("HDX RWANDA geography-only regression: route is not safely blocked")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
