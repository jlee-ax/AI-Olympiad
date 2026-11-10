#!/usr/bin/env python3
"""Inspect an explicitly recorded contest-depth evidence bundle; do not verify it."""

import argparse
from datetime import date
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


LIMITATIONS = [
    'Recorded observations are advisory declarations, not an automated assessment of lesson meaning or problem difficulty.',
    'The tool does not open sources or verify their official status, quotations, locations, truth, or currentness.',
    'Artifact paths and declared SHA-256 values are not read or verified against file bytes.',
    'Reviewer identity and independence are reported declarations and are not authenticated.',
    'Assessment-format counts are recorded observations; they are not extracted from the lesson.',
    'It does not establish learner achievement, equivalence to middle-school past problems, or completeness of competition coverage.',
    'This report is independent of K01–K16 and does not change any earlier quality evaluation.',
    'Only the two pinned KOAI 2026 example URLs have a fixed metadata consistency check; it does not fetch or authenticate them.',
]
MISSING = object()
PRIORITY = {'high': 0, 'medium': 1, 'low': 2}
KNOWN_EXAMPLE_PATHS = {
    '/files/36',
    '/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf',
}
KNOWN_HIGH_SCHOOL_TARGETS = {'high_school', 'high school', '고등부', '고등부 기준'}
KNOWN_MIDDLE_SCHOOL_TARGETS = {'middle_school', 'middle school', '중등부', '중등부 기준'}


class Inspection:
    def __init__(self):
        self.findings = []
        self.errors = []

    def uncertain(self, path, code, message):
        self.findings.append({'status': 'uncertain', 'path': path, 'code': code, 'message': message})

    def gap(self, path, code, message):
        self.findings.append({'status': 'gap', 'path': path, 'code': code, 'message': message})

    def error(self, path, code, message):
        self.errors.append({'path': path, 'code': code, 'message': message})

    def checkpoint(self):
        return len(self.findings), len(self.errors)

    def changed(self, checkpoint):
        return checkpoint != self.checkpoint()

    def obj(self, value, path):
        if value is MISSING or value is None:
            self.uncertain(path, 'missing', 'An object is required.')
            return {}
        if not isinstance(value, dict):
            self.error(path, 'invalid_type', 'Expected an object.')
            return {}
        return value

    def array(self, value, path, nonempty=False):
        if value is MISSING or value is None:
            self.uncertain(path, 'missing', 'An array is required.')
            return []
        if not isinstance(value, list):
            self.error(path, 'invalid_type', 'Expected an array.')
            return []
        if nonempty and not value:
            self.uncertain(path, 'empty', 'At least one item is required.')
        return value

    def string(self, value, path, allow_empty=False):
        if value is MISSING or value is None:
            self.uncertain(path, 'missing', 'A string is required.')
            return ''
        if not isinstance(value, str):
            self.error(path, 'invalid_type', 'Expected a string.')
            return ''
        if not value.strip() and not allow_empty:
            self.uncertain(path, 'empty', 'A nonempty string is required.')
        return value.strip()

    def strings(self, value, path, nonempty=True):
        return [self.string(item, f'{path}[{i}]') for i, item in
                enumerate(self.array(value, path, nonempty=nonempty))]

    def integer(self, value, path, minimum, maximum):
        if value is MISSING or value is None:
            self.uncertain(path, 'missing', 'An integer is required.')
            return None
        if type(value) is not int:
            self.error(path, 'invalid_type', 'Expected an integer, not a boolean or decimal.')
            return None
        if value < minimum or value > maximum:
            self.error(path, 'out_of_range', f'Expected an integer from {minimum} through {maximum}.')
            return None
        return value

    def boolean(self, value, path):
        if value is MISSING or value is None:
            self.uncertain(path, 'missing', 'A boolean is required.')
            return None
        if type(value) is not bool:
            self.error(path, 'invalid_type', 'Expected a boolean.')
            return None
        return value

    def choice(self, value, path, choices):
        text = self.string(value, path)
        if text and text not in choices:
            self.error(path, 'invalid_value', 'Expected one of: ' + ', '.join(sorted(choices)) + '.')
            return None
        return text or None


def is_known_2026_example(url):
    try:
        parts = urlsplit(url)
        return (parts.scheme in ('http', 'https') and parts.hostname in ('kitpa.org', 'www.kitpa.org')
                and unquote(parts.path).rstrip('/') in KNOWN_EXAMPLE_PATHS)
    except ValueError:
        return False


