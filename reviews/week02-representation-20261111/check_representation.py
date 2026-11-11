#!/usr/bin/env python3
"""Finite checks on the actual Week 2 worked functions; no student answer is graded."""
import ast
import contextlib
import hashlib
import io
from pathlib import Path
import nbformat
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[2]
main_path = ROOT / 'lessons/week02/week02_prediction_evaluation.ipynb'
temporal_path = ROOT / 'lessons/week02/week02_temporal_preprocessing.ipynb'
expected = {
    main_path: '6f79589e33574104bd8a471b008259f5b1d4847a19b8b8fc0c32a18418a5249e',
    temporal_path: 'ea847303906a48c98ae69f80cdaaa7a008e1ab31ad197ce69b3c0b7fdf2be326',
}
for path, digest in expected.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
main = nbformat.read(main_path, 4)
temporal = nbformat.read(temporal_path, 4)
nbformat.validate(main)
nbformat.validate(temporal)
namespace = {'np': np, 'pd': pd}
source = ast.parse(temporal.cells[4].source)
functions = [n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in {'make_features', 'last_observed_change'}]
assert {n.name for n in functions} == {'make_features', 'last_observed_change'}
exec(compile(ast.Module(body=functions, type_ignores=[]), '<actual-lesson-functions>', 'exec'), namespace)
make, change = namespace['make_features'], namespace['last_observed_change']

# New histories, deliberately unlike the displayed V/W worked pair.
data = {
    'P': [2, 8, 5], 'Q': [8, 2, 5],
    'R': [2, np.nan, 5], 'S': [np.nan, 2, 5],
    'T': [4, np.nan, np.nan], 'U': [2, 2, np.nan],
    'M': [5, 7, 9], 'N': [7, 5, 9],
}
rows = [(unit, time, value) for unit, values in data.items()
        for time, value in enumerate(values, start=1)]
rows += [('P', 4, 999.), ('Q', 4, -999.), ('P', 5, 12345.)]
raw = pd.DataFrame(rows, columns=['unit', 'time', 'reading'])
targets = pd.DataFrame([(u.lower()+'4', u, 4, 'gold', np.nan) for u in data],
                       columns=['id', 'unit', 'time', 'kind', 'label'])
x = make(raw, targets)
assert np.allclose(x.loc['p4', ['recent','mean3','std3']].astype(float), [5,5,np.sqrt(6)])
assert np.allclose(x.loc['q4', ['recent','mean3','std3']].astype(float), [5,5,np.sqrt(6)])
assert change(raw, 'P', 4) == -3 and change(raw, 'Q', 4) == 3
assert all(pd.isna(x.loc[unit+'4', 'mean3']) and pd.isna(x.loc[unit+'4', 'std3']) for unit in ['r','s','t','u'])
assert change(raw, 'R', 4) == change(raw, 'S', 4) == 3
assert pd.isna(change(raw, 'T', 4)) and change(raw, 'U', 4) == 0
assert np.allclose(x.loc['m4', ['recent','mean3','std3']].astype(float), [9,7,np.sqrt(8/3)])
assert np.allclose(x.loc['n4', ['recent','mean3','std3']].astype(float), [9,7,np.sqrt(8/3)])
assert change(raw, 'M', 4) == 2 and change(raw, 'N', 4) == 4
assert (x.loc['m4','mean3'] >= 6, x.loc['n4','mean3'] >= 6) == (True, True)
assert (change(raw,'M',4) >= 3, change(raw,'N',4) >= 3) == (False, True)
shuffled = raw.sample(frac=1, random_state=731).reset_index(drop=True)
pd.testing.assert_frame_equal(make(shuffled, targets), x)
assert [change(shuffled, u, 4) for u in ['P','Q','R','S']] == [-3,3,3,3]
changed_future = raw.copy()
changed_future.loc[(changed_future.unit == 'P') & (changed_future.time >= 4), 'reading'] = -123456
pd.testing.assert_frame_equal(make(changed_future, targets), x)
assert change(changed_future, 'P', 4) == -3
changed_past = raw.copy()
changed_past.loc[(changed_past.unit == 'P') & (changed_past.time == 3), 'reading'] = 10
assert make(changed_past, targets).loc['p4','recent'] == 10
assert change(changed_past, 'P', 4) == 2
changed_labels = targets.copy()
changed_labels['label'] = -123
pd.testing.assert_frame_equal(make(raw, changed_labels), x)
reordered = targets.iloc[::-1]
assert make(raw, reordered).index.tolist() == reordered.id.tolist()
duplicate = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
for action in (lambda: make(duplicate, targets), lambda: change(duplicate, 'P', 4)):
    try:
        action()
    except ValueError:
        pass
    else:
        raise AssertionError('duplicate time was not rejected')
print('actual lesson feature functions: new collisions, independent exercise, shuffle, missing/zero, time, label, order, duplicate passed')

# The lesson assumes arrival immediately after measurement. This is an explicit
# limitation check: measurement at 2 arriving at 9 is wrongly eligible at t=4
# unless a caller checks actual arrival, which the lesson helper does not accept.
late = pd.DataFrame([('X',1,4.), ('X',2,900.)], columns=['unit','time','reading'])
assert change(late, 'X', 4) == 896
arrival = pd.Series([1.1, 9.0])
assert late.loc[arrival < 4, 'reading'].tolist() == [4.]
print('arrival-time limitation: helper cannot enforce delayed arrival without extra information')

# Verify the real worked main cell and independent count-based F1 boundaries.
ns = {}
for i in [5,7,11]:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(main.cells[i].source, f'<main-{i}>', 'exec'), ns)
assert np.isclose(ns['f1'], 2/5)
cases = [
    ([1,1,-1,-1], [1,-1,1,1], (1,2,1), (1/3,1/2,2/5)),
    ([1,-1], [-1,-1], (0,0,1), (np.nan,0,0)),
    ([-1,-1], [1,-1], (0,1,0), (0,np.nan,0)),
    ([-1,-1], [-1,-1], (0,0,0), (np.nan,np.nan,np.nan)),
]
for truth,pred,(tp,fp,fn),expected_metrics in cases:
    y,p=np.array(truth),np.array(pred)
    counts=(int(((y==1)&(p==1)).sum()),int(((y==-1)&(p==1)).sum()),int(((y==1)&(p==-1)).sum()))
    assert counts == (tp,fp,fn)
    denom=2*tp+fp+fn
    count_f1=2*tp/denom if denom else np.nan
    got=precision_recall_fscore_support(y,p,average='binary',pos_label=1,zero_division=np.nan)[:3]
    assert np.allclose(got, expected_metrics, equal_nan=True)
    assert np.allclose(got[2],count_f1,equal_nan=True)
print('main worked F1 and distinct precision/recall/F1 denominator boundaries passed')

# Actual preprocessing APIs: value collision/indicator and clip policy.
observed=pd.DataFrame({'x':[2.,4.,6.,np.nan]})
test=pd.DataFrame({'x':[4.,np.nan]})
imputer=SimpleImputer(strategy='median',add_indicator=True).fit(observed)
out=imputer.transform(test)
assert np.array_equal(out[:,0],[4,4]) and np.array_equal(out[:,1],[0,1])
train=np.array([[2.],[6.]])
assert np.array_equal(MinMaxScaler().fit(train).transform([[8.],[10.]]).ravel(),[1.5,2.])
assert np.array_equal(MinMaxScaler(clip=True).fit(train).transform([[8.],[10.]]).ravel(),[1.,1.])
print('median-imputation collision, missing indicator, MinMax clip policy passed')
print('No learner answer, learning outcome or duration was observed.')
