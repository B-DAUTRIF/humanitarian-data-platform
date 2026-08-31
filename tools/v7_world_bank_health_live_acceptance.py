from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source" / "payload" / "api"))

from app.providers.world_bank_health.service import WorldBankHealthService

SETTINGS = {"timeout_seconds": 30, "connect_timeout_seconds": 10, "user_agent": "HDP/7 WorldBankHealthQualification", "accept_language": "en"}


async def _record(name: str, call, checks: list[dict]) -> None:
    payload, rows, native = await call
    checks.append({"name": name, "status": "PASS", "http_status": native.get("http_status"), "url": native.get("url"), "row_count": len(rows), "has_payload": bool(payload)})


async def main_async() -> int:
    service = WorldBankHealthService(SETTINGS)
    checks: list[dict] = []
    try:
        await _record("country_RWA", service.list_countries(identifier="RWA", per_page=10), checks)
        await _record("indicator_metadata", service.indicator_metadata("SH.MLR.INCD.P3", source=2), checks)
        await _record("topic_catalogue", service.list_topics(per_page=20), checks)
        await _record("source_catalogue", service.list_sources(per_page=20), checks)
        await _record("source_2_metadata_search_health", service.get_metadata(source=2, query="health", per_page=50), checks)
        payload, items, native = await service.observations(country="RWA", indicator="SH.MLR.INCD.P3", source=2, date="2020:2025", page=1, per_page=20)
        checks.append({"name": "health_observations_RWA_2020_2025", "status": "PASS", "http_status": native.get("http_status"), "url": native.get("url"), "item_count": len(items), "has_payload": bool(payload)})
        status = "PASS"
    except Exception as exc:
        checks.append({"name": "provider_live", "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
        status = "FAIL"
    report = {"schema_version": 1, "provider": "world-bank-health", "status": status, "checks": checks, "rule": "Provider/network failures remain errors and are never empty_valid."}
    out_dir = ROOT / "qualification-state"; out_dir.mkdir(exist_ok=True)
    (out_dir / "WORLD_BANK_HEALTH_LIVE_STATUS.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main_async()))
