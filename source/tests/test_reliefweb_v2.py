from __future__ import annotations
import sys
import unittest
from pathlib import Path
APP_ROOT = Path(__file__).resolve().parents[1] / "payload" / "api"
sys.path.insert(0, str(APP_ROOT))
from app.reliefweb_v2 import DEFAULT_APPNAME, ReliefWebValidationError, build_payload, request_spec, resolve_appname, validate_filter

class ReliefWebV2Tests(unittest.TestCase):
    def test_default_appname(self):
        x=resolve_appname({}, {}); self.assertEqual((x.value,x.origin),(DEFAULT_APPNAME,'default'))
    def test_global_appname(self):
        x=resolve_appname({}, {'appname':'global-app'}); self.assertEqual((x.value,x.origin),('global-app','global'))
    def test_project_override(self):
        x=resolve_appname({'appname':'project-app'}, {'appname':'global-app'}); self.assertEqual((x.value,x.origin),('project-app','project'))
    def test_recursive_filter(self):
        f=validate_filter({'operator':'AND','conditions':[{'field':'country','value':'Rwanda'},{'operator':'OR','conditions':[{'field':'format','value':'Map'},{'field':'format','value':'Infographic'}]}]}); self.assertEqual(f['conditions'][1]['operator'],'OR')
    def test_filter_field_conditions_exclusive(self):
        with self.assertRaises(ReliefWebValidationError): validate_filter({'field':'country','conditions':[{'field':'theme'}]})
    def test_full_payload(self):
        p=build_payload({'query':'malaria','query_fields':['title^5','body'],'query_operator':'AND','filter':{'field':'country','value':'Rwanda'},'facets':[{'field':'theme','limit':20,'sort':'count:desc','scope':'query'}],'limit':25,'offset':0,'sort':['date.created:desc'],'profile':'full','preset':'latest','fields_include':['title','country','source'],'fields_exclude':['body-html'],'slim':True,'verbose':True})
        self.assertEqual(p['query']['operator'],'AND'); self.assertEqual(p['facets'][0]['scope'],'query'); self.assertEqual(p['slim'],1); self.assertEqual(p['verbose'],1)
    def test_limit_contract(self):
        with self.assertRaises(ReliefWebValidationError): build_payload({'limit':1001})
    def test_complex_request_uses_post(self):
        r=request_spec('reports',{'filter':{'operator':'AND','conditions':[{'field':'country','value':'Rwanda'},{'field':'theme','value':'Health'}]}},global_settings={}); self.assertEqual(r['method'],'POST'); self.assertEqual(r['appname'],DEFAULT_APPNAME)
    def test_simple_request_uses_get(self): self.assertEqual(request_spec('reports',{'query':'malaria','limit':10})['method'],'GET')
    def test_item_only_profile_fields(self):
        r=request_spec('reports',{'query':'ignored','profile':'full','fields_include':['source.name']},item_id=1082221); self.assertNotIn('query',r['payload']); self.assertEqual(r['method'],'GET')
    def test_nine_content_types(self):
        for c in ('reports','disasters','countries','jobs','training','sources','blog','book','references'): self.assertIn('/'+c,request_spec(c,{'limit':1})['url'])
if __name__ == '__main__': unittest.main()
