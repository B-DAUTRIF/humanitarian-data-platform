from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..base.errors import ProviderConfigurationError, ProviderRateLimitedError, ProviderValidationError
from .descriptor import RELIEFWEB_DESCRIPTOR
from .service import ReliefWebService

router = APIRouter(prefix="/api/providers/reliefweb", tags=["provider-reliefweb"])


class ReliefWebSearchRequest(BaseModel):
    project_id: uuid.UUID | None = None
    content_type: str = Field(default="reports", max_length=40)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ReliefWebItemRequest(BaseModel):
    project_id: uuid.UUID | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


def _contexts(project_id: uuid.UUID | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from ...main import get_project_source_settings, get_source_global_settings

    global_record = get_source_global_settings("reliefweb")
    global_settings = dict(global_record.get("settings") or {})
    project_parameters: dict[str, Any] = {}
    if project_id is not None:
        project_record = get_project_source_settings(project_id, "reliefweb")
        if not project_record.get("enabled", True):
            raise ProviderConfigurationError("ReliefWeb is disabled for this HDP project")
        project_parameters = dict(project_record.get("parameters") or {})
    runtime = dict(global_settings)
    runtime.setdefault("timeout_seconds", 20)
    runtime.setdefault("connect_timeout_seconds", 5)
    runtime.setdefault("user_agent", "HDP/7")
    runtime.setdefault("accept_language", "en")
    return runtime, global_settings, project_parameters


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ProviderConfigurationError):
        return HTTPException(status_code=503, detail={"status":"configuration_error", "message":str(exc)})
    if isinstance(exc, ProviderRateLimitedError):
        return HTTPException(status_code=429, detail={"status":"rate_limited", "message":str(exc)})
    if isinstance(exc, (ProviderValidationError, ValueError)):
        return HTTPException(status_code=422, detail={"status":"validation_error", "message":str(exc)})
    return HTTPException(status_code=502, detail={"status":"provider_error", "message":f"{type(exc).__name__}: {exc}"})


@router.get("/descriptor")
def descriptor() -> dict[str, Any]:
    return RELIEFWEB_DESCRIPTOR.to_dict()


@router.get("/configuration/effective")
def effective_configuration(project_id: uuid.UUID | None = None) -> dict[str, Any]:
    runtime, global_settings, project_parameters = _contexts(project_id)
    service = ReliefWebService(runtime)
    return {"provider":"reliefweb", "project_id":str(project_id) if project_id else None, "configuration":service.effective_configuration(global_settings=global_settings, project_settings=project_parameters)}


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def reliefweb_ui() -> str:
    content_options = "".join(f'<option value="{value}">{value}</option>' for value in RELIEFWEB_DESCRIPTOR.content_types)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP — ReliefWeb V2</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;color:#172033;margin:0}}header{{padding:18px 24px;background:#172033;color:white}}main{{max-width:1500px;margin:auto;padding:20px}}.tabs,.actions{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}.panel{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:10px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}input,select,textarea,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box;width:100%}}button{{width:auto;cursor:pointer}}textarea{{min-height:110px;font-family:Consolas,monospace}}pre{{white-space:pre-wrap;overflow:auto;max-height:650px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}.hidden{{display:none}}label{{display:flex;flex-direction:column;gap:4px;font-size:13px}}.hint{{color:#586174;font-size:13px}}</style></head>