def inspect_sources(check, bundle):
    catalogs = {'scope_sources': {}, 'problem_sources': {}}
    all_ids = set()
    for category in catalogs:
        entries = check.array(bundle.get(category, MISSING), category, nonempty=True)
        for i, raw in enumerate(entries):
            path = f'{category}[{i}]'
            start = check.checkpoint()
            item = check.obj(raw, path)
            sid = check.string(item.get('id', MISSING), path + '.id')
            if sid:
                if sid in all_ids:
                    check.error(path + '.id', 'duplicate_id', 'Source IDs must be unique across both catalogs.')
                all_ids.add(sid)
            for field in ('title', 'locator', 'verification_evidence', 'version', 'read_extent'):
                check.string(item.get(field, MISSING), path + '.' + field)
            accessed = check.string(item.get('accessed_at', MISSING), path + '.accessed_at')
            if accessed:
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', accessed):
                        raise ValueError('expected YYYY-MM-DD')
                    date.fromisoformat(accessed)
                except ValueError:
                    check.error(path + '.accessed_at', 'invalid_date', 'Expected a real date in YYYY-MM-DD format.')
            url = check.string(item.get('url', MISSING), path + '.url')
            if url:
                try:
                    parts = urlsplit(url)
                    if parts.scheme not in ('http', 'https') or not parts.hostname or any(c.isspace() for c in url):
                        raise ValueError('not an HTTP(S) URL')
                except ValueError:
                    check.error(path + '.url', 'invalid_url', 'Expected an HTTP(S) URL with a host.')
            verification = check.choice(item.get('verification', MISSING), path + '.verification',
                                        {'verified_official', 'unconfirmed'})
            if verification == 'unconfirmed':
                check.uncertain(path + '.verification', 'unconfirmed_source',
                                'The recorder has not confirmed this source as official.')
            if category == 'problem_sources':
                kind = check.choice(item.get('kind', MISSING), path + '.kind', {'past_problem', 'example'})
                check.string(item.get('problem', MISSING), path + '.problem')
                year = check.integer(item.get('year', MISSING), path + '.year', 1, 9999)
                target = check.string(item.get('target', MISSING), path + '.target')
                if is_known_2026_example(url):
                    if kind is not None and kind != 'example':
                        check.error(path + '.kind', 'known_source_conflict',
                                    'This pinned source is a 2026 example, not a past problem.')
                    if year is not None and year != 2026:
                        check.error(path + '.year', 'known_source_conflict',
                                    'This pinned example identifies the year 2026.')
                    normalized = target.casefold()
                    if normalized in KNOWN_MIDDLE_SCHOOL_TARGETS:
                        check.error(path + '.target', 'known_source_conflict',
                                    'This pinned example is written to a high-school standard.')
                    elif normalized and normalized not in KNOWN_HIGH_SCHOOL_TARGETS:
                        check.uncertain(path + '.target', 'known_source_target_unresolved',
                                        'For this source, record high_school or 고등부 as the source target; distinguish its classroom use separately.')
            if sid:
                # Keep an ambiguous ID unusable, rather than silently selecting a duplicate.
                usable = not check.changed(start) and sum(1 for catalog in catalogs.values() if sid in catalog) == 0
                if not usable and any(sid in catalog for catalog in catalogs.values()):
                    for catalog in catalogs.values():
                        if sid in catalog:
                            catalog[sid] = False
                catalogs[category][sid] = usable
    return catalogs


