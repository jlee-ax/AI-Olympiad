import hashlib,json,shutil,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parents[2];work=D/'portability-work-final';work.mkdir(exist_ok=False);copy=work/'minimal-checkout';newD=copy/'reviews/week01-sequence-20261111/independent';newD.mkdir(parents=True)
names=['execute_sequence_case.py','rebase-case-configs.py','baseline-manifest.json','native_sequence_checks.py','independent-inputs-and-expectations.json','oracle-native-base.py','oracle-mutant-wrong-T-denominator.py','case-configs/final-native-base.json','case-configs/final-mutant-wrong-T-denominator.json']
notebook='lessons/week01/week01_axes_linear_bridge.ipynb';records=[]
for rel,src,dst in [(x,D/x,newD/x) for x in names]+[(notebook,R/notebook,copy/notebook)]:
 dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());sha=hashlib.sha256(src.read_bytes()).hexdigest();assert hashlib.sha256(dst.read_bytes()).hexdigest()==sha;records.append({'relative_path':rel,'sha256':sha,'bytes':src.stat().st_size})
rebase_command=[sys.executable,'-B',str(newD/'rebase-case-configs.py'),'--repo-root',str(copy),'--run-prefix','portable','--case','final-native-base','--case','final-mutant-wrong-T-denominator']
r=subprocess.run(rebase_command,capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
out=D/'portability-raw';out.mkdir(exist_ok=False);(out/'rebasing-process.json').write_text(json.dumps({'command':rebase_command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
results=[]
for name,expected in [('final-native-base','passed'),('final-mutant-wrong-T-denominator','oracle_error')]:
 cfg=newD/'rebased-configs/portable'/f'{name}.json';command=[sys.executable,'-B',str(newD/'execute_sequence_case.py'),str(cfg)];q=subprocess.run(command,capture_output=True,text=True)
 raw=newD/'runs'/('portable-'+name)/'result.json';j=json.loads(raw.read_text());assert j['status']==expected and q.returncode==(0 if expected=='passed' else 1)
 assert j['source_unchanged'] and j['runtime_removed']
 if expected=='oracle_error':assert j['error']['ename']=='AssertionError' and j['error']['evalue']=="('values', 4)"
 target=out/(name+'.json');target.write_bytes(raw.read_bytes())
 (out/(name+'-process.json')).write_text(json.dumps({'command':command,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr},ensure_ascii=False,indent=2)+'\n')
 results.append({'id':name,'expected_status':expected,'actual_status':j['status'],'returncode':q.returncode,'raw_result':str(target.relative_to(D)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'new_candidate_path':j['notebook']})
# Recheck original + copied bytes before removing only the newly created temporary copy.
for rel,src,dst in [(x,D/x,newD/x) for x in names]+[(notebook,R/notebook,copy/notebook)]:assert src.read_bytes()==dst.read_bytes()
shutil.rmtree(work)
summary={'status':'passed','scope':'two representative paths from relocated exact-byte minimal checkout; shared existing venv, not fresh dependency installation or full repo regression','copied_inputs':records,'cases':results,'new_config_only':True,'original_frozen_and_config_bytes_unchanged':True,'temporary_copy_removed':not work.exists(),'student_time_and_achievement':'unobserved'}
(D/'portability-results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':summary['status'],'cases':results,'temporary_copy_removed':summary['temporary_copy_removed']}))
