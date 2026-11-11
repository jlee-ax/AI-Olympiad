import hashlib,json,shutil,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;work=D/'portability-work-final';work.mkdir(exist_ok=False);repo=work/'minimal-checkout';newD=repo/'reviews/week01-rectangle-20261111/independent';newD.mkdir(parents=True)
files=['execute_notebook_case.py','rebase-case-configs.py','baseline-manifest.json','rectangle_probe.py','frozen-inputs-v2.json','rectangle_case_oracle.py','reviewer_rectangle_sample.py','oracles/reviewer-valid-other-position-same-area.py','oracles/mutant-ceil-budget.py','case-configs/portability-source-normal.json','case-configs/portability-source-error.json','final-inputs/week01_integrated.ipynb'];copied=[]
for name in files:
 src=D/name;dst=newD/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha;copied.append({'path':name,'sha256':sha,'bytes':src.stat().st_size})
cmd=[sys.executable,'-B',str(newD/'rebase-case-configs.py'),'--repo-root',str(repo),'--run-prefix','portable','--case','portability-source-normal','--case','portability-source-error'];p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,(p.stdout,p.stderr)
out=D/'portability-raw';out.mkdir(exist_ok=False);(out/'rebasing-process.json').write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n');rows=[]
for name,status,code in [('portability-source-normal','passed',0),('portability-source-error','oracle_error',1)]:
 cfg=newD/'rebased-configs/portable'/f'{name}.json';cmd=[sys.executable,'-B',str(newD/'execute_notebook_case.py'),str(cfg)];p=subprocess.run(cmd,capture_output=True,text=True);raw=newD/'runs'/('portable-'+name)/'result.json';j=json.loads(raw.read_text());assert p.returncode==code and j['status']==status and j['source_unchanged'] and j['runtime_removed']
 if code:assert j['error']['ename']=='ProbeMismatch' and 'invalid contract accepted' in j['error']['evalue']
 target=out/(name+'.json');target.write_bytes(raw.read_bytes());(out/(name+'-process.json')).write_text(json.dumps({'command':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},ensure_ascii=False,indent=2)+'\n');rows.append({'id':name,'expected_status':status,'actual_status':j['status'],'returncode':p.returncode,'raw_result':str(target.relative_to(D)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'scope':j['scope']})
for name in files:assert (D/name).read_bytes()==(newD/name).read_bytes()
shutil.rmtree(work)
summary={'status':'passed','scope':'relocated exact-byte minimum fixture, final input41/42 and reviewer sample/adapter normal plus single fault; shared existing venv, not full repository relocation or fresh install','cases':rows,'copied_input_manifest':copied,'original_files_unchanged':True,'temporary_copy_removed':not work.exists(),'student_achievement':'not_observed'}
(D/'portability-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':'passed','representative_cases':len(rows),'temporary_copy_removed':summary['temporary_copy_removed']}))
