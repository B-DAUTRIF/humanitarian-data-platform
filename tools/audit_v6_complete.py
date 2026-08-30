#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "source" / "payload" / "api"
APP_ROOT = API_ROOT / "app"
UI = API_ROOT / "static" / "index.html"
VERSION = "6.0.0"

# Imports are intentionally delayed until environment variables required at module import
# have safe audit-only defaults.
os.environ.setdefault("DATABASE_URL", "postgresql://hdp:hdp@127.0.0.1:5432/hdp")
os.environ.setdefault("SQL_READER_URL", os.environ["DATABASE_URL"])
os.environ.setdefault("HDP_LOCAL_TOKEN", "audit-token")
sys.path.insert(0, str(API_ROOT))

FAILURES: list[str] = []
WARNINGS: list[str] = []
CHECKS: list[dict[str, object]] = []


def check(name: str, ok: bool, detail: str = "", blocking: bool = True) -> None:
    CHECKS.append({"name": name, "ok": bool(ok), "detail": detail, "blocking": blocking})
    if not ok:
        (FAILURES if blocking else WARNINGS).append(f"{name}: {detail}")


def text(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8") if isinstance(path, str) else path.read_text(encoding="utf-8")


def route_normal_form(path: str) -> str:
    path = re.sub(r"\$\{[^}]+\}", "{x}", path)
    path = re.sub(r"\{[^}]+\}", "{x}", path)
    return path.rstrip("/") or "/"


def has_route(routes: set[str], candidate: str) -> bool:
    target = route_normal_form(candidate)
    return any(route_normal_form(route) == target for route in routes)


def main() -> None:
    # Native release identity.
    main_py = text("source/payload/api/app/main.py")
    source_registry = text("source/payload/api/app/source_registry.py")
    dockerfile = text("source/payload/api/Dockerfile")
    html = UI.read_text(encoding="utf-8")
    installer = text("source/src/installer.c")
    installer_rc = text("source/src/installer.rc")
    build_ps1 = text("source/build-windows.ps1")

    check("backend version native", 'APP_VERSION = "6.0.0"' in main_py, "APP_VERSION doit être 6.0.0")
    check("registry version native", 'REGISTRY_VERSION = "6.0.0"' in source_registry, "source_registry est encore ancien")
    check("user-agent V6", 'HDP/6.0.0' in source_registry, "user_agent du registre doit être HDP/6.0.0")
    check("Docker V6 entrypoint", 'app.main_v6:app' in dockerfile, "Docker doit démarrer main_v6")
    check("UI release label", "6.0.0-dev" not in html, "l'interface contient encore 6.0.0-dev")
    check("backend release label", "6.0.0-dev" not in main_py, "main.py contient encore 6.0.0-dev")
    check("installer source V6", "6.0.0" in installer and "5.0.2" not in installer, "installer.c n'est pas exclusivement V6")
    check("installer resources V6", ("6,0,0,0" in installer_rc or "6.0.0" in installer_rc) and "5.0.2" not in installer_rc, "installer.rc n'est pas V6")
    check("Windows build V6", "6.0.0" in build_ps1 and "5.0.2" not in build_ps1, "build-windows.ps1 contient une version antérieure")

    # HTML integrity: duplicate IDs are functional bugs because querySelector/getElementById
    # then bind to only one of the duplicated controls.
    ids = re.findall(r'\bid="([^"]+)"', html)
    dup_ids = sorted(name for name, count in Counter(ids).items() if count > 1)
    check("UI unique element IDs", not dup_ids, f"IDs dupliqués: {dup_ids[:30]}")

    nav_views = re.findall(r'data-view="([^"]+)"', html)
    section_views = re.findall(r'<section\s+id="view-([^"]+)"', html)
    nav_set, section_set = set(nav_views), set(section_views)
    orphan_nav = sorted(nav_set - section_set)
    hidden_views = sorted(section_set - nav_set - {"home"})
    check("navigation points to existing views", not orphan_nav, f"navigation orpheline: {orphan_nav}")
    check("all user views reachable", not hidden_views, f"vues sans onglet: {hidden_views}")

    required_views = {
        "search", "intelligence", "actions", "sources", "source-settings", "inventory",
        "projects", "data", "rss", "spip", "mail", "timeline", "map", "scripts",
        "notebooks", "schedules", "sql", "backups", "technologies",
    }
    check("all required V6 views", required_views <= section_set, f"vues manquantes: {sorted(required_views-section_set)}")
    check("all required V6 tabs", required_views <= nav_set, f"onglets manquants: {sorted(required_views-nav_set)}")

    # Explicit UX modes requested in the V4/V6 functional specification.
    modes = {word.casefold() for word in re.findall(r"\b(Simple|Avanc(?:é|e)|Expert)\b", html, flags=re.IGNORECASE)}
    check("Simple/Avancé/Expert modes", len(modes) >= 3, f"modes repérés: {sorted(modes)}")

    # Backend route and OpenAPI audit.
    try:
        from app.main_v6 import app
        routes = {getattr(route, "path", "") for route in app.routes if getattr(route, "path", None)}
        openapi = app.openapi()
        openapi_paths = set(openapi.get("paths", {}))
        check("FastAPI OpenAPI generation", bool(openapi_paths), f"{len(openapi_paths)} chemins")
    except Exception as exc:
        routes = set(); openapi_paths = set()
        check("FastAPI V6 import", False, repr(exc))

    essential_routes = {
        "/api-inventory", "/api-inventory/data", "/api-inventory/sources",
        "/api/v6/catalog", "/api/v6/timeline", "/api/v6/backups",
        "/api/v6/rules/validate", "/api/v6/rules/simulate",
        "/api/v6/rss/candidates", "/api/v6/spip/connections", "/api/v6/mail/messages",
        "/api/auth/status", "/api/projects", "/api/sources", "/api/search",
    }
    missing_routes = sorted(route for route in essential_routes if not has_route(routes, route))
    check("essential backend routes mounted", not missing_routes, f"routes absentes: {missing_routes}")

    # UI references to local APIs should resolve to a backend route after normalizing template IDs.
    api_literals = set(re.findall(r"api\(\s*`([^`]+)`", html)) | set(re.findall(r"api\(\s*'([^']+)'", html)) | set(re.findall(r'api\(\s*"([^"]+)"', html))
    unresolved = []
    for literal in sorted(api_literals):
        path = literal.split("?", 1)[0]
        if path.startswith("/api/") and not has_route(routes, path):
            unresolved.append(path)
    check("UI API calls resolve to backend", not unresolved, f"appels UI non résolus: {unresolved[:40]}")

    # Inventory must be readable and must contain every field that can be configured in the UI.
    try:
        from app.api_inventory import inventory
        from app.source_registry import CONNECTORS, connector_definition
        rows = inventory()
        source_ids = {str(row.get("source_slug")) for row in rows}
        check("inventory covers all searchable connectors", source_ids == set(CONNECTORS), f"inventaire={sorted(source_ids)}, registre={sorted(CONNECTORS)}")
        duplicate_keys = Counter((r.get("source_slug"),r.get("Opération"),r.get("Méthode"),r.get("Endpoint"),r.get("Emplacement"),r.get("Paramètre")) for r in rows)
        dup = [key for key,count in duplicate_keys.items() if count > 1]
        check("inventory keys unique", not dup, f"doublons={len(dup)}")
        missing_schema_fields = []
        for source_id in CONNECTORS:
            definition = connector_definition(source_id)
            names = {str(r.get("Paramètre")) for r in rows if r.get("source_slug") == source_id}
            for scope, schema in (("global",definition["global_settings_schema"]),("project",definition["project_schema"])):
                for field in schema.get("properties", {}):
                    if field not in names:
                        missing_schema_fields.append(f"{source_id}:{scope}:{field}")
        check("all connector schema fields in inventory", not missing_schema_fields, f"absents={missing_schema_fields[:30]}")
        supported = sum(bool(r.get("supported")) for r in rows)
        info = len(rows) - supported
        check("inventory has executable and informational classifications", supported > 0 and info > 0, f"supported={supported}, information={info}")
    except Exception as exc:
        rows = []
        check("inventory readable", False, repr(exc))

    # Functional domains previously requested for HDP. A domain is accepted only when the
    # implementation component and its UI exposure both exist (or when it is installer-only).
    domains = {
        "federated_search": ("source/payload/api/app/federated_search.py", "search"),
        "data_grid_signals": ("source/payload/api/app/v5_features.py", "intelligence"),
        "source_specific_settings": ("source/payload/api/app/source_registry.py", "source-settings"),
        "api_inventory": ("source/payload/api/app/api_inventory.py", "inventory"),
        "projects_preferences": ("source/payload/api/app/main.py", "projects"),
        "github_project_sync": ("source/payload/api/app/github_sync.py", "projects"),
        "cod_m49_hdx": ("source/payload/api/app/project_integrations.py", "projects"),
        "local_library": ("source/payload/api/app/local_library.py", "data"),
        "rss": ("source/payload/api/app/rss_registry.py", "rss"),
        "spip": ("source/payload/api/app/spip_bridge.py", "spip"),
        "mail": ("source/payload/api/app/mail_features.py", "mail"),
        "map": ("source/payload/api/app/map_utils.py", "map"),
        "scripts_python_r": ("source/payload/api/app/script_runtime.py", "scripts"),
        "notebooks": ("source/payload/api/app/main.py", "notebooks"),
        "schedules": ("source/payload/api/app/scheduler_utils.py", "schedules"),
        "timeline": ("source/payload/api/app/v6_timeline.py", "timeline"),
        "sql_readonly": ("source/payload/api/app/sql_workspace.py", "sql"),
        "backups": ("source/payload/api/app/v6_backup.py", "backups"),
        "rules": ("source/payload/api/app/v6_rules.py", "intelligence"),
        "actions": ("source/payload/api/app/v6_actions.py", "actions"),
        "data_jobs": ("source/payload/api/app/v6_data_jobs.py", "actions"),
        "passkey_auth": ("source/payload/api/app/passkey_auth.py", "home"),
        "technology_code_docs": ("source/payload/api/app/technology_registry.py", "technologies"),
        "r_service": ("source/payload/r-service/Dockerfile", "scripts"),
        "spip_plugin": ("source/spip-plugin/hdp/paquet.xml", "spip"),
        "python_client": ("clients-v6/python/pyproject.toml", "technologies"),
        "r_client": ("clients-v6/R/DESCRIPTION", "technologies"),
    }
    matrix = []
    for domain, (component, view) in domains.items():
        exists = (ROOT / component).exists()
        exposed = view == "home" or view in section_set
        ok = exists and exposed
        matrix.append({"domain":domain,"component":component,"view":view,"implemented":exists,"ui":exposed,"ok":ok})
        check(f"function:{domain}", ok, f"component={exists}, ui={exposed}")

    # Installer requirements: environment scan, Docker/winget handling, logs and shortcuts/menu.
    installer_lower = installer.casefold()
    installer_requirements = {
        "environment scan": any(token in installer_lower for token in ("winget", "docker", "probe", "detect")),
        "Docker": "docker" in installer_lower,
        "Windows shortcut/menu": any(token in installer_lower for token in ("shortcut", "start menu", "startmenu", ".lnk")),
        "installation log": "log" in installer_lower,
    }
    for name, ok in installer_requirements.items():
        check(f"installer:{name}", ok, "fonction introuvable dans installer.c")

    report = {
        "version": VERSION,
        "checks": CHECKS,
        "failures": FAILURES,
        "warnings": WARNINGS,
        "summary": {
            "checks": len(CHECKS),
            "passed": sum(1 for item in CHECKS if item["ok"]),
            "failed": len(FAILURES),
            "warnings": len(WARNINGS),
            "backend_routes": len(routes),
            "openapi_paths": len(openapi_paths),
            "inventory_entries": len(rows),
            "ui_views": len(section_set),
        },
        "functional_matrix": matrix,
    }
    out = ROOT / "docs" / "versions" / VERSION / "AUDIT_MACHINE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md = ["# Audit machine HDP V6.0.0", "", f"Contrôles: **{report['summary']['checks']}** · réussis: **{report['summary']['passed']}** · échecs bloquants: **{report['summary']['failed']}**.", "", "## Matrice fonctionnelle", "", "| Domaine | Composant | Vue UI | État |", "|---|---|---|---|"]
    for item in matrix:
        md.append(f"| {item['domain']} | `{item['component']}` | `{item['view']}` | {'OK' if item['ok'] else 'ÉCHEC'} |")
    md += ["", "## Contrôles", "", "| Contrôle | Résultat | Détail |", "|---|---|---|"]
    for item in CHECKS:
        detail = str(item["detail"]).replace("|", "\\|").replace("\n", " ")
        md.append(f"| {item['name']} | {'OK' if item['ok'] else 'ÉCHEC'} | {detail} |")
    if WARNINGS:
        md += ["", "## Avertissements", ""] + [f"- {warning}" for warning in WARNINGS]
    (out.parent / "AUDIT_FONCTIONNEL_UI.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False, sort_keys=True))
    if FAILURES:
        for failure in FAILURES:
            print("FAIL:", failure, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
