#!/usr/bin/env python3
"""Inspect concrete KOAI criteria and select bounded work; never execute workers."""
import argparse
import copy
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'skills/references/criteria.json'
CONTRACT = 'curriculum/contract.json'
UNIT_SPECIFICATIONS = 'skills/koai-evaluate/references/unit-specifications.json'
THEORY_SPECIFICATION = 'skills/koai-evaluate/references/theory-explanation.json'
ORACLE_KINDS = {'axis_mean', 'binary_metrics', 'weighted_sum', 'split_fit'}
REVIEW_CRITERIA = {'K02', 'K05', 'K06', 'K09', 'K15', 'K16'}
STATES = {'passed', 'failed', 'uncertain', 'not_run'}
TIERS = {'critical': 0, 'major': 1, 'moderate': 2, 'minor': 3}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('File references must be nonempty relative paths')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('File reference is outside the root or not a regular file: ' + ascii(name))
    return path


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + ascii(key))
        result[key] = value
    return result


def clean_json(value):
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            item.encode('utf-8')
        elif type(item) is float and not math.isfinite(item):
            raise ValueError('Non-finite JSON number')
        elif isinstance(item, dict):
            stack.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)


def load(path):
    value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
    clean_json(value)
    return value


class PlanParser(HTMLParser):
    """Extract table row regions, retaining cells, attributes and link targets."""
    def __init__(self):
        super().__init__()
        self.rows = {}
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'tr':
            self.row = {'attrs': attrs, 'cells': [], 'links': [], 'markup': []}
        if self.row is not None:
            self.row['markup'].append(self.get_starttag_text())
        if tag in ('th', 'td') and self.row is not None:
            self.cell = []
        if tag == 'a' and self.row is not None:
            self.row['links'].append(attrs.get('href', ''))

    def handle_data(self, text):
        if self.row is not None:
            self.row['markup'].append(text)
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if self.row is not None:
            self.row['markup'].append('</' + tag + '>')
        if tag in ('th', 'td') and self.cell is not None and self.row is not None:
            self.row['cells'].append(' '.join(''.join(self.cell).split()))
            self.cell = None
        if tag == 'tr' and self.row is not None:
            identifier = self.row['attrs'].get('id')
            if identifier:
                if identifier in self.rows:
                    raise ValueError('Duplicate HTML row ID: ' + identifier)
                self.rows[identifier] = self.row
            self.row = None


def regions(path):
    if path.suffix.lower() == '.html':
        parser = PlanParser()
        parser.feed(path.read_text(encoding='utf-8'))
        return {'#' + key: digest(value) for key, value in parser.rows.items()}
    if path.suffix.lower() == '.ipynb':
        data = load(path)
        cells = data.get('cells', [])
        result = {}
        for cell in cells:
            cid = cell.get('id')
            if not cid:
                continue
            if 'cell:' + cid in result:
                raise ValueError('Duplicate notebook cell ID')
            outputs = cell.get('outputs', [])
            if not isinstance(outputs, list) or any(not isinstance(x, dict) for x in outputs):
                raise ValueError('Notebook outputs must be object arrays')
            displayed = [{key: value for key, value in output.items() if key != 'execution_count'} for output in outputs]
            result['cell:' + cid] = digest({'cell_type': cell['cell_type'], 'source': cell['source'],
                                         'attachments': cell.get('attachments', {}), 'outputs': displayed})
        return result
    return {'file': file_digest(path)}


def baseline(root=ROOT):
    contract = load(safe_file(root, CONTRACT))
    path = safe_file(root, contract['baseline']['path'])
    parser = PlanParser()
    parser.feed(path.read_text(encoding='utf-8'))
    errors = []
    if file_digest(path) != contract['baseline']['sha256']:
        errors.append('Student HTML does not match the pinned baseline')
    if contract['competition_year'] != 2027 or contract['division'] != 'middle_school':
        errors.append('Competition target differs from the recorded governing baseline')
    if contract['class_minutes'] != 120 or len(contract['weeks']) != 10:
        errors.append('Expected ten 120-minute class meetings')
    expected_week_ids = {'week-' + str(n) for n in range(1, 11)}
    actual_week_ids = {key for key in parser.rows if key.startswith('week-')}
    if actual_week_ids != expected_week_ids:
        errors.append('Missing or unexpected week row IDs')
    actual_scope_ids = {key for key in parser.rows if key.startswith('scope-')}
    expected_scope_ids = {'scope-' + f'{n:02}' for n in range(1, 61)}
    if actual_scope_ids != expected_scope_ids:
        errors.append('Expected exactly the 60 numbered scope rows')
    if {t['id'] for t in contract['topics']} != {'KOAI-' + f'{n:02}' for n in range(1, 61)} or len(contract['topics']) != 60:
        errors.append('Curriculum contract must retain all 60 unique topic IDs')
    weeks = []
    for item in contract['weeks']:
        row = parser.rows.get('week-' + str(item['week']))
        if row is None:
            continue
        attrs = row['attrs']
        values = [int(attrs['data-' + key + '-minutes']) for key in ('theory', 'noncoding', 'coding')]
        expected = [item[key + '_minutes'] for key in ('theory', 'noncoding', 'coding')]
        # Compare visible top-level activity times, not only decorative data attributes.
        text = row['cells'][1]
        visible = []
        for label in ('\uc774\ub860', '\ube44\ucf54\ub529', '\ucf54\ub529'):
            match = re.search(r'(?<![\uac00-\ud7a3])' + label + r'\s+(\d+)\ubd84', text)
            visible.append(int(match.group(1)) if match else None)
        if values != expected or sum(values) != 120 or visible != values:
            errors.append('Class allocation mismatch at week ' + str(item['week']))
        if item['written_minutes_within_noncoding'] != 10 or values[1] < 10:
            errors.append('Written practice must remain inside noncoding time')
        outside = [int(attrs['data-self-' + key + '-hours']) for key in ('min', 'max')]
        if outside != item['required_self_study_hours'] or outside[0] > outside[1]:
            errors.append('Outside-work allocation mismatch at week ' + str(item['week']))
        weeks.append({'week': item['week'], 'class_minutes': sum(values), 'required_self_study_hours': outside})
    for topic in contract['topics']:
        row = parser.rows.get(topic['plan_locator'].lstrip('#'))
        if row is None or len(row['cells']) < 5:
            errors.append('Missing scope region for ' + topic['id'])
            continue
        flags = [bool(re.search('\uc774\ub860 O', row['cells'][2])), bool(re.search('\uc2e4\uc804 O', row['cells'][3]))]
        if flags != [topic['theory'], topic['practical']]:
            errors.append('Theory/practical flag mismatch: ' + topic['id'])
        scheduled = sorted({int(link.rsplit('-', 1)[1]) for link in row['links'] if link.startswith('#week-')})
        if scheduled != topic['scheduled_weeks'] or not scheduled:
            errors.append('Placement mismatch: ' + topic['id'])
    return {'authority': 'advisory_only', 'status': 'failed' if errors else 'passed',
            'errors': errors, 'baseline_sha256': file_digest(path), 'weeks': weeks,
            'topic_count': len(contract['topics']), 'coverage': 'scheduled_only'}


