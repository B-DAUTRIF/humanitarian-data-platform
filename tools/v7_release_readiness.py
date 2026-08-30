from __future__ import annotations

"""Offline V7 release-readiness audit used by CI before building deliverables."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "source/payload/api/app/semantic_router.py",
    "source/payload/api/app/provider_semantic_adapters.py",
    "source/payload/api/app/semantic_provider_execution.py",
    "source/payload/api/app/semantic_provenance.py",
    "source/payload/api/app/semantic_persistence.py",
    "source/payload/api/app/v7_migrations.py",
    "source/payload/api/app/v7_semantic_jobs.py",
    "source/payload/api/app/v6_semantic_api.py",
    "source/payload/api/app/main_v6.py",
    "source/build-windows-v7.ps1",
    "source/tests/test_semantic_router.py",
    "source/tests/test_semantic_provider_execution.py",
    "source/tests/test_semantic_project_context.py",
    "source/tests/test_v7_semantic_jobs.py",
    "source/tests/test_v7_semantic_input_contract.py",
    "source/tests/test_v7_semantic_provenance_security.py",
    "source/tests/test_v7_use_case_matrix.py",
    "clients-v6/python/src/hdp_clients/client.py",
    "clients-v6/R/DESCRIPTION",
    "clients-v6/R/NAMESPACE",
    ".github/workflows/windows-v7-full.yml",
)

REQUIRED_DIRS = ("docs", "tools", "clients-v6/python", "clients-v6/R")
EXE = "HumanitarianDataPlatform_Setup_Native_GUI_v7.0.0.exe"
ARCHIVE = "HumanitarianDataPlatform_Archive_complete_v7.0.0.zip"


def audit() -> dict[str, object]:
    issues: list[str] = []
    for relative in REQUIRED_FILES:
        if not ROOT.joinpath(relative).is_file():
            issues.append(f"missing_file:{relative}")
    for relative in REQUIRED_DIRS:
        if not ROOT.joinpath(relative).is_dir():
            issues.append(f"missing_directory:{relative}")

    main_v6 = ROOT.joinpath("source/payload/api/app/main_v6.py").read_text(encoding="utf-8")
    if 'ACTIVE_APPLICATION_VERSION = "7.0.0"' not in main_v6:
        issues.append("active_application_version_not_7.0.0")
    if "apply_v7_migrations" not in main_v6 or "semantic_jobs_router" not in main_v6:
        issues.append("v7_runtime_not_fully_wired")

    workflow = ROOT.joinpath(".github/workflows/windows-v7-full.yml").read_text(encoding="utf-8")
    required_workflow_markers = (
        EXE,
        ARCHIVE,
        "HDP-V7-qualified-candidate",
        "Get-FileHash",
        "source/tests/test_v7_use_case_matrix.py",
        "tools/v7_release_readiness.py",
        "Copy-Item -Recurse source",
        "Copy-Item -Recurse clients-v6",
        "Copy-Item -Recurse docs",
        "Copy-Item -Recurse tools",
    )
    for marker in required_workflow_markers:
        if marker not in workflow:
            issues.append(f"workflow_missing:{marker}")

    report = {
        "schema_version": 1,
        "release": "7.0.0",
        "status": "ready" if not issues else "blocked",
        "issues": issues,
        "required_file_count": len(REQUIRED_FILES),
        "required_directory_count": len(REQUIRED_DIRS),
        "expected_exe": EXE,
        "expected_archive": ARCHIVE,
    }
    return report


def main() -> int:
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