def inspect_target(check, bundle):
    start = check.checkpoint()
    target = check.obj(bundle.get('target', MISSING), 'target')
    for field in ('artifact', 'artifact_revision'):
        check.string(target.get(field, MISSING), 'target.' + field)
    digest = check.string(target.get('artifact_sha256', MISSING), 'target.artifact_sha256')
    if digest and not re.fullmatch(r'[0-9a-f]{64}', digest):
        check.error('target.artifact_sha256', 'invalid_digest', 'Expected 64 lowercase hexadecimal characters.')
    check.integer(target.get('competition_year', MISSING), 'target.competition_year', 1, 9999)
    check.choice(target.get('division', MISSING), 'target.division', {'middle_school', 'high_school'})
    class_minutes = check.integer(target.get('class_minutes', MISSING), 'target.class_minutes', 1, 1000000)
    check.strings(target.get('baseline_assumptions', MISSING), 'target.baseline_assumptions')
    weeks = []
    for i, raw in enumerate(check.array(target.get('weeks', MISSING), 'target.weeks', nonempty=True)):
        week = check.integer(raw, f'target.weeks[{i}]', 1, 10)
        if week is not None:
            if week in weeks:
                check.error(f'target.weeks[{i}]', 'duplicate_week', 'Each target week must occur once.')
            else:
                weeks.append(week)
    goals = {}
    for i, raw in enumerate(check.array(target.get('goals', MISSING), 'target.goals', nonempty=True)):
        path = f'target.goals[{i}]'
        item = check.obj(raw, path)
        goal_id = check.string(item.get('id', MISSING), path + '.id')
        week = check.integer(item.get('week', MISSING), path + '.week', 1, 10)
        check.string(item.get('description', MISSING), path + '.description')
        if week is not None and weeks and week not in weeks:
            check.error(path + '.week', 'outside_target', 'The goal week must belong to target.weeks.')
        if goal_id:
            if goal_id in goals:
                check.error(path + '.id', 'duplicate_id', 'Goal IDs must be unique.')
            goals[goal_id] = week
    return weeks, goals, class_minutes, not check.changed(start)


def inspect_format_counts(check, value, path):
    counts = check.obj(value, path)
    result = {}
    for kind, raw in counts.items():
        if not isinstance(kind, str) or not kind.strip():
            check.error(path, 'invalid_kind', 'Assessment kind names must be nonempty strings.')
            continue
        result[kind] = check.integer(raw, path + '.' + kind, 0, 1000000)
    return result


def inspect_assessment_format(check, item, path, week):
    start = check.checkpoint()
    req_path = path + '.required_assessment_format'
    obs_path = path + '.observed_assessment_format'
    required = check.obj(item.get('required_assessment_format', MISSING), req_path)
    observed = check.obj(item.get('observed_assessment_format', MISSING), obs_path)
    req_status = check.choice(required.get('status', MISSING), req_path + '.status', {'specified', 'none', 'uncertain'})
    obs_status = check.choice(observed.get('status', MISSING), obs_path + '.status',
                              {'observed', 'not_applicable', 'uncertain'})
    req_counts = inspect_format_counts(check, required.get('counts', MISSING), req_path + '.counts')
    obs_counts = inspect_format_counts(check, observed.get('counts', MISSING), obs_path + '.counts')
    check.string(required.get('locator', MISSING), req_path + '.locator')
    check.string(observed.get('locator', MISSING), obs_path + '.locator')
    if req_status == 'uncertain':
        check.uncertain(req_path, 'format_requirement_uncertain', 'The required assessment format is unconfirmed.')
    if obs_status == 'uncertain':
        check.uncertain(obs_path, 'format_observation_uncertain', 'The observed assessment format is unconfirmed.')
    if req_status == 'specified' and not req_counts:
        check.uncertain(req_path + '.counts', 'empty', 'Specify at least one assessment kind and count.')
    if req_status == 'none' and req_counts:
        check.error(req_path + '.counts', 'format_contradiction', 'No format requirement cannot also specify counts.')
    if obs_status == 'not_applicable' and obs_counts:
        check.error(obs_path + '.counts', 'format_contradiction', 'Not-applicable observations cannot also specify counts.')
    if req_status == 'specified' and obs_status == 'not_applicable':
        check.uncertain(obs_path, 'format_observation_missing', 'A specified format requires observed counts.')
    if req_status != 'none' and obs_status == 'not_applicable':
        # A missing or uncertain requirement cannot establish that observation is unnecessary.
        if req_status != 'specified':
            check.uncertain(obs_path, 'format_applicability_unknown', 'It is unknown whether format observations are needed.')
    kinds, generated = [], []
    if req_status == 'specified' and obs_status == 'observed':
        for kind in sorted(set(obs_counts) - set(req_counts)):
            if obs_counts[kind]:
                check.uncertain(obs_path + '.counts.' + kind, 'additional_format_kind',
                                f'Observed kind {kind!r} has no specified requirement; its acceptability is unassessed.')
                kinds.append({'kind': kind, 'required': None, 'observed': obs_counts[kind],
                              'difference': None, 'status': 'uncertain'})
        for kind, expected in sorted(req_counts.items()):
            if kind not in obs_counts:
                check.uncertain(obs_path + '.counts', 'missing_format_kind',
                                f'Observed count for {kind!r} is missing; record zero explicitly if none were found.')
                kinds.append({'kind': kind, 'required': expected, 'observed': None, 'difference': None,
                              'status': 'uncertain'})
                continue
            actual = obs_counts[kind]
            if expected is None or actual is None:
                kinds.append({'kind': kind, 'required': expected, 'observed': actual, 'difference': None,
                              'status': 'uncertain'})
                continue
            difference = actual - expected
            kinds.append({'kind': kind, 'required': expected, 'observed': actual, 'difference': difference,
                          'status': 'gap' if difference else 'matched'})
            if difference:
                check.gap(obs_path + '.counts.' + kind, 'assessment_count_mismatch',
                          f'Recorded {kind} count is {actual}; the requirement is {expected}.')
                generated.append({'id': f'assessment:week:{week}:{kind}', 'origin': 'assessment_format',
                                  'week': week, 'priority': None,
                                  'difference': f'Recorded {kind} count is {actual}; required count is {expected}.',
                                  'rationale': 'Arithmetic comparison of declared counts only.'})
    if generated:
        status = 'gap'
    elif check.changed(start):
        status = 'uncertain'
    elif req_status == 'none':
        status = 'not_required'
    else:
        status = 'matched'
    return {'week': week, 'status': status, 'kinds': kinds}, generated