def closure(bundle, identifier):
    nodes = {node['id']: node for node in bundle['dependencies']}
    seen, queue = set(), [identifier]
    while queue:
        current = queue.pop()
        if current in seen:
            continue
        if current not in nodes:
            raise ValueError('Missing dependency node: ' + ascii(current))
        seen.add(current)
        queue.extend(nodes[current]['depends_on'])
    return [nodes[key] for key in sorted(seen)]


def impact(bundle, changed):
    nodes = {node['id']: node for node in bundle['dependencies']}
    unknown = sorted(set(changed) - nodes.keys())
    if unknown:
        raise ValueError('Unknown changed node IDs: ' + ', '.join(unknown))
    affected = set(changed)
    while True:
        more = {node['id'] for node in nodes.values() if set(node['depends_on']) & affected}
        if more <= affected:
            break
        affected |= more
    return {'changed': sorted(set(changed)), 'affected': sorted(affected),
            'unaffected': sorted(nodes.keys() - affected),
            'limit': 'Only declared dependency edges are covered; no file is modified.'}


def validate(bundle):
    clean_json(bundle)
    if not isinstance(bundle, dict) or bundle.get('schema_version') != 1:
        raise ValueError('Expected quality bundle schema_version 1')
    if type(bundle.get('synthetic')) is not bool:
        raise ValueError('synthetic must be boolean')
    for key in ('revision', 'author_id'):
        if not isinstance(bundle.get(key), str) or not bundle[key].strip():
            raise ValueError(key + ' must be a nonempty string')
    for key in ('artifact', 'target', 'policy', 'checkpoint', 'budget'):
        if not isinstance(bundle.get(key), dict):
            raise ValueError(key + ' must be an object')
    for key in ('units', 'claims', 'source_reads', 'research_cycles', 'dependencies',
                'reviews', 'candidates', 'attempts', 'lesson_allocations'):
        if not isinstance(bundle.get(key), list) or any(not isinstance(x, dict) for x in bundle[key]):
            raise ValueError(key + ' must be an object array')
    manifest = bundle['artifact']
    for key in ('id', 'revision', 'path'):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError('artifact.' + key + ' must be a nonempty string')
    if not re.fullmatch('[0-9a-f]{64}', manifest.get('sha256', '')):
        raise ValueError('artifact.sha256 must be a lowercase SHA256 digest')
    if type(bundle['schema_version']) is not int:
        raise ValueError('schema_version must be integer')
    if bundle['target'].get('coverage_claim') not in ('selected_scope', 'full_syllabus'):
        raise ValueError('Unknown coverage claim')
    if not isinstance(bundle['target'].get('objective_ids'), list) or not bundle['target']['objective_ids']:
        raise ValueError('target.objective_ids must be a nonempty list')
    if any(not isinstance(x, str) or not x for x in bundle['target']['objective_ids']) or len(set(bundle['target']['objective_ids'])) != len(bundle['target']['objective_ids']):
        raise ValueError('Objective IDs must be unique nonempty strings')
    for key in ('max_attempts', 'max_elapsed_minutes', 'max_no_progress'):
        value = bundle['budget'].get(key)
        if value is not None and (type(value) is not int or value <= 0):
            raise ValueError('Budget limits must be null or positive integers')
    if type(bundle['policy'].get('stop_requested')) is not bool:
        raise ValueError('stop_requested must be boolean')
    for key in ('agreed',):
        if type(bundle['policy'].get(key)) is not bool:
            raise ValueError('policy.' + key + ' must be boolean')
    homework_cap = bundle['policy'].get('maximum_required_homework_minutes')
    if homework_cap is not None and (type(homework_cap) is not int or homework_cap < 0):
        raise ValueError('The weekly required-homework cap must be null or a nonnegative integer')
    for key in ('minutes_since', 'elapsed_total', 'no_progress_count'):
        if type(bundle['checkpoint'].get(key)) is not int or bundle['checkpoint'][key] < 0:
            raise ValueError('checkpoint counters must be nonnegative integers')
    for collection in ('units', 'claims', 'source_reads', 'research_cycles', 'dependencies', 'reviews', 'candidates'):
        ids = [x.get('id') for x in bundle[collection]]
        if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
            raise ValueError(collection + ': IDs must be unique nonempty strings')
    for node in bundle['dependencies']:
        if not isinstance(node.get('depends_on'), list) or any(not isinstance(x, str) for x in node['depends_on']):
            raise ValueError('depends_on must be a string array')
        if not isinstance(node.get('revision'), str) or not re.fullmatch('[0-9a-f]{64}', node.get('sha256', '')):
            raise ValueError('Dependency nodes need revision and digest')
        closure(bundle, node['id'])
    unit_ids = {x['id'] for x in bundle['units']}
    claim_ids = {x['id'] for x in bundle['claims']}
    if unit_ids & claim_ids:
        raise ValueError('Unit and claim IDs must be distinct')
    for unit in bundle['units']:
        for key in ('syllabus_ids', 'concept_ids', 'prerequisites', 'claim_ids'):
            if not isinstance(unit.get(key), list):
                raise ValueError('Unit ' + key + ' must be an array')
        if not isinstance(unit.get('chain'), dict) or not isinstance(unit.get('execution'), dict):
            raise ValueError('Unit chain and execution must be objects')
        if any(x not in claim_ids for x in unit['claim_ids']):
            raise ValueError('Unit refers to an unknown claim')
        if not isinstance(unit.get('explanation_regions', {}), dict):
            raise ValueError('explanation_regions must map theory-check IDs to artifact locators')
        explanation_checks = unit.get('explanation_checks')
        if explanation_checks is not None and (not isinstance(explanation_checks, list) or any(not isinstance(x, str) or not x for x in explanation_checks) or len(set(explanation_checks)) != len(explanation_checks)):
            raise ValueError('Unit explanation_checks must be unique nonempty check IDs')
        declared = unit.get('oracle_kinds')
        if declared is not None and (not isinstance(declared, list) or any(not isinstance(x, str) or x not in ORACLE_KINDS for x in declared) or len(set(declared)) != len(declared)):
            raise ValueError('Unit oracle_kinds must be unique supported reference kinds')
        closure(bundle, unit['id'])
    for claim in bundle['claims']:
        if not isinstance(claim.get('statement'), str) or not claim['statement'].strip() or not isinstance(claim.get('source_ids'), list) or not isinstance(claim.get('assumptions'), list) or not claim.get('domain') or not claim.get('quantity'):
            raise ValueError('Claim needs statement and source_ids')
        ancestors = {x['id'] for x in closure(bundle, claim['id'])}
        if not set(claim['source_ids']) <= ancestors:
            raise ValueError('Every cited source must be a declared claim dependency')
    for unit in bundle['units']:
        if not set(unit['claim_ids']) <= {x['id'] for x in closure(bundle, unit['id'])}:
            raise ValueError('Every used claim must be a declared unit dependency')
    for review in bundle['reviews']:
        if review.get('status') not in STATES or not isinstance(review.get('evidence'), list):
            raise ValueError('Review needs a known status and evidence array')
    for candidate in bundle['candidates']:
        if candidate.get('severity') not in TIERS or candidate.get('confidence') not in ('confirmed', 'unresolved'):
            raise ValueError('Candidate needs a defined severity and confidence')
        for key in ('object_id', 'criterion_id', 'hypothesis', 'action'):
            if not isinstance(candidate.get(key), str) or not candidate[key].strip():
                raise ValueError('Candidate ' + key + ' must be a nonempty string')
        closure(bundle, candidate['object_id'])
    return bundle


