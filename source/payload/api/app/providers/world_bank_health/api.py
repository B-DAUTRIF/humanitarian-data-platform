from __future__ import annotations

import uuid
from typing import Any, Literal

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .descriptor import WORLD_BANK_HEALTH_DESCRIPTOR
from .service import WorldBankHealthService

router = APIRouter(prefix="/api/providers/world-bank-health", tags=["provider-world-bank-health"])


class WorldBankObservationRequest(BaseModel):
    project_id: uuid.UUID | None = None
    country: str = Field(default="all", max_length=399)
    indicator: str = Field(min_length=1, max_length=1000)
    date: str = Field(default="", pattern=r"^$|^\d{4}(:\d{4})?$")
    source: int = Field(default=2, ge=1, le=10000)
    page: int = Field(default=1, ge=1, le=10000)
    per_page: int = Field(default=50, ge=1, le=50000)
    mrv: int | None = Field(default=None, ge=1, le=10000)
    mrnev: int | None = Field(default=None, ge=1, le=10000)
    gapfill: bool = False
    frequency: str = Field(default="", pattern=r"^(|Y|Q|M)$")
    footnote: bool = False
    format: Literal["json"] = "json"
    language: str = Field(default="en", pattern=r"^(en|fr|es|ar|zh)$")


class WorldBankMetadataRequest(BaseModel):
    project_id: uuid.UUID | None = None
    query: str = Field(min_length=1, max_length=500)
    source: int = Field(default=2, ge=1, le=10000)
    page: int = Field(default=1, ge=1, le=10000)
    per_page: int = Field(default=1000, ge=1, le=50000)
    format: Literal["json"] = "json"
    language: str = Field(default="en", pattern=r"^(en|fr|es|ar|zh)$")


def _bounded_status(items: list[dict[str, Any]]) -> str:
    """A single bounded/paginated response cannot prove provider-wide absence."""
    return "success" if items else "partial"


def _contexts(project_id: uuid.UUID | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from ...main import get_project_source_settings, get_source_global_settings

    global_record = get_source_global_settings("world-bank-health")
    global_settings = dict(global_record.get("settings") or {})
    project_parameters: dict[str, Any] = {}
    if project_id is not None:
        project_record = get_project_source_settings(project_id, "world-bank-health")
        if not project_record.get("enabled", True):
            raise ValueError("World Bank Health is disabled for this HDP project")
        project_parameters = dict(project_record.get("parameters") or {})
    runtime = dict(global_settings)
    runtime.setdefault("timeout_seconds", 40)
    runtime.setdefault("connect_timeout_seconds", 20)
    runtime.setdefault("retry_count", 2)
    runtime.setdefault("backoff_seconds", 2)
    runtime.setdefault("user_agent", "HDP/7.0.0")
    runtime.setdefault("accept_language", "en")
    return runtime, global_settings, project_parameters


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail={"status": "validation_error", "message": str(exc)})
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            return HTTPException(status_code=429, detail={"status": "rate_limited", "message": str(exc)})
        return HTTPException(status_code=502, detail={"status": "provider_error", "provider_http_status": status, "message": str(exc)})
    if isinstance(exc, httpx.TimeoutException):
        return HTTPException(status_code=504, detail={"status": "timeout", "message": str(exc)})
    if isinstance(exc, httpx.HTTPError):
        return HTTPException(status_code=502, detail={"status": "provider_error", "message": str(exc)})
    return HTTPException(status_code=502, detail={"status": "provider_error", "message": f"{type(exc).__name__}: {exc}"})


@router.get("/descriptor")
def descriptor() -> dict[str, Any]:
    return WORLD_BANK_HEALTH_DESCRIPTOR.to_dict()


@router.get("/configuration/effective")
def effective_configuration(project_id: uuid.UUID | None = None) -> dict[str, Any]:
    try:
        runtime, global_settings, project_parameters = _contexts(project_id)
        service = WorldBankHealthService(runtime)
        return {"provider":"world-bank-health", "project_id":str(project_id) if project_id else None,
                "configuration":service.effective_configuration(global_settings=global_settings, project_settings=project_parameters)}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/observations")
async def observations(payload: WorldBankObservationRequest) -> dict[str, Any]:
    try:
        runtime, _global_settings, project_parameters = _contexts(payload.project_id)
        service = WorldBankHealthService(runtime)
        values = payload.model_dump(exclude={"project_id", "format"})
        for name in ("source", "page", "per_page", "mrv", "mrnev", "gapfill", "frequency", "footnote", "language"):
            if name in project_parameters and name not in payload.model_fields_set:
                values[name] = project_parameters[name]
        raw, normalized, native_request = await service.observations(**values)
        return {"provider":"world-bank-health", "status":_bounded_status(normalized), "completeness":"bounded",
                "count":len(normalized), "items":normalized, "native_response":raw, "native_request":native_request,
                "qualified_format":payload.format}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.post("/metadata")
