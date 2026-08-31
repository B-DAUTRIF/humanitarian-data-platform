from __future__ import annotations

import ast
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from fastapi.routing import APIRoute  # noqa: E402
from app.main_v6 import app  # noqa: E402
from app.source_registry import CONNECTORS, connector_definition, request_preview  # noqa: E402

OUT = ROOT / "qualification-state"
ACTIVE_ROOTS = [ROOT / "source", ROOT / "clients-v6", ROOT / "tools", ROOT / ".github"]
TEXT_EXTENSIONS = {".py", ".r", ".R", ".js", ".mjs", ".ts", ".html", ".css", ".yml", ".yaml", ".md", ".json", ".toml", ".c", ".h", ".ps1", ".cmd", ".iss"}
CODE_EXTENSIONS = {".py", ".r", ".R", ".js", ".mjs", ".ts", ".html", ".css", ".c", ".h", ".ps1", ".cmd", ".iss"}


def _active_files() -> list[Path]:
    files: list[Path] = []
    for root in ACTIVE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                files.append(path)
    return sorted(set(files))


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def _code_metrics(files: list[Path]) -> dict[str, Any]:
    extension_files = Counter()
    extension_lines = Counter()
    python_functions = 0
    python_async_functions = 0
    python_classes = 0
    python_parse_errors: list[str] = []
    todo_markers: list[dict[str, Any]] = []
    suspicious_markers: dict[str, list[str]] = defaultdict(list)
    patterns = {
        "eval_call": "eval(",
        "exec_call": "exec(",
        "shell_true": "shell=True",
        "pickle_loads": "pickle.loads(",
        "yaml_unsafe_load": "yaml.load(",
    }
    for path in files:
        suffix = path.suffix
        extension_files[suffix or "<none>"] += 1
        text = _read(path)
        if text and suffix in TEXT_EXTENSIONS:
            extension_lines[suffix or "<none>"] += text.count("\n") + 1
            rel = str(path.relative_to(ROOT))
            for line_no, line in enumerate(text.splitlines(), start=1):
                upper = line.upper()
                if "TODO" in upper or "FIXME" in upper:
                    todo_markers.append({"file": rel, "line": line_no, "text": line.strip()[:240]})
            for name, token in patterns.items():
                if token in text:
                    suspicious_markers[name].append(rel)
        if suffix == ".py" and text:
            try:
                tree = ast.parse(text, filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        python_functions += 1
                    elif isinstance(node, ast.AsyncFunctionDef):
                        python_async_functions += 1
                    elif isinstance(node, ast.ClassDef):
                        python_classes += 1
            except SyntaxError as exc:
                python_parse_errors.append(f"{path.relative_to(ROOT)}:{exc.lineno}:{exc.msg}")
    return {
        "active_file_count": len(files),
        "code_file_count": sum(1 for p in files if p.suffix in CODE_EXTENSIONS),
        "files_by_extension": dict(sorted(extension_files.items())),
        "lines_by_extension": dict(sorted(extension_lines.items())),
        "python_functions": python_functions,
        "python_async_functions": python_async_functions,
        "python_classes": python_classes,
        "python_parse_errors": python_parse_errors,
        "todo_fixme_count": len(todo_markers),
        "todo_fixme_examples": todo_markers[:50],
        "static_review_markers": {k: sorted(set(v)) for k, v in suspicious_markers.items()},
    }


def _api_inventory() -> dict[str, Any]:
    routes = []
    prefix_counts = Counter()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        methods = sorted(route.methods or [])
        path = route.path
        first = "/" + path.strip("/").split("/")[0] if path.strip("/") else "/"
        prefix_counts[first] += 1
        routes.append({
            "path": path,
            "methods": methods,
            "name": route.name,
            "include_in_schema": route.include_in_schema,
        })
    duplicate_keys = Counter((r["path"], tuple(r["methods"])) for r in routes)
    duplicates = [
        {"path": path, "methods": list(methods), "count": count}
        for (path, methods), count in duplicate_keys.items()
        if count > 1
    ]
    required_paths = {
        "/api/health",
        "/api/semantic/ui",
        "/api/providers/reliefweb/ui",
        "/api/providers/world-bank-health/ui",
    }
    present = {r["path"] for r in routes}
    return {
        "application_version": app.version,
        "route_count": len(routes),
        "schema_route_count": sum(bool(r["include_in_schema"]) for r in routes),
        "routes_by_first_prefix": dict(sorted(prefix_counts.items())),
        "required_route_checks": {path: path in present for path in sorted(required_paths)},
        "duplicate_method_path_routes": duplicates,
        "routes": sorted(routes, key=lambda x: (x["path"], x["methods"])),
    }


def _connector_inventory() -> dict[str, Any]:
    rows = []
    failed = []
    for source_id in sorted(CONNECTORS):
        definition = connector_definition(source_id)
        schema = definition["project_schema"]
        defaults = definition["project_defaults"]
        preview_status = "PASS"
        preview_error = ""
        preview: dict[str, Any] = {}
        try:
            preview = request_preview(source_id, defaults)
        except Exception as exc:  # audit must record rather than hide a connector failure
            preview_status = "FAIL"
            preview_error = f"{type(exc).__name__}: {exc}"
            failed.append(source_id)
        rows.append({
            "source_id": source_id,
            "version": definition.get("version"),
            "base_url": definition.get("base_url"),
            "allowed_hosts": definition.get("allowed_hosts", []),
            "documentation_evidence": definition.get("documentation_evidence", []),
            "project_parameter_count": len(schema.get("properties", {})),
            "required_project_parameters": schema.get("required", []),
            "additional_properties": schema.get("additionalProperties"),
            "global_parameter_count": len(definition["global_settings_schema"].get("properties", {})),
            "secret_environment_variable": definition.get("secret_environment_variable"),
            "request_preview_status": preview_status,
            "request_preview_error": preview_error,
            "request_method": preview.get("method"),
            "request_url": preview.get("url"),
            "native_query_parameters": sorted((preview.get("query_parameters") or {}).keys()),
            "has_python_example": bool((preview.get("code_examples") or {}).get("python")),
            "has_r_example": bool((preview.get("code_examples") or {}).get("r")),
        })
    return {
        "connector_count": len(rows),
        "preview_failures": failed,
        "connectors": rows,
    }


def _repository_contracts(files: list[Path]) -> dict[str, Any]:
    rels = {str(p.relative_to(ROOT)) for p in files}
    test_files = sorted(p for p in rels if p.startswith("source/tests/") and p.endswith(".py"))
    python_client_tests = sorted(p for p in rels if p.startswith("clients-v6/python/tests/") and p.endswith(".py"))
    r_client_tests = sorted(p for p in rels if p.startswith("clients-v6/R/tests/") and p.endswith(".R"))
    workflows = sorted(p for p in rels if p.startswith(".github/workflows/") and (p.endswith(".yml") or p.endswith(".yaml")))
    migrations = sorted(p for p in rels if "migration" in p.lower() and p.endswith(".py"))
    installer_sources = sorted(p for p in rels if "installer" in p.lower() or p.endswith(".iss"))
    provider_files = sorted(p for p in rels if "/providers/" in p)
    required = {
        "compose": "source/payload/compose.yaml",
        "main_v7_compat_entrypoint": "source/payload/api/app/main_v6.py",
        "source_registry": "source/payload/api/app/source_registry.py",
        "semantic_api": "source/payload/api/app/v6_semantic_api.py",
        "semantic_ui": "source/payload/api/app/v7_semantic_ui.py",
        "github_sync": "source/payload/api/app/github_sync.py",
        "api_inventory": "source/payload/api/app/api_inventory.py",
        "python_client": "clients-v6/python/pyproject.toml",
        "r_client": "clients-v6/R/DESCRIPTION",
        "windows_installer_workflow": ".github/workflows/windows-installer.yml",
    }
    return {
        "required_files": {name: path in rels for name, path in required.items()},
        "source_test_file_count": len(test_files),
        "python_client_test_file_count": len(python_client_tests),
        "r_client_test_file_count": len(r_client_tests),
        "workflow_count": len(workflows),
        "migration_like_file_count": len(migrations),
        "installer_related_file_count": len(installer_sources),
        "provider_file_count": len(provider_files),
        "workflows": workflows,
        "installer_related_files": installer_sources[:100],
    }


def _status(report: dict[str, Any]) -> tuple[str, list[str]]:
    failures: list[str] = []
    metrics = report["code"]
    if metrics["python_parse_errors"]:
        failures.append("Python syntax/AST parse errors")
    api = report["api"]
    missing_routes = [k for k, ok in api["required_route_checks"].items() if not ok]
    if missing_routes:
        failures.append("Missing required API routes: " + ", ".join(missing_routes))
    if api["duplicate_method_path_routes"]:
        failures.append("Duplicate FastAPI method/path registrations")
    connectors = report["connectors"]
    if connectors["preview_failures"]:
        failures.append("Connector request preview failures: " + ", ".join(connectors["preview_failures"]))
    missing_files = [k for k, ok in report["repository"]["required_files"].items() if not ok]
    if missing_files:
        failures.append("Missing required files: " + ", ".join(missing_files))
    return ("PASS" if not failures else "FAIL", failures)


def _markdown(report: dict[str, Any]) -> str:
    code = report["code"]
    api = report["api"]
    con = report["connectors"]
    repo = report["repository"]
    lines = [
        "# HDP V7 — audit intégral de l'application",
        "",
        f"Commit audité: `{report['git_sha']}`",
        f"Statut structurel du moteur d'audit: **{report['audit_engine_status']}**",
        "",
        "## Périmètre exécuté",
        "",
        "Code actif, fonctions/classes Python, routes FastAPI, contrats de connecteurs, génération de requêtes natives, clients Python/R, tests, workflows, migrations, Docker/Compose, installateur Windows et marqueurs statiques de sécurité/dette.",
        "",
        "## Métriques code",
        "",
        f"- Fichiers actifs analysés: {code['active_file_count']}",
        f"- Fichiers de code: {code['code_file_count']}",
        f"- Fonctions Python: {code['python_functions']} synchrones + {code['python_async_functions']} async",
        f"- Classes Python: {code['python_classes']}",
        f"- Erreurs AST Python: {len(code['python_parse_errors'])}",
        f"- TODO/FIXME trouvés: {code['todo_fixme_count']}",
        "",
        "## API FastAPI",
        "",
        f"- Version active: {api['application_version']}",
        f"- Routes FastAPI: {api['route_count']}",
        f"- Routes exposées dans le schéma: {api['schema_route_count']}",
        f"- Doublons méthode/chemin: {len(api['duplicate_method_path_routes'])}",
        "",
        "## Connecteurs",
        "",
        f"Connecteurs du registre: **{con['connector_count']}**. Échecs de génération de requête par défaut: **{len(con['preview_failures'])}**.",
        "",
        "|Connecteur|Version|Paramètres projet|Preview|Python|R|",
        "|---|---:|---:|---|---|---|",
    ]
    for row in con["connectors"]:
        lines.append(
            f"|{row['source_id']}|{row['version']}|{row['project_parameter_count']}|{row['request_preview_status']}|"
            f"{'oui' if row['has_python_example'] else 'non'}|{'oui' if row['has_r_example'] else 'non'}|"
        )
    lines += [
        "",
        "## Tests, automatisation et packaging",
        "",
        f"- Fichiers de tests API/source: {repo['source_test_file_count']}",
        f"- Fichiers de tests client Python: {repo['python_client_test_file_count']}",
        f"- Fichiers de tests client R: {repo['r_client_test_file_count']}",
        f"- Workflows GitHub Actions: {repo['workflow_count']}",
        f"- Fichiers liés migrations: {repo['migration_like_file_count']}",
        f"- Fichiers liés installateur: {repo['installer_related_file_count']}",
        "",
        "## Limites de ce fichier",
        "",
        "Ce rapport structurel ne transforme jamais un test non exécuté en PASS. Les résultats des suites unitaires, E2E, R, Docker, sécurité, connecteurs live et Windows sont qualifiés séparément par le workflow `v7-full-application-audit.yml` et doivent être rattachés au même commit avant verdict final.",
        "",
        "## Défauts structurels bloquants",
        "",
    ]
    if report["audit_engine_failures"]:
        lines.extend(f"- {item}" for item in report["audit_engine_failures"])
    else:
        lines.append("Aucun défaut structurel bloquant détecté par le moteur statique/runtime.")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    files = _active_files()
    report: dict[str, Any] = {
        "schema_version": 1,
        "git_sha": os.getenv("GITHUB_SHA", "LOCAL_OR_UNKNOWN"),
        "code": _code_metrics(files),
        "api": _api_inventory(),
        "connectors": _connector_inventory(),
        "repository": _repository_contracts(files),
    }
    status, failures = _status(report)
    report["audit_engine_status"] = status
    report["audit_engine_failures"] = failures
    (OUT / "HDP_V7_FULL_APPLICATION_AUDIT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT / "HDP_V7_FULL_APPLICATION_AUDIT.md").write_text(_markdown(report), encoding="utf-8")
    summary = {
        "git_sha": report["git_sha"],
        "status": status,
        "files": report["code"]["active_file_count"],
        "python_functions": report["code"]["python_functions"] + report["code"]["python_async_functions"],
        "api_routes": report["api"]["route_count"],
        "connectors": report["connectors"]["connector_count"],
        "source_test_files": report["repository"]["source_test_file_count"],
        "workflows": report["repository"]["workflow_count"],
        "failures": failures,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
