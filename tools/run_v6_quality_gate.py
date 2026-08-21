#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    blocking: bool = True

    @property
    def passed(self) -> bool:
        return self.status in {"passed", "not_applicable", "not_executed"}


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def summary(process: subprocess.CompletedProcess[str]) -> str:
    output = "\n".join(part.strip() for part in (process.stdout, process.stderr) if part.strip())
    lines = output.splitlines()
    return " | ".join(lines[-4:])[-2000:] or f"code de sortie {process.returncode}"


def check_python_tests() -> CheckResult:
    process = run(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "source/tests",
            "-p",
            "test_*.py",
        ]
    )
    return CheckResult(
        "python_tests",
        "passed" if process.returncode == 0 else "failed",
        summary(process),
    )


def check_python_ast() -> CheckResult:
    files = sorted((ROOT / "source").rglob("*.py")) + sorted((ROOT / "tools").rglob("*.py"))
    for path in files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path.relative_to(ROOT)))
    return CheckResult("python_ast", "passed", f"{len(files)} fichiers Python analysés")


def check_migrations() -> CheckResult:
    sys.path.insert(0, str(API_ROOT))
    from app.migrations import MIGRATIONS
    from pglast import parser

    statements = 0
    for migration in MIGRATIONS:
        for statement in migration.statements:
            parser.parse_sql(statement)
            statements += 1
    return CheckResult(
        "postgresql_migrations",
        "passed",
        f"{len(MIGRATIONS)} migrations et {statements} instructions analysées",
    )


def check_javascript() -> CheckResult:
    node = shutil.which("node")
    if not node:
        return CheckResult("javascript", "failed", "Node.js indisponible")
    process = run(
        [
            node,
            "tools/check_inline_javascript.mjs",
            "source/payload/api/static/index.html",
            "source/payload/api/static/login.html",
        ]
    )
    return CheckResult(
        "javascript",
        "passed" if process.returncode == 0 else "failed",
        summary(process),
    )


def check_openapi() -> CheckResult:
    os.environ.setdefault("DATABASE_URL", "postgresql://hdp:hdp@127.0.0.1:5432/hdp")
    os.environ.setdefault("DATA_DIR", str(Path(tempfile.gettempdir()) / "hdp-v6-quality-data"))
    os.environ.setdefault("EXECUTION_SPOOL_DIR", str(Path(tempfile.gettempdir()) / "hdp-v6-quality-spool"))
    sys.path.insert(0, str(API_ROOT))
    from app.main import APP_VERSION, app

    schema = app.openapi()
    paths = schema.get("paths", {})
    v6_paths = [path for path in paths if path.startswith("/api/v6")]
    if APP_VERSION != "6.0.0-dev" or not v6_paths:
        raise RuntimeError(f"contrat V6 incohérent: version={APP_VERSION}, chemins={len(v6_paths)}")
    operation_ids = [
        operation.get("operationId")
        for item in paths.values()
        for operation in item.values()
        if isinstance(operation, dict) and operation.get("operationId")
    ]
    duplicates = sorted({value for value in operation_ids if operation_ids.count(value) > 1})
    if duplicates:
        raise RuntimeError(f"operationId OpenAPI dupliqués: {duplicates}")
    return CheckResult(
        "fastapi_openapi",
        "passed",
        f"version={APP_VERSION}, routes={len(app.routes)}, chemins={len(paths)}, chemins_v6={len(v6_paths)}",
    )


def check_c_builds() -> CheckResult:
    compiler = shutil.which("gcc")
    if not compiler:
        return CheckResult("c_builds", "failed", "GCC indisponible")
    with tempfile.TemporaryDirectory(prefix="hdp-v6-c-") as temporary:
        source = "source/payload/runner/runner.c"
        target = str(Path(temporary) / "runner")
        process = run([compiler, "-std=c17", "-O2", "-Wall", "-Wextra", "-Werror", source, "-o", target])
        if process.returncode != 0:
            return CheckResult("c_builds", "failed", f"{source}: {summary(process)}")
    return CheckResult("c_builds", "passed", "runner compilé en C17 strict")


def check_spip_php() -> CheckResult:
    php = shutil.which("php")
    if not php:
        return CheckResult(
            "spip_php_syntax",
            "not_executed",
            "interpréteur PHP indisponible; validation SPIP native à exécuter séparément",
            blocking=False,
        )
    files = sorted((ROOT / "source" / "spip-plugin" / "hdp").rglob("*.php"))
    for path in files:
        process = run([php, "-l", str(path)])
        if process.returncode != 0:
            return CheckResult("spip_php_syntax", "failed", f"{path}: {summary(process)}")
    return CheckResult("spip_php_syntax", "passed", f"{len(files)} fichiers PHP analysés")


def environment_checks() -> list[CheckResult]:
    docker = shutil.which("docker")
    docker_detail = "Docker disponible, recette Compose distincte requise" if docker else "Docker indisponible"
    windows_status = "not_executed" if platform.system() == "Windows" else "not_applicable"
    windows_detail = (
        "recette Windows à exécuter séparément"
        if platform.system() == "Windows"
        else f"hôte {platform.system()}: recette Windows non applicable"
    )
    return [
        CheckResult("docker_compose", "not_executed", docker_detail, blocking=False),
        CheckResult("windows_installer", windows_status, windows_detail, blocking=False),
        CheckResult(
            "live_connector_calls",
            "not_executed",
            "appels réels à planifier pour les connecteurs modifiés",
            blocking=False,
        ),
    ]


def guarded(name: str, function: Callable[[], CheckResult]) -> CheckResult:
    try:
        return function()
    except Exception as exc:  # le rapport doit survivre à un contrôle défaillant
        return CheckResult(name, "failed", f"{type(exc).__name__}: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Jalon de qualité répétable pour chaque implémentation HDP V6")
    parser.add_argument("--compact", action="store_true", help="produire un JSON compact")
    arguments = parser.parse_args()
    checks = [
        guarded("python_tests", check_python_tests),
        guarded("python_ast", check_python_ast),
        guarded("postgresql_migrations", check_migrations),
        guarded("javascript", check_javascript),
        guarded("fastapi_openapi", check_openapi),
        guarded("c_builds", check_c_builds),
        guarded("spip_php_syntax", check_spip_php),
        *environment_checks(),
    ]
    blocking_failures = [item.name for item in checks if item.blocking and not item.passed]
    report = {
        "gate": "HDP_V6_IMPLEMENTATION_GATE",
        "application_version": "6.0.0-dev",
        "result": "passed" if not blocking_failures else "failed",
        "blocking_failures": blocking_failures,
        "qualification_complete": all(item.status == "passed" for item in checks),
        "checks": [{**asdict(item), "passed": item.passed} for item in checks],
        "rule": "tout échec bloquant impose correction ou arbitrage avant le lot suivant",
    }
    print(json.dumps(report, ensure_ascii=False, indent=None if arguments.compact else 2))
    return 0 if not blocking_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
