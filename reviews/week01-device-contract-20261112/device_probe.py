"""Independent comparison of actual e3d3afde and current lesson cells.

The reviewer's model and error checks are external to student notebooks.
They do not establish student achievement or a complete general validator.
"""
from pathlib import Path
from itertools import combinations
from hashlib import sha256
from contextlib import redirect_stdout
from io import StringIO
import argparse
import json
import subprocess
import sys

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestCentroid
from sklearn.tree import DecisionTreeClassifier

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, default=Path.cwd(), help='Repository checkout root')
parser.add_argument('--candidate-sha', required=True, help='Expected SHA-256 of the frozen integrated notebook')
parser.add_argument('--teacher-sha', required=True, help='Expected SHA-256 of the teacher notes')
parser.add_argument('--labels-sha', required=True, help='Expected SHA-256 of the separate truth CSV')
args = parser.parse_args()
ROOT = args.root.resolve()
NOTEBOOK = ROOT / 'lessons/week01/week01_integrated.ipynb'
baseline = json.loads(subprocess.check_output(['git', 'show', 'e3d3afde:lessons/week01/week01_integrated.ipynb'], cwd=ROOT))
current_bytes = NOTEBOOK.read_bytes()
current_hash = sha256(current_bytes).hexdigest()
if current_hash != args.candidate_sha:
    raise SystemExit('Supply the exact frozen notebook SHA-256')
candidate = json.loads(current_bytes)

def source(cell):
    s = cell['source']
    return s if isinstance(s, str) else ''.join(s)

def getcell(nb, cell_id):
    return next(c for c in nb['cells'] if c.get('id') == cell_id)

def data(nb):
    ns = {'np': np, 'pd': pd}
    with redirect_stdout(StringIO()):
        exec(source(getcell(nb, '9462ed76')), ns)
    return ns

def cell_array(frame, unit):
    return frame.loc[frame['unit'].eq(unit), 'panel'].iloc[0]

old, new = data(baseline), data(candidate)
tables = ('exercise_train', 'exercise_validation', 'exercise_input')
snapshot = lambda frames: {row.unit: np.array(row.panel, copy=True) for f in frames for row in f.itertuples()}
old_frames = [old[k] for k in tables]
new_frames = [new[k] for k in tables]
old_panels, new_panels = snapshot(old_frames), snapshot(new_frames)
assert old_panels.keys() == new_panels.keys()
for key in old_panels:
    np.testing.assert_array_equal(old_panels[key], new_panels[key])
for x,y in zip(old_frames,new_frames):
    cols=[c for c in x.columns if c not in ('panel', 'label')]
    pd.testing.assert_frame_equal(x[cols],y[cols])
pd.testing.assert_series_equal(old_frames[0]['label'],new_frames[0]['label'])

old_t2,old_n7 = cell_array(old_frames[0],'T2'),cell_array(old_frames[2],'N7')
assert np.shares_memory(old_t2,old_n7) and int(old_n7[0,1,0]) == 1
old_t2[0,1,0] = 0
assert int(old_n7[0,1,0]) == 0

rows = [(row.unit,row.panel) for f in new_frames for row in f.itertuples()]
assert len(rows) == 11
pairs = list(combinations(rows,2))
assert len(pairs) == 55
assert all(not np.shares_memory(a[1],b[1]) for a,b in pairs)
assert all(not np.shares_memory(a,p) for _,a in rows for p in new['panel_examples'].values())
for target_uid in [uid for uid,_ in rows]:
    ns = data(candidate)
    frames = [ns[k] for k in tables]
    before = snapshot(frames)
    frame = next(f for f in frames if target_uid in f.unit.values)
    arr = cell_array(frame,target_uid)
    arr[0,0,0] = 1 - arr[0,0,0]
    after = snapshot(frames)
    assert not np.array_equal(before[target_uid],after[target_uid])
    assert all(np.array_equal(before[k],after[k]) for k in before if k != target_uid)

train = new_frames[0]
trial = train.copy(deep=True)
assert np.shares_memory(cell_array(train,'T2'),cell_array(trial,'T2'))
trial['panel'] = [p.copy() for p in trial['panel']]
assert not np.shares_memory(cell_array(train,'T2'),cell_array(trial,'T2'))
original_t2 = cell_array(train,'T2').copy()
cell_array(trial,'T2')[0,1,0] = 0
np.testing.assert_array_equal(cell_array(train,'T2'),original_t2)

