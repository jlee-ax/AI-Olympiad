#!/usr/bin/env python3
"""Bounded, replayable discovery bookkeeping with real local reads, not a semantic agent."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re

VERSION = 'discovery-loop-v1'
KINDS = {'official_scope', 'official_problem', 'research', 'background'}
LIMITS = [
    'Discovery/search execution, official attribution, semantic extraction and adequacy judgments are supplied by a human or model; this program does not browse or run one.',
    'Read receipts prove the bytes and line ranges opened by this program, not reader comprehension, source truth or completeness of the external universe.',
    'The frozen frontier and append-only hash chain expose changed declarations when bound to a review; they do not authenticate identity or prevent a caller from rewriting and rebinding history.',
    'Recorded readiness applies only to the declared boundary; deferred placement does not establish later teaching or learner performance.',
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be nonempty text')
    value.encode('utf-8')
    return value


def strings(value, label, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError(label + ' must be ' + ('a nonempty' if nonempty else 'an') + ' array')
    for item in value:
        text(item, label)
    if len(set(value)) != len(value):
        raise ValueError(label + ' must not contain duplicates')
    return value


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(label + ' must be an integer >= ' + str(minimum))
    return value


def local_file(root, name):
    text(name, 'path')
    if Path(name).is_absolute():
        raise ValueError('Paths must be root-relative')
    path = (Path(root).resolve() / name).resolve()
    if not path.is_relative_to(Path(root).resolve()) or not path.is_file():
        raise ValueError('File missing or outside root: ' + name)
    return path


def read_span(root, name, start, end):
    integer(start, 'start_line', 1)
    integer(end, 'end_line', start)
    raw = local_file(root, name).read_bytes()
    lines = raw.decode('utf-8').splitlines(keepends=True)
    if end > len(lines):
        raise ValueError('Read range exceeds file: ' + name)
    excerpt = ''.join(lines[start - 1:end])
    return {'path': name, 'sha256': hashlib.sha256(raw).hexdigest(),
            'start_line': start, 'end_line': end, 'excerpt': excerpt,
            'excerpt_sha256': hashlib.sha256(excerpt.encode()).hexdigest()}


def verify_receipt(receipt):
    if not isinstance(receipt, dict):
        raise ValueError('Missing read receipt')
    for key in ('path', 'excerpt'):
        text(receipt.get(key), 'receipt.' + key)
    integer(receipt.get('start_line'), 'receipt.start_line', 1)
    integer(receipt.get('end_line'), 'receipt.end_line', receipt['start_line'])
    for key in ('sha256', 'excerpt_sha256'):
        if not isinstance(receipt.get(key), str) or not re.fullmatch(r'[0-9a-f]{64}', receipt[key]):
            raise ValueError('Invalid receipt digest')
    if hashlib.sha256(receipt['excerpt'].encode()).hexdigest() != receipt['excerpt_sha256']:
        raise ValueError('Corrupt receipt excerpt')


def initialize(config):
    if not isinstance(config, dict) or type(config.get('schema_version')) is not int or config['schema_version'] != 1:
        raise ValueError('Expected discovery schema_version 1')
    if type(config.get('synthetic')) is not bool:
        raise ValueError('synthetic must be boolean')
    scope = config['scope']
    for key in ('id', 'lesson_path', 'boundary', 'lesson_revision'):
        text(scope.get(key), 'scope.' + key)
    if scope.get('readiness') not in ('scoped_foundation', 'course'):
        raise ValueError('readiness must be scoped_foundation or course')
    if 'artifact_path' in scope or 'artifact_sha256' in scope:
        text(scope.get('artifact_path'), 'scope.artifact_path')
        if not isinstance(scope.get('artifact_sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', scope['artifact_sha256']):
            raise ValueError('scope.artifact_sha256 must bind the original artifact')
    frontier = config['frontier']
    if not isinstance(frontier, list) or not frontier:
        raise ValueError('Seed the external frontier before lesson comparison')
    seen = set()
    for probe in frontier:
        text(probe.get('id'), 'frontier.id')
        text(probe.get('question'), 'frontier.question')
        if probe['id'] in seen:
            raise ValueError('Duplicate frontier id')
        seen.add(probe['id'])
        if not set(strings(probe.get('required_kinds'), 'required_kinds', True)) <= KINDS:
            raise ValueError('Unknown source kind')
    for key in ('max_events', 'max_rounds', 'max_no_progress', 'max_elapsed_minutes'):
        integer(config['policy'].get(key), 'policy.' + key, 1)
    seed = copy.deepcopy(config)
    return {'schema_version': 1, 'seed': seed, 'seed_sha256': digest(seed), 'events': []}


def replay(state):
    if not isinstance(state, dict) or state.get('schema_version') != 1:
        raise ValueError('Expected discovery session schema_version 1')
    initialize(state['seed'])
    if state.get('seed_sha256') != digest(state['seed']):
        raise ValueError('Changed seed/frontier: start an explicitly new review baseline')
    if not isinstance(state.get('events'), list):
        raise ValueError('events must be an array')
    view = {'sources': {}, 'reads': {}, 'demands': {}, 'comparisons': {}, 'retired': {},
            'searches': [], 'traces': [], 'questions': {}, 'retired_sources': {}, 'retirement_reviews': [], 'demand_aliases': {}, 'frontier': {p['id']: p for p in state['seed']['frontier']},
            'paused': False, 'elapsed_minutes': 0, 'rounds': 0, 'no_progress': 0}
    previous, ids = state['seed_sha256'], set()
    for index, event in enumerate(state['events']):
        policy = state['seed']['policy']
        if (index >= policy['max_events'] or view['rounds'] >= policy['max_rounds'] or
                view['no_progress'] >= policy['max_no_progress'] or view['elapsed_minutes'] >= policy['max_elapsed_minutes']):
            raise ValueError('Event appended after finite budget exhaustion; resume cannot erase a historical stop')
        text(event.get('id'), 'event.id')
        if event['id'] in ids:
            raise ValueError('Duplicate event id')
        ids.add(event['id'])
        payload = {k: v for k, v in event.items() if k not in ('previous_sha256', 'sha256')}
        if event.get('previous_sha256') != previous or event.get('sha256') != digest({'previous_sha256': previous, **payload}):
            raise ValueError('Broken event chain; history cannot be dropped or edited')
        previous = event['sha256']
        apply_event(view, payload, state['seed'])
    return view


def apply_event(view, event, seed):
    op = event['op']
    data = event['data']
    if not isinstance(data, dict):
        raise ValueError('event.data must be an object')
    text(data.get('reason'), 'event.reason')
    integer(data.get('minutes', 0), 'event.minutes')
    view['elapsed_minutes'] += data.get('minutes', 0)
    if view['paused'] and op != 'resume':
        raise ValueError('Paused session requires an explicit resume event')
    if op in ('pause', 'resume'):
        view['paused'] = op == 'pause'
    elif op == 'frontier':
        probe = data['probe']
        # Additions are explicit and never remove an earlier obligation.
        initialize({**seed, 'frontier': [probe]})
        if probe['id'] in view['frontier']:
            raise ValueError('Frontier identifiers are immutable; add a new probe')
        for qid in strings(data.get('resolves', []), 'frontier.resolves'):
            if qid not in view['questions'] or view['questions'][qid].get('resolved_by'):
                raise ValueError('Only an open known question can expand into a new frontier')
            view['questions'][qid]['resolved_by'] = probe['id']
        view['frontier'][probe['id']] = probe
    elif op == 'discover':
        if data['frontier_id'] not in view['frontier']:
            raise ValueError('Unknown frontier')
        for field in ('query', 'actor'):
            text(data.get(field), field)
        if data.get('outcome') not in ('found', 'unavailable', 'no_results'):
            raise ValueError('Invalid discovery outcome')
        candidates = data.get('candidates')
        if not isinstance(candidates, list) or (data['outcome'] == 'found') != bool(candidates):
            raise ValueError('Found searches need candidates; other outcomes must preserve an empty result')
        old_source_keys = {digest({key: source[key] for key in ('uri', 'path', 'revision', 'kind')}) for source in view['sources'].values()}
        new_source_keys = {digest({key: source[key] for key in ('uri', 'path', 'revision', 'kind')}) for source in candidates} - old_source_keys
        for source in candidates:
            for field in ('id', 'uri', 'path', 'revision', 'attribution'):
                text(source.get(field), 'source.' + field)
            if source.get('kind') not in KINDS:
                raise ValueError('Invalid source kind')
            if source['id'] in view['sources'] and source != view['sources'][source['id']]:
                raise ValueError('Source versions are immutable: use a new source id')
            view['sources'][source['id']] = source
        view['searches'].append({'event_id': event['id'], **data})
        view['rounds'] += 1
        view['no_progress'] = 0 if new_source_keys else view['no_progress'] + 1
    elif op == 'read':
        source = view['sources'][data['source_id']]
        text(data.get('actor'), 'read.actor')
        verify_receipt(data.get('receipt'))
        if data['receipt']['path'] != source['path']:
            raise ValueError('Read receipt must name the discovered source')
        view['reads'][event['id']] = data
    elif op == 'supersede_source':
        old, new = data['old_source_id'], data['new_source_id']
        if old not in view['sources'] or new not in view['sources'] or old == new or old in view['retired_sources']:
            raise ValueError('Source supersession needs active old and distinct new versions')
        text(data.get('reviewer'), 'supersede_source.reviewer')
        current, seen = new, {old}
        while current in view['retired_sources']:
            if current in seen:
                raise ValueError('Source supersession cycle')
            seen.add(current)
            current = view['retired_sources'][current]
        if current in seen:
            raise ValueError('Source supersession cycle')
        view['retired_sources'][old] = new
    elif op == 'trace':
        if data['frontier_id'] not in view['frontier']:
            raise ValueError('Unknown frontier')
        for field in ('actor', 'rationale', 'counterevidence'):
            text(data.get(field), 'trace.' + field)
        strings(data.get('uninvestigated'), 'trace.uninvestigated')
        strings(data.get('read_ids'), 'trace.read_ids', True)
        if any(rid not in view['reads'] for rid in data['read_ids']):
            raise ValueError('Trace requires prior direct-read receipts')
        if any(view['reads'][rid]['source_id'] in view['retired_sources'] for rid in data['read_ids']):
            raise ValueError('Trace must use current source versions, not retired reads')
        discovered = {source['id'] for search in view['searches'] if search['frontier_id'] == data['frontier_id'] for source in search['candidates']}
        if any(view['reads'][rid]['source_id'] not in discovered for rid in data['read_ids']):
            raise ValueError('Trace reads must come from that frontier discovery')
        for question in data['uninvestigated']:
            qid = 'question:' + digest({'frontier_id': data['frontier_id'], 'question': question})[:16]
            view['questions'].setdefault(qid, {'id': qid, 'frontier_id': data['frontier_id'], 'question': question, 'trace_id': event['id'], 'resolved_by': None})
        if not isinstance(data.get('demands'), list):
            raise ValueError('trace.demands must be an array')
        new_demands = 0
        for demand in data['demands']:
            for field in ('id', 'statement', 'learning_demand', 'assessment_demand'):
                text(demand.get(field), 'demand.' + field)
            strings(demand.get('prerequisites'), 'demand.prerequisites')
            if 'dimensions' in demand:
                if not isinstance(demand['dimensions'], list) or not demand['dimensions']:
                    raise ValueError('Demand dimensions must be nonempty')
                dimension_ids = set()
                for dimension in demand['dimensions']:
                    text(dimension.get('id'), 'dimension.id')
                    text(dimension.get('required_behavior'), 'dimension.required_behavior')
                    if dimension['id'] in dimension_ids:
                        raise ValueError('Duplicate demand dimension id')
                    dimension_ids.add(dimension['id'])
            if demand['id'] in view['demands'] or demand['id'] in view['demand_aliases']:
                raise ValueError('Demand ids are immutable; explicitly supersede with a new demand')
            payload = {key: value for key, value in demand.items() if key != 'id'}
            duplicate = next((old for old in view['demands'].values() if
                              {key: value for key, value in old.items() if key not in ('id', 'trace_id', 'frontier_id', 'read_ids')} == payload
                              and old['frontier_id'] == data['frontier_id'] and read_basis(view, old['read_ids']) == read_basis(view, data['read_ids'])), None)
            if duplicate:
                view['demand_aliases'][demand['id']] = duplicate['id']
                continue
            new_demands += 1
            view['demands'][demand['id']] = {**demand, 'trace_id': event['id'],
                                          'frontier_id': data['frontier_id'], 'read_ids': data['read_ids']}
        view['traces'].append({'event_id': event['id'], **data})
        view['no_progress'] = 0 if new_demands else view['no_progress'] + 1
    elif op == 'compare':
        did = view['demand_aliases'].get(data['demand_id'], data['demand_id'])
        demand = view['demands'][did]
        text(data.get('reviewer'), 'compare.reviewer')
        if data['reviewer'] == next(t['actor'] for t in view['traces'] if t['event_id'] == demand['trace_id']):
            raise ValueError('Comparison needs a distinct declared reviewer from demand extraction')
        text(data.get('rationale'), 'compare.rationale')
        if data.get('judgment') not in ('covered', 'gap', 'uncertain', 'deferred', 'out_of_scope'):
            raise ValueError('Invalid comparison judgment')
        verify_receipt(data.get('lesson_receipt'))
        if data['lesson_receipt']['path'] != seed['scope']['lesson_path']:
            raise ValueError('Comparison must read the selected actual lesson')
        if data['judgment'] not in ('deferred', 'out_of_scope'):
            expected = {item['id'] for item in demand_dimensions(demand)}
            dimensions = data.get('dimensions')
            if not isinstance(dimensions, list) or len(dimensions) != len(expected) or {item['id'] for item in dimensions} != expected:
                raise ValueError('Compare every demand-specific learning/assessment/prerequisite dimension')
            for dimension in dimensions:
                if dimension.get('judgment') not in ('met', 'gap', 'uncertain'):
                    raise ValueError('Invalid dimension judgment')
                for field in ('observed_behavior', 'rationale'):
                    text(dimension.get(field), 'dimension.' + field)
                verify_receipt(dimension.get('receipt'))
                if dimension['receipt']['path'] != seed['scope']['lesson_path']:
                    raise ValueError('Dimension must read actual lesson bytes')
        if data['judgment'] in ('deferred', 'out_of_scope'):
            text(data.get('scope_basis'), 'compare.scope_basis')
        if data['judgment'] == 'deferred':
            placement = data['placement']
            for field in ('unit_id', 'owner', 'rationale'):
                text(placement.get(field), 'placement.' + field)
            verify_receipt(placement.get('receipt'))
        view['comparisons'][did] = {'event_id': event['id'], **data, 'demand_id': did}
    elif op in ('supersede', 'review_supersession'):
        old, new = data['old_demand_id'], data['new_demand_id']
        if old not in view['demands'] or new not in view['demands'] or old == new:
            raise ValueError('Supersession requires old and distinct successor demands')
        if op == 'supersede' and old in view['retired']:
            raise ValueError('Supersession requires an active old demand')
        if op == 'review_supersession' and view['retired'].get(old) != new:
            raise ValueError('Re-review must bind the existing old-to-successor mapping')
        text(data.get('reviewer'), 'supersede.reviewer')
        if view['demands'][old]['frontier_id'] != view['demands'][new]['frontier_id']:
            raise ValueError('Replacement demand must retain the original frontier obligation')
        old_dimensions = {d['id']: d for d in demand_dimensions(view['demands'][old])}
        new_dimensions = {d['id']: d for d in demand_dimensions(view['demands'][new])}
        dispositions = data.get('dimension_dispositions')
        if not isinstance(dispositions, list) or len(dispositions) != len(old_dimensions) or {d['old_dimension_id'] for d in dispositions} != set(old_dimensions):
            raise ValueError('Supersession needs an explicit disposition for every old demand dimension')
        for disposition in dispositions:
            if disposition.get('new_dimension_id') not in new_dimensions or disposition.get('judgment') not in ('preserved', 'unresolved'):
                raise ValueError('Supersession must map each old dimension to a successor dimension, or leave it unresolved')
            text(disposition.get('rationale'), 'supersede.dimension.rationale')
        trace_authors = {t['actor'] for t in view['traces'] if t['event_id'] in (view['demands'][old]['trace_id'], view['demands'][new]['trace_id'])}
        if data['reviewer'] in trace_authors:
            raise ValueError('Dimension preservation needs a distinct declared reviewer')
        view['retirement_reviews'].append({'event_id': event['id'], **data,
            'old_dimensions': list(old_dimensions.values()), 'new_dimensions': list(new_dimensions.values()),
            'prior_comparison': view['comparisons'].get(old)})
        # This preserves an explicit reviewed mapping, not proof of semantic equivalence.
        view['retired'][old] = new
        current, seen = new, {old}
        while current in view['retired']:
            if current in seen:
                raise ValueError('Demand supersession cycle')
            seen.add(current)
            current = view['retired'][current]
    else:
        raise ValueError('Unknown event operation: ' + str(op))


def read_basis(view, read_ids):
    return sorted({digest({'source': {key: view['sources'][view['reads'][rid]['source_id']][key]
                                      for key in ('uri', 'path', 'revision', 'kind')},
                           'receipt': view['reads'][rid]['receipt']}) for rid in read_ids})


def demand_dimensions(demand):
    result = [{'id': 'learning', 'required_behavior': demand['learning_demand']},
              {'id': 'assessment', 'required_behavior': demand['assessment_demand']}]
    if demand['prerequisites']:
        result.insert(0, {'id': 'prerequisites', 'required_behavior': '; '.join(demand['prerequisites'])})
    known = {item['id'] for item in result}
    result.extend(item for item in demand.get('dimensions', []) if item['id'] not in known)
    return result


def receipt_current(root, receipt):
    try:
        actual = read_span(root, receipt['path'], receipt['start_line'], receipt['end_line'])
        return actual == receipt
    except (OSError, ValueError, UnicodeError):
        return False


def inspect(state, root):
    view = replay(state)
    seed, blockers, queue = state['seed'], [], []
    def block(code, identifier):
        blockers.append({'code': code, 'id': identifier})
    artifact_sha256 = None
    if 'artifact_path' in seed['scope']:
        try:
            artifact_sha256 = hashlib.sha256(local_file(root, seed['scope']['artifact_path']).read_bytes()).hexdigest()
        except (OSError, ValueError):
            block('artifact_unreadable', seed['scope']['artifact_path'])
        if artifact_sha256 != seed['scope']['artifact_sha256']:
            block('artifact_changed', seed['scope']['artifact_path'])
    stale_reads = {rid for rid, read in view['reads'].items() if not receipt_current(root, read['receipt'])}
    for rid in sorted(stale_reads):
        if view['reads'][rid]['source_id'] not in view['retired_sources']:
            block('stale_source_read', rid)
    latest_retirements = {r['old_demand_id']: r for r in view['retirement_reviews']}
    for retirement in latest_retirements.values():
        if any(item['judgment'] == 'unresolved' for item in retirement['dimension_dispositions']):
            block('supersession_unresolved', retirement['event_id'])
    for question in view['questions'].values():
        if question['resolved_by'] is None:
            block('uninvestigated_requirement', question['id'])
    frontier_report = []
    for fid, probe in view['frontier'].items():
        traces = [t for t in view['traces'] if t['frontier_id'] == fid]
        discovered = {source['id'] for search in view['searches'] if search['frontier_id'] == fid for source in search['candidates'] if source['id'] not in view['retired_sources']}
        source_key = lambda sid: digest({key: view['sources'][sid][key] for key in ('uri', 'path', 'revision', 'kind')})
        read_sources = {source_key(read['source_id']) for rid, read in view['reads'].items() if rid not in stale_reads}
        traced_sources = {source_key(view['reads'][rid]['source_id']) for trace in traces for rid in trace['read_ids'] if rid not in stale_reads}
        for sid in sorted(discovered):
            if source_key(sid) not in read_sources:
                block('discovered_source_unread', sid)
            if source_key(sid) not in traced_sources:
                block('discovered_source_untraced', sid)
        # Latest trace for each required kind applies; earlier failed/partial traces cannot be cherry-picked.
        missing = []
        for kind in probe['required_kinds']:
            relevant = [t for t in traces if any(view['sources'][view['reads'][rid]['source_id']]['kind'] == kind and view['reads'][rid]['source_id'] not in view['retired_sources'] for rid in t['read_ids'])]
            latest = relevant[-1] if relevant else None
            if latest is None or any(rid in stale_reads for rid in latest['read_ids']) or any(q['frontier_id'] == fid and q['resolved_by'] is None for q in view['questions'].values()):
                missing.append(kind)
        if missing:
            block('frontier_unresolved', fid)
        if not traces or not any(t['demands'] for t in traces):
            # A declaration that nothing applies cannot close the universe by itself.
            block('frontier_no_demands_requires_review', fid)
        frontier_report.append({'id': fid, 'question': probe['question'], 'missing_kinds': missing,
                                'trace_ids': [t['event_id'] for t in traces],
                                'uninvestigated': traces[-1]['uninvestigated'] if traces else ['Not investigated']})
    for did, demand in view['demands'].items():
        if did in view['retired']:
            continue
        comparison = view['comparisons'].get(did)
        reasons = []
        if any(rid in stale_reads for rid in demand['read_ids']):
            reasons.append('source_changed_retrace_required')
        if any(view['reads'][rid]['source_id'] in view['retired_sources'] for rid in demand['read_ids']):
            reasons.append('source_superseded_retrace_required')
        if comparison is None:
            reasons.append('comparison_required')
        else:
            if not receipt_current(root, comparison['lesson_receipt']):
                reasons.append('lesson_changed_review_required')
            for dimension in comparison.get('dimensions', []):
                if dimension['judgment'] != 'met':
                    reasons.append('dimension_' + dimension['id'] + '_' + dimension['judgment'])
                if not receipt_current(root, dimension['receipt']):
                    reasons.append('dimension_' + dimension['id'] + '_stale')
            if comparison['judgment'] in ('gap', 'uncertain'):
                reasons.append(comparison['judgment'])
            if comparison['judgment'] == 'deferred':
                if seed['scope']['readiness'] != 'scoped_foundation':
                    reasons.append('deferred_is_not_course_readiness')
                if not receipt_current(root, comparison['placement']['receipt']):
                    reasons.append('placement_changed_review_required')
        if reasons:
            block('demand_unresolved', did)
            queue.append({'demand_id': did, 'statement': demand['statement'], 'reasons': reasons,
                          'next_action': 'discover_read_retrace' if any('source' in r for r in reasons) else
                          'compare_actual_lesson' if comparison is None else 'research_or_refine_and_recompare',
                          'affected': sorted({did, demand['frontier_id'], seed['scope']['id']})})
    usage = {'events': len(state['events']), 'rounds': view['rounds'],
             'elapsed_minutes': view['elapsed_minutes'], 'no_progress': view['no_progress']}
    exhausted = [key for key in usage if usage[key] >= seed['policy']['max_' + key]]
    if exhausted:
        status, action = 'stopped', 'new_budget_requires_explicit_new_baseline'
    elif view['paused']:
        status, action = 'paused', 'resume_with_reason'
    elif blockers:
        status = 'needs_work'
        codes = {b['code'] for b in blockers}
        if 'uninvestigated_requirement' in codes:
            action = 'expand_frontier'
        elif codes & {'artifact_changed', 'artifact_unreadable'}:
            action = 'refresh_artifact_baseline'
        elif 'discovered_source_unread' in codes:
            action = 'read_discovered_sources'
        elif 'discovered_source_untraced' in codes:
            action = 'trace_source_requirements'
        elif 'frontier_unresolved' in codes:
            action = 'discover_original_sources'
        elif 'frontier_no_demands_requires_review' in codes:
            action = 'review_extraction_or_expand_frontier'
        elif 'supersession_unresolved' in codes:
            action = 'review_retired_dimension_mapping'
        else:
            action = queue[0]['next_action'] if queue else 'refresh_source_reads'
    else:
        status, action = 'recorded_ready', 'independent_aggregate_review'
    return {'schema_version': 1, 'authority': 'advisory_only', 'status': status,
            'ready_for_review': status == 'recorded_ready', 'synthetic': seed['synthetic'],
            'session_sha256': digest(state), 'seed_sha256': state['seed_sha256'],
            'scope': seed['scope'], 'artifact_sha256': artifact_sha256,
            'bounded_scope_condition': 'Only the declared, sampled frontier has been investigated; neither complete external coverage nor contest sufficiency is established.',
            'frontier': frontier_report, 'demands': list(view['demands'].values()),
            'comparisons': list(view['comparisons'].values()), 'retired_demands': view['retired'],
            'retired_sources': view['retired_sources'], 'retirement_reviews': view['retirement_reviews'], 'historical_stale_read_ids': sorted(stale_reads),
            'open_questions': [q for q in view['questions'].values() if q['resolved_by'] is None],
            'questions': list(view['questions'].values()), 'demand_aliases': view['demand_aliases'],
            'queue': queue, 'blockers': blockers, 'usage': usage, 'exhausted': exhausted,
            'next_action': action, 'search_history': view['searches'], 'limits': LIMITS}


def step(state, event, root):
    view = replay(state)
    text(event.get('id'), 'event.id')
    payload = {key: copy.deepcopy(event[key]) for key in ('id', 'op', 'data')}
    data = payload['data']
    if view['paused'] and payload['op'] not in ('resume', 'pause'):
        raise ValueError('Paused session requires an explicit resume event')
    # The CLI creates receipts from actual files; callers cannot inject a claimed read.
    if payload['op'] == 'read':
        source = view['sources'][data['source_id']]
        data['receipt'] = read_span(root, source['path'], data.pop('start_line'), data.pop('end_line'))
    elif payload['op'] == 'compare':
        data['lesson_receipt'] = read_span(root, state['seed']['scope']['lesson_path'], data.pop('start_line'), data.pop('end_line'))
        for dimension in data.get('dimensions', []):
            dimension['receipt'] = read_span(root, state['seed']['scope']['lesson_path'], dimension.pop('start_line'), dimension.pop('end_line'))
        if data.get('judgment') == 'deferred':
            placement = data['placement']
            placement['receipt'] = read_span(root, placement.pop('path'), placement.pop('start_line'), placement.pop('end_line'))
    content_key = digest({key: payload[key] for key in ('op', 'data')})
    for old in state['events']:
        if old['id'] == payload['id']:
            if old['op'] == payload['op'] and old['data'] == payload['data']:
                return copy.deepcopy(state)
            raise ValueError('Event id reused for different content')
        if payload['op'] == 'compare' and digest({key: old[key] for key in ('op', 'data')}) == content_key and view['comparisons'].get(view['demand_aliases'].get(data['demand_id'], data['demand_id']), {}).get('event_id') == old['id']:
            return copy.deepcopy(state)
    report = inspect(state, root)
    if report['exhausted']:
        raise ValueError('Finite budget exhausted; counters cannot be reset on resume')
    apply_event(view, payload, state['seed'])
    result = copy.deepcopy(state)
    previous = result['events'][-1]['sha256'] if result['events'] else result['seed_sha256']
    result['events'].append({**payload, 'previous_sha256': previous,
                             'sha256': digest({'previous_sha256': previous, **payload})})
    return result


def manifest(state):
    replay(state)
    return {'id': 'review:discovery', 'revision': VERSION, 'sha256': digest(state)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('init', 'step', 'report', 'next', 'manifest'))
    parser.add_argument('input', type=Path)
    parser.add_argument('--event', type=Path)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        value = load(args.input)
        if args.command == 'init':
            result = initialize(value)
        elif args.command == 'step':
            if args.event is None:
                parser.error('step requires --event')
            result = step(value, load(args.event), args.root)
        elif args.command == 'manifest':
            result = manifest(value)
        else:
            result = inspect(value, args.root)
            if args.command == 'next':
                result = {key: result[key] for key in ('authority', 'status', 'next_action', 'queue', 'usage', 'exhausted', 'limits')}
        print(json.dumps(result, sort_keys=True, ensure_ascii=True, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError, RecursionError, OverflowError) as exc:
        print(json.dumps({'authority': 'advisory_only', 'status': 'invalid', 'errors': [str(exc)]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
