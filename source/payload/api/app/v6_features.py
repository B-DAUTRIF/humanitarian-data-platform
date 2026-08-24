from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator

import psycopg
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from .v6_actions import ACTION_POLICY, ActionValidationError, action_status, validate_actions
from .v6_catalog import (
    CAPABILITIES,
    ENDPOINT_STATES,
    FreshnessPolicy,
    cache_decision,
    canonical_cache_key,
    canonical_json,
    contract_diff,
    preserve_unmapped_fields,
    validate_capability_matrix,
    validate_endpoint_transition,
    validate_endpoint_contract,
)
from .v6_storage import (
    StorageValidationError,
    publish_atomically,
    serialize_public_content,
    validation_delay_seconds,
)
from .v6_openapi import OpenApiInventoryError, document_sha256, inventory_openapi_document
from .rss_registry import (
    MAX_RSS_BYTES,
    RSS_REGISTRY_SCOPE,
    RSS_REGISTRY_VERSION,
    parse_rss,
    rss_schema_signature,
    validate_feed_definition,
)
from .secure_http import download_public_file
from .v6_backup import (
    BackupError,
    backup_root,
    build_manifest,
    create_global_dump,
    export_query_as_jsonl,
    file_sha256,
    prevalidate_backup_bundle,
    publish_bundle,
)
from .v6_rules import (
    CONDITION_OPERATORS,
    CORRELATION_MODES,
    MAX_RULE_DEPTH,
    RULE_SCHEMA_VERSION,
    RuleValidationError,
    evaluate_rule,
    rule_sha256,
    validate_rule_tree,
)
from .source_registry import connector_definition


router = APIRouter(prefix="/api/v6", tags=["HDP V6"])
DATABASE_URL = os.environ["DATABASE_URL"]


@contextmanager
def db(*, autocommit: bool = True) -> Iterator[psycopg.Connection[Any]]:
    with psycopg.connect(DATABASE_URL, autocommit=autocommit) as connection:
        yield connection


def ensure_project(project_id: uuid.UUID) -> None:
    with db() as connection:
        row = connection.execute("SELECT 1 FROM projects WHERE id=%s", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Projet introuvable")


def _json_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _contains_sensitive_key(value: Any) -> bool:
    markers = ("password", "secret", "token", "api_key", "authorization", "cookie")
    if isinstance(value, dict):
        return any(
            any(marker in str(key).casefold() for marker in markers) or _contains_sensitive_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def _event_from_row(row: tuple[Any, ...]) -> dict[str, Any]:
    keys = (
        "id",
        "source",
        "external_id",
        "title",
        "summary",
        "occurred_at",
        "received_at",
        "locations",
        "themes",
        "severity",
        "confidence",
        "evidence",
        "raw",
    )
    event = dict(zip(keys, row, strict=True))
    event["id"] = str(event["id"])
    event["severity"] = float(event["severity"])
    event["confidence"] = float(event["confidence"])
    return event


def _maximum_window_hours(node: dict[str, Any]) -> float:
    if node["type"] == "group":
        return max((_maximum_window_hours(child) for child in node["children"]), default=1.0)
    if node["type"] != "correlation":
        return 1.0
    if node["mode"] in {"count", "sequence", "absence"}:
        return float(node["window_hours"])
    return float(node["current_window_hours"]) + float(node["baseline_window_hours"])


def _validated_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        return validate_actions(actions)
    except ActionValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class RuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    rule_tree: dict[str, Any]
    actions: list[dict[str, Any]] = Field(default_factory=list, max_length=50)


class RuleVersionCreate(BaseModel):
    rule_tree: dict[str, Any]
    actions: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    created_by: str = Field(default="local-operator", min_length=2, max_length=120)


class RuleSimulation(BaseModel):
    rule_tree: dict[str, Any]
    event: dict[str, Any]
    events: list[dict[str, Any]] = Field(default_factory=list, max_length=10_000)
    now: datetime | None = None


class RuleTreeRequest(BaseModel):
    rule_tree: dict[str, Any]


class RuleEvaluate(BaseModel):
    event_id: uuid.UUID
    simulate: bool = False


class RuleInheritanceDecision(BaseModel):
    decision: str = Field(pattern="^(adopt|reject|suspend|resume|override|restore_global)$")
    proposed_version_id: uuid.UUID | None = None
    override_name: str | None = Field(default=None, min_length=2, max_length=120)
    decided_by: str = Field(default="local-operator", min_length=2, max_length=120)


class EndpointContractRequest(BaseModel):
    contract: dict[str, Any]


class ConnectorContractBundle(BaseModel):
    api_version: str = Field(min_length=1, max_length=80)
    documentation_url: str = Field(pattern=r"^https://", max_length=1000)
    documentation_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    verified_at: datetime
    contracts: list[dict[str, Any]] = Field(min_length=1, max_length=50_000)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    imported_by: str = Field(default="local-operator", min_length=2, max_length=120)


class EndpointActivationRequest(BaseModel):
    target_state: str = Field(
        pattern="^(inventoried|contract_imported|adapter_implemented|tests_validated|active_global|suspended|obsolete)$"
    )
    adapter_version: str | None = Field(default=None, min_length=1, max_length=120)
    evidence: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class OpenApiInventoryRequest(BaseModel):
    api_version: str = Field(min_length=1, max_length=80)
    documentation_url: str = Field(pattern=r"^https://", max_length=1000)
    verified_at: datetime
    document: dict[str, Any]
    capabilities: dict[str, Any] = Field(default_factory=dict)
    imported_by: str = Field(default="local-operator", min_length=2, max_length=120)


class ProjectEndpointActivation(BaseModel):
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class ContractDiffRequest(BaseModel):
    previous: dict[str, Any]
    current: dict[str, Any]


class CapabilityRequest(BaseModel):
    capabilities: dict[str, Any]


class CacheKeyRequest(BaseModel):
    source_id: str = Field(min_length=2, max_length=80)
    api_version: str = Field(min_length=1, max_length=80)
    endpoint_id: str = Field(min_length=1, max_length=160)
    parameters: dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(min_length=1, max_length=40)
    connector_version: str = Field(min_length=1, max_length=80)
    transformation_version: str = Field(min_length=1, max_length=80)


class CacheDecisionRequest(BaseModel):
    cached_at: datetime
    next_validation_at: datetime
    now: datetime | None = None
    source_failed: bool = False
    project_policy: str = "stale_if_error"
    max_stale_mode: str = "manual"
    fixed_duration_seconds: int | None = None
    frequency_multiple: float | None = None
    project_cap_seconds: int | None = None
    source_frequency_seconds: int | None = None


class CacheMaterializationRequest(BaseModel):
    source_id: str = Field(min_length=2, max_length=80)
    api_version: str = Field(min_length=1, max_length=80)
    endpoint_id: str = Field(min_length=1, max_length=160)
    parameters: dict[str, Any] = Field(default_factory=dict)
    output_format: str = Field(min_length=1, max_length=40)
    connector_version: str = Field(min_length=1, max_length=80)
    transformation_version: str = Field(min_length=1, max_length=80)
    content: Any
    source_frequency_seconds: int | None = Field(default=None, gt=0)
    source_duration_seconds: int | None = Field(default=None, gt=0)
    http_etag: str | None = Field(default=None, max_length=1000)
    http_last_modified: str | None = Field(default=None, max_length=1000)
    data_classification: str = Field(default="public", pattern="^public$")
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class CacheRevalidationRequest(BaseModel):
    outcome: str = Field(pattern="^(not_modified|modified|failed|forced)$")
    response_etag: str | None = Field(default=None, max_length=1000)
    response_last_modified: str | None = Field(default=None, max_length=1000)
    source_frequency_seconds: int | None = Field(default=None, gt=0)
    source_duration_seconds: int | None = Field(default=None, gt=0)
    details: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class EquivalentMaterializationRequest(CacheMaterializationRequest):
    recipe: dict[str, Any]


class ProjectPolicyUpdate(BaseModel):
    stale_policy: str = "stale_if_error"
    max_stale_mode: str = "manual"
    fixed_duration_seconds: int | None = Field(default=None, gt=0)
    frequency_multiple: float | None = Field(default=None, gt=0)
    project_cap_seconds: int | None = Field(default=None, gt=0)
    automatic_request_limit: int = Field(default=100, ge=1, le=100_000)
    automatic_download_bytes: int = Field(default=104_857_600, ge=1_024, le=20_000_000_000)
    automatic_duration_seconds: int = Field(default=300, ge=1, le=86_400)


class CatalogRecordInput(BaseModel):
    external_id: str = Field(min_length=1, max_length=500)
    record_type: str = Field(min_length=1, max_length=120)
    title: str = Field(default="", max_length=2000)
    raw_metadata: dict[str, Any]
    normalized_metadata: dict[str, Any] = Field(default_factory=dict)
    mapped_paths: list[str] = Field(default_factory=list, max_length=5000)
    lineage: dict[str, dict[str, Any]] = Field(default_factory=dict)
    confidence: dict[str, dict[str, Any]] = Field(default_factory=dict)
    valid_until: datetime | None = None


class CatalogBatchInput(BaseModel):
    source_id: str = Field(min_length=2, max_length=80)
    api_version: str = Field(min_length=1, max_length=80)
    endpoint_id: str = Field(min_length=1, max_length=160)
    connector_version: str = Field(min_length=1, max_length=80)
    transformation_version: str = Field(min_length=1, max_length=80)
    acquisition_parameters: dict[str, Any] = Field(default_factory=dict)
    records: list[CatalogRecordInput] = Field(min_length=1, max_length=1000)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class CatalogScheduleUpdate(BaseModel):
    endpoint_id: str = Field(min_length=1, max_length=160)
    api_version: str = Field(min_length=1, max_length=80)
    interval_minutes: int = Field(ge=15, le=525_600)
    enabled: bool = True
    acquisition_parameters: dict[str, Any] = Field(default_factory=dict)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class RssFeedCandidateCreate(BaseModel):
    source_key: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,79}$")
    name: str = Field(min_length=2, max_length=200)
    organization: str = Field(min_length=2, max_length=200)
    region: str = Field(min_length=2, max_length=200)
    themes: list[str] = Field(min_length=1, max_length=50)
    languages: list[str] = Field(min_length=1, max_length=20)
    feed_url: str = Field(pattern=r"^https://", max_length=2000)
    portal_url: str = Field(pattern=r"^https://", max_length=2000)
    evidence_url: str = Field(pattern=r"^https://", max_length=2000)
    license: str = Field(min_length=2, max_length=500)
    declared_frequency: str = Field(min_length=2, max_length=200)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class RssFeedDecision(BaseModel):
    decision: str = Field(pattern="^(approve|suspend|reject)$")
    reason: str = Field(min_length=2, max_length=2000)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class RssApprovedSubscriptionCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    interval_minutes: int = Field(default=360, ge=15, le=43_200)
    enabled: bool = True
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


class DatabaseBackupCreate(BaseModel):
    scope: str = Field(pattern="^(global|project|signals)$")
    project_id: uuid.UUID | None = None
    signal_ids: list[uuid.UUID] = Field(default_factory=list, max_length=10_000)
    actor: str = Field(default="local-operator", min_length=2, max_length=120)


@router.get("/rule-schema")
def rule_schema() -> dict[str, Any]:
    return {
        "schema_version": RULE_SCHEMA_VERSION,
        "node_types": ["group", "condition", "correlation"],
        "group_operators": ["AND", "OR"],
        "condition_operators": sorted(CONDITION_OPERATORS),
        "correlation_modes": sorted(CORRELATION_MODES),
        "engine_max_depth": MAX_RULE_DEPTH,
        "recommended_ui_max_depth": 5,
        "action_types": ACTION_POLICY,
    }


@router.post("/rules/validate")
def validate_rule(payload: RuleTreeRequest) -> dict[str, Any]:
    try:
        tree = validate_rule_tree(payload.rule_tree)
    except RuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"valid": True, "rule_tree": tree, "sha256": rule_sha256(tree)}


