"""Candidate checks on actual-record copies and explicitly counterfactual capture probes.
No probe is appended as a review or used to claim real approval.
"""
from __future__ import annotations
import argparse,copy,datetime,hashlib,json,pathlib,re,shutil,types
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--label',required=True);ap.add_argument('--expected-quality-sha');ap.add_argument('--baseline-control',default='baseline-01/cases/00-control');a=ap.parse_args();folder=OUT/a.label
 if folder.exists():raise ValueError('New immutable label required')
 folder.mkdir();raw=(ROOT/'tools/quality.py').read_bytes();assert not a.expected_quality_sha or hashlib.sha256(raw).hexdigest()==a.expected_quality_sha; (folder/'quality-code-snapshot.py').write_bytes(raw);q=types.ModuleType('quality_candidate');q.__file__=str(ROOT/'tools/quality.py');exec(compile(raw,q.__file__,'exec'),q.__dict__)
 previous=load(OUT/'baseline-01/results.json');base=(OUT/a.baseline_control).resolve();base.relative_to(OUT);real=load(base/'record.json');latest={}
 for rv in real['reviews']:latest[rv['criterion_id'],rv['object_id']]=rv
 def save(path,value):
  assert not path.exists(),path;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 def clone(name):
  rt=folder/'cases'/name;rt.mkdir(parents=True)
  for item in previous['copied_input_files']:
   p=item['path'];dst=rt/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(base/p,dst)
  return rt,copy.deepcopy(real)
 def attach(rt,b):
  co=load(rt/q.CONTRACT);topics={x['id']:x for x in co['topics']}
  for unit in b['units']:
   nid='reproduction-plan:'+unit['id'];loc=sorted({'#plan-context','#week-'+str(unit['week'])}|{topics[s]['plan_locator'] for s in unit['syllabus_ids']});b['dependencies'].append({'id':nid,'path':co['baseline']['path'],'revision':'copy-only-explicit-scope','sha256':sha(rt/co['baseline']['path']),'locators':loc,'depends_on':[]});next(n for n in b['dependencies'] if n['id']==unit['id'])['depends_on'].append(nid);unit['plan_dependency_ids']=[nid]
 def probes(rt,b):
  values={}
  for unit in b['units']:
   rv=copy.deepcopy(latest['K05',unit['id']]);rv['id']='mechanical-capture-probe:'+unit['id'];rv['context_fingerprint']=q.object_fingerprint(b,'K05',unit['id'],rt);rv['dependency_scope_fingerprint']=q.plan_bindings(b,unit['id'],rt)['scope_fingerprint'];rv['context_bindings']=q.context_bindings(b,unit['id'],rt);rv['probe_only']='Counterfactual current capture for testing bookkeeping only. No new semantic review, impact confirmation or approval was performed. Never appended to record.reviews.';values[unit['id']]=rv
  return values
 def statuses(rt,b,ps):return {k:q.review_freshness(b,v,rt) for k,v in ps.items()}
 def edit_row(rt,identifier):
  p=rt/'curriculum/student-plan.html';s=p.read_text();m=re.search(r'<tr\b[^>]*\bid="'+re.escape(identifier)+r'"[^>]*>.*?</tr>',s,re.S);assert m;block=m.group(0);new=block.replace('</th>',' [copy changed]</th>',1);assert new!=block;p.write_text(s[:m.start()]+new+s[m.end():])
 def edit_cell(rt,cid):
  p=rt/real['artifact']['path'];n=load(p);c=next(x for x in n['cells'] if x.get('id')==cid);c['source']=''.join(c['source'])+'\n[copy changed]\n';p.write_text(json.dumps(n,ensure_ascii=False,indent=1)+'\n')
 def evidence_file(rt,path):
  p=rt/path;p.write_bytes(p.read_bytes()+b'\ncopy changed evidence bytes\n')
 rt,b=clone('00-real-legacy-control');legacy={k+'/'+o:q.review_freshness(b,rv,rt) for (k,o),rv in latest.items() if k in q.REVIEW_CRITERIA};save(rt/'record.json',b);save(rt/'freshness.json',legacy)
 rt,b=clone('01-explicit-bindings-unconfirmed');attach(rt,b);unc={u['id']:q.review_freshness(b,latest['K05',u['id']],rt) for u in b['units']};save(rt/'record.json',b);save(rt/'freshness.json',unc)
 rt,b=clone('02-scoped-mechanical-capture-control');attach(rt,b);capture=probes(rt,b);fresh=statuses(rt,b,capture);save(rt/'record.json',b);save(rt/'probe-only-not-reviews.json',capture);save(rt/'freshness.json',fresh)
 results=[]
 def run(name,mutate,expected,mode='scoped'):
  rt,b=clone(name)
  if mode=='scoped':attach(rt,b)
  ps=copy.deepcopy(capture) if mode=='scoped' else {u['id']:copy.deepcopy(latest['K16',u['id']]) for u in b['units']}
  mutate(rt,b);actual=statuses(rt,b,ps);save(rt/'record.json',b);save(rt/'probe-only-not-reviews.json',ps);save(rt/'freshness.json',actual);got={k:v['status'] for k,v in actual.items()};checks={k:got[k]==v for k,v in expected.items()};results.append({'case':name,'probe_scope':mode,'expected':expected,'actual_statuses':got,'checks':checks,'all_expectations_met':all(checks.values()),'changed_bindings':{k:v['changed_bindings'] for k,v in actual.items()},'reason_codes':{k:[x['code'] for x in v['reasons']] for k,v in actual.items()},'binding_issues':{k:v['binding_issues'] for k,v in actual.items()},'binding_statuses':{k:v.get('binding_status') for k,v in actual.items()}})
 units=[u['id'] for u in real['units']];all_current={k:'current' for k in units};all_review={k:'review_required' for k in units}
 run('03-related-week1',lambda r,b:edit_row(r,'week-1'),all_review)
 run('04-unrelated-week10',lambda r,b:edit_row(r,'week-10'),all_current)
 run('05-related-topic-scope02',lambda r,b:edit_row(r,'scope-02'),{**all_current,'W1-table':'review_required','W1-array':'review_required'})
 run('06-unrelated-topic-scope60',lambda r,b:edit_row(r,'scope-60'),all_current)
 def global_context(r,b):
  p=r/'curriculum/student-plan.html';s=p.read_text();assert '계획' in s;p.write_text(s.replace('학습 계획</th>','학습 계획 변경</th>',1))
 run('07-shared-plan-context',global_context,all_review)
 def css(r,b):
  p=r/'curriculum/student-plan.html';s=p.read_text();assert '#fff' in s;p.write_text(s.replace('#fff','#fffffe',1))
 run('08-unselected-css',css,all_current)
 run('09-related-table-cell',lambda r,b:edit_cell(r,'08e374f4'),{**all_current,'W1-table':'review_required'})
 nb=load(base/real['artifact']['path']);used={x['locator'] for ps in capture.values() for x in ps['context_bindings'] if x['kind']=='artifact'};unrelated=next(c['id'] for c in nb['cells'] if 'cell:'+c.get('id','') not in used)
 run('10-unselected-notebook-cell',lambda r,b:edit_cell(r,unrelated),all_current)
 ev=next(x['path'] for x in latest['K05','W1-table']['evidence'] if 'path' in x)
 run('11-shared-review-evidence-file',lambda r,b:evidence_file(r,ev),all_review)
 run('12-unreferenced-evidence-file',lambda r,b:(r/'unreferenced-evidence.txt').write_text('irrelevant bytes\n'),all_current)
 def used_read(r,b):next(x for x in b['source_reads'] if x['id']=='read-followup:3')['finding']+=' [changed]'
 run('13-used-source-read',used_read,{**all_current,'W1-table':'review_required'})
 def unused_read(r,b):next(x for x in b['source_reads'] if x['id']=='read-followup:1')['finding']+=' [changed]'
 run('14-unused-source-read',unused_read,all_current)
 def rebind_pin_only(r,b):
  for n in b['dependencies']:
   if n['id'].startswith('reproduction-plan:'):n['sha256']='0'*64;n['revision']='changed-provenance-only'
 run('15-selected-plan-provenance-only',rebind_pin_only,all_current)
 def missing_selector(r,b):next(x for x in b['dependencies'] if x['id']=='reproduction-plan:W1-table')['locators'].remove('#scope-02')
 run('16-missing-required-scope',missing_selector,{**all_current,'W1-table':'binding_required'})
 def missing_edge(r,b):next(x for x in b['dependencies'] if x['id']=='W1-table')['depends_on'].remove('reproduction-plan:W1-table')
 run('17-missing-declared-edge',missing_edge,{**all_current,'W1-table':'binding_required'})
 common=next(x['path'] for x in latest['K16','W1-table']['evidence'] if 'path' in x)
 run('18-known-evidence-drift-unbound-legacy-unit',lambda r,b:evidence_file(r,common),all_review,mode='legacy')
 def outside_policy(r,b):
  p=r/'curriculum/student-plan.html';s=p.read_text();assert '</main>' in s;p.write_text(s.replace('</main>','<p>추가 평가 조건: 검증 정답을 훈련 특성으로 사용한다.</p></main>',1))
 run('19-visible-global-policy-outside-table',outside_policy,all_review)
 def script_only(r,b):
  p=r/'curriculum/student-plan.html';s=p.read_text();p.write_text(s.replace('</main>','<script>console.log("unrelated script bytes");</script></main>',1))
 run('20-unselected-script-content',script_only,all_current)
 rt,b=clone('21-outside-source-href-only');attach(rt,b);p=rt/'curriculum/student-plan.html';s=p.read_text();p.write_text(s.replace('</main>','<p>추가 근거: <a href="https://example.invalid/source-v1">same visible source label</a></p></main>',1));link_capture=probes(rt,b);before_link=statuses(rt,b,link_capture);s=p.read_text();p.write_text(s.replace('https://example.invalid/source-v1','https://example.invalid/source-v2',1));actual=statuses(rt,b,link_capture);save(rt/'record.json',b);save(rt/'probe-only-not-reviews.json',link_capture);save(rt/'freshness.json',actual);got={k:v['status'] for k,v in actual.items()};results.append({'case':'21-outside-source-href-only','expected':all_review,'actual_statuses':got,'control_statuses':{k:v['status'] for k,v in before_link.items()},'all_expectations_met':got==all_review and all(v['status']=='current' for v in before_link.values()),'reason_codes':{k:[x['code'] for x in v['reasons']] for k,v in actual.items()},'note':'Extra source-link context is an explicit mechanical control, not an actual source or new authoritative evidence. Only href changes; visible label stays identical.'})
 result={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'quality_code_sha256':hashlib.sha256(raw).hexdigest(),'quality_code_snapshot':str((folder/'quality-code-snapshot.py').relative_to(ROOT)),'baseline_record_sha256':previous['real_record_sha256'],'real_legacy_control_statuses':{k:v['status'] for k,v in legacy.items()},'actual_record_with_explicit_scope_but_no_new_review_statuses':{k:v['status'] for k,v in unc.items()},'counterfactual_capture_control_statuses':{k:v['status'] for k,v in fresh.items()},'all_expectations_met':all(x['all_expectations_met'] for x in results),'cases':results,'real_lesson_record_workflow_unchanged':all(sha(ROOT/p)==v for p,v in previous['original_protected_paths_before'].items()),'limits':['Original record.reviews was never changed. Explicit plan dependency declarations in copies are not independently confirmed old approvals.','Mechanical capture probes set current context fields only to test change detection. They are stored separately, never appended to copied or original reviews, and are not evidence of semantic sufficiency or authenticated review.','No notebook code was executed. Hash/region differences establish declared byte context changes only.','Legacy unbound records are not declared unaffected; expected binding/impact-confirmation work is kept separate from detected evidence/region drift.']};save(folder/'results.json',result);print(json.dumps({'label':a.label,'candidate_sha256':result['quality_code_sha256'],'case_count':len(results),'all_expectations_met':result['all_expectations_met'],'failed_cases':[x['case'] for x in results if not x['all_expectations_met']],'originals_unchanged':result['real_lesson_record_workflow_unchanged']},ensure_ascii=False));return 0 if result['all_expectations_met'] else 2
if __name__=='__main__':raise SystemExit(main())
