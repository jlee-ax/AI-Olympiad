"""Representative path relocation, using a temporary minimal asset copy, not a full git clone."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--python',required=True);args=p.parse_args()
repo=BASE.parents[2]
output=BASE/'relocation-results';output.mkdir(exist_ok=False)
temp=Path(tempfile.mkdtemp(prefix='relocation-copy-',dir=BASE));new_repo=temp/'checkout'
new_base=new_repo/'reviews/week01-deepening-20261111/independent'
new_base.mkdir(parents=True)
relative_files=['lessons/week01/week01_integrated.ipynb']
local_files=['baseline-manifest.json','execute_candidate_case.py','rebase-case-configs.py','oracle-full.py','oracle-native-aggregation.py']
cases=['full-candidate','native-aggregation','mutant-memory-replaces-physical']
copy_manifest=[]
for rel in relative_files:
    src=repo/rel;dst=new_repo/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    copy_manifest.append({'path':rel,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
for rel in local_files+[f'case-configs/{case}.json' for case in cases]:
    src=BASE/rel;dst=new_base/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
    copy_manifest.append({'path':'reviews/week01-deepening-20261111/independent/'+rel,'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
original_config_hashes={case:hashlib.sha256((BASE/'case-configs'/f'{case}.json').read_bytes()).hexdigest() for case in cases}
rows=[]
summary={'copy_type':'temporary minimal asset checkout copy, not a full git clone','shared_dependency_environment':args.python,'original_repo':str(repo),'temporary_repo':str(new_repo),'copied_files':copy_manifest,'candidate_sha256':copy_manifest[0]['sha256'],'expected':{'full-candidate':'passed','native-aggregation':'passed','mutant-memory-replaces-physical':'intentional physical-file assertion rejection'},'rows':rows}
try:
    command=[args.python,'-B',str(new_base/'rebase-case-configs.py'),'--repo-root',str(new_repo)]
    for case in cases:command+=['--case',case]
    r=subprocess.run(command,cwd=new_repo,capture_output=True,text=True)
    (output/'rebasing-process.json').write_text(json.dumps({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2)+'\n')
    assert r.returncode==0
    (output/'rebasing-manifest.json').write_bytes((new_base/'rebased-configs/rebasing-manifest.json').read_bytes())
    for case in cases:
        command=[args.python,'-B',str(new_base/'execute_candidate_case.py'),str(new_base/'rebased-configs'/f'{case}.json')]
        r=subprocess.run(command,cwd=new_repo,capture_output=True,text=True,timeout=180)
        (output/f'{case}-process.json').write_text(json.dumps({'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=False,indent=2)+'\n')
        raw=json.loads((new_base/'runs'/case/'result.json').read_text())
        (output/f'{case}-result.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
        matched=raw['status']=='passed' if not case.startswith('mutant-') else raw['status']=='harness_or_assertion_error' and raw['error']['message']=='actual notebook physical file write/read missing: result.csv'
        rows.append({'id':case,'actual':raw['status'],'returncode':r.returncode,'matched_expected':matched,'source_unchanged':raw['source_unchanged'],'runtime_removed':raw['runtime_removed']})
        assert matched
    summary['original_config_hashes_unchanged']=all(hashlib.sha256((BASE/'case-configs'/f'{case}.json').read_bytes()).hexdigest()==original_config_hashes[case] for case in cases)
    summary['original_source_unchanged']=hashlib.sha256((repo/relative_files[0]).read_bytes()).hexdigest()==copy_manifest[0]['sha256']
    assert summary['original_config_hashes_unchanged'] and summary['original_source_unchanged']
    summary['status']='passed'
except Exception as e:
    summary.update(status='failed',error={'type':type(e).__name__,'message':str(e)})
finally:
    assert temp.is_relative_to(BASE) and temp.name.startswith('relocation-copy-')
    shutil.rmtree(temp)
    summary['temporary_copy_removed']=not temp.exists()
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
raise SystemExit(0 if summary['status']=='passed' else 1)
