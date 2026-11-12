"""Independent source and boundary audit; no student solution is executed."""
from pathlib import Path
from hashlib import sha256
from contextlib import redirect_stdout
from io import StringIO
import argparse, difflib, json, re, subprocess
import numpy as np
import pandas as pd

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,required=True)
parser.add_argument('--base-ref',default='eb154346cfbc2f182f51a17e8b84a319f972dafb',help='Git reference for the approved preceding candidate')
parser.add_argument('--candidate-sha',required=True)
parser.add_argument('--teacher-sha',required=True)
parser.add_argument('--with-progress',action='store_true')
a=parser.parse_args();root=a.root.resolve();lesson=root/'lessons/week01'
if not re.fullmatch(r'[A-Za-z0-9._/-]+',a.base_ref):raise ValueError('invalid base ref')
raw=(lesson/'week01_integrated.ipynb').read_bytes()
assert sha256(raw).hexdigest()==a.candidate_sha
teacher=(lesson/'week01_integrated_teacher.md').read_bytes()
assert sha256(teacher).hexdigest()==a.teacher_sha
new=json.loads(raw);old=json.loads(subprocess.check_output(['git','show',a.base_ref+':lessons/week01/week01_integrated.ipynb'],cwd=root))
assert len(old['cells'])==len(new['cells'])==46
assert [c['id'] for c in old['cells']]==[c['id'] for c in new['cells']]
def src(c):
 s=c['source'];return s if isinstance(s,str) else ''.join(s)
oldmap={c['id']:c for c in old['cells']};cells={c['id']:c for c in new['cells']}
changed={k for k in cells if src(cells[k])!=src(oldmap[k])}
expected_changes={'deep-count-intro','deep-count-code','303c6117'}
if a.with_progress:expected_changes.add('4042bdda')
assert changed==expected_changes,changed
if a.with_progress:
 before=src(oldmap['4042bdda']).splitlines();after=src(cells['4042bdda']).splitlines()
 operations=list(difflib.SequenceMatcher(a=before,b=after,autojunk=False).get_opcodes())
 assert all(op in ('equal','insert') for op,_,_,_,_ in operations),operations
 inserted='\n'.join('\n'.join(after[j:k]) for op,_,_,j,k in operations if op=='insert')
 assert '미완료' in inserted and '도움' in inserted and '다음' in inserted,inserted
 assert not re.search(r'\d+\s*(?:분|시간)|수업 시간|자습 시간|실제 시간|걸린 시간',inserted),inserted

for k in cells:
 assert cells[k]['cell_type']==oldmap[k]['cell_type']
 assert cells[k].get('attachments')==oldmap[k].get('attachments')
for k in ['9462ed76','e49ac1c2','exercise-validation-release','exercise-validation-answer','rectangle-independent-input','rectangle-independent-answer']:
 assert src(cells[k])==src(oldmap[k]),k
for k in ['e49ac1c2','exercise-validation-answer','rectangle-independent-answer']:
 assert all(not line.strip() or line.lstrip().startswith('#') for line in src(cells[k]).splitlines())
 assert not cells[k].get('outputs')

# Only the completed plant setup and new worked example are executed.
def context(transform=None):
 ns={}
 with redirect_stdout(StringIO()):
  exec(src(cells['484f22ba']),ns)
  exec(src(cells['deep-leaf-grid']),ns)
  if transform is not None:ns['plants']=transform(ns['plants'])
  exec(src(cells['deep-count-code']),ns)
 return ns

def reordered(frame):
 q=frame.copy();q.index=[101,3,22,54,8,31]
 return q.iloc[[4,2,5,0,3,1]]

def reordered_duplicate_index(frame):
 q=frame.copy();q.index=[101,101,8,8,3,3]
 return q.iloc[[4,2,5,0,3,1]]