def object_fingerprint(bundle, criterion_id, object_id, root=ROOT):
    catalog = load(safe_file(root, CATALOG))
    criterion = next((x for x in catalog['criteria'] if x['id'] == criterion_id), None)
    if criterion is None:
        raise ValueError('Unknown criterion: ' + ascii(criterion_id))
    objects = {x['id']: x for x in bundle['units'] + bundle['claims']}
    obj = objects.get(object_id)
    if obj is None:
        raise ValueError('Unknown assessed object: ' + ascii(object_id))
    actual_regions = regions(safe_file(root, bundle['artifact']['path']))
    locator = obj.get('locator', 'file')
    if locator not in actual_regions:
        raise ValueError('Object locator not found in artifact: ' + ascii(locator))
    # Bind the actual regions of this object and declared upstream objects. Node
    # digests alone cannot detect an edited cell whose manifest was not refreshed.
    blueprints = {x['id']: x for x in load(safe_file(root, UNIT_SPECIFICATIONS))['units']}
    dependencies = closure(bundle, object_id)
    bound_objects = {}
    bound_dependencies = []
    for node in dependencies:
        binding = copy.deepcopy(node)
        if 'path' in node:
            binding['actual_file_sha256'] = file_digest(safe_file(root, node['path']))
        bound_dependencies.append(binding)
        dependent = objects.get(node['id'])
        if dependent is None:
            continue
        projection = copy.deepcopy(dependent)
        if criterion_id != 'K08':
            projection.pop('execution', None)
        if criterion_id != 'K15':
            projection.pop('calibration', None)
        locators = {dependent.get('locator', 'file')}
        for role in dependent.get('chain', {}).values():
            if isinstance(role, dict) and isinstance(role.get('locator'), str):
                locators.add(role['locator'])
        for locations in dependent.get('explanation_regions', {}).values():
            if isinstance(locations, list):
                locators.update(x for x in locations if isinstance(x, str))
        bound_objects[node['id']] = {
            'object': projection,
            'regions': {location: actual_regions.get(location) for location in sorted(locators)},
            'unit_specification': blueprints.get(node['id']),
        }
    stable_read_keys = ('id', 'kind', 'url', 'version', 'extent', 'locator', 'finding', 'limitation', 'method', 'result', 'content_sha256')
    theory_rubric = load(safe_file(root, THEORY_SPECIFICATION)) if criterion_id == 'K16' else None
    return digest({'criterion': criterion, 'objects': bound_objects, 'theory_rubric': theory_rubric,
                   'dependencies': bound_dependencies,
                   'source_reads': sorted(({key: x[key] for key in stable_read_keys if key in x} for x in bundle['source_reads'] if x['id'] in {n['id'] for n in dependencies}), key=lambda x: x['id']),
                   'target': {key: bundle['target'].get(key) for key in ('competition_year', 'division')}})


def _evidence(items, root):
    if not items:
        return False
    for item in items:
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and bool(item[key].strip()) for key in ('locator', 'observation')):
            return False
        if 'path' in item:
            if not item.get('sha256') or file_digest(safe_file(root, item['path'])) != item['sha256']:
                return False
    return True


def _review(bundle, criterion, object_id, root):
    matches = [r for r in bundle['reviews'] if r.get('criterion_id') == criterion and r.get('object_id') == object_id]
    if not matches:
        return 'not_run'
    review = matches[-1]
    if review.get('context_fingerprint') != object_fingerprint(bundle, criterion, object_id, root):
        return 'uncertain'
    if review['status'] == 'passed':
        if review.get('reviewer_id') in (None, '', bundle['author_id']) or not _evidence(review['evidence'], root):
            return 'uncertain'
    return review['status']


def oracle(spec):
    """Finite two-dimensional math/reference cases; no eval or submitted-code execution."""
    kind = spec.get('kind')
    if kind == 'axis_mean':
        matrix, axis = spec['input'], spec['axis']
        if type(axis) is not int or axis not in (0, 1) or not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix):
            raise ValueError('axis_mean requires rectangular nonempty 2D data and axis 0/1')
        vectors = list(zip(*matrix)) if axis == 0 else matrix
        return [sum(vector) / len(vector) for vector in vectors]
    if kind == 'binary_metrics':
        counts = [spec[key] for key in ('tp', 'fp', 'fn', 'tn')]
        if any(type(x) is not int or x < 0 for x in counts):
            raise ValueError('Binary counts must be nonnegative integers')
        tp, fp, fn, tn = counts
        zero = spec.get('zero_division')
        def ratio(numerator, denominator):
            if denominator:
                return numerator / denominator
            if zero in (0, 1) and type(zero) is int:
                return zero
            raise ValueError('Undefined ratio requires explicit zero_division 0 or 1; otherwise abstain')
        return {'accuracy': ratio(tp + tn, sum(counts)), 'precision': ratio(tp, tp + fp),
                'recall': ratio(tp, tp + fn), 'f1': ratio(2 * tp, 2 * tp + fp + fn)}
    if kind == 'weighted_sum':
        weights, values = spec['weights'], spec['values']
        if not weights or len(weights) != len(values) or any(x < 0 for x in weights) or not math.isclose(sum(weights), 1):
            raise ValueError('Weights must be nonnegative, aligned and sum to one')
        return sum(w * v for w, v in zip(weights, values))
    if kind == 'split_fit':
        train, validation, test = (set(spec[key]) for key in ('train', 'validation', 'test'))
        fit = set(spec['fit_ids'])
        return {'disjoint': not (train & validation or train & test or validation & test),
                'fit_train_only': fit <= train, 'test_used_for_selection': bool(spec['test_used_for_selection'])}
    raise ValueError('Unsupported reference check: ' + ascii(kind))


