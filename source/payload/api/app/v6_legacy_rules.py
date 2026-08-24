from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from string import Formatter
from typing import Any, Mapping

from psycopg.types.json import Jsonb

from .v6_rules import RULE_SCHEMA_VERSION, canonical_json, legacy_signal_rule_tree


LEGACY_DATAGRID_ACTION = "legacy_datagrid_search_and_due_refresh"
LEGACY_TEMPLATE_FIELDS = frozenset({"title", "themes", "locations"})
LEGACY_ESTIMATE_KEYS = frozenset(
    {"estimated_requests", "estimated_bytes", "estimated_duration_seconds"}
)


class LegacyRuleMigrationError(ValueError):
    pass


def validate_legacy_query_template(template: Any) -> str:
    if not isinstance(template, str) or len(template) > 300:
        raise LegacyRuleMigrationError("query_template: texte de 300 caractères maximum attendu")
    try:
        parts = list(Formatter().parse(template))
    except ValueError as exc:
        raise LegacyRuleMigrationError("query_template: accolades invalides") from exc
    for _, field_name, format_spec, conversion in parts:
        if field_name is None:
            continue
        if field_name not in LEGACY_TEMPLATE_FIELDS or format_spec or conversion:
            raise LegacyRuleMigrationError(
                "query_template: seuls {title}, {themes} et {locations} sont autorisés"
            )
    return template


def _estimate(parameters: Mapping[str, Any], key: str) -> int:
    value = parameters.get(key, 0)
    if type(value) is not int or not 0 <= value <= 2**63 - 1:
        raise LegacyRuleMigrationError(f"{key}: entier positif ou nul attendu")
    return value


def validate_legacy_datagrid_parameters(parameters: Any) -> dict[str, Any]:
    if not isinstance(parameters, Mapping):
        raise LegacyRuleMigrationError("legacy_datagrid.parameters: objet attendu")
    allowed = {
        "query",
        "query_template",
        "dimensions",
        "locations",
        "refresh_due_resources",
    } | LEGACY_ESTIMATE_KEYS
    unknown = sorted(set(parameters) - allowed)
    if unknown:
        raise LegacyRuleMigrationError(f"legacy_datagrid.parameters: champs inconnus: {unknown}")
    query = parameters.get("query")
    template = parameters.get("query_template")
    if (query is None) == (template is None):
        raise LegacyRuleMigrationError("legacy_datagrid.parameters: query ou query_template requis")
    if template is not None:
        validate_legacy_query_template(template)
    if query is not None and (not isinstance(query, str) or len(query) > 200):
        raise LegacyRuleMigrationError("legacy_datagrid.parameters.query: texte de 200 caractères maximum attendu")
    dimensions = parameters.get("dimensions", [])
    if (
        not isinstance(dimensions, list)
        or len(dimensions) > 6
        or any(not isinstance(item, str) or not item or len(item) > 80 for item in dimensions)
    ):
        raise LegacyRuleMigrationError("legacy_datagrid.parameters.dimensions: liste invalide")
    locations = parameters.get("locations", [])
    if (
        not isinstance(locations, list)
        or len(locations) > 50
        or any(not isinstance(item, str) or not item or len(item) > 160 for item in locations)
    ):
        raise LegacyRuleMigrationError("legacy_datagrid.parameters.locations: liste invalide")
    refresh = parameters.get("refresh_due_resources", False)
    if type(refresh) is not bool:
        raise LegacyRuleMigrationError("legacy_datagrid.parameters.refresh_due_resources: booléen attendu")
    return {
        **({"query": query} if query is not None else {"query_template": template}),
        "dimensions": list(dimensions),
        "locations": list(locations),
        "refresh_due_resources": refresh,
        **{key: _estimate(parameters, key) for key in LEGACY_ESTIMATE_KEYS},
    }


def legacy_datagrid_action(rule: Mapping[str, Any]) -> dict[str, Any]:
    parameters = validate_legacy_datagrid_parameters(
        {
            "query_template": rule.get("query_template", "{title} {themes} {locations}"),
            "dimensions": list(rule.get("data_grid_dimensions") or []),
            "refresh_due_resources": bool(rule.get("refresh_due_resources", True)),
            "estimated_requests": 1,
            "estimated_bytes": 0,
            "estimated_duration_seconds": 45,
        }
    )
    return {
        "type": LEGACY_DATAGRID_ACTION,
        "parameters": parameters,
        "limits": {
            "estimated_requests": 1,
            "estimated_bytes": 0,
            "estimated_duration_seconds": 45,
        },
    }


