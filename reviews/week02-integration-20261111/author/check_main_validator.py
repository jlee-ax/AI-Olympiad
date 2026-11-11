from pathlib import Path
import hashlib,json,os,subprocess,sys
r=Path.cwd();root=r/'reviews/week02-integration-20261111/author'; lesson=r/'lessons/week02'
script=lesson/'teacher_validate_week02.py'; target=root/'candidate-main.ipynb'; output=root/'main-validator-output'; run=root/'runtime-main'/'validator';run.mkdir(exist_ok=False)
for name in ['tmp','ipython','matplotlib','jupyter','cache']:(run/name).mkdir()
env=os.environ.copy();env.update(TMPDIR=str(run/'tmp'),IPYTHONDIR=str(run/'ipython'),MPLCONFIGDIR=str(run/'matplotlib'),JUPYTER_RUNTIME_DIR=str(run/'jupyter'),XDG_CACHE_HOME=str(run/'cache'),OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
watched=[lesson/'week02_prediction_evaluation.ipynb',lesson/'week02_prediction_evaluation.html',lesson/'validation.json',target]
hash_files=lambda:{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in watched}
before=hash_files();runs=[]
for name,additional in [('stdout',[]),('new_output',['--output-dir',str(output)])]:
 cmd=[sys.executable,'-B',str(script),'--inprocess','--notebook',str(target),*additional]
 result=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=180)
 (root/f'main-validator-{name}.stdout').write_text(result.stdout,encoding='utf-8')
 (root/f'main-validator-{name}.stderr').write_text(result.stderr,encoding='utf-8')
 runs.append({'mode':name,'cmd':cmd,'exit':result.returncode,'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest(),'stderr':result.stderr[-1200:]})
 assert result.returncode==0,(name,result.stdout[-800:],result.stderr[-1200:])
 assert hash_files()==before
assert {p.name for p in output.iterdir()}=={'week02_prediction_evaluation.ipynb','week02_prediction_evaluation.html','validation.json'}
validation=json.loads((output/'validation.json').read_text())
result={'runs':runs,'watched_hashes_unchanged':before,'new_output_validation':validation,'output_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}}
with (root/'main-validation-summary.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'runs':runs,'outputs':result['output_files'],'watched_unchanged':True},ensure_ascii=False))