def _same(actual, expected):
    if type(actual) is bool or type(expected) is bool:
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(actual, list) and isinstance(expected, list):
        return len(actual) == len(expected) and all(_same(a, e) for a, e in zip(actual, expected))
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same(actual[k], expected[k]) for k in actual)
    return actual == expected


def evaluate(bundle, root=ROOT):
    validate(bundle)
    catalog = load(safe_file(root, CATALOG))
    contract = load(safe_file(root, CONTRACT))
    criteria = {x['id']: x for x in catalog['criteria']}
    findings, checks = [], []
    def result(cid, status, measurement, objects=None):
        checks.append({'id': cid, 'status': status, 'measurement': measurement})
        if status != 'passed':
            findings.append({'criterion_id': cid, 'status': status, 'severity': criteria[cid]['severity'],
                             'objects': sorted(objects or []), 'measurement': measurement})
    def aggregate(values):
        return 'failed' if 'failed' in values else 'uncertain' if 'uncertain' in values else 'not_run' if not values or 'not_run' in values else 'passed'
    plan = baseline(root)
    artifact_path = safe_file(root, bundle['artifact']['path'])
    actual_sha = file_digest(artifact_path)
    artifact_ok = actual_sha == bundle['artifact']['sha256']
    target_ok = all(bundle['target'].get(key) == contract[key] for key in ('competition_year', 'division'))
    result('K01', 'passed' if plan['status'] == 'passed' and artifact_ok and target_ok else 'failed',
           {'baseline': plan['status'], 'artifact_digest_matches': artifact_ok, 'target_matches': target_ok})
    units = {x['id']: x for x in bundle['units']}
    claims = {x['id']: x for x in bundle['claims']}
    expected = set(bundle['target']['objective_ids'])
    missing = expected - units.keys()
    selected = [units[k] for k in sorted(expected & units.keys())]
    blueprints = {x['id']: x for x in load(safe_file(root, UNIT_SPECIFICATIONS))['units']}
    topics = {t['id']: t for t in contract['topics']}
    coverage = []
    for unit in selected:
        ids = unit['syllabus_ids']
        if not ids or any(key not in topics for key in ids):
            coverage.append('failed')
        else:
            mode = unit.get('mode_evidence', {})
            expected_theory = any(topics[key]['theory'] for key in ids)
            expected_practical = any(topics[key]['practical'] for key in ids)
            contradictory = (expected_practical and unit.get('claimed_depth') not in ('guided', 'independent'))
            missing_modes = ((expected_theory and mode.get('theory') != 'passed') or
                             (expected_practical and mode.get('practical') != 'passed'))
            coverage.append('failed' if contradictory else 'not_run' if missing_modes else _review(bundle, 'K02', unit['id'], root))
    covered = {key for unit in selected for key in unit['syllabus_ids']}
    full_missing = set(topics) - covered if bundle['target']['coverage_claim'] == 'full_syllabus' else set()
    result('K02', aggregate(coverage + (['not_run'] if missing or full_missing else [])),
           {'requested_objectives': len(expected), 'present': len(selected), 'missing': sorted(missing),
            'planned_topics': sorted(covered), 'full_claim_missing_topics': sorted(full_missing),
            'scheduled_topics_in_plan': 60, 'scheduled_is_not_achieved': True}, missing | full_missing)
    allocation_states, allocation_details = [], []
    by_week = {}
    for allocation in bundle['lesson_allocations']:
        week = allocation.get('week')
        if type(week) is not int or week in by_week or not 1 <= week <= 10:
            raise ValueError('Lesson allocation weeks must be unique integers 1–10')
        blocks = allocation.get('blocks')
        if not isinstance(blocks, list) or not blocks:
            raise ValueError('Lesson allocations need nonempty block arrays')
        ids = [b.get('id') for b in blocks]
        if any(not isinstance(x, str) or not x for x in ids) or len(set(ids)) != len(ids):
            raise ValueError('Class block IDs must be unique')
        if any(type(b.get('minutes')) is not int or b['minutes'] < 0 or b.get('kind') not in ('theory', 'noncoding', 'coding') for b in blocks):
            raise ValueError('Class blocks need defined kinds and nonnegative integer minutes')
        expected_week = next(x for x in contract['weeks'] if x['week'] == week)
        totals = {kind: sum(b['minutes'] for b in blocks if b['kind'] == kind) for kind in ('theory', 'noncoding', 'coding')}
        written = sum(b.get('written_minutes', 0) for b in blocks)
        valid = (sum(totals.values()) == 120 and written == 10 and
                 all(totals[k] == expected_week[k + '_minutes'] for k in totals) and
                 all(type(b.get('written_minutes', 0)) is int and 0 <= b.get('written_minutes', 0) <= b['minutes'] and
                     (b.get('written_minutes', 0) == 0 or b['kind'] == 'noncoding') for b in blocks))
        by_week[week] = {b['id'] for b in blocks}
        allocation_states.append('passed' if valid else 'failed')
        allocation_details.append({'week': week, 'totals': totals, 'written_minutes_inside_blocks': written})
    for unit in selected:
        activity_ids = [unit['chain'].get(role, {}).get('activity_id') for role in ('theory', 'noncoding', 'coding', 'assessment')]
        if unit.get('week') not in by_week or any(a not in by_week.get(unit.get('week'), set()) for a in activity_ids):
            allocation_states.append('not_run')
    homework_details = []
    cap = bundle['policy'].get('maximum_required_homework_minutes')
    allocations = {x['week']: x for x in bundle['lesson_allocations']}
    selected_weeks = {u.get('week') for u in selected if type(u.get('week')) is int and 1 <= u['week'] <= 10}
    for week in sorted(selected_weeks):
        governed = next(x for x in contract['weeks'] if x['week'] == week)
        lower, upper = [hours * 60 for hours in governed['required_self_study_hours']]
        outside = allocations.get(week, {}).get('outside_work')
        detail = {'week': week, 'baseline_required_minutes': [lower, upper],
                  'weekly_cap_minutes': cap, 'required_minutes': None, 'optional_minutes': None}
        if outside is not None:
            if not isinstance(outside, list) or any(not isinstance(x, dict) for x in outside):
                raise ValueError('outside_work must be an object array')
            ids = [x.get('id') for x in outside]
            if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
                raise ValueError('Outside-work IDs must be unique nonempty strings per week')
            if any(type(x.get('required')) is not bool or type(x.get('minutes')) is not int or x['minutes'] < 0 for x in outside):
                raise ValueError('Outside work needs boolean required and nonnegative integer minutes')
            detail['required_minutes'] = sum(x['minutes'] for x in outside if x['required'])
            detail['optional_minutes'] = sum(x['minutes'] for x in outside if not x['required'])
            if detail['required_minutes'] < lower:
                allocation_states.append('failed')
                detail['ledger_status'] = 'required_plan_work_not_accounted'
            else:
                detail['ledger_status'] = 'recorded_estimate_not_observed_time'
        else:
            detail['ledger_status'] = 'not_recorded'
        if cap is None:
            detail['cap_status'] = 'not_agreed_not_assessed'
        elif upper > cap or (outside is not None and detail['required_minutes'] > cap):
            allocation_states.append('failed')
            detail['cap_status'] = 'exceeded'
        elif outside is None:
            allocation_states.append('not_run')
            detail['cap_status'] = 'current_required_work_ledger_missing'
        else:
            detail['cap_status'] = 'within_declared_cap'
        homework_details.append(detail)
    result('K03', 'failed' if plan['status'] == 'failed' else aggregate(allocation_states + (['not_run'] if missing else [])),
           {'baseline_weeks': plan['weeks'], 'material_allocations': allocation_details, 'errors': plan['errors'],
            'actual_completion_time': 'unobserved', 'outside_work_is_separate': True,
            'homework_cap_period': 'each_selected_week', 'outside_work': homework_details})
    prerequisite_states, chain_states, execution_states, assessment_states = [], [], [], []
    for unit in selected:
        prerequisites = unit['prerequisites']
        states = []
        blueprint = blueprints.get(unit['id'])
        expected_prerequisites = set(blueprint['prerequisite_ids']) if blueprint else None
        if not bundle['synthetic'] and (expected_prerequisites is None or not expected_prerequisites <= {x.get('id') for x in prerequisites}):
            states.append('failed')
        for req in prerequisites:
            if not all(req.get(key) for key in ('id', 'task', 'expected', 'observed', 'help')):
                states.append('not_run')
            elif req.get('status') == 'passed' and _evidence(req.get('evidence', []), root):
                states.append('passed')
            elif req.get('status') == 'needs_support':
                support = req.get('support_before_use')
                support_valid = (isinstance(support, dict) and support.get('before_unit') == unit['id'] and
                                 all(support.get(key) for key in ('activity_id', 'locator', 'time_location')))
                states.append('passed' if support_valid and _evidence(req.get('evidence', []), root) else 'failed')
            else:
                states.append('uncertain')
        prerequisite_states.append(aggregate(states))
        roles = unit['chain']
        actual_regions = regions(artifact_path)
        concepts = set(unit['concept_ids'])
        valid_roles = all(isinstance(roles.get(role), dict) and roles[role].get('locator') and
                          roles[role].get('expected_behavior') and roles[role].get('locator') in actual_regions and set(roles[role].get('concept_ids', [])) == concepts
                          for role in ('theory', 'noncoding', 'coding', 'assessment'))
        chain_states.append(_review(bundle, 'K05', unit['id'], root) if valid_roles and concepts else 'failed')
        assess = roles.get('assessment', {})
        independent = unit.get('claimed_depth') == 'independent'
        if independent and assess.get('help') != 'none':
            assessment_states.append('failed')
        elif independent and not assess.get('new_input'):
            assessment_states.append('failed')
        else:
            assessment_states.append(_review(bundle, 'K09', unit['id'], root))
        execution = unit['execution']
        if execution.get('status') != 'passed':
            execution_states.append(execution.get('status') if execution.get('status') in STATES else 'not_run')
        elif (execution.get('artifact_sha256') != actual_sha or (type(execution.get('exit_code')) is not int or execution['exit_code'] != 0) or
              not all(execution.get(key) for key in ('command', 'environment')) or
              execution.get('clean_run') is not True or execution.get('new_input') is not True or
              not execution.get('assertions') or any(x.get('status') != 'passed' for x in execution['assertions']) or
              not _evidence(execution.get('evidence', []), root) or
              not any('path' in x for x in execution.get('evidence', []))):
            execution_states.append('failed')
        else:
            execution_states.append('passed')
    extra = ['not_run'] if missing else []
    result('K04', aggregate(prerequisite_states + extra), {'diagnosed_units': len(selected), 'missing_units': sorted(missing)}, [u['id'] for u, status in zip(selected, prerequisite_states) if status != 'passed'])
    result('K05', aggregate(chain_states + extra), {'linked_units': len(selected), 'semantic_review_required': True}, [u['id'] for u, status in zip(selected, chain_states) if status != 'passed'])
    referenced_claims = {key for unit in selected for key in unit['claim_ids']}
    theory_states = [_review(bundle, 'K06', key, root) for key in sorted(referenced_claims)]
    if any(not unit['claim_ids'] for unit in selected):
        theory_states.append('not_run')
    result('K06', aggregate(theory_states + extra), {'claims': sorted(referenced_claims), 'reviewed_records_only': True}, [key for key, status in zip(sorted(referenced_claims), theory_states) if status != 'passed'])
    numerical = []
    numerical_details = []
    for cid in sorted(referenced_claims):
        claim = claims[cid]
        if 'oracle' not in claim:
            continue
        try:
            actual = oracle(claim['oracle'])
            status = 'passed' if _same(actual, claim['oracle'].get('expected')) else 'failed'
            if claim['oracle']['kind'] == 'split_fit' and (not actual['disjoint'] or not actual['fit_train_only'] or actual['test_used_for_selection']):
                status = 'failed'
            numerical_details.append({'claim_id': cid, 'status': status, 'actual': actual})
        except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError) as exc:
            status = 'uncertain'
            numerical_details.append({'claim_id': cid, 'status': status, 'reason': str(exc)})
        numerical.append(status)
    unit_oracles, oracle_gaps = [], []
    for unit in selected:
        blueprint = blueprints.get(unit['id'])
        # Real unit requirements come from the versioned specification. Synthetic
        # custom units must declare an explicit contract, including an empty list.
        required = blueprint['oracle_kinds'] if blueprint else unit.get('oracle_kinds') if bundle['synthetic'] else None
        present = {claims[cid].get('oracle', {}).get('kind') for cid in unit['claim_ids'] if 'oracle' in claims[cid]}
        missing_kinds = sorted(set(required) - present) if required is not None else []
        status = 'uncertain' if required is None else 'not_run' if missing_kinds else 'passed'
        numerical.append(status)
        if status != 'passed':
            oracle_gaps.append(unit['id'])
        unit_oracles.append({'unit_id': unit['id'], 'required_kinds': required,
                             'present_kinds': sorted(present), 'missing_kinds': missing_kinds,
                             'status': status, 'basis': 'versioned_unit_specification' if blueprint else 'synthetic_declaration' if bundle['synthetic'] else 'missing_unit_specification'})
    result('K07', aggregate(numerical + extra), {'reference_checks': numerical_details, 'unit_requirements': unit_oracles,
           'empty_requirement': 'No numerical oracle is required; semantic and execution checks still apply.'},
           [x['claim_id'] for x in numerical_details if x['status'] != 'passed'] + oracle_gaps)
    result('K08', aggregate(execution_states + extra), {'receipts_checked': len(selected), 'does_not_authenticate_execution': True}, [u['id'] for u, status in zip(selected, execution_states) if status != 'passed'])
    result('K09', aggregate(assessment_states + extra), {'assessments_checked': len(selected), 'learning_outcomes': bundle['target'].get('learning_outcomes', 'untested')}, [u['id'] for u, status in zip(selected, assessment_states) if status != 'passed'])
    reads = {x['id']: x for x in bundle['source_reads']}
    source_states = []
    for cid in sorted(referenced_claims):
        claim = claims[cid]
        if not claim['source_ids']:
            source_states.append('not_run')
        for sid in claim['source_ids']:
            read = reads.get(sid)
            if not read:
                source_states.append('not_run')
                continue
            empirical = claim.get('claim_type') == 'empirical_effect'
            required = ('method', 'result', 'limitation') if empirical else ('finding', 'limitation')
            adequate = (read.get('kind') in ('official', 'academic_primary', 'documentation') and
                        read.get('extent') in ('relevant_sections', 'full_text') and
                        all(read.get(key) for key in ('url', 'version', 'accessed_at', 'locator', *required)))
            source_states.append('passed' if adequate else 'uncertain')
    result('K10', aggregate(source_states + extra), {'claim_count': len(referenced_claims), 'read_receipts': len(reads), 'reading_authenticity': 'not_authenticated'}, sorted(referenced_claims))
    cycles = bundle['research_cycles']
    cycle_states, active_cycles = [], []
    for oid in sorted(referenced_claims):
        matches = [c for c in cycles if isinstance(c.get('object_ids'), list) and oid in c['object_ids']]
        if not matches:
            cycle_states.append('not_run')
            active_cycles.append({'object_id': oid, 'cycle_id': None, 'status': 'not_run'})
            continue
        cycle = matches[-1]
        valid = all(cycle.get(key) for key in ('trigger', 'queries', 'source_ids', 'disposition', 'reason'))
        valid &= isinstance(cycle.get('queries'), list) and all(isinstance(q, str) and bool(q.strip()) for q in cycle.get('queries', []))
        contexts = cycle.get('object_contexts', {})
        valid &= isinstance(contexts, dict) and contexts.get(oid) == object_fingerprint(bundle, 'K10', oid, root)
        source_ids = cycle.get('source_ids', [])
        valid &= isinstance(source_ids, list) and all(sid in reads for sid in source_ids)
        valid &= set(claims[oid]['source_ids']) <= set(source_ids)
        status = 'passed' if valid and cycle.get('disposition') in ('updated', 'unchanged') else 'uncertain'
        cycle_states.append(status)
        active_cycles.append({'object_id': oid, 'cycle_id': cycle['id'], 'status': status})
    result('K11', aggregate(cycle_states + extra), {'cycles': len(cycles), 'active_by_object': active_cycles,
           'selection': 'last_appended_cycle_per_current_claim', 'automatic_search': False},
           [x['object_id'] for x in active_cycles if x['status'] != 'passed'])
    current_objects = {u['id'] for u in selected} | referenced_claims
    latest = {}
    for review in bundle['reviews']:
        if review.get('object_id') in current_objects and review.get('criterion_id') in REVIEW_CRITERIA:
            latest[(review['criterion_id'], review['object_id'])] = review
    stale = []
    for review in latest.values():
        try:
            if review.get('context_fingerprint') != object_fingerprint(bundle, review['criterion_id'], review['object_id'], root):
                stale.append(review['id'])
        except ValueError:
            stale.append(review['id'])
    active_review_ids = {r['id'] for r in latest.values()}
    historical = [r['id'] for r in bundle['reviews'] if r['id'] not in active_review_ids]
    result('K12', 'uncertain' if stale else 'passed', {'stale_review_ids': stale,
           'active_review_ids': sorted(active_review_ids), 'historical_review_ids': historical,
           'selection': 'last_appended_review_per_criterion_and_current_object',
           'dependency_nodes': len(bundle['dependencies'])},
           [r['object_id'] for r in latest.values() if r['id'] in stale])
    keys = [candidate_key(bundle, item, root) for item in bundle['candidates']]
    repeats = sorted({key for key in keys if keys.count(key) > 1})
    result('K13', 'passed', {'exact_duplicate_proposals': len(repeats), 'action': 'suppress_duplicates', 'semantic_merge': False})
    agreed = (bundle['policy']['agreed'] and bool(bundle['policy'].get('decision_ref')) and
              bundle['policy'].get('agreement_fingerprint') == agreement_fingerprint(bundle, root))
    result('K14', 'passed' if agreed else 'uncertain', {'priority_policy': 'agreed_record' if agreed else 'proposal',
           'checkpoint_due': bundle['checkpoint']['minutes_since'] >= 30, 'thresholds_not_invented': True,
           'agreement_fingerprint': agreement_fingerprint(bundle, root)})
    calibration = []
    calibration_counts = []
    tolerance = bundle['policy'].get('calibration_tolerance')
    for unit in selected:
        controls = unit.get('calibration', [])
        known_good = [x for x in controls if x.get('expected') == 'passed']
        known_fault = [x for x in controls if x.get('expected') == 'failed']
        fp = sum(x.get('observed') != 'passed' for x in known_good)
        fn = sum(x.get('observed') != 'failed' for x in known_fault)
        calibration_counts.append({'unit': unit['id'], 'known_good': len(known_good), 'known_fault': len(known_fault), 'false_rejects': fp, 'missed_faults': fn})
        if not known_good or not known_fault:
            calibration.append('not_run')
        elif any(not x.get('case_id') or not _evidence(x.get('evidence', []), root) for x in controls):
            calibration.append('uncertain')
        elif not isinstance(tolerance, dict) or type(tolerance.get('false_rejects')) is not int or type(tolerance.get('missed_faults')) is not int:
            calibration.append('uncertain')
        elif fp > tolerance['false_rejects'] or fn > tolerance['missed_faults']:
            calibration.append('failed')
        else:
            calibration.append(_review(bundle, 'K15', unit['id'], root))
    learning_claim = bundle['target'].get('learning_outcomes', 'untested')
    if learning_claim != 'untested':
        calibration.append('uncertain' if _evidence(bundle['target'].get('learner_study_evidence', []), root) else 'failed')
    result('K15', aggregate(calibration + extra), {'educator_calibration': 'requires_actual_evidence',
           'learning_outcomes': learning_claim, 'tool_tests_are_not_learner_results': True, 'controls': calibration_counts}, [u['id'] for u, status in zip(selected, calibration) if status != 'passed'])
    explanation_states, explanation_details = [], []
    theory_rubric = load(safe_file(root, THEORY_SPECIFICATION))
    theory_ids = {x['id'] for x in theory_rubric['checks']}
    actual_regions = regions(artifact_path)
    for unit in selected:
        blueprint = blueprints.get(unit['id'])
        required = blueprint['explanation_checks'] if blueprint else unit.get('explanation_checks') if bundle['synthetic'] else None
        registered = unit.get('explanation_regions', {})
        if required is None:
            explanation_states.append('uncertain')
            explanation_details.append({'unit_id': unit['id'], 'status': 'uncertain', 'reason': 'missing_unit_explanation_contract'})
            continue
        expected_checks = set(required) | set(registered) | {'T05'}
        matches = [r for r in bundle['reviews'] if r.get('criterion_id') == 'K16' and r.get('object_id') == unit['id']]
        review = matches[-1] if matches else None
        subchecks = review.get('subchecks', {}) if review else {}
        if not isinstance(subchecks, dict):
            subchecks = {}
        states, details = [], []
        for identifier in sorted(expected_checks):
            locations = registered.get(identifier)
            subcheck = subchecks.get(identifier)
            if identifier not in theory_ids:
                status, reason = 'failed', 'unknown_theory_check'
            elif not isinstance(locations, list) or not locations:
                status, reason = 'not_run', 'explanation_regions_missing'
            elif any(not isinstance(loc, str) or loc not in actual_regions for loc in locations):
                status, reason = 'failed', 'explanation_region_not_found'
            elif not isinstance(subcheck, dict):
                status, reason = 'not_run', 'independent_subcheck_missing'
            else:
                status = subcheck.get('status', 'not_run')
                reason = 'recorded_review_outcome'
                if status not in STATES:
                    status, reason = 'uncertain', 'unknown_subcheck_outcome'
                if status == 'passed':
                    covered = subcheck.get('artifact_locators')
                    complete = (isinstance(covered, list) and all(isinstance(loc, str) for loc in covered)
                                and set(covered) == set(locations))
                    if not complete or not _evidence(subcheck.get('evidence', []), root):
                        status, reason = 'uncertain', 'subcheck_support_or_region_coverage_missing'
            states.append(status)
            details.append({'id': identifier, 'status': status, 'reason': reason, 'artifact_locators': locations})
        states.append(_review(bundle, 'K16', unit['id'], root))
        status = aggregate(states)
        explanation_states.append(status)
        explanation_details.append({'unit_id': unit['id'], 'status': status, 'checks': details,
                                    'review_id': review['id'] if review else None})
    result('K16', aggregate(explanation_states + extra), {'units': explanation_details,
           'rubric_revision': theory_rubric['revision'], 'semantic_understanding': 'not_automated',
           'learner_understanding': 'unobserved_without_actual_learner_evidence'},
           [u['id'] for u, status in zip(selected, explanation_states) if status != 'passed'])
    ready = all(check['status'] == 'passed' for check in checks)
    return {'schema_version': 1, 'authority': 'advisory_only', 'synthetic': bundle['synthetic'],
            'revision': bundle['revision'], 'bundle_sha256': digest(bundle), 'artifact_sha256': actual_sha,
            'specification_sha256': file_digest(safe_file(root, CATALOG)), 'specification_revision': catalog['revision'],
            'evaluator_sha256': file_digest(Path(__file__)),
            'ready_for_review': ready, 'status': 'passed' if ready else 'failed' if any(c['status'] == 'failed' for c in checks) else 'uncertain',
            'checks': checks, 'findings': findings,
            'limits': ['Semantic judgments and source reading are recorded claims, not authenticated facts.',
                       'Synthetic success is not real material readiness.', 'No worker, scheduler, writer or publisher is executed.']}


