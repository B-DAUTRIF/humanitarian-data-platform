from __future__ import annotations

import base64
import json
import lzma
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api-inventory", tags=["API inventory V6"])

@lru_cache(maxsize=1)
def inventory() -> list[dict[str, Any]]:
    parts = Path(__file__).with_name("api_inventory_parts")
    encoded = "".join(p.read_text(encoding="ascii") for p in sorted(parts.glob("part*.txt")))
    rows = json.loads(lzma.decompress(base64.b85decode(encoded.encode("ascii"))).decode("utf-8"))
    if not isinstance(rows, list) or len(rows) != 2057:
        raise RuntimeError(f"Inventaire API V6 invalide: {len(rows) if isinstance(rows, list) else 'type'}")
    return rows

def source_rows(slug: str) -> list[dict[str, Any]]:
    s = slug.strip().lower()
    return [r for r in inventory() if r.get("source_slug", "").lower() == s or r.get("Source", "").lower() == s]

@router.get("/data")
def data(source: str | None = None, q: str | None = Query(default=None), limit: int = Query(default=250, ge=1, le=2057), offset: int = Query(default=0, ge=0)):
    rows = inventory() if not source else source_rows(source)
    if q:
        needle = q.casefold()
        keys = ("Source", "Opération", "Endpoint", "Méthode", "Paramètre", "Type", "Emplacement", "Description officielle / synthèse", "Catégorie UI")
        rows = [r for r in rows if needle in " ".join(str(r.get(k, "")) for k in keys).casefold()]
    return {"total": len(rows), "offset": offset, "limit": limit, "rows": rows[offset:offset + limit]}

@router.get("/sources")
def sources():
    rows = inventory(); out = []
    for slug in sorted({r["source_slug"] for r in rows}):
        rs = source_rows(slug)
        out.append({"slug": slug, "name": rs[0]["Source"], "parameters": len(rs), "operations": len({(r["Opération"], r["Endpoint"], r["Méthode"]) for r in rs}), "readonly": sum(bool(r.get("readonly")) for r in rs)})
    return {"parameters": len(rows), "sources": len(out), "items": out}

@router.get("/source/{slug}")
def source_schema(slug: str):
    rows = source_rows(slug)
    if not rows: raise HTTPException(404, "Source inconnue")
    ops: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for r in rows: ops.setdefault((r["Opération"], r["Endpoint"], r["Méthode"]), []).append(r)
    return {"source": rows[0]["Source"], "source_slug": slug, "parameter_count": len(rows), "operations": [{"operation": k[0], "endpoint": k[1], "method": k[2], "parameters": v} for k, v in sorted(ops.items())]}

PAGE = r'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V6 — Inventaire API</title><style>
:root{font-family:system-ui,Segoe UI,sans-serif;color:#182230;background:#f4f6f8}body{margin:0}.top{background:#15283b;color:white;padding:18px 24px;display:flex;gap:18px;align-items:center}.top a{color:white}.wrap{padding:18px 24px}.stats{display:flex;gap:12px;flex-wrap:wrap}.card{background:white;border:1px solid #d7dde4;border-radius:9px;padding:12px 16px}.toolbar{display:grid;grid-template-columns:minmax(220px,1fr) minmax(180px,320px) auto;gap:10px;margin:16px 0}input,select,button{font:inherit;padding:9px;border:1px solid #aeb8c3;border-radius:6px;background:white}button{cursor:pointer;background:#163f68;color:white}.tablewrap{overflow:auto;max-height:65vh;background:white;border:1px solid #d7dde4}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;vertical-align:top;padding:8px;border-bottom:1px solid #e7ebef;max-width:340px}th{position:sticky;top:0;background:#e9eef3;z-index:1}.ro{background:#f6f1df}.tag{white-space:nowrap;font-size:11px;border:1px solid #c4ccd4;border-radius:10px;padding:2px 6px}.foot{margin-top:10px;color:#53606d;font-size:13px}@media(max-width:760px){.toolbar{grid-template-columns:1fr}.wrap{padding:12px}}
</style></head><body><div class="top"><strong>HDP V6 · Inventaire exhaustif des API</strong><a href="/">Retour à HDP</a></div><main class="wrap"><div class="stats"><div class="card"><b id="n">2 057</b><br>paramètres</div><div class="card"><b>10</b><br>sources</div><div class="card"><b>440</b><br>opérations cataloguées</div></div><div class="toolbar"><input id="q" placeholder="Rechercher paramètre, endpoint, description…"><select id="src"><option value="">Toutes les sources</option></select><button id="go">Rechercher</button></div><div class="tablewrap"><table><thead><tr><th>Source</th><th>Opération</th><th>Méthode</th><th>Endpoint</th><th>Paramètre</th><th>Emplacement</th><th>Type</th><th>Obligatoire</th><th>Contrôle UI</th><th>Accès</th><th>Description</th></tr></thead><tbody id="body"></tbody></table></div><div class="foot" id="foot"></div></main><script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function init(){let s=await fetch('/api-inventory/sources').then(r=>r.json());for(const x of s.items){src.insertAdjacentHTML('beforeend',`<option value="${esc(x.slug)}">${esc(x.name)} (${x.parameters})</option>`)}load()}
async function load(){let u=new URL('/api-inventory/data',location.origin);if(src.value)u.searchParams.set('source',src.value);if(q.value)u.searchParams.set('q',q.value);u.searchParams.set('limit','2057');let d=await fetch(u).then(r=>r.json());n.textContent=d.total.toLocaleString('fr-FR');body.innerHTML=d.rows.map(r=>`<tr class="${r.readonly?'ro':''}"><td>${esc(r.Source)}</td><td>${esc(r['Opération'])}</td><td><span class="tag">${esc(r['Méthode'])}</span></td><td>${esc(r.Endpoint)}</td><td><b>${esc(r['Paramètre'])}</b></td><td>${esc(r['Emplacement'])}</td><td>${esc(r.Type)}</td><td>${esc(r['Obligatoire'])}</td><td>${esc(r['Contrôle recommandé']||r.widget)}</td><td>${r.readonly?'Lecture seule':esc(r['Classe d’accès'])}</td><td>${esc(r['Description officielle / synthèse'])}</td></tr>`).join('');foot.textContent=`${d.total} paramètre(s) affiché(s). Les champs en fond beige sont exposés à titre informatif/lecture seule selon la politique HDP.`}
go.onclick=load;q.onkeydown=e=>{if(e.key==='Enter')load()};src.onchange=load;init();
</script></body></html>'''

@router.get("", response_class=HTMLResponse)
def page() -> str:
    return PAGE
