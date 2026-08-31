from __future__ import annotations

import html
import json
import uuid
from typing import Any, Type

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .contracts import ProviderDescriptor
from .native_service import NativeProviderService


class ProviderQueryRequest(BaseModel):
    project_id: uuid.UUID | None = None
    operation: str = Field(min_length=1, max_length=120)
    parameters: dict[str, Any] = Field(default_factory=dict)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail={"status": "validation_error", "message": str(exc)})
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            return HTTPException(status_code=429, detail={"status": "rate_limited", "provider_http_status": status, "message": str(exc)})
        return HTTPException(status_code=502, detail={"status": "provider_error", "provider_http_status": status, "message": str(exc)})
    if isinstance(exc, httpx.TimeoutException):
        return HTTPException(status_code=504, detail={"status": "timeout", "message": str(exc)})
    if isinstance(exc, httpx.HTTPError):
        return HTTPException(status_code=502, detail={"status": "provider_error", "message": str(exc)})
    return HTTPException(status_code=502, detail={"status": "provider_error", "message": f"{type(exc).__name__}: {exc}"})


def _contexts(provider_id: str, project_id: uuid.UUID | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from ...main import get_project_source_settings, get_source_global_settings

    global_record = get_source_global_settings(provider_id)
    global_settings = dict(global_record.get("settings") or {})
    project_parameters: dict[str, Any] = {}
    if project_id is not None:
        project_record = get_project_source_settings(project_id, provider_id)
        if not project_record.get("enabled", True):
            raise ValueError(f"{provider_id} is disabled for this HDP project")
        project_parameters = dict(project_record.get("parameters") or {})
    runtime = dict(global_settings)
    runtime.setdefault("timeout_seconds", 40)
    runtime.setdefault("connect_timeout_seconds", 20)
    runtime.setdefault("retry_count", 2)
    runtime.setdefault("backoff_seconds", 2)
    runtime.setdefault("max_response_bytes", 25_000_000)
    runtime.setdefault("user_agent", "HDP/7.0.0")
    runtime.setdefault("accept_language", "en")
    return runtime, global_settings, project_parameters


def _ui_html(descriptor: ProviderDescriptor) -> str:
    provider = descriptor.provider_id
    title = html.escape(descriptor.name)
    contracts = descriptor.metadata.get("parameter_contracts") or {}
    official = [{"label": url, "url": url} for url in descriptor.evidence]
    model = json.dumps({"contracts": contracts, "official": official}, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>HDP — {title}</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;color:#172033;margin:0}}header{{padding:18px 24px;background:#172033;color:white}}main{{max-width:1500px;margin:auto;padding:20px}}.tabs,.actions,.links{{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}}.panel{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:10px 0}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}label{{display:flex;flex-direction:column;gap:5px;font-size:13px}}input,select,textarea,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box}}button{{cursor:pointer}}pre{{white-space:pre-wrap;overflow:auto;max-height:700px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}.hidden{{display:none}}.meta{{font-size:12px;color:#586174}}a{{color:#2357a6}}</style></head><body>
<header><h1>{title}</h1><div>{html.escape(descriptor.api_version)} · service fournisseur de référence HDP V7</div></header><main>
<div class='tabs'><button data-mode='simple'>Simple</button><button data-mode='advanced'>Avancé</button><button data-mode='expert'>Expert</button><button onclick="location.href='/api/semantic/ui'">Routeur sémantique</button><button onclick="location.href='/'">Retour HDP</button></div>
<div class='panel'><div class='grid'><label>Opération<select id='operation'></select></label><label>Projet HDP (UUID, optionnel)<input id='project' autocomplete='off' placeholder='UUID'></label></div><div id='fields' class='grid' style='margin-top:12px'></div><div class='actions'><button id='run'>Exécuter</button><button id='descriptor'>Descripteur</button></div></div>
<div class='panel'><strong>Documentation officielle</strong><div id='links' class='links'></div></div>
<div class='panel'><pre id='result'>Prêt.</pre></div>
<script>const MODEL={model};const q=s=>document.querySelector(s);let mode='simple';function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}function control(spec){{const id='p_'+spec.name;const level=spec.ui_level||'advanced';const wrap=document.createElement('label');wrap.dataset.level=level;wrap.innerHTML='<span>'+spec.name+(spec.required?' *':'')+'</span>';let el;if(spec.type==='boolean'){{el=document.createElement('select');el.innerHTML='<option value="false">false</option><option value="true">true</option>'}}else if(spec.enum){{el=document.createElement('select');el.innerHTML=spec.enum.map(v=>'<option value="'+String(v).replace(/"/g,'&quot;')+'">'+v+'</option>').join('')}}else{{el=document.createElement(spec.type.startsWith('array')?'textarea':'input');if(spec.type==='integer')el.type='number';if(spec.minimum!==undefined)el.min=spec.minimum;if(spec.maximum!==undefined)el.max=spec.maximum;if(spec.type.startsWith('array'))el.placeholder='une valeur par ligne ou séparée par virgule'}}el.id=id;if(spec.default!==undefined)el.value=Array.isArray(spec.default)?spec.default.join(','):String(spec.default);wrap.appendChild(el);const d=document.createElement('span');d.className='meta';d.textContent=(spec.location?spec.location+' · ':'')+(spec.description||'');wrap.appendChild(d);return wrap}}function visible(level){{return mode==='expert'||(mode==='advanced'&&level!=='expert')||(mode==='simple'&&level==='simple')}}function render(){{const op=q('#operation').value;const root=q('#fields');root.innerHTML='';for(const spec of (MODEL.contracts[op]||[])){{const node=control(spec);node.classList.toggle('hidden',!visible(node.dataset.level));root.appendChild(node)}}}}function read(){{const op=q('#operation').value;const out={{}};for(const spec of (MODEL.contracts[op]||[])){{const el=q('#p_'+spec.name);if(!el)continue;let v=el.value;if(v===''&&!spec.required&&spec.default===undefined)continue;if(spec.type==='integer')v=Number(v);else if(spec.type==='boolean')v=v==='true';else if(spec.type.startsWith('array')){{v=v.split(/[\n,]+/).map(x=>x.trim()).filter(Boolean);if(spec.type==='array[integer]')v=v.map(Number)}}out[spec.name]=v}}return out}}async function req(path,method='GET',body=null){{const o={{method,credentials:'same-origin',headers:{{Accept:'application/json'}}}};if(body!==null){{o.headers['Content-Type']='application/json';o.headers['x-hdp-csrf']=decodeURIComponent(cookie('hdp_csrf'));o.body=JSON.stringify(body)}}const r=await fetch(path,o);const x=await r.json();if(!r.ok)throw new Error(JSON.stringify(x.detail||x));return x}}q('#run').onclick=async()=>{{q('#result').textContent='Exécution…';try{{const body={{operation:q('#operation').value,parameters:read()}};if(q('#project').value.trim())body.project_id=q('#project').value.trim();const x=await req('/api/providers/{provider}/query','POST',body);q('#result').textContent=JSON.stringify(x,null,2)}}catch(e){{q('#result').textContent='ERREUR '+e.message}}}};q('#descriptor').onclick=async()=>{{try{{q('#result').textContent=JSON.stringify(await req('/api/providers/{provider}/descriptor'),null,2)}}catch(e){{q('#result').textContent='ERREUR '+e.message}}}};for(const op of Object.keys(MODEL.contracts)){{const o=document.createElement('option');o.value=op;o.textContent=op;q('#operation').appendChild(o)}}q('#operation').onchange=render;document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{mode=b.dataset.mode;render()}});q('#links').innerHTML=MODEL.official.map(x=>'<a target="_blank" rel="noopener" href="'+x.url+'">'+x.label+'</a>').join(' · ');render();</script></body></html>"""


def build_provider_router(descriptor: ProviderDescriptor, service_type: Type[NativeProviderService]) -> APIRouter:
    provider_id = descriptor.provider_id
    router = APIRouter(prefix=f"/api/providers/{provider_id}", tags=[f"provider-{provider_id}"])

    @router.get("/descriptor")
    def provider_descriptor() -> dict[str, Any]:
        return descriptor.to_dict()

    @router.get("/configuration/effective")
    def effective_configuration(project_id: uuid.UUID | None = None) -> dict[str, Any]:
        try:
            runtime, global_settings, project_parameters = _contexts(provider_id, project_id)
            service = service_type(runtime)
            return {
                "provider": provider_id,
                "project_id": str(project_id) if project_id else None,
                "configuration": service.effective_configuration(global_settings=global_settings, project_settings=project_parameters),
            }
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.post("/query")
    async def provider_query(payload: ProviderQueryRequest) -> dict[str, Any]:
        try:
            runtime, _global_settings, project_parameters = _contexts(provider_id, payload.project_id)
            service = service_type(runtime)
            raw, items, native = await service.execute(payload.operation, payload.parameters, project_settings=project_parameters)
            return {
                "provider": provider_id,
                "operation": payload.operation,
                "status": "success" if items else "partial",
                "completeness": "bounded",
                "count": len(items),
                "items": items,
                "native_response": raw,
                "native_request": native,
            }
        except Exception as exc:
            raise _http_error(exc) from exc

    @router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    def provider_ui() -> str:
        return _ui_html(descriptor)

    return router
