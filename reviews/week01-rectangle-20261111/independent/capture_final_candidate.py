from pathlib import Path
import json,hashlib,re,difflib
R=Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision');D=R/'reviews/week01-rectangle-20261111/independent';dest=D/'final-inputs';dest.mkdir(exist_ok=False)
expected={'week01_integrated.ipynb':'201e2de6ecf2a27f7a39e45744a162dfde6c26334a46370b77135ac0793047cb','week01_integrated.html':'c74c81f94996d0839ed2f5506e16746f2987c778e2fd266a614b4d607f977639','week01_integrated_teacher.md':'871bbc08dc9a678a2598c28ce9151cc74357e7d79ffe6fa5021fcfea9a814b51'};rows=[]
for n,sha in expected.items():
 src=R/'lessons/week01'/n;raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==sha;target=dest/n;target.write_bytes(raw);rows.append({'path':str(src.relative_to(R)),'snapshot':str(target.relative_to(D)),'sha256':sha,'bytes':len(raw)})
old=json.loads((D/'candidate-387b-inputs/week01_integrated.ipynb').read_text());new=json.loads((dest/'week01_integrated.ipynb').read_text());changes=[]
for i,(a,b) in enumerate(zip(old['cells'],new['cells'])):
 if a!=b:changes.append({'cell':i,'type':b['cell_type'],'source_changed':a['source']!=b['source'],'other_fields_unchanged':{k:v for k,v in a.items() if k!='source'}=={k:v for k,v in b.items() if k!='source'}})
assert len(old['cells'])==len(new['cells'])==44 and [c['cell'] for c in changes]==[17,40]
assert all(c['type']=='markdown' and c['other_fields_unchanged'] for c in changes)
assert ''.join(''.join(old['cells'][40]['source']).split())==''.join(''.join(new['cells'][40]['source']).split())
teacher=(dest/'week01_integrated_teacher.md').read_text();blocks=re.findall(r'```python\n(.*?)```',teacher,re.S);code=next(s for s in blocks if 'def rectangle_region(' in s);assert code==(D/'active-teacher-rectangle.py').read_text();(D/'final-teacher-rectangle.py').write_text(code)
assert '3,136' in ''.join(new['cells'][17]['source']) and '0.0625' in ''.join(new['cells'][17]['source'])
rebinding={'raw_case_candidate_sha256':'387b80845473172d35f9b7a979ca9f3098024b4b5c0c1b3a5df018144e16cba4','final_candidate_sha256':expected['week01_integrated.ipynb'],'actual_teacher_function_source_sha256':hashlib.sha256(code.encode()).hexdigest(),'teacher_function_bytes_unchanged':True,'case_setup_cells41_42_unchanged':all(old['cells'][i]==new['cells'][i] for i in [41,42]),'student_contract40_unchanged_ignoring_whitespace':True,'other_source_change':'Markdown17 adds correct percentage arithmetic only; no input or code changes','all_code_and_stored_outputs_unchanged':True,'raw_results_relabelled_or_overwritten':False,'scope':'Rebind same finite function/reference cases after explicit source/contract comparison; final whole notebook separately rerun.'}
(D/'v2-final-rebinding.json').write_text(json.dumps(rebinding,ensure_ascii=False,indent=2)+'\n')
(D/'final-input-manifest.json').write_text(json.dumps({'inputs':rows,'changes_vs_387b':changes,'cell_count':44,'code_cells':21,'all_code_and_stored_outputs_unchanged':True},ensure_ascii=False,indent=2)+'\n')
cfg=json.loads((D/'case-configs/initial-f19f-full.json').read_text());cfg.update(id='final-201e-full',notebook=str(dest/'week01_integrated.ipynb'),sha256=expected['week01_integrated.ipynb'],scope='final201e complete provided code and fixed example; blank responses not learner achievement')
(D/'case-configs/final-201e-full.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'final_snapshot_captured':True,'changes':changes,'all_code_output_unchanged':True,'v2_rebinding_possible':True}))
print('FINAL17_ADDED_SENTENCE\n'+''.join(difflib.unified_diff(''.join(old['cells'][17]['source']).splitlines(True),''.join(new['cells'][17]['source']).splitlines(True))))
