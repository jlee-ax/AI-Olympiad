#!/usr/bin/env python3
"""Exercise the exact lesson helpers on independent sequences and boundaries."""
import ast
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / 'lessons/week01/week01_axes_linear_bridge.ipynb'
raw = path.read_bytes()
expected_sha = 'f3f739cf8fdd90a68550e3b1b093bedaeb3fc7ce1a310bcf4303b6feb29de544'
assert hashlib.sha256(raw).hexdigest() == expected_sha
book = json.loads(raw)
functions = []
for cell in book['cells']:
    if cell['cell_type'] == 'code':
        module = ast.parse(''.join(cell['source']))
        functions += [x for x in module.body if isinstance(x, ast.FunctionDef)
                      and x.name in ('lookup_and_masked_mean', 'normalize_rows', 'cosine_scores')]
assert len(functions) == 3
ns = {'np': np}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), ns)
E = np.array([[100.,-100.,9.], [1.,0.,-1.], [0.,0.,0.], [2.,2.,2.], [-2.,4.,6.], [7.,8.,9.]])
I = np.array([[2,2,0], [1,4,0], [3,1,3]])
E0, I0 = E.copy(), I.copy()
vectors, valid, sums, counts, means = ns['lookup_and_masked_mean'](E,I)
assert vectors.shape == (3,3,3)
assert counts.ravel().tolist() == [2,2,3]
assert np.array_equal(sums, [[0,0,0],[-1,4,5],[5,4,3]])
assert np.allclose(means, [[0,0,0],[-.5,2,2.5],[5/3,4/3,1]])
Epad = E.copy(); Epad[0] = [-7,19,22]
assert np.allclose(ns['lookup_and_masked_mean'](Epad,I)[-1], means)
extended = np.column_stack([I, np.zeros((3,2),dtype=int)])
assert np.allclose(ns['lookup_and_masked_mean'](E,extended)[-1],means)
assert np.allclose(ns['lookup_and_masked_mean'](E,I[:,::-1])[-1],means)
assert np.array_equal(E,E0) and np.array_equal(I,I0)
invalid = [[[-1,1]], [[6,1]], [[True,1]], [[1.0,2.0]], [[0,0]], [], [1,2]]
for ids in invalid:
    try:
        ns['lookup_and_masked_mean'](E,ids)
    except (ValueError,TypeError):
        pass
    else:
        raise AssertionError('Invalid ID, dimension or all-PAD row was accepted')
try:
    ns['cosine_scores'](means[:1],[[1,0,0]])
except ValueError:
    pass
else:
    raise AssertionError('Valid zero mean must not be treated as a valid cosine direction')
example = np.array([[7.,11.],[2,0],[2,9],[6,4],[0,0]])
tokens = np.array([[1,1,2,0],[3,4,0,0]])
gallery = np.array([[2.,1.],[0.,3.],[1.,1.],[2.,0.]])
q = ns['lookup_and_masked_mean'](example,tokens)[-1]
zero_pad = example.copy();zero_pad[0] = [0,0]
wrong = zero_pad[tokens].mean(axis=1)
assert not np.allclose(q,wrong)
assert np.allclose(ns['cosine_scores'](q,gallery),ns['cosine_scores'](wrong,gallery))
print(json.dumps({'candidate_sha256':expected_sha,'status':'passed',
                  'independent_means':means.tolist(),'counts':counts.ravel().tolist(),
                  'checks':['nonzero PAD and real zero vectors','repeat ID counts',
                            'change/extend PAD invariance','fixed lookup order loss',
                            'input arrays unchanged','negative/out-of-range/bool/float/all-PAD/dimensions rejected',
                            'valid zero mean distinguished from invalid cosine direction',
                            'wrong denominator can preserve all cosine scores'],
                  'limits':'Synthetic finite cases; does not show student mastery or actual model training.'},
                 ensure_ascii=False,indent=2))
