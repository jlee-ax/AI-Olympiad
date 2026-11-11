"""Actual-record source dependency drift, unreadability and CLI diagnostics.
Extra path bindings and capture probes exist only in copies; no review approval is added.
"""
import argparse,copy,hashlib,json,pathlib,re,shutil,subprocess,sys,types
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();load=lambda p:json.loads(p.read_text())
EXPECTED='03f24f7e9b89979e30facf258f8c8f9f358b1aca2de876a1adae5e058f0fc96b'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--baseline-control',default='restored-control-04/cases/00-control');a=ap.parse_args();folder=OUT/a.label
 if folder.exists():raise ValueError('New immutable label required')
 folder.mkdir();raw=(ROOT/'tools/quality.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED;(folder/'quality-code-snapshot.py').write_bytes(raw);q=types.ModuleType('quality_source_failure');q.__file__=str(ROOT/'tools/quality.py');exec(compile(raw,q.__file__,'exec'),q.__dict__)
 previous=load(OUT/'baseline-01/results.json');base=(OUT/a.baseline_control).resolve();base.relative_to(OUT);real=load(base/'record.json');prefix='reviews/week01/independent-transfer-20261111/';record_files=[prefix+x for x in ('workflow.json','depth.json','graph.json','paths.json','semantic-review.json')];inputs={x['path'] for x in previous['copied_input_files']}|set(record_files)
 def collect(value):
  if isinstance(value,dict):
   for v in value.values():collect(v)
  elif isinstance(value,list):
   for v in value:collect(v)
  elif isinstance(value,str) and len(value)<350 and '\n' not in value:
   name=value[5:] if value.startswith('file:') else value
   try:
    p=(ROOT/name).resolve();p.relative_to(ROOT)
    if p.is_file():inputs.add(str(p.relative_to(ROOT)))
   except (OSError,ValueError):pass
 for p in list(inputs):
  if p.endswith('.json'):
   try:collect(load(ROOT/p))
   except (OSError,ValueError):pass
 latest={}
 for r in real['reviews']:latest[r['criterion_id'],r['object_id']]=r
 used=next(x for x in real['source_reads'] if x['id']=='read-followup:PYTHON_RETURN');receipt=used['reading_receipt'];assert receipt in inputs
 results=[]
 def make(name,mode):
  case=folder/'cases'/name;case.mkdir(parents=True)
  for p in sorted(inputs):
   src=base/p if (base/p).exists() else ROOT/p;dst=case/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  b=copy.deepcopy(real);node=next(x for x in b['dependencies'] if x['id']==used['id']);node['path']=receipt
  probe=copy.deepcopy(latest['K06','claim:python']);probe['id']='mechanical-source-capture-probe';probe['context_fingerprint']=q.object_fingerprint(b,'K06','claim:python',case);probe['context_bindings']=q.context_bindings(b,'claim:python',case);probe['probe_only']='Counterfactual context capture for change detection; not appended to actual or copied reviews.'
  if mode=='changed':p=case/receipt;p.write_bytes(p.read_bytes()+b'\nsource-dependency-byte-change\n')
  elif mode=='missing':(case/receipt).unlink()
  elif mode=='used_read':next(x for x in b['source_reads'] if x['id']==used['id'])['finding']+=' [changed reading finding]'
  elif mode=='unused_read':next(x for x in b['source_reads'] if x['id']=='read-followup:1')['finding']+=' [changed unused reading finding]'
  elif mode=='unrelated':(case/'unreferenced-source.txt').write_text('unrelated source bytes\n')
  (case/'record.json').write_text(json.dumps(b,ensure_ascii=False,indent=2)+'\n');(case/'probe-only-not-reviews.json').write_text(json.dumps(probe,ensure_ascii=False,indent=2)+'\n')
  probe_status=q.review_freshness(b,probe,case);(case/'freshness.json').write_text(json.dumps(probe_status,ensure_ascii=False,indent=2)+'\n')
  commands=[('evaluate',[str(folder/'quality-code-snapshot.py'),'evaluate',str(case/'record.json'),'--root',str(case)]),('plan',[str(folder/'quality-code-snapshot.py'),'plan',str(case/'record.json'),'--root',str(case)]),('workflow',[str(ROOT/'tools/workflow.py'),'decide',str(case/(prefix+'workflow.json')),'--quality',str(case/'record.json'),'--root',str(case)]),('preflight',[str(ROOT/'tools/review_preflight.py'),'--root',str(case),'--depth',prefix+'depth.json','--graph',prefix+'graph.json','--paths',prefix+'paths.json','--semantic-review',prefix+'semantic-review.json','--state',prefix+'workflow.json','--quality','record.json'])];values={};calls=[]
  for command,args in commands:
   argv=[sys.executable,'-B',*args];p=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True);v=json.loads(p.stdout);values[command]=v;(case/(command+'-result.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');calls.append({'name':command,'argv':argv,'exit_code':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout.encode()).hexdigest(),'stderr':p.stderr})
  sr=values['evaluate'].get('selective_review');checks={'evaluate_retains_selective_review':isinstance(sr,dict),'plan_forwards_same_selective':values['plan'].get('selective_review')==sr and isinstance(sr,dict),'workflow_forwards_same_selective_while_paused':values['workflow'].get('selective_review')==sr and values['workflow']['reason']=='criteria_agreement_required','preflight_forwards_same_selective':values['preflight'].get('selective_review')==sr and isinstance(sr,dict),'no_new_readiness':not values['evaluate'].get('ready_for_review',True),'probe_expected_status':probe_status['status']==('review_required' if mode in ('changed','missing','used_read') else 'current')}
  if sr:
   fresh=sr['review_freshness'];target=next(x for x in fresh if x['criterion_id']=='K06' and x['object_id']=='claim:python');checks['unrelated_K06_claims_current']=all(next(x for x in fresh if x['criterion_id']=='K06' and x['object_id']==k)['status']=='current' for k in ('claim:table','claim:array','claim:visualise'))
   if mode=='missing':
    checks['target_known_missing_source_requires_review']=target['status']=='review_required';checks['explicit_missing_node_path_null_sha']=any(x.get('node_id')==used['id'] and x.get('path')==receipt and x.get('sha256') is None and x.get('error') for x in target['current_bindings']);k11=next(x for x in values['evaluate']['checks'] if x['id']=='K11');checks['K11_claim_error_is_retained']=any(x.get('object_id')=='claim:python' and x.get('context_error') for x in k11['measurement']['active_by_object']);k13=next(x for x in values['evaluate']['checks'] if x['id']=='K13');checks['existing_candidate_context_unavailable_retained']=any(x['candidate_id']=='correct-return-trace' for x in k13['measurement']['unavailable_contexts']);checks['plan_existing_candidate_unavailable_retained']=any(x['id']=='correct-return-trace' and x.get('context_status')=='unavailable' for x in values['plan']['ranked'])
  if mode=='missing':
   v3=OUT/'finalcandidate-03/quality-code-snapshot.py';old=[]
   for command in ['evaluate','plan']:
    argv=[sys.executable,'-B',str(v3),command,str(case/'record.json'),'--root',str(case)];p=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True);v=json.loads(p.stdout);(case/('v3-'+command+'-failure.json')).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');old.append({'name':command,'exit_code':p.returncode,'selective_review_present':'selective_review' in v,'actual':v})
   checks['same_copy_v3_diagnostic_loss_reproduced']=all(x['exit_code']==2 and not x['selective_review_present'] for x in old)
  result={'case':name,'mode':mode,'existing_candidate_preserved':b['candidates']==real['candidates'],'stored_reviews_unchanged':b['reviews']==real['reviews'],'source_binding_added_only_in_copy':{'node_id':used['id'],'path':receipt,'origin':'Actual source_read.reading_receipt field; local reading receipt, not authenticated upstream source bytes.'},'checks':checks,'all_checks_passed':all(checks.values()),'calls':calls,'probe_status':probe_status['status'],'actual_state':{n:{'status':v.get('status'),'reason':v.get('reason')} for n,v in values.items()}};(case/'measurement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');results.append(result)
 for i,(mode,name) in enumerate([('intact','control'),('changed','used-source-file-changed'),('missing','used-source-file-missing'),('used_read','used-source-reading-changed'),('unused_read','unused-source-reading-changed'),('unrelated','unrelated-source-file')]):make(f'{i:02d}-{name}',mode)
 original_ok=all(sha(ROOT/p)==h for p,h in previous['original_protected_paths_before'].items());result={'quality_sha256':hashlib.sha256(raw).hexdigest(),'quality_code_stable':sha(ROOT/'tools/quality.py')==EXPECTED,'workflow_sha256':sha(ROOT/'tools/workflow.py'),'preflight_sha256':sha(ROOT/'tools/review_preflight.py'),'source_record_sha256':previous['real_record_sha256'],'copied_input_paths':sorted(inputs),'cases':results,'all_checks_passed':all(x['all_checks_passed'] for x in results),'original_lesson_record_workflow_unchanged':original_ok,'limits':['The extra dependency.path is explicit only in copied records and points to the actual declared local reading receipt, not to authenticated upstream primary content.','Original/copy historical reviews and existing candidates remain identical. Capture probes are separate controls, not appended or treated as independent reviews.','Only review bookkeeping is run; no mutated lesson code, learner task, publication or external operation is executed.']};(folder/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'label':a.label,'quality_sha256':result['quality_sha256'],'all_checks_passed':result['all_checks_passed'],'cases':len(results),'originals_unchanged':original_ok,'failed_checks':{x['case']:[k for k,v in x['checks'].items() if not v] for x in results if not x['all_checks_passed']}},ensure_ascii=False));return 0 if result['all_checks_passed'] and original_ok else 2
if __name__=='__main__':raise SystemExit(main())