def materialize_legacy_datagrid_action(
    action: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any]:
    if action.get("type") != LEGACY_DATAGRID_ACTION:
        return dict(action)
    parameters = validate_legacy_datagrid_parameters(action.get("parameters", {}))
    template = parameters.get("query_template")
    if template is None:
        return {"type": LEGACY_DATAGRID_ACTION, "parameters": parameters, "limits": dict(action.get("limits", {}))}
    values = {
        "title": str(event.get("title") or ""),
        "themes": " ".join(str(item) for item in event.get("themes", []) if str(item).strip()),
        "locations": " ".join(str(item) for item in event.get("locations", []) if str(item).strip()),
    }
    query = template.format_map(values)[:200]
    runtime = {
        key: value for key, value in parameters.items() if key != "query_template"
    }
    runtime["query"] = query
    runtime["locations"] = [
        str(item)[:160] for item in event.get("locations", []) if str(item).strip()
    ][:50]
    return {
        "type": LEGACY_DATAGRID_ACTION,
        "parameters": validate_legacy_datagrid_parameters(runtime),
        "limits": dict(action.get("limits", {})),
    }


def migrate_legacy_signal_rules(
    connection: Any,
    project_id: uuid.UUID,
    *,
    confirm: bool,
    actor: str = "local-operator",
) -> dict[str, Any]:
    if not isinstance(actor, str) or not 2 <= len(actor.strip()) <= 120:
        raise LegacyRuleMigrationError("actor: texte de 2 à 120 caractères attendu")
    rows = connection.execute(
        """SELECT id,name,enabled,locations,themes,min_severity,min_confidence,
                  lookback_hours,data_grid_dimensions,query_template,
                  refresh_due_resources,migrated_definition_id
           FROM signal_rules WHERE project_id=%s ORDER BY name,id
           FOR UPDATE""",
        (project_id,),
    ).fetchall()
    candidates: list[dict[str, Any]] = []
    already_migrated: list[dict[str, str]] = []
    for row in rows:
        if row[11] is not None:
            already_migrated.append(
                {"legacy_rule_id": str(row[0]), "definition_id": str(row[11])}
            )
            continue
        legacy = {
            "id": row[0],
            "name": row[1],
            "enabled": bool(row[2]),
            "locations": list(row[3] or []),
            "themes": list(row[4] or []),
            "min_severity": float(row[5]),
            "min_confidence": float(row[6]),
            "lookback_hours": int(row[7]),
            "data_grid_dimensions": list(row[8] or []),
            "query_template": row[9],
            "refresh_due_resources": bool(row[10]),
        }
        tree = legacy_signal_rule_tree(legacy)
        action = legacy_datagrid_action(legacy)
        candidates.append({"legacy": legacy, "tree": tree, "action": action})
    if not confirm:
        return {
            "project_id": str(project_id),
            "confirmed": False,
            "candidates": [
                {
                    "legacy_rule_id": str(item["legacy"]["id"]),
                    "name": item["legacy"]["name"],
                    "enabled": item["legacy"]["enabled"],
                    "rule_tree": item["tree"],
                    "actions": [item["action"]],
                }
                for item in candidates
            ],
            "already_migrated": already_migrated,
        }
    now = datetime.now(UTC)
    migrated: list[dict[str, str]] = []
    for item in candidates:
        legacy = item["legacy"]
        definition_id, version_id = uuid.uuid4(), uuid.uuid4()
        actions = [item["action"]]
        digest = hashlib.sha256(
            canonical_json({"rule_tree": item["tree"], "actions": actions}).encode("utf-8")
        ).hexdigest()
        connection.execute(
            """INSERT INTO rule_definitions
               (id,project_id,scope,name,description,enabled,current_version_number,
                legacy_signal_rule_id,created_by,created_at,updated_at)
               VALUES (%s,%s,'project',%s,%s,%s,1,%s,%s,%s,%s)""",
            (
                definition_id,
                project_id,
                legacy["name"],
                f"Migration sans perte de la règle V5 {legacy['id']}",
                legacy["enabled"],
                legacy["id"],
                actor.strip(),
                now,
                now,
            ),
        )
        connection.execute(
            """INSERT INTO rule_versions
               (id,definition_id,version_number,schema_version,rule_tree,actions,
                definition_sha256,created_by,created_at)
               VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s)""",
            (
                version_id,
                definition_id,
                RULE_SCHEMA_VERSION,
                Jsonb(item["tree"]),
                Jsonb(actions),
                digest,
                actor.strip(),
                now,
            ),
        )
        connection.execute(
            """UPDATE signal_rules
               SET enabled=FALSE,migrated_definition_id=%s,updated_at=%s
               WHERE id=%s AND project_id=%s AND migrated_definition_id IS NULL""",
            (definition_id, now, legacy["id"], project_id),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,
                summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','rule.legacy_migrated','rule_definition',%s,
                       'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(),
                project_id,
                str(definition_id),
                f"Règle V5 migrée : {legacy['name']}",
                Jsonb(
                    {
                        "legacy_signal_rule_id": str(legacy["id"]),
                        "version_id": str(version_id),
                        "sha256": digest,
                    }
                ),
                actor.strip(),
                now,
            ),
        )
        migrated.append(
            {
                "legacy_rule_id": str(legacy["id"]),
                "definition_id": str(definition_id),
                "version_id": str(version_id),
                "sha256": digest,
            }
        )
    return {
        "project_id": str(project_id),
        "confirmed": True,
        "migrated": migrated,
        "already_migrated": already_migrated,
    }
