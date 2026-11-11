#!/usr/bin/env python3
"""Read-only, deterministic workflow decisions; never executes recorded actions."""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1
DIGEST = re.compile(r'^[0-9a-f]{64}$')
MANIFEST_KEYS = ('id', 'revision', 'sha256')
MEASUREMENT_KEYS = ('rubric', 'evaluator', 'references', 'required_checks', 'finish_condition')
STATUSES = {'passed', 'failed', 'not_run'}


def _hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def _manifest(value):
    return None if value is None else {key: value[key] for key in MANIFEST_KEYS}


def _sorted_manifests(values):
    return sorted((_manifest(value) for value in values), key=lambda value: value['id'])


def measurement(state):
    """The frozen measurement harness, not an execution or permission object."""
    context = state['context']
    return {
        'rubric': _manifest(context['rubric']),
        'evaluator': _manifest(context['evaluator']),
        'references': _sorted_manifests(context['references']),
        'required_checks': sorted(context['required_checks']),
        'finish_condition': context['finish_condition'],
    }


def criteria_fingerprint(state):
    return _hash(measurement(state))


def _scope(state):
    return {key: state['scope'][key] for key in ('task_kind', 'lesson_production_allowed', 'recurring_allowed')}


def budget_fingerprint(state):
    return _hash({'scope': _scope(state), 'limits': {key: state['limits'][key] for key in
                 ('checkpoint_minutes', 'max_iterations', 'max_elapsed_minutes', 'max_no_progress')}})


def _record_ancestors(state):
    ancestors = {}
    for record in state['records']:
        parents = set(record['supersedes'])
        ancestors[record['id']] = parents.union(*(ancestors[parent] for parent in parents))
    return ancestors


def _active_records(state):
    replaced = {old for record in state['records'] for old in record['supersedes']}
    old_payloads = {}
    for record in state['records']:
        if record['id'] in replaced:
            old_payloads.setdefault(_hash(_record_payload(record)), set()).add(record['id'])
    ancestors = _record_ancestors(state)
    active = []
    for record in state['records']:
        if record['id'] in replaced:
            continue
        prior = old_payloads.get(_hash(_record_payload(record)), set())
        if not prior or ancestors[record['id']] & prior:
            active.append(record)
    return active


def _record_payload(record):
    return {
        'kind': record['kind'], 'text': record['text'],
        'source_refs': [{'source_id': sid, 'locator': locator} for sid, locator in
                        sorted({(ref['source_id'], ref['locator']) for ref in record['source_refs']})],
    }


def recall_records(state, query=''):
    """Active records only; exact payload deduplication, then AND substring search."""
    sources = {source['id']: source for source in state['sources']}
    seen, recalled = set(), []
    terms = query.casefold().split()
    for record in _active_records(state):
        key = _hash(_record_payload(record))
        if key in seen:
            continue
        seen.add(key)
        if not all(term in record['text'].casefold() for term in terms):
            continue
        recalled.append({
            **record,
            'source_details': [
                {**sources[ref['source_id']], 'locator': ref['locator']}
                for ref in record['source_refs']
            ],
        })
    return recalled


def context_fingerprint(state):
    """Bind the artifact, all input/harness versions, and active source-linked records."""
    context = state['context']
    active_payloads = {_hash(_record_payload(record)): _record_payload(record)
                       for record in _active_records(state)}
    source_ids = {ref['source_id'] for record in _active_records(state)
                  for ref in record['source_refs']}
    source_ids.update(reference['id'] for reference in context['references'])
    sources = sorted(({key: source[key] for key in (*MANIFEST_KEYS, 'uri')}
                      for source in state['sources'] if source['id'] in source_ids),
                     key=lambda source: source['id'])
    return _hash({
        'scope': _scope(state),
        'context': {
            **measurement(state),
            'inputs': _sorted_manifests(context['inputs']),
            'skills': _sorted_manifests(context['skills']),
            'artifact': _manifest(context['artifact']),
            'author': None if context['author'] is None else
                      {key: context['author'][key] for key in ('id', 'model_family')},
        },
        'records': [active_payloads[key] for key in sorted(active_payloads)],
        'sources': sources,
    })


