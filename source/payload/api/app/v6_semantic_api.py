from __future__ import annotations

"""HDP V7 semantic API. Filename retained for V6 import compatibility."""

import asyncio
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .federated_search import filter_catalog_items, unified_federated_items
from .health_sources import SEARCHABLE_SOURCE_IDS
from .semantic_contracts import CONTRACT_VERSION, Completeness, can_claim_empty_valid
from .semantic_persistence import finish_semantic_search, start_semantic_search
from .semantic_provenance import query_fingerprint, result_snapshot_hash, sha256_json
from .semantic_provider_execution import execute_native_route
from .semantic_router import SOURCE_CAPABILITIES, build_execution_plan

router = APIRouter(prefix="/api/semantic", tags=["semantic-router"])
DEFAULT_PROJECT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


class SemanticSearchRequest(BaseModel):
    project_id: uuid.UUID = DEFAULT_PROJECT_ID
    sources: list[str] = Field(default_factory=lambda: list(SEARCHABLE_SOURCE_IDS), min_length=1, max_length=20)
    query: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=160)
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    result_limit: int = Field(default=25, ge=1, le=100)


def _validate_sources(sources: list[str]) -> list[str]:
    unique = list(dict.fromkeys(value.strip() for value in sources if value.strip()))
    invalid = [value for value in unique if value not in SEARCHABLE_SOURCE_IDS]
    if invalid:
        raise HTTPException(status_code=422, detail=f"Sources inconnues: {', '.join(invalid)}")
    if not unique:
        raise HTTPException(status_code=422, detail="Sélectionnez au moins une source")
    return unique


def _project_plan(payload: SemanticSearchRequest, sources: list[str]) -> dict[str, Any]:
    """Bind the semantic plan to existing HDP project source settings."""
    from .main import ensure_project, get_project_source_settings

    ensure_project(payload.project_id)
    plan = build_execution_plan(
        sources,
        query=payload.query,
        location=payload.location,
        date_from=payload.date_from,
        date_to=payload.date_to,
        result_limit=payload.result_limit,
    )
    project_sources: dict[str, Any] = {}
    for route in plan["routes"]:
        source_id = str(route["source"])
        project_settings = get_project_source_settings(payload.project_id, source_id)
        enabled = bool(project_settings.get("enabled", True))
        project_parameters = project_settings.get("parameters") or {}
        project_sources[source_id] = {
            "enabled": enabled,
            "parameters": project_parameters,
            "schedule_defaults": project_settings.get("schedule_defaults") or {},
        }
        route["project_enabled"] = enabled
        route["provider_configuration"] = dict(project_parameters)
        if not enabled:
            route["executable"] = False
            route["project_blocked"] = True
            route.setdefault("warnings", []).append("Source désactivée dans la configuration du projet HDP.")
    plan["project_context"] = {"project_id": str(payload.project_id), "sources": project_sources}
    plan["query_fingerprint"] = query_fingerprint(plan)
    return plan


@router.get("/contracts")
def semantic_contracts() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "capability_modes": ["native_filter", "translated_filter", "post_filter", "output_only", "unsupported", "blocked_missing_mapping"],
        "completeness": ["exhaustive", "paginated_exhaustive", "bounded", "sampled", "partial", "unknown"],
        "operations": {source: value["operation"] for source, value in SOURCE_CAPABILITIES.items()},
        "invariants": {
            "non_exhaustive_post_filter_cannot_claim_empty_valid": True,
            "no_unverified_provider_identifier": True,
            "project_disabled_source_is_not_executed": True,
            "project_context_is_fingerprinted": True,
        },
    }


@router.get("/capabilities")
def semantic_capabilities() -> dict[str, Any]:
    plan = build_execution_plan(list(SEARCHABLE_SOURCE_IDS), query="health")
    return {"contract_version": CONTRACT_VERSION, "sources": plan["routes"]}


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def semantic_router_ui() -> str:
    source_boxes = "".join(f'<label class="src"><input type="checkbox" name="source" value="{source}" checked> {source}</label>' for source in SEARCHABLE_SOURCE_IDS)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V7 — Routeur sémantique</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f5f7fa;color:#172033}}header{{background:#172033;color:white;padding:18px 24px}}main{{max-width:1500px;margin:auto;padding:20px}}.tabs,.actions{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}button{{cursor:pointer}}input,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box}}.grid{{display:grid;grid-template-columns:2fr 2fr 1fr 1fr 100px;gap:10px}}.sources{{display:flex;flex-wrap:wrap;gap:8px 16px;background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px;margin:12px 0}}.src input{{width:auto}}.panel{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:10px 0}}.hidden{{display:none}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}}.card{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px}}pre{{white-space:pre-wrap;overflow:auto;max-height:600px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}code{{word-break:break-all}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}</style></head>
