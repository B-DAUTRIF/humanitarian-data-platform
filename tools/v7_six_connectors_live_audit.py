from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source" / "payload" / "api"))

from app.providers.dhs.service import DHSService
from app.providers.gdacs.service import GDACSService
from app.providers.un_sdg.service import UNSDGService
from app.providers.unhcr.service import UNHCRService
from app.providers.unicef_sdmx.service import UNICEFSDMXService
from app.providers.who_gho.service import WHOGHOService

SETTINGS = {"timeout_seconds":40, "connect_timeout_seconds":20, "retry_count":1, "backoff_seconds":1, "max_response_bytes":10_000_000, "user_agent":"HDP-V7-six-live-audit", "accept_language":"en"}


async def sentinel(provider: str):
    now = datetime.now(UTC)
    start = (now - timedelta(days=14)).date().isoformat()
    if provider == "dhs":
        return await DHSService(SETTINGS).execute("list_countries", {"f":"json", "page":1, "perpage":5})
    if provider == "gdacs":
        return await GDACSService(SETTINGS).execute("search_events", {"fromdate":start, "todate":now.date().isoformat(), "eventlist":[], "alertlevel":["green","orange","red"]})
    if provider == "un-sdg":
        return await UNSDGService(SETTINGS).execute("list_indicators", {})
    if provider == "unhcr":
        return await UNHCRService(SETTINGS).execute("countries", {"limit":5, "page":1})
    if provider == "unicef-sdmx":
        return await UNICEFSDMXService(SETTINGS).execute("list_dataflows", {"agency":"all", "dataflow":"all", "version":"latest", "format":"sdmx-json", "detail":"allstubs", "references":"none"})
    if provider == "who-gho":
        return await WHOGHOService(SETTINGS).execute("list_indicators", {"filter":"", "top":5, "skip":0, "format":"json"})
    raise ValueError(provider)


async def main_async() -> int:
    providers = ["dhs", "gdacs", "un-sdg", "unhcr", "unicef-sdmx", "who-gho"]
    rows = []
    for provider in providers:
        started = datetime.now(UTC)
        try:
            _payload, items, native = await sentinel(provider)
            rows.append({"provider":provider, "status":"PASS", "http_status":native.get("http_status"), "native_request":native, "item_count":len(items), "started_at":started.isoformat(), "finished_at":datetime.now(UTC).isoformat(), "error":None})
        except Exception as exc:
            rows.append({"provider":provider, "status":"BLOCKED", "http_status":getattr(getattr(exc, "response", None), "status_code", None), "native_request":None, "item_count":None, "started_at":started.isoformat(), "finished_at":datetime.now(UTC).isoformat(), "error":f"{type(exc).__name__}: {exc}"})
    report = {
        "protocol":"dev_connecteurs v1.0 / live non-destructive sentinels",
        "executed_at":datetime.now(UTC).isoformat(),
        "providers":rows,
        "pass_count":sum(row["status"] == "PASS" for row in rows),
        "blocked_count":sum(row["status"] == "BLOCKED" for row in rows),
        "false_zero_policy":"provider/network/auth/schema errors are BLOCKED and never empty_valid",
        "execution_status":"PASS" if len(rows) == len(providers) else "FAIL",
        "qualification_status":"PASS" if all(row["status"] == "PASS" for row in rows) else "BLOCKED_PARTIAL",
    }
    out = ROOT / "qualification-state"
    out.mkdir(exist_ok=True)
    (out / "V7_SIX_CONNECTORS_LIVE_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pass":report["pass_count"], "blocked":report["blocked_count"], "qualification_status":report["qualification_status"]}, ensure_ascii=False))
    return 0 if report["execution_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
