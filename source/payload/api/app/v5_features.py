from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import psycopg
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from .script_runtime import prepare_execution_job, script_sha256, validate_execution_request


router = APIRouter(prefix="/api", tags=["HDP V5"])
DATABASE_URL = os.environ["DATABASE_URL"]
SPOOL = Path(os.getenv("EXECUTION_SPOOL_DIR", "/app/execution_spool"))

# Grille fonctionnelle HDP. L'appartenance officielle reste celle publiée par HDX :
# ce vocabulaire sert à rechercher et mesurer la couverture, jamais à la réécrire.
DATA_GRID_DIMENSIONS: tuple[dict[str, Any], ...] = (
    {"id": "geography", "label": "Géographie", "terms": ["boundary", "admin", "place", "location", "roads"]},
    {"id": "population", "label": "Population et société", "terms": ["population", "demographic", "poverty", "settlement"]},
    {"id": "infrastructure", "label": "Infrastructures et services", "terms": ["facility", "school", "hospital", "water", "transport"]},
    {"id": "hazards", "label": "Aléas et crises", "terms": ["hazard", "disaster", "conflict", "flood", "drought"]},
    {"id": "needs_response", "label": "Besoins et réponse", "terms": ["needs", "response", "3w", "funding", "cluster"]},
    {"id": "health_food", "label": "Santé, nutrition et sécurité alimentaire", "terms": ["health", "disease", "nutrition", "food security", "ipc"]},
)
DIMENSION_IDS = {item["id"] for item in DATA_GRID_DIMENSIONS}

SIGNAL_PROMPTS: dict[str, dict[str, Any]] = {
    "classify": {
        "purpose": "Classer un signal par lieu, thème, gravité et confiance.",
        "constraints": [
            "Utiliser uniquement le titre, le résumé et les preuves fournis.",
            "Ne pas transformer une absence de donnée en absence d'événement.",
            "Retourner un JSON strict et citer les URL des preuves.",
            "Employer null et expliciter l'incertitude plutôt que d'inventer.",
        ],
        "output": {"locations": [], "themes": [], "severity": 0.0, "confidence": 0.0, "evidence_urls": []},
    },
    "syndromic_summary": {
        "purpose": "Résumer un groupe de signaux convergents sans produire de diagnostic causal.",
        "constraints": [
            "Distinguer faits observés, déductions et lacunes.",
            "Conserver les signaux contradictoires.",
            "Ne produire aucun nombre absent des preuves.",
            "Proposer les jeux Data Grid à vérifier, pas une conclusion automatique.",
        ],
        "output": {"observations": [], "uncertainties": [], "contradictions": [], "data_to_verify": []},
    },
}


def db(*, autocommit: bool = True) -> psycopg.Connection[Any]:
    return psycopg.connect(DATABASE_URL, autocommit=autocommit)


