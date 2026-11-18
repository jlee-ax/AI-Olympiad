"""Build and verify a source-grounded notebook candidate without overwriting its baseline."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import discovery_loop as discovery
import quality
import workflow

KINDS = {'add', 'deepen', 'replace', 'merge', 'remove', 'reorder', 'move', 'keep'}
CELL_ID = re.compile(r'[A-Za-z0-9_-]{1,64}')


def ids(value, label, required=False):
    result = discovery.strings(value, label, required)
    if any(not CELL_ID.fullmatch(cid) for cid in result):
        raise ValueError(label + ' needs notebook cell IDs')
    return result


def validate_intent(intent, comparison, dimensions):
    actions = intent.get('actions')
    if not isinstance(actions, list) or not actions:
        raise ValueError('An edit needs at least one action')
    kinds = set()
    for action in actions:
        kind = action['kind']
        if kind not in KINDS:
            raise ValueError('Unknown content edit kind')
        kinds.add(kind)
        for field in ('reason', 'alternative', 'postcondition'):
            discovery.text(action.get(field), 'action.' + field)
        before = ids(action.get('before'), 'action.before', kind != 'add')
        after = ids(action.get('after'), 'action.after', kind != 'remove')
        if ((kind == 'add' and before) or (kind == 'remove' and after)
                or (kind in ('keep', 'deepen', 'move', 'reorder') and set(before) != set(after))
                or (kind == 'merge' and len(before) <= len(after))):
            raise ValueError('Cell disposition contradicts action ' + kind)
    if comparison.get('judgment') not in ('covered', 'gap'):
        raise ValueError('A revision requires a settled content comparison')
    findings = {item['id']: item['judgment'] for item in comparison['dimensions']}
    gap = comparison['judgment'] == 'gap' or 'gap' in findings.values()
    if 'uncertain' in findings.values() or gap == (kinds == {'keep'}):
        raise ValueError('Resolve uncertainty and match edit/keep to the actual finding')
    routes = intent.get('routes')
    if not isinstance(routes, dict) or not {d['id'] for d in dimensions} <= routes.keys():
        raise ValueError('Describe the route for every required capability after editing')
    for key, route in routes.items():
        discovery.text(key, 'route id')
        ids(route.get('before'), 'route.before', findings.get(key, 'met') == 'met')
        ids(route.get('after'), 'route.after', True)


def notebook_index(notebook):
    if notebook.get('nbformat') != 4 or not isinstance(notebook.get('cells'), list):
        raise ValueError('Expected a version 4 notebook')
    cells = notebook['cells']
    ids([cell.get('id') for cell in cells], 'notebook cells', True)
    return {cell['id']: cell for cell in cells}


def registered_cells(bundle):
    protected = set()
    for unit in bundle['units']:
        protected.add(unit.get('locator'))
        protected.update(quality.design_locators(unit))
        protected.update(role.get('locator') for role in unit['chain'].values())
        for locations in unit.get('explanation_regions', {}).values():
            protected.update(locations)
    protected.update(claim.get('locator') for claim in bundle['claims'])
    return {loc[5:] for loc in protected if isinstance(loc, str) and loc.startswith('cell:')}


def ordered(route, lookup):
    positions = [lookup.get(key, -1) for key in route]
    return -1 not in positions and positions == sorted(positions)


def check_diff(base, proposed, intent, protected):
    old, new = notebook_index(base), notebook_index(proposed)
    before, after = list(old), list(new)
    old_positions, new_positions = ({k: i for i, k in enumerate(keys)} for keys in (before, after))
    if {k: v for k, v in base.items() if k != 'cells'} != {k: v for k, v in proposed.items() if k != 'cells'}:
        raise ValueError('Notebook metadata outside the edit changed')
    allowed_old, allowed_new, movable = set(), set(), set()
    for action in intent['actions']:
        kind, src, dst = action['kind'], set(action['before']), set(action['after'])
        if not src <= old.keys() or not dst <= new.keys():
            raise ValueError('Missing action endpoint: ' + kind)
        if kind != 'keep':
            allowed_old.update(src)
            allowed_new.update(dst)
        if kind in ('reorder', 'move'):
            movable.update(src)
            common = old.keys() & new.keys()
            if not any((old_positions[a] < old_positions[b]) != (new_positions[a] < new_positions[b])
                       for a in src for b in common):
                raise ValueError('The planned move did not change relative order')
        if (kind == 'add' and dst & old.keys()) or (kind == 'remove' and src & new.keys()):
            raise ValueError('Added or removed cells did not change membership')
        if kind in ('merge', 'replace') and ((src - dst) & new.keys() or (dst - src) & old.keys()):
            raise ValueError('Superseded or replacement cells do not match the declared disposition')
        if kind in ('deepen', 'replace', 'merge') and src == dst and all(old[k]['source'] == new[k]['source'] for k in src):
            raise ValueError('A content revision must change the actual source')
        if kind in ('move', 'reorder') and any(old[k] != new[k] for k in src):
            if not any(other['kind'] in ('deepen', 'replace', 'merge') and
                       {k for k in src if old[k] != new[k]} <= set(other['before']) & set(other['after'])
                       for other in intent['actions']):
                raise ValueError('Moving content does not authorize rewriting it')
        if kind == 'keep' and any(old[k] != new[k] for k in src):
            raise ValueError('Protected foundation changed')
    if not (old.keys() - new.keys()) <= allowed_old or not (new.keys() - old.keys()) <= allowed_new:
        raise ValueError('Unexpected cell added or removed')
    for key in old.keys() & new.keys():
        if old[key] != new[key] and key not in allowed_old & allowed_new:
            raise ValueError('Unrelated cell changed: ' + key)
    stable = (old.keys() & new.keys()) - movable
    if [k for k in before if k in stable] != [k for k in after if k in stable]:
        raise ValueError('Unrelated cell order changed')
    for key, route in intent['routes'].items():
        if not ordered(route['before'], old_positions) or not ordered(route['after'], new_positions):
            raise ValueError('Required path is missing or out of order: ' + key)
    mapped = {cid for route in intent['routes'].values() for cid in route['before']}
    if (protected & (old.keys() - new.keys())) - mapped:
        raise ValueError('Deleted a registered prerequisite, explanation or assessment without a successor route')
    return {'added': [k for k in after if k not in old], 'removed': [k for k in before if k not in new],
            'modified': [k for k in after if k in old and new[k] != old[k]],
            'moved': sorted(movable), 'routes_checked': sorted(intent['routes'])}


def build(base, item, patch, protected):
    discovery.text(patch.get('author'), 'patch.author')
    if patch.get('work_key') != item['key'] or not item.get('intent'):
        raise ValueError('Patch needs a current, scoped revision and its work key')
    result = copy.deepcopy(base)
    cells = result['cells']
    by_id = notebook_index(result)
    operations = patch.get('operations')
    if not isinstance(operations, list) or not operations:
        raise ValueError('Provide actual cell edits')
    for op in operations:
        kind, cid = op['op'], op['id']
        if not isinstance(cid, str) or not CELL_ID.fullmatch(cid):
            raise ValueError('Invalid edit cell ID')
        if kind == 'insert':
            if cid in by_id or op.get('cell_type') not in ('markdown', 'code'):
                raise ValueError('Invalid new cell')
            cell = {'id': cid, 'cell_type': op['cell_type'], 'metadata': {}}
            by_id[cid] = cell
        else:
            cell = by_id[cid]
        if kind in ('insert', 'replace'):
            source = discovery.text(op.get('source'), 'cell source')
            cell['source'] = source.splitlines(keepends=True)
            if cell['cell_type'] == 'code':
                cell.update(outputs=[], execution_count=None)
        if kind in ('remove', 'move'):
            cells.remove(cell)
            if kind == 'remove':
                del by_id[cid]
        if kind in ('insert', 'move'):
            anchor = op['before']
            where = len(cells) if anchor is None else cells.index(by_id[anchor])
            cells.insert(where, cell)
        if kind not in ('insert', 'replace', 'remove', 'move'):
            raise ValueError('Unknown notebook operation')
    return result, check_diff(base, result, item['intent'], protected)


def review_candidate(root, path, item, review, author):
    actual = quality.file_digest(path)
    reviewer = discovery.text(review.get('reviewer'), 'reviewer')
    if reviewer.strip().casefold() == author.strip().casefold() or review.get('candidate_sha256') != actual or review.get('work_key') != item['key']:
        raise ValueError('Review must be independent and bound to this candidate and work key')
    current = notebook_index(quality.load(path))
    intent = item['intent']
    expected = {'route:' + key: route['after'] for key, route in intent['routes'].items()}
    expected.update({'action:' + str(i): a['after'] for i, a in enumerate(intent['actions'])})
    expected.update({'new_input': [], 'boundary': [], 'regression': []})
    checks = review.get('checks', {})
    if not isinstance(checks, dict) or set(checks) != set(expected):
        raise ValueError('Review every edit, capability route, new input, boundary and regression')
    failed = []
    new_inputs = set()
    for key, required in expected.items():
        check = checks[key]
        locators = ids(check.get('cells'), 'reviewed cells', True)
        evidence = check.get('evidence')
        if (not set(required) <= set(locators) <= current.keys() or not quality._evidence(evidence, root)
                or not all(e.get('path') and e.get('sha256') for e in evidence)):
            raise ValueError('Current evidence and actual candidate cells required for ' + key)
        discovery.text(check.get('finding'), 'review finding')
        if key in ('new_input', 'boundary'):
            run = quality.load(quality.safe_file(root, evidence[0]['path']))
            case_id = discovery.text(check.get('case_id'), 'execution case_id')
            cases = [case for case in run.get('cases', []) if case.get('id') == case_id]
            if run.get('candidate_sha256') != actual or len(cases) != 1:
                raise ValueError('Execution receipt does not identify this candidate and case')
            case = cases[0]
            if not {'input', 'actual', 'expected'} <= case.keys() or quality.digest(case['input']) in new_inputs:
                raise ValueError('Use distinct new and boundary inputs with observed and expected results')
            new_inputs.add(quality.digest(case['input']))
            if not quality._same(case['actual'], case['expected']):
                failed.append(key)
        if check.get('status') != 'passed' and key not in failed:
            failed.append(key)
    return {'status': 'rejected' if failed else 'reviewed_candidate', 'failed': failed,
            'candidate_sha256': actual, 'reviewer': reviewer, 'work_key': item['key'],
            'release_ready': False}


def publish_candidate(path, payload):
    # Atomic, no overwrite, including races with another writer.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        temporary = Path(tmp.name)
    try:
        temporary.write_bytes(payload)
        try:
            os.link(temporary, path)
            return 'created'
        except FileExistsError:
            if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
                raise ValueError('Candidate already exists with different content')
            return 'already_created'
    finally:
        temporary.unlink(missing_ok=True)


def run(command, root, state, bundle, patch, output, review=None):
    report = quality.evaluate(bundle, root)
    plan = quality.plan_work(bundle, root, report=report)
    decision = workflow.decide(state, report, repair_plan=plan)
    if decision['reason'] != 'scoped_repair_only':
        raise ValueError('Repair unavailable: ' + decision['reason'])
    item = decision['candidate']
    if item.get('work_kind') != 'revise_lesson':
        raise ValueError('A source-grounded typed edit needs to be selected first')
    baseline = quality.safe_file(root, bundle['artifact']['path'])
    if baseline.suffix != '.ipynb' or Path(output).is_absolute():
        raise ValueError('Expected a notebook baseline and root-relative candidate')
    path = root / output
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or path.resolve() == baseline or path.suffix != '.ipynb':
        raise ValueError('Use a separate candidate notebook inside the selected root')
    original = baseline.read_bytes()
    if hashlib.sha256(original).hexdigest() != report['artifact_sha256'] or report['artifact_sha256'] != bundle['artifact']['sha256']:
        raise ValueError('Baseline changed during planning')
    base = json.loads(original, object_pairs_hook=quality._pairs)
    result, changes = build(base, item, patch, registered_cells(bundle))
    payload = (json.dumps(result, ensure_ascii=False, indent=1, allow_nan=False) + '\n').encode()
    if command == 'apply':
        return {'status': publish_candidate(path, payload), 'work_key': item['key'], 'diff': changes,
                'candidate_sha256': quality.file_digest(path), 'release_ready': False}
    if path.read_bytes() != payload:
        raise ValueError('Candidate differs from the reviewed patch')
    return {**review_candidate(root, path, item, review, patch['author']), 'diff': changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('apply', 'verify'))
    for field in ('workflow', 'quality', 'patch'):
        parser.add_argument(field, type=Path)
    parser.add_argument('candidate')
    parser.add_argument('--root', type=Path, default=quality.ROOT)
    parser.add_argument('--review', type=Path)
    args = parser.parse_args()
    if args.command == 'verify' and not args.review:
        parser.error('verify needs --review')
    try:
        result = run(args.command, args.root.resolve(), quality.load(args.workflow), quality.load(args.quality),
                     quality.load(args.patch), args.candidate, quality.load(args.review) if args.review else None)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, OverflowError) as error:
        result = {'status': 'blocked', 'reason': str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] in ('created', 'already_created', 'reviewed_candidate') else 1


if __name__ == '__main__':
    raise SystemExit(main())
