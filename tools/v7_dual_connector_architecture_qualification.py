from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CYCLES = 10
COMMANDS = [
    [sys.executable, "-m", "unittest",
     "source/tests/test_semantic_router.py",
     "source/tests/test_semantic_provider_execution.py",
     "source/tests/test_semantic_project_context.py",
     "source/tests/test_v7_semantic_jobs.py",
     "source/tests/test_v7_semantic_input_contract.py",
     "source/tests/test_v7_semantic_provenance_security.py",
     "source/tests/test_v7_use_case_matrix.py",
     "source/tests/test_reliefweb_v2.py",
     "source/tests/test_provider_reliefweb_architecture.py",
     "source/tests/test_reliefweb_use_case_qualification.py",
     "source/tests/test_provider_world_bank_health_architecture.py"],
    [sys.executable, "-m", "pytest", "-q", "clients-v6/python/tests"],
]


def run() -> int:
    report = {"schema_version": 1, "purpose": "HDP V7 complete architecture with ReliefWeb and World Bank Health", "cycles_required": CYCLES, "cycles": [], "started_at_utc": datetime.now(timezone.utc).isoformat()}
    out = Path("qualification-state"); out.mkdir(exist_ok=True)
    failed = False
    for cycle in range(1, CYCLES + 1):
        cycle_result = {"cycle": cycle, "commands": [], "status": "PASS"}
        for command in COMMANDS:
            started = time.monotonic()
            proc = subprocess.run(command, text=True, capture_output=True)
            item = {"command": command, "returncode": proc.returncode, "elapsed_seconds": round(time.monotonic()-started, 3), "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:]}
            cycle_result["commands"].append(item)
            if proc.returncode != 0:
                cycle_result["status"] = "FAIL"; failed = True; break
        report["cycles"].append(cycle_result)
        print(f"cycle {cycle}/{CYCLES}: {cycle_result['status']}", flush=True)
        if failed: break
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "FAIL" if failed or len(report["cycles"]) != CYCLES else "PASS"
    path = out / "HDP_V7_DUAL_CONNECTOR_ARCHITECTURE_10_CYCLES.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(run())
