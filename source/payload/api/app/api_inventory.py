from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api-inventory", tags=["API inventory V6"])


@lru_cache(maxsize=1)
def inventory() -> list[dict[str, Any]]:
    """Load the versioned V6 API inventory from plain UTF-8 JSONL parts.

    JSONL is deliberately used instead of opaque compressed payloads so corruption,
    truncation and review problems are caught by normal parsing and CI.
    """
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
    return [
        row for row in inventory()
        if str(row.get("source_slug", "")).casefold() == needle
        or str(row.get("Source", "")).casefold() == needle
    ]


def operation_count(rows: list[dict[str, Any]]) -> int:
    return len({(r.get("source_slug"), r.get("Opération"), r.get("Méthode"), r.get("Endpoint")) for r in rows})


@router.get("/data")
def data(
    source: str | None = None,
    q: str | None = Query(default=None),
    supported: bool | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
):
    rows = inventory() if not source else source_rows(source)
    if supported is not None:
        rows = [r for r in rows if bool(r.get("supported")) is supported]
    if q:
        needle = q.casefold()
        keys = (
            "Source", "Opération", "Endpoint", "Méthode", "Paramètre", "Type",
            "Emplacement", "Description officielle / synthèse", "Contrôle recommandé",
            "Classe d’accès", "origin", "documentation_url",
        )
        rows = [r for r in rows if needle in " ".join(str(r.get(k, "")) for k in keys).casefold()]
    return {
        "total": len(rows),
        "offset": offset,
        "limit": limit,
        "rows": rows[offset:offset + limit],
    }


@router.get("/sources")
def sources():
    rows = inventory()
    items = []
    for slug in sorted({str(r["source_slug"]) for r in rows}):
        rs = source_rows(slug)
        items.append({
            "slug": slug,
            "name": rs[0]["Source"],
            "parameters": len(rs),
            "operations": operation_count(rs),
            "supported": sum(bool(r.get("supported")) for r in rs),
            "informational": sum(not bool(r.get("supported")) for r in rs),
            "readonly": sum(bool(r.get("readonly")) for r in rs),
        })
    return {
        "parameters": len(rows),
        "sources": len(items),
        "operations": operation_count(rows),
        "supported": sum(bool(r.get("supported")) for r in rows),
        "informational": sum(not bool(r.get("supported")) for r in rows),
        "items": items,
    }


@router.get("/source/{slug}")
def source_schema(slug: str):
    rows = source_rows(slug)
    if not rows:
        raise HTTPException(404, "Source inconnue")
    operations: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        operations.setdefault((row["Opération"], row["Endpoint"], row["Méthode"]), []).append(row)
    return {
        "source": rows[0]["Source"],
        "source_slug": rows[0]["source_slug"],
        "parameter_count": len(rows),
        "supported": sum(bool(r.get("supported")) for r in rows),
        "informational": sum(not bool(r.get("supported")) for r in rows),
        "operations": [
            {"operation": key[0], "endpoint": key[1], "method": key[2], "parameters": value}
            for key, value in sorted(operations.items())
        ],
    }