def validate_state(state):
    """Validate shape and recorded reference integrity, never semantic truth."""
    errors, warnings = [], []
    # Reject values that stdlib JSON accepts but canonical UTF-8 JSON cannot encode.
    stack = [('state', state)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, str):
            try:
                value.encode('utf-8')
            except UnicodeEncodeError:
                errors.append(path + ': lone surrogate is not valid UTF-8 text')
        elif type(value) is float and not math.isfinite(value):
            errors.append(path + ': non-finite number is not permitted')
        elif isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    errors.append(path + ': object keys must be strings')
                    continue
                stack.append((path + '[key]', key))
                stack.append((f'{path}[{key!a}]', item))
        elif isinstance(value, list):
            stack.extend((f'{path}[{index}]', item) for index, item in enumerate(value))
        elif value is not None and type(value) not in (bool, int, float):
            errors.append(path + ': unsupported non-JSON value')
    if errors:
        return errors, warnings

    def obj(value, path):
        if not isinstance(value, dict):
            errors.append(f'{path}: must be an object')
            return {}
        return value

    def array(value, path):
        if not isinstance(value, list):
            errors.append(f'{path}: must be an array')
            return []
        return value

    def string(value, path, nullable=False):
        if nullable and value is None:
            return True
        valid = isinstance(value, str) and bool(value.strip())
        if not valid:
            errors.append(f'{path}: must be a nonempty string')
        return valid

    def digest(value, path, nullable=False):
        if nullable and value is None:
            return
        if not isinstance(value, str) or not DIGEST.fullmatch(value):
            errors.append(f'{path}: must be a lowercase SHA256 digest')

    def boolean(value, path):
        if type(value) is not bool:
            errors.append(f'{path}: must be a boolean')

    def integer(value, path, minimum, nullable=False):
        if nullable and value is None:
            return
        if type(value) is not int or value < minimum:
            errors.append(f'{path}: must be an integer >= {minimum}')

    def manifest(value, path, nullable=False):
        if nullable and value is None:
            return
        value = obj(value, path)
        string(value.get('id'), path + '.id')
        string(value.get('revision'), path + '.revision')
        digest(value.get('sha256'), path + '.sha256')

    def manifest_list(value, path):
        values, ids = array(value, path), set()
        for index, item in enumerate(values):
            manifest(item, f'{path}[{index}]')
            if isinstance(item, dict) and isinstance(item.get('id'), str):
                if item['id'] in ids:
                    errors.append(f'{path}: duplicate manifest id {item["id"]}')
                ids.add(item['id'])
        return values

    def string_list(value, path):
        values = array(value, path)
        seen = set()
        for index, item in enumerate(values):
            if string(item, f'{path}[{index}]'):
                if item in seen:
                    errors.append(f'{path}: duplicate value {item}')
                seen.add(item)
        return values

    def required(value, keys, path):
        if isinstance(value, dict):
            for key in keys:
                if key not in value:
                    errors.append(f'{path}.{key}: required field is missing')

    if not isinstance(state, dict):
        return ['state: must be an object'], []
    required(state, ('schema_version', 'synthetic', 'scope', 'agreement', 'context', 'frozen',
                     'limits', 'usage', 'stop', 'sources', 'records', 'reviews', 'history'), 'state')
    if type(state.get('schema_version')) is not int or state.get('schema_version') != SCHEMA_VERSION:
        errors.append('schema_version: must be 1')
    boolean(state.get('synthetic'), 'synthetic')
    scope = obj(state.get('scope'), 'scope')
    if scope.get('task_kind') not in ('design', 'lesson_production', 'recurring'):
        errors.append('scope.task_kind: unknown task kind')
    for key in ('lesson_production_allowed', 'recurring_allowed'):
        boolean(scope.get(key), 'scope.' + key)
        if scope.get(key) is True:
            warnings.append(f'scope.{key} is a recorded claim, not an execution capability or authenticated permission')
    agreement = obj(state.get('agreement'), 'agreement')
    required(agreement, ('operator_agreed', 'operator_id', 'criteria_agreed', 'criteria_fingerprint', 'budget_fingerprint'), 'agreement')
    for key in ('operator_agreed', 'criteria_agreed'):
        boolean(agreement.get(key), 'agreement.' + key)
    string(agreement.get('operator_id'), 'agreement.operator_id', nullable=True)
    for key in ('criteria_fingerprint', 'budget_fingerprint'):
        digest(agreement.get(key), 'agreement.' + key, nullable=True)
    context = obj(state.get('context'), 'context')
    required(context, ('inputs', 'skills', 'references', 'artifact', 'rubric', 'evaluator',
                       'required_checks', 'finish_condition', 'author'), 'context')
    for key in ('inputs', 'skills', 'references'):
        manifest_list(context.get(key), 'context.' + key)
    for key in ('artifact', 'rubric', 'evaluator'):
        manifest(context.get(key), 'context.' + key, nullable=True)
    string_list(context.get('required_checks'), 'context.required_checks')
    string(context.get('finish_condition'), 'context.finish_condition', nullable=True)
    if context.get('author') is not None:
        author = obj(context.get('author'), 'context.author')
        string(author.get('id'), 'context.author.id')
        string(author.get('model_family'), 'context.author.model_family')
    if state.get('frozen') is not None:
        frozen = obj(state.get('frozen'), 'frozen')
        for key in ('rubric', 'evaluator'):
            manifest(frozen.get(key), 'frozen.' + key)
        manifest_list(frozen.get('references'), 'frozen.references')
        string_list(frozen.get('required_checks'), 'frozen.required_checks')
        string(frozen.get('finish_condition'), 'frozen.finish_condition')
    limits = obj(state.get('limits'), 'limits')
    required(limits, ('checkpoint_minutes', 'max_iterations', 'max_elapsed_minutes', 'max_no_progress'), 'limits')
    integer(limits.get('checkpoint_minutes'), 'limits.checkpoint_minutes', 1)
    for key in ('max_iterations', 'max_elapsed_minutes', 'max_no_progress'):
        integer(limits.get(key), 'limits.' + key, 1, nullable=True)
    usage = obj(state.get('usage'), 'usage')
    for key in ('iterations_used', 'elapsed_minutes', 'no_progress_count', 'minutes_since_checkpoint'):
        integer(usage.get(key), 'usage.' + key, 0)
    stop = obj(state.get('stop'), 'stop')
    required(stop, ('requested', 'goal_claimed', 'reason'), 'stop')
    boolean(stop.get('requested'), 'stop.requested')
    boolean(stop.get('goal_claimed'), 'stop.goal_claimed')
    string(stop.get('reason'), 'stop.reason', nullable=True)
    if stop.get('requested') is True and not stop.get('reason'):
        errors.append('stop.reason: required for an explicit stop')

    source_ids, source_by_id = set(), {}
    for index, source in enumerate(array(state.get('sources'), 'sources')):
        path = f'sources[{index}]'
        source = obj(source, path)
        manifest(source, path)
        string(source.get('uri'), path + '.uri')
        sid = source.get('id')
        if isinstance(sid, str):
            if sid in source_ids:
                errors.append(f'{path}: duplicate source id {sid}')
            source_ids.add(sid)
            source_by_id[sid] = source
    for reference in context.get('references', []) if isinstance(context.get('references'), list) else []:
        if not isinstance(reference, dict) or not isinstance(reference.get('id'), str):
            continue
        source = source_by_id.get(reference['id'])
        if source is None:
            errors.append(f'context.references: unknown source {reference["id"]}')
        elif any(source.get(key) != reference.get(key) for key in MANIFEST_KEYS):
            errors.append(f'context.references: source version mismatch {reference["id"]}')

    record_ids, superseded, payloads = set(), set(), set()
    for index, record in enumerate(array(state.get('records'), 'records')):
        path = f'records[{index}]'
        record = obj(record, path)
        rid = record.get('id')
        string(rid, path + '.id')
        if isinstance(rid, str) and rid in record_ids:
            errors.append(f'{path}: duplicate record id {rid}')
        if record.get('kind') not in ('evidence', 'decision', 'observation', 'skill'):
            errors.append(path + '.kind: invalid kind')
        string(record.get('text'), path + '.text')
        string(record.get('created_at'), path + '.created_at')
        refs = array(record.get('source_refs'), path + '.source_refs')
        if not refs:
            errors.append(path + '.source_refs: at least one source is required')
        for ref_index, ref in enumerate(refs):
            refpath = f'{path}.source_refs[{ref_index}]'
            ref = obj(ref, refpath)
            sid = ref.get('source_id')
            if not isinstance(sid, str) or sid not in source_ids:
                errors.append(refpath + '.source_id: unknown source')
            string(ref.get('locator'), refpath + '.locator')
        for old in string_list(record.get('supersedes'), path + '.supersedes'):
            if not isinstance(old, str):
                continue
            if old not in record_ids:
                errors.append(path + '.supersedes: predecessor must be an earlier record')
            if old in superseded:
                errors.append(path + '.supersedes: branching replacement is invalid in v1; keep alternatives unsuperseding until one resolution')
            superseded.add(old)
        if isinstance(rid, str):
            record_ids.add(rid)
        if not errors:
            payload = _hash(_record_payload(record))
            if payload in payloads:
                warnings.append(f'{path}: exact duplicate payload; recall and context fingerprint deduplicate it')
            payloads.add(payload)

    review_ids = set()
    for index, review in enumerate(array(state.get('reviews'), 'reviews')):
        path = f'reviews[{index}]'
        review = obj(review, path)
        rid = review.get('id')
        string(rid, path + '.id')
        if isinstance(rid, str):
            if rid in review_ids:
                errors.append(path + ': duplicate review id')
            review_ids.add(rid)
        digest(review.get('context_fingerprint'), path + '.context_fingerprint')
        string(review.get('author_id'), path + '.author_id')
        reviewer = obj(review.get('reviewer'), path + '.reviewer')
        string(reviewer.get('id'), path + '.reviewer.id')
        string(reviewer.get('model_family'), path + '.reviewer.model_family')
        string(review.get('reason'), path + '.reason')
        if review.get('conclusion') not in ('accepted', 'changes_requested', 'abstain'):
            errors.append(path + '.conclusion: invalid conclusion')
        check_ids = set()
        for check_index, check in enumerate(array(review.get('checks'), path + '.checks')):
            checkpath = f'{path}.checks[{check_index}]'
            check = obj(check, checkpath)
            cid = check.get('id')
            string(cid, checkpath + '.id')
            if isinstance(cid, str):
                if cid in check_ids:
                    errors.append(checkpath + ': duplicate check id')
                check_ids.add(cid)
            if check.get('status') not in ('passed', 'failed', 'not_run'):
                errors.append(checkpath + '.status: invalid status')
            for evidence_id in string_list(check.get('evidence_record_ids'), checkpath + '.evidence_record_ids'):
                if not isinstance(evidence_id, str) or evidence_id not in record_ids:
                    errors.append(checkpath + '.evidence_record_ids: unknown record')
    history_ids = set()
    for index, receipt in enumerate(array(state.get('history'), 'history')):
        path = f'history[{index}]'
        receipt = obj(receipt, path)
        hid = receipt.get('id')
        string(hid, path + '.id')
        if isinstance(hid, str):
            if hid in history_ids:
                errors.append(path + ': duplicate receipt id')
            history_ids.add(hid)
        digest(receipt.get('context_fingerprint'), path + '.context_fingerprint')
        if receipt.get('outcome') not in ('accepted', 'rejected', 'no_progress'):
            errors.append(path + '.outcome: invalid completed-attempt outcome')
        string(receipt.get('reason'), path + '.reason')
    if not errors:
        ancestors = _record_ancestors(state)
        by_id = {record['id']: record for record in state['records']}
        retired = {}
        for record in state['records']:
            for old in record['supersedes']:
                retired.setdefault(_hash(_record_payload(by_id[old])), set()).add(old)
            prior = retired.get(_hash(_record_payload(record)), set())
            if record['supersedes'] and prior and not ancestors[record['id']] & prior:
                errors.append(f'record {record["id"]}: a reversion must supersede its own correction chain')
    return errors, warnings