async def metadata(payload: WorldBankMetadataRequest) -> dict[str, Any]:
    try:
        runtime, _global_settings, project_parameters = _contexts(payload.project_id)
        service = WorldBankHealthService(runtime)
        source = payload.source if "source" in payload.model_fields_set else int(project_parameters.get("source", payload.source))
        language = payload.language if "language" in payload.model_fields_set else str(project_parameters.get("language", payload.language))
        raw, normalized, native_request = await service.get_metadata(source=source, query=payload.query, page=payload.page, per_page=payload.per_page, language=language)
        return {"provider":"world-bank-health", "status":_bounded_status(normalized), "completeness":"bounded",
                "count":len(normalized), "items":normalized, "native_response":raw, "native_request":native_request,
                "qualified_format":payload.format}
    except Exception as exc:
        raise _http_error(exc) from exc


async def _catalog(operation: str, **kwargs: Any) -> dict[str, Any]:
    try:
        runtime, _, _ = _contexts(None)
        service = WorldBankHealthService(runtime)
        method = getattr(service, operation)
        raw, rows, native = await method(**kwargs)
        return {"provider":"world-bank-health", "status":_bounded_status(rows), "completeness":"bounded",
                "count":len(rows), "items":rows, "native_response":raw, "native_request":native}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.get("/indicators")
async def indicators(source: int = Query(2, ge=1), page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1, le=50000), language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$")) -> dict[str, Any]:
    return await _catalog("list_indicators", source=source, page=page, per_page=per_page, language=language)


@router.get("/countries")
async def countries(identifier: str = "", page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1, le=50000), language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$")) -> dict[str, Any]:
    return await _catalog("list_countries", identifier=identifier, page=page, per_page=per_page, language=language)


@router.get("/topics")
async def topics(identifier: str = "", page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1, le=50000), language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$")) -> dict[str, Any]:
    return await _catalog("list_topics", identifier=identifier, page=page, per_page=per_page, language=language)