PAGE = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V6 — Inventaire API</title><style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#182230;background:#f4f6f8}body{margin:0}.top{background:#15283b;color:white;padding:18px 24px;display:flex;gap:18px;align-items:center}.top a{color:white}.wrap{padding:18px 24px}.stats{display:flex;gap:12px;flex-wrap:wrap}.card{background:white;border:1px solid #d7dde4;border-radius:9px;padding:12px 16px}.toolbar{display:grid;grid-template-columns:minmax(220px,1fr) minmax(180px,320px) minmax(150px,220px) auto;gap:10px;margin:16px 0}input,select,button{font:inherit;padding:9px;border:1px solid #aeb8c3;border-radius:6px;background:white}button{cursor:pointer;background:#163f68;color:white}.tablewrap{overflow:auto;max-height:65vh;background:white;border:1px solid #d7dde4}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #e7ebef;max-width:340px}th{position:sticky;top:0;background:#e9eef3;z-index:1}.info{background:#f6f1df}.supported{background:#edf9f1}.tag{white-space:nowrap;font-size:11px;border:1px solid #c4ccd4;border-radius:10px;padding:2px 6px}.foot{margin-top:10px;color:#53606d;font-size:13px}@media(max-width:900px){.toolbar{grid-template-columns:1fr}.wrap{padding:12px}}
</style></head><body><div class="top"><strong>HDP V6 · Inventaire des paramètres API</strong><a href="/">Retour à HDP</a></div><main class="wrap"><div class="stats"><div class="card"><b id="n">—</b><br>entrées</div><div class="card"><b id="ns">—</b><br>sources</div><div class="card"><b id="no">—</b><br>opérations</div><div class="card"><b id="sup">—</b><br>prises en charge</div><div class="card"><b id="info">—</b><br>informatives</div></div><div class="toolbar"><input id="q" placeholder="Rechercher paramètre, endpoint, description…"><select id="src"><option value="">Toutes les sources</option></select><select id="support"><option value="">Tous les paramètres</option><option value="true">Pris en charge par HDP</option><option value="false">Information / non encore mappé</option></select><button id="go">Rechercher</button></div><div class="tablewrap"><table><thead><tr><th>Source</th><th>Opération</th><th>Méthode</th><th>Endpoint</th><th>Paramètre</th><th>Emplacement</th><th>Type</th><th>Obligatoire</th><th>Contrôle UI</th><th>Accès</th><th>Origine</th><th>Description</th></tr></thead><tbody id="body"></tbody></table></div><div class="foot" id="foot"></div></main><script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function init(){const s=await fetch('/api-inventory/sources').then(r=>r.json());ns.textContent=s.sources.toLocaleString('fr-FR');no.textContent=s.operations.toLocaleString('fr-FR');sup.textContent=s.supported.toLocaleString('fr-FR');info.textContent=s.informational.toLocaleString('fr-FR');for(const x of s.items){src.insertAdjacentHTML('beforeend',`<option value="${esc(x.slug)}">${esc(x.name)} (${x.parameters})</option>`)}load();installNativeSourceInventory(s)}
async function load(){const u=new URL('/api-inventory/data',location.origin);if(src.value)u.searchParams.set('source',src.value);if(q.value)u.searchParams.set('q',q.value);if(support.value)u.searchParams.set('supported',support.value);u.searchParams.set('limit','10000');const d=await fetch(u).then(r=>r.json());n.textContent=d.total.toLocaleString('fr-FR');body.innerHTML=d.rows.map(r=>`<tr class="${r.supported?'supported':'info'}"><td>${esc(r.Source)}</td><td>${esc(r['Opération'])}</td><td><span class="tag">${esc(r['Méthode'])}</span></td><td>${esc(r.Endpoint)}</td><td><b>${esc(r['Paramètre'])}</b></td><td>${esc(r['Emplacement'])}</td><td>${esc(r.Type)}</td><td>${r['Obligatoire']?'oui':'non'}</td><td>${esc(r['Contrôle recommandé'])}</td><td>${r.supported?'modifiable/exposé':(r.sensitive?'secret':'information')}</td><td>${esc(r.origin)}</td><td>${esc(r['Description officielle / synthèse'])}</td></tr>`).join('');foot.textContent=`${d.total} entrée(s). Vert : paramètre mappé dans HDP. Beige : paramètre visible comme information mais non présenté comme exécutable tant que son adaptateur n’est pas validé.`}
function controlFor(p){const ro=!p.supported||p.readonly;const name=esc(p['Paramètre']);const id='hdp-inv-'+Math.random().toString(36).slice(2);const common=`id="${id}" data-hdp-api-parameter="${name}" data-location="${esc(p['Emplacement'])}" data-endpoint="${esc(p.Endpoint)}" ${ro?'disabled':''} ${p['Obligatoire']?'required':''}`;let c='';if(Array.isArray(p.enum)&&p.enum.length){c=`<select ${common}><option value="">— sélectionner —</option>${p.enum.map(v=>`<option value="${esc(v)}" ${String(v)===String(p.default)?'selected':''}>${esc(v)}</option>`).join('')}</select>`}else if(String(p.Type).toLowerCase().includes('bool')){c=`<label class="check"><input type="checkbox" ${common} ${p.default===true?'checked':''}> actif</label>`}else if(/integer|number|float|double/i.test(String(p.Type))){c=`<input type="number" ${common} ${p.minimum!=null?`min="${esc(p.minimum)}"`:''} ${p.maximum!=null?`max="${esc(p.maximum)}"`:''} ${p.default!=null?`value="${esc(p.default)}"`:''}>`}else{c=`<input type="text" ${common} ${p.pattern?`pattern="${esc(p.pattern)}"`:''} ${p.default!=null?`value="${esc(p.default)}"`:''} placeholder="${ro?'information seulement':'valeur du paramètre'}">`}return `<div class="item" data-inventory-parameter-row data-search="${esc([p['Paramètre'],p.Type,p['Emplacement'],p['Description officielle / synthèse'],p['Contrôle recommandé']].join(' ').toLowerCase())}"><div class="item-head"><div><h4>${name}</h4><small>${esc(p.Type)} · ${esc(p['Emplacement'])}${p['Obligatoire']?' · obligatoire':''}</small></div><span class="pill ${p.supported&&!p.readonly?'completed':''}">${p.supported&&!p.readonly?'modifiable':'information'}</span></div><label for="${id}">${esc(p['Contrôle recommandé']||'Valeur')}</label>${c}<small>${esc(p['Description officielle / synthèse']||'Aucune description fournie par la source.')}</small>${p.documentation_url?`<div class="source-links"><a href="${esc(p.documentation_url)}" target="_blank" rel="noopener">Documentation source</a></div>`:''}</div>`}
async function installNativeSourceInventory(summary){try{if(window.parent===window)return;const d=window.parent.document;const section=d.getElementById('view-source-settings');if(!section||d.getElementById('native-api-inventory-panel'))return;const panel=d.createElement('div');panel.id='native-api-inventory-panel';panel.className='card';panel.style.marginTop='16px';panel.innerHTML=`<h2>Inventaire exhaustif des paramètres API</h2><p class="intro">Interface native générée depuis l’inventaire vérifié : ${summary.parameters.toLocaleString('fr-FR')} paramètres, ${summary.sources} sources, ${summary.operations} opérations. Tous les paramètres sont visibles ; seuls ceux validés par un adaptateur HDP sont modifiables.</p><div class="filters" style="grid-template-columns:2fr 2fr 2fr"><div><label>Source</label><select id="native-inventory-source"></select></div><div><label>Opération</label><select id="native-inventory-operation"></select></div><div><label>Filtrer les paramètres</label><input id="native-inventory-filter" type="search" placeholder="nom, type, description…"></div></div><div id="native-inventory-summary" class="notice"></div><div id="native-inventory-parameters" class="list" style="max-height:720px"></div>`;section.appendChild(panel);const ss=d.getElementById('native-inventory-source');const os=d.getElementById('native-inventory-operation');const fi=d.getElementById('native-inventory-filter');const out=d.getElementById('native-inventory-parameters');const note=d.getElementById('native-inventory-summary');summary.items.forEach(x=>ss.insertAdjacentHTML('beforeend',`<option value="${esc(x.slug)}">${esc(x.name)} — ${x.parameters} paramètres / ${x.operations} opérations</option>`));let schema=null;async function sourceChanged(){schema=await fetch('/api-inventory/source/'+encodeURIComponent(ss.value)).then(r=>r.json());os.innerHTML=schema.operations.map((op,i)=>`<option value="${i}">${esc(op.method)} ${esc(op.endpoint)} — ${esc(op.operation)} (${op.parameters.length})</option>`).join('');operationChanged()}function operationChanged(){if(!schema)return;const op=schema.operations[Number(os.value)||0];if(!op){out.innerHTML='<div class="empty">Aucune opération.</div>';return}note.textContent=`${schema.source} : ${schema.parameter_count} paramètres inventoriés au total, dont ${schema.supported} mappés et ${schema.informational} informatifs. Opération affichée : ${op.method} ${op.endpoint}.`;out.innerHTML=op.parameters.map(controlFor).join('');filterRows()}function filterRows(){const needle=String(fi.value||'').trim().toLowerCase();out.querySelectorAll('[data-inventory-parameter-row]').forEach(el=>{el.style.display=!needle||String(el.dataset.search||'').includes(needle)?'':'none'})}ss.addEventListener('change',sourceChanged);os.addEventListener('change',operationChanged);fi.addEventListener('input',filterRows);await sourceChanged()}catch(err){console.error('HDP native API inventory injection failed',err)}}
go.onclick=load;q.onkeydown=e=>{if(e.key==='Enter')load()};src.onchange=load;support.onchange=load;init();
</script></body></html>'''


@router.get("", response_class=HTMLResponse)
def page() -> str:
    return PAGE
