from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, Response

router = APIRouter(prefix="/api-inventory", tags=["API inventory V6"])


@lru_cache(maxsize=1)
def inventory() -> list[dict[str, Any]]:
    parts = Path(__file__).with_name("api_inventory_parts")
    files = sorted(parts.glob("part*.jsonl"))
    if not files:
        raise RuntimeError("Inventaire API V6 absent : exécuter tools/build_v6_inventory.py")
    rows: list[dict[str, Any]] = []
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Inventaire API V6 corrompu: {path.name}:{line_number}") from exc
                if not isinstance(row, dict):
                    raise RuntimeError(f"Inventaire API V6 invalide: {path.name}:{line_number}")
                rows.append(row)
    if not rows:
        raise RuntimeError("Inventaire API V6 vide")
    required = {"Source", "source_slug", "Opération", "Méthode", "Endpoint", "Paramètre", "Emplacement", "Type"}
    for index, row in enumerate(rows):
        missing = required - set(row)
        if missing:
            raise RuntimeError(f"Inventaire API V6 ligne {index + 1}: champs absents {sorted(missing)}")
    return rows


def source_rows(slug: str) -> list[dict[str, Any]]:
    needle = slug.strip().casefold()
    return [row for row in inventory() if str(row.get("source_slug", "")).casefold() == needle or str(row.get("Source", "")).casefold() == needle]


def operation_count(rows: list[dict[str, Any]]) -> int:
    return len({(r.get("source_slug"), r.get("Opération"), r.get("Méthode"), r.get("Endpoint")) for r in rows})


def provenance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    origins = sorted({str(r.get("origin") or "inconnu") for r in rows})
    docs = sorted({str(r.get("documentation_url") or "") for r in rows if r.get("documentation_url")})
    machine = any("openapi" in o.casefold() or "swagger" in o.casefold() for o in origins)
    return {"origins": origins, "documentation_urls": docs, "machine_verified": machine}


@router.get("/data")
def data(source: str | None = None, q: str | None = Query(default=None), supported: bool | None = Query(default=None), limit: int = Query(default=500, ge=1, le=10000), offset: int = Query(default=0, ge=0)):
    rows = inventory() if not source else source_rows(source)
    if supported is not None:
        rows = [r for r in rows if bool(r.get("supported")) is supported]
    if q:
        needle = q.casefold()
        keys = ("Source", "Opération", "Endpoint", "Méthode", "Paramètre", "Type", "Emplacement", "Description officielle / synthèse", "Contrôle recommandé", "Classe d’accès", "origin", "documentation_url")
        rows = [r for r in rows if needle in " ".join(str(r.get(k, "")) for k in keys).casefold()]
    return {"total": len(rows), "offset": offset, "limit": limit, "rows": rows[offset:offset + limit]}


@router.get("/sources")
def sources():
    rows = inventory()
    items = []
    for slug in sorted({str(r["source_slug"]) for r in rows}):
        rs = source_rows(slug)
        items.append({"slug": slug, "name": rs[0]["Source"], "parameters": len(rs), "operations": operation_count(rs), "supported": sum(bool(r.get("supported")) for r in rs), "informational": sum(not bool(r.get("supported")) for r in rs), "readonly": sum(bool(r.get("readonly")) for r in rs), **provenance(rs)})
    return {"parameters": len(rows), "sources": len(items), "operations": operation_count(rows), "supported": sum(bool(r.get("supported")) for r in rows), "informational": sum(not bool(r.get("supported")) for r in rows), "items": items}


@router.get("/source/{slug}")
def source_schema(slug: str):
    rows = source_rows(slug)
    if not rows:
        raise HTTPException(404, "Source inconnue")
    operations: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        operations.setdefault((row["Opération"], row["Endpoint"], row["Méthode"]), []).append(row)
    return {"source": rows[0]["Source"], "source_slug": rows[0]["source_slug"], "parameter_count": len(rows), "supported": sum(bool(r.get("supported")) for r in rows), "informational": sum(not bool(r.get("supported")) for r in rows), **provenance(rows), "operations": [{"operation": key[0], "endpoint": key[1], "method": key[2], "parameters": value} for key, value in sorted(operations.items())]}


