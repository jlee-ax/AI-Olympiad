from pathlib import Path
import json,hashlib,difflib,re
R=Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision');D=R/'reviews/week01-rectangle-20261111/independent';(D/'candidate-387b-inputs').mkdir(exist_ok=False)
expected={'week01_integrated.ipynb':'387b80845473172d35f9b7a979ca9f3098024b4b5c0c1b3a5df018144e16cba4','week01_integrated.html':'8879c7d0b668a2f215406808cb1b54404c0590e47d4fadb47a7b55094d17143d','week01_integrated_teacher.md':'de3ac1b2b84a81f9a52abce0e351d29a4cbb92c52db2ad9794eeeec021df65c3'};rows=[]
for n,sha in expected.items():
 p=R/'lessons/week01'/n;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;(D/'candidate-387b-inputs'/n).write_bytes(raw);rows.append({'path':str(p.relative_to(R)),'snapshot':'candidate-387b-inputs/'+n,'sha256':sha,'bytes':len(raw)})
a=json.loads((D/'initial-inputs/week01_integrated.ipynb').read_text());b=json.loads((D/'candidate-387b-inputs/week01_integrated.ipynb').read_text());changes=[]
for i,(x,y) in enumerate(zip(a['cells'],b['cells'])):
 if x!=y:changes.append({'cell':i,'type':y['cell_type'],'source_changed':x['source']!=y['source'],'other_fields_unchanged':{k:v for k,v in x.items() if k!='source'}=={k:v for k,v in y.items() if k!='source'}})
assert len(a['cells'])==len(b['cells'])==44 and [x['cell'] for x in changes]==[17,40]
assert all(x['type']=='markdown' and x['source_changed'] and x['other_fields_unchanged'] for x in changes)
(D/'candidate-387b-manifest.json').write_text(json.dumps({'inputs':rows,'cell_count':44,'code_cells':sum(c['cell_type']=='code' for c in b['cells']),'initial_final_cell_changes':changes,'all_code_and_stored_outputs_unchanged':True},ensure_ascii=False,indent=2)+'\n')
for i in [17,40]:print('CELL',i,'\n'+''.join(b['cells'][i]['source']))
old=(D/'initial-inputs/week01_integrated_teacher.md').read_text();new=(D/'candidate-387b-inputs/week01_integrated_teacher.md').read_text();print('TEACHER_DIFF\n'+''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True))))
for kind,folder in [('initial','initial-inputs'),('candidate-387b','candidate-387b-inputs')]:
 text=(D/folder/'week01_integrated_teacher.md').read_text();blocks=re.findall(r'```python\n(.*?)```',text,re.S);codes=[x for x in blocks if 'def rectangle_region(' in x];assert len(codes)==1;(D/f'{kind}-teacher-rectangle.py').write_text(codes[0])
assert (D/'initial-teacher-rectangle.py').read_bytes()==(D/'candidate-387b-teacher-rectangle.py').read_bytes()
cfg=json.loads((D/'case-configs/initial-f19f-full.json').read_text());cfg.update(id='candidate-387b-full',notebook=str(D/'candidate-387b-inputs/week01_integrated.ipynb'),sha256=expected['week01_integrated.ipynb'],scope='candidate387b complete provided code, fixed example and existing fit/CSV; blank responses are not achievement')
(D/'case-configs/candidate-387b-full.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
print('CANDIDATE_387B_SNAPSHOT_CAPTURED')
