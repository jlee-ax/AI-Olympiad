"""Actual CLI/API joins with explicit fictional declarations, plus immutable old real bundles."""
from pathlib import Path
import copy,hashlib,json,sys,subprocess,importlib.util
from candidate_support import OUT,REPO,bound_fixture,load_candidate,review,write_json
expected='03f24f7e9b89979e30facf258f8c8f9f358b1aca2de876a1adae5e058f0fc96b'
assert hashlib.sha256((REPO/'tools/quality.py').read_bytes()).hexdigest()==expected
chain=OUT/'inputs/v4-tools';chain.mkdir(exist_ok=False)
for name in ['quality.py','workflow.py','review_preflight.py','contest_depth.py','discovery_loop.py','graph_paths.py','validate.py']:(chain/name).write_bytes((REPO/'tools'/name).read_bytes())
sys.path.insert(0,str(chain))
for name in ['quality','workflow','review_preflight','contest_depth','discovery_loop','graph_paths','validate']:sys.modules.pop(name,None)
import quality as q,workflow as w,review_preflight as pf
# Reuse only the pre-existing *data fixture* definition, not the new candidate's test assertions.
old_fixture=OUT/'inputs/contest-fixture-before.py';old_fixture.write_bytes(subprocess.check_output(['git','show','76b680d64548af5c87d0455008b25358af06a698:tests/test_contest_depth.py'],cwd=REPO))
spec=importlib.util.spec_from_file_location('independent_depth_fixture',old_fixture);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
root=OUT/'cases/integration-v4/root';b=bound_fixture(q,root);quality_report=q.evaluate(b,root);assert quality_report['ready_for_review']
artifact_sha=q.file_digest(root/'lesson.ipynb');depth=f.synthetic_bundle();depth['target'].update(artifact='lesson.ipynb',artifact_sha256=artifact_sha)
roles=['source','demand','prerequisite','theory_explanation','coding_practice','independent_assessment','feedback']
graph={'nodes':[{'id':r,'type':'evidence','status':'verified','label':r} for r in roles],'edges':[{'from':x,'to':y,'type':'supports'} for x,y in zip(roles,roles[1:])]}
paths={'schema_version':1,'synthetic':True,'required_demands':['demand'],'paths':[{'id':'path:independent-fictional','comparison_id':'comparison:synthetic','roles':{r:r for r in roles},'provenance':{r:{'path':'lesson.ipynb','sha256':artifact_sha,'locator':'fictional input','revision':'fixture-v1','origin':'fictional author'} for r in roles},'assessment':{'independent':True,'allowed_support':'Fictional fixture only.','answer_conditions':'No real learner assessed.'}}]}
canonical=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()
judgment={'judgment':'met','rationale':'Fictional recorded comparison, not an educator conclusion.','evidence':[{'path':'lesson.ipynb','sha256':artifact_sha,'locator':'fictional reviewed bytes'}]}
semantic={'schema_version':1,'synthetic':True,'graph_sha256':canonical(graph),'path_spec_sha256':canonical(paths),'reviewer':{'id':'fictional-content-reviewer','method':'Fictional data for software join test.'},'comparisons':[{'comparison_id':'comparison:synthetic','path_id':'path:independent-fictional',**{k:copy.deepcopy(judgment) for k in ['problem_specific_key','feedback','independent_assessment']}}]}
state=json.loads(subprocess.check_output(['git','show','76b680d64548af5c87d0455008b25358af06a698:examples/workflow.json'],cwd=REPO));state['context']['artifact']['sha256']=artifact_sha
unused=root/'catalog-unused.txt';unused.write_text('Pinned unused fictional catalog entry.')
state['sources'].append({'id':'source:unused-local','revision':'fixture-v1','uri':'catalog-unused.txt','sha256':q.file_digest(unused)})
state['context']['inputs'].extend(pf.context_manifests(depth,graph,paths,semantic,state['sources']))
state['context']['inputs'].extend([{'id':'quality:bundle','revision':quality_report['revision'],'sha256':quality_report['bundle_sha256']},{'id':'quality:criteria','revision':quality_report['specification_revision'],'sha256':quality_report['specification_sha256']},{'id':'quality:evaluator','revision':'quality-v1','sha256':quality_report['evaluator_sha256']}])
state['frozen']=w.measurement(state);state['agreement']['criteria_fingerprint']=w.criteria_fingerprint(state);state['reviews'][-1]['context_fingerprint']=w.context_fingerprint(state)
for name,data in [('quality.json',b),('depth.json',depth),('graph.json',graph),('paths.json',paths),('semantic.json',semantic),('state.json',state)]:write_json(root/name,data)
files_before={str(p.relative_to(root)):q.file_digest(p) for p in root.rglob('*') if p.is_file()};state_before=copy.deepcopy(state);bundle_before=copy.deepcopy(b)
commands={
 'quality-evaluate':[sys.executable,'-B',str(chain/'quality.py'),'evaluate',str(root/'quality.json'),'--root',str(root)],
 'quality-plan':[sys.executable,'-B',str(chain/'quality.py'),'plan',str(root/'quality.json'),'--root',str(root)],
 'review-context':[sys.executable,'-B',str(chain/'quality.py'),'review-context',str(root/'quality.json'),'--root',str(root),'--criterion','K05','--object','demo:a'],
 'workflow':[sys.executable,'-B',str(chain/'workflow.py'),'decide',str(root/'state.json'),'--quality',str(root/'quality.json'),'--root',str(root)],
 'preflight':[sys.executable,'-B',str(chain/'review_preflight.py'),'--root',str(root),'--depth','depth.json','--graph','graph.json','--paths','paths.json','--semantic-review','semantic.json','--state','state.json','--quality','quality.json']}
