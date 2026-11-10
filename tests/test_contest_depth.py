import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import contest_depth as depth

KNOWN_URLS = [
    'https://kitpa.org/files/36',
    'https://kitpa.org/storage/c4016751-0e2c-4548-ab70-ecec994e8f8d.pdf',
]


def synthetic_bundle():
    """Fictional records; these are not source reads or an actual lesson review."""
    scope = {'id': 'scope:fictional', 'title': 'Fictional scope',
             'url': 'https://example.invalid/fictional-scope', 'locator': 'fictional section 1',
             'version': 'synthetic-v1', 'accessed_at': '2026-11-10', 'read_extent': 'fictional section 1',
             'verification': 'verified_official',
             'verification_evidence': 'Synthetic declaration only; no source was consulted.'}
    problem = {**scope, 'id': 'problem:fictional', 'title': 'Fictional example',
               'url': 'https://example.invalid/fictional-problem', 'kind': 'example',
               'problem': 'fictional question 1', 'year': 2026, 'target': 'high_school'}
    return {
        'schema_version': 1, 'synthetic': True, 'scope_sources': [scope], 'problem_sources': [problem],
        'target': {'competition_year': 2027, 'division': 'middle_school', 'artifact': 'fictional-lesson.ipynb',
                   'artifact_revision': 'synthetic-v1', 'artifact_sha256': '0' * 64, 'class_minutes': 120,
                   'weeks': [1], 'baseline_assumptions': ['Fictional prerequisites; not a learner diagnosis.'],
                   'goals': [{'id': 'goal:synthetic', 'week': 1, 'description': 'A fictional goal.'}]},
        'comparisons': [{
            'id': 'comparison:synthetic', 'week': 1, 'goal_id': 'goal:synthetic',
            'competency': 'A fictional competency.',
            'scope_refs': [{'source_id': 'scope:fictional', 'locator': 'fictional section 1'}],
            'problem_refs': [{'source_id': 'problem:fictional', 'locator': 'fictional question 1'}],
            'student_task_locators': ['fictional cell 1'], 'difference': 'A fictional difference.',
            'judgment': 'met', 'rationale': 'Synthetic record; not an actual lesson review.',
            'assessment_method': 'Fictional written explanation.',
            'answer_conditions': 'Fictional answer is withheld until after submission.',
            'allowed_support': 'Fictional task permits no support.', 'author_id': 'synthetic-author',
            'reviewer': {'id': 'synthetic-reviewer', 'independent': True, 'evidence_locator': 'fictional review'},
            'theory': {'applicable': True, 'claim': 'Fictional claim.', 'evidence_locators': ['fictional explanation']},
        }],
        'time_allocations': [{
            'week': 1, 'in_class_minutes': 120, 'outside_class_minutes': 300, 'locator': 'fictional schedule',
            'required_assessment_format': {'status': 'specified', 'counts': {'multiple_choice': 2, 'written': 1},
                                           'locator': 'fictional requirement'},
            'observed_assessment_format': {'status': 'observed', 'counts': {'multiple_choice': 2, 'written': 1},
                                           'locator': 'fictional inspection'},
        }],
        'unknowns': [],
    }


def codes(items):
    return {item['code'] for item in items}


