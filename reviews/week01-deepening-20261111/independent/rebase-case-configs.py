"""Write new rebased configs; preserve original configs/logs/frozen inputs unchanged."""
import argparse,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--repo-root',required=True);p.add_argument('--case',action='append',dest='cases');args=p.parse_args()
repo=Path(args.repo_root).resolve();old_repo=Path(json.loads((BASE/'baseline-manifest.json').read_text())['root'])
new_base=repo/'reviews/week01-deepening-20261111/independent'
assert new_base.is_dir()
out=new_base/'rebased-configs';out.mkdir(exist_ok=False)
selected=[BASE/'case-configs'/f'{name}.json' for name in args.cases] if args.cases else sorted((BASE/'case-configs').glob('*.json'))
rows=[]
for path in selected:
    old=json.loads(path.read_text());new=dict(old)
    for key in ['notebook','oracle']:
        if old.get(key):
            rel=Path(old[key]).relative_to(old_repo)
            new[key]=str(repo/rel)
            assert Path(new[key]).is_file(),new[key]
    assert hashlib.sha256(Path(new['notebook']).read_bytes()).hexdigest()==new['sha256']
    target=out/path.name;target.write_text(json.dumps(new,ensure_ascii=False,indent=2)+'\n')
    rows.append({'input_config':str(path),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'new_config':str(target),'new_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'notebook':new['notebook'],'oracle':new.get('oracle'),'candidate_sha256':new['sha256']})
manifest={'old_repo_from_frozen_manifest':str(old_repo),'new_repo':str(repo),'method':'Only notebook/oracle path fields are rebased relative to frozen repo root. No source/oracle/config/log/frozen baseline is modified.','configs':rows}
(out/'rebasing-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
