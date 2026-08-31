from __future__ import annotations

"""World Bank provider-facing bridge to the canonical HDP V7 semantic router.

The bridge does not implement a second semantic engine. It constrains the canonical
semantic request to `world-bank-health`, preserving one source of truth for intent,
geography mapping, completeness, project context, provenance and anti-false-zero.
"""

import uuid
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ...v6_semantic_api import DEFAULT_PROJECT_ID, SemanticSearchRequest, semantic_plan, semantic_search
from .parameters import SEMANTIC_PARAMETER_MAPPING, parameter_documentation

router = APIRouter(
    prefix="/api/providers/world-bank-health",
    tags=["provider-world-bank-health-semantic"],
)


class WorldBankSemanticRequest(BaseModel):
    project_id: uuid.UUID = DEFAULT_PROJECT_ID
    query: str = Field(default="", max_length=200, description="Theme/keywords; never interpreted as an indicator code without catalogue evidence.")
    location: str = Field(default="", max_length=160, description="Human geography expression, e.g. Rwanda, RWA or an HDP-supported M49 value.")
    date_from: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    date_to: str = Field(default="", pattern=r"^$|^\d{4}-\d{2}-\d{2}$")
    result_limit: int = Field(default=25, ge=1, le=100)

    def canonical_payload(self) -> SemanticSearchRequest:
        return SemanticSearchRequest(
            project_id=self.project_id,
            sources=["world-bank-health"],
            query=self.query,
            location=self.location,
            date_from=self.date_from,
            date_to=self.date_to,
            result_limit=self.result_limit,
        )


@router.get("/parameters")
def documented_parameters() -> dict[str, Any]:
    """Return documented native/provider parameters with explicit HDP qualification status."""
    return parameter_documentation()


@router.get("/semantic-contract")
def semantic_contract() -> dict[str, Any]:
    """Describe, without executing, the provider-facing contract to the semantic router."""
    return {
        "provider": "world-bank-health",
        "canonical_router": {
            "plan": "/api/semantic/plan",
            "search": "/api/semantic/search",
            "ui": "/api/semantic/ui",
        },
        "provider_bridge": {
            "plan": "/api/providers/world-bank-health/semantic/plan",
            "search": "/api/providers/world-bank-health/semantic/search",
            "ui": "/api/providers/world-bank-health/semantic-ui",
        },
        "fixed_sources": ["world-bank-health"],
        "canonical_fields": ["project_id", "query", "location", "date_from", "date_to", "result_limit"],
        "mapping": SEMANTIC_PARAMETER_MAPPING,
        "invariants": {
            "project_id_is_never_sent_to_world_bank": True,
            "location_never_overwrites_project_id": True,
            "indicator_codes_require_catalogue_evidence": True,
            "world_bank_aggregates_are_not_sovereign_countries": True,
            "bounded_empty_result_is_not_provider_wide_absence": True,
            "semantic_execution_uses_reference_world_bank_service": True,
        },
    }


@router.get("/semantic-ui", response_class=HTMLResponse, include_in_schema=False)
def semantic_ui() -> str:
    """World Bank-only graphical entry point to the canonical semantic router."""
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>HDP — World Bank sémantique</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;color:#172033;margin:0}}header{{padding:18px 24px;background:#172033;color:white}}main{{max-width:1200px;margin:auto;padding:20px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}}.panel{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:12px 0}}input,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box;width:100%}}button{{width:auto;cursor:pointer;margin-right:8px}}label{{display:flex;flex-direction:column;gap:4px;font-size:13px}}pre{{white-space:pre-wrap;overflow:auto;max-height:650px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}</style></head><body>
<header><h1>World Bank Health — interface sémantique HDP V7</h1><div>Intention → concept canonique → géographie vérifiée → indicateur vérifié → requête World Bank native.</div></header><main>
<div class='panel'><div class='grid'><label>Projet UUID<input id='project_id' value='{DEFAULT_PROJECT_ID}'></label><label>Thème / mots-clés<input id='query' placeholder='malaria'></label><label>Lieu<input id='location' placeholder='Rwanda'></label><label>Date début<input id='date_from' type='date'></label><label>Date fin<input id='date_to' type='date'></label><label>Limite<input id='result_limit' type='number' min='1' max='100' value='25'></label></div><p>Le lieu n'est jamais utilisé comme project_id. Les codes indicateurs et géographiques ne sont jamais inventés.</p><button id='plan'>Prévisualiser le plan</button><button id='search'>Exécuter</button><button id='params'>Documentation paramètres</button><button onclick="location.href='/api/providers/world-bank-health/ui'">Interface native</button><button onclick="location.href='/api/semantic/ui'">Routeur global</button></div>
<div class='panel'><pre id='out'>Prêt.</pre></div>
<script>const q=s=>document.querySelector(s);function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}function body(){{return {{project_id:q('#project_id').value,query:q('#query').value,location:q('#location').value,date_from:q('#date_from').value,date_to:q('#date_to').value,result_limit:Number(q('#result_limit').value||25)}}}}async function call(path,method='POST',payload=null){{const o={{method,credentials:'same-origin',headers:{{Accept:'application/json'}}}};if(payload!==null){{o.headers['Content-Type']='application/json';o.headers['x-hdp-csrf']=decodeURIComponent(cookie('hdp_csrf'));o.body=JSON.stringify(payload)}}const r=await fetch(path,o),x=await r.json();q('#out').textContent=JSON.stringify(x,null,2);if(!r.ok)throw new Error('HTTP '+r.status);return x}}q('#plan').onclick=()=>call('/api/providers/world-bank-health/semantic/plan','POST',body()).catch(e=>q('#out').textContent+='\nERREUR '+e.message);q('#search').onclick=()=>call('/api/providers/world-bank-health/semantic/search','POST',body()).catch(e=>q('#out').textContent+='\nERREUR '+e.message);q('#params').onclick=()=>call('/api/providers/world-bank-health/parameters','GET',null).catch(e=>q('#out').textContent+='\nERREUR '+e.message);</script></main></body></html>"""


@router.post("/semantic/plan")
def provider_semantic_plan(payload: WorldBankSemanticRequest) -> dict[str, Any]:
    """Build the canonical HDP semantic plan constrained to World Bank Health."""
    return semantic_plan(payload.canonical_payload())


@router.post("/semantic/search")
async def provider_semantic_search(payload: WorldBankSemanticRequest) -> dict[str, Any]:
    """Execute through the canonical semantic router, not through a duplicate provider path."""
    return await semantic_search(payload.canonical_payload())
