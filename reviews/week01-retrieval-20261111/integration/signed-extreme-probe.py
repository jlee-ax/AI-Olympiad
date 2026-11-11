#!/usr/bin/env python3
"""Independently exercise the lesson's actual functions with signed 3D inputs."""
import ast
import hashlib
import json
import math
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
path = ROOT / 'lessons/week01/week01_axes_linear_bridge.ipynb'
raw = path.read_bytes()
book = json.loads(raw)
source = ''.join(book['cells'][16]['source'])
parsed = ast.parse(source)
functions = [n for n in parsed.body if isinstance(n, ast.FunctionDef)
             and n.name in ('normalize_rows', 'cosine_scores')]
assert len(functions) == 2
ns = {'np': np}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), ns)
Q = np.array([[1., 2., -2.], [-2., 1., 2.]])
G = np.array([[3., 0., 4.], [-1., -2., 2.], [0., 1., -1.]])
ids = np.array(['A', 'K', 'Z'])
before = (Q.copy(), G.copy())
actual = ns['cosine_scores'](Q, G)
reference = np.array([[sum(x*y for x, y in zip(q, g)) /
                       (math.sqrt(sum(x*x for x in q)) * math.sqrt(sum(y*y for y in g)))
                       for g in G] for q in Q])
assert np.allclose(actual, reference, rtol=1e-12, atol=1e-12)
assert np.allclose(ns['cosine_scores'](Q, G * np.array([[2.], [3.], [4.]])), actual)
assert np.allclose(ns['cosine_scores'](-Q, G), -actual)
order = np.array([2, 0, 1])
assert np.array_equal(ids[np.argmax(actual, axis=1)],
                      ids[order][np.argmax(ns['cosine_scores'](Q, G[order]), axis=1)])
assert np.array_equal(Q, before[0]) and np.array_equal(G, before[1])
invalid = [[[0., 0., 0.]], [[float('nan'), 0., 1.]], [[float('inf'), 0., 1.]],
           [[1e308, 1e308, 1e308]], [[1e-308, 0., 0.]], [], [1., 2.]]
for row in invalid:
    try:
        ns['normalize_rows'](row)
    except (ValueError, TypeError):
        pass
    else:
        raise AssertionError('Invalid or unrepresentable norm was accepted')
try:
    ns['cosine_scores']([[1., 2.]], [[1., 2., 3.]])
except ValueError:
    pass
else:
    raise AssertionError('Different feature counts were accepted')
print(json.dumps({'candidate_sha256': hashlib.sha256(raw).hexdigest(),
                  'method': 'lesson function definitions; independent scalar-loop oracle',
                  'scores': actual.round(8).tolist(),
                  'selected_ids': ids[np.argmax(actual, axis=1)].tolist(),
                  'checks': ['signed unseen 3D inputs', 'positive and negative scaling',
                             'joint ID permutation', 'inputs unchanged',
                             'zero/NaN/inf/overflow/underflow/empty/shape rejection',
                             'incompatible feature counts rejected'],
                  'status': 'passed'}, ensure_ascii=False, indent=2))
