from pathlib import Path
import sys,importlib.util,copy,json,hashlib
OUT=Path(__file__).resolve().parent;REPO=OUT.parents[2]
sys.path.insert(0,str(REPO/'tools'))
sys.path.insert(0,str(OUT))
from fixture_factory import make_fixture,seed_records

def load_candidate(path):
    path=Path(path).resolve();spec=importlib.util.spec_from_file_location('independent_quality_candidate',path)
    q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q);return q

def bound_fixture(q,root):
    b=make_fixture(q,root,record_context=False);contract=q.load(Path(root)/q.CONTRACT)
    for u in b['units']:
        branch=u['id'].split(':')[-1];node_id='plan:'+branch
        locators=[q.PLAN_CONTEXT,'#week-'+str(u['week'])]+[t['plan_locator'] for t in contract['topics'] if t['id'] in u['syllabus_ids']]
        b['dependencies'].append({'id':node_id,'revision':'fictional-plan-v1','sha256':q.file_digest(Path(root)/contract['baseline']['path']),'path':contract['baseline']['path'],'locators':locators,'depends_on':[]})
        next(n for n in b['dependencies'] if n['id']==u['id'])['depends_on'].append(node_id)
        u['plan_dependency_ids']=[node_id]
    seed_records(q,b,root)
    for r in b['reviews']:
        r['dependency_scope_fingerprint']=q.plan_bindings(b,r['object_id'],root)['scope_fingerprint']
        r['context_bindings']=q.context_bindings(b,r['object_id'],root)
    return b

def review(b,object_id='demo:a',criterion_id='K05'):
    return next(r for r in reversed(b['reviews']) if r['object_id']==object_id and r['criterion_id']==criterion_id)

def captures(q,b,root):
    return {oid:q.review_freshness(b,review(b,oid),root) for oid in ['demo:a','demo:b']}

def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