def inspect_times(check, bundle, weeks, class_minutes):
    entries = check.array(bundle.get('time_allocations', MISSING), 'time_allocations', nonempty=True)
    by_week = {}
    generated_gaps, formats = [], []
    for i, raw in enumerate(entries):
        path = f'time_allocations[{i}]'
        start = check.checkpoint()
        item = check.obj(raw, path)
        week = check.integer(item.get('week', MISSING), path + '.week', 1, 10)
        inside = check.integer(item.get('in_class_minutes', MISSING), path + '.in_class_minutes', 0, 1000000)
        check.integer(item.get('outside_class_minutes', MISSING), path + '.outside_class_minutes', 0, 1000000)
        check.string(item.get('locator', MISSING), path + '.locator')
        if week is not None and week not in weeks and weeks:
            check.error(path + '.week', 'outside_target', 'The allocation week must belong to target.weeks.')
        if inside is not None and class_minutes is not None and inside != class_minutes:
            check.gap(path + '.in_class_minutes', 'class_time_mismatch', 'Recorded class time does not match target.class_minutes.')
            generated_gaps.append({'id': f'time:week:{week}' if week is not None else path,
                                   'origin': 'time_allocation', 'week': week, 'priority': None,
                                   'difference': f'Recorded class time is {inside} minutes, expected {class_minutes}.',
                                   'rationale': 'Arithmetic comparison of the recorded number only.'})
        time_complete = not check.changed(start)
        format_result, format_gaps = inspect_assessment_format(check, item, path, week)
        formats.append(format_result)
        generated_gaps.extend(format_gaps)
        if week is not None:
            if week in by_week:
                check.error(path + '.week', 'duplicate_week', 'Provide one allocation per target week.')
                by_week[week] = False
            else:
                by_week[week] = time_complete
    for week in weeks:
        if week not in by_week:
            check.uncertain('time_allocations', 'missing_week', f'No time allocation is recorded for week {week}.')
    return by_week, generated_gaps, formats


def inspect_unknowns(check, bundle):
    start = check.checkpoint()
    entries = check.strings(bundle.get('unknowns', MISSING), 'unknowns', nonempty=False)
    for i, entry in enumerate(entries):
        if entry:
            check.uncertain(f'unknowns[{i}]', 'reported_unknown', entry)
    return not check.changed(start)


def inspect_refs(check, value, path, catalog, other_catalog):
    refs = check.array(value, path, nonempty=True)
    for i, raw in enumerate(refs):
        ref_path = f'{path}[{i}]'
        ref = check.obj(raw, ref_path)
        sid = check.string(ref.get('source_id', MISSING), ref_path + '.source_id')
        check.string(ref.get('locator', MISSING), ref_path + '.locator')
        if sid:
            if sid not in catalog:
                detail = 'belongs to the other source category' if sid in other_catalog else 'is not declared'
                check.error(ref_path + '.source_id', 'invalid_reference', f'This source ID {detail}.')
            elif not catalog[sid]:
                check.uncertain(ref_path + '.source_id', 'unusable_source',
                                'The referenced source has missing, invalid, ambiguous, or unconfirmed details.')