normal=context();shuffled=context(reordered);duplicate_index=context(reordered_duplicate_index)
expected={'P01':0,'P02':1,'P03':2,'P04':3,'P05':2,'P06':3}
for ns in [normal,shuffled,duplicate_index]:
 col=ns['observation_column'];rows=ns['leaf_rows'];images=ns['leaf_images'];count=ns['count_yellow_leaf']
 assert isinstance(col,pd.Series) and col.shape==(6,) and col.dtype==object
 assert list(rows['pot_id'])==list(ns['plants']['pot_id'])
 for pot, observation in zip(rows['pot_id'],col):
  assert observation.shape==(2,2,2)
  np.testing.assert_array_equal(observation,images[pot]);assert count(observation)==expected[pot]
  assert not np.shares_memory(observation,images[pot])
 selected=rows.loc[rows.pot_id.eq('P02'),'observation'].iloc[0]
 extracted=ns['p02_from_table']
 assert extracted.shape==(2,2,2) and count(extracted)==1
 np.testing.assert_array_equal(extracted,images['P02'])
 assert not np.shares_memory(extracted,selected)
 old_table=selected.copy();old_dict=images['P02'].copy();extracted[0,1,1]=0
 np.testing.assert_array_equal(selected,old_table);np.testing.assert_array_equal(images['P02'],old_dict)
 # Mutating a table cell must not alter its corresponding original dictionary array.
 p01=rows.loc[rows.pot_id.eq('P01'),'observation'].iloc[0];old_p01=images['P01'].copy()
 p01[0,0,1]=1-p01[0,0,1];np.testing.assert_array_equal(images['P01'],old_p01)
assert shuffled['plants'].index.tolist()==[8,22,31,101,54,3]
assert shuffled['leaf_rows']['pot_id'].iloc[-1]=='P02'

errors=[]
for name,transform in [
 ('missing_p02',lambda f:f.loc[f.pot_id.ne('P02')].copy()),
 ('duplicate_p02',lambda f:pd.concat([f,f.loc[f.pot_id.eq('P02')]],ignore_index=True)),
]:
 try:context(transform)
 except ValueError as e:
  assert 'P02' in str(e);errors.append(name)
 else:raise AssertionError(name+' was not rejected')

# No source, teacher, 2nd week or curriculum files are altered outside the candidate.
for rel in ['week01_python_tables.ipynb','teacher-notes.txt','week01_axes_linear_bridge.ipynb','week01_axes_linear_bridge_teacher.md','week01_integrated_validation_labels.csv']:
 p='lessons/week01/'+rel
 prior=subprocess.check_output(['git','show',a.base_ref+':'+p],cwd=root)
 assert (root/p).read_bytes()==prior,p
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','lessons/week02','curriculum'],cwd=root,text=True)
main=json.loads((lesson/'week01_python_tables.ipynb').read_bytes())
bridge=json.loads((lesson/'week01_axes_linear_bridge.ipynb').read_bytes())
pipeline=json.loads((lesson/'week01_problem_pipeline.ipynb').read_bytes())
lookup={c['id']:src(c) for n in [main,bridge,pipeline] for c in n['cells']}
required={'0fd965eb':'과제 C','depth-function-spec':'과제 D','d0ddef13':'과제 E',
          'c6d01f13':'함수를 고쳐 새 입력','08bf506c':'분산','b38de2c6':'도움 없이 해 볼',
          'ec433d3b':'X_new','07c93362':'q_ids_new','bb177697':'다른 명세','06ceb97e':'#'}
t=teacher.decode('utf-8');t=t[t.index('## 남은 필수 연습과 복귀'):t.index('## 공식 근거와 경계')]
for key,fragment in required.items():
 assert key in t and key in lookup and fragment in lookup[key],(key,fragment)
assert '본문 14–25' not in t and '과제 D 80–82' not in t
print(json.dumps({'status':'passed','candidate_sha256':sha256(raw).hexdigest(),'teacher_sha256':sha256(teacher).hexdigest(),
 'base':a.base_ref,'source_changes':sorted(changed),'cell_order_and_student_answers':'preserved',
 'normal_permuted_noncontiguous_and_duplicate_index':'passed','object_series_shape':[6], 'cell_array_shape':[2,2,2], 'P02_count':1,
 'all_IDs_and_original_leaf_arrays':'same values and independent memory',
 'returned_array_and_frame_copy_isolation':'passed','rejected':errors,
 'teacher_cell_IDs_verified':required,'original_user_files_and_week02':'preserved',
 'limitations':'Representative code checks only; no student work, student timing or learning outcome observed.'},ensure_ascii=False,indent=2))