def cli(label,stage):
 proc=subprocess.run(commands[label],capture_output=True,text=True,timeout=60);value=json.loads(proc.stdout)
 write_json(root.parent/(stage+'-'+label+'.json'),{'exit':proc.returncode,'result':value,'stderr':proc.stderr});return proc.returncode,value
results=[]
for label in commands:
 code,result=cli(label,'normal')
 if label=='preflight':assert code==0 and result['status']=='consistent_recorded_context',result
 elif label=='workflow':assert result['status']=='continue',result
 elif label=='quality-evaluate':assert result['ready_for_review']
 elif label=='review-context':assert result['plan_bindings']['issues']==[] and result['context_bindings']
 if label in ['quality-evaluate','quality-plan','workflow','preflight']:assert isinstance(result.get('selective_review'),dict)
 results.append({'stage':'normal','command':label,'exit':code,'status':result.get('status'),'selective_exposed':isinstance(result.get('selective_review'),dict)})
# Existing candidate + missing source must retain actionable diagnostics through every ordinary gate.
b['candidates']=[{'id':'fictional-proposal-a','object_id':'demo:a','criterion_id':'K05','severity':'major','confidence':'unresolved','hypothesis':'Inspect fictional source support.','action':'Restore or inspect the declared missing file.'}]
write_json(root/'quality.json',b);(root/'sources/a.txt').unlink()
for label in ['quality-evaluate','quality-plan','workflow','preflight']:
 code,result=cli(label,'missing-source');selective=result.get('selective_review');assert isinstance(selective,dict),(label,result)
 statuses={(r['criterion_id'],r['object_id']):r['status'] for r in selective['review_freshness']}
 assert statuses['K05','demo:a']=='review_required' and statuses['K05','demo:b']=='current',(label,statuses)
 assert 'sources/a.txt' in json.dumps(selective)
 if label=='quality-plan':assert any(x.get('context_status')=='unavailable' for x in result['ranked'])
 if label=='quality-evaluate':assert not result['ready_for_review'];assert next(c for c in result['checks'] if c['id']=='K13')['measurement']['unavailable_contexts']
 if label in ['workflow','preflight']:assert result['status']=='blocked',(label,result)
 results.append({'stage':'missing-source','command':label,'exit':code,'status':result.get('status'),'affected':'demo:a','unaffected':'demo:b','path_diagnostic_retained':True})
# Restore original quality context; an unused joined catalog file still blocks its global gate.
(root/'sources/a.txt').write_text('Fictional a source v1; software control only.\n');b=copy.deepcopy(bundle_before);write_json(root/'quality.json',b)
unused.write_text('Changed unused catalog file.')
code,result=cli('preflight','unused-catalog');assert result['status']=='blocked' and any(x['code']=='stale_declared_source' for x in result['blockers'])
assert all(r['status']=='current' for r in result['selective_review']['review_freshness'])
results.append({'stage':'unused-catalog-change','command':'preflight','exit':code,'status':result['status'],'unit_content_reviews_current':True,'global_catalog_gate_still_blocks':True})
# Inspect APIs without mutating the caller's dictionary/history.
before=copy.deepcopy((b,state));pf.preflight(root,depth,graph,paths,state,b,semantic_review=semantic);assert (b,state)==before
# Real old bundles: evaluate AND plan; no hashes/reviews/agreements refreshed.
old=[]
for name,path in [('old-week1','reviews/week01/final-followup/quality.json'),('old-system','reviews/system-followup-20261111/current/quality.json')]:
 source=REPO/path;original=q.file_digest(source)
 for command in ['evaluate','plan']:
    proc=subprocess.run([sys.executable,'-B',str(chain/'quality.py'),command,str(source),'--root',str(REPO)],capture_output=True,text=True,timeout=60);value=json.loads(proc.stdout)
    write_json(OUT/(name+'-v4-'+command+'.json'),{'exit':proc.returncode,'result':value,'stderr':proc.stderr})
    assert isinstance(value.get('selective_review'),dict),(name,command,value)
    if command=='evaluate':assert not value['ready_for_review']
    counts={}
    for row in value['selective_review']['review_freshness']:counts[row['status']]=counts.get(row['status'],0)+1
    old.append({'bundle':path,'command':command,'exit':proc.returncode,'status':value['status'],'freshness_counts':counts,'real_records_refreshed':False})
 assert q.file_digest(source)==original
report={'quality_sha256':expected,'checks':results,'actual_old_records':old,'caller_inputs_unchanged_by_inspection':True,'scope':'Only explicit fictional fixtures were constructed/updated. Actual old bundles were read unchanged; no actual review/consent/learner evidence manufactured.'}
write_json(OUT/'integration-v4-results.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
