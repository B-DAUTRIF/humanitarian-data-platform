from __future__ import annotations
import base64,gzip,json
from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter,HTTPException
from fastapi.responses import HTMLResponse
router=APIRouter(tags=['V6 API inventory']); CATALOG=Path(__file__).with_name('operations.json.gz.b64')
@lru_cache(maxsize=1)
def catalog():
 raw=base64.b64decode(''.join(CATALOG.read_text(encoding='utf-8').split())); return json.loads(gzip.decompress(raw).decode('utf-8'))
def sources():
 out={}
 for op in catalog().get('operations',[]):
  k=op.get('source_slug') or op.get('source'); x=out.setdefault(k,{'slug':k,'name':op.get('source') or k,'operations':0,'parameters':0}); x['operations']+=1; x['parameters']+=len(op.get('parameters') or [])
 return sorted(out.values(),key=lambda x:x['name'])
@router.get('/api/v6/inventory/summary')
def summary():
 s=sources(); return {'version':'6.0.0','sources':len(s),'operations':sum(x['operations'] for x in s),'parameters':sum(x['parameters'] for x in s),'by_source':s}
@router.get('/api/v6/inventory/operations')
def operations(source:str|None=None):
 o=catalog().get('operations',[])
 if source: o=[x for x in o if source.casefold() in str(x.get('source_slug','')).casefold() or source.casefold() in str(x.get('source','')).casefold()]
 return o
@router.get('/api/v6/inventory/operations/{operation_id:path}')
def operation(operation_id:str):
 for x in catalog().get('operations',[]):
  if str(x.get('id'))==operation_id:return x
 raise HTTPException(404,'Operation API inconnue')
@router.get('/api-inventory',response_class=HTMLResponse)
def page(): return HTMLResponse(PAGE)
PAGE='''<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>HDP V6 - Inventaire API</title><style>body{font:14px Segoe UI,Arial;margin:0;background:#f5f7fb;color:#172033}header{background:#172033;color:#fff;padding:20px}nav{padding:12px 20px;background:#fff;position:sticky;top:0}input,select{padding:9px;margin-right:8px}input{width:55%}main{padding:20px}.op{background:#fff;border:1px solid #ccd5df;border-radius:8px;margin:9px 0}.op summary{padding:11px;cursor:pointer;font-weight:600}.p{padding:10px;overflow:auto}table{border-collapse:collapse;width:100%}th,td{padding:7px;border-bottom:1px solid #e5e9ef;text-align:left;vertical-align:top}small{color:#64748b}</style></head><body><header><h1>Inventaire API — HDP V6</h1><div id="stats">Chargement…</div></header><nav><input id="q" placeholder="Source, opération, endpoint, paramètre…"><select id="src"><option value="">Toutes les sources</option></select></nav><main id="out"></main><script>let ops=[];const E=s=>String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));async function boot(){let s=await fetch('/api/v6/inventory/summary').then(r=>r.json());ops=await fetch('/api/v6/inventory/operations').then(r=>r.json());stats.textContent=`${s.sources} sources · ${s.operations} opérations · ${s.parameters} paramètres`;src.innerHTML+=[...s.by_source].map(x=>`<option value="${E(x.slug)}">${E(x.name)} (${x.operations}/${x.parameters})</option>`).join('');render()}function render(){let z=q.value.toLowerCase(),v=src.value;let a=ops.filter(o=>(!v||o.source_slug===v)&&(!z||JSON.stringify(o).toLowerCase().includes(z)));out.innerHTML=a.map(o=>`<details class="op"><summary>${E(o.source)} — ${E(o.operation||o.id)}<br><small>${E((o.methods||[]).join(', '))} ${E(o.endpoint)} · ${(o.parameters||[]).length} paramètre(s)</small></summary><div class="p"><table><tr><th>Paramètre</th><th>Emplacement</th><th>Type</th><th>Obligatoire</th><th>Défaut / valeurs</th><th>Description / UI</th></tr>${(o.parameters||[]).map(p=>`<tr><td><b>${E(p.name)}</b></td><td>${E(p.location)}</td><td>${E(p.type)}</td><td>${E(p.required)}</td><td>${E(p.default||p.allowed_values||p.options||'')}</td><td>${E(p.description||'')}<br><small>UI: ${E(p.ui_control||p.widget||'automatique')}</small></td></tr>`).join('')}</table></div></details>`).join('')||'<p>Aucun résultat.</p>'}q.oninput=render;src.onchange=render;boot().catch(e=>stats.textContent='Erreur: '+e.message)</script></body></html>'''
