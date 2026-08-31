from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source" / "payload" / "api"))

from app.providers.world_bank_health.service import WorldBankHealthService

SETTINGS = {"timeout_seconds": 30, "connect_timeout_seconds": 10, "user_agent": "HDP/7 WorldBankHealthQualification", "accept_language": "en"}


async def main_async() -> int:
    service = WorldBankHealthService(SETTINGS)
    checks = []
    try:
        country_payload, country_url, country_status = await service.get_json("https://api.worldbank.org/v2/country/RWA", {"format": "json"})
        checks.append({"name": "country_RWA", "status": "PASS", "http_status": country_status, "url": country_url, "has_payload": bool(country_payload)})
        indicator_payload, indicator_url, indicator_status = await service.get_json("https://api.worldbank.org/v2/indicator/SH.MLR.INCD.P3", {"format": "json", "source": 2})
        checks.append({"name": "indicator_metadata", "status": "PASS", "http_status": indicator_status, "url": indicator_url, "has_payload": bool(indicator_payload)})
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
