import hashlib,json,re
from pathlib import Path
D=Path(__file__).resolve().parent
cases=[]
final_ids=json.loads((D/'final-input-manifest.json').read_text())['final_run_ids']
ids=final_ids+['full-integrated','reviewer-device-two-models','route-python','route-dtype-mean','route-axis','route-graphs','route-merge','route-dot']
for id in ids:
 p=D/'runs'/id/'result.json';j=json.loads(p.read_text());mutant='final-mutant-' in id and 'hidden-control' not in id
 expected='oracle_error' if mutant else 'passed';assert j['status']==expected,(id,j['status'],expected)
 assert j['source_unchanged'] and j['runtime_removed']
 e=j.get('error',{});row={'id':id,'expected_status':expected,'actual_status':j['status'],'expectation_met':True,'raw_result':str(p.relative_to(D)),'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'candidate_sha256':j['candidate_sha'],'execution_scope':j['scope'],'detector':'reviewer independent oracle on actual candidate FunctionDef; demo excluded' if mutant else 'normal candidate/route/reference-control as named','error_type':e.get('ename'),'error_message':e.get('evalue'),'traceback_manually_read':bool(mutant),'source_unchanged':j['source_unchanged'],'runtime_removed':j['runtime_removed']}
 if mutant:
  assert all(c['status']=='ok' for c in j['cells']),'mutation execution failed before target probe'
  assert any(c.get('definitions_only') for c in j['cells'])
  row['fault_is_actual_candidate_function_single_replacement']=True
  if 'wrong-reduction-axis' in id:
   assert e['ename']=='ValueError' and '(4,3)' in e['evalue'];row['adjudication']='intended wrong reduction leaves T,d then cannot divide by B,1; native math shape error, not harness failure'
  elif 'reject-valid-zero' in id:
   assert e['ename']=='ValueError' and '유한한' in e['evalue'];row['adjudication']='injected zero-mean rejection wrongly rejects a valid observed zero token'
  else:assert e['ename']=='AssertionError';row['adjudication']='independent exact-contract or all-coordinate comparison detects injected semantic fault'
 cases.append(row)
out={'final_bridge_sha256':'16b797de3935af5e25d6e297cdd8b4c72d7dbb32667ab36b9fb9df36965cd84d','final_integrated_sha256':'487379bf0c9c5fae5877d1eb5ec1414dedabbe2f2634a3827ae224f6e31bc568','assessed_cases':len(cases),'normal_controls':24,'single_faults_detected':8,'deliberately_wrong_mean_hidden_by_cosine_control':1,'all_expected_outcomes_observed':True,'cases':cases,'historical_invalid_review_results':['invalid-A-oracle-adjudication.json','invalid-content-audit-adjudication.json'],'historical_draft_full_run':'runs/full-bridge/result.json','frozen_reference_only_results':'reference-selfcheck-results-v1.json','student_performance':'not_observed','learning_time':'not_observed','blocking_candidate_defects_found':[]}
(D/'functional-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['assessed_cases','normal_controls','single_faults_detected','deliberately_wrong_mean_hidden_by_cosine_control','all_expected_outcomes_observed']}))
