"""Relocate minimal exact assets; preserve existing logs/settings and remove only our temporary copy."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--python',required=True);args=p.parse_args();repo=BASE.parents[2]
result_dir=BASE/'relocation-results';result_dir.mkdir(exist_ok=False)
temp=Path(tempfile.mkdtemp(prefix='relocation-copy-',dir=BASE));new_repo=temp/'checkout'
new_base=new_repo/'reviews/week01-retrieval-20261111/independent';new_base.mkdir(parents=True)
cases=['full-bridge','mutant-zero-silent']
assets=['baseline-manifest.json','execute_candidate_case.py','native_probe.py','rebase-case-configs.py','independent-inputs-and-expectations.json','independent-3d-addendum.json','probe-oracles/mutant-zero-silent.py']+[f'case-configs/{x}.json' for x in cases]
copy_manifest=[]
for rel,src in [('lessons/week01/week01_axes_linear_bridge.ipynb',repo/'lessons/week01/week01_axes_linear_bridge.ipynb')]+[('reviews/week01-retrieval-20261111/independent/'+x,BASE/x) for x in assets]:
    dst=new_repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());copy_manifest.append({'path':rel,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
config_before={x:hashlib.sha256((BASE/'case-configs'/f'{x}.json').read_bytes()).hexdigest() for x in cases}
summary={'copy_type':'temporary minimal exact asset copy, not a full git clone','shared_venv':args.python,'temporary_repo':str(new_repo),'copied_files':copy_manifest,'rows':[]}
try:
    cmd=[args.python,'-B',str(new_base/'rebase-case-configs.py'),'--repo-root',str(new_repo)]
    for x in cases:cmd+=['--case',x]
    r=subprocess.run(cmd,cwd=new_repo,capture_output=True,text=True)
    (result_dir/'rebasing-process.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2)+'\n');assert r.returncode==0
    (result_dir/'rebasing-manifest.json').write_bytes((new_base/'rebased-configs/rebasing-manifest.json').read_bytes())
    for case in cases:
        cmd=[args.python,'-B',str(new_base/'execute_candidate_case.py'),str(new_base/'rebased-configs'/f'{case}.json')]
        r=subprocess.run(cmd,cwd=new_repo,capture_output=True,text=True,timeout=180)
        (result_dir/f'{case}-process.json').write_text(json.dumps({'command':cmd,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2)+'\n')
        raw=json.loads((new_base/'runs'/case/'result.json').read_text());(result_dir/f'{case}-result.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        match=raw['status']=='passed' if case=='full-bridge' else raw['status']=='oracle_error' and raw['error']['ename']=='AssertionError' and raw['error']['evalue']=='candidate stated zero rejection did not occur'
        summary['rows'].append({'case':case,'status':raw['status'],'returncode':r.returncode,'matched_expected':match,'source_unchanged':raw['source_unchanged'],'runtime_removed':raw['runtime_removed']});assert match
    summary['original_configs_unchanged']=all(hashlib.sha256((BASE/'case-configs'/f'{x}.json').read_bytes()).hexdigest()==config_before[x] for x in cases)
    summary['original_source_unchanged']=hashlib.sha256((repo/'lessons/week01/week01_axes_linear_bridge.ipynb').read_bytes()).hexdigest()==copy_manifest[0]['sha256']
    assert summary['original_configs_unchanged'] and summary['original_source_unchanged'];summary['status']='passed'
except Exception as e:summary.update(status='failed',error={'type':type(e).__name__,'message':str(e)})
finally:
    assert temp.is_relative_to(BASE) and temp.name.startswith('relocation-copy-');shutil.rmtree(temp);summary['temporary_copy_removed']=not temp.exists()
    (result_dir/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2));raise SystemExit(0 if summary['status']=='passed' else 1)