def agreement_fingerprint(bundle, root=ROOT):
    contract = load(safe_file(root, CONTRACT))
    return digest({'criteria': load(safe_file(root, CATALOG)),
                   'unit_specifications': load(safe_file(root, UNIT_SPECIFICATIONS)),
                   'theory_specification': load(safe_file(root, THEORY_SPECIFICATION)),
                   'governing_scope': {key: contract[key] for key in ('competition_year', 'division', 'syllabus_label', 'class_minutes')},
                   'official_modes': [{k: t[k] for k in ('id', 'theory', 'practical')} for t in contract['topics']],
                   'target': bundle['target'], 'budget': bundle['budget'],
                   'diagnostic_cutoff': bundle['policy'].get('diagnostic_cutoff'),
                   'maximum_required_homework_minutes': bundle['policy'].get('maximum_required_homework_minutes'),
                   'calibration_tolerance': bundle['policy'].get('calibration_tolerance'),
                   'checkpoint_minutes': 30})


def candidate_key(bundle, candidate, root=ROOT):
    return digest({'criterion': candidate['criterion_id'], 'object': candidate['object_id'],
                   'hypothesis': candidate['hypothesis'].strip(), 'action': candidate['action'].strip(),
                   'new_evidence_basis': candidate.get('evidence_basis', []),
                   'context': object_fingerprint(bundle, candidate['criterion_id'], candidate['object_id'], root)})