assert 'label' not in new_frames[1].columns
truth_before = old_frames[1].set_index('unit')['label'].to_dict()
files = sorted((ROOT/'lessons/week01').glob('*validation*labels*.csv'))
assert len(files) == 1, files
labels = pd.read_csv(files[0])
assert sha256(files[0].read_bytes()).hexdigest() == args.labels_sha
assert not labels.unit.duplicated().any()
assert labels.set_index('unit')['label'].to_dict() == truth_before == {'V9':'정상','V4':'점검','V7':'점검'}

# The following features and models are *reviewer* examples, not filled student work.
known = train[train.label.isin(['정상','점검'])]
mean = known.signal.mean()
assert mean == 4 and known.unit.tolist() == ['T1','T2','T3','T4']
def feature(frame):
    return np.column_stack((frame.signal.fillna(mean).to_numpy(),[
        int(((p[:,:,0] == 1) & (p[:,:,1] == 2)).sum()) for p in frame.panel
    ]))
X,y = feature(known),known.label.to_numpy()
np.testing.assert_array_equal(X,[[0,3],[3,1],[4,2],[9,0]])
validation_order = new_frames[1].unit.tolist()
truth = labels.set_index('unit').loc[validation_order,'label'].to_numpy()
out = {}
for name, model in [('nearest_centroid',NearestCentroid()),('tree',DecisionTreeClassifier(max_depth=2,random_state=0))]:
    model.fit(X,y)
    vp = model.predict(feature(new_frames[1]))
    pred = dict(zip(new_frames[2].unit,model.predict(feature(new_frames[2]))))
    assert set(pred) == {'N7','N3','N1'}
    out[name] = {'validation':dict(zip(validation_order,vp.tolist())), 'accuracy':float(np.mean(vp==truth)), 'submission':[[u,pred[u]] for u in new['exercise_order']]}
assert list(out['nearest_centroid']['validation'].values()) == ['정상','점검','정상']
assert list(out['tree']['validation'].values()) == ['정상','점검','점검']
assert [r[0] for r in out['tree']['submission']] == ['N7','N3','N1']
shuffle = labels.iloc[::-1].set_index('unit').loc[validation_order,'label'].to_numpy()
assert np.array_equal(shuffle,truth)

# A reviewer-only implementation checks the *stated* ID contract. It is not
# included as a solution or as an automatic grader in the student lesson.
def reviewer_align(prediction, answer, expected):
    expected_set=set(expected)
    for frame, col in [(prediction,'prediction'),(answer,'label')]:
        if set(frame.columns) != {'unit',col} or frame.unit.duplicated().any():
            raise ValueError('invalid columns or duplicate ID')
        if set(frame.unit) != expected_set or len(frame) != len(expected):
            raise ValueError('missing or unexpected ID')
        if not set(frame[col]).issubset({'정상','점검'}):
            raise ValueError('invalid label')
    merged=prediction.merge(answer,on='unit',validate='one_to_one')
    return merged.set_index('unit').loc[expected]

def reviewer_submission(frame, expected):
    if list(frame.columns) != ['sample_id','prediction']:
        raise ValueError('invalid submission columns')
    if frame.sample_id.tolist() != expected:
        raise ValueError('invalid submission ID order')
    if not set(frame.prediction).issubset({'정상','점검'}):
        raise ValueError('invalid submission label')
    return True

pred=pd.DataFrame({'unit':validation_order,'prediction':['정상','점검','정상']})
assert reviewer_align(pred,labels,validation_order).index.tolist()==validation_order
assert reviewer_align(pred.iloc[::-1],labels.iloc[::-1],validation_order).index.tolist()==validation_order
bad_cases=[
    ('missing answer ID',pred,labels.iloc[:-1]),
    ('duplicate answer ID',pred,pd.concat([labels,labels.iloc[[0]]],ignore_index=True)),
    ('unexpected answer ID',pred,pd.concat([labels,pd.DataFrame([{'unit':'V0','label':'정상'}])],ignore_index=True)),
    ('invalid answer label',pred,labels.assign(label=['정상','점검','?'])),
    ('missing prediction ID',pred.iloc[:-1],labels),
    ('duplicate prediction ID',pd.concat([pred,pred.iloc[[0]]],ignore_index=True),labels),
    ('unexpected prediction ID',pd.concat([pred,pd.DataFrame([{'unit':'V0','prediction':'정상'}])],ignore_index=True),labels),
    ('invalid prediction label',pred.assign(prediction=['정상','점검','?']),labels),
]
rejected=[]
for name, p, a in bad_cases:
    try: reviewer_align(p,a,validation_order)
    except ValueError: rejected.append(name)
    else: raise AssertionError('reviewer failed to reject '+name)
