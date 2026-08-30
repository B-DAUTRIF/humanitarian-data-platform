from __future__ import annotations

"""Semantic-router API for the reconciled HDP architecture."""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .federated_search import filter_catalog_items, unified_federated_items
from .health_sources import SEARCHABLE_SOURCE_IDS
from .semantic_contracts import Completeness, can_claim_empty_valid
from .semantic_provider_execution import execute_reliefweb_native
from .semantic_router import build_execution_plan

router = APIRouter(prefix="/api/semantic", tags=["semantic-router"])


class SemanticSearchRequest(BaseModel):
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


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def semantic_router_ui() -> str:
    source_boxes = "".join(f'<label><input type="checkbox" name="source" value="{s}" checked> {s}</label> ' for s in SEARCHABLE_SOURCE_IDS)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V7 — Routeur sémantique</title>
<style>body{{font-family:Segoe UI,Arial;margin:0;background:#f5f7fa;color:#172033}}header{{background:#172033;color:white;padding:18px 24px}}main{{max-width:1400px;margin:auto;padding:20px}}.grid{{display:grid;grid-template-columns:2fr 2fr 1fr 1fr 100px;gap:10px}}input,button{{padding:8px}}.sources{{background:white;padding:12px;margin:12px 0}}pre{{white-space:pre-wrap;background:#111827;color:#e5e7eb;padding:14px;max-height:650px;overflow:auto}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px}}.card{{background:white;padding:12px;border:1px solid #ddd}}</style></head>
<body><header><h1>HDP V7 — Routeur sémantique</h1><div>Contrats versionnés · opérations fournisseurs explicites · anti-faux-zéro</div></header><main>
<div class="grid"><input id="query" placeholder="Mots-clés ou RWANDA"><input id="location" placeholder="Localisation"><input id="date_from" type="date"><input id="date_to" type="date"><input id="limit" type="number" min="1" max="100" value="25"></div><div class="sources">{source_boxes}</div><button id="plan">Plan</button> <button id="run">Exécuter</button> <button onclick="location.href='/'">Retour</button><div id="summary" class="cards"></div><pre id="output">Test sentinelle : RWANDA.</pre>
<script>const q=s=>document.querySelector(s);function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}function body(){{return {{sources:[...document.querySelectorAll('input[name=source]:checked')].map(x=>x.value),query:q('#query').value,location:q('#location').value,date_from:q('#date_from').value,date_to:q('#date_to').value,result_limit:Number(q('#limit').value||25)}}}}async function call(p){{q('#output').textContent='Exécution…';let r=await fetch(p,{{method:'POST',headers:{{'Content-Type':'application/json','x-hdp-csrf':decodeURIComponent(cookie('hdp_csrf'))}},credentials:'same-origin',body:JSON.stringify(body())}});let x=await r.json();q('#output').textContent=JSON.stringify(x,null,2);render(x)}}function render(x){{let p=x.plan||x,c=[];for(let z of (x.sources||p.routes||[])){{let r=z.route||z;c.push(`<div class="card"><b>${{r.source}}</b><br>operation=${{r.operation}}<br>executable=${{r.executable}}<br>completeness=${{r.completeness}}${{z.status?'<br>status='+z.status:''}}${{z.item_count!==undefined?'<br>items='+z.item_count:''}}${{r.warnings?.length?'<br>'+r.warnings.join('<br>'):''}}</div>`)}}q('#summary').innerHTML=c.join('')}}q('#plan').onclick=()=>call('/api/semantic/plan');q('#run').onclick=()=>call('/api/semantic/search');</script></main></body></html>"""


@router.post("/plan")
def semantic_plan(payload: SemanticSearchRequest) -> dict[str, Any]:
    try:
        return build_execution_plan(_validate_sources(payload.sources), query=payload.query, location=payload.location, date_from=payload.date_from, date_to=payload.date_to, result_limit=payload.result_limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _blocked_status(route: dict[str, Any]) -> str:
    values = set(route.get("criteria", {}).values())
    return "blocked_missing_mapping" if "blocked_missing_mapping" in values else "unsupported"


async def _execute_source(route: dict[str, Any]) -> dict[str, Any]:
    from .main import get_source_global_settings, search_remote_source
    source_id = str(route["source"])
    if not route.get("executable", False):
        return {"source": source_id, "status": _blocked_status(route), "completeness": route["completeness"], "item_count": 0, "items": [], "error": None, "route": route}
    try:
        global_settings = get_source_global_settings(source_id)["settings"]
        if not global_settings.get("enabled", True):
            return {"source": source_id, "status": "configuration_error", "completeness": "unknown", "item_count": 0, "items": [], "error": "Connecteur désactivé", "route": route}
        if source_id == "reliefweb" and route.get("native_parameters"):
            _, items = await execute_reliefweb_native(route, global_settings)
        else:
            _, items = await search_remote_source(source_id, dict(route["parameters"]), global_settings)
        params = route["parameters"]
        uses_post_filter = "post_filter" in set(route.get("criteria", {}).values())
        filtered = items
        if uses_post_filter:
            filtered = filter_catalog_items(items, date_from=str(params.get("date_from") or ""), date_to=str(params.get("date_to") or ""), location=str(params.get("location") or ""))
        filtered = filtered[: int(params.get("result_limit") or 25)]
        completeness = Completeness(route.get("completeness", "unknown"))
        if filtered:
            status = "success"
        elif can_claim_empty_valid(completeness=completeness, used_post_filter=uses_post_filter):
            status = "empty_valid"
        else:
            status = "partial"
        return {"source": source_id, "status": status, "completeness": completeness.value, "item_count": len(filtered), "items": filtered, "error": None, "route": route}
    except HTTPException as exc:
        status = "authentication_error" if exc.status_code in {401, 403, 503} else "provider_error"
        return {"source": source_id, "status": status, "completeness": "unknown", "item_count": 0, "items": [], "error": str(exc.detail), "route": route}
    except Exception as exc:
        return {"source": source_id, "status": "provider_error", "completeness": "unknown", "item_count": 0, "items": [], "error": f"{type(exc).__name__}: {exc}", "route": route}


@router.post("/search")
async def semantic_search(payload: SemanticSearchRequest) -> dict[str, Any]:
    try:
        plan = build_execution_plan(_validate_sources(payload.sources), query=payload.query, location=payload.location, date_from=payload.date_from, date_to=payload.date_to, result_limit=payload.result_limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    executions = await asyncio.gather(*(_execute_source(route) for route in plan["routes"]))
    usable = [e for e in executions if e["status"] in {"success", "empty_valid"}]
    unified = unified_federated_items((e["source"], e["items"]) for e in usable if e["items"])
    overall = "success" if len(usable) == len(executions) else "partial"
    return {"status": overall, "plan": plan, "sources": executions, "item_count": len(unified), "items": unified}