def inspect_theory(check, value, path):
    theory = check.obj(value, path)
    applicable = check.boolean(theory.get('applicable', MISSING), path + '.applicable')
    claim = check.string(theory.get('claim', MISSING), path + '.claim', allow_empty=applicable is False)
    locators = check.strings(theory.get('evidence_locators', MISSING), path + '.evidence_locators',
                             nonempty=applicable is not False)
    if applicable is False and (claim or any(locators)):
        check.uncertain(path, 'theory_contradiction', 'Theory is marked inapplicable but a claim or evidence is recorded.')


def inspect_comparisons(check, bundle, catalogs, weeks, goals, target_ready, time_ready, format_ready, unknowns_clear):
    entries = check.array(bundle.get('comparisons', MISSING), 'comparisons', nonempty=True)
    results, gaps, seen_ids, covered_weeks, covered_goals = [], [], set(), set(), set()
    for i, raw in enumerate(entries):
        path = f'comparisons[{i}]'
        start = check.checkpoint()
        item = check.obj(raw, path)
        cid = check.string(item.get('id', MISSING), path + '.id')
        if cid:
            if cid in seen_ids:
                check.error(path + '.id', 'duplicate_id', 'Comparison IDs must be unique.')
            seen_ids.add(cid)
        week = check.integer(item.get('week', MISSING), path + '.week', 1, 10)
        if week is not None:
            covered_weeks.add(week)
            if weeks and week not in weeks:
                check.error(path + '.week', 'outside_target', 'The comparison week must belong to target.weeks.')
        goal_id = check.string(item.get('goal_id', MISSING), path + '.goal_id')
        if goal_id:
            if goal_id not in goals:
                check.error(path + '.goal_id', 'invalid_reference', 'This goal ID is not declared in target.goals.')
            else:
                covered_goals.add(goal_id)
                if week is not None and goals[goal_id] is not None and week != goals[goal_id]:
                    check.error(path + '.week', 'goal_week_mismatch', 'The comparison and selected goal must have the same week.')
        for field in ('competency', 'assessment_method', 'answer_conditions', 'allowed_support'):
            check.string(item.get(field, MISSING), path + '.' + field)
        author = check.string(item.get('author_id', MISSING), path + '.author_id')
        reviewer = check.obj(item.get('reviewer', MISSING), path + '.reviewer')
        reviewer_id = check.string(reviewer.get('id', MISSING), path + '.reviewer.id')
        independent = check.boolean(reviewer.get('independent', MISSING), path + '.reviewer.independent')
        check.string(reviewer.get('evidence_locator', MISSING), path + '.reviewer.evidence_locator')
        if independent is False:
            check.uncertain(path + '.reviewer.independent', 'not_independent', 'The reviewer is not recorded as independent.')
        if author and reviewer_id and author == reviewer_id:
            check.uncertain(path + '.reviewer.id', 'same_author_reviewer', 'The recorded author and reviewer IDs match.')
        inspect_refs(check, item.get('scope_refs', MISSING), path + '.scope_refs',
                     catalogs['scope_sources'], catalogs['problem_sources'])
        inspect_refs(check, item.get('problem_refs', MISSING), path + '.problem_refs',
                     catalogs['problem_sources'], catalogs['scope_sources'])
        check.strings(item.get('student_task_locators', MISSING), path + '.student_task_locators')
        difference = check.string(item.get('difference', MISSING), path + '.difference')
        judgment = check.choice(item.get('judgment', MISSING), path + '.judgment', {'met', 'gap', 'uncertain'})
        rationale = check.string(item.get('rationale', MISSING), path + '.rationale')
        inspect_theory(check, item.get('theory', MISSING), path + '.theory')
        priority = None
        if judgment == 'gap' or 'priority' in item:
            priority = check.choice(item.get('priority', MISSING), path + '.priority', PRIORITY)
        if judgment == 'uncertain':
            check.uncertain(path + '.judgment', 'recorded_uncertainty', 'The recorder judged this comparison uncertain.')
        if not target_ready:
            check.uncertain(path, 'incomplete_target', 'The target, artifact, weeks, or prerequisite assumptions are incomplete.')
        if week is not None and not time_ready.get(week, False):
            check.uncertain(path, 'incomplete_time', 'A complete allocation consistent with target.class_minutes is unavailable for this week.')
        if week is not None and not format_ready.get(week, False):
            check.uncertain(path, 'assessment_format_unresolved', 'The recorded assessment format is incomplete or differs from its requirement.')
        if not unknowns_clear:
            check.uncertain(path, 'unresolved_unknowns', 'The bundle has missing or unresolved unknowns with no per-item scope.')
        issue_paths = [x['path'] for x in check.findings[start[0]:]] + [x['path'] for x in check.errors[start[1]:]]
        status = 'gap' if judgment == 'gap' else ('uncertain' if check.changed(start) or judgment != 'met' else 'met')
        results.append({'id': cid or path, 'week': week, 'goal_id': goal_id or None, 'recorded_judgment': judgment,
                        'status': status, 'issue_paths': issue_paths})
        if judgment == 'gap':
            gaps.append({'id': cid or path, 'origin': 'recorded_comparison', 'week': week, 'priority': priority,
                         'difference': difference, 'rationale': rationale})
    for week in weeks:
        if week not in covered_weeks:
            check.uncertain('comparisons', 'missing_week', f'No comparison is recorded for target week {week}.')
    for goal_id in goals:
        if goal_id not in covered_goals:
            check.uncertain('comparisons', 'missing_goal', f'No comparison is recorded for selected goal {goal_id}.')
    return results, gaps