submission=pd.DataFrame(out['tree']['submission'],columns=['sample_id','prediction'])
assert reviewer_submission(submission,new['exercise_order'])
for name, item in [
    ('wrong submission order',submission.iloc[::-1]),
    ('duplicate submission ID',submission.assign(sample_id=['N7','N7','N1'])),
    ('missing submission ID',submission.iloc[:-1]),
    ('invalid submission label',submission.assign(prediction=['점검','?','정상'])),
]:
    try: reviewer_submission(item,new['exercise_order'])
    except ValueError: rejected.append(name)
    else: raise AssertionError('reviewer failed to reject '+name)
assert len(rejected)==12

# Execute the real worked leaf-count function on new, valid shapes and inputs.
scope={'np':np,'pd':pd}
with redirect_stdout(StringIO()):
    exec(source(getcell(candidate,'484f22ba')),scope)
    exec(source(getcell(candidate,'deep-leaf-grid')),scope)
    exec(source(getcell(candidate,'deep-count-code')),scope)
count=scope['count_yellow_leaf']
image=np.array([[[1,1],[1,0],[0,1]],[[1,1],[0,0],[1,1]]])
saved=image.copy()
assert count(image)==3
background=image.copy(); mask=background[:,:,0]==0; background[:,:,1][mask] = 1-background[:,:,1][mask]
assert count(background)==3 and count(image.transpose(1,0,2))==3
assert count(np.zeros((2,3,2),dtype=int))==0
np.testing.assert_array_equal(image,saved)

ids = [c['id'] for c in candidate['cells']]
pos = [ids.index(c['id']) for c in baseline['cells']]
assert pos == sorted(pos), 'baseline cells missing or reordered'
old_cells = {c['id']: c for c in baseline['cells']}
new_cells = {c['id']: c for c in candidate['cells']}
allowed_changes = {'7591b8af', '303c6117', '9462ed76', '97f45dbb'}
assert set(new_cells) - set(old_cells) == {'exercise-validation-release','exercise-validation-answer'}
for cell_id, old_cell in old_cells.items():
    new_cell = new_cells[cell_id]
    assert old_cell['cell_type'] == new_cell['cell_type']
    if cell_id not in allowed_changes:
        assert source(old_cell) == source(new_cell), cell_id
        assert old_cell.get('attachments') == new_cell.get('attachments'), cell_id
teacher_path = ROOT/'lessons/week01/week01_integrated_teacher.md'
assert sha256(teacher_path.read_bytes()).hexdigest() == args.teacher_sha
teacher_text = teacher_path.read_text(encoding='utf-8')
assert '96셀' in teacher_text and '접근 통제가 아닙니다' in teacher_text
for rel in ['week01_python_tables.ipynb','teacher-notes.txt','week01_axes_linear_bridge.ipynb','week01_axes_linear_bridge_teacher.md']:
    path='lessons/week01/'+rel
    expected=subprocess.check_output(['git','show','e3d3afde:'+path],cwd=ROOT)
    assert (ROOT/path).read_bytes()==expected,path
unchanged_scope = subprocess.check_output(['git','status','--porcelain','--untracked-files=all','--','lessons/week02','curriculum'],cwd=ROOT,text=True)
assert not unchanged_scope, unchanged_scope

student_ids=['e49ac1c2','exercise-validation-answer','rectangle-independent-answer']
for cell_id in student_ids:
    c=getcell(candidate,cell_id)
    assert all(not x.strip() or x.lstrip().startswith('#') for x in source(c).splitlines())
    assert not c.get('outputs')
result={'baseline':'e3d3afdee8d2ad60141ca7a91b5b5bf3e7d3ec6d','candidate_sha256':current_hash,'teacher_sha256':args.teacher_sha,'labels_sha256':args.labels_sha,'old_alias_T2_N7_reproduced':True,'unchanged_panel_values_and_ids':True,'candidate_rows':11,'memory_pairs':55,'changed_each_row_others_unchanged':True,'deep_copy_limit_and_per_array_copy':True,'validation_truth_by_id':truth_before,'reviewer_models':out,'reviewer_contract_normal_and_shuffled':'passed','reviewer_contract_rejected':rejected,'new_leaf_inputs':'passed: count 3, background, transpose, all background, source unchanged','baseline_cell_id_order':'preserved; unrelated cell source and attachments unchanged','unmodified_course_files':'byte equal e3d3afde','student_answers':'blank and ungraded','caveat':'Reviewer references are not student work or an automated grader.'}
print(json.dumps(result,ensure_ascii=False,indent=2))
