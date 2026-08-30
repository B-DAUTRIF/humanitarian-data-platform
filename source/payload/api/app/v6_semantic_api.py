from __future__ import annotations

"""V6 semantic-router API and test UI.

This test-branch API executes the existing verified source connectors through a
semantic plan. Provider failures and unsupported/degraded criteria are returned per
source instead of being collapsed into an empty result set.
"""

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .federated_search import filter_catalog_items, unified_federated_items
from .health_sources import SEARCHABLE_SOURCE_IDS
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
    """Small authenticated cockpit for manual qualification of the test router."""
    source_boxes = "".join(
        f'<label class="src"><input type="checkbox" name="source" value="{source}" checked> {source}</label>'
        for source in SEARCHABLE_SOURCE_IDS
    )
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HDP V6 — Routeur sémantique TEST</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f5f7fa;color:#172033}}header{{background:#172033;color:white;padding:18px 24px}}
main{{max-width:1400px;margin:auto;padding:20px}}.notice{{padding:12px;border:1px solid #d0d5dd;background:white;border-radius:8px;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:2fr 2fr 1fr 1fr 100px;gap:10px}}input,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box;width:100%}}
.sources{{display:flex;flex-wrap:wrap;gap:8px 16px;background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px;margin:12px 0}}.src input{{width:auto}}
.actions{{display:flex;gap:10px;margin-bottom:16px}}.actions button{{width:auto;cursor:pointer}}pre{{white-space:pre-wrap;overflow:auto;max-height:650px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin:12px 0}}.card{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px}}.ok{{font-weight:700}}.warn{{font-weight:700}}
</style></head><body><header><h1>Routeur sémantique HDP — branche de test</h1><div>Plan explicable, recherche multisource, résolution géographique M49 déterministe.</div></header>
<main><div class="notice"><strong>Important :</strong> cette interface ne fabrique aucun identifiant fournisseur. Une traduction non vérifiée est signalée comme partielle. Un échec API reste un échec et n'est jamais affiché comme « 0 résultat ».</div>
<div class="grid"><input id="query" placeholder="Mots-clés, ex. cholera ou RWANDA"><input id="location" placeholder="Localisation, ex. Rwanda"><input id="date_from" type="date"><input id="date_to" type="date"><input id="limit" type="number" min="1" max="100" value="25"></div>
<div class="sources">{source_boxes}</div><div class="actions"><button id="plan">Prévisualiser le plan</button><button id="run">Exécuter la recherche</button><button onclick="location.href='/'">Retour HDP</button></div>
<div id="summary" class="cards"></div><pre id="output">Prêt. Test recommandé : saisir RWANDA dans « Mots-clés », laisser « Localisation » vide et conserver les 10 sources.</pre></main>
<script>
const qs=s=>document.querySelector(s);
function cookie(name){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(name+'='))?.slice(name.length+1)||''}}
function payload(){{return {{sources:[...document.querySelectorAll('input[name=source]:checked')].map(x=>x.value),query:qs('#query').value,location:qs('#location').value,date_from:qs('#date_from').value,date_to:qs('#date_to').value,result_limit:Number(qs('#limit').value||25)}}}}
async function call(path){{qs('#output').textContent='Exécution…';qs('#summary').innerHTML='';const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json','x-hdp-csrf':decodeURIComponent(cookie('hdp_csrf'))}},credentials:'same-origin',body:JSON.stringify(payload())}});let x;try{{x=await r.json()}}catch(e){{x={{detail:'Réponse non JSON',status:r.status}}}};qs('#output').textContent=JSON.stringify(x,null,2);if(x.plan)render(x);else if(x.routes)render({{plan:x,sources:[]}});if(!r.ok)throw new Error(x.detail||('HTTP '+r.status));}}
function render(x){{const p=x.plan||x,geo=p.intent?.geography;let cards=[`<div class="card"><strong>Interprétation</strong><br>${{p.intent?.interpretation||''}}<br>${{geo?geo.name+' · ISO3 '+geo.iso3+' · M49 '+geo.m49:'Aucune entité M49 résolue'}}</div>`];for(const r of (x.sources||p.routes||[])){{const route=r.route||r;cards.push(`<div class="card"><strong>${{route.source}}</strong><br>route=${{route.status}}${{r.status?'<br>exécution='+r.status:''}}${{r.item_count!==undefined?'<br>résultats='+r.item_count:''}}${{r.error?'<br>erreur='+String(r.error):''}}${{route.warnings?.length?'<br>'+route.warnings.join('<br>'):''}}</div>`)}}qs('#summary').innerHTML=cards.join('')}}
qs('#plan').onclick=()=>call('/api/semantic/plan').catch(e=>qs('#output').textContent+='\n\nERREUR: '+e.message);qs('#run').onclick=()=>call('/api/semantic/search').catch(e=>qs('#output').textContent+='\n\nERREUR: '+e.message);
</script></body></html>"""


@router.post("/plan")
def semantic_plan(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        return build_execution_plan(
            sources,
            query=payload.query,
            location=payload.location,
            date_from=payload.date_from,
            date_to=payload.date_to,
            result_limit=payload.result_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _execute_source(route: dict[str, Any]) -> dict[str, Any]:
    # Imported lazily to avoid a circular import while app.main is bootstrapping.
    from .main import get_source_global_settings, search_remote_source

    source_id = str(route["source"])
    try:
        global_configuration = get_source_global_settings(source_id)
        global_settings = global_configuration["settings"]
        if not global_settings.get("enabled", True):
            return {
                "source": source_id,
                "status": "disabled",
                "item_count": 0,
                "items": [],
                "error": "Ce connecteur est désactivé globalement",
                "route": route,
            }
        _, items = await search_remote_source(source_id, dict(route["parameters"]), global_settings)
        params = route["parameters"]
        filtered = filter_catalog_items(
            items,
            date_from=str(params.get("date_from") or ""),
            date_to=str(params.get("date_to") or ""),
            location=str(params.get("location") or ""),
        )[: int(params.get("result_limit") or 25)]
        return {
            "source": source_id,
            "status": "success",
            "item_count": len(filtered),
            "items": filtered,
            "error": None,
            "route": route,
        }
    except Exception as exc:  # Source/API failures are data, not fake empty successes.
        return {
            "source": source_id,
            "status": "error",
            "item_count": 0,
            "items": [],
            "error": f"{type(exc).__name__}: {exc}",
            "route": route,
        }


@router.post("/search")
async def semantic_search(payload: SemanticSearchRequest) -> dict[str, Any]:
    sources = _validate_sources(payload.sources)
    try:
        plan = build_execution_plan(
            sources,
            query=payload.query,
            location=payload.location,
            date_from=payload.date_from,
            date_to=payload.date_to,
            result_limit=payload.result_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    executions = await asyncio.gather(*(_execute_source(route) for route in plan["routes"]))
    successes = [entry for entry in executions if entry["status"] == "success"]
    unified = unified_federated_items((entry["source"], entry["items"]) for entry in successes)
    return {
        "status": "success" if len(successes) == len(executions) else "partial",
        "plan": plan,
        "sources": executions,
        "item_count": len(unified),
        "items": unified,
    }
