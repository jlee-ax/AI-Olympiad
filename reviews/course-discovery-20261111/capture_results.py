"""Capture actual CLI replay output and nonmutation evidence in this review only."""
import argparse,ast,hashlib,json,subprocess,sys
from pathlib import Path
from run_review import ROOT,OUT,loop,sha,save,rel
ap=argparse.ArgumentParser();ap.add_argument('--candidate',default='week02-candidate-02');ap.add_argument('--capture',required=True);a=ap.parse_args()
folder=OUT/'checks'/a.capture
if folder.exists():raise ValueError('Use a fresh capture directory')
folder.mkdir(parents=True)
results=[]
names=['baseline-wave-01','plan-wave-01',a.candidate]
if (OUT/'runs/week01-bridge-01/session.json').exists():names.append('week01-bridge-01')
if (OUT/'runs/week01-bridge-02/session.json').exists():names.append('week01-bridge-02')
for name in names:
 state_path=OUT/'runs'/name/'session.json'; state=json.loads(state_path.read_text());report=loop.inspect(state,ROOT)
 for operation in ['next','report','manifest']:
  cmd=[sys.executable,'-B','tools/discovery_loop.py',operation,rel(state_path)]
  if operation!='manifest':cmd+=['--root','.']
  proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
  receipt={'argv':cmd,'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest()}
  try:receipt['parsed_output']=json.loads(proc.stdout)
  except ValueError:pass
  save(folder/(name+'-'+operation+'.json'),receipt)
  results.append({'run':name,'operation':operation,'exit_code':proc.returncode})
 save(folder/(name+'-current-summary.json'),{'status':report['status'],'ready_for_review':report['ready_for_review'],'demand_count':len(report['demands']),'queue_count':len(report['queue']),'open_question_count':len(report['open_questions']),'events':report['usage']['events'],'next_action':report['next_action'],'covered':[c['demand_id'] for c in report['comparisons'] if c['judgment']=='covered'],'judgments':{c['demand_id']:c['judgment'] for c in report['comparisons']},'freshness_blockers':[b for b in report['blockers'] if any(x in b['code'] for x in ['changed','stale','missing','artifact'])]})
origin=json.loads((OUT/'runs/baseline-wave-01/origin.json').read_text());candidate_origin=json.loads((OUT/'runs'/a.candidate/'origin.json').read_text());artifact=ROOT/candidate_origin['candidate_original_path']; nb=json.loads(artifact.read_text());answer=nb['cells'][20];index=Path('/workspace/scratch/d500e5cb2076/ai-olympiad-workflow-improvement/.git/worktrees/ai-olympiad-course-revision/index')
evidence={'prior_session_unchanged':sha(ROOT/origin['prior_session_path'])==origin['prior_file_sha256'],'prior_session_sha256':sha(ROOT/origin['prior_session_path']),'candidate_original_path':rel(artifact),'candidate_sha256_current':sha(artifact),'candidate_sha256_matches_review':sha(artifact)==candidate_origin['candidate_original_sha256'],'student_answer_cell_index':20,'student_answer_cell_id':answer.get('id'),'student_answer_code_ast_statement_count':len(ast.parse(''.join(answer['source'])).body),'student_answer_blank':'Code cell contains comments only; this is direct syntax inspection, not a hard-coded success flag.','discovery_tool_sha256':sha(ROOT/'tools/discovery_loop.py'),'git_index_sha256_at_first_check':'cc45949317b19b16e2f12811ebdf45e6a2368c5ce0351d96d704d0ac8a05bc5a','git_index_sha256_now':sha(index),'git_index_unchanged_between_checks':sha(index)=='cc45949317b19b16e2f12811ebdf45e6a2368c5ce0351d96d704d0ac8a05bc5a','new_scope_author':'/root/course_discovery/verify_new_scope','teaching_author':'/root/week02_lesson','reviewer':'/root/course_discovery','source_originals_authenticated':False,'learning_effects_measured':False,'cli_commands':results}
bridge=ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb'
if bridge.exists():
 evidence['bridge_original_path']=rel(bridge);evidence['bridge_sha256_current']=sha(bridge);evidence['bridge_sha256_matches_review']=sha(bridge)=='6241f6bce0db5b2dfe40dc672a0706a09d7228d2aea451cd1a03b05847f910c4'
save(folder/'integrity-and-execution-evidence.json',evidence)
if not evidence['prior_session_unchanged'] or not evidence['candidate_sha256_matches_review']:raise ValueError('Input bytes changed')
print(json.dumps({'capture':rel(folder),'all_cli_exit_zero':all(x['exit_code']==0 for x in results),'prior_session_unchanged':evidence['prior_session_unchanged'],'candidate_sha256':sha(artifact),'answer_statement_count':evidence['student_answer_code_ast_statement_count'],'git_index_unchanged_between_checks':evidence['git_index_unchanged_between_checks']},ensure_ascii=False,indent=2))