class ContestDepthTest(unittest.TestCase):
    def setUp(self):
        self.bundle = synthetic_bundle()

    def test_complete_synthetic_record_is_only_advisory_and_immutable(self):
        before = copy.deepcopy(self.bundle)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('No artifact or source read is allowed')):
            result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'recorded_met')
        self.assertEqual(result['comparisons'][0]['status'], 'met')
        self.assertEqual(result['assessment_formats'][0]['status'], 'matched')
        self.assertEqual(result['authority'], 'advisory_only')
        self.assertTrue(result['synthetic'])
        self.assertEqual(set(result['verification'].values()), {'not_checked'})
        self.assertIn('not read or verified', ' '.join(result['limitations']))
        self.assertIn('middle-school past problems', ' '.join(result['limitations']))
        self.assertEqual(self.bundle, before)
        self.assertEqual(result, depth.inspect(self.bundle))

    def test_recorded_gaps_are_sorted_and_priority_is_not_invented(self):
        base = self.bundle['comparisons'][0]
        comparisons = []
        for identifier, priority in [('z-low', 'low'), ('b-high', 'high'), ('a-high', 'high'), ('missing', None)]:
            entry = copy.deepcopy(base)
            entry.update(id=identifier, judgment='gap')
            if priority:
                entry['priority'] = priority
            comparisons.append(entry)
        self.bundle['comparisons'] = comparisons
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertEqual([x['id'] for x in result['gaps']], ['a-high', 'b-high', 'z-low', 'missing'])
        self.assertIsNone(result['gaps'][-1]['priority'])
        self.assertTrue(any(x['path'].endswith('.priority') for x in result['findings']))

    def test_missing_essential_metadata_never_upgrades_met(self):
        cases = [
            ('target', 'competition_year'), ('target', 'division'), ('target', 'artifact'),
            ('target', 'artifact_revision'), ('target', 'artifact_sha256'), ('target', 'class_minutes'),
            ('target', 'baseline_assumptions'), ('scope_sources', 'version'), ('scope_sources', 'accessed_at'),
            ('scope_sources', 'read_extent'), ('scope_sources', 'verification_evidence'),
            ('problem_sources', 'problem'), ('problem_sources', 'year'), ('problem_sources', 'target'),
            ('problem_sources', 'kind'), ('comparisons', 'competency'), ('comparisons', 'student_task_locators'),
            ('comparisons', 'scope_refs'), ('comparisons', 'problem_refs'), ('comparisons', 'difference'),
            ('comparisons', 'rationale'), ('comparisons', 'assessment_method'), ('comparisons', 'answer_conditions'),
            ('comparisons', 'allowed_support'), ('comparisons', 'author_id'), ('comparisons', 'reviewer'),
            ('comparisons', 'goal_id'), ('time_allocations', 'outside_class_minutes'),
            ('time_allocations', 'locator'), ('time_allocations', 'required_assessment_format'),
            ('time_allocations', 'observed_assessment_format'),
        ]
        for collection, field in cases:
            with self.subTest(collection=collection, field=field):
                data = copy.deepcopy(self.bundle)
                subject = data[collection] if collection == 'target' else data[collection][0]
                subject.pop(field)
                result = depth.inspect(data)
                self.assertEqual(result['status'], 'uncertain')
                self.assertEqual(result['comparisons'][0]['status'], 'uncertain')
                self.assertTrue(result['findings'])

    def test_missing_theory_or_empty_difference_is_uncertain(self):
        for field, value in [('claim', ''), ('evidence_locators', []), ('applicable', None)]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.bundle)
                data['comparisons'][0]['theory'][field] = value
                result = depth.inspect(data)
                self.assertEqual(result['status'], 'uncertain')
                self.assertEqual(result['comparisons'][0]['status'], 'uncertain')
        self.bundle['comparisons'][0]['difference'] = '  '
        self.assertEqual(depth.inspect(self.bundle)['comparisons'][0]['status'], 'uncertain')

    def test_theory_inapplicability_is_explicit_and_consistent(self):
        theory = {'applicable': False, 'claim': '', 'evidence_locators': []}
        self.bundle['comparisons'][0]['theory'] = theory
        self.assertEqual(depth.inspect(self.bundle)['status'], 'recorded_met')
        theory['claim'] = 'Yet a claim is recorded.'
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertIn('theory_contradiction', codes(result['findings']))
        theory.pop('claim')
        self.assertEqual(depth.inspect(self.bundle)['status'], 'uncertain')

    def test_unconfirmed_or_fabricated_source_status_cannot_pass(self):
        self.bundle['problem_sources'][0]['verification'] = 'unconfirmed'
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(result['comparisons'][0]['status'], 'uncertain')
        self.assertIn('unconfirmed_source', codes(result['findings']))
        self.bundle['problem_sources'][0]['verification'] = 'definitely_true_because_ai_said_so'
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('invalid_value', codes(result['errors']))

    def test_known_2026_example_source_and_neighboring_false_labels(self):
        for url in KNOWN_URLS:
            with self.subTest(url=url):
                data = copy.deepcopy(self.bundle)
                data['problem_sources'][0]['url'] = url + '?view=1#question'
                # Source standard and intended course division are deliberately different.
                self.assertEqual(depth.inspect(data)['status'], 'recorded_met')
                for field, value in [('kind', 'past_problem'), ('year', 2027), ('target', 'middle_school')]:
                    wrong = copy.deepcopy(data)
                    wrong['problem_sources'][0][field] = value
                    result = depth.inspect(wrong)
                    self.assertEqual(result['status'], 'invalid')
                    self.assertEqual(result['comparisons'][0]['status'], 'uncertain')
                    self.assertIn('known_source_conflict', codes(result['errors']))
                unknown_label = copy.deepcopy(data)
                unknown_label['problem_sources'][0]['target'] = 'ambiguous audience'
                self.assertEqual(depth.inspect(unknown_label)['status'], 'uncertain')

    def test_other_source_truth_is_not_inferred(self):
        self.bundle['problem_sources'][0].update(url='https://example.invalid/other', kind='past_problem',
                                                 year=2027, target='middle_school')
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'recorded_met')
        self.assertEqual(result['verification']['source_authenticity'], 'not_checked')
        self.assertEqual(result['verification']['source_content'], 'not_checked')

    def test_selected_goal_coverage_and_week_mapping(self):
        self.bundle['target']['goals'].append({'id': 'goal:second', 'week': 1, 'description': 'A second goal.'})
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertIn('missing_goal', codes(result['findings']))
        second = copy.deepcopy(self.bundle['comparisons'][0])
        second.update(id='comparison:second', goal_id='goal:second')
        self.bundle['comparisons'].append(second)
        self.assertEqual(depth.inspect(self.bundle)['status'], 'recorded_met')
        self.bundle['comparisons'][1]['week'] = 2
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('goal_week_mismatch', codes(result['errors']))

    def test_class_and_outside_time_are_separate_and_configurable(self):
        self.bundle['target']['class_minutes'] = 90
        self.bundle['time_allocations'][0]['in_class_minutes'] = 90
        self.assertEqual(depth.inspect(self.bundle)['status'], 'recorded_met')
        self.bundle['time_allocations'][0]['in_class_minutes'] = 120
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertIn('class_time_mismatch', codes(result['findings']))
        self.assertEqual(result['gaps'][0]['origin'], 'time_allocation')
        self.assertIsNone(result['gaps'][0]['priority'])
        self.assertEqual(result['comparisons'][0]['status'], 'uncertain')

    def test_required_assessment_counts_missing_from_observed_lesson(self):
        observed = self.bundle['time_allocations'][0]['observed_assessment_format']
        observed['counts'] = {'multiple_choice': 0, 'written': 0}
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(result['assessment_formats'][0]['status'], 'gap')
        self.assertEqual([x['difference'] for x in result['assessment_formats'][0]['kinds']], [-2, -1])
        self.assertEqual(len(result['gaps']), 2)
        self.assertTrue(all(x['origin'] == 'assessment_format' for x in result['gaps']))
        self.assertTrue(all(x['priority'] is None for x in result['gaps']))
        observed['counts'] = {'multiple_choice': 2, 'written': 1}
        self.assertEqual(depth.inspect(self.bundle)['status'], 'recorded_met')
        observed['counts'].pop('written')
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertIn('missing_format_kind', codes(result['findings']))

    def test_assessment_mismatch_does_not_misreport_valid_class_time(self):
        allocation = self.bundle['time_allocations'][0]
        self.assertEqual(allocation['in_class_minutes'], 120)
        allocation['observed_assessment_format']['counts'] = {'multiple_choice': 0, 'written': 4}
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(result['assessment_formats'][0]['status'], 'gap')
        kinds = {item['kind']: item for item in result['assessment_formats'][0]['kinds']}
        self.assertEqual(kinds['multiple_choice']['difference'], -2)
        self.assertEqual(kinds['written']['difference'], 3)
        self.assertIn('assessment_format_unresolved', codes(result['findings']))
        self.assertNotIn('incomplete_time', codes(result['findings']))
        self.assertNotIn('class_time_mismatch', codes(result['findings']))
        self.assertEqual(result['comparisons'][0]['status'], 'uncertain')

        # The adjacent time-only defect must be attributed to time, not format.
        allocation['in_class_minutes'] = 119
        allocation['observed_assessment_format']['counts'] = {'multiple_choice': 2, 'written': 1}
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertIn('incomplete_time', codes(result['findings']))
        self.assertIn('class_time_mismatch', codes(result['findings']))
        self.assertNotIn('assessment_format_unresolved', codes(result['findings']))
        self.assertEqual(result['assessment_formats'][0]['status'], 'matched')

        allocation['in_class_minutes'] = 120
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'recorded_met')
        self.assertNotIn('incomplete_time', codes(result['findings']))
        self.assertNotIn('assessment_format_unresolved', codes(result['findings']))

    def test_additional_unrequired_assessment_kind_is_not_called_matched(self):
        observed = self.bundle['time_allocations'][0]['observed_assessment_format']['counts']
        observed['additional_essays'] = 12
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertEqual(result['assessment_formats'][0]['status'], 'uncertain')
        self.assertIn('additional_format_kind', codes(result['findings']))
        observed['additional_essays'] = 0
        self.assertEqual(depth.inspect(self.bundle)['status'], 'recorded_met')

    def test_assessment_format_can_be_explicitly_unrequired(self):
        allocation = self.bundle['time_allocations'][0]
        allocation['required_assessment_format'] = {'status': 'none', 'counts': {}, 'locator': 'fictional scope'}
        allocation['observed_assessment_format'] = {'status': 'not_applicable', 'counts': {}, 'locator': 'fictional scope'}
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'recorded_met')
        self.assertEqual(result['assessment_formats'][0]['status'], 'not_required')
        allocation['required_assessment_format']['status'] = 'uncertain'
        self.assertEqual(depth.inspect(self.bundle)['status'], 'uncertain')

    def test_uncertainty_remains_visible_alongside_a_gap(self):
        self.bundle['comparisons'][0].update(judgment='gap', priority='high', difference='')
        self.bundle['unknowns'] = ['The source audience has not been checked.']
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'gap')
        self.assertEqual(result['gaps'][0]['id'], 'comparison:synthetic')
        self.assertIn('reported_unknown', codes(result['findings']))
        self.assertIn('empty', codes(result['findings']))

    def test_reviewer_identity_and_independence_are_declarations(self):
        self.bundle['comparisons'][0]['reviewer']['id'] = 'synthetic-author'
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'uncertain')
        self.assertIn('same_author_reviewer', codes(result['findings']))
        self.bundle['comparisons'][0]['reviewer'].update(id='other', independent=False)
        self.assertIn('not_independent', codes(depth.inspect(self.bundle)['findings']))
        self.bundle['comparisons'][0]['reviewer']['independent'] = True
        self.assertEqual(depth.inspect(self.bundle)['verification']['reviewer_independence'], 'not_checked')

    def test_missing_unknowns_and_invalid_references_are_distinct(self):
        self.bundle.pop('unknowns')
        self.assertEqual(depth.inspect(self.bundle)['status'], 'uncertain')
        self.bundle['unknowns'] = []
        self.bundle['comparisons'][0]['scope_refs'][0]['source_id'] = 'problem:fictional'
        result = depth.inspect(self.bundle)
        self.assertEqual(result['status'], 'invalid')
        self.assertIn('invalid_reference', codes(result['errors']))

    def test_bad_dates_digests_and_boolean_integers_are_rejected(self):
        for section, field, value in [('scope_sources', 'accessed_at', '2026-02-30'),
                                      ('target', 'artifact_sha256', 'no-digest'),
                                      ('scope_sources', 'url', 'https://user@'),
                                      ('target', 'class_minutes', True)]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.bundle)
                (data[section] if section == 'target' else data[section][0])[field] = value
                self.assertEqual(depth.inspect(data)['status'], 'invalid')

    def test_cli_status_exit_and_read_only_behavior(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'bundle.json'
            self.bundle['comparisons'][0].update(judgment='gap', priority='high')
            content = json.dumps(self.bundle)
            path.write_text(content, encoding='utf-8')
            run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/contest_depth.py'), str(path)],
                                 cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(run.returncode, 0)
            self.assertEqual(json.loads(run.stdout)['status'], 'gap')
            self.assertEqual(path.read_text(encoding='utf-8'), content)
            for content in ['{"schema_version": 1, "schema_version": 1}', '{"value": NaN}', '{']:
                with self.subTest(content=content):
                    path.write_text(content, encoding='utf-8')
                    run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/contest_depth.py'), str(path)],
                                         cwd=ROOT, capture_output=True, text=True, check=False)
                    self.assertEqual(run.returncode, 2)
                    self.assertEqual(json.loads(run.stdout)['status'], 'invalid')


if __name__ == '__main__':
    if sys.argv[1:] == ['--emit-example']:
        print(json.dumps(synthetic_bundle(), ensure_ascii=False, indent=2))
    else:
        unittest.main()