<body><header><h1>ReliefWeb V2 dans HDP</h1><div>Client natif individualisé — même ProviderService pour UI, API, projets et routeur sémantique.</div></header><main>
<div class="tabs"><button data-mode="simple">Simple</button><button data-mode="advanced">Avancé</button><button data-mode="expert">Expert</button><button onclick="location.href='/'">Retour HDP</button></div>
<div class="panel"><div class="grid"><label>Projet (optionnel)<input id="project" placeholder="UUID"></label><label>Type de contenu<select id="content">{content_options}</select></label><label>Mots-clés<input id="query" placeholder="malaria"></label><label>Pays<input id="country" placeholder="Rwanda"></label><label>Du<input id="date_from" type="date"></label><label>Au<input id="date_to" type="date"></label><label>Limite<input id="limit" type="number" min="1" max="1000" value="25"></label><label>Tri<input id="sort" value="date.created:desc"></label></div><div class="actions"><button id="run">Rechercher</button><button id="config">Configuration effective</button><button id="descriptor">Descripteur</button></div><div id="effective" class="hint"></div></div>
<div id="advanced" class="panel hidden"><h3>Avancé</h3><div class="grid"><label>Champs de recherche<input id="query_fields" placeholder="title^5,body"></label><label>Opérateur<select id="query_operator"><option value="">défaut</option><option>AND</option><option>OR</option></select></label><label>Profile<select id="profile"><option value="">défaut</option><option>minimal</option><option>list</option><option>full</option></select></label><label>Preset<select id="preset"><option value="">aucun</option><option>analysis</option><option>latest</option><option>minimal</option></select></label><label>Offset<input id="offset" type="number" min="0" value="0"></label><label>Fields include<input id="fields_include" placeholder="title,country,source"></label><label>Fields exclude<input id="fields_exclude" placeholder="body-html"></label><label>Facettes JSON<textarea id="facets" placeholder='[{{"field":"theme","limit":20,"scope":"query"}}]'></textarea></label></div><label>Filtre ReliefWeb JSON récursif<textarea id="filter" placeholder='{{"operator":"AND","conditions":[{{"field":"country","value":"Rwanda"}},{{"field":"theme","value":"Health"}}]}}'></textarea></label><div class="hint">Les filtres complexes sont validés côté serveur et envoyés en POST. Le pays/date Simple sont combinés dans le même arbre AND.</div></div>
<div id="expert" class="panel hidden"><h3>Expert</h3><div class="grid"><label><span>slim</span><select id="slim"><option value="">défaut</option><option value="true">true</option><option value="false">false</option></select></label><label><span>verbose</span><select id="verbose"><option value="">défaut</option><option value="true">true</option><option value="false">false</option></select></label></div><p class="hint">Affiche requête effective, appname/origine, payload natif, réponse native et objets normalisés. Les secrets des autres fournisseurs ne sont jamais exposés par ce panneau.</p><pre id="output">Prêt.</pre></div>
<div class="panel"><h3>Résultat</h3><pre id="result">Aucune recherche exécutée.</pre></div>
<script>
const q=s=>document.querySelector(s);function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}function csv(id){{return q(id).value.split(',').map(x=>x.trim()).filter(Boolean)}}function parse(id){{const v=q(id).value.trim();return v?JSON.parse(v):null}}function bool(id){{const v=q(id).value;return v===''?undefined:v==='true'}}
function payload(){{const p={{query:q('#query').value,limit:Number(q('#limit').value||25),offset:Number(q('#offset').value||0)}};const qf=csv('#query_fields');if(qf.length)p.query_fields=qf;if(q('#query_operator').value)p.query_operator=q('#query_operator').value;if(q('#profile').value)p.profile=q('#profile').value;if(q('#preset').value)p.preset=q('#preset').value;const s=q('#sort').value.trim();if(s)p.sort=[s];const fi=csv('#fields_include'),fe=csv('#fields_exclude');if(fi.length)p.fields_include=fi;if(fe.length)p.fields_exclude=fe;const facets=parse('#facets');if(facets)p.facets=facets;let filters=[];const native=parse('#filter');if(native)filters.push(native);if(q('#country').value)filters.push({{field:'country',value:q('#country').value}});if(q('#date_from').value||q('#date_to').value){{let v={{}};if(q('#date_from').value)v.from=q('#date_from').value+'T00:00:00+00:00';if(q('#date_to').value)v.to=q('#date_to').value+'T23:59:59+00:00';filters.push({{field:'date.created',value:v}})}}if(filters.length===1)p.filter=filters[0];else if(filters.length)p.filter={{operator:'AND',conditions:filters}};const sl=bool('#slim'),vb=bool('#verbose');if(sl!==undefined)p.slim=sl;if(vb!==undefined)p.verbose=vb;return {{project_id:q('#project').value||null,content_type:q('#content').value,parameters:p}}}}
async function req(path,method='GET',body=null){{const opts={{method,credentials:'same-origin',headers:{{'Accept':'application/json'}}}};if(body!==null){{opts.headers['Content-Type']='application/json';opts.headers['x-hdp-csrf']=decodeURIComponent(cookie('hdp_csrf'));opts.body=JSON.stringify(body)}}const r=await fetch(path,opts);const x=await r.json();if(!r.ok)throw new Error(JSON.stringify(x.detail||x));return x}}
q('#run').onclick=async()=>{{try{{const x=await req('/api/providers/reliefweb/search','POST',payload());q('#result').textContent=JSON.stringify(x.items,null,2);q('#output').textContent=JSON.stringify({{native_request:x.native_request,native_response:x.native_response,status:x.status}},null,2)}}catch(e){{q('#result').textContent='ERREUR '+e.message}}}};
q('#config').onclick=async()=>{{try{{const id=q('#project').value;const x=await req('/api/providers/reliefweb/configuration/effective'+(id?'?project_id='+encodeURIComponent(id):''));q('#effective').textContent=JSON.stringify(x.configuration)}}catch(e){{q('#effective').textContent='ERREUR '+e.message}}}};
q('#descriptor').onclick=async()=>{{try{{const x=await req('/api/providers/reliefweb/descriptor');q('#output').textContent=JSON.stringify(x,null,2)}}catch(e){{q('#output').textContent='ERREUR '+e.message}}}};
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{const m=b.dataset.mode;q('#advanced').classList.toggle('hidden',m==='simple');q('#expert').classList.toggle('hidden',m!=='expert')}});
</script></main></body></html>"""


@router.post("/search")
async def search(payload: ReliefWebSearchRequest) -> dict[str, Any]:
    if payload.content_type not in RELIEFWEB_DESCRIPTOR.content_types:
        raise HTTPException(status_code=422, detail={"status":"validation_error", "message":f"Unknown ReliefWeb content type: {payload.content_type}"})
    try:
        runtime, global_settings, project_parameters = _contexts(payload.project_id)
        service = ReliefWebService(runtime)
        raw, normalized, native_request = await service.execute(payload.content_type, payload.parameters, global_settings=global_settings, project_settings=project_parameters)
        return {"provider":"reliefweb", "content_type":payload.content_type, "status":"success" if normalized else "empty_valid", "count":len(normalized), "items":normalized, "native_response":raw, "native_request":native_request}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/item/{content_type}/{item_id}")
async def item(content_type: str, item_id: str, payload: ReliefWebItemRequest) -> dict[str, Any]:
    if content_type not in RELIEFWEB_DESCRIPTOR.content_types:
        raise HTTPException(status_code=422, detail={"status":"validation_error", "message":f"Unknown ReliefWeb content type: {content_type}"})
    try:
        runtime, global_settings, project_parameters = _contexts(payload.project_id)
        service = ReliefWebService(runtime)
        raw, normalized, native_request = await service.execute(content_type, payload.parameters, global_settings=global_settings, project_settings=project_parameters, item_id=item_id)
        return {"provider":"reliefweb", "content_type":content_type, "item_id":item_id, "status":"success" if normalized else "empty_valid", "items":normalized, "native_response":raw, "native_request":native_request}
    except Exception as exc:
        raise _http_error(exc) from exc
