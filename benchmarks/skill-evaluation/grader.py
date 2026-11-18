"""Harbor verifier for observable fields in the KOAI public pilot cases."""
import hashlib
import json
import math
import os
import stat
from pathlib import Path


def exact(actual, expected):
    # JSON numbers compare by value. Booleans and strings remain distinct.
    if type(actual) in (int, float) and type(expected) in (int, float):
        return actual == expected
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(exact(a, e) for a, e in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in expected)
    return actual == expected


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON field')
        obj[key] = value
    return obj


def finite_number(text):
    value = float(text)
    if not math.isfinite(value):
        raise ValueError('Non-finite JSON number')
    return value


def strict_json(text):
    return json.loads(text, object_pairs_hook=unique_object, parse_float=finite_number, parse_constant=finite_number)


def read_answer(file, limit=65536):
    if file.parent.is_symlink() or file.is_symlink():
        return None
    try:
        if not stat.S_ISREG(file.stat().st_mode):
            return None
        with file.open('rb') as source:
            payload = source.read(limit + 1)
        return strict_json(payload) if len(payload) <= limit else None
    except (OSError, ValueError, UnicodeError, RecursionError):
        return None


def cell_signature(cell):
    source = cell['source']
    if not isinstance(source, str):
        if not isinstance(source, list) or any(not isinstance(row, str) for row in source):
            raise ValueError('Invalid cell source')
        source = ''.join(source)
    payload = {**cell, 'source': source}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                     allow_nan=False).encode()).hexdigest()


def grade_notebook(key, path):
    result = dict.fromkeys(('required_content_preserved', 'unrequested_content_absent', 'prerequisite_order'), 0)
    notebook = read_answer(path, 4 * 1024 * 1024)
    try:
        if not isinstance(notebook, dict) or notebook.get('nbformat') != 4:
            raise ValueError('Missing version 4 notebook')
        cells = notebook['cells']
        if not isinstance(cells, list) or not cells:
            raise ValueError('Missing cells')
        actual = {cell['id']: cell_signature(cell) for cell in cells}
        if len(actual) != len(cells):
            raise ValueError('Ambiguous cell IDs')
        positions = {cid: n for n, cid in enumerate(actual)}
        required = key['cells']
        result['required_content_preserved'] = int(all(actual.get(k) == h for k, h in required.items()))
        result['unrequested_content_absent'] = int(actual.keys() <= required.keys())
        result['prerequisite_order'] = int(all(a in positions and b in positions and positions[a] < positions[b]
                                                for a, b in key['precedence']))
    except (ValueError, KeyError, TypeError, AttributeError, RecursionError, UnicodeError):
        pass
    passed = int(all(result.values()))
    return {'overall': float(passed), 'custom_metrics': {'koai_material_repair': passed, **result}}


def grade(entry, output):
    if 'koai_notebook' in entry:
        return grade_notebook(entry['koai_notebook'], output.with_name('lesson.ipynb'))
    expected = entry.get('koai_facts')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('The verifier needs a nonempty koai_facts answer key.')
    answer = read_answer(output)
    match = isinstance(answer, dict) and all(k in answer and exact(answer[k], v) for k, v in expected.items())
    return {'overall': float(match), 'custom_metrics': {'koai_case_facts_correct': float(match)}}


def main():
    tests = Path(os.environ.get('HARBOR_TESTS_DIR', '/tests'))
    workspace = Path(os.environ.get('HARBOR_WORKSPACE_DIR', '/workspace'))
    verifier = Path(os.environ.get('HARBOR_VERIFIER_DIR', '/logs/verifier'))
    reward = grade(strict_json((tests / 'entry.json').read_text(encoding='utf-8')), workspace / 'output/answer.json')
    reward_json = Path(os.environ.get('HARBOR_REWARD_JSON', verifier / 'reward.json'))
    reward_txt = Path(os.environ.get('HARBOR_REWARD_TXT', verifier / 'reward.txt'))
    for path, value in [(reward_json, json.dumps(reward)), (reward_txt, str(reward['overall']))]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
