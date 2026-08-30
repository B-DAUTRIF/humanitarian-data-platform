#!/usr/bin/env python3
"""HDP V6 exhaustive functional coverage gate.

This gate does not replace the executable test suites.  It guarantees that every
frozen V6 feature is attached to an executable acceptance path.  CI executes the
referenced suites separately; this script prevents a feature from disappearing
from the qualification matrix unnoticed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CASES = {
    "UC01_sources_search": {
        "features": range(1, 7),
        "evidence": [
            "source/tests/test_source_registry.py",
            "source/tests/test_federated_search.py",
            "source/tests/test_epidemiologist_use_case.py",
            "tools/browser_ui_e2e.py",
            "tools/epidemiology_acceptance.py",
        ],
    },
    "UC02_geodata_data": {
        "features": range(7, 12),
        "evidence": [
            "tools/browser_ui_e2e.py",
            "source/tests/test_v23_helpers.py",
            "source/tests/test_epidemiology_reference_e2e.py",
        ],
    },
    "UC03_projects_github": {
        "features": range(12, 15),
        "evidence": ["tools/browser_ui_e2e.py", "source/tests/test_github_api_contracts.py"],
    },
    "UC04_scientific_clients": {
        "features": range(15, 20),
        "evidence": [
            "clients-v6/python/tests",
            "clients-v6/R/tests/testthat",
            "source/tests/test_processing_recipes.py",
            "tools/browser_ui_e2e.py",
        ],
    },
    "UC05_epidemiology_surveillance": {
        "features": range(20, 25),
        "evidence": [
            "source/tests/test_epidemiology_reference_e2e.py",
            "tools/epidemiology_reference_acceptance.py",
        ],
    },
    "UC06_security_persistence": {
        "features": range(25, 28),
        "evidence": [
            "source/tests/test_request_security.py",
            "source/tests/test_migrations.py",
            "tools/browser_ui_e2e.py",
            "tools/security_static_checks.py",
        ],
    },
    "UC07_ingestion_publication_logs": {
        "features": range(28, 31),
        "evidence": ["source/tests", "tools/browser_ui_e2e.py", "source/src/installer.c"],
    },
    "UC08_windows_architecture_ui": {
        "features": range(31, 36),
        "evidence": [
            "source/build-windows.ps1",
            "tools/windows/windows_installer_e2e.ps1",
            "source/payload/compose.yaml",
            "tools/audit_v6_complete.py",
            "tools/browser_ui_e2e.py",
        ],
    },
    "UC09_docs_upgrade_release": {
        "features": range(36, 41),
        "evidence": [
            "docs",
            "tools/finalize_v6.py",
            "tools/windows/windows_installer_e2e.ps1",
            "tools/epidemiology_reference_acceptance.py",
        ],
    },
    "UC10_windows10": {
        "features": [41],
        "evidence": [
            "source/build-windows.ps1",
            "tools/windows/windows10_compatibility_gate.ps1",
            "tools/windows/windows10_full_e2e.ps1",
        ],
    },
}

covered: set[int] = set()
missing_paths: list[str] = []
for case in CASES.values():
    covered.update(int(x) for x in case["features"])
    for relative in case["evidence"]:
        if not (ROOT / relative).exists():
            missing_paths.append(relative)

expected = set(range(1, 42))
missing_features = sorted(expected - covered)
extra_features = sorted(covered - expected)
result = {
    "version": "6.0.0",
    "use_cases": len(CASES),
    "features_expected": len(expected),
    "features_covered": len(covered & expected),
    "missing_features": missing_features,
    "extra_features": extra_features,
    "missing_evidence_paths": sorted(set(missing_paths)),
    "windows10_policy": "blocking_real_windows10_x64_e2e",
}
print(json.dumps(result, ensure_ascii=False, sort_keys=True))
if missing_features or extra_features or missing_paths:
    raise SystemExit(1)