NATIVE_JS = r'''
(()=>{
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function field(p){const editable=!!p.supported&&!p.readonly&&!p.sensitive;const id='inv-'+Math.random().toString(36).slice(2);const attrs=`id="${id}" data-api-param="${esc(p['Paramètre'])}" data-api-endpoint="${esc(p.Endpoint)}" data-api-location="${esc(p['Emplacement'])}" ${editable?'':'disabled'} ${p['Obligatoire']?'required':''}`;let x;if(Array.isArray(p.enum)&&p.enum.length)x=`<select ${attrs}><option value="">— sélectionner —</option>${p.enum.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}</select>`;else if(/bool/i.test(String(p.Type)))x=`<label class="check"><input type="checkbox" ${attrs}> actif</label>`;else if(/integer|number|float|double/i.test(String(p.Type)))x=`<input type="number" ${attrs} ${p.minimum!=null?`min="${esc(p.minimum)}"`:''} ${p.maximum!=null?`max="${esc(p.maximum)}"`:''}>`;else x=`<input type="text" ${attrs} ${p.pattern?`pattern="${esc(p.pattern)}"`:''}>`;return `<div class="item" data-inventory-param data-filter="${esc([p['Paramètre'],p.Type,p['Emplacement'],p['Description officielle / synthèse']].join(' ').toLowerCase())}"><div class="item-head"><div><h4>${esc(p['Paramètre'])}</h4><small>${esc(p.Type)} · ${esc(p['Emplacement'])}${p['Obligatoire']?' · obligatoire':''}</small></div><span class="pill ${editable?'completed':''}">${editable?'modifiable':'information'}</span></div><label for="${id}">${esc(p['Contrôle recommandé']||'Valeur')}</label>${x}<small>${esc(p['Description officielle / synthèse']||'Aucune description officielle disponible.')}</small>${p.documentation_url?`<div class="source-links"><a href="${esc(p.documentation_url)}" target="_blank" rel="noopener">Documentation officielle</a></div>`:''}</div>`}
async function boot(){const section=document.getElementById('view-source-settings');if(!section||document.getElementById('native-api-inventory-panel'))return;const summary=await fetch('/api-inventory/sources').then(r=>{if(!r.ok)throw Error('inventaire '+r.status);return r.json()});const panel=document.createElement('div');panel.id='native-api-inventory-panel';panel.className='card';panel.style.marginTop='16px';panel.innerHTML=`<h2>Inventaire exhaustif des paramètres API</h2><p class="intro">${summary.parameters.toLocaleString('fr-FR')} paramètres · ${summary.sources} sources · ${summary.operations} opérations. Tous sont visibles. Les paramètres non validés restent informatifs afin de ne jamais simuler une prise en charge inexistante.</p><div class="filters" style="grid-template-columns:2fr 2fr 2fr"><div><label>Source</label><select id="inv-source"></select></div><div><label>Opération / endpoint</label><select id="inv-operation"></select></div><div><label>Filtrer</label><input id="inv-filter" type="search" placeholder="nom, type, description…"></div></div><div id="inv-provenance" class="notice"></div><div id="inv-params" class="list" style="max-height:760px"></div>`;section.appendChild(panel);const ss=document.getElementById('inv-source'),os=document.getElementById('inv-operation'),fi=document.getElementById('inv-filter'),out=document.getElementById('inv-params'),note=document.getElementById('inv-provenance');summary.items.forEach(x=>ss.insertAdjacentHTML('beforeend',`<option value="${esc(x.slug)}">${esc(x.name)} — ${x.parameters} paramètres</option>`));let schema;async function changeSource(){schema=await fetch('/api-inventory/source/'+encodeURIComponent(ss.value)).then(r=>r.json());os.innerHTML=schema.operations.map((o,i)=>`<option value="${i}">${esc(o.method)} ${esc(o.endpoint)} — ${o.parameters.length}</option>`).join('');changeOperation()}function changeOperation(){const o=schema?.operations?.[Number(os.value)||0];if(!o)return;note.innerHTML=`<strong>${esc(schema.source)}</strong> · ${schema.parameter_count} paramètres · ${schema.supported} mappés · ${schema.informational} informatifs · qualification machine : <strong>${schema.machine_verified?'oui':'non'}</strong><br><small>Origine : ${esc(schema.origins.join(' ; '))}</small>`;out.innerHTML=o.parameters.map(field).join('');applyFilter()}function applyFilter(){const n=String(fi.value||'').trim().toLowerCase();out.querySelectorAll('[data-inventory-param]').forEach(e=>e.style.display=!n||String(e.dataset.filter||'').includes(n)?'':'none')}ss.onchange=changeSource;os.onchange=changeOperation;fi.oninput=applyFilter;await changeSource()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>boot().catch(console.error));else boot().catch(console.error);
})();
'''


@router.get("/native.js")
def native_js() -> Response:
    return Response(NATIVE_JS, media_type="application/javascript")


PAGE = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V6 — Inventaire API</title><style>body{font-family:system-ui;margin:20px;background:#f4f6f8;color:#182230}table{border-collapse:collapse;width:100%;background:white;font-size:13px}th,td{padding:8px;border:1px solid #d7dde4;text-align:left;vertical-align:top}input,select,button{padding:8px;margin:4px}</style></head><body><h1>Inventaire des paramètres API</h1><p><a href="/">Retour HDP</a></p><input id="q" placeholder="Rechercher"><select id="src"><option value="">Toutes les sources</option></select><button id="go">Rechercher</button><p id="stats"></p><table><thead><tr><th>Source</th><th>Opération</th><th>Endpoint</th><th>Paramètre</th><th>Type</th><th>Accès</th><th>Origine</th><th>Description</th></tr></thead><tbody id="body"></tbody></table><script>const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));async function load(){let u=new URL('/api-inventory/data',location.origin);if(src.value)u.searchParams.set('source',src.value);if(q.value)u.searchParams.set('q',q.value);u.searchParams.set('limit','10000');let d=await fetch(u).then(r=>r.json());stats.textContent=d.total+' paramètres';body.innerHTML=d.rows.map(r=>`<tr><td>${esc(r.Source)}</td><td>${esc(r['Opération'])}</td><td>${esc(r.Endpoint)}</td><td>${esc(r['Paramètre'])}</td><td>${esc(r.Type)}</td><td>${r.supported&&!r.readonly?'modifiable':'information'}</td><td>${esc(r.origin)}</td><td>${esc(r['Description officielle / synthèse'])}</td></tr>`).join('')}async function init(){let s=await fetch('/api-inventory/sources').then(r=>r.json());s.items.forEach(x=>src.insertAdjacentHTML('beforeend',`<option value="${esc(x.slug)}">${esc(x.name)}</option>`));load()}go.onclick=load;src.onchange=load;q.onkeydown=e=>{if(e.key==='Enter')load()};init()</script></body></html>'''


@router.get("", response_class=HTMLResponse)
def page() -> str:
    return PAGE