def _verification(state, fingerprint):
    reviews = [review for review in state['reviews'] if review['context_fingerprint'] == fingerprint]
    if not reviews:
        return {'passed': False, 'reason': 'stale_verification' if state['reviews'] else 'verification_required',
                'checks': [], 'warnings': []}
    review = reviews[-1]
    author = state['context']['author']
    warnings = []
    if review['reviewer']['model_family'] == author['model_family']:
        warnings.append('Reviewer reports the same model family; distinct identity does not establish independent reasoning.')
    independent = review['author_id'] == author['id'] and review['reviewer']['id'] != author['id']
    active_records = _active_records(state)
    active_ids = {record['id'] for record in active_records}
    evidence_ids = {record['id'] for record in active_records if record['kind'] == 'evidence'}
    reported = {check['id']: check for check in review['checks']}
    checks = []
    for cid in state['context']['required_checks']:
        check = reported.get(cid)
        status = check['status'] if check else 'not_run'
        if status == 'passed':
            if not check['evidence_record_ids']:
                status = 'unsupported'
            elif any(eid not in active_ids for eid in check['evidence_record_ids']):
                status = 'stale'
            elif any(eid not in evidence_ids for eid in check['evidence_record_ids']):
                status = 'unsupported'
        checks.append({'id': cid, 'status': status})
    passed = independent and review['conclusion'] == 'accepted' and all(check['status'] == 'passed' for check in checks)
    reason = ('reviewer_not_independent' if not independent else
              'review_not_accepted' if review['conclusion'] != 'accepted' else
              'checks_not_passed' if not passed else 'recorded_checks_passed')
    return {'passed': passed, 'reason': reason, 'review_id': review['id'], 'checks': checks, 'warnings': warnings}


