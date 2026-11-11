import hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent;decoder=json.JSONDecoder()
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def payloads(j):
 text=''.join(o.get('text','') for o in j.get('oracle',{}).get('outputs',[]) if o.get('output_type')=='stream');out=[]
 while text.strip():
  text=text.lstrip();obj,end=decoder.raw_decode(text);out.append(obj);text=text[end:]
 return out
expected=json.loads((D/'v2-expectations.json').read_text());fixture=json.loads((D/'frozen-inputs-v2.json').read_text());byid={c['id']:c for c in fixture['cases']};rows=[]
for item in expected['normal_cases']:
 id=item['id'];p=D/'runs'/id/'result.json';j=json.loads(p.read_text());assert j['status']=='passed';data=payloads(j);report=next(x for x in data if 'case_id' in x);case=byid[report['case_id']]
 if case['expected_valid']:
  assert report['status']=='passed';semantic='valid_output_matches_frozen_coordinates_and_2d_values';manual=False
 else:
  assert report['status']=='rejection_observed_pending_manual_traceback_review';err=report['raw_exception'];assert err['type']=='ValueError'
  area=any(s in id for s in ['budget','ceiling']);guard='area_maximum' if area else 'nonempty_coordinate_bounds'
  wanted=('남길 수 있는 칸 수를 넘었습니다' if area else '비어 있거나 격자 밖인 영역입니다') if id.startswith('teacher-') else ('rectangle spatial area exceeds declared maximum' if area else 'rectangle coordinates violate declared nonempty bounds')
  assert err['message']==wanted and 'in rectangle_region' in err['traceback'] if id.startswith('teacher-') else err['message']==wanted and 'in reviewer_rectangle_region' in err['traceback']
  semantic='expected_contract_rejection_after_manual_traceback_review';manual=True
 rows.append({'id':id,'scope':item['scope'],'expected':item['expected_semantic_outcome'],'worker_status':j['status'],'actual_semantic_outcome':semantic,'expectation_met':True,'manual_traceback_adjudicated':manual,'raw_result':str(p.relative_to(D)),'sha256':digest(p),'original_unchanged':report['original_unchanged'],'runtime_removed':j['runtime_removed']})
messages={'inclusive-stop':'same shape/area is insufficient: selected coordinate set differs','swap-spatial-axes':'same shape/area is insufficient: selected coordinate set differs','reject-valid-stop':'valid declared input raised an exception','allow-clipping':'invalid contract accepted; small/clipped/zero-valued slice is insufficient','channel-budget':'invalid contract accepted; small/clipped/zero-valued slice is insufficient','ceil-budget':'invalid contract accepted; small/clipped/zero-valued slice is insufficient','mutate-original':'adapter/solution modified original image, including on rejected input','count-values-not-area':'invalid contract accepted; small/clipped/zero-valued slice is insufficient'}
for item in expected['single_fault_cases']:
 id=item['id'];p=D/'runs'/id/'result.json';j=json.loads(p.read_text());err=j['error'];assert j['status']=='oracle_error' and err['ename']=='ProbeMismatch';assert err['evalue']==messages[id.removeprefix('mutant-')];assert all(c['status']=='ok' for c in j['cells'])
 rows.append({'id':id,'scope':item['scope'],'expected':'independent oracle detects single injected fault','worker_status':j['status'],'actual_semantic_outcome':err['evalue'],'expectation_met':True,'manual_traceback_adjudicated':True,'mutated_actual_student_notebook':False,'detector':'frozen reviewer oracle, not learner or lesson auto-grader','raw_result':str(p.relative_to(D)),'sha256':digest(p),'runtime_removed':j['runtime_removed']})
routeids=['final-201e-full','final-route-python','final-route-dtype-mean','final-route-axis','final-route-graphs','final-route-merge','final-route-dot','final-integrated-T-route','final-bridge-A-route','final-bridge-B-route','final-reviewer-device-two-models']
for id in routeids:
 p=D/'runs'/id/'result.json';j=json.loads(p.read_text());assert j['status']=='passed' and j['source_unchanged'] and j['runtime_removed'];rows.append({'id':id,'scope':j['scope'],'expected':'passed','actual_semantic_outcome':'passed with scope limits; blank responses not completed','expectation_met':True,'raw_result':str(p.relative_to(D)),'sha256':digest(p),'runtime_removed':j['runtime_removed']})
assert len(rows)==47
out={'final_notebook_sha256':'201e2de6ecf2a27f7a39e45744a162dfde6c26334a46370b77135ac0793047cb','assessed_cases':47,'normal_output_or_route_controls':21,'expected_contract_rejections_manually_adjudicated':18,'injected_reference_or_adapter_faults_detected':8,'all_expected_outcomes_observed':True,'blocking_candidate_defects_found':[],'records':rows,'raw_v2_binding_preserved':'387b80845473172d35f9b7a979ca9f3098024b4b5c0c1b3a5df018144e16cba4','final_rebinding_evidence':'v2-final-rebinding.json','old_full_runs_retained':['runs/initial-f19f-full/result.json','runs/candidate-387b-full/result.json'],'invalid_reviewer_preparation_attempt':'invalid-capture-attempt-01.json','exposed_v1_not_used':True,'RGB_implementation':'not_required_not_tested; channel arithmetic and spatial 2D mask only','student_performance_and_actual_time':'not_observed'}
(D/'functional-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['assessed_cases','normal_output_or_route_controls','expected_contract_rejections_manually_adjudicated','injected_reference_or_adapter_faults_detected']}))