@router.get("/sources")
async def sources(identifier: str = "", page: int = Query(1, ge=1), per_page: int = Query(1000, ge=1, le=50000), language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$")) -> dict[str, Any]:
    return await _catalog("list_sources", identifier=identifier, page=page, per_page=per_page, language=language)


@router.get("/indicator/{indicator}/metadata")
async def indicator_metadata(indicator: str, source: int = Query(2, ge=1), language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$")) -> dict[str, Any]:
    try:
        runtime, _, _ = _contexts(None)
        service = WorldBankHealthService(runtime)
        raw, rows, native = await service.indicator_metadata(indicator, source=source, language=language)
        return {"provider":"world-bank-health", "status":_bounded_status(rows), "completeness":"bounded",
                "count":len(rows), "items":rows, "native_response":raw, "native_request":native}
    except Exception as exc:
        raise _http_error(exc) from exc


@router.get("/geography-vocabulary")
async def geography_vocabulary(language: str = Query("en", pattern=r"^(en|fr|es|ar|zh)$"), refresh: bool = False) -> dict[str, Any]:
    try:
        runtime, _, _ = _contexts(None)
        service = WorldBankHealthService(runtime)
        vocabulary = await service.geography_vocabulary(language=language, refresh=refresh)
        return vocabulary.to_record()
    except Exception as exc:
        raise _http_error(exc) from exc


@router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def world_bank_ui() -> str:
    """Provider-native UI. Every qualified observation parameter has its own control."""
    return """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP — World Bank Health</title>
<style>body{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fa;color:#172033;margin:0}header{padding:18px 24px;background:#172033;color:white}main{max-width:1500px;margin:auto;padding:20px}.tabs,.actions{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.panel{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:10px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}input,select,button{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box;width:100%}button{width:auto;cursor:pointer}pre{white-space:pre-wrap;overflow:auto;max-height:650px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}.hidden{display:none}label{display:flex;flex-direction:column;gap:4px;font-size:13px}.hint{color:#586174;font-size:13px}</style></head><body>
<header><h1>World Bank Health / WDI dans HDP</h1><div>Contrat JSON qualifié — pays et agrégats restent sémantiquement distincts.</div></header><main>
<div class="tabs"><button data-mode="simple">Simple</button><button data-mode="advanced">Avancé</button><button data-mode="expert">Expert</button><button onclick="location.href='/'">Retour HDP</button></div>
<div class="panel"><div class="grid"><label>Projet (UUID, optionnel)<input id="project" autocomplete="off" placeholder="UUID"></label><label>Recherche catalogue<input id="query" placeholder="malaria"></label><label>Pays ISO3<input id="country" value="RWA"></label><label>Indicateur(s)<input id="indicator" placeholder="SH.MLR.INCD.P3"></label><label>Année / intervalle<input id="date" placeholder="2020:2025"></label></div></div>
<div id="advanced" class="panel hidden"><h3>Paramètres natifs qualifiés</h3><div class="grid"><label>source<input id="source" type="number" min="1" value="2"></label><label>page<input id="page" type="number" min="1" value="1"></label><label>per_page<input id="per_page" type="number" min="1" max="50000" value="50"></label><label>mrv<input id="mrv" type="number" min="1"></label><label>mrnev<input id="mrnev" type="number" min="1"></label><label>gapfill<select id="gapfill"><option value="false">false</option><option value="true">true</option></select></label><label>frequency<select id="frequency"><option value=""></option><option>Y</option><option>Q</option><option>M</option></select></label><label>footnote<select id="footnote"><option value="false">false</option><option value="true">true</option></select></label><label>format<select id="format"><option value="json">json</option></select></label><label>language<select id="language"><option>en</option><option>fr</option><option>es</option><option>ar</option><option>zh</option></select></label></div></div>
<div id="expert" class="panel hidden"><h3>Expert</h3><div class="actions"><button id="descriptor">Descripteur</button><button id="config">Configuration</button><button id="countries">Nomenclature géographique</button><button id="metadata">Métadonnées</button></div><pre id="expertout">Prêt.</pre></div>
<div class="panel"><div class="actions"><button id="run">Interroger</button></div><pre id="result">Aucune requête.</pre></div>
<script>const q=s=>document.querySelector(s);function cookie(n){return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}async function req(path,method='GET',body=null){const o={method,credentials:'same-origin',headers:{Accept:'application/json'}};if(body!==null){o.headers['Content-Type']='application/json';o.headers['x-hdp-csrf']=decodeURIComponent(cookie('hdp_csrf'));o.body=JSON.stringify(body)}const r=await fetch(path,o),x=await r.json();if(!r.ok)throw new Error(JSON.stringify(x.detail||x));return x}function body(){return {project_id:q('#project').value||null,country:q('#country').value,indicator:q('#indicator').value,date:q('#date').value,source:Number(q('#source').value),page:Number(q('#page').value),per_page:Number(q('#per_page').value),mrv:q('#mrv').value?Number(q('#mrv').value):null,mrnev:q('#mrnev').value?Number(q('#mrnev').value):null,gapfill:q('#gapfill').value==='true',frequency:q('#frequency').value,footnote:q('#footnote').value==='true',format:q('#format').value,language:q('#language').value}}q('#run').onclick=async()=>{try{const x=await req('/api/providers/world-bank-health/observations','POST',body());q('#result').textContent=JSON.stringify(x.items,null,2);q('#expertout').textContent=JSON.stringify({status:x.status,completeness:x.completeness,native_request:x.native_request},null,2)}catch(e){q('#result').textContent='ERREUR '+e.message}};q('#descriptor').onclick=async()=>{try{q('#expertout').textContent=JSON.stringify(await req('/api/providers/world-bank-health/descriptor'),null,2)}catch(e){q('#expertout').textContent='ERREUR '+e.message}};q('#config').onclick=async()=>{try{const id=q('#project').value;const p='/api/providers/world-bank-health/configuration/effective'+(id?'?project_id='+encodeURIComponent(id):'');q('#expertout').textContent=JSON.stringify(await req(p),null,2)}catch(e){q('#expertout').textContent='ERREUR '+e.message}};q('#countries').onclick=async()=>{try{q('#expertout').textContent=JSON.stringify(await req('/api/providers/world-bank-health/geography-vocabulary'),null,2)}catch(e){q('#expertout').textContent='ERREUR '+e.message}};q('#metadata').onclick=async()=>{try{const query=q('#query').value;if(!query)throw new Error('Saisir Recherche catalogue');const b={project_id:q('#project').value||null,query,source:Number(q('#source').value),page:Number(q('#page').value),per_page:Number(q('#per_page').value),format:q('#format').value,language:q('#language').value};q('#expertout').textContent=JSON.stringify(await req('/api/providers/world-bank-health/metadata','POST',b),null,2)}catch(e){q('#expertout').textContent='ERREUR '+e.message}};document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{const m=b.dataset.mode;q('#advanced').classList.toggle('hidden',m==='simple');q('#expert').classList.toggle('hidden',m!=='expert')});</script></main></body></html>"""