@router.post("/rules/simulate")
def simulate_rule(payload: RuleSimulation) -> dict[str, Any]:
    try:
        tree = validate_rule_tree(payload.rule_tree)
        history = payload.events or [payload.event]
        return evaluate_rule(tree, payload.event, history, now=payload.now)
    except (RuleValidationError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _create_rule(scope: str, project_id: uuid.UUID | None, payload: RuleCreate) -> dict[str, Any]:
    try:
        tree = validate_rule_tree(payload.rule_tree)
    except RuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    actions = _validated_actions(payload.actions)
    definition_id, version_id, now = uuid.uuid4(), uuid.uuid4(), datetime.now(UTC)
    digest = _json_hash({"rule_tree": tree, "actions": actions})
    with db(autocommit=False) as connection:
        connection.execute(
            """INSERT INTO rule_definitions
               (id,project_id,scope,name,description,enabled,current_version_number,created_by,created_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,TRUE,1,'local-operator',%s,%s)""",
            (definition_id, project_id, scope, payload.name, payload.description, now, now),
        )
        connection.execute(
            """INSERT INTO rule_versions
               (id,definition_id,version_number,schema_version,rule_tree,actions,definition_sha256,created_by,created_at)
               VALUES (%s,%s,1,%s,%s,%s,%s,'local-operator',%s)""",
            (version_id, definition_id, RULE_SCHEMA_VERSION, Jsonb(tree), Jsonb(actions), digest, now),
        )
        if scope == "global":
            project_rows = connection.execute("SELECT id FROM projects WHERE archived_at IS NULL").fetchall()
            for (existing_project_id,) in project_rows:
                connection.execute(
                    """INSERT INTO rule_inheritance
                       (id,project_id,global_definition_id,adopted_version_id,status,decided_at)
                       VALUES (%s,%s,%s,%s,'current',%s)
                       ON CONFLICT (project_id,global_definition_id) DO NOTHING""",
                    (uuid.uuid4(), existing_project_id, definition_id, version_id, now),
                )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,%s,'rule.created','rule_definition',%s,'completed',%s,%s,'local-operator',%s)""",
            (
                uuid.uuid4(),
                project_id,
                scope,
                str(definition_id),
                f"Règle {payload.name} créée",
                Jsonb({"version_id": str(version_id), "sha256": digest}),
                now,
            ),
        )
    return {
        "id": str(definition_id),
        "version_id": str(version_id),
        "version_number": 1,
        "scope": scope,
        "project_id": str(project_id) if project_id else None,
        "sha256": digest,
        "rule_tree": tree,
        "actions": actions,
    }


@router.post("/rules/global", status_code=201)
def create_global_rule(payload: RuleCreate) -> dict[str, Any]:
    return _create_rule("global", None, payload)


@router.post("/projects/{project_id}/rules", status_code=201)
def create_project_rule(project_id: uuid.UUID, payload: RuleCreate) -> dict[str, Any]:
    ensure_project(project_id)
    return _create_rule("project", project_id, payload)


@router.get("/projects/{project_id}/rules")
def list_rules(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT d.id,d.project_id,d.scope,d.name,d.description,d.enabled,
                      v.version_number,v.id,v.schema_version,v.rule_tree,
                      v.actions,v.definition_sha256,v.created_at,
                      i.status,i.proposed_version_id,pv.version_number,i.project_definition_id
               FROM rule_definitions d
               LEFT JOIN rule_inheritance i ON d.scope='global'
                AND i.global_definition_id=d.id AND i.project_id=%s
               JOIN rule_versions v ON v.definition_id=d.id AND (
                    (d.scope='project' AND v.version_number=d.current_version_number) OR
                    (d.scope='global' AND v.id=i.adopted_version_id)
               )
               LEFT JOIN rule_versions pv ON pv.id=i.proposed_version_id
               WHERE d.project_id=%s OR (d.scope='global' AND i.id IS NOT NULL)
               ORDER BY d.scope,d.name""",
            (project_id, project_id),
        ).fetchall()
    keys = (
        "id",
        "project_id",
        "scope",
        "name",
        "description",
        "enabled",
        "version_number",
        "version_id",
        "schema_version",
        "rule_tree",
        "actions",
        "sha256",
        "created_at",
        "inheritance_status",
        "proposed_version_id",
        "proposed_version_number",
        "override_definition_id",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


@router.post("/rules/{definition_id}/versions", status_code=201)
def create_rule_version(definition_id: uuid.UUID, payload: RuleVersionCreate) -> dict[str, Any]:
    try:
        tree = validate_rule_tree(payload.rule_tree)
    except RuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    actions = _validated_actions(payload.actions)
    digest = _json_hash({"rule_tree": tree, "actions": actions})
    version_id, now = uuid.uuid4(), datetime.now(UTC)
    with db(autocommit=False) as connection:
        row = connection.execute(
            "SELECT scope,project_id,current_version_number FROM rule_definitions WHERE id=%s FOR UPDATE",
            (definition_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Règle introuvable")
        version_number = int(row[2]) + 1
        connection.execute(
            """INSERT INTO rule_versions
               (id,definition_id,version_number,schema_version,rule_tree,actions,definition_sha256,created_by,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                version_id,
                definition_id,
                version_number,
                RULE_SCHEMA_VERSION,
                Jsonb(tree),
                Jsonb(actions),
                digest,
                payload.created_by,
                now,
            ),
        )
        connection.execute(
            "UPDATE rule_definitions SET current_version_number=%s,updated_at=%s WHERE id=%s",
            (version_number, now, definition_id),
        )
        if row[0] == "global":
            connection.execute(
                """UPDATE rule_inheritance
                   SET proposed_version_id=%s,
                       status=CASE WHEN status IN ('overridden','suspended') THEN status ELSE 'update_proposed' END,
                       proposed_at=%s
                   WHERE global_definition_id=%s AND adopted_version_id IS DISTINCT FROM %s""",
                (version_id, now, definition_id, version_id),
            )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,%s,'rule.version_created','rule_definition',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(),
                row[1],
                row[0],
                str(definition_id),
                f"Version {version_number} de règle créée",
                Jsonb({"version_id": str(version_id), "sha256": digest}),
                payload.created_by,
                now,
            ),
        )
    return {"definition_id": str(definition_id), "version_id": str(version_id), "version_number": version_number, "sha256": digest}


@router.post("/projects/{project_id}/rules/{definition_id}/inheritance")
def decide_rule_inheritance(
    project_id: uuid.UUID,
    definition_id: uuid.UUID,
    payload: RuleInheritanceDecision,
) -> dict[str, Any]:
    ensure_project(project_id)
    now = datetime.now(UTC)
    override_definition_id: uuid.UUID | None = None
    with db(autocommit=False) as connection:
        row = connection.execute(
            """SELECT i.id,i.adopted_version_id,i.proposed_version_id,i.status,
                      d.name,d.description,v.rule_tree,v.actions,i.project_definition_id
               FROM rule_inheritance i
               JOIN rule_definitions d ON d.id=i.global_definition_id AND d.scope='global'
               JOIN rule_versions v ON v.id=i.adopted_version_id
               WHERE i.project_id=%s AND i.global_definition_id=%s
               FOR UPDATE""",
            (project_id, definition_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Héritage de règle introuvable")
        (
            inheritance_id,
            adopted_id,
            proposed_id,
            current_status,
            name,
            description,
            tree,
            actions,
            current_override_id,
        ) = row
        if payload.proposed_version_id and payload.proposed_version_id != proposed_id:
            raise HTTPException(status_code=409, detail="Cette version n'est pas la proposition courante du projet")
        target_version_id = payload.proposed_version_id or proposed_id
        if payload.decision == "adopt":
            if current_status == "overridden":
                raise HTTPException(status_code=409, detail="Restaurez d'abord la règle globale avant d'adopter sa mise à jour")
            if not target_version_id:
                raise HTTPException(status_code=409, detail="Aucune version proposée à adopter")
            valid_target = connection.execute(
                "SELECT 1 FROM rule_versions WHERE id=%s AND definition_id=%s",
                (target_version_id, definition_id),
            ).fetchone()
            if not valid_target:
                raise HTTPException(status_code=422, detail="La version proposée n'appartient pas à cette règle")
            connection.execute(
                """UPDATE rule_inheritance SET adopted_version_id=%s,proposed_version_id=NULL,
                          status='current',decided_at=%s
                   WHERE id=%s""",
                (target_version_id, now, inheritance_id),
            )
            adopted_id = target_version_id
        elif payload.decision == "reject":
            if not target_version_id:
                raise HTTPException(status_code=409, detail="Aucune version proposée à rejeter")
            connection.execute(
                "UPDATE rule_inheritance SET status='rejected',decided_at=%s WHERE id=%s",
                (now, inheritance_id),
            )
        elif payload.decision == "suspend":
            if current_status == "overridden":
                raise HTTPException(status_code=409, detail="Suspendez directement la règle de surcharge du projet")
            connection.execute(
                "UPDATE rule_inheritance SET status='suspended',decided_at=%s WHERE id=%s",
                (now, inheritance_id),
            )
        elif payload.decision == "resume":
            if current_status != "suspended":
                raise HTTPException(status_code=409, detail="Seul un héritage suspendu peut être repris")
            connection.execute(
                "UPDATE rule_inheritance SET status='current',decided_at=%s WHERE id=%s",
                (now, inheritance_id),
            )
        elif payload.decision == "override":
            if current_status == "overridden":
                raise HTTPException(status_code=409, detail="Cette règle possède déjà une surcharge de projet")
            override_definition_id, override_version_id = uuid.uuid4(), uuid.uuid4()
            override_name = payload.override_name or f"{name} — surcharge projet"
            digest = _json_hash({"rule_tree": tree, "actions": actions})
            connection.execute(
                """INSERT INTO rule_definitions
                   (id,project_id,scope,name,description,enabled,current_version_number,created_by,created_at,updated_at)
                   VALUES (%s,%s,'project',%s,%s,TRUE,1,%s,%s,%s)""",
                (override_definition_id, project_id, override_name, description, payload.decided_by, now, now),
            )
            connection.execute(
                """INSERT INTO rule_versions
                   (id,definition_id,version_number,schema_version,rule_tree,actions,definition_sha256,created_by,created_at)
                   VALUES (%s,%s,1,%s,%s,%s,%s,%s,%s)""",
                (
                    override_version_id,
                    override_definition_id,
                    RULE_SCHEMA_VERSION,
                    Jsonb(tree),
                    Jsonb(actions),
                    digest,
                    payload.decided_by,
                    now,
                ),
            )
            connection.execute(
                """UPDATE rule_inheritance SET project_definition_id=%s,status='overridden',
                          decided_at=%s WHERE id=%s""",
                (override_definition_id, now, inheritance_id),
            )
        else:
            if current_status != "overridden" or not current_override_id:
                raise HTTPException(status_code=409, detail="Aucune surcharge de projet à abandonner")
            connection.execute(
                "UPDATE rule_definitions SET enabled=FALSE,updated_at=%s WHERE id=%s AND project_id=%s",
                (now, current_override_id, project_id),
            )
            connection.execute(
                """UPDATE rule_inheritance SET project_definition_id=NULL,
                          status=CASE WHEN proposed_version_id IS NULL THEN 'current' ELSE 'update_proposed' END,
                          decided_at=%s WHERE id=%s""",
                (now, inheritance_id),
            )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','rule.inheritance_decided','rule_definition',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(),
                project_id,
                str(definition_id),
                f"Décision d'héritage : {payload.decision}",
                Jsonb(
                    {
                        "adopted_version_id": str(adopted_id),
                        "proposed_version_id": str(target_version_id) if target_version_id else None,
                        "override_definition_id": str(override_definition_id) if override_definition_id else None,
                    }
                ),
                payload.decided_by,
                now,
            ),
        )
    return {
        "project_id": str(project_id),
        "global_definition_id": str(definition_id),
        "decision": payload.decision,
        "adopted_version_id": str(adopted_id),
        "override_definition_id": str(override_definition_id) if override_definition_id else None,
        "decided_at": now,
    }


@router.post("/projects/{project_id}/rules/{definition_id}/evaluate", status_code=201)
def evaluate_stored_rule(project_id: uuid.UUID, definition_id: uuid.UUID, payload: RuleEvaluate) -> dict[str, Any]:
    ensure_project(project_id)
    with db() as connection:
        rule = connection.execute(
            """SELECT d.scope,d.project_id,v.version_number,v.id,v.rule_tree,v.actions,v.definition_sha256
               FROM rule_definitions d
               LEFT JOIN rule_inheritance i ON d.scope='global'
                AND i.global_definition_id=d.id AND i.project_id=%s
               JOIN rule_versions v ON v.definition_id=d.id AND (
                    (d.scope='project' AND v.version_number=d.current_version_number) OR
                    (d.scope='global' AND v.id=i.adopted_version_id)
               )
               WHERE d.id=%s AND d.enabled=TRUE AND (
                    d.project_id=%s OR
                    (d.scope='global' AND i.status IN ('current','update_proposed','rejected'))
               )""",
            (project_id, definition_id, project_id),
        ).fetchone()
        event_row = connection.execute(
            """SELECT id,source,external_id,title,summary,occurred_at,received_at,
                      locations,themes,severity,confidence,evidence,raw
               FROM signal_events WHERE id=%s AND project_id=%s""",
            (payload.event_id, project_id),
        ).fetchone()
    if not rule:
        raise HTTPException(status_code=404, detail="Règle introuvable dans ce projet")
    if not event_row:
        raise HTTPException(status_code=404, detail="Événement introuvable dans ce projet")
    tree, actions = rule[4], rule[5]
    window_hours = min(_maximum_window_hours(tree), 24 * 365 * 5)
    now = datetime.now(UTC)
    start = now - timedelta(hours=window_hours)
    with db() as connection:
        history_rows = connection.execute(
            """SELECT id,source,external_id,title,summary,occurred_at,received_at,
                      locations,themes,severity,confidence,evidence,raw
               FROM signal_events
               WHERE project_id=%s AND occurred_at BETWEEN %s AND %s
               ORDER BY occurred_at LIMIT 10000""",
            (project_id, start, now),
        ).fetchall()
    event = _event_from_row(event_row)
    history = [_event_from_row(row) for row in history_rows]
    result = evaluate_rule(tree, event, history, now=now)
    input_sha = _json_hash({"rule_version": str(rule[3]), "event": event, "history": history})
    evaluation_id = uuid.uuid4()
    action_requests: list[dict[str, Any]] = []
    with db(autocommit=False) as connection:
        connection.execute(
            """INSERT INTO rule_evaluations
               (id,project_id,definition_id,rule_version_id,triggering_event_id,input_version_sha256,
                window_start,window_end,matched,events_examined,proof,simulated,created_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                evaluation_id,
                project_id,
                definition_id,
                rule[3],
                payload.event_id,
                input_sha,
                start,
                now,
                result["matched"],
                Jsonb([item["id"] for item in history]),
                Jsonb(result["proof"]),
                payload.simulate,
                now,
            ),
        )
        if result["matched"] and not payload.simulate:
            policy = connection.execute(
                """SELECT automatic_request_limit,automatic_download_bytes,automatic_duration_seconds
                   FROM project_data_policies WHERE project_id=%s""",
                (project_id,),
            ).fetchone() or (100, 104_857_600, 300)
            for index, action in enumerate(actions):
                status, reason = action_status(action, int(policy[0]), int(policy[1]), int(policy[2]))
                idempotency_key = _json_hash(
                    {
                        "project_id": str(project_id),
                        "rule_version_id": str(rule[3]),
                        "event_id": str(payload.event_id),
                        "input_sha256": input_sha,
                        "action_index": index,
                        "action_type": action["type"],
                    }
                )
                request_id = uuid.uuid4()
                inserted = connection.execute(
                    """INSERT INTO action_requests
                       (id,project_id,evaluation_id,action_type,risk_level,status,parameters,limits,
                        idempotency_key,requested_at,decision_reason)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (idempotency_key) DO NOTHING RETURNING id""",
                    (
                        request_id,
                        project_id,
                        evaluation_id,
                        action["type"],
                        ACTION_POLICY[action["type"]]["risk"],
                        status,
                        Jsonb(action.get("parameters", {})),
                        Jsonb(action.get("limits", {})),
                        idempotency_key,
                        now,
                        reason,
                    ),
                ).fetchone()
                action_requests.append(
                    {
                        "id": str(inserted[0]) if inserted else None,
                        "type": action["type"],
                        "status": status if inserted else "deduplicated",
                        "idempotency_key": idempotency_key,
                        "reason": reason,
                    }
                )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project',%s,'rule_evaluation',%s,'completed',%s,%s,'local-operator',%s)""",
            (
                uuid.uuid4(),
                project_id,
                "rule.simulated" if payload.simulate else "rule.evaluated",
                str(evaluation_id),
                "Règle simulée" if payload.simulate else "Règle évaluée",
                Jsonb(
                    {
                        "definition_id": str(definition_id),
                        "rule_version_id": str(rule[3]),
                        "matched": result["matched"],
                        "input_sha256": input_sha,
                        "action_requests": action_requests,
                    }
                ),
                now,
            ),
        )
    return {"evaluation_id": str(evaluation_id), **result, "input_sha256": input_sha, "action_requests": action_requests}


def dispatch_event_to_v6_rules(project_id: uuid.UUID, event_id: uuid.UUID) -> dict[str, Any]:
    """Évalue un événement ingéré contre toutes les règles V6 actives du projet."""
    with db() as connection:
        rows = connection.execute(
            """SELECT d.id
               FROM rule_definitions d
               WHERE d.project_id=%s AND d.scope='project' AND d.enabled=TRUE
               UNION
               SELECT d.id
               FROM rule_definitions d
               JOIN rule_inheritance i ON i.global_definition_id=d.id AND i.project_id=%s
               WHERE d.scope='global' AND d.enabled=TRUE
                 AND i.status IN ('current','update_proposed','rejected')
               ORDER BY 1""",
            (project_id, project_id),
        ).fetchall()
    evaluations: list[dict[str, Any]] = []
    for row in rows:
        try:
            result = evaluate_stored_rule(
                project_id,
                row[0],
                RuleEvaluate(event_id=event_id, simulate=False),
            )
            evaluations.append(
                {
                    "definition_id": str(row[0]),
                    "evaluation_id": result["evaluation_id"],
                    "matched": result["matched"],
                    "action_requests": result["action_requests"],
                }
            )
        except HTTPException as exc:
            evaluations.append(
                {"definition_id": str(row[0]), "error": str(exc.detail), "status_code": exc.status_code}
            )
    return {"event_id": str(event_id), "evaluations": evaluations}


def _timeline(scope: str, project_id: uuid.UUID | None, event_type: str | None, limit: int) -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute(
            """SELECT id,project_id,scope,event_type,object_type,object_id,status,
                      summary,details,actor,occurred_at
               FROM application_timeline
               WHERE scope=%s AND project_id IS NOT DISTINCT FROM %s
                 AND (%s IS NULL OR event_type=%s)
               ORDER BY occurred_at DESC,id DESC LIMIT %s""",
            (scope, project_id, event_type, event_type, limit),
        ).fetchall()
    keys = (
        "id",
        "project_id",
        "scope",
        "event_type",
        "object_type",
        "object_id",
        "status",
        "summary",
        "details",
        "actor",
        "occurred_at",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


@router.get("/timeline")
def global_timeline(
    event_type: str | None = Query(default=None, min_length=2, max_length=120),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    return _timeline("global", None, event_type, limit)


@router.get("/projects/{project_id}/timeline")
def project_timeline(
    project_id: uuid.UUID,
    event_type: str | None = Query(default=None, min_length=2, max_length=120),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    ensure_project(project_id)
    return _timeline("project", project_id, event_type, limit)


@router.post("/connectors/contracts/validate")
def validate_contract(payload: EndpointContractRequest) -> dict[str, Any]:
    try:
        return {"valid": True, "contract": validate_endpoint_contract(payload.contract)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/connectors/contracts/diff")
def compare_contracts(payload: ContractDiffRequest) -> dict[str, Any]:
    try:
        return contract_diff(payload.previous, payload.current)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/connectors/capabilities/validate")
def validate_capabilities(payload: CapabilityRequest) -> dict[str, Any]:
    try:
        return {"valid": True, "capabilities": validate_capability_matrix(payload.capabilities)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/connectors/schema")
def connector_schema() -> dict[str, Any]:
    return {
        "capabilities": CAPABILITIES,
        "endpoint_states": ENDPOINT_STATES,
        "inventory_is_not_execution": True,
        "activation_policy": "progressive",
        "openapi_inventory": {
            "formats": ["OpenAPI 3.x", "Swagger 2.0"],
            "scope": "all documented paths and HTTP operations",
            "remote_references": False,
        },
    }


@router.post("/sources/{source_id}/openapi/inventory", status_code=201)
def inventory_source_openapi(source_id: str, payload: OpenApiInventoryRequest) -> dict[str, Any]:
    try:
        contracts = inventory_openapi_document(
            payload.document,
            source_id=source_id,
            api_version=payload.api_version,
            documentation_url=payload.documentation_url,
        )
        bundle = ConnectorContractBundle(
            api_version=payload.api_version,
            documentation_url=payload.documentation_url,
            documentation_sha256=document_sha256(payload.document),
            verified_at=payload.verified_at,
            contracts=contracts,
            capabilities=payload.capabilities,
            imported_by=payload.imported_by,
        )
    except (OpenApiInventoryError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = import_connector_contracts(source_id, bundle)
    return {
        **result,
        "inventory_format": "openapi",
        "document_sha256": bundle.documentation_sha256.casefold(),
        "documented_operations": len(contracts),
        "execution_activated": False,
    }


def _bundle_changes(previous: dict[str, Any] | None, current_contracts: list[dict[str, Any]]) -> dict[str, Any]:
    previous_contracts = previous.get("contracts", []) if isinstance(previous, dict) else []
    previous_map = {
        (item.get("endpoint_id"), str(item.get("method", "")).upper(), item.get("path")): item
        for item in previous_contracts
        if isinstance(item, dict)
    }
    current_map = {
        (item["endpoint_id"], item["method"], item["path"]): item for item in current_contracts
    }
    changed: list[dict[str, Any]] = []
    for key in sorted(previous_map.keys() & current_map.keys(), key=str):
        comparison = contract_diff(previous_map[key], {
            field: value
            for field, value in current_map[key].items()
            if field not in {"contract_sha256", "schema_version"}
        })
        if comparison["activation_requires_validation"]:
            changed.append({"identity": list(key), **comparison})
    return {
        "added": [list(key) for key in sorted(current_map.keys() - previous_map.keys(), key=str)],
        "removed": [list(key) for key in sorted(previous_map.keys() - current_map.keys(), key=str)],
        "changed": changed,
        "breaking": bool(
            previous_map.keys() - current_map.keys()
            or any(item["breaking"] for item in changed)
        ),
    }


@router.post("/sources/{source_id}/contracts", status_code=201)
def import_connector_contracts(source_id: str, payload: ConnectorContractBundle) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    identities: set[tuple[str, str, str]] = set()
    try:
        for raw_contract in payload.contracts:
            contract = validate_endpoint_contract(raw_contract)
            if contract["source_id"] != source_id:
                raise ValueError("source_id du contrat différent de la source demandée")
            if contract["api_version"] != payload.api_version:
                raise ValueError("version d'API incohérente dans le lot")
            if contract.get("documentation_url") not in {None, payload.documentation_url}:
                raise ValueError("URL documentaire incohérente dans le lot")
            identity = (contract["endpoint_id"], contract["method"], contract["path"])
            if identity in identities:
                raise ValueError(f"endpoint dupliqué dans le lot: {identity}")
            identities.add(identity)
            normalized.append(contract)
        capabilities = validate_capability_matrix(payload.capabilities)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    known_endpoint_ids = {item["endpoint_id"] for item in normalized}
    for capability, item in capabilities.items():
        unknown = set(item["endpoint_ids"]) - known_endpoint_ids
        if unknown:
            raise HTTPException(
                status_code=422,
                detail=f"{capability}: endpoints inconnus dans la matrice: {sorted(unknown)}",
            )

    bundle_sha256 = _json_hash(
        {
            "source_id": source_id,
            "api_version": payload.api_version,
            "documentation_sha256": payload.documentation_sha256.casefold(),
            "contracts": normalized,
            "capabilities": capabilities,
        }
    )
    now = datetime.now(UTC)
    raw_bundle = {
        "bundle_sha256": bundle_sha256,
        "schema_version": "6.0.0",
        "contracts": payload.contracts,
        "capabilities": capabilities,
    }
    with db(autocommit=False) as connection:
        previous = connection.execute(
            """SELECT id,raw_contract FROM source_api_versions
               WHERE source_id=%s AND valid_until IS NULL
               ORDER BY valid_from DESC LIMIT 1 FOR UPDATE""",
            (source_id,),
        ).fetchone()
        if previous and isinstance(previous[1], dict) and previous[1].get("bundle_sha256") == bundle_sha256:
            return {
                "source_id": source_id,
                "api_version_id": str(previous[0]),
                "bundle_sha256": bundle_sha256,
                "endpoint_count": len(normalized),
                "idempotent": True,
                "changes": {"added": [], "removed": [], "changed": [], "breaking": False},
            }
        changes = _bundle_changes(previous[1] if previous else None, normalized)
        if previous:
            connection.execute(
                "UPDATE source_api_versions SET valid_until=%s WHERE id=%s",
                (now, previous[0]),
            )
        api_version_id = uuid.uuid4()
        connection.execute(
            """INSERT INTO source_api_versions
               (id,source_id,api_version,documentation_url,documentation_sha256,
                verified_at,valid_from,raw_contract)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                api_version_id,
                source_id,
                payload.api_version,
                payload.documentation_url,
                payload.documentation_sha256.casefold(),
                payload.verified_at,
                now,
                Jsonb(raw_bundle),
            ),
        )
        for contract in normalized:
            endpoint_uuid = uuid.uuid4()
            imported_state = "obsolete" if contract["state"] == "obsolete" else (
                "inventoried" if contract["state"] == "inventoried" else "contract_imported"
            )
            connection.execute(
                """INSERT INTO source_endpoints
                   (id,api_version_id,endpoint_id,method,path,summary,authentication,
                    formats,limits,cache_contract,allowed_hosts,state,contract_sha256,state_updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    endpoint_uuid,
                    api_version_id,
                    contract["endpoint_id"],
                    contract["method"],
                    contract["path"],
                    str(contract.get("summary", ""))[:5000],
                    Jsonb(contract["authentication"]),
                    Jsonb(contract.get("formats", [])),
                    Jsonb(contract.get("limits", {})),
                    Jsonb(contract.get("cache", {})),
                    Jsonb(contract["allowed_hosts"]),
                    imported_state,
                    contract["contract_sha256"],
                    now,
                ),
            )
            for parameter in contract["parameters"]:
                connection.execute(
                    """INSERT INTO endpoint_parameters
                       (id,endpoint_id,name,location,schema,required,documented,supported,
                        sensitive,description,dependencies)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        uuid.uuid4(), endpoint_uuid, parameter["name"], parameter["location"],
                        Jsonb(parameter["schema"]), parameter["required"], parameter["documented"],
                        parameter["supported"], parameter["sensitive"], parameter["description"],
                        Jsonb(parameter["dependencies"]),
                    ),
                )
            for field in contract["response_fields"]:
                connection.execute(
                    """INSERT INTO response_fields
                       (id,endpoint_id,field_path,schema,documented,observed,nullable,
                        cardinality,first_seen_version,last_seen_at)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        uuid.uuid4(), endpoint_uuid, field["path"], Jsonb(field["schema"]),
                        field["documented"], field["observed"], field["nullable"],
                        field["cardinality"], field["first_seen_version"],
                        now if field["observed"] else None,
                    ),
                )
        for capability, item in capabilities.items():
            connection.execute(
                """INSERT INTO connector_capabilities
                   (source_id,capability,support_level,state,endpoint_ids,equivalent_recipe,tested_at,updated_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (source_id,capability) DO UPDATE SET
                     support_level=EXCLUDED.support_level,state=EXCLUDED.state,
                     endpoint_ids=EXCLUDED.endpoint_ids,equivalent_recipe=EXCLUDED.equivalent_recipe,
                     tested_at=EXCLUDED.tested_at,updated_at=EXCLUDED.updated_at""",
                (
                    source_id, capability, item["support"], item["state"],
                    Jsonb(item["endpoint_ids"]), Jsonb(item["equivalent_recipe"]),
                    item["tested_at"], now,
                ),
            )
        connection.execute(
            """INSERT INTO application_timeline
               (id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,'global','connector.contract_imported','source_api_version',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), str(api_version_id), f"Contrat {source_id} {payload.api_version} importé",
                Jsonb({"bundle_sha256": bundle_sha256, "endpoint_count": len(normalized), "changes": changes}),
                payload.imported_by, now,
            ),
        )
    return {
        "source_id": source_id,
        "api_version_id": str(api_version_id),
        "bundle_sha256": bundle_sha256,
        "endpoint_count": len(normalized),
        "idempotent": False,
        "changes": changes,
    }


@router.get("/sources/{source_id}/endpoints")
def list_source_endpoints(source_id: str, include_obsolete: bool = False) -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute(
            """SELECT e.id,v.api_version,v.documentation_url,v.verified_at,e.endpoint_id,
                      e.method,e.path,e.summary,e.authentication,e.formats,e.limits,
                      e.cache_contract,e.allowed_hosts,e.state,e.contract_sha256,e.activated_at,
                      e.adapter_version,e.test_evidence,e.state_updated_at,
                      (SELECT count(*) FROM endpoint_parameters p WHERE p.endpoint_id=e.id),
                      (SELECT count(*) FROM response_fields f WHERE f.endpoint_id=e.id),
                      (v.valid_until IS NULL)
               FROM source_endpoints e JOIN source_api_versions v ON v.id=e.api_version_id
               WHERE v.source_id=%s AND (%s OR e.state<>'obsolete')
               ORDER BY v.valid_from DESC,e.path,e.method""",
            (source_id, include_obsolete),
        ).fetchall()
    keys = (
        "id",
        "api_version",
        "documentation_url",
        "verified_at",
        "endpoint_id",
        "method",
        "path",
        "summary",
        "authentication",
        "formats",
        "limits",
        "cache",
        "allowed_hosts",
        "state",
        "contract_sha256",
        "activated_at",
        "adapter_version",
        "test_evidence",
        "state_updated_at",
        "parameter_count",
        "response_field_count",
        "current_api_version",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


def _endpoint_record(connection: Any, source_id: str, endpoint_uuid: uuid.UUID, *, lock: bool = False) -> tuple[Any, ...] | None:
    suffix = " FOR UPDATE" if lock else ""
    return connection.execute(
        """SELECT e.id,e.endpoint_id,e.method,e.path,e.summary,e.authentication,e.formats,
                  e.limits,e.cache_contract,e.allowed_hosts,e.state,e.contract_sha256,
                  e.activated_at,e.suspended_at,e.adapter_version,e.test_evidence,
                  e.state_updated_at,v.id,v.api_version,v.documentation_url,
                  v.documentation_sha256,v.verified_at,v.valid_from,v.valid_until
           FROM source_endpoints e
           JOIN source_api_versions v ON v.id=e.api_version_id
           WHERE v.source_id=%s AND e.id=%s""" + suffix,
        (source_id, endpoint_uuid),
    ).fetchone()


@router.get("/sources/{source_id}/endpoints/{endpoint_uuid}")
def source_endpoint_detail(source_id: str, endpoint_uuid: uuid.UUID) -> dict[str, Any]:
    with db() as connection:
        row = _endpoint_record(connection, source_id, endpoint_uuid)
        if not row:
            raise HTTPException(status_code=404, detail="Endpoint introuvable pour cette source")
        parameters = connection.execute(
            """SELECT id,name,location,schema,required,documented,supported,sensitive,
                      description,dependencies
               FROM endpoint_parameters WHERE endpoint_id=%s ORDER BY location,name""",
            (endpoint_uuid,),
        ).fetchall()
        fields = connection.execute(
            """SELECT id,field_path,schema,documented,observed,nullable,cardinality,
                      first_seen_version,last_seen_at
               FROM response_fields WHERE endpoint_id=%s ORDER BY field_path""",
            (endpoint_uuid,),
        ).fetchall()
        history = connection.execute(
            """SELECT id,previous_state,new_state,evidence,actor,occurred_at
               FROM endpoint_activation_history WHERE endpoint_id=%s
               ORDER BY occurred_at DESC,id DESC""",
            (endpoint_uuid,),
        ).fetchall()
    endpoint_keys = (
        "id", "endpoint_id", "method", "path", "summary", "authentication", "formats",
        "limits", "cache", "allowed_hosts", "state", "contract_sha256", "activated_at",
        "suspended_at", "adapter_version", "test_evidence", "state_updated_at",
        "api_version_id", "api_version", "documentation_url", "documentation_sha256",
        "verified_at", "valid_from", "valid_until",
    )
    parameter_keys = (
        "id", "name", "location", "schema", "required", "documented", "supported",
        "sensitive", "description", "dependencies",
    )
    field_keys = (
        "id", "path", "schema", "documented", "observed", "nullable", "cardinality",
        "first_seen_version", "last_seen_at",
    )
    history_keys = ("id", "previous_state", "new_state", "evidence", "actor", "occurred_at")
    return {
        "source_id": source_id,
        "endpoint": dict(zip(endpoint_keys, row, strict=True)),
        "parameters": [dict(zip(parameter_keys, item, strict=True)) for item in parameters],
        "response_fields": [dict(zip(field_keys, item, strict=True)) for item in fields],
        "activation_history": [dict(zip(history_keys, item, strict=True)) for item in history],
    }


@router.post("/sources/{source_id}/endpoints/{endpoint_uuid}/state")
def activate_source_endpoint(
    source_id: str,
    endpoint_uuid: uuid.UUID,
    payload: EndpointActivationRequest,
) -> dict[str, Any]:
    if _contains_sensitive_key(payload.evidence):
        raise HTTPException(status_code=422, detail="Les preuves d'activation ne doivent contenir aucun secret")
    now = datetime.now(UTC)
    with db(autocommit=False) as connection:
        row = _endpoint_record(connection, source_id, endpoint_uuid, lock=True)
        if not row:
            raise HTTPException(status_code=404, detail="Endpoint introuvable pour cette source")
        current_state = str(row[10])
        contract_sha = str(row[11])
        current_adapter = row[14]
        current_evidence = row[15] if isinstance(row[15], dict) else {}
        valid_until = row[23]
        if valid_until is not None and payload.target_state != "obsolete":
            raise HTTPException(status_code=409, detail="Une ancienne version d'API ne peut plus être activée")
        try:
            target_state, transition = validate_endpoint_transition(current_state, payload.target_state)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if transition == "unchanged":
            return {
                "source_id": source_id,
                "endpoint_id": str(endpoint_uuid),
                "state": current_state,
                "idempotent": True,
            }
        adapter_version = payload.adapter_version or current_adapter
        if target_state in {"adapter_implemented", "tests_validated", "active_global"} and not adapter_version:
            raise HTTPException(status_code=422, detail="La version de l'adaptateur est obligatoire")
        evidence = {**current_evidence, **payload.evidence}
        if target_state == "tests_validated":
            if not _is_sha256(evidence.get("test_report_sha256")):
                raise HTTPException(status_code=422, detail="Une empreinte SHA-256 du rapport de test est obligatoire")
            if not evidence.get("tested_at") or evidence.get("passed") is not True:
                raise HTTPException(status_code=422, detail="La date du test et un résultat réussi sont obligatoires")
            if evidence.get("contract_sha256") != contract_sha:
                raise HTTPException(status_code=422, detail="Le rapport doit viser le contrat courant")
        if target_state == "active_global" and (
            not _is_sha256(evidence.get("test_report_sha256"))
            or evidence.get("passed") is not True
            or evidence.get("contract_sha256") != contract_sha
        ):
            raise HTTPException(status_code=409, detail="Les preuves de validation du contrat courant sont absentes")
        if target_state in {"suspended", "obsolete"} and not str(evidence.get("reason", "")).strip():
            raise HTTPException(status_code=422, detail="Un motif est obligatoire pour suspendre ou déclarer obsolète")
        connection.execute(
            """UPDATE source_endpoints
               SET state=%s,adapter_version=%s,test_evidence=%s,state_updated_at=%s,
                   activated_at=CASE WHEN %s='active_global' THEN %s ELSE activated_at END,
                   suspended_at=CASE WHEN %s='suspended' THEN %s
                                     WHEN %s<>'suspended' THEN NULL ELSE suspended_at END
               WHERE id=%s""",
            (
                target_state, adapter_version, Jsonb(evidence), now,
                target_state, now, target_state, now, target_state, endpoint_uuid,
            ),
        )
        connection.execute(
            """INSERT INTO endpoint_activation_history
               (id,endpoint_id,previous_state,new_state,evidence,actor,occurred_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (uuid.uuid4(), endpoint_uuid, current_state, target_state, Jsonb(payload.evidence), payload.actor, now),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,'global','connector.endpoint_state','source_endpoint',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), str(endpoint_uuid),
                f"Endpoint {row[1]} : {current_state} → {target_state}",
                Jsonb({"source_id": source_id, "transition": transition, "contract_sha256": contract_sha}),
                payload.actor, now,
            ),
        )
    return {
        "source_id": source_id,
        "endpoint_id": str(endpoint_uuid),
        "previous_state": current_state,
        "state": target_state,
        "transition": transition,
        "adapter_version": adapter_version,
        "idempotent": False,
    }


@router.put("/projects/{project_id}/sources/{source_id}/endpoints/{endpoint_uuid}")
def configure_project_endpoint(
    project_id: uuid.UUID,
    source_id: str,
    endpoint_uuid: uuid.UUID,
    payload: ProjectEndpointActivation,
) -> dict[str, Any]:
    ensure_project(project_id)
    if _contains_sensitive_key(payload.settings):
        raise HTTPException(status_code=422, detail="Les réglages de projet ne doivent contenir aucun secret")
    now = datetime.now(UTC)
    with db(autocommit=False) as connection:
        row = _endpoint_record(connection, source_id, endpoint_uuid, lock=True)
        if not row:
            raise HTTPException(status_code=404, detail="Endpoint introuvable pour cette source")
        state, valid_until = str(row[10]), row[23]
        if payload.enabled and (valid_until is not None or state not in {"tests_validated", "active_global"}):
            raise HTTPException(
                status_code=409,
                detail="L'endpoint doit appartenir à la version courante et avoir des tests validés",
            )
        connection.execute(
            """INSERT INTO project_endpoint_activations
               (project_id,endpoint_id,enabled,settings,activated_by,activated_at,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (project_id,endpoint_id) DO UPDATE SET
                 enabled=EXCLUDED.enabled,settings=EXCLUDED.settings,
                 activated_by=EXCLUDED.activated_by,updated_at=EXCLUDED.updated_at,
                 activated_at=CASE WHEN EXCLUDED.enabled THEN EXCLUDED.activated_at
                                   ELSE project_endpoint_activations.activated_at END""",
            (project_id, endpoint_uuid, payload.enabled, Jsonb(payload.settings), payload.actor, now, now),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','connector.project_activation','source_endpoint',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, str(endpoint_uuid),
                f"Endpoint {row[1]} {'activé' if payload.enabled else 'désactivé'} pour le projet",
                Jsonb({"source_id": source_id, "endpoint_state": state, "settings_sha256": _json_hash(payload.settings)}),
                payload.actor, now,
            ),
        )
    return {
        "project_id": str(project_id),
        "source_id": source_id,
        "endpoint_id": str(endpoint_uuid),
        "enabled": payload.enabled,
        "settings_sha256": _json_hash(payload.settings),
    }


@router.get("/sources/{source_id}/configuration")
def source_configuration(source_id: str) -> dict[str, Any]:
    try:
        definition = connector_definition(source_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Connecteur introuvable") from exc
    return {
        "source_id": source_id,
        "configuration_file": "app/source_registry.py",
        "read_only": True,
        "registry_version": definition["registry_version"],
        "verified_at": definition["verified_at"],
        "base_url": definition["base_url"],
        "global_settings_schema": definition["global_settings_schema"],
        "project_schema": definition["project_schema"],
        "official_links": definition["official_links"],
        "documentation_evidence": definition["documentation_evidence"],
        "technical_profile": definition["technical_profile"],
        "secret_environment_variable": definition["secret_environment_variable"],
        "secret_value_exposed": False,
    }


@router.post("/cache/key")
def build_cache_key(payload: CacheKeyRequest) -> dict[str, Any]:
    try:
        key, descriptor = canonical_cache_key(**payload.model_dump())
        return {"cache_key": key, "descriptor": descriptor}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/cache/decision")
def decide_cache(payload: CacheDecisionRequest) -> dict[str, Any]:
    try:
        policy = FreshnessPolicy(
            project_policy=payload.project_policy,
            max_stale_mode=payload.max_stale_mode,
            fixed_duration_seconds=payload.fixed_duration_seconds,
            frequency_multiple=payload.frequency_multiple,
            project_cap_seconds=payload.project_cap_seconds,
        )
        return cache_decision(
            cached_at=payload.cached_at,
            next_validation_at=payload.next_validation_at,
            now=payload.now,
            source_failed=payload.source_failed,
            policy=policy,
            source_frequency_seconds=payload.source_frequency_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _assert_project_endpoint_available(
    connection: Any,
    project_id: uuid.UUID,
    source_id: str,
    api_version: str,
    endpoint_id: str,
) -> tuple[uuid.UUID, str]:
    row = connection.execute(
        """SELECT e.id,e.contract_sha256
           FROM source_endpoints e
           JOIN source_api_versions v ON v.id=e.api_version_id
           LEFT JOIN project_endpoint_activations p
             ON p.endpoint_id=e.id AND p.project_id=%s AND p.enabled=TRUE
           WHERE v.source_id=%s AND v.api_version=%s AND v.valid_until IS NULL
             AND e.endpoint_id=%s AND e.state IN ('tests_validated','active_global')
             AND (e.state='active_global' OR p.endpoint_id IS NOT NULL)
           ORDER BY e.state='active_global' DESC,e.state_updated_at DESC NULLS LAST
           LIMIT 1""",
        (project_id, source_id, api_version, endpoint_id),
    ).fetchone()
    if not row:
        raise HTTPException(
            status_code=409,
            detail="Le connecteur ou l'endpoint n'est pas activé pour ce projet et cette version",
        )
    return row[0], str(row[1])


def _project_cache_policy(connection: Any, project_id: uuid.UUID) -> tuple[FreshnessPolicy, int]:
    row = connection.execute(
        """SELECT stale_policy,max_stale_mode,fixed_duration_seconds,frequency_multiple,
                  project_cap_seconds,automatic_download_bytes
           FROM project_data_policies WHERE project_id=%s""",
        (project_id,),
    ).fetchone()
    if not row:
        return FreshnessPolicy(project_policy="stale_if_error", max_stale_mode="manual"), 104_857_600
    return (
        FreshnessPolicy(
            project_policy=row[0],
            max_stale_mode=row[1],
            fixed_duration_seconds=row[2],
            frequency_multiple=float(row[3]) if row[3] is not None else None,
            project_cap_seconds=row[4],
        ).validate(),
        int(row[5]),
    )


def _materialize_cache(
    project_id: uuid.UUID,
    payload: CacheMaterializationRequest,
    *,
    purpose: str,
    capability: str | None = None,
    recipe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if _contains_sensitive_key(payload.parameters) or (recipe is not None and _contains_sensitive_key(recipe)):
        raise HTTPException(status_code=422, detail="Aucun secret ne peut être matérialisé ou mis en cache")
    try:
        cache_key, descriptor = canonical_cache_key(
            source_id=payload.source_id,
            api_version=payload.api_version,
            endpoint_id=payload.endpoint_id,
            parameters=payload.parameters,
            output_format=payload.output_format,
            connector_version=payload.connector_version,
            transformation_version=payload.transformation_version,
        )
        data, media_type, suffix = serialize_public_content(payload.content, payload.output_format)
        delay_seconds = validation_delay_seconds(
            source_frequency_seconds=payload.source_frequency_seconds,
            source_duration_seconds=payload.source_duration_seconds,
        )
    except (ValueError, StorageValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    next_validation_at = now + timedelta(seconds=delay_seconds)
    cache_root = Path(os.environ.get("HDP_V6_CACHE_ROOT", os.path.join(os.environ.get("DATA_DIR", "/app/data"), "v6-cache")))
    with db(autocommit=False) as connection:
        _, maximum_bytes = _project_cache_policy(connection, project_id)
        if len(data) > maximum_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Artefact de {len(data)} octets supérieur à la limite projet de {maximum_bytes} octets",
            )
        if capability is None:
            endpoint_uuid, contract_sha = _assert_project_endpoint_available(
                connection, project_id, payload.source_id, payload.api_version, payload.endpoint_id
            )
        else:
            capability_row = connection.execute(
                """SELECT support_level,state,endpoint_ids,equivalent_recipe
                   FROM connector_capabilities WHERE source_id=%s AND capability=%s""",
                (payload.source_id, capability),
            ).fetchone()
            if (
                not capability_row
                or capability_row[0] != "hdp_equivalent"
                or capability_row[1] not in {"tests_validated", "active_global"}
            ):
                raise HTTPException(status_code=409, detail="L'équivalent HDP demandé n'est pas activable")
            registered_recipe = capability_row[3]
            if canonical_json(registered_recipe) != canonical_json(recipe):
                raise HTTPException(status_code=409, detail="La recette ne correspond pas à la version enregistrée")
            endpoint_contracts: list[str] = []
            endpoint_uuid = None
            for dependency_endpoint_id in capability_row[2] or []:
                dependency_uuid, dependency_sha = _assert_project_endpoint_available(
                    connection,
                    project_id,
                    payload.source_id,
                    payload.api_version,
                    str(dependency_endpoint_id),
                )
                endpoint_uuid = endpoint_uuid or dependency_uuid
                endpoint_contracts.append(dependency_sha)
            contract_sha = _json_hash({"capability": capability, "contracts": endpoint_contracts, "recipe": recipe})
        connection.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (cache_key,))
        current = connection.execute(
            """SELECT id,content_sha256,storage_path
               FROM cache_entries WHERE cache_key=%s AND state<>'superseded' FOR UPDATE""",
            (cache_key,),
        ).fetchone()
        try:
            storage_path, content_sha256, file_created = publish_atomically(cache_root, cache_key, data, suffix)
        except (OSError, StorageValidationError) as exc:
            raise HTTPException(status_code=500, detail=f"Publication atomique du cache impossible: {exc}") from exc
        idempotent = bool(current and str(current[1]) == content_sha256)
        if idempotent:
            cache_entry_id = current[0]
            connection.execute(
                """UPDATE cache_entries SET state='fresh',http_etag=%s,http_last_modified=%s,
                          fetched_at=%s,next_validation_at=%s,validation_requested_at=NULL
                   WHERE id=%s""",
                (payload.http_etag, payload.http_last_modified, now, next_validation_at, cache_entry_id),
            )
        else:
            supersedes = current[0] if current else None
            if current:
                connection.execute("UPDATE cache_entries SET state='superseded' WHERE id=%s", (current[0],))
            cache_entry_id = uuid.uuid4()
            connection.execute(
                """INSERT INTO cache_entries
                   (id,cache_key,source_id,api_version,endpoint_id,canonical_parameters,
                    output_format,connector_version,transformation_version,storage_path,
                    content_sha256,size_bytes,http_etag,http_last_modified,fetched_at,
                    next_validation_at,state,supersedes_cache_entry_id,created_at,media_type)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'fresh',%s,%s,%s)""",
                (
                    cache_entry_id, cache_key, payload.source_id, payload.api_version,
                    payload.endpoint_id, Jsonb(descriptor["parameters"]), payload.output_format,
                    payload.connector_version, payload.transformation_version, str(storage_path),
                    content_sha256, len(data), payload.http_etag, payload.http_last_modified,
                    now, next_validation_at, supersedes, now, media_type,
                ),
            )
        connection.execute(
            """INSERT INTO project_cache_references
               (project_id,cache_entry_id,purpose,referenced_at) VALUES (%s,%s,%s,%s)
               ON CONFLICT (project_id,cache_entry_id,purpose) DO UPDATE SET
                 referenced_at=EXCLUDED.referenced_at""",
            (project_id, cache_entry_id, purpose, now),
        )
        if capability is not None:
            recipe_sha256 = _json_hash(recipe)
            connection.execute(
                """INSERT INTO equivalent_materializations
                   (id,project_id,source_id,capability,cache_entry_id,recipe,recipe_sha256,
                    materialized_at,materialized_by)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    uuid.uuid4(), project_id, payload.source_id, capability, cache_entry_id,
                    Jsonb(recipe), recipe_sha256, now, payload.actor,
                ),
            )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project',%s,'cache_entry',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id,
                "cache.equivalent_materialized" if capability else "cache.materialized",
                str(cache_entry_id),
                "Équivalent HDP matérialisé" if capability else "Artefact public mis en cache",
                Jsonb(
                    {
                        "source_id": payload.source_id,
                        "endpoint_id": payload.endpoint_id,
                        "capability": capability,
                        "cache_key": cache_key,
                        "content_sha256": content_sha256,
                        "contract_sha256": contract_sha,
                        "file_created": file_created,
                    }
                ),
                payload.actor, now,
            ),
        )
    return {
        "project_id": str(project_id),
        "cache_entry_id": str(cache_entry_id),
        "cache_key": cache_key,
        "content_sha256": content_sha256,
        "size_bytes": len(data),
        "media_type": media_type,
        "next_validation_at": next_validation_at,
        "idempotent": idempotent,
        "shared_existing_artifact": not file_created,
        "data_classification": "public",
    }


@router.post("/projects/{project_id}/cache/materialize", status_code=201)
def materialize_project_cache(project_id: uuid.UUID, payload: CacheMaterializationRequest) -> dict[str, Any]:
    ensure_project(project_id)
    return _materialize_cache(project_id, payload, purpose="acquisition")


@router.post("/projects/{project_id}/sources/{source_id}/equivalents/{capability}/materialize", status_code=201)
def materialize_equivalent(
    project_id: uuid.UUID,
    source_id: str,
    capability: str,
    payload: EquivalentMaterializationRequest,
) -> dict[str, Any]:
    ensure_project(project_id)
    if capability not in CAPABILITIES or payload.source_id != source_id:
        raise HTTPException(status_code=422, detail="Source ou capacité incohérente")
    return _materialize_cache(
        project_id,
        payload,
        purpose=f"equivalent:{capability}",
        capability=capability,
        recipe=payload.recipe,
    )


@router.post("/projects/{project_id}/cache/{cache_entry_id}/revalidate")
def revalidate_project_cache(
    project_id: uuid.UUID,
    cache_entry_id: uuid.UUID,
    payload: CacheRevalidationRequest,
) -> dict[str, Any]:
    ensure_project(project_id)
    if _contains_sensitive_key(payload.details):
        raise HTTPException(status_code=422, detail="Les détails de revalidation ne doivent contenir aucun secret")
    now = datetime.now(UTC)
    with db(autocommit=False) as connection:
        row = connection.execute(
            """SELECT c.id,c.state,c.fetched_at,c.next_validation_at,c.http_etag,
                      c.http_last_modified,c.source_id,c.endpoint_id
               FROM cache_entries c JOIN project_cache_references r ON r.cache_entry_id=c.id
               WHERE c.id=%s AND r.project_id=%s FOR UPDATE OF c""",
            (cache_entry_id, project_id),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Référence de cache introuvable dans ce projet")
        policy, _ = _project_cache_policy(connection, project_id)
        if payload.outcome == "not_modified":
            try:
                delay = validation_delay_seconds(
                    source_frequency_seconds=payload.source_frequency_seconds,
                    source_duration_seconds=payload.source_duration_seconds,
                )
            except StorageValidationError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            next_validation_at = now + timedelta(seconds=delay)
            state, decision = "fresh", "use_fresh"
            connection.execute(
                """UPDATE cache_entries SET state='fresh',fetched_at=%s,next_validation_at=%s,
                          http_etag=COALESCE(%s,http_etag),
                          http_last_modified=COALESCE(%s,http_last_modified),
                          validation_requested_at=NULL WHERE id=%s""",
                (now, next_validation_at, payload.response_etag, payload.response_last_modified, cache_entry_id),
            )
        elif payload.outcome == "failed":
            cache_result = cache_decision(
                cached_at=row[2], next_validation_at=row[3], now=now, source_failed=True,
                policy=policy, source_frequency_seconds=payload.source_frequency_seconds,
            )
            decision = cache_result["decision"]
            state = "stale" if decision in {"use_stale", "pending_approval"} else "failed"
            next_validation_at = row[3]
            connection.execute(
                "UPDATE cache_entries SET state=%s,validation_requested_at=NULL WHERE id=%s",
                (state, cache_entry_id),
            )
        else:
            state, decision, next_validation_at = "stale", "refresh_required", row[3]
            connection.execute(
                "UPDATE cache_entries SET state='stale',validation_requested_at=%s WHERE id=%s",
                (now, cache_entry_id),
            )
        connection.execute(
            """INSERT INTO cache_revalidations
               (id,project_id,cache_entry_id,outcome,request_etag,request_last_modified,
                response_etag,response_last_modified,details,actor,occurred_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, cache_entry_id, payload.outcome, row[4], row[5],
                payload.response_etag, payload.response_last_modified, Jsonb(payload.details),
                payload.actor, now,
            ),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','cache.revalidated','cache_entry',%s,%s,%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, str(cache_entry_id),
                "failed" if payload.outcome == "failed" else "completed",
                f"Cache : revalidation {payload.outcome}",
                Jsonb({"decision": decision, "state": state, "source_id": row[6], "endpoint_id": row[7]}),
                payload.actor, now,
            ),
        )
    return {
        "project_id": str(project_id),
        "cache_entry_id": str(cache_entry_id),
        "outcome": payload.outcome,
        "state": state,
        "decision": decision,
        "next_validation_at": next_validation_at,
        "requires_materialization": payload.outcome == "modified",
    }


@router.get("/projects/{project_id}/cache")
def list_project_cache(project_id: uuid.UUID, limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT c.id,c.cache_key,c.source_id,c.api_version,c.endpoint_id,c.output_format,
                      c.connector_version,c.transformation_version,c.content_sha256,c.size_bytes,
                      c.http_etag,c.http_last_modified,c.fetched_at,c.next_validation_at,c.state,
                      c.media_type,r.purpose,r.referenced_at
               FROM project_cache_references r JOIN cache_entries c ON c.id=r.cache_entry_id
               WHERE r.project_id=%s ORDER BY r.referenced_at DESC LIMIT %s""",
            (project_id, limit),
        ).fetchall()
    keys = (
        "id", "cache_key", "source_id", "api_version", "endpoint_id", "output_format",
        "connector_version", "transformation_version", "content_sha256", "size_bytes",
        "http_etag", "http_last_modified", "fetched_at", "next_validation_at", "state",
        "media_type", "purpose", "referenced_at",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


@router.get("/projects/{project_id}/data-policy")
def get_project_policy(project_id: uuid.UUID) -> dict[str, Any]:
    ensure_project(project_id)
    with db() as connection:
        row = connection.execute(
            """SELECT stale_policy,max_stale_mode,fixed_duration_seconds,frequency_multiple,
                      project_cap_seconds,automatic_request_limit,automatic_download_bytes,
                      automatic_duration_seconds,updated_at
               FROM project_data_policies WHERE project_id=%s""",
            (project_id,),
        ).fetchone()
    if not row:
        return {
            "project_id": str(project_id),
            "stale_policy": "stale_if_error",
            "max_stale_mode": "manual",
            "arbitration_required": True,
            "automatic_request_limit": 100,
            "automatic_download_bytes": 104_857_600,
            "automatic_duration_seconds": 300,
        }
    keys = (
        "stale_policy",
        "max_stale_mode",
        "fixed_duration_seconds",
        "frequency_multiple",
        "project_cap_seconds",
        "automatic_request_limit",
        "automatic_download_bytes",
        "automatic_duration_seconds",
        "updated_at",
    )
    return {"project_id": str(project_id), **dict(zip(keys, row, strict=True)), "arbitration_required": row[1] == "manual"}


@router.put("/projects/{project_id}/data-policy")
def update_project_policy(project_id: uuid.UUID, payload: ProjectPolicyUpdate) -> dict[str, Any]:
    ensure_project(project_id)
    try:
        FreshnessPolicy(
            project_policy=payload.stale_policy,
            max_stale_mode=payload.max_stale_mode,
            fixed_duration_seconds=payload.fixed_duration_seconds,
            frequency_multiple=payload.frequency_multiple,
            project_cap_seconds=payload.project_cap_seconds,
        ).validate()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now = datetime.now(UTC)
    with db() as connection:
        connection.execute(
            """INSERT INTO project_data_policies
               (project_id,stale_policy,max_stale_mode,fixed_duration_seconds,frequency_multiple,
                project_cap_seconds,automatic_request_limit,automatic_download_bytes,
                automatic_duration_seconds,updated_at)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (project_id) DO UPDATE SET
                 stale_policy=EXCLUDED.stale_policy,max_stale_mode=EXCLUDED.max_stale_mode,
                 fixed_duration_seconds=EXCLUDED.fixed_duration_seconds,
                 frequency_multiple=EXCLUDED.frequency_multiple,
                 project_cap_seconds=EXCLUDED.project_cap_seconds,
                 automatic_request_limit=EXCLUDED.automatic_request_limit,
                 automatic_download_bytes=EXCLUDED.automatic_download_bytes,
                 automatic_duration_seconds=EXCLUDED.automatic_duration_seconds,
                 updated_at=EXCLUDED.updated_at""",
            (
                project_id,
                payload.stale_policy,
                payload.max_stale_mode,
                payload.fixed_duration_seconds,
                payload.frequency_multiple,
                payload.project_cap_seconds,
                payload.automatic_request_limit,
                payload.automatic_download_bytes,
                payload.automatic_duration_seconds,
                now,
            ),
        )
    return {"project_id": str(project_id), **payload.model_dump(), "updated_at": now}


def _validate_catalog_record(record: CatalogRecordInput) -> None:
    if any(not isinstance(path, str) or not path or len(path) > 500 for path in record.mapped_paths):
        raise HTTPException(status_code=422, detail="Un chemin de métadonnée mappé est invalide")
    allowed_confidence = {"documented", "observed", "inferred", "unavailable"}
    for target, value in record.normalized_metadata.items():
        confidence = record.confidence.get(target)
        lineage = record.lineage.get(target)
        if not isinstance(confidence, dict) or confidence.get("status") not in allowed_confidence:
            raise HTTPException(
                status_code=422,
                detail=f"Le champ normalisé {target} doit déclarer sa provenance de confiance",
            )
        score = confidence.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            raise HTTPException(status_code=422, detail=f"Score de confiance invalide pour {target}")
        if confidence["status"] == "unavailable":
            if value is not None:
                raise HTTPException(
                    status_code=422,
                    detail=f"Une métadonnée indisponible doit être explicitement nulle: {target}",
                )
            continue
        if not isinstance(lineage, dict) or not isinstance(lineage.get("recipe"), dict):
            raise HTTPException(status_code=422, detail=f"Recette de lignée absente pour {target}")
        source_paths = lineage.get("source_paths")
        if not isinstance(source_paths, list) or not source_paths or any(
            not isinstance(path, str) or not path or len(path) > 500 for path in source_paths
        ):
            raise HTTPException(status_code=422, detail=f"Chemins sources absents pour {target}")
    unknown_lineage = set(record.lineage) - set(record.normalized_metadata)
    if unknown_lineage:
        raise HTTPException(status_code=422, detail=f"Lignée sans champ normalisé: {sorted(unknown_lineage)}")


@router.post("/projects/{project_id}/catalog/import", status_code=201)
def import_catalog_batch(project_id: uuid.UUID, payload: CatalogBatchInput) -> dict[str, Any]:
    ensure_project(project_id)
    if _contains_sensitive_key(payload.acquisition_parameters):
        raise HTTPException(status_code=422, detail="Les paramètres d'acquisition ne doivent contenir aucun secret")
    external_ids = [record.external_id for record in payload.records]
    if len(set(external_ids)) != len(external_ids):
        raise HTTPException(status_code=422, detail="Les identifiants externes du lot doivent être uniques")
    for record in payload.records:
        _validate_catalog_record(record)
    now, run_id = datetime.now(UTC), uuid.uuid4()
    record_ids: list[str] = []
    with db(autocommit=False) as connection:
        endpoint_uuid, contract_sha = _assert_project_endpoint_available(
            connection,
            project_id,
            payload.source_id,
            payload.api_version,
            payload.endpoint_id,
        )
        connection.execute(
            """INSERT INTO catalog_ingestion_runs
               (id,project_id,source_id,api_version,endpoint_id,connector_version,
                transformation_version,acquisition_parameters,record_count,status,
                started_at,actor)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'running',%s,%s)""",
            (
                run_id, project_id, payload.source_id, payload.api_version, payload.endpoint_id,
                payload.connector_version, payload.transformation_version,
                Jsonb(payload.acquisition_parameters), len(payload.records), now, payload.actor,
            ),
        )
        for record in payload.records:
            raw_content = record.raw_metadata
            raw_sha256 = _json_hash(raw_content)
            snapshot = connection.execute(
                """INSERT INTO raw_metadata_snapshots
                   (id,source_id,api_version,endpoint_id,external_id,content,content_sha256,
                    http_etag,http_last_modified,observed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,NULL,NULL,%s)
                   ON CONFLICT (source_id,api_version,endpoint_id,content_sha256)
                   DO NOTHING
                   RETURNING id""",
                (
                    uuid.uuid4(), payload.source_id, payload.api_version, payload.endpoint_id,
                    record.external_id, Jsonb(raw_content), raw_sha256, now,
                ),
            ).fetchone()
            if not snapshot:
                snapshot = connection.execute(
                    """SELECT id FROM raw_metadata_snapshots
                       WHERE source_id=%s AND api_version=%s AND endpoint_id=%s AND content_sha256=%s""",
                    (payload.source_id, payload.api_version, payload.endpoint_id, raw_sha256),
                ).fetchone()
            if not snapshot:
                raise HTTPException(status_code=500, detail="Instantané brut non enregistré")
            catalog_record_id = uuid.uuid4()
            unmapped = preserve_unmapped_fields(raw_content, set(record.mapped_paths))
            connection.execute(
                """INSERT INTO catalog_records
                   (id,source_id,api_version,endpoint_id,external_id,record_type,title,
                    normalized_metadata,unmapped_fields,raw_snapshot_id,connector_version,
                    transformation_version,confidence,observed_at,valid_until)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    catalog_record_id, payload.source_id, payload.api_version, payload.endpoint_id,
                    record.external_id, record.record_type, record.title, Jsonb(record.normalized_metadata),
                    Jsonb(unmapped), snapshot[0], payload.connector_version,
                    payload.transformation_version, Jsonb(record.confidence), now, record.valid_until,
                ),
            )
            for target_path, lineage in record.lineage.items():
                connection.execute(
                    """INSERT INTO catalog_field_lineage
                       (id,catalog_record_id,target_path,source_paths,recipe,connector_version,
                        transformation_version,confidence)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        uuid.uuid4(), catalog_record_id, target_path,
                        Jsonb(lineage["source_paths"]), Jsonb(lineage["recipe"]),
                        payload.connector_version, payload.transformation_version,
                        Jsonb(record.confidence[target_path]),
                    ),
                )
            connection.execute(
                """INSERT INTO project_catalog_references
                   (project_id,catalog_record_id,ingestion_run_id,referenced_at)
                   VALUES (%s,%s,%s,%s)""",
                (project_id, catalog_record_id, run_id, now),
            )
            record_ids.append(str(catalog_record_id))
        connection.execute(
            "UPDATE catalog_ingestion_runs SET status='completed',finished_at=%s WHERE id=%s",
            (now, run_id),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','catalog.ingested','catalog_ingestion_run',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, str(run_id),
                f"{len(record_ids)} enregistrement(s) ajouté(s) au catalogue",
                Jsonb(
                    {
                        "source_id": payload.source_id,
                        "endpoint_id": payload.endpoint_id,
                        "endpoint_uuid": str(endpoint_uuid),
                        "contract_sha256": contract_sha,
                        "acquisition_parameters_sha256": _json_hash(payload.acquisition_parameters),
                    }
                ),
                payload.actor, now,
            ),
        )
    return {
        "project_id": str(project_id),
        "ingestion_run_id": str(run_id),
        "record_count": len(record_ids),
        "record_ids": record_ids,
        "raw_metadata_preserved": True,
    }


@router.put("/projects/{project_id}/sources/{source_id}/catalog-schedule")
def update_catalog_schedule(
    project_id: uuid.UUID,
    source_id: str,
    payload: CatalogScheduleUpdate,
) -> dict[str, Any]:
    ensure_project(project_id)
    if _contains_sensitive_key(payload.acquisition_parameters):
        raise HTTPException(status_code=422, detail="Aucun secret ne peut être enregistré dans la planification")
    now = datetime.now(UTC)
    next_run_at = now if payload.enabled else now + timedelta(minutes=payload.interval_minutes)
    with db(autocommit=False) as connection:
        _assert_project_endpoint_available(
            connection, project_id, source_id, payload.api_version, payload.endpoint_id
        )
        connection.execute(
            """INSERT INTO catalog_update_schedules
               (project_id,source_id,endpoint_id,api_version,interval_minutes,enabled,
                acquisition_parameters,next_run_at,updated_at,updated_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (project_id,source_id,endpoint_id) DO UPDATE SET
                 api_version=EXCLUDED.api_version,interval_minutes=EXCLUDED.interval_minutes,
                 enabled=EXCLUDED.enabled,acquisition_parameters=EXCLUDED.acquisition_parameters,
                 next_run_at=EXCLUDED.next_run_at,updated_at=EXCLUDED.updated_at,
                 updated_by=EXCLUDED.updated_by""",
            (
                project_id, source_id, payload.endpoint_id, payload.api_version,
                payload.interval_minutes, payload.enabled, Jsonb(payload.acquisition_parameters),
                next_run_at, now, payload.actor,
            ),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','catalog.schedule_updated','catalog_schedule',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, f"{source_id}:{payload.endpoint_id}",
                f"Planification du catalogue {source_id} {'activée' if payload.enabled else 'suspendue'}",
                Jsonb({"interval_minutes": payload.interval_minutes, "next_run_at": next_run_at}),
                payload.actor, now,
            ),
        )
    return {
        "project_id": str(project_id),
        "source_id": source_id,
        "endpoint_id": payload.endpoint_id,
        "enabled": payload.enabled,
        "next_run_at": next_run_at,
    }


@router.get("/projects/{project_id}/catalog-schedules")
def list_catalog_schedules(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT source_id,endpoint_id,api_version,interval_minutes,enabled,
                      acquisition_parameters,next_run_at,last_run_at,last_status,last_error,
                      updated_at,updated_by
               FROM catalog_update_schedules WHERE project_id=%s ORDER BY source_id,endpoint_id""",
            (project_id,),
        ).fetchall()
    keys = (
        "source_id", "endpoint_id", "api_version", "interval_minutes", "enabled",
        "acquisition_parameters", "next_run_at", "last_run_at", "last_status", "last_error",
        "updated_at", "updated_by",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


def _rss_source_definition(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": f"custom:{row[1]}:v{row[2]}",
        "feed_source_id": str(row[0]),
        "source_key": row[1],
        "version_number": row[2],
        "name": row[3],
        "organization": row[4],
        "region": row[5],
        "themes": row[6],
        "languages": row[7],
        "base_url": row[8],
        "portal_url": row[9],
        "evidence_url": row[10],
        "protocol": row[11],
        "license": row[12],
        "declared_frequency": row[13],
        "allowed_hosts": row[14],
        "state": row[15],
        "created_at": row[16],
        "created_by": row[17],
        "decided_at": row[18],
        "decided_by": row[19],
        "supports_query": False,
        "registry_version": RSS_REGISTRY_VERSION,
    }


def _rss_source_row(connection: Any, feed_source_id: uuid.UUID, *, lock: bool = False) -> tuple[Any, ...] | None:
    return connection.execute(
        """SELECT id,source_key,version_number,name,organization,region,themes,languages,
                  feed_url,portal_url,evidence_url,protocol,license,declared_frequency,
                  allowed_hosts,state,created_at,created_by,decided_at,decided_by
           FROM rss_feed_sources WHERE id=%s""" + (" FOR UPDATE" if lock else ""),
        (feed_source_id,),
    ).fetchone()


@router.get("/rss/inventory-scope")
def rss_inventory_scope() -> dict[str, Any]:
    return {
        "registry_version": RSS_REGISTRY_VERSION,
        "reference_date": "2026-08-21",
        "scope": RSS_REGISTRY_SCOPE,
        "claim": "exhaustive_within_declared_scope",
        "portals_without_verified_feed_are_not_active": True,
    }


@router.post("/rss/candidates", status_code=201)
def create_rss_candidate(payload: RssFeedCandidateCreate) -> dict[str, Any]:
    if any(not item.strip() or len(item) > 120 for item in [*payload.themes, *payload.languages]):
        raise HTTPException(status_code=422, detail="Thème ou langue RSS invalide")
    proposed = {
        "id": payload.source_key,
        "name": payload.name,
        "organization": payload.organization,
        "base_url": payload.feed_url,
        "portal_url": payload.portal_url,
        "region": payload.region,
        "themes": payload.themes,
        "languages": payload.languages,
        "license": payload.license,
        "declared_frequency": payload.declared_frequency,
        "evidence_url": payload.evidence_url,
        "verified_at": datetime.now(UTC).date().isoformat(),
        "state": "draft",
    }
    try:
        definition = validate_feed_definition(proposed)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    now, feed_source_id = datetime.now(UTC), uuid.uuid4()
    with db(autocommit=False) as connection:
        connection.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,0))", (payload.source_key,))
        row = connection.execute(
            "SELECT COALESCE(MAX(version_number),0)+1 FROM rss_feed_sources WHERE source_key=%s",
            (payload.source_key,),
        ).fetchone()
        version_number = int(row[0]) if row else 1
        connection.execute(
            """INSERT INTO rss_feed_sources
               (id,source_key,version_number,name,organization,region,themes,languages,
                feed_url,portal_url,evidence_url,protocol,license,declared_frequency,
                allowed_hosts,state,created_at,created_by)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft',%s,%s)""",
            (
                feed_source_id, payload.source_key, version_number, payload.name,
                payload.organization, payload.region, Jsonb(payload.themes), Jsonb(payload.languages),
                payload.feed_url, payload.portal_url, payload.evidence_url, definition["protocol"],
                payload.license, payload.declared_frequency, Jsonb(definition["allowed_hosts"]),
                now, payload.actor,
            ),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,'global','rss.candidate_created','rss_feed_source',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), str(feed_source_id), f"Candidat RSS {payload.name} créé",
                Jsonb({"source_key": payload.source_key, "version_number": version_number}),
                payload.actor, now,
            ),
        )
    return {
        "id": str(feed_source_id),
        "source_key": payload.source_key,
        "version_number": version_number,
        "state": "draft",
        "next_step": "preview_and_parser_validation",
    }


@router.get("/rss/candidates")
def list_rss_candidates(state: str | None = None) -> list[dict[str, Any]]:
    if state is not None and state not in {"draft", "validated", "approved", "suspended", "rejected"}:
        raise HTTPException(status_code=422, detail="État RSS invalide")
    with db() as connection:
        rows = connection.execute(
            """SELECT id,source_key,version_number,name,organization,region,themes,languages,
                      feed_url,portal_url,evidence_url,protocol,license,declared_frequency,
                      allowed_hosts,state,created_at,created_by,decided_at,decided_by
               FROM rss_feed_sources WHERE (%s IS NULL OR state=%s)
               ORDER BY created_at DESC""",
            (state, state),
        ).fetchall()
    return [_rss_source_definition(row) for row in rows]


@router.post("/rss/candidates/{feed_source_id}/preview")
async def preview_rss_candidate(feed_source_id: uuid.UUID, actor: str = "local-operator") -> dict[str, Any]:
    with db() as connection:
        row = _rss_source_row(connection, feed_source_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidat RSS introuvable")
    definition = _rss_source_definition(row)
    now = datetime.now(UTC)
    try:
        with tempfile.TemporaryDirectory(prefix="hdp-rss-preview-") as directory:
            result = await asyncio.to_thread(
                download_public_file,
                definition["base_url"],
                Path(directory),
                max_bytes=MAX_RSS_BYTES,
                user_agent="HDP/6.0.0-dev RSS validation",
                max_redirects=3,
                allowed_hosts=frozenset(definition["allowed_hosts"]),
            )
            content = result.temporary_path.read_bytes()
            result.temporary_path.unlink(missing_ok=True)
        items = parse_rss(content)
        schema_sha256 = rss_schema_signature(content)
        with db(autocommit=False) as connection:
            locked = _rss_source_row(connection, feed_source_id, lock=True)
            if not locked:
                raise HTTPException(status_code=404, detail="Candidat RSS introuvable")
            previous = connection.execute(
                """SELECT c.schema_sha256 FROM rss_feed_checks c
                   JOIN rss_feed_sources s ON s.id=c.feed_source_id
                   WHERE s.source_key=%s AND c.status='passed'
                   ORDER BY c.checked_at DESC LIMIT 1""",
                (locked[1],),
            ).fetchone()
            schema_changed = bool(previous and previous[0] and str(previous[0]) != schema_sha256)
            next_state = "validated" if locked[15] == "draft" or (locked[15] == "approved" and schema_changed) else locked[15]
            connection.execute("UPDATE rss_feed_sources SET state=%s WHERE id=%s", (next_state, feed_source_id))
            connection.execute(
                """INSERT INTO rss_feed_checks
                   (id,feed_source_id,status,requested_url,final_url,http_etag,http_last_modified,
                    content_sha256,schema_sha256,schema_changed,item_count,checked_at,checked_by)
                   VALUES (%s,%s,'passed',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    uuid.uuid4(), feed_source_id, definition["base_url"], result.final_url,
                    result.headers.get("etag"), result.headers.get("last-modified"), result.sha256,
                    schema_sha256, schema_changed, len(items), now, actor,
                ),
            )
            connection.execute(
                """INSERT INTO application_timeline
                   (id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
                   VALUES (%s,'global','rss.candidate_checked','rss_feed_source',%s,'completed',%s,%s,%s,%s)""",
                (
                    uuid.uuid4(), str(feed_source_id), f"Flux RSS {locked[3]} validé par le parseur",
                    Jsonb({"item_count": len(items), "schema_changed": schema_changed, "content_sha256": result.sha256}),
                    actor, now,
                ),
            )
        return {
            "id": str(feed_source_id),
            "state": next_state,
            "item_count": len(items),
            "items": items[:10],
            "content_sha256": result.sha256,
            "schema_sha256": schema_sha256,
            "schema_changed": schema_changed,
            "final_url": result.final_url,
        }
    except HTTPException:
        raise
    except Exception as exc:
        with db() as connection:
            connection.execute(
                """INSERT INTO rss_feed_checks
                   (id,feed_source_id,status,requested_url,error,checked_at,checked_by)
                   VALUES (%s,%s,'failed',%s,%s,%s,%s)""",
                (uuid.uuid4(), feed_source_id, definition["base_url"], str(exc)[:2000], now, actor),
            )
        raise HTTPException(status_code=502, detail=f"Validation du flux impossible: {str(exc)[:500]}") from exc


@router.post("/rss/candidates/{feed_source_id}/decision")
def decide_rss_candidate(feed_source_id: uuid.UUID, payload: RssFeedDecision) -> dict[str, Any]:
    now = datetime.now(UTC)
    target = {"approve": "approved", "suspend": "suspended", "reject": "rejected"}[payload.decision]
    with db(autocommit=False) as connection:
        row = _rss_source_row(connection, feed_source_id, lock=True)
        if not row:
            raise HTTPException(status_code=404, detail="Candidat RSS introuvable")
        if payload.decision == "approve":
            check = connection.execute(
                """SELECT status,schema_changed FROM rss_feed_checks
                   WHERE feed_source_id=%s ORDER BY checked_at DESC LIMIT 1""",
                (feed_source_id,),
            ).fetchone()
            if row[15] not in {"validated", "suspended"} or not check or check[0] != "passed":
                raise HTTPException(status_code=409, detail="Un contrôle de flux réussi est requis avant approbation")
        if payload.decision == "suspend" and row[15] not in {"approved", "validated"}:
            raise HTTPException(status_code=409, detail="Ce flux ne peut pas être suspendu dans son état actuel")
        connection.execute(
            """UPDATE rss_feed_sources SET state=%s,decided_at=%s,decided_by=%s WHERE id=%s""",
            (target, now, payload.actor, feed_source_id),
        )
        if target in {"suspended", "rejected"}:
            connection.execute(
                """UPDATE rss_subscriptions SET enabled=FALSE,last_status='source_suspended',
                          last_error=%s,updated_at=%s WHERE feed_source_id=%s AND archived_at IS NULL""",
                (payload.reason, now, feed_source_id),
            )
        connection.execute(
            """INSERT INTO application_timeline
               (id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,'global','rss.source_decided','rss_feed_source',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), str(feed_source_id), f"Flux RSS {row[3]} : {target}",
                Jsonb({"previous_state": row[15], "new_state": target, "reason": payload.reason}),
                payload.actor, now,
            ),
        )
    return {"id": str(feed_source_id), "previous_state": row[15], "state": target}


@router.post("/projects/{project_id}/rss/sources/{feed_source_id}/subscriptions", status_code=201)
def subscribe_approved_rss_source(
    project_id: uuid.UUID,
    feed_source_id: uuid.UUID,
    payload: RssApprovedSubscriptionCreate,
) -> dict[str, Any]:
    ensure_project(project_id)
    now, subscription_id = datetime.now(UTC), uuid.uuid4()
    with db(autocommit=False) as connection:
        row = _rss_source_row(connection, feed_source_id, lock=True)
        if not row or row[15] != "approved":
            raise HTTPException(status_code=409, detail="Le flux doit être approuvé avant abonnement")
        definition = _rss_source_definition(row)
        connection.execute(
            """INSERT INTO rss_subscriptions
               (id,project_id,registry_id,name,query,language,interval_minutes,enabled,
                next_fetch_at,created_at,updated_at,feed_definition,feed_source_id)
               VALUES (%s,%s,%s,%s,'','en',%s,%s,%s,%s,%s,%s,%s)""",
            (
                subscription_id, project_id, definition["id"], payload.name,
                payload.interval_minutes, payload.enabled,
                now if payload.enabled else now + timedelta(minutes=payload.interval_minutes),
                now, now, Jsonb(definition), feed_source_id,
            ),
        )
        connection.execute(
            """INSERT INTO application_timeline
               (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
               VALUES (%s,%s,'project','rss.subscription_created','rss_subscription',%s,'completed',%s,%s,%s,%s)""",
            (
                uuid.uuid4(), project_id, str(subscription_id),
                f"Abonnement au flux {row[3]} créé",
                Jsonb({"feed_source_id": str(feed_source_id), "interval_minutes": payload.interval_minutes}),
                payload.actor, now,
            ),
        )
    return {
        "id": str(subscription_id),
        "project_id": str(project_id),
        "feed_source_id": str(feed_source_id),
        "enabled": payload.enabled,
        "next_fetch_at": now if payload.enabled else now + timedelta(minutes=payload.interval_minutes),
    }


def _export_backup_query(
    connection: Any,
    directory: Path,
    name: str,
    query: Any,
    parameters: tuple[Any, ...],
    files: list[Path],
    row_counts: dict[str, int],
) -> None:
    destination = directory / f"{name}.jsonl"
    row_counts[name] = export_query_as_jsonl(connection, destination, query, parameters)
    files.append(destination)


@router.post("/backups", status_code=201)
def create_database_backup(payload: DatabaseBackupCreate) -> dict[str, Any]:
    if payload.scope == "global" and (payload.project_id is not None or payload.signal_ids):
        raise HTTPException(status_code=422, detail="Une sauvegarde globale n'accepte aucun sélecteur projet ou signal")
    if payload.scope in {"project", "signals"} and payload.project_id is None:
        raise HTTPException(status_code=422, detail="Le projet est obligatoire pour ce périmètre")
    if payload.scope == "signals" and not payload.signal_ids:
        raise HTTPException(status_code=422, detail="Sélectionnez au moins un signal")
    if payload.project_id is not None:
        ensure_project(payload.project_id)
    backup_uuid, started = uuid.uuid4(), datetime.now(UTC)
    backup_id = f"{payload.scope}-{started:%Y%m%dT%H%M%SZ}-{str(backup_uuid)[:8]}"
    selector = {
        "project_id": str(payload.project_id) if payload.project_id else None,
        "signal_ids": [str(identifier) for identifier in payload.signal_ids],
    }
    with db() as connection:
        connection.execute(
            """INSERT INTO database_backups
               (id,scope,project_id,selector,status,created_at,created_by)
               VALUES (%s,%s,%s,%s,'running',%s,%s)""",
            (backup_uuid, payload.scope, payload.project_id, Jsonb(selector), started, payload.actor),
        )
    root = backup_root(Path(os.environ.get("DATA_DIR", "/app/data")))
    try:
        with tempfile.TemporaryDirectory(prefix=f"hdp-{backup_id}-", dir=root) as temporary_name:
            directory = Path(temporary_name)
            files: list[Path] = []
            row_counts: dict[str, int] = {}
            with db() as connection:
                schema_versions = [str(row[0]) for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                ).fetchall()]
            if payload.scope == "global":
                dump = directory / "postgresql-global.dump"
                create_global_dump(DATABASE_URL, dump)
                files.append(dump)
                row_counts["postgresql-global"] = -1
            elif payload.scope == "project":
                assert payload.project_id is not None
                with db(autocommit=False) as connection:
                    connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    _export_backup_query(
                        connection, directory, "projects", "SELECT * FROM projects WHERE id=%s",
                        (payload.project_id,), files, row_counts,
                    )
                    tables = connection.execute(
                        """SELECT DISTINCT table_name FROM information_schema.columns
                           WHERE table_schema='public' AND column_name='project_id'
                             AND table_name NOT IN ('projects','database_backups')
                           ORDER BY table_name"""
                    ).fetchall()
                    for table_row in tables:
                        table = str(table_row[0])
                        query = psycopg.sql.SQL("SELECT * FROM {} WHERE project_id=%s").format(
                            psycopg.sql.Identifier(table)
                        )
                        _export_backup_query(
                            connection, directory, table, query, (payload.project_id,), files, row_counts
                        )
                    related_queries = {
                        "rss_items": """SELECT i.* FROM rss_items i JOIN rss_subscriptions s ON s.id=i.subscription_id WHERE s.project_id=%s""",
                        "schedule_runs": """SELECT r.* FROM schedule_runs r JOIN schedules s ON s.id=r.schedule_id WHERE s.project_id=%s""",
                        "rule_versions": """SELECT DISTINCT v.* FROM rule_versions v JOIN rule_definitions d ON d.id=v.definition_id LEFT JOIN rule_inheritance i ON i.global_definition_id=d.id WHERE d.project_id=%s OR i.project_id=%s""",
                        "action_executions": """SELECT x.* FROM action_executions x JOIN action_requests r ON r.id=x.request_id WHERE r.project_id=%s""",
                        "endpoint_activation_history": """SELECT DISTINCT h.* FROM endpoint_activation_history h JOIN project_endpoint_activations p ON p.endpoint_id=h.endpoint_id WHERE p.project_id=%s""",
                        "source_endpoints": """SELECT DISTINCT e.* FROM source_endpoints e JOIN project_endpoint_activations p ON p.endpoint_id=e.id WHERE p.project_id=%s""",
                        "source_api_versions": """SELECT DISTINCT v.* FROM source_api_versions v JOIN source_endpoints e ON e.api_version_id=v.id JOIN project_endpoint_activations p ON p.endpoint_id=e.id WHERE p.project_id=%s""",
                        "endpoint_parameters": """SELECT DISTINCT x.* FROM endpoint_parameters x JOIN project_endpoint_activations p ON p.endpoint_id=x.endpoint_id WHERE p.project_id=%s""",
                        "response_fields": """SELECT DISTINCT x.* FROM response_fields x JOIN project_endpoint_activations p ON p.endpoint_id=x.endpoint_id WHERE p.project_id=%s""",
                        "catalog_records": """SELECT DISTINCT c.* FROM catalog_records c JOIN project_catalog_references p ON p.catalog_record_id=c.id WHERE p.project_id=%s""",
                        "raw_metadata_snapshots": """SELECT DISTINCT s.* FROM raw_metadata_snapshots s JOIN catalog_records c ON c.raw_snapshot_id=s.id JOIN project_catalog_references p ON p.catalog_record_id=c.id WHERE p.project_id=%s""",
                        "catalog_field_lineage": """SELECT DISTINCT l.* FROM catalog_field_lineage l JOIN project_catalog_references p ON p.catalog_record_id=l.catalog_record_id WHERE p.project_id=%s""",
                        "cache_entries": """SELECT DISTINCT c.* FROM cache_entries c JOIN project_cache_references p ON p.cache_entry_id=c.id WHERE p.project_id=%s""",
                    }
                    for name, query in related_queries.items():
                        parameters = (payload.project_id, payload.project_id) if name == "rule_versions" else (payload.project_id,)
                        _export_backup_query(
                            connection, directory, f"related-{name}", query, parameters, files, row_counts
                        )
                    connection.commit()
            else:
                assert payload.project_id is not None
                signal_ids = payload.signal_ids
                with db(autocommit=False) as connection:
                    connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                    owned = connection.execute(
                        "SELECT id FROM signal_events WHERE project_id=%s AND id=ANY(%s)",
                        (payload.project_id, signal_ids),
                    ).fetchall()
                    if {row[0] for row in owned} != set(signal_ids):
                        raise HTTPException(status_code=422, detail="Un signal n'appartient pas au projet")
                    signal_queries = {
                        "signal_events": "SELECT * FROM signal_events WHERE project_id=%s AND id=ANY(%s)",
                        "signal_actions": "SELECT * FROM signal_actions WHERE event_id=ANY(%s)",
                        "rule_evaluations": "SELECT * FROM rule_evaluations WHERE project_id=%s AND triggering_event_id=ANY(%s)",
                        "action_requests": """SELECT r.* FROM action_requests r JOIN rule_evaluations e ON e.id=r.evaluation_id WHERE e.project_id=%s AND e.triggering_event_id=ANY(%s)""",
                        "action_executions": """SELECT x.* FROM action_executions x JOIN action_requests r ON r.id=x.request_id JOIN rule_evaluations e ON e.id=r.evaluation_id WHERE e.project_id=%s AND e.triggering_event_id=ANY(%s)""",
                        "rule_definitions": """SELECT DISTINCT d.* FROM rule_definitions d JOIN rule_evaluations e ON e.definition_id=d.id WHERE e.project_id=%s AND e.triggering_event_id=ANY(%s)""",
                        "rule_versions": """SELECT DISTINCT v.* FROM rule_versions v JOIN rule_evaluations e ON e.rule_version_id=v.id WHERE e.project_id=%s AND e.triggering_event_id=ANY(%s)""",
                    }
                    for name, query in signal_queries.items():
                        parameters = (signal_ids,) if name == "signal_actions" else (payload.project_id, signal_ids)
                        _export_backup_query(connection, directory, name, query, parameters, files, row_counts)
                    connection.commit()
            manifest = build_manifest(
                backup_id=backup_id,
                application_version="6.0.0-dev",
                schema_versions=schema_versions,
                scope=payload.scope,
                selector=selector,
                files=files,
                row_counts=row_counts,
                created_at=started,
            )
            bundle = publish_bundle(root, backup_id, files, manifest)
        finished = datetime.now(UTC)
        bundle_sha256 = file_sha256(bundle)
        with db() as connection:
            connection.execute(
                """UPDATE database_backups SET status='completed',storage_path=%s,
                          bundle_sha256=%s,size_bytes=%s,manifest=%s,finished_at=%s WHERE id=%s""",
                (
                    str(bundle), bundle_sha256, bundle.stat().st_size, Jsonb(manifest),
                    finished, backup_uuid,
                ),
            )
            connection.execute(
                """INSERT INTO application_timeline
                   (id,project_id,scope,event_type,object_type,object_id,status,summary,details,actor,occurred_at)
                   VALUES (%s,%s,%s,'backup.completed','database_backup',%s,'completed',%s,%s,%s,%s)""",
                (
                    uuid.uuid4(), payload.project_id,
                    "global" if payload.scope == "global" else "project",
                    str(backup_uuid), f"Sauvegarde {payload.scope} terminée",
                    Jsonb({"bundle_sha256": bundle_sha256, "size_bytes": bundle.stat().st_size}),
                    payload.actor, finished,
                ),
            )
        return {
            "id": str(backup_uuid),
            "backup_id": backup_id,
            "scope": payload.scope,
            "status": "completed",
            "bundle_sha256": bundle_sha256,
            "size_bytes": bundle.stat().st_size,
            "manifest": manifest,
            "download_url": f"/api/v6/backups/{backup_uuid}/download",
            "restore_automatically_authorized": False,
        }
    except HTTPException as exc:
        error = str(exc.detail)
        with db() as connection:
            connection.execute(
                "UPDATE database_backups SET status='failed',error=%s,finished_at=%s WHERE id=%s",
                (error[:2000], datetime.now(UTC), backup_uuid),
            )
        raise
    except (BackupError, OSError, subprocess.SubprocessError, psycopg.Error) as exc:
        with db() as connection:
            connection.execute(
                "UPDATE database_backups SET status='failed',error=%s,finished_at=%s WHERE id=%s",
                (str(exc)[:2000], datetime.now(UTC), backup_uuid),
            )
        raise HTTPException(status_code=500, detail=f"Sauvegarde impossible: {str(exc)[:500]}") from exc


@router.get("/backups")
def list_database_backups(
    project_id: uuid.UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    if project_id is not None:
        ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT id,scope,project_id,selector,status,bundle_sha256,size_bytes,manifest,
                      error,created_at,finished_at,created_by
               FROM database_backups
               WHERE (%s IS NULL OR project_id=%s)
               ORDER BY created_at DESC LIMIT %s""",
            (project_id, project_id, limit),
        ).fetchall()
    keys = (
        "id", "scope", "project_id", "selector", "status", "bundle_sha256", "size_bytes",
        "manifest", "error", "created_at", "finished_at", "created_by",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]


def _completed_backup_file(backup_id: uuid.UUID) -> Path:
    with db() as connection:
        row = connection.execute(
            """SELECT storage_path,bundle_sha256,status FROM database_backups WHERE id=%s""",
            (backup_id,),
        ).fetchone()
    if not row or row[2] != "completed" or not row[0]:
        raise HTTPException(status_code=404, detail="Sauvegarde terminée introuvable")
    root = backup_root(Path(os.environ.get("DATA_DIR", "/app/data")))
    path = Path(row[0]).resolve()
    if root != path.parent or path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=409, detail="Chemin de sauvegarde invalide")
    if file_sha256(path) != row[1]:
        raise HTTPException(status_code=409, detail="L'empreinte de la sauvegarde est incohérente")
    return path


@router.post("/backups/{backup_id}/prevalidate")
def prevalidate_database_backup(backup_id: uuid.UUID) -> dict[str, Any]:
    path = _completed_backup_file(backup_id)
    try:
        report = prevalidate_backup_bundle(path)
    except BackupError as exc:
        raise HTTPException(status_code=409, detail=f"Sauvegarde non restaurable: {exc}") from exc
    return {
        "id": str(backup_id),
        **report,
        "message": "Prévalidation réussie; aucune restauration n'a été exécutée ni autorisée",
    }


@router.get("/backups/{backup_id}/download", response_class=FileResponse)
def download_database_backup(backup_id: uuid.UUID) -> FileResponse:
    path = _completed_backup_file(backup_id)
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.get("/catalog")
def list_catalog(
    source_id: str | None = None,
    record_type: str | None = None,
    query: str = Query(default="", max_length=200),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    with db() as connection:
        rows = connection.execute(
            """SELECT id,source_id,api_version,endpoint_id,external_id,record_type,title,
                      normalized_metadata,unmapped_fields,raw_snapshot_id,connector_version,
                      transformation_version,confidence,observed_at,valid_until
               FROM catalog_records
               WHERE (%s IS NULL OR source_id=%s)
                 AND (%s IS NULL OR record_type=%s)
                 AND (%s='' OR title ILIKE %s OR normalized_metadata::text ILIKE %s)
               ORDER BY observed_at DESC LIMIT %s""",
            (source_id, source_id, record_type, record_type, query, f"%{query}%", f"%{query}%", limit),
        ).fetchall()
    keys = (
        "id",
        "source_id",
        "api_version",
        "endpoint_id",
        "external_id",
        "record_type",
        "title",
        "metadata",
        "unmapped_fields",
        "raw_snapshot_id",
        "connector_version",
        "transformation_version",
        "confidence",
        "observed_at",
        "valid_until",
    )
    return [dict(zip(keys, row, strict=True)) for row in rows]
