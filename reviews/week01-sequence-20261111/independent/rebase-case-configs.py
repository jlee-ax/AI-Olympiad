"""Create fresh configs only. No frozen input, original config/log or candidate is modified."""
import argparse,datetime,hashlib,json
from pathlib import Path
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--repo-root',required=True);p.add_argument('--case',action='append',required=True);p.add_argument('--run-prefix',default=datetime.datetime.now(datetime.timezone.utc).strftime('replay-%Y%m%dT%H%M%S%f'));a=p.parse_args()
assert a.run_prefix and all(c.isalnum() or c in '-_' for c in a.run_prefix)
repo=Path(a.repo_root).resolve();oldrepo=Path(json.loads((D/'baseline-manifest.json').read_text())['repo_root']);newD=repo/'reviews/week01-sequence-20261111/independent';assert newD.is_dir()
out=newD/'rebased-configs'/a.run_prefix;out.mkdir(parents=True,exist_ok=False);rows=[]
for name in a.case:
 source=D/'case-configs'/f'{name}.json';cfg=json.loads(source.read_text());cfg['id']=a.run_prefix+'-'+cfg['id']
 for key in ['notebook','oracle']:
  if cfg.get(key):cfg[key]=str(repo/Path(cfg[key]).relative_to(oldrepo));assert Path(cfg[key]).is_file()
 actual=hashlib.sha256(Path(cfg['notebook']).read_bytes()).hexdigest();assert actual==cfg['sha256']
 target=out/source.name;target.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
 rows.append({'original_config':str(source),'original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'new_config':str(target),'new_id':cfg['id'],'candidate_sha256':actual})
manifest={'method':'new config path fields rebased from frozen old repo to explicit repo-root; unique output IDs; exact candidate SHA required','original_files_unchanged':True,'old_repo':str(oldrepo),'new_repo':str(repo),'configs':rows}
(out/'rebasing-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
