from __future__ import annotations

"""Safe semantic-router UI.

The original V7 page serialized the hidden project text field in every mode. Browser
form restoration/autofill or a user mistaking that field for geography could therefore
send values such as ``rwanda`` as ``project_id`` and trigger a Pydantic UUID error.
This page makes project context explicit and validates it before any request.
"""

import html

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .health_sources import SEARCHABLE_SOURCE_IDS
from .v6_semantic_api import DEFAULT_PROJECT_ID

router = APIRouter(tags=["semantic-router-ui"])


@router.get("/api/semantic/ui", response_class=HTMLResponse, include_in_schema=False)
def semantic_router_ui_safe() -> str:
    source_boxes = "".join(
        f'<label class="src"><input type="checkbox" name="source" value="{html.escape(source)}" checked> {html.escape(source)}</label>'
        for source in SEARCHABLE_SOURCE_IDS
    )
    default_project = str(DEFAULT_PROJECT_ID)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HDP V7 — Routeur sémantique</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f5f7fa;color:#172033}}header{{background:#172033;color:white;padding:18px 24px}}main{{max-width:1500px;margin:auto;padding:20px}}.tabs,.actions{{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}}button{{cursor:pointer}}input,button{{font:inherit;padding:8px;border:1px solid #b8c0cc;border-radius:6px;box-sizing:border-box}}.grid{{display:grid;grid-template-columns:2fr 2fr 1fr 1fr 100px;gap:10px}}.sources{{display:flex;flex-wrap:wrap;gap:8px 16px;background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px;margin:12px 0}}.src input{{width:auto}}.panel{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:14px;margin:10px 0}}.hidden{{display:none}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px}}.card{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:12px}}.error{{color:#991b1b;font-weight:600}}pre{{white-space:pre-wrap;overflow:auto;max-height:600px;background:#111827;color:#e5e7eb;padding:14px;border-radius:8px}}code{{word-break:break-all}}@media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>HDP V7 — Routeur sémantique</h1><div>Intention canonique → projet → traduction fournisseur → requête native → provenance.</div></header><main>
<div class="tabs"><button type="button" data-mode="simple">Simple</button><button type="button" data-mode="advanced">Avancé</button><button type="button" data-mode="expert">Expert</button></div>
<div class="panel"><div class="grid"><input id="query" name="hdp_semantic_query" autocomplete="off" placeholder="Thème, ex. paludisme"><input id="location" name="hdp_semantic_location" autocomplete="off" placeholder="Pays, ISO3 ou M49, ex. Rwanda"><input id="date_from" type="date"><input id="date_to" type="date"><input id="limit" type="number" min="1" max="100" value="25"></div><div class="sources">{source_boxes}</div><div class="actions"><button type="button" id="plan">Prévisualiser</button><button type="button" id="run">Exécuter</button><button type="button" onclick="location.href='/'">Retour HDP</button></div><div id="form-error" class="error" aria-live="polite"></div></div>
<div id="advanced" class="panel hidden"><strong>Contexte projet</strong><p>UUID du projet HDP : <input id="project_id" name="hdp_project_uuid" value="{default_project}" size="38" autocomplete="off" autocapitalize="off" spellcheck="false" pattern="[0-9a-fA-F-]{{36}}">. <strong>Un pays comme Rwanda doit être saisi dans le champ Pays/ISO3/M49 ci-dessus, jamais ici.</strong></p><div id="coverage"></div></div>
<div id="expert" class="panel hidden"><strong>Expert</strong><p>Plan, paramètres natifs, complétude, preuves, empreintes et erreurs.</p><pre id="output">Prêt.</pre></div>
<div id="fingerprints" class="panel"></div><div id="summary" class="cards"></div>
<script>
const DEFAULT_PROJECT_ID={default_project!r};
const q=s=>document.querySelector(s);let mode='simple';
function cookie(n){{return document.cookie.split(';').map(x=>x.trim()).find(x=>x.startsWith(n+'='))?.slice(n.length+1)||''}}
function validUuid(v){{return /^[0-9a-f]{{8}}-[0-9a-f]{{4}}-[1-5][0-9a-f]{{3}}-[89ab][0-9a-f]{{3}}-[0-9a-f]{{12}}$/i.test(String(v||'').trim())}}
function payload(){{
  const projectValue=mode==='simple'?DEFAULT_PROJECT_ID:String(q('#project_id').value||'').trim();
  if(!validUuid(projectValue)) throw new Error('Identifiant projet invalide : utilisez un UUID HDP. Saisissez le pays dans « Pays, ISO3 ou M49 ».');
  const sources=[...document.querySelectorAll('input[name=source]:checked')].map(x=>x.value);
  if(!sources.length) throw new Error('Sélectionnez au moins une source.');
  return {{project_id:projectValue,sources,query:q('#query').value,location:q('#location').value,date_from:q('#date_from').value,date_to:q('#date_to').value,result_limit:Number(q('#limit').value||25)}};
}}
function esc(v){{return String(v??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}}[c]))}}
function render(x){{const p=x.plan||x,geo=p.intent?.geography;let cards=[`<div class="card"><b>Interprétation</b><br>${{esc(p.intent?.interpretation)}}<br>${{geo?esc(geo.name)+' · '+esc(geo.iso3)+' · M49 '+esc(geo.m49):'géographie non résolue'}}<br>concept=${{esc(p.intent?.canonical_keywords||p.intent?.keywords)}}<br>projet=${{esc(p.project_context?.project_id||x.project_id||'')}}</div>`];for(const e of (x.sources||p.routes||[])){{const r=e.route||e;cards.push(`<div class="card"><b>${{esc(r.source)}}</b><br>opération=${{esc(r.operation)}}<br>exécutable=${{esc(r.executable)}}<br>projet actif=${{esc(r.project_enabled)}}<br>complétude=${{esc(e.completeness||r.completeness)}}${{e.status?'<br><b>statut='+esc(e.status)+'</b>':''}}${{e.item_count!==undefined?'<br>résultats='+esc(e.item_count):''}}</div>`)}}q('#summary').innerHTML=cards.join('');q('#fingerprints').innerHTML=`<b>query_fingerprint</b> <code>${{esc(p.query_fingerprint||'')}}</code>${{x.result_snapshot_hash?'<br><b>result_snapshot_hash</b> <code>'+esc(x.result_snapshot_hash)+'</code>':''}}`;q('#coverage').textContent=(p.routes||[]).map(r=>`${{r.source}}: ${{r.operation}} / ${{r.completeness}} / project=${{r.project_enabled}}`).join(' · ');q('#output').textContent=JSON.stringify(x,null,2)}}
async function call(path){{q('#form-error').textContent='';let body;try{{body=payload()}}catch(e){{q('#form-error').textContent=e.message;q('#output').textContent='ERREUR '+e.message;return}}q('#output').textContent='Exécution…';const r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json','x-hdp-csrf':decodeURIComponent(cookie('hdp_csrf'))}},credentials:'same-origin',body:JSON.stringify(body)}});const x=await r.json();if(r.ok)render(x);else q('#output').textContent='ERREUR '+JSON.stringify(x);if(!r.ok)throw new Error(x.detail||('HTTP '+r.status))}}
q('#plan').onclick=()=>call('/api/semantic/plan').catch(e=>q('#form-error').textContent=String(e.message||e));q('#run').onclick=()=>call('/api/semantic/search').catch(e=>q('#form-error').textContent=String(e.message||e));document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{{mode=b.dataset.mode;q('#advanced').classList.toggle('hidden',mode==='simple');q('#expert').classList.toggle('hidden',mode!=='expert')}});
</script></main></body></html>"""
