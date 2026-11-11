"""Actual-record clone experiments. Never edits lesson, original record, index or remote.
Hashes establish byte changes and declared scope only, never semantic equivalence.
"""
from __future__ import annotations
import argparse,copy,datetime,hashlib,importlib.util,json,pathlib,re,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
RECORD='reviews/week01/independent-transfer-20261111/quality.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,value):
 p.resolve().relative_to(OUT)
 if p.exists():raise ValueError('Choose new label; never replace result '+str(p))
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def walk_paths(value):
 if isinstance(value,dict):
  p=value.get('path')
  if isinstance(p,str) and (ROOT/p).is_file():yield p
  for v in value.values():yield from walk_paths(v)
 elif isinstance(value,list):
  for v in value:yield from walk_paths(v)
def changed(a,b):return sorted(k for k in a if a[k]!=b[k])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--quality-code',default=str(OUT/'code-baseline/quality.py'));a=ap.parse_args();code=pathlib.Path(a.quality_code).resolve();spec=importlib.util.spec_from_file_location('quality_reproduction',code);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
 b=load(ROOT/RECORD);folder=OUT/a.label
 if folder.exists():raise ValueError('Existing label is immutable')
 folder.mkdir();originals={str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'lessons').rglob('*')) if p.is_file()};originals[RECORD]=sha(ROOT/RECORD);originals['reviews/week01/independent-transfer-20261111/workflow.json']=sha(ROOT/'reviews/week01/independent-transfer-20261111/workflow.json')
 idx=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=ROOT,text=True).strip());idx=idx if idx.is_absolute() else ROOT/idx;index_before=sha(idx)
 inputs=set(walk_paths(b))|{RECORD,q.CONTRACT,q.CATALOG,q.UNIT_SPECIFICATIONS,q.THEORY_SPECIFICATION,'curriculum/student-plan.html'}
 latest={}
 for rv in b['reviews']:latest[(rv['criterion_id'],rv['object_id'])]=rv
 def measure(bundle,root):
  q.validate(bundle);fps={};reviews={}
  for (cid,oid),rv in latest.items():
   k=cid+'/'+oid;fps[k]=q.object_fingerprint(bundle,cid,oid,root);reviews[k]={'latest_review_id':rv['id'],'stored_status':rv['status'],'stored_context_matches':rv.get('context_fingerprint')==fps[k],'effective_status':q._review(bundle,cid,oid,root)}
  report=q.evaluate(bundle,root);k12=next(x for x in report['checks'] if x['id']=='K12');return {'fingerprints':fps,'reviews':reviews,'aggregate':{k:report.get(k) for k in ('status','ready_for_review','discovery_gate')},'criterion_statuses':{x['id']:x['status'] for x in report['checks']},'k12_measurement':k12['measurement'],'agreement':bundle['policy'],'plan_baseline':q.baseline(root)}
 def clone(name):
  case=folder/'cases'/name;case.mkdir(parents=True)
  for p in sorted(inputs):
   t=case/p;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,t)
  return case,copy.deepcopy(b)
 root,control=clone('00-control');baseline=measure(control,root);save(root/'record.json',control);save(root/'measurement.json',baseline)
 def edit_week(root,week):
  p=root/'curriculum/student-plan.html';s=p.read_text();pattern=r'(<tr\b[^>]*\bid="week-'+str(week)+r'"[^>]*>)(.*?)(</tr>)';m=re.search(pattern,s,re.S)
  if not m:raise ValueError('Missing week row')
  block=m.group(0);old=str(week)+'주차';assert old in block;new=block.replace(old,old+' [reproduction changed]',1);p.write_text(s[:m.start()]+new+s[m.end():])
 def edit_cell(root,cid):
  p=root/b['artifact']['path'];n=load(p);c=next(c for c in n['cells'] if c['id']==cid);c['source']=''.join(c['source'])+'\n[reproduction changed source]\n';p.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
 def edit_file(root,path):
  p=root/path;p.write_bytes(p.read_bytes()+b'\nreproduction changed evidence bytes\n')
 all_locators=set()
 for obj in b['units']+b['claims']:
  all_locators.add(obj.get('locator','file'))
  all_locators.update(x['locator'] for x in obj.get('chain',{}).values() if 'locator' in x)
  for ls in obj.get('explanation_regions',{}).values():all_locators.update(ls)
 nb=load(ROOT/b['artifact']['path']);unrelated=next(c['id'] for c in nb['cells'] if 'cell:'+c.get('id','') not in all_locators)
 rows=[]
 def run(name,mutate,expected):
  rt,cb=clone(name);mutate(rt,cb);now=measure(cb,rt);save(rt/'record.json',cb);save(rt/'measurement.json',now)
  diffs={'changed_fingerprints':changed(baseline['fingerprints'],now['fingerprints']),'changed_effective_review_statuses':{k:{'before':baseline['reviews'][k]['effective_status'],'after':now['reviews'][k]['effective_status']} for k in baseline['reviews'] if baseline['reviews'][k]['effective_status']!=now['reviews'][k]['effective_status']},'changed_criterion_statuses':{k:{'before':baseline['criterion_statuses'][k],'after':now['criterion_statuses'][k]} for k in baseline['criterion_statuses'] if baseline['criterion_statuses'][k]!=now['criterion_statuses'][k]},'aggregate_before':baseline['aggregate'],'aggregate_after':now['aggregate'],'plan_baseline_after':now['plan_baseline']['status']}
  checks={}
  if expected.get('all_fingerprints_unchanged'):checks['all_fingerprints_unchanged']=not diffs['changed_fingerprints']
  for k in expected.get('fingerprints_changed',[]):checks['fingerprint_changed:'+k]=k in diffs['changed_fingerprints']
  for k in expected.get('fingerprints_unchanged',[]):checks['fingerprint_unchanged:'+k]=k not in diffs['changed_fingerprints']
  for k,v in expected.get('effective_statuses',{}).items():checks['effective_status:'+k]=now['reviews'][k]['effective_status']==v
  if 'plan_status' in expected:checks['plan_status']=now['plan_baseline']['status']==expected['plan_status']
  item={'case':name,'expected':expected,'actual':diffs,'expectation_checks':checks,'all_expectations_met':all(checks.values()),'record_path':str((rt/'record.json').relative_to(ROOT)),'measurement_path':str((rt/'measurement.json').relative_to(ROOT))};rows.append(item)
 run('01-plan-week1-unlinked',lambda r,c:edit_week(r,1),{'all_fingerprints_unchanged':True,'plan_status':'failed','interpretation':'Original PLAN has no path and no assessed object closure edge. Relevant plan change fails aggregate K01 but changes no object fingerprint; never claim an aggregate approval survived.'})
 run('02-plan-week10-unlinked',lambda r,c:edit_week(r,10),{'all_fingerprints_unchanged':True,'plan_status':'failed','interpretation':'Same legacy omission. This alone does not prove appropriate selective classification.'})
 def repin(r,c):
  edit_week(r,1);p=r/'curriculum/contract.json';co=load(p);co['baseline']['sha256']=sha(r/'curriculum/student-plan.html');co['revision']+='-clone-repin';p.write_text(json.dumps(co,ensure_ascii=False,indent=2)+'\n')
 run('03-plan-week1-repin-clone',repin,{'all_fingerprints_unchanged':True,'plan_status':'passed','interpretation':'Explicit cloned pin revision restores structural baseline, still supplies no individual new content judgment, agreement or readiness.'})
 run('04-related-claim-table-cell',lambda r,c:edit_cell(r,'08e374f4'),{'fingerprints_changed':['K06/claim:table','K05/W1-table'],'fingerprints_unchanged':['K06/claim:array','K06/claim:visualise'],'effective_statuses':{'K06/claim:table':'uncertain','K06/claim:array':'passed'},'interpretation':'Already-working region invalidation changes a truly current local passed claim to uncertain; unrelated local pass survives.'})
 run('05-unregistered-notebook-cell',lambda r,c:edit_cell(r,unrelated),{'all_fingerprints_unchanged':True,'interpretation':'Unregistered cell '+unrelated+' does not change declared local review contexts, while full artifact digest/execution gates may fail. Omitted semantic dependencies remain a limit.'})
 def metadata(r,c):
  p=r/b['artifact']['path'];n=load(p);n.setdefault('metadata',{})['reproduction_unrelated']='metadata only';
  for cell in n['cells']:
   if cell['cell_type']=='code':cell['execution_count']=999
  p.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
 run('06-execution-count-metadata-only',metadata,{'all_fingerprints_unchanged':True,'interpretation':'Region logic intentionally excludes execution counters/notebook metadata; full raw byte identity remains separate.'})
 def output(r,c):
  p=r/b['artifact']['path'];n=load(p);cell=next(x for x in n['cells'] if x['id']=='81129230');assert cell['cell_type']=='code';cell.setdefault('outputs',[]).append({'output_type':'stream','name':'stdout','text':['reproduction changed displayed output\n']});p.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
 run('07-linked-output-cell',output,{'fingerprints_changed':['K05/W1-python'],'fingerprints_unchanged':['K06/claim:array'],'interpretation':'Displayed output is included in cell-region fingerprints. This detects declared byte-level context drift, not output correctness.'})
 def source(r,c,sid):next(x for x in c['source_reads'] if x['id']==sid)['finding']+=' [reproduction changed finding]'
 run('08-used-source-reading-record',lambda r,c:source(r,c,'read-followup:3'),{'fingerprints_changed':['K06/claim:table','K05/W1-table'],'fingerprints_unchanged':['K06/claim:array'],'effective_statuses':{'K06/claim:table':'uncertain'},'interpretation':'Used source read stable metadata is already in upstream object fingerprints.'})
 run('09-unconnected-source-reading-record',lambda r,c:source(r,c,'read-followup:1'),{'all_fingerprints_unchanged':True,'interpretation':'Unused source read outside assessed closure has no local review impact; no universal invalidation.'})
 ev=next(x for x in latest['K06','claim:table']['evidence'] if 'path' in x)['path']
 run('10-review-evidence-bytes',lambda r,c:edit_file(r,ev),{'all_fingerprints_unchanged':True,'effective_statuses':{'K06/claim:table':'uncertain'},'interpretation':'Evidence SHA fails _evidence and withdraws local passed status without changing object_fingerprint. Legacy K12 lists context staleness only and may omit this reason.'})
 run('11-unrelated-new-evidence-file',lambda r,c:(r/'unreferenced-evidence.txt').write_text('unrelated local bytes\n'),{'all_fingerprints_unchanged':True,'effective_statuses':{'K06/claim:table':'passed'},'interpretation':'A file not in the recorded evidence/dependency set has no declared influence; omitted necessary dependencies cannot be inferred from bytes.'})
 run('12-shared-dependency-file',lambda r,c:edit_file(r,'reviews/week01/independent-transfer-20261111/source-brief.md'),{'fingerprints_changed':['K05/W1-python','K05/W1-table','K05/W1-array','K05/W1-visualise'],'fingerprints_unchanged':['K06/claim:table','K06/claim:array'],'interpretation':'All four units explicitly depend on this file; broad unit impact is declared dependency behavior, not blanket invalidation.'})
 def linked_plan(r,c):
  next(x for x in c['dependencies'] if x['id']=='PLAN')['path']='curriculum/student-plan.html';next(x for x in c['dependencies'] if x['id']=='W1-table')['depends_on'].append('PLAN')
 rt,cb=clone('13-plan-whole-file-linked-control');linked_plan(rt,cb);linked_base=measure(cb,rt);save(rt/'record.json',cb);save(rt/'measurement.json',linked_base)
 for number,week in [(14,1),(15,10)]:
  rt,cb=clone(str(number)+'-plan-whole-file-linked-week'+str(week));linked_plan(rt,cb);edit_week(rt,week);now=measure(cb,rt);save(rt/'record.json',cb);save(rt/'measurement.json',now);diff=changed(linked_base['fingerprints'],now['fingerprints']);rows.append({'case':rt.name,'expected':{'fingerprints_changed':['K05/W1-table'],'interpretation':'A whole-file PLAN path plus edge detects week1, but also invalidates W1table on unrelated week10 changes. Region-selective provenance must be explicit; hashes do not classify meaning.'},'actual':{'changed_fingerprints':diff},'expectation_checks':{'whole_file_path_invalidates_table': 'K05/W1-table' in diff,'unconnected_claim_unchanged':'K06/claim:array' not in diff},'all_expectations_met':'K05/W1-table' in diff and 'K06/claim:array' not in diff,'record_path':str((rt/'record.json').relative_to(ROOT)),'measurement_path':str((rt/'measurement.json').relative_to(ROOT))})
 current_originals={p:sha(ROOT/p) for p in originals};assert current_originals==originals
 result={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':a.label,'quality_code_path':str(code),'quality_code_sha256':sha(code),'real_record_path':RECORD,'real_record_sha256':sha(ROOT/RECORD),'control_record_is_byte_equivalent_semantics':control==b,'original_protected_paths_before':originals,'original_protected_paths_after':current_originals,'original_lessons_and_record_unchanged':True,'git_index_before':index_before,'git_index_after':sha(idx),'git_index_unchanged':sha(idx)==index_before,'copied_input_files':[{'path':p,'sha256':sha(ROOT/p)} for p in sorted(inputs)],'baseline_actual_status':baseline,'plan_node':next(x for x in b['dependencies'] if x['id']=='PLAN'),'plan_in_assessed_closures':{x['id']:'PLAN' in {n['id'] for n in q.closure(b,x['id'])} for x in b['units']+b['claims']},'cases':rows,'all_expectations_met':all(x['all_expectations_met'] for x in rows),'limits':['Record copies retain real historical declarations but do not create new real reviews, re-agreement or acceptance. No review fingerprint is refreshed to fabricate a passing control.','The original aggregate is already uncertain/not ready with discovery_missing and unagreed policy; only stated local K06 claims currently resolve passed.','Changes are deliberate byte/context perturbations, not assertions about semantic equivalence. Scope omissions cannot be discovered by a digest.','No code or lesson is executed from a mutated notebook. Only existing review bookkeeping reads the copies.']}
 save(folder/'results.json',result);print(json.dumps({'label':a.label,'case_count':len(rows),'all_expectations_met':result['all_expectations_met'],'originals_unchanged':True,'git_index_unchanged':result['git_index_unchanged'],'failed_cases':[x['case'] for x in rows if not x['all_expectations_met']]},ensure_ascii=False));return 0 if result['all_expectations_met'] else 2
if __name__=='__main__':raise SystemExit(main())