def ensure_project(project_id: uuid.UUID) -> None:
    with db() as connection:
        row = connection.execute(
            "SELECT 1 FROM projects WHERE id=%s AND archived_at IS NULL", (project_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Projet introuvable ou archivé")


def text(value: Any) -> str:
    return str(value or "").strip()


def parse_date(value: Any) -> datetime | None:
    raw = text(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except ValueError:
        return None


def extra_map(dataset: dict[str, Any]) -> dict[str, str]:
    return {
        text(item.get("key")).casefold(): text(item.get("value"))
        for item in dataset.get("extras", [])
        if isinstance(item, dict) and item.get("key")
    }


def inferred_dimensions(dataset: dict[str, Any]) -> list[str]:
    corpus = " ".join(
        [text(dataset.get("title")), text(dataset.get("notes"))]
        + [text(tag.get("name")) for tag in dataset.get("tags", []) if isinstance(tag, dict)]
        + [text(group.get("title")) for group in dataset.get("groups", []) if isinstance(group, dict)]
    ).casefold()
    return [
        dimension["id"]
        for dimension in DATA_GRID_DIMENSIONS
        if any(term.casefold() in corpus for term in dimension["terms"])
    ]


def reliability(dataset: dict[str, Any]) -> dict[str, Any]:
    modified = parse_date(dataset.get("metadata_modified"))
    freshness_days = (datetime.now(UTC) - modified).days if modified else None
    checks = {
        "described": bool(text(dataset.get("notes"))),
        "licensed": bool(text(dataset.get("license_id") or dataset.get("license_title"))),
        "maintained": modified is not None,
        "resources_described": all(
            text(resource.get("description") or resource.get("name"))
            for resource in dataset.get("resources", [])
            if isinstance(resource, dict)
        ),
    }
    score = round(sum(checks.values()) / max(len(checks), 1), 2)
    return {
        "score": score,
        "method": "metadata-completeness-v1",
        "checks": checks,
        "freshness_days": freshness_days,
        "warning": "Indicateur technique de complétude, pas une certification de la source.",
    }


def normalize_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    extras = extra_map(dataset)
    resources = []
    for resource in dataset.get("resources", []):
        if not isinstance(resource, dict):
            continue
        resources.append(
            {
                "id": text(resource.get("id")),
                "name": text(resource.get("name")),
                "description": text(resource.get("description")),
                "format": text(resource.get("format")).upper(),
                "url": text(resource.get("url")),
                "created": text(resource.get("created")),
                "last_modified": text(resource.get("last_modified")),
                "size": resource.get("size"),
                "schema": resource.get("schema") or resource.get("datastore_active") or {},
            }
        )
    official_grid_values = [
        value for key, value in extras.items() if "data grid" in key or "data_grid" in key
    ]
    inferred = inferred_dimensions(dataset)
    geography = [
        text(group.get("title") or group.get("name"))
        for group in dataset.get("groups", [])
        if isinstance(group, dict) and text(group.get("title") or group.get("name"))
    ]
    periodicity = extras.get("update frequency") or extras.get("update_frequency") or extras.get("frequency")
    return {
        "dataset_id": text(dataset.get("name") or dataset.get("id")),
        "title": text(dataset.get("title")),
        "description": text(dataset.get("notes")),
        "organization": text((dataset.get("organization") or {}).get("title")),
        "license": text(dataset.get("license_title") or dataset.get("license_id")),
        "created": text(dataset.get("metadata_created")),
        "modified": text(dataset.get("metadata_modified")),
        "geography": geography,
        "tags": [text(tag.get("name")) for tag in dataset.get("tags", []) if isinstance(tag, dict)],
        "data_grid": {
            "official_metadata": official_grid_values,
            "inferred_dimensions": inferred,
            "classification": "official_metadata" if official_grid_values else "hdp_candidate",
        },
        "periodicity": periodicity,
        "expected_update_at": extras.get("expected update date") or extras.get("expected_update_at"),
        "temporal_coverage": {
            "start": extras.get("dataset date") or extras.get("time period of the dataset"),
            "end": extras.get("end date"),
        },
        "reliability": reliability(dataset),
        "resources": resources,
        "source_url": f"https://data.humdata.org/dataset/{text(dataset.get('name'))}",
        "raw_metadata": dataset,
    }


def store_hdx_metadata(project_id: uuid.UUID, datasets: list[dict[str, Any]]) -> int:
    now = datetime.now(UTC)
    count = 0
    with db() as connection:
        for dataset in datasets:
            base = (
                uuid.uuid4(), project_id, dataset["dataset_id"], "", dataset["title"],
                dataset["description"], Jsonb(dataset["data_grid"]["inferred_dimensions"]),
                Jsonb(dataset["geography"]), Jsonb(dataset["temporal_coverage"]),
                Jsonb({"resource_count": len(dataset["resources"])}),
                Jsonb(sorted({item["format"] for item in dataset["resources"] if item["format"]})),
                dataset["periodicity"] or None, parse_date(dataset["expected_update_at"]),
                Jsonb(dataset["reliability"]), Jsonb(dataset["raw_metadata"]), now,
            )
            connection.execute(
                """
                INSERT INTO hdx_metadata_records
                    (id, project_id, dataset_id, resource_id, title, description,
                     data_grid_dimensions, geography, temporal_coverage, structure,
                     formats, update_periodicity, expected_update_at, reliability,
                     source_metadata, observed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (project_id, dataset_id, resource_id) DO UPDATE SET
                    title=EXCLUDED.title, description=EXCLUDED.description,
                    data_grid_dimensions=EXCLUDED.data_grid_dimensions,
                    geography=EXCLUDED.geography, temporal_coverage=EXCLUDED.temporal_coverage,
                    structure=EXCLUDED.structure, formats=EXCLUDED.formats,
                    update_periodicity=EXCLUDED.update_periodicity,
                    expected_update_at=EXCLUDED.expected_update_at,
                    reliability=EXCLUDED.reliability, source_metadata=EXCLUDED.source_metadata,
                    observed_at=EXCLUDED.observed_at
                """,
                base,
            )
            count += 1
            for resource in dataset["resources"]:
                connection.execute(
                    """
                    INSERT INTO hdx_metadata_records
                        (id, project_id, dataset_id, resource_id, title, description,
                         data_grid_dimensions, geography, temporal_coverage, structure,
                         formats, update_periodicity, expected_update_at, reliability,
                         source_metadata, observed_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (project_id, dataset_id, resource_id) DO UPDATE SET
                        title=EXCLUDED.title, description=EXCLUDED.description,
                        structure=EXCLUDED.structure, formats=EXCLUDED.formats,
                        reliability=EXCLUDED.reliability,
                        source_metadata=EXCLUDED.source_metadata, observed_at=EXCLUDED.observed_at
                    """,
                    (
                        uuid.uuid4(), project_id, dataset["dataset_id"], resource["id"],
                        resource["name"] or dataset["title"], resource["description"],
                        Jsonb(dataset["data_grid"]["inferred_dimensions"]), Jsonb(dataset["geography"]),
                        Jsonb(dataset["temporal_coverage"]), Jsonb(resource["schema"]),
                        Jsonb([resource["format"]] if resource["format"] else []),
                        dataset["periodicity"] or None, parse_date(dataset["expected_update_at"]),
                        Jsonb(dataset["reliability"]), Jsonb(resource), now,
                    ),
                )
                count += 1
    return count


class DataGridSearch(BaseModel):
    query: str = Field(default="", max_length=200)
    dimensions: list[str] = Field(default_factory=list, max_length=6)
    location: str = Field(default="", max_length=160)
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    formats: list[str] = Field(default_factory=list, max_length=20)
    rows: int = Field(default=25, ge=1, le=100)


async def perform_datagrid_search(project_id: uuid.UUID, payload: DataGridSearch) -> dict[str, Any]:
    unknown = set(payload.dimensions) - DIMENSION_IDS
    if unknown:
        raise HTTPException(status_code=422, detail=f"Dimensions inconnues : {sorted(unknown)}")
    dimension_terms = [
        term
        for item in DATA_GRID_DIMENSIONS if item["id"] in payload.dimensions
        for term in item["terms"][:2]
    ]
    query_parts = [payload.query, payload.location, " ".join(dimension_terms)]
    query = " ".join(part.strip() for part in query_parts if part.strip()) or "humanitarian"
    params = {"q": query, "rows": payload.rows, "sort": "metadata_modified desc"}
    try:
        async with httpx.AsyncClient(timeout=45, follow_redirects=False, trust_env=False) as client:
            response = await client.get("https://data.humdata.org/api/3/action/package_search", params=params)
            response.raise_for_status()
            raw = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"HDX indisponible : {str(exc)[:300]}") from exc
    result = raw.get("result") if isinstance(raw, dict) else None
    packages = result.get("results", []) if isinstance(result, dict) else []
    datasets = [normalize_dataset(item) for item in packages if isinstance(item, dict)]
    wanted_formats = {item.upper() for item in payload.formats}
    if wanted_formats:
        datasets = [item for item in datasets if wanted_formats & {r["format"] for r in item["resources"]}]
    if payload.date_from:
        datasets = [item for item in datasets if not item["modified"] or item["modified"][:10] >= payload.date_from]
    if payload.date_to:
        datasets = [item for item in datasets if not item["modified"] or item["modified"][:10] <= payload.date_to]
    stored = store_hdx_metadata(project_id, datasets)
    coverage = Counter(dim for item in datasets for dim in item["data_grid"]["inferred_dimensions"])
    return {"query": query, "count": len(datasets), "metadata_records_updated": stored, "coverage": dict(coverage), "datasets": datasets}


@router.get("/hdx/datagrid/taxonomy")
def datagrid_taxonomy() -> dict[str, Any]:
    return {
        "version": "5.0.0",
        "dimensions": DATA_GRID_DIMENSIONS,
        "official_reference": "https://data.humdata.org/dashboards/overview-of-data-grids",
        "classification_rule": "Les dimensions inférées sont des candidats HDP; seule une métadonnée HDX explicite est marquée officielle.",
    }


@router.post("/projects/{project_id}/hdx/datagrid/search")
async def datagrid_search(project_id: uuid.UUID, payload: DataGridSearch) -> dict[str, Any]:
    ensure_project(project_id)
    return await perform_datagrid_search(project_id, payload)


@router.get("/projects/{project_id}/hdx/metadata")
def hdx_metadata(project_id: uuid.UUID, limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT dataset_id, resource_id, title, description, data_grid_dimensions,
                      geography, temporal_coverage, structure, formats, update_periodicity,
                      expected_update_at, reliability, source_metadata, observed_at
               FROM hdx_metadata_records WHERE project_id=%s
               ORDER BY observed_at DESC LIMIT %s""", (project_id, limit),
        ).fetchall()
    keys = ["dataset_id", "resource_id", "title", "description", "data_grid_dimensions", "geography", "temporal_coverage", "structure", "formats", "update_periodicity", "expected_update_at", "reliability", "source_metadata", "observed_at"]
    return [dict(zip(keys, row, strict=True)) for row in rows]


class AggregationPlan(BaseModel):
    metadata_ids: list[uuid.UUID] = Field(min_length=2, max_length=50)
    target_granularity: str = Field(default="admin1", pattern="^(country|admin1|admin2|point)$")
    time_bucket: str = Field(default="month", pattern="^(day|week|month|year)$")


@router.post("/projects/{project_id}/hdx/aggregation-plan")
def aggregation_plan(project_id: uuid.UUID, payload: AggregationPlan) -> dict[str, Any]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute(
            """SELECT id, dataset_id, resource_id, title, formats, geography,
                      temporal_coverage, structure, reliability
               FROM hdx_metadata_records WHERE project_id=%s AND id=ANY(%s)""",
            (project_id, payload.metadata_ids),
        ).fetchall()
    if len(rows) != len(set(payload.metadata_ids)):
        raise HTTPException(status_code=404, detail="Une ou plusieurs métadonnées sont absentes du projet")
    compatible = all(row[4] for row in rows) and all(row[5] for row in rows)
    return {
        "status": "ready" if compatible else "mapping_required",
        "join_contract": {"geography": payload.target_granularity, "time_bucket": payload.time_bucket, "missing_values": "preserve_and_flag", "provenance": "one lineage edge per input"},
        "inputs": [{"metadata_id": str(row[0]), "dataset_id": row[1], "resource_id": row[2], "title": row[3], "formats": row[4], "geography": row[5], "temporal": row[6], "schema": row[7], "reliability": row[8]} for row in rows],
        "blocking_checks": ["mapping géographique explicite", "unité et type compatibles", "périodes non ambiguës", "licences compatibles"],
    }


class SignalRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    locations: list[str] = Field(default_factory=list, max_length=50)
    themes: list[str] = Field(default_factory=list, max_length=50)
    min_severity: float = Field(default=0.0, ge=0, le=1)
    min_confidence: float = Field(default=0.0, ge=0, le=1)
    lookback_hours: int = Field(default=168, ge=1, le=8760)
    data_grid_dimensions: list[str] = Field(default_factory=list, max_length=6)
    query_template: str = Field(default="{title} {themes} {locations}", max_length=300)
    refresh_due_resources: bool = True


class SignalEventCreate(BaseModel):
    source: str = Field(pattern="^(hdx-signals|rss|news|gdacs|manual|webhook)$")
    external_id: str = Field(min_length=1, max_length=300)
    title: str = Field(min_length=2, max_length=300)
    summary: str = Field(default="", max_length=5000)
    occurred_at: datetime
    locations: list[str] = Field(default_factory=list, max_length=50)
    themes: list[str] = Field(default_factory=list, max_length=50)
    severity: float = Field(default=0.0, ge=0, le=1)
    confidence: float = Field(default=0.0, ge=0, le=1)
    evidence: list[dict[str, Any]] = Field(default_factory=list, max_length=50)
    raw: dict[str, Any] = Field(default_factory=dict)


def overlap(required: list[str], observed: list[str]) -> bool:
    if not required:
        return True
    observed_text = " ".join(observed).casefold()
    return any(item.casefold() in observed_text for item in required)


@router.get("/signals/prompts")
def signal_prompts() -> dict[str, Any]:
    return {"templates": SIGNAL_PROMPTS, "reference": "https://docs.humdata.org/about/hdx-signals/prompts", "human_review": "required before operational publication"}


@router.get("/projects/{project_id}/signals/rules")
def list_signal_rules(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute("SELECT id,name,enabled,locations,themes,min_severity,min_confidence,lookback_hours,data_grid_dimensions,query_template,refresh_due_resources FROM signal_rules WHERE project_id=%s ORDER BY name", (project_id,)).fetchall()
    keys = ["id","name","enabled","locations","themes","min_severity","min_confidence","lookback_hours","data_grid_dimensions","query_template","refresh_due_resources"]
    return [dict(zip(keys, row, strict=True)) for row in rows]


@router.post("/projects/{project_id}/signals/rules", status_code=201)
def create_signal_rule(project_id: uuid.UUID, payload: SignalRuleCreate) -> dict[str, Any]:
    ensure_project(project_id)
    unknown = set(payload.data_grid_dimensions) - DIMENSION_IDS
    if unknown:
        raise HTTPException(status_code=422, detail=f"Dimensions inconnues : {sorted(unknown)}")
    rule_id, now = uuid.uuid4(), datetime.now(UTC)
    with db() as connection:
        connection.execute("""INSERT INTO signal_rules (id,project_id,name,enabled,locations,themes,min_severity,min_confidence,lookback_hours,data_grid_dimensions,query_template,refresh_due_resources,created_at,updated_at) VALUES (%s,%s,%s,TRUE,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", (rule_id, project_id, payload.name, Jsonb(payload.locations), Jsonb(payload.themes), payload.min_severity, payload.min_confidence, payload.lookback_hours, Jsonb(payload.data_grid_dimensions), payload.query_template, payload.refresh_due_resources, now, now))
    return {"id": str(rule_id), **payload.model_dump(), "enabled": True}


async def evaluate_signal(project_id: uuid.UUID, event_id: uuid.UUID, event: SignalEventCreate) -> list[dict[str, Any]]:
    with db() as connection:
        rules = connection.execute("SELECT id,name,locations,themes,min_severity,min_confidence,data_grid_dimensions,query_template,refresh_due_resources FROM signal_rules WHERE project_id=%s AND enabled=TRUE", (project_id,)).fetchall()
    actions = []
    for rule in rules:
        if float(event.severity) < float(rule[4]) or float(event.confidence) < float(rule[5]) or not overlap(rule[2], event.locations) or not overlap(rule[3], event.themes):
            continue
        query = rule[7].format(title=event.title, themes=" ".join(event.themes), locations=" ".join(event.locations))[:200]
        action_id, started = uuid.uuid4(), datetime.now(UTC)
        try:
            search = await perform_datagrid_search(project_id, DataGridSearch(query=query, dimensions=rule[6], location=" ".join(event.locations)[:160], rows=25))
            refreshed = 0
            if rule[8]:
                with db() as connection:
                    result = connection.execute("""UPDATE resource_refresh_schedules s SET next_run_at=%s, updated_at=%s FROM local_resources r WHERE s.resource_id=r.id AND s.project_id=%s AND s.enabled=TRUE AND r.expected_update_at IS NOT NULL AND r.expected_update_at<=%s AND (r.geographic_scope IS NULL OR r.geographic_scope ILIKE ANY(%s))""", (started, started, project_id, started, [f"%{item}%" for item in event.locations] or ["%"] ))
                    refreshed = result.rowcount
            outcome = {"datasets_found": search["count"], "coverage": search["coverage"], "refreshes_queued": refreshed, "query": query}
            status, error = "completed", None
        except Exception as exc:  # Action isolated: the event remains observable.
            outcome, status, error = {}, "failed", str(exc)[:1000]
        with db() as connection:
            connection.execute("""INSERT INTO signal_actions (id,event_id,rule_id,action_type,status,result,error,started_at,finished_at) VALUES (%s,%s,%s,'datagrid_search_and_due_refresh',%s,%s,%s,%s,%s) ON CONFLICT (event_id,rule_id,action_type) DO NOTHING""", (action_id,event_id,rule[0],status,Jsonb(outcome),error,started,datetime.now(UTC)))
        actions.append({"rule_id": str(rule[0]), "rule": rule[1], "status": status, "result": outcome, "error": error})
    return actions


@router.post("/projects/{project_id}/signals", status_code=201)
async def ingest_signal(project_id: uuid.UUID, payload: SignalEventCreate) -> dict[str, Any]:
    ensure_project(project_id)
    event_id, now = uuid.uuid4(), datetime.now(UTC)
    with db() as connection:
        row = connection.execute("""INSERT INTO signal_events (id,project_id,source,external_id,title,summary,occurred_at,received_at,locations,themes,severity,confidence,evidence,raw) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (project_id,source,external_id) DO UPDATE SET title=EXCLUDED.title,summary=EXCLUDED.summary,received_at=EXCLUDED.received_at,evidence=EXCLUDED.evidence,raw=EXCLUDED.raw RETURNING id""", (event_id,project_id,payload.source,payload.external_id,payload.title,payload.summary,payload.occurred_at,now,Jsonb(payload.locations),Jsonb(payload.themes),payload.severity,payload.confidence,Jsonb(payload.evidence),Jsonb(payload.raw))).fetchone()
    actual_id = row[0]
    actions = await evaluate_signal(project_id, actual_id, payload)
    return {"id": str(actual_id), "deduplicated": actual_id != event_id, "actions": actions}


@router.get("/projects/{project_id}/signals")
def list_signals(project_id: uuid.UUID, limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute("SELECT id,source,external_id,title,summary,occurred_at,received_at,locations,themes,severity,confidence,evidence FROM signal_events WHERE project_id=%s ORDER BY occurred_at DESC LIMIT %s", (project_id,limit)).fetchall()
    keys = ["id","source","external_id","title","summary","occurred_at","received_at","locations","themes","severity","confidence","evidence"]
    return [dict(zip(keys,row,strict=True)) for row in rows]


@router.post("/projects/{project_id}/signals/syndromic-snapshot", status_code=201)
def syndromic_snapshot(project_id: uuid.UUID, hours: int = Query(default=168, ge=1, le=8760), scope: str = Query(default="global", max_length=160)) -> dict[str, Any]:
    ensure_project(project_id)
    end, start = datetime.now(UTC), datetime.now(UTC) - timedelta(hours=hours)
    with db() as connection:
        rows = connection.execute("SELECT id,title,occurred_at,locations,themes,severity,confidence,evidence FROM signal_events WHERE project_id=%s AND occurred_at BETWEEN %s AND %s AND (%s='global' OR locations::text ILIKE %s OR themes::text ILIKE %s)", (project_id,start,end,scope,f"%{scope}%",f"%{scope}%")).fetchall()
    theme_counts = Counter(value for row in rows for value in row[4])
    location_counts = Counter(value for row in rows for value in row[3])
    score = round(sum(float(row[5]) * float(row[6]) for row in rows), 3)
    snapshot_id = uuid.uuid4()
    evidence = [{"signal_id": str(row[0]), "title": row[1], "occurred_at": row[2]} for row in rows[:100]]
    with db() as connection:
        connection.execute("INSERT INTO syndromic_snapshots (id,project_id,scope_key,window_start,window_end,event_count,score,themes,locations,evidence,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (snapshot_id,project_id,scope,start,end,len(rows),score,Jsonb(dict(theme_counts)),Jsonb(dict(location_counts)),Jsonb(evidence),end))
    return {"id": str(snapshot_id), "scope": scope, "window_start": start, "window_end": end, "event_count": len(rows), "score": score, "themes": dict(theme_counts), "locations": dict(location_counts), "evidence": evidence, "interpretation": "Indice de convergence non diagnostique; validation humaine requise."}


class NotebookCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kernel: str = Field(default="python3", pattern="^(python3|ir)$")
    description: str = Field(default="", max_length=1000)
    cells: list[dict[str, Any]] = Field(default_factory=list, max_length=500)


class NotebookRevision(BaseModel):
    cells: list[dict[str, Any]] = Field(max_length=500)


def notebook_document(kernel: str, cells: list[dict[str, Any]]) -> dict[str, Any]:
    clean_cells = []
    for cell in cells:
        cell_type = cell.get("cell_type", "code")
        if cell_type not in {"code", "markdown", "raw"}:
            raise HTTPException(status_code=422, detail="Type de cellule Jupyter invalide")
        source = cell.get("source", "")
        if isinstance(source, list):
            source = "".join(str(item) for item in source)
        if not isinstance(source, str) or len(source) > 500_000:
            raise HTTPException(status_code=422, detail="Contenu de cellule invalide ou trop long")
        clean_cells.append({"cell_type": cell_type, "metadata": cell.get("metadata", {}), "source": source, "outputs": [], "execution_count": None} if cell_type == "code" else {"cell_type": cell_type, "metadata": cell.get("metadata", {}), "source": source})
    language = "python" if kernel == "python3" else "R"
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {"kernelspec": {"name": kernel, "display_name": kernel, "language": language}, "language_info": {"name": language.casefold()}}, "cells": clean_cells}


@router.post("/projects/{project_id}/notebooks", status_code=201)
def create_notebook(project_id: uuid.UUID, payload: NotebookCreate) -> dict[str, Any]:
    ensure_project(project_id)
    notebook_id, revision_id, now = uuid.uuid4(), uuid.uuid4(), datetime.now(UTC)
    document = notebook_document(payload.kernel, payload.cells)
    digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with db(autocommit=False) as connection:
        connection.execute("INSERT INTO notebooks (id,project_id,name,kernel,description,current_revision,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,1,%s,%s)", (notebook_id,project_id,payload.name,payload.kernel,payload.description,now,now))
        connection.execute("INSERT INTO notebook_revisions (id,notebook_id,revision_number,document,document_sha256,created_at) VALUES (%s,%s,1,%s,%s,%s)", (revision_id,notebook_id,Jsonb(document),digest,now))
    return {"id": str(notebook_id), "revision": 1, "sha256": digest, "document": document}


@router.get("/projects/{project_id}/notebooks")
def list_notebooks(project_id: uuid.UUID) -> list[dict[str, Any]]:
    ensure_project(project_id)
    with db() as connection:
        rows = connection.execute("SELECT id,name,kernel,description,current_revision,created_at,updated_at FROM notebooks WHERE project_id=%s ORDER BY updated_at DESC", (project_id,)).fetchall()
    keys = ["id","name","kernel","description","current_revision","created_at","updated_at"]
    return [dict(zip(keys,row,strict=True)) for row in rows]


@router.get("/notebooks/{notebook_id}")
def get_notebook(notebook_id: uuid.UUID) -> dict[str, Any]:
    with db() as connection:
        row = connection.execute("SELECT n.id,n.project_id,n.name,n.kernel,n.description,n.current_revision,r.id,r.document,r.document_sha256,r.created_at FROM notebooks n JOIN notebook_revisions r ON r.notebook_id=n.id AND r.revision_number=n.current_revision WHERE n.id=%s", (notebook_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Notebook introuvable")
    return {"id":str(row[0]),"project_id":str(row[1]),"name":row[2],"kernel":row[3],"description":row[4],"revision":row[5],"revision_id":str(row[6]),"document":row[7],"sha256":row[8],"created_at":row[9]}


@router.post("/notebooks/{notebook_id}/revisions", status_code=201)
def revise_notebook(notebook_id: uuid.UUID, payload: NotebookRevision) -> dict[str, Any]:
    with db(autocommit=False) as connection:
        row = connection.execute("SELECT kernel,current_revision FROM notebooks WHERE id=%s FOR UPDATE", (notebook_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Notebook introuvable")
        revision = int(row[1]) + 1
        document = notebook_document(row[0], payload.cells)
        digest = hashlib.sha256(json.dumps(document, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        revision_id, now = uuid.uuid4(), datetime.now(UTC)
        connection.execute("INSERT INTO notebook_revisions (id,notebook_id,revision_number,document,document_sha256,created_at) VALUES (%s,%s,%s,%s,%s,%s)", (revision_id,notebook_id,revision,Jsonb(document),digest,now))
        connection.execute("UPDATE notebooks SET current_revision=%s,updated_at=%s WHERE id=%s", (revision,now,notebook_id))
    return {"id":str(notebook_id),"revision":revision,"sha256":digest,"document":document}


class CellExecution(BaseModel):
    confirmed_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    timeout_seconds: int = Field(default=60, ge=1, le=300)
    max_output_bytes: int = Field(default=262144, ge=1024, le=1048576)


@router.post("/notebooks/{notebook_id}/cells/{cell_index}/executions", status_code=202)
def execute_notebook_cell(notebook_id: uuid.UUID, cell_index: int, payload: CellExecution) -> dict[str, Any]:
    notebook = get_notebook(notebook_id)
    cells = notebook["document"]["cells"]
    if cell_index < 0 or cell_index >= len(cells) or cells[cell_index]["cell_type"] != "code":
        raise HTTPException(status_code=422, detail="Cellule de code introuvable")
    code = cells[cell_index]["source"]
    digest = script_sha256(code)
    if digest != payload.confirmed_sha256:
        raise HTTPException(status_code=409, detail="Le code a changé : confirmer son nouveau SHA-256")
    language = "python" if notebook["kernel"] == "python3" else "r"
    try:
        timeout, max_output = validate_execution_request(language, payload.timeout_seconds, payload.max_output_bytes, False, [])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    execution_id, script_id, version_id, now = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), datetime.now(UTC)
    with db(autocommit=False) as connection:
        connection.execute("INSERT INTO project_scripts (id,project_id,name,language,content,description,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (script_id,uuid.UUID(notebook["project_id"]),f"{notebook['name']} · cellule {cell_index}",language,code,"Cellule Jupyter immuable",now,now))
        connection.execute("INSERT INTO script_versions (id,script_id,project_id,version_number,name,language,description,content,content_sha256,created_at) VALUES (%s,%s,%s,1,%s,%s,%s,%s,%s,%s)", (version_id,script_id,uuid.UUID(notebook["project_id"]),f"{notebook['name']} · cellule {cell_index}",language,"Cellule Jupyter immuable",code,digest,now))
        connection.execute("INSERT INTO script_executions (id,project_id,script_id,script_version_id,language,status,requested_at,timeout_seconds,max_output_bytes,network_enabled) VALUES (%s,%s,%s,%s,%s,'queued',%s,%s,%s,FALSE)", (execution_id,uuid.UUID(notebook["project_id"]),script_id,version_id,language,now,timeout,max_output))
        connection.execute("INSERT INTO notebook_cell_executions (id,notebook_id,revision_id,cell_index,script_execution_id,code_sha256,requested_at) VALUES (%s,%s,%s,%s,%s,%s,%s)", (uuid.uuid4(),notebook_id,uuid.UUID(notebook["revision_id"]),cell_index,execution_id,digest,now))
    prepare_execution_job(SPOOL, execution_id, language, code, timeout, max_output)
    return {"execution_id":str(execution_id),"status":"queued","code_sha256":digest,"network":"disabled","result_url":f"/api/executions/{execution_id}"}