def decide(state, quality_report=None):
    errors, warnings = validate_state(state)
    result = {'status': 'blocked', 'reason': 'invalid_state', 'authority': 'advisory_only',
              'synthetic': state.get('synthetic') if isinstance(state, dict) and type(state.get('synthetic')) is bool else None,
              'errors': errors, 'warnings': warnings}
    if errors:
        return result
    fingerprint = context_fingerprint(state)
    result['context_fingerprint'] = fingerprint

    def finish(status, reason):
        return {**result, 'status': status, 'reason': reason}

    if state['stop']['requested']:
        result['operator_reason'] = state['stop']['reason']
        return finish('stop', 'operator_stop')
    agreement, context = state['agreement'], state['context']
    if not agreement['operator_agreed'] or not agreement['operator_id']:
        return finish('pause', 'operator_agreement_required')
    if not agreement['criteria_agreed']:
        return finish('pause', 'criteria_agreement_required')
    scope = state['scope']
    if scope['task_kind'] == 'lesson_production' and not scope['lesson_production_allowed']:
        return finish('pause', 'lesson_production_not_authorized')
    if scope['task_kind'] == 'recurring' and not scope['recurring_allowed']:
        return finish('pause', 'recurring_not_authorized')
    if (not context['inputs'] or not context['skills'] or not context['required_checks']
            or any(context[key] is None for key in ('artifact', 'rubric', 'evaluator', 'author', 'finish_condition'))):
        return finish('pause', 'context_unconfigured')
    if state['frozen'] is None:
        return finish('pause', 'baseline_required')
    frozen = {
        'rubric': _manifest(state['frozen']['rubric']),
        'evaluator': _manifest(state['frozen']['evaluator']),
        'references': _sorted_manifests(state['frozen']['references']),
        'required_checks': sorted(state['frozen']['required_checks']),
        'finish_condition': state['frozen']['finish_condition'],
    }
    if frozen != measurement(state):
        return finish('pause', 'baseline_change_required')
    if agreement['criteria_fingerprint'] != criteria_fingerprint(state):
        return finish('pause', 'criteria_agreement_stale')
    limits, usage = state['limits'], state['usage']
    if any(limits[key] is None for key in ('max_iterations', 'max_elapsed_minutes', 'max_no_progress')):
        return finish('pause', 'budget_unset')
    if agreement['budget_fingerprint'] != budget_fingerprint(state):
        return finish('pause', 'budget_agreement_required')
    # Receipts provide a conservative lower bound on caller-reported counters.
    trailing_no_progress = 0
    for receipt in reversed(state['history']):
        if receipt['outcome'] == 'accepted':
            break
        trailing_no_progress += 1
    usage = {**usage, 'iterations_used': max(usage['iterations_used'], len(state['history'])),
             'no_progress_count': max(usage['no_progress_count'], trailing_no_progress)}
    for used, maximum, reason in (
            ('iterations_used', 'max_iterations', 'iteration_budget_exhausted'),
            ('elapsed_minutes', 'max_elapsed_minutes', 'elapsed_budget_exhausted'),
            ('no_progress_count', 'max_no_progress', 'no_progress_limit')):
        if usage[used] >= limits[maximum]:
            return finish('stop', reason)
    if usage['minutes_since_checkpoint'] >= limits['checkpoint_minutes']:
        return finish('pause', 'checkpoint_due')
    if scope['task_kind'] != 'design' or quality_report is not None:
        if quality_report is None:
            return finish('pause', 'quality_assessment_required')
        required = {'schema_version', 'authority', 'synthetic', 'revision', 'bundle_sha256',
                    'artifact_sha256', 'specification_sha256', 'specification_revision',
                    'evaluator_sha256', 'ready_for_review', 'checks'}
        if not isinstance(quality_report, dict) or not required <= quality_report.keys():
            return finish('blocked', 'invalid_quality_report')
        result['quality_assessment'] = quality_report
        if quality_report['synthetic'] and not state['synthetic']:
            return finish('blocked', 'synthetic_quality_cannot_validate_real_work')
        if quality_report['artifact_sha256'] != context['artifact']['sha256']:
            return finish('blocked', 'quality_artifact_mismatch')
        required_inputs = [
            {'id': 'quality:bundle', 'revision': quality_report['revision'], 'sha256': quality_report['bundle_sha256']},
            {'id': 'quality:criteria', 'revision': quality_report['specification_revision'], 'sha256': quality_report['specification_sha256']},
            {'id': 'quality:evaluator', 'revision': 'quality-v1', 'sha256': quality_report['evaluator_sha256']},
        ]
        bound_inputs = [_manifest(item) for item in context['inputs']]
        if any(item not in bound_inputs for item in required_inputs):
            return finish('blocked', 'quality_context_not_bound')
        checks = quality_report['checks']
        if (quality_report['ready_for_review'] is not True or not isinstance(checks, list) or
                {item.get('id') for item in checks if isinstance(item, dict)} !=
                {'K' + str(n).zfill(2) for n in range(1, 17)} or len(checks) != 16 or
                any(not isinstance(item, dict) or item.get('status') != 'passed' for item in checks)):
            return finish('blocked', 'quality_checks_not_passed')
    verification = _verification(state, fingerprint)
    result['verification'] = verification
    result['warnings'] = warnings + verification['warnings']
    if state['stop']['goal_claimed'] and verification['passed']:
        return finish('stop', 'verified_completion_claim')
    if not verification['passed']:
        return finish('blocked', verification['reason'])
    if any(receipt['context_fingerprint'] == fingerprint for receipt in state['history']):
        return finish('noop', 'no_new_evidence')
    return finish('continue', 'verified_candidate_within_budget')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('validate', 'decide', 'fingerprint', 'recall'))
    parser.add_argument('state', type=Path)
    parser.add_argument('--query', default='', help='AND substring terms for recall only')
    parser.add_argument('--quality', type=Path, help='Quality bundle for decide; required for lesson/recurring scope')
    args = parser.parse_args(argv)
    if args.quality and args.command != 'decide':
        parser.error('--quality applies only to decide')
    if args.query and args.command != 'recall':
        parser.error('--query applies only to recall')
    try:
        state = json.loads(args.state.read_text(encoding='utf-8'),
                           parse_constant=lambda token: (_ for _ in ()).throw(ValueError('non-finite JSON number: ' + token)))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        print(json.dumps({'status': 'blocked', 'reason': 'unreadable_state', 'authority': 'advisory_only', 'errors': [str(exc)]}))
        return 2
    errors, warnings = validate_state(state)
    if args.command == 'decide':
        quality_report = None
        if args.quality and not errors:
            import quality
            try:
                quality_report = quality.evaluate(quality.load(args.quality))
            except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError) as exc:
                print(json.dumps({'status': 'blocked', 'reason': 'invalid_quality_input', 'authority': 'advisory_only',
                                  'errors': [ascii(str(exc))]}))
                return 2
        output = decide(state, quality_report)
    else:
        output = {'status': 'invalid' if errors else 'valid', 'reason': 'invalid_state' if errors else 'structural_checks_only',
                  'authority': 'advisory_only', 'errors': errors, 'warnings': warnings,
                  'synthetic': state.get('synthetic') if isinstance(state, dict) and type(state.get('synthetic')) is bool else None}
        if not errors and args.command == 'fingerprint':
            output.update(context_fingerprint=context_fingerprint(state), criteria_fingerprint=criteria_fingerprint(state),
                          budget_fingerprint=budget_fingerprint(state))
        elif not errors and args.command == 'recall':
            output['records'] = recall_records(state, args.query)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
