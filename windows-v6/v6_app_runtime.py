from __future__ import annotations
import gzip, json, os, sys, threading, time, webbrowser
from pathlib import Path
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

def resource_path(name: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base / name

DATA_GZ = resource_path('api_parameters_inventory.json.gz')
HTML = resource_path('index.html').read_text(encoding='utf-8')
with gzip.open(DATA_GZ, 'rt', encoding='utf-8') as fh:
    INVENTORY: list[dict[str, Any]] = json.load(fh)
SOURCES = sorted({str(r.get('source') or r.get('Source') or '').strip() for r in INVENTORY if (r.get('source') or r.get('Source'))})

app = FastAPI(title='HDP V6 API UI', version='6.0.0')
class Preview(BaseModel):
    source: str
    values: dict[str, Any] = Field(default_factory=dict)

@app.get('/', response_class=HTMLResponse)
def root(): return HTML

@app.get('/api/health')
def health(): return {'status':'ok','version':'6.0.0','parameters':len(INVENTORY),'sources':len(SOURCES)}

@app.get('/api/sources')
def sources():
    return [{'id':s,'label':s,'parameter_count':sum(1 for r in INVENTORY if (r.get('source') or r.get('Source'))==s)} for s in SOURCES]

@app.get('/api/schema/{source}')
def schema(source: str):
    rows=[r for r in INVENTORY if str(r.get('source') or r.get('Source') or '')==source]
    if not rows: raise HTTPException(404,'Source inconnue')
    return {'source':source,'count':len(rows),'parameters':rows}

@app.post('/api/requests/preview')
def preview(p: Preview):
    rows=[r for r in INVENTORY if str(r.get('source') or r.get('Source') or '')==p.source]
    if not rows: raise HTTPException(404,'Source inconnue')
    accepted={}; blocked={}
    for k,v in p.values.items():
        row=next((r for r in rows if str(r.get('parameter') or r.get('Paramètre') or '')==k),None)
        if not row: blocked[k]='paramètre inconnu'; continue
        policy=str(row.get('policy') or row.get('Politique HDP') or '')
        access=str(row.get('access_class') or row.get("Classe d’accès") or '')
        if any(x in (policy+' '+access).casefold() for x in ('inventaire uniquement','écriture','administration','secret')):
            blocked[k]='lecture seule / non exécutable'
        else: accepted[k]=v
    return {'source':p.source,'accepted':accepted,'blocked':blocked,'input':p.values}

@app.get('/api/export/inventory.csv')
def export_csv():
    import csv, io
    keys=sorted({k for r in INVENTORY for k in r})
    buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=keys); w.writeheader(); w.writerows(INVENTORY)
    data=buf.getvalue().encode('utf-8-sig')
    return StreamingResponse(iter([data]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=HDP_V6_API_inventory.csv'})

def open_browser():
    time.sleep(1.4); webbrowser.open('http://127.0.0.1:8766/')

if __name__=='__main__':
    threading.Thread(target=open_browser,daemon=True).start()
    uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning')