def inspect(bundle):
    check = Inspection()
    bundle = check.obj(bundle, '$')
    version = bundle.get('schema_version', MISSING)
    if version is MISSING or version is None:
        check.uncertain('schema_version', 'missing', 'Schema version 1 is required.')
    elif type(version) is not int or version != 1:
        check.error('schema_version', 'invalid_value', 'Expected integer schema version 1.')
    synthetic = check.boolean(bundle.get('synthetic', MISSING), 'synthetic')
    catalogs = inspect_sources(check, bundle)
    weeks, goals, class_minutes, target_ready = inspect_target(check, bundle)
    time_ready, generated_gaps, formats = inspect_times(check, bundle, weeks, class_minutes)
    unknowns_clear = inspect_unknowns(check, bundle)
    format_ready = {item['week']: item['status'] in ('matched', 'not_required') for item in formats}
    comparisons, gaps = inspect_comparisons(check, bundle, catalogs, weeks, goals, target_ready, time_ready, format_ready, unknowns_clear)
    gaps.extend(generated_gaps)
    gaps.sort(key=lambda item: (PRIORITY.get(item['priority'], 3), item['id']))
    status = ('invalid' if check.errors else 'gap' if gaps else
              'uncertain' if check.findings else 'recorded_met')
    return {'authority': 'advisory_only', 'status': status, 'synthetic': synthetic,
            'comparisons': comparisons, 'assessment_formats': formats, 'gaps': gaps, 'findings': check.findings,
            'errors': check.errors, 'verification': {'artifact_digest': 'not_checked', 'source_authenticity': 'not_checked',
                                                      'source_content': 'not_checked', 'reviewer_independence': 'not_checked',
                                                      'assessment_counts': 'not_checked'},
            'limitations': LIMITATIONS}


def reject_constant(value):
    raise ValueError('Non-finite JSON number: ' + value)


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path, help='JSON evidence bundle to inspect')
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.bundle.read_text(encoding='utf-8'), parse_constant=reject_constant,
                          object_pairs_hook=unique_pairs)
        result = inspect(data)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        result = {'authority': 'advisory_only', 'status': 'invalid', 'synthetic': None,
                  'comparisons': [], 'assessment_formats': [], 'gaps': [], 'findings': [],
                  'errors': [{'path': '$', 'code': 'unreadable_or_invalid_json', 'message': str(exc)}],
                  'verification': {'artifact_digest': 'not_checked', 'source_authenticity': 'not_checked',
                                   'source_content': 'not_checked', 'reviewer_independence': 'not_checked',
                                   'assessment_counts': 'not_checked'},
                  'limitations': LIMITATIONS}
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False))
    return 2 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
