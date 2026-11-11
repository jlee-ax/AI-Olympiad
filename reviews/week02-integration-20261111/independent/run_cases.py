import concurrent.futures,json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent
def run(name):
 p=subprocess.run([sys.executable,'-B',str(D/'execute_notebook_case.py'),str(D/'case-configs'/f'{name}.json')],capture_output=True,text=True)
 target=D/'runs'/name/'process.json';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps({'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr},ensure_ascii=False,indent=2)+'\n');return {'id':name,'returncode':p.returncode,'stdout':p.stdout.strip()}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for row in pool.map(run,sys.argv[1:]):print(json.dumps(row,ensure_ascii=False),flush=True)