def plan_work(bundle, root=ROOT):
    report = evaluate(bundle, root)
    previous = {x['key']: x for x in bundle['attempts'] if x.get('outcome') in ('accepted', 'rejected', 'no_change')}
    ranked, skipped, seen = [], [], set()
    candidates = copy.deepcopy(bundle['candidates'])
    existing_targets = {(x['criterion_id'], x['object_id']) for x in candidates}
    object_ids = {x['id'] for x in bundle['units'] + bundle['claims']}
    for finding in report['findings']:
        for oid in finding['objects']:
            if oid in object_ids and (finding['criterion_id'], oid) not in existing_targets:
                candidates.append({'id': 'finding:' + finding['criterion_id'] + ':' + oid,
                                   'criterion_id': finding['criterion_id'], 'object_id': oid,
                                   'severity': finding['severity'], 'confidence': 'confirmed' if finding['status'] == 'failed' else 'unresolved',
                                   'hypothesis': 'Resolve ' + finding['status'] + ' ' + finding['criterion_id'] + ' evidence for ' + oid,
                                   'action': 'Inspect the criterion measurement and original evidence; make one scoped correction or record abstention.'})
    for item in candidates:
        matching = [f for f in report['findings'] if f['criterion_id'] == item['criterion_id'] and item['object_id'] in f['objects'] and f['status'] == 'failed']
        if matching:
            computed_severity = min((f['severity'] for f in matching), key=lambda x: TIERS[x])
            if TIERS[computed_severity] < TIERS[item['severity']]:
                item['severity'] = computed_severity
            item['confidence'] = 'confirmed'
            item['priority_basis'] = 'computed_failed_criterion'
        key = candidate_key(bundle, item, root)
        if key in seen or key in previous:
            skipped.append({'id': item['id'], 'key': key, 'reason': previous.get(key, {}).get('reason', 'exact_duplicate')})
            continue
        seen.add(key)
        affected = impact(bundle, [item['object_id']])['affected']
        # Unresolved possible critical defects get evidence-gathering priority P1, not a false confirmed P0 label.
        tier = max(TIERS[item['severity']], 1) if item['confidence'] == 'unresolved' else TIERS[item['severity']]
        ranked.append({**copy.deepcopy(item), 'key': key, 'priority': 'P' + str(tier),
                       'affected_ids': affected, '_rank': (tier, -len(affected), item['id'])})
    ranked.sort(key=lambda x: x['_rank'])
    for item in ranked:
        del item['_rank']
    checkpoint_due = bundle['checkpoint']['minutes_since'] >= 30
    agreed = (bundle['policy']['agreed'] and bool(bundle['policy'].get('decision_ref')) and
              bundle['policy'].get('agreement_fingerprint') == agreement_fingerprint(bundle, root))
    trailing = 0
    for attempt in reversed(bundle['attempts']):
        if attempt.get('outcome') == 'accepted':
            break
        trailing += 1
    budget = bundle['budget']
    exhausted = ((budget.get('max_attempts') is not None and len(bundle['attempts']) >= budget['max_attempts']) or
                 (budget.get('max_elapsed_minutes') is not None and bundle['checkpoint']['elapsed_total'] >= budget['max_elapsed_minutes']) or
                 (budget.get('max_no_progress') is not None and max(trailing, bundle['checkpoint']['no_progress_count']) >= budget['max_no_progress']))
    active_tiers = [max(TIERS[f['severity']], 1) if f['status'] != 'failed' else TIERS[f['severity']] for f in report['findings']]
    best_blocker = min(active_tiers, default=4)
    if bundle['policy']['stop_requested']:
        status, reason = 'stop', 'operator_stop'
    elif not report['checks'][0]['status'] == 'passed':
        status, reason = 'blocked', 'baseline_or_artifact_binding_failed'
    elif exhausted:
        status, reason = 'stop', 'finite_budget_exhausted'
    elif checkpoint_due:
        status, reason = 'pause', 'checkpoint_due'
    elif not agreed:
        status, reason = 'pause', 'priority_policy_requires_agreement'
    elif any(budget.get(key) is None for key in ('max_attempts', 'max_elapsed_minutes', 'max_no_progress')):
        status, reason = 'pause', 'finite_budget_requires_agreement'
    elif ranked and int(ranked[0]['priority'][1]) > best_blocker:
        status, reason = 'pause', 'blocking_finding_requires_scoped_candidate'
    elif ranked:
        status, reason = 'continue', 'highest_priority_new_candidate'
    elif report['ready_for_review']:
        status, reason = 'stop', 'recorded_checks_ready_for_independent_final_review'
    else:
        status, reason = 'noop', 'no_new_candidate_not_complete'
    return {'status': status, 'reason': reason, 'authority': 'advisory_only', 'synthetic': bundle['synthetic'],
            'quality_status': report['status'], 'ranked': ranked, 'skipped': skipped,
            'next_candidate': ranked[0]['id'] if ranked and status == 'continue' else None,
            'checkpoint_required_fields': ['artifact version', 'changed sources', 'checks and uncertainty',
                                           'accepted/rejected/no-change work', 'usage and remaining finite budget',
                                           'in-flight work', 'next action and unresolved decisions'],
            'limit': 'Proposal ranking does not authorize execution or establish completion.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('baseline', 'evaluate', 'plan', 'impact', 'review-context', 'agreement-context'))
    parser.add_argument('bundle', nargs='?', type=Path)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--changed', action='append', default=[])
    parser.add_argument('--criterion')
    parser.add_argument('--object')
    args = parser.parse_args(argv)
    try:
        if args.command == 'baseline':
            result = baseline(args.root)
        else:
            if args.bundle is None:
                parser.error('This command requires a bundle')
            bundle = validate(load(args.bundle))
            if args.command == 'evaluate':
                result = evaluate(bundle, args.root)
            elif args.command == 'plan':
                result = plan_work(bundle, args.root)
            elif args.command == 'agreement-context':
                result = {'authority': 'advisory_only', 'agreement_fingerprint': agreement_fingerprint(bundle, args.root)}
            elif args.command == 'impact':
                if not args.changed:
                    parser.error('impact requires --changed')
                result = {'authority': 'advisory_only', **impact(bundle, args.changed)}
            else:
                if not args.criterion or not args.object:
                    parser.error('review-context requires --criterion and --object')
                result = {'authority': 'advisory_only', 'context_fingerprint':
                          object_fingerprint(bundle, args.criterion, args.object, args.root)}
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
        return 2 if result.get('errors') else 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, OverflowError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': 'invalid_quality_input',
                          'authority': 'advisory_only', 'errors': [ascii(str(exc))]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