<body><header><h1>HDP V7 — Routeur sémantique</h1><div>Intention canonique → projet → traduction fournisseur → requête native → provenance.</div></header><main>
<div class="tabs"><button data-mode="simple">Simple</button><button data-mode="advanced">Avancé</button><button data-mode="expert">Expert</button></div>
<div class="panel"><div class="grid"><input id="query" placeholder="Thème, ex. paludisme"><input id="location" placeholder="Pays, ISO3 ou M49, ex. Rwanda"><input id="date_from" type="date"><input id="date_to" type="date"><input id="limit" type="number" min="1" max="100" value="25"></div><div class="sources">{source_boxes}</div><div class="actions"><button id="plan">Prévisualiser</button><button id="run">Exécuter</button><button onclick="location.href='/'">Retour HDP</button></div></div>
<div id="advanced" class="panel hidden"><strong>Avancé</strong><p>Projet : <input id="project_id" value="{DEFAULT_PROJECT_ID}" size="38">. Les sources désactivées dans le projet ne sont jamais exécutées.</p><div id="coverage"></div></div>
<div id="expert" class="panel hidden"><strong>Expert</strong><p>Plan, paramètres natifs, complétude, preuves, empreintes et erreurs.</p><pre id="output">Prêt.</pre></div>
<div id="fingerprints" class="panel"></div><div id="summary" class="cards"></div></main>
<script>const q=s=>document.querySelector(s);function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}function payload(){{return {{project_id:q('#project_id').value,sources:[...document.querySelectorAll('input[name=source]:checked')].map(x=>x.value),query:q('#query').value,location:q('#location').value,date_from:q('#date_from').value,date_to:q('#date_to').value,result_limit:Number(q('#limit').value||25)}}}}function esc(v){{return String(v??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]))}}function render(x){{const p=x.plan||x,geo=p.intent?.geography;let cards=[`<div class="card"><b>Interprétation</b><br>${{esc(p.intent?.interpretation)}}<br>${{geo?esc(geo.name)+' · '+esc(geo.iso3)+' · M49 '+esc(geo.m49):'géographie non résolue'}}<br>concept=${{esc(p.intent?.canonical_keywords||p.intent?.keywords)}}<br>projet=${{esc(p.project_context?.project_id||x.project_id||'')}}</div>`];for(const e of (x.sources||p.routes||[])){{const r=e.route||e;cards.push(`<div class="card"><b>${{esc(r.source)}}</b><br>opération=${{esc(r.operation)}}<br>exécutable=${{esc(r.executable)}}<br>projet actif=${{esc(r.project_enabled)}}<br>complétude=${{esc(e.completeness||r.completeness)}}${{e.status?'<br><b>statut='+esc(e.status)+'</b>':''}}${{e.item_count!==undefined?'<br>résultats='+esc(e.item_count):''}}${{r.criteria?'<br>critères=<code>'+esc(JSON.stringify(r.criteria))+'</code>':''}}${{r.warnings?.length?'<br>'+r.warnings.map(esc).join('<br>'):''}}</div>`)}}q('#summary').innerHTML=cards.join('');q('#fingerprints').innerHTML=`<b>query_fingerprint</b> <code>${{esc(p.query_fingerprint||'')}}</code>${{x.result_snapshot_hash?'<br><b>result_snapshot_hash</b> <code>'+esc(x.result_snapshot_hash)+'</code>':''}}${{x.semantic_search_id?'<br><b>semantic_search_id</b> '+esc(x.semantic_search_id):''}}`;q('#coverage').textContent=(p.routes||[]).map(r=>`${{r.source}}: ${{r.operation}} / ${{r.completeness}} / project=${{r.project_enabled}}`).join(' · ');q('#output').textContent=JSON.stringify(x,null,2)}}async function call(path){{q('#output').textContent='Exécution…';const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json','x-hdp-csrf':decodeURIComponent(cookie('hdp_csrf'))}},credentials:'same-origin',body:JSON.stringify(payload())}});const x=await r.json();render(x);if(!r.ok)throw new Error(x.detail||('HTTP '+r.status))}}q('#plan').onclick=()=>call('/api/semantic/plan').catch(e=>q('#output').textContent+='\nERREUR '+e.message);q('#run').onclick=()=>call('/api/semantic/search').catch(e=>q('#output').textContent+='\nERREUR '+e.message);document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{const m=b.dataset.mode;q('#advanced').classList.toggle('hidden',m==='simple');q('#expert').classList.toggle('hidden',m!=='expert')}});</script></body></html>"""


@router.post("/plan")
def semantic_plan(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        return _project_plan(payload, sources)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _blocked_status(route: dict[str, Any]) -> str:
    if route.get("project_blocked"):
        return "configuration_error"
    if route["source"] == "who-gho" and any("requalification" in warning for warning in route.get("warnings", [])):
        return "schema_drift"
    if "blocked_missing_mapping" in set(route.get("criteria", {}).values()):
        return "blocked_missing_mapping"
    return "unsupported"


async def _execute_source(route: dict[str, Any]) -> dict[str, Any]:
    from .main import get_source_global_settings, search_remote_source
    from .source_registry import request_preview

    source_id = str(route["source"])
    completeness = str(route.get("completeness") or "unknown")
    if not route.get("executable", False):
        return {"source": source_id, "status": _blocked_status(route), "completeness": completeness, "item_count": 0, "items": [], "error": "; ".join(route.get("warnings", [])) or None, "native_request": {}, "response_hash": None, "route": route}
    try:
        configuration = get_source_global_settings(source_id)
        settings = configuration["settings"]
        if not settings.get("enabled", True):
            return {"source": source_id, "status": "configuration_error", "completeness": completeness, "item_count": 0, "items": [], "error": "Connecteur désactivé globalement", "native_request": {}, "response_hash": None, "route": route}
        native_result = await execute_native_route(route, settings)
        if native_result is not None:
            provider_payload, items, native_request = native_result
        else:
            parameters = dict(route["parameters"])
            provider_payload, items = await search_remote_source(source_id, parameters, settings)
            preview = request_preview(source_id, parameters)
            native_request = {"method": preview["method"], "url": preview["url"], "query_parameters": preview["query_parameters"]}
        used_post_filter = "post_filter" in set(route.get("criteria", {}).values())
        if used_post_filter:
            params = route["parameters"]
            items = filter_catalog_items(items, date_from=str(params.get("date_from") or ""), date_to=str(params.get("date_to") or ""), location=str(params.get("location") or ""))
        items = items[: int(route["parameters"].get("result_limit") or 25)]
        comp = Completeness(completeness)
        if items:
            status = "success" if not used_post_filter else "partial"
        else:
            status = "empty_valid" if can_claim_empty_valid(completeness=comp, used_post_filter=used_post_filter) else "partial"
        return {"source": source_id, "status": status, "completeness": completeness, "item_count": len(items), "items": items, "error": None, "native_request": native_request, "response_hash": sha256_json(provider_payload), "route": route}
    except HTTPException as exc:
        status, error = ("authentication_error" if exc.status_code in {401, 403, 503} else "provider_error"), str(exc.detail)
    except httpx.TimeoutException as exc:
        status, error = "timeout", str(exc)
    except httpx.HTTPStatusError as exc:
        status, error = ("rate_limited" if exc.response.status_code == 429 else "provider_error"), f"HTTP {exc.response.status_code}: {exc}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        status = "authentication_error" if "exige" in error and ("APPNAME" in error or "IDENTIFIER" in error) else "failed"
    return {"source": source_id, "status": status, "completeness": completeness, "item_count": 0, "items": [], "error": error, "native_request": {}, "response_hash": None, "route": route}


@router.post("/search")
async def semantic_search(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        plan = _project_plan(payload, sources)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    request_record = payload.model_dump(mode="json")
    search_id = start_semantic_search(request_record, plan, project_id=payload.project_id)
    executions = await asyncio.gather(*(_execute_source(route) for route in plan["routes"]))
    usable = [entry for entry in executions if entry["status"] in {"success", "empty_valid", "partial"}]
    unified = unified_federated_items((entry["source"], entry["items"]) for entry in usable if entry["items"])
    snapshot = result_snapshot_hash([{"source": entry["source"], "status": entry["status"], "completeness": entry["completeness"], "response_hash": entry["response_hash"]} for entry in executions], unified)
    blocking = [entry for entry in executions if entry["status"] not in {"success", "empty_valid"}]
    overall = "success" if not blocking else "partial"
    persisted = finish_semantic_search(search_id, overall, snapshot, len(unified), executions)
    return {"status": overall, "contract_version": CONTRACT_VERSION, "project_id": str(payload.project_id), "semantic_search_id": search_id, "persistence_recorded": persisted, "query_fingerprint": plan["query_fingerprint"], "result_snapshot_hash": snapshot, "plan": plan, "sources": executions, "item_count": len(unified), "items": unified}
