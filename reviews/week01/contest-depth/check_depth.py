"""Independent calculations for the week-1 depth revision; no student answers are filled."""
from contextlib import redirect_stdout
from fractions import Fraction
from io import StringIO
from pathlib import Path
import ast
import json
import math
import random
import re
import statistics
import textwrap

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / 'lessons/week01'
notebook = json.loads((LESSON / 'week01_python_tables.ipynb').read_text(encoding='utf-8'))
by_id = {cell.get('id'): ''.join(cell.get('source', [])) for cell in notebook['cells']}
teacher = (LESSON / 'teacher-notes.txt').read_text(encoding='utf-8')

# Execute the actual question-1 snippet, rather than trusting its printed key.
quiz = by_id['71068cea']
snippet = re.search(r'~~~python\n(.*?)\n~~~', quiz, re.S).group(1)
out = StringIO()
with redirect_stdout(out):
    exec(compile(snippet, '<quiz>', 'exec'), {})
assert out.getvalue().strip() == '13'
array = np.arange(6).reshape(2, 3)
assert array.mean(axis=0, keepdims=False).shape == (3,)
assert len(array[:, 0]) == 2
assert Fraction(0 + 12, 2) == 6
assert Fraction(0 + 12 + 0, 3) != Fraction(0 + 12 + 9, 3)
assert '선택형 1' in quiz and '선택형 2' in quiz and '**서술형.**' in quiz

# Recompute the actual reshape counterexample and protect preceding lesson names.
prior_a = np.array([[2, 4], [6, 8], [10, 12]])
prior_b = np.array([[1, 5, 9], [3, 7, 11]])
state = {'np': np, 'A': prior_a.copy(), 'B': prior_b.copy()}
block = re.search(r'~~~python\n(.*?)\n~~~', by_id['depth-reshape-compare'], re.S).group(1)
exec(compile(block, '<reshape comparison>', 'exec'), state)
assert state['A'][1, 0] == 6 and state['B'][1, 2] == 11
assert state['reshaped_task'].shape == state['transposed_task'].shape == (3, 2)
assert state['reshaped_task'].tolist() == [[2, 5], [8, 11], [14, 17]]
assert state['transposed_task'].tolist() == [[2, 11], [5, 14], [8, 17]]
assert state['reshaped_task'][0, 1] != state['transposed_task'][0, 1]

# Run the teacher's actual solution against independent cases and an oracle.
lines = teacher.splitlines()
start = next(i for i, line in enumerate(lines) if line.startswith('  def recorded_mean(values):'))
body = [lines[start]]
for line in lines[start + 1:]:
    if line.strip() and not line.startswith('    '):
        break
    body.append(line)
source = textwrap.dedent('\n'.join(body)).strip()
module = ast.parse(source)
assert len(module.body) == 1 and isinstance(module.body[0], ast.FunctionDef)
namespace = {}
exec(compile(module, '<teacher key>', 'exec'), namespace)
recorded_mean = namespace['recorded_mean']
examples = [([], (0, None)), ([None], (0, None)), ([None, None], (0, None)),
            ([None, 0], (1, 0.0)), ([0, None, 6, 12], (3, 6.0)),
            ([2, None, 8, 10], (3, Fraction(20, 3))), ([3, None, 9], (2, 6.0)),
            ([1000000] * 10000, (10000, 1000000.0)), ([None] * 10000, (0, None))]
rng = random.Random(20261110)
for _ in range(150):
    values = [None if rng.randrange(4) == 0 else rng.randrange(0, 1000001) for _ in range(rng.randrange(0, 40))]
    valid = [v for v in values if v is not None]
    examples.append((values, (len(valid), statistics.fmean(valid) if valid else None)))
for values, expected in examples:
    before = values.copy()
    actual = recorded_mean(values)
    assert values == before and isinstance(actual, tuple) and len(actual) == 2
    assert actual[0] == expected[0]
    if expected[1] is None:
        assert actual[1] is None
    else:
        assert math.isclose(actual[1], float(expected[1]), rel_tol=1e-9, abs_tol=1e-12)

# Independently check translations and scalings of population variance.
def population_variance(values):
    mean = sum(map(Fraction, values)) / len(values)
    return sum((Fraction(v) - mean) ** 2 for v in values) / len(values)
base = [0, 4, 8]
assert population_variance(base) == Fraction(32, 3)
assert population_variance([x + 3 for x in base]) == Fraction(32, 3)
assert population_variance([x * 2 for x in base]) == Fraction(128, 3)
assert population_variance([20, 40, 60]) == Fraction(800, 3)
assert population_variance([2, 4, 6]) * 100 == Fraction(800, 3)

# Verify that the published student notebook and generated HTML do not contain
# the teacher's solution or its separate check inputs; this is not access control.
student_text = '\n'.join(by_id.values())
html = (LESSON / 'week01_python_tables.html').read_text(encoding='utf-8')
for text in (student_text, html):
    assert 'def recorded_mean(values):' not in text
    assert '[2,None,8,10]' not in text.replace(' ', '')
    assert 'task_array' in text and '1,000,000' in text
for cell in notebook['cells']:
    if 'student-code' in cell.get('metadata', {}).get('tags', []):
        assert all(not line.strip() or line.lstrip().startswith('#') for line in cell.get('source', []))

print(json.dumps({'status': 'passed', 'quiz': 'actual snippet and axis/denominator checked',
                  'reshape': 'values, shape, axis mapping and prior state checked',
                  'teacher_key': 'boundary cases and 150 seeded independent cases checked',
                  'variance': 'translation, scaling and units checked with fractions',
                  'student_artifact': 'teacher key absent from notebook and HTML text',
                  'learner_performance': 'not_observed'}, ensure_ascii=False, indent=2))
