#!/usr/bin/env python3
"""Reviewer-supplied checks; no student work or automatic student scoring."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--notebook', type=Path,
                    default=root / 'lessons/week01/week01_integrated.ipynb')
parser.add_argument('--expected-sha256')
args = parser.parse_args()
raw = args.notebook.read_bytes()
actual_sha = hashlib.sha256(raw).hexdigest()
if args.expected_sha256 and actual_sha != args.expected_sha256:
    raise AssertionError(f'Notebook sha256 mismatch: {actual_sha}')
nb = json.loads(raw)
ns = {'np': np, 'pd': pd}
cell = next(c for c in nb['cells'] if c.get('id') == '9462ed76')
exec(''.join(cell['source']), ns)
frames = [ns[name] for name in ('exercise_train', 'exercise_validation', 'exercise_input')]
frozen = [(f.drop(columns=['panel']).copy(deep=True), [x.copy() for x in f['panel']])
          for f in frames]
original = frames[0].loc[frames[0]['unit'] == 'T2', 'panel'].iloc[0]
before = original.copy()
count = lambda x: int(((x[:, :, 0] == 1) & (x[:, :, 1] == 2)).sum())
trial = original.copy()
view = trial[:, :, 0]
snapshot = view.copy()
saved = count(trial)
view[0, 0] = 0  # the background in this input
assert (saved, count(trial)) == (1, 1)
view[0, 1] = 0  # turn off T2's active sensor
assert (saved, count(trial)) == (1, 0)
assert np.array_equal(original, before)
assert int(trial[0, 1, 0]) == int(view[0, 1]) == 0
assert int(snapshot[0, 1]) == 1
assert np.shares_memory(trial, view) and not np.shares_memory(trial, snapshot)
assert trial.shape == original.transpose(1, 0, 2).shape
assert before[0, 1].tolist() == [1, 2]
assert original.transpose(1, 0, 2)[0, 1].tolist() == [0, 2]
for frame, (scalar, panels) in zip(frames, frozen):
    pd.testing.assert_frame_equal(frame.drop(columns=['panel']), scalar)
    assert all(np.array_equal(a, b) for a, b in zip(frame['panel'], panels))
print('T2: background 1->1; sensor 1->0; saved 1; inputs unchanged')

backing = np.zeros((4, 4, 2), dtype=int)
backing[::2, ::2, :] = np.array([[[0, 2], [1, 0]], [[1, 2], [0, 0]]])
other = backing[::2, ::2, :]
assert not other.flags.c_contiguous
before_other, before_backing = other.copy(), backing.copy()
trial2 = other.copy()
view2 = trial2[:, :, 0]
snapshot2 = view2.copy()
saved2 = count(trial2)
view2[0, 1] = 0  # change background
assert (saved2, count(trial2)) == (1, 1)
view2[0, 0] = 1  # turn on a previously inactive sensor
assert (saved2, count(trial2)) == (1, 2)
assert int(snapshot2[0, 0]) == 0
assert np.array_equal(other, before_other) and np.array_equal(backing, before_backing)
assert np.shares_memory(trial2, view2) and not np.shares_memory(trial2, snapshot2)
print('independent noncontiguous input: background 1->1; sensor 1->2; saved 1')

def mutant(mode):
    src = before.copy()
    src_before = src.copy()
    result = src if mode == 'original_as_trial' else src.copy()
    channel = result[:, :, 0]
    if mode == 'copied_view':
        channel = channel.copy()
    frozen_view = channel if mode == 'aliased_snapshot' else channel.copy()
    channel[0, 1] = 0
    return (np.array_equal(src, src_before),
            int(result[0, 1, 0]) == int(channel[0, 1]) == 0,
            int(frozen_view[0, 1]) == 1)

assert mutant('correct') == (True, True, True)
assert mutant('original_as_trial') == (False, True, True)
assert mutant('copied_view') == (True, False, True)
assert mutant('aliased_snapshot') == (True, True, False)
print('mutants detected: original-as-trial, copied-view, aliased-snapshot')
print(f'notebook sha256={actual_sha}; reviewer checks only; student work not assessed')
