from __future__ import annotations
import json, sys
import httpx
BASE='https://api.reliefweb.int/v2'
APPNAME='HDP_plateforme'

def get(path, params):
    r=httpx.get(BASE+path,params={'appname':APPNAME,**params},timeout=30,follow_redirects=True); r.raise_for_status(); return r.json()

def assert_envelope(x):
    assert isinstance(x,dict) and 'data' in x and 'count' in x and 'totalCount' in x

def main():
    cases=[]
    for content in ('reports','disasters','countries','jobs','training','sources','blog','book','references'):
        x=get('/'+content,{'limit':1,'profile':'full'}); assert_envelope(x); cases.append((content,x['count'],x['totalCount']))
    x=get('/reports',{'query[value]':'malaria','filter[field]':'country','filter[value]':'Rwanda','limit':5,'profile':'full','verbose':1}); assert_envelope(x); assert 'details' in x; cases.append(('malaria+rwanda',x['count'],x['totalCount']))
    x=get('/reports',{'filter[field]':'date.created','filter[value][from]':'2020-01-01T00:00:00+00:00','filter[value][to]':'2025-12-31T23:59:59+00:00','limit':1}); assert_envelope(x); cases.append(('date-range',x['count'],x['totalCount']))
    x=get('/reports',{'facets[0][field]':'theme','facets[0][limit]':10,'limit':0}); assert_envelope(x); assert 'facets' in x; cases.append(('facet-theme',x['count'],x['totalCount']))
    first=get('/reports',{'limit':1,'preset':'latest','profile':'full'}); item_id=first['data'][0]['id']; item=get('/reports/'+str(item_id),{'profile':'full'}); assert 'data' in item; cases.append(('item',1,item_id))
    print(json.dumps({'appname':APPNAME,'status':'success','cases':cases},ensure_ascii=False,indent=2))
if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'appname':APPNAME,'status':'failed','error':f'{type(exc).__name__}: {exc}'},ensure_ascii=False)); sys.exit(1)
