from __future__ import annotations
import csv, io, json, sys, threading, time, webbrowser
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from inventory_blob import ROWS
import uvicorn

def resource_path(name: str) -> Path:
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / name
HTML = resource_path('index.html').read_text(encoding='utf-8')
app = FastAPI(title='HDP V6 — API Parameter UI', version='6.0.0-api-ui')

class PreviewRequest(BaseModel):
    source: str
    operation: str | None = None
    endpoint: str | None = None
    values: dict[str, Any] = {}

def _source_rows(source: str) -> list[dict[str, Any]]:
    s=source.strip().lower()
    return [r for r in ROWS if r['source_slug']==s or r['Source'].lower()==s]

def _truthy(v: Any) -> bool:
    return v is True or str(v).lower() in {'1','true','yes','oui','on'}

def serialize_parameter(row: dict[str, Any], value: Any) -> Any:
    typ=(row.get('Type') or '').lower()
    if row.get('widget')=='checkbox': return bool(_truthy(value))
    if 'integer' in typ: return int(value)
    if any(t in typ for t in ('number','float','double','decimal')): return float(value)
    if 'array' in typ:
        return value if isinstance(value,list) else [x.strip() for x in str(value).split(',') if x.strip()]
    if row.get('widget')=='json': return value if isinstance(value,(dict,list)) else json.loads(value)
    return value

@app.get('/', response_class=HTMLResponse)
def home() -> str: return HTML
@app.get('/api/sources')
def sources():
    out=[]
    for slug in sorted({r['source_slug'] for r in ROWS}):
        rs=_source_rows(slug)
        out.append({'slug':slug,'name':rs[0]['Source'],'parameters':len(rs),'operations':len({(r['Opération'],r['Endpoint'],r['Méthode']) for r in rs}),'active':sum(not r.get('readonly',False) for r in rs),'readonly':sum(bool(r.get('readonly',False)) for r in rs)})
    return out
@app.get('/api/schema/{source}')
def schema(source: str, operation: str|None=None, q: str|None=Query(default=None)):
    rows=_source_rows(source)
    if not rows: raise HTTPException(404,'Source inconnue')
    if operation: rows=[r for r in rows if r['Opération']==operation]
    if q:
        n=q.lower(); rows=[r for r in rows if n in ' '.join(str(r.get(k,'')) for k in ('Paramètre','Description officielle / synthèse','Endpoint','Opération')).lower()]
    ops={}
    for r in rows: ops.setdefault((r['Opération'],r['Endpoint'],r['Méthode']),[]).append(r)
    return {'source':rows[0]['Source'] if rows else source,'source_slug':source,'parameter_count':len(rows),'operations':[{'operation':k[0],'endpoint':k[1],'method':k[2],'parameters':v} for k,v in sorted(ops.items(),key=lambda kv:(kv[0][0],kv[0][1],kv[0][2]))]}
@app.post('/api/requests/preview')
def preview(body: PreviewRequest):
    rows=_source_rows(body.source)
    if body.operation: rows=[r for r in rows if r['Opération']==body.operation]
    if body.endpoint: rows=[r for r in rows if r['Endpoint']==body.endpoint]
    by_name={}
    for r in rows: by_name.setdefault(r['Paramètre'],r)
    query_params={}; path_params={}; body_params={}; ignored={}
    for name,value in body.values.items():
        row=by_name.get(name)
        if not row: ignored[name]='paramètre absent de l’opération'; continue
        if row.get('readonly'): ignored[name]='lecture seule / désactivé par politique HDP'; continue
        if value in ('',None,[],{}): continue
        try: v=serialize_parameter(row,value)
        except Exception as exc: raise HTTPException(422,f'{name}: {exc}') from exc
        loc=(row.get('Emplacement') or '').lower()
        if 'path' in loc and 'query' not in loc: path_params[name]=v
        elif 'json' in loc or 'body' in loc or 'form' in loc: body_params[name]=v
        else: query_params[name]=v
    return {'source':body.source,'operation':body.operation,'method':rows[0]['Méthode'] if rows else 'GET','endpoint':body.endpoint or (rows[0]['Endpoint'] if rows else ''),'input':body.values,'serialized':{'path':path_params,'query':query_params,'body':body_params},'ignored':ignored,'output_contract':{'raw':'Réponse fournisseur conservable en JSON/binaire selon le connecteur','tabular':['CSV','XLSX'],'metadata':['source','operation','endpoint','parameters','retrieved_at','status_code']}}
@app.get('/api/export/inventory.csv')
def export_inventory_csv(source: str|None=None):
    rows=ROWS if not source else _source_rows(source)
    if not rows: raise HTTPException(404,'Aucune ligne')
    buf=io.StringIO(); keys=list(rows[0].keys()); w=csv.DictWriter(buf,fieldnames=keys); w.writeheader(); w.writerows(rows)
    data=buf.getvalue().encode('utf-8-sig')
    return StreamingResponse(io.BytesIO(data),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="hdp_api_parameters.csv"'})
@app.get('/api/health')
def health(): return {'status':'ok','version':'6.0.0-api-ui','parameters':len(ROWS),'sources':len({r['source_slug'] for r in ROWS})}

def open_browser(): time.sleep(1.4); webbrowser.open('http://127.0.0.1:8766/')
if __name__=='__main__':
    threading.Thread(target=open_browser,daemon=True).start()
    uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning')
