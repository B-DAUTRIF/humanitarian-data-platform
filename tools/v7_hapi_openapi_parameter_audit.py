from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "source" / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))

from app.source_registry import connector_definition  # noqa: E402

OPENAPI_URL = "https://hapi.humdata.org/openapi.json"
OUT = ROOT / "qualification-state"


def _schema_type(parameter: dict) -> str:
    schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
    if "$ref" in schema:
        return str(schema["$ref"])
    return str(schema.get("type") or "")


def _enumerate_parameters(document: dict) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path, path_item in sorted((document.get("paths") or {}).items()):
        if not str(path).startswith("/api/v2/") or not isinstance(path_item, dict):
            continue
        operation = path_item.get("get")
        if not isinstance(operation, dict):
            continue
        inherited = path_item.get("parameters") if isinstance(path_item.get("parameters"), list) else []
        own = operation.get("parameters") if isinstance(operation.get("parameters"), list) else []
        seen: set[tuple[str, str]] = set()
        for parameter in [*inherited, *own]:
            if not isinstance(parameter, dict) or "$ref" in parameter:
                continue
            name = str(parameter.get("name") or "")
            location = str(parameter.get("in") or "")
            key = (name, location)
            if not name or key in seen:
                continue
            seen.add(key)
            schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
            rows.append({
                "path": path,
                "operation_id": str(operation.get("operationId") or ""),
                "parameter": name,
                "location": location,
                "required": bool(parameter.get("required", False)),
                "type": _schema_type(parameter),
                "default": schema.get("default"),
                "minimum": schema.get("minimum"),
                "maximum": schema.get("maximum"),
                "enum": schema.get("enum") if isinstance(schema.get("enum"), list) else [],
                "description": str(parameter.get("description") or ""),
            })
    return rows


def _classify(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    definition = connector_definition("hdx-hapi")
    schema = definition["project_schema"]["properties"]
    mapping = {
        "app_identifier": "<environment>",
        "output_format": "<fixed-json>",
        "limit": "result_limit",
        "offset": "offset",
        "location_code": "location_code",
        "admin_level": "admin_level",
    }
    configured_endpoints = set(schema["endpoint"].get("enum", []))
    for row in rows:
        path = str(row["path"])
        suffix = path.removeprefix("/api/v2/").rstrip("/")
        row["endpoint_configured"] = suffix in configured_endpoints
        native = str(row["parameter"])
        hdp = mapping.get(native, "")
        row["hdp_parameter"] = hdp
        implemented = hdp.startswith("<") or hdp in schema
        row["implementation_status"] = "IMPLEMENTED" if implemented else "NOT_IMPLEMENTED"
        row["qualification_status"] = "AUDIT_EXECUTED" if implemented else "NOT_QUALIFIED"
        if native == "limit" and row.get("maximum") is not None:
            hdp_max = schema["result_limit"].get("maximum")
            row["contract_check"] = "PASS" if hdp_max is None or int(hdp_max) <= int(row["maximum"]) else "FAIL"
        elif native == "admin_level" and mapping[native] in schema:
            enum = schema[mapping[native]].get("enum")
            provider_enum = row.get("enum")
            row["contract_check"] = "PASS" if not provider_enum or set(enum or []).issubset(set(provider_enum)) else "FAIL"
        else:
            row["contract_check"] = "PASS"
    return rows


def main() -> int:
    OUT.mkdir(exist_ok=True)
    status: dict[str, object] = {"source": OPENAPI_URL, "execution_status": "NOT_TESTED", "qualification_verdict": "À VÉRIFIER"}
    try:
        request = Request(OPENAPI_URL, headers={"User-Agent": "HDP-V7-ParameterAudit/1.1", "Accept": "application/json"})
        with urlopen(request, timeout=30) as response:  # nosec B310 - fixed HTTPS authority
            raw = response.read(20_000_001)
            http_status = response.status
        if len(raw) > 20_000_000:
            raise RuntimeError("HAPI OpenAPI exceeds 20 MB audit safety limit")
        document = json.loads(raw)
        rows = _classify(_enumerate_parameters(document))
        failures = [row for row in rows if row.get("contract_check") == "FAIL"]
        configured_missing = [row for row in rows if row.get("endpoint_configured") and row.get("implementation_status") == "NOT_IMPLEMENTED"]
        verdict = "NON QUALIFIÉ" if failures else ("QUALIFICATION PARTIELLE" if configured_missing else "QUALIFIÉ POUR TEST UTILISATEUR")
        status = {
            "source": OPENAPI_URL,
            "execution_status": "PASS" if not failures else "FAIL",
            "qualification_verdict": verdict,
            "http_status": http_status,
            "openapi": document.get("openapi"),
            "title": (document.get("info") or {}).get("title"),
            "version": (document.get("info") or {}).get("version"),
            "parameter_rows": len(rows),
            "implemented_rows": sum(row["implementation_status"] == "IMPLEMENTED" for row in rows),
            "not_implemented_rows": sum(row["implementation_status"] == "NOT_IMPLEMENTED" for row in rows),
            "configured_endpoint_rows": sum(bool(row["endpoint_configured"]) for row in rows),
            "configured_endpoint_missing_parameter_rows": len(configured_missing),
            "contract_failures": failures,
            "rows": rows,
        }
    except Exception as exc:
        status = {
            "source": OPENAPI_URL,
            "execution_status": "BLOCKED",
            "qualification_verdict": "BLOQUÉ",
            "error": f"{type(exc).__name__}: {exc}",
            "rows": [],
        }

    (OUT / "V7_HAPI_OPENAPI_PARAMETER_AUDIT.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = status.get("rows") if isinstance(status.get("rows"), list) else []
    if rows:
        fields = ["path", "operation_id", "parameter", "location", "required", "type", "default", "minimum", "maximum", "enum", "hdp_parameter", "endpoint_configured", "implementation_status", "qualification_status", "contract_check", "description"]
        with (OUT / "V7_HAPI_OPENAPI_PARAMETER_MATRIX.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        md = [
            "# HDX HAPI v2 — paramètres OpenAPI",
            "",
            f"Exécution live: **{status['execution_status']}**",
            f"Verdict de qualification: **{status['qualification_verdict']}**",
            "",
            "|Endpoint|Paramètre|Type|HDP|Implémentation|Qualification|",
            "|---|---|---|---|---|---|",
        ]
        for row in rows:
            md.append(f"|{row['path']}|{row['parameter']}|{row['type']}|{row['hdp_parameter']}|{row['implementation_status']}|{row['qualification_status']}|")
        (OUT / "V7_HAPI_OPENAPI_PARAMETER_MATRIX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in status.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0 if status["execution_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
