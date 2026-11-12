#!/usr/bin/env python3
"""Compare the candidate notebook against a supplied baseline commit."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
relative = 'lessons/week01/week01_integrated.ipynb'
parser = argparse.ArgumentParser()
parser.add_argument('--base-ref', default='110bab1')
parser.add_argument('--notebook', type=Path, default=root / relative)
parser.add_argument('--expected-sha256')
parser.add_argument('--expected-teacher-sha256')
args = parser.parse_args()
raw = args.notebook.read_bytes()
actual = hashlib.sha256(raw).hexdigest()
if args.expected_sha256 and actual != args.expected_sha256:
    raise AssertionError('notebook sha256 mismatch: ' + actual)
old = json.loads(subprocess.check_output(['git', '-C', str(root), 'show',
                                          args.base_ref + ':' + relative]))
new = json.loads(raw)
assert {k: v for k, v in old.items() if k != 'cells'} == {
    k: v for k, v in new.items() if k != 'cells'}
assert len(old['cells']) == len(new['cells']) == 46
assert [c['id'] for c in old['cells']] == [c['id'] for c in new['cells']]
changed = set()
for before, after in zip(old['cells'], new['cells']):
    if before != after:
        changed.add(after['id'])
        assert {k: v for k, v in before.items() if k != 'source'} == {
            k: v for k, v in after.items() if k != 'source'}
assert changed == {'deep-count-intro', '303c6117', '97f45dbb'}
by_id = {c['id']: c for c in new['cells']}
answer = by_id['e49ac1c2']
assert not ast.parse(''.join(answer['source'])).body
assert answer['outputs'] == []
for cell_id in ('9462ed76', 'rectangle-independent-text',
                'rectangle-independent-input', 'rectangle-independent-answer'):
    assert next(c for c in old['cells'] if c['id'] == cell_id) == by_id[cell_id]
teacher = root / 'lessons/week01/week01_integrated_teacher.md'
teacher_hash = hashlib.sha256(teacher.read_bytes()).hexdigest()
if args.expected_teacher_sha256 and teacher_hash != args.expected_teacher_sha256:
    raise AssertionError('teacher sha256 mismatch: ' + teacher_hash)
week02_diff = subprocess.check_output(['git', '-C', str(root), 'diff', '--name-only',
                                       args.base_ref, '--', 'lessons/week02/'], text=True)
week02_status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain',
                                         '--', 'lessons/week02/'], text=True)
assert not week02_diff.strip() and not week02_status.strip()
print('notebook sha256=' + actual)
print('teacher sha256=' + teacher_hash)
print('changed source:', ', '.join(sorted(changed)))
print('other cells/output/metadata, blank answer, rectangle, and week02: unchanged')
print('HTML synchronization, student work, actual time, and visual browser display: not assessed')
