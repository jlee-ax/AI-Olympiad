"""Fault injection and neighboring valid cases; every learner/review receipt here is synthetic."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import quality
import workflow


def evidence(root):
    path = root / 'fixture-receipt.json'
    path.write_text('{"synthetic":true,"note":"No real lesson, learner or source review was executed."}\n')
    return [{'locator': 'synthetic control receipt', 'observation': 'Synthetic normal/fault control, not a learner result.',
             'path': path.name, 'sha256': quality.file_digest(path)}]


def agree(bundle, root):
    bundle['policy']['agreed'] = True
    bundle['policy']['decision_ref'] = 'synthetic decision, not user consent'
    bundle['policy']['agreement_fingerprint'] = quality.agreement_fingerprint(bundle, root)


def refresh_reviews(bundle, root):
    for review in bundle['reviews']:
        review['context_fingerprint'] = quality.object_fingerprint(
            bundle, review['criterion_id'], review['object_id'], root)
        review['context_bindings'] = quality.context_bindings(bundle, review['object_id'], root)
        binding = quality.plan_bindings(bundle, review['object_id'], root)
        if binding['required']:
            review['dependency_scope_fingerprint'] = binding['scope_fingerprint']


def normal_bundle(root):
    receipt = evidence(root)
    artifact = quality.load(root / quality.CONTRACT)['baseline']
    bundle = quality.load(ROOT / 'templates/quality.json')
    bundle.update(synthetic=True, revision='synthetic-v1', author_id='synthetic-author')
    bundle['target']['objective_ids'] = ['unit:axis']
    bundle['budget'] = {'max_attempts': 8, 'max_elapsed_minutes': 90, 'max_no_progress': 3}
    bundle['policy']['calibration_tolerance'] = {'false_rejects': 0, 'missed_faults': 0}
    bundle['policy']['maximum_required_homework_minutes'] = 420
    bundle['artifact']['sha256'] = artifact['sha256']
    claim = {'id': 'claim:axis', 'statement': 'Synthetic axis=0 mean result.',
             'domain': 'Rectangular finite two-dimensional input', 'quantity': 'arithmetic_mean',
             'assumptions': ['keepdims=False'], 'source_ids': ['source:numpy'], 'locator': '#week-1',
             'oracle': {'kind': 'axis_mean', 'input': [[1, 2, 3], [4, 5, 6]], 'axis': 0,
                        'expected': [2.5, 3.5, 4.5]}}
    unit = {'id': 'unit:axis', 'week': 1, 'locator': '#week-1', 'syllabus_ids': ['KOAI-02', 'KOAI-06'],
            'concept_ids': ['axis_mean'], 'claim_ids': ['claim:axis'], 'claimed_depth': 'independent',
            'plan_dependency_ids': ['unit:axis'],
            'oracle_kinds': ['axis_mean'],
            'explanation_checks': ['T01', 'T02', 'T03', 'T04', 'T05'],
            'explanation_regions': {tid: ['#week-1'] for tid in ('T01', 'T02', 'T03', 'T04', 'T05')},
            'mode_evidence': {'theory': 'passed', 'practical': 'passed'},
            'prerequisites': [{'id': 'synthetic-list', 'task': 'Trace a small list.',
                               'expected': 'State selected values.', 'observed': 'Synthetic matching response.',
                               'help': 'none', 'status': 'passed', 'evidence': receipt}],
            'chain': {role: {'concept_ids': ['axis_mean'], 'locator': '#week-1',
                             'expected_behavior': 'Synthetic corresponding behavior.',
                             'activity_id': 'class:' + ('noncoding' if role == 'assessment' else role),
                             'help': 'none', 'new_input': True}
                      for role in ('theory', 'noncoding', 'coding', 'assessment')},
            'execution': {'status': 'passed', 'artifact_sha256': artifact['sha256'],
                          'command': 'synthetic fixture; no external worker executed',
                          'environment': 'synthetic', 'exit_code': 0, 'clean_run': True, 'new_input': True,
                          'assertions': [{'name': 'synthetic expected output', 'status': 'passed'}], 'evidence': receipt},
            'calibration': [{'case_id': 'synthetic-good', 'expected': 'passed', 'observed': 'passed', 'evidence': receipt},
                            {'case_id': 'synthetic-fault', 'expected': 'failed', 'observed': 'failed', 'evidence': receipt}]}
    bundle['lesson_allocations'] = [{'week': 1,
        'outside_work': [{'id': 'required-week-1', 'required': True, 'minutes': 420}], 'blocks': [
        {'id': 'class:theory', 'kind': 'theory', 'minutes': 20, 'written_minutes': 0},
        {'id': 'class:noncoding', 'kind': 'noncoding', 'minutes': 20, 'written_minutes': 10},
        {'id': 'class:coding', 'kind': 'coding', 'minutes': 80, 'written_minutes': 0}]}]
    bundle['claims'] = [claim]
    bundle['units'] = [unit]
    bundle['source_reads'] = [{'id': 'source:numpy', 'url': 'https://numpy.org/doc/stable/reference/generated/numpy.mean.html',
                              'kind': 'documentation', 'extent': 'relevant_sections', 'version': 'synthetic-v1',
                              'accessed_at': '2026-11-10', 'locator': 'axis parameter',
                              'finding': 'Synthetic source-reading declaration.', 'limitation': 'Not a real reading receipt.'}]
    bundle['research_cycles'] = [{'id': 'cycle:synthetic', 'trigger': 'synthetic case',
                                  'queries': ['synthetic axis question'], 'source_ids': ['source:numpy'],
                                  'object_ids': ['claim:axis'], 'disposition': 'unchanged', 'reason': 'Synthetic fixture.'}]
    bundle['dependencies'] = [
        {'id': 'source:numpy', 'revision': 'synthetic-v1', 'sha256': quality.digest('synthetic source'), 'depends_on': []},
        {'id': 'claim:axis', 'revision': 'synthetic-v1', 'sha256': quality.digest(claim), 'depends_on': ['source:numpy']},
        {'id': 'unit:axis', 'revision': 'synthetic-v1', 'sha256': quality.digest(unit), 'depends_on': ['claim:axis'],
         'path': 'curriculum/student-plan.html', 'locators': ['#week-1', '#scope-02', '#scope-06', '#plan-context']},
    ]
    bundle['reviews'] = [{'id': 'review:' + cid, 'criterion_id': cid, 'object_id': oid,
                          'status': 'passed', 'reviewer_id': 'synthetic-independent-reviewer',
                          'evidence': receipt, 'reason': 'Synthetic fixture review, not educator calibration.'}
                         for cid, oid in [('K02', 'unit:axis'), ('K05', 'unit:axis'), ('K06', 'claim:axis'),
                                          ('K09', 'unit:axis'), ('K15', 'unit:axis'), ('K16', 'unit:axis')]]
    bundle['reviews'][-1]['subchecks'] = {tid: {'status': 'passed', 'artifact_locators': ['#week-1'], 'evidence': receipt}
                                        for tid in ('T01', 'T02', 'T03', 'T04', 'T05')}
    agree(bundle, root)
    refresh_reviews(bundle, root)
    bundle['research_cycles'][0]['object_contexts'] = {'claim:axis': quality.object_fingerprint(bundle, 'K10', 'claim:axis', root)}
    return bundle


def check(report, identifier):
    return next(x for x in report['checks'] if x['id'] == identifier)


class QualityTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for relative in (quality.CATALOG, quality.CONTRACT, 'curriculum/student-plan.html', quality.UNIT_SPECIFICATIONS, quality.THEORY_SPECIFICATION):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.bundle = normal_bundle(self.root)

    def report(self):
        return quality.evaluate(self.bundle, self.root)

    def test_confirmed_baseline_is_10_by_120_with_60_planned_topics(self):
        result = quality.baseline(self.root)
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['weeks']), 10)
        self.assertTrue(all(x['class_minutes'] == 120 for x in result['weeks']))
        self.assertEqual(result['topic_count'], 60)
        self.assertEqual(result['coverage'], 'scheduled_only')

    def test_unconfigured_template_does_not_pass_or_invent_thresholds(self):
        bundle = quality.load(ROOT / 'templates/quality.json')
        report = quality.evaluate(bundle)
        self.assertFalse(report['ready_for_review'])
        self.assertEqual(check(report, 'K04')['status'], 'not_run')
        self.assertIsNone(bundle['policy']['diagnostic_cutoff'])
        self.assertIsNone(bundle['budget']['max_attempts'])
        self.assertEqual(quality.plan_work(bundle)['reason'], 'priority_policy_requires_agreement')

    def test_synthetic_normal_case_is_explicit_and_deterministic(self):
        before = copy.deepcopy(self.bundle)
        first = self.report()
        self.assertTrue(first['ready_for_review'])
        self.assertTrue(first['synthetic'])
        self.assertEqual(first, self.report())
        self.assertEqual(self.bundle, before)

    def test_visible_240_minute_fault_is_detected_even_if_metadata_unchanged(self):
        path = self.root / 'curriculum/student-plan.html'
        path.write_text(path.read_text().replace('\ucf54\ub529 80\ubd84:', '\ucf54\ub529 200\ubd84:', 1))
        result = quality.baseline(self.root)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('week 1' in x for x in result['errors']))

    def test_material_time_cannot_add_written_practice_on_top_of_120(self):
        self.bundle['lesson_allocations'][0]['blocks'].append(
            {'id': 'extra-writing', 'kind': 'noncoding', 'minutes': 10, 'written_minutes': 10})
        self.assertEqual(check(self.report(), 'K03')['status'], 'failed')

    def test_material_activities_must_point_to_an_accounted_block(self):
        self.bundle['units'][0]['chain']['coding']['activity_id'] = 'unbudgeted-activity'
        self.assertEqual(check(self.report(), 'K03')['status'], 'not_run')

    def test_source_update_requires_a_current_research_cycle(self):
        self.bundle['source_reads'][0]['version'] = 'synthetic-v2'
        self.assertEqual(check(self.report(), 'K11')['status'], 'uncertain')

    def test_missing_scope_row_and_wrong_official_mode_are_detected(self):
        contract_path = self.root / quality.CONTRACT
        contract = quality.load(contract_path)
        contract['topics'][0]['theory'] = True
        contract_path.write_text(json.dumps(contract))
        self.assertIn('Theory/practical flag mismatch: KOAI-01', quality.baseline(self.root)['errors'])

    def test_concept_only_cannot_pass_practical_requirement(self):
        self.bundle['units'][0]['claimed_depth'] = 'concept'
        refresh_reviews(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K02')['status'], 'failed')

    def test_missing_practical_receipt_is_not_run_even_with_positive_review(self):
        self.bundle['units'][0]['mode_evidence']['practical'] = 'not_run'
        refresh_reviews(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K02')['status'], 'not_run')

    def test_full_scope_claim_exposes_missing_topics(self):
        self.bundle['target']['coverage_claim'] = 'full_syllabus'
        result = check(self.report(), 'K02')
        self.assertEqual(result['status'], 'not_run')
        self.assertGreater(len(result['measurement']['full_claim_missing_topics']), 0)

    def test_support_route_is_distinct_from_unobserved_readiness(self):
        prerequisite = self.bundle['units'][0]['prerequisites'][0]
        prerequisite['status'] = 'needs_support'
        self.assertEqual(check(self.report(), 'K04')['status'], 'failed')
        prerequisite['support_before_use'] = {'before_unit': 'unit:axis', 'activity_id': 'synthetic-bridge', 'locator': '#week-1', 'time_location': 'before class'}
        self.assertEqual(check(self.report(), 'K04')['status'], 'passed')
        prerequisite['observed'] = ''
        self.assertEqual(check(self.report(), 'K04')['status'], 'not_run')

    def test_wrong_concept_link_fails_even_with_refreshed_review(self):
        self.bundle['units'][0]['chain']['coding']['concept_ids'] = ['unrelated_plot']
        refresh_reviews(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K05')['status'], 'failed')

    def test_wrong_axis_output_is_independently_rejected(self):
        self.bundle['claims'][0]['oracle']['expected'] = [2, 5]
        refresh_reviews(self.bundle, self.root)
        result = check(self.report(), 'K07')
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['measurement']['reference_checks'][0]['actual'], [2.5, 3.5, 4.5])

    def test_neighbor_axis_1_case_is_correct(self):
        self.bundle['claims'][0]['oracle'].update(axis=1, expected=[2, 5])
        refresh_reviews(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K07')['status'], 'passed')

    def test_metrics_denominators_and_undefined_convention(self):
        spec = {'kind': 'binary_metrics', 'tp': 5, 'fp': 10, 'fn': 5, 'tn': 80}
        values = quality.oracle(spec)
        self.assertAlmostEqual(values['precision'], 1 / 3)
        self.assertEqual(values['recall'], .5)
        self.assertEqual(values['f1'], .4)
        spec.update(tp=0, fp=0)
        with self.assertRaisesRegex(ValueError, 'Undefined'):
            quality.oracle(spec)
        spec['zero_division'] = 0
        self.assertEqual(quality.oracle(spec)['precision'], 0)

    def test_fitted_validation_data_and_overlap_fail_even_if_declared_expected(self):
        spec = {'kind': 'split_fit', 'train': ['a'], 'validation': ['b'], 'test': ['c'],
                'fit_ids': ['a'], 'test_used_for_selection': False}
        self.assertEqual(quality.oracle(spec), {'disjoint': True, 'fit_train_only': True, 'test_used_for_selection': False})
        spec['fit_ids'].append('b')
        self.bundle['claims'][0]['oracle'] = {**spec, 'expected': quality.oracle(spec)}
        self.assertEqual(check(self.report(), 'K07')['status'], 'failed')
        spec['fit_ids'] = ['a']
        spec['test'] = ['a']
        self.bundle['claims'][0]['oracle'] = {**spec, 'expected': quality.oracle(spec)}
        self.assertEqual(check(self.report(), 'K07')['status'], 'failed')

    def test_execution_requires_current_digest_and_actual_receipt_bytes(self):
        execution = self.bundle['units'][0]['execution']
        execution['artifact_sha256'] = '0' * 64
        self.assertEqual(check(self.report(), 'K08')['status'], 'failed')
        execution['artifact_sha256'] = self.bundle['artifact']['sha256']
        self.assertEqual(check(self.report(), 'K08')['status'], 'passed')
        (self.root / 'fixture-receipt.json').write_text('changed receipt')
        self.assertEqual(check(self.report(), 'K08')['status'], 'failed')

    def test_failed_execution_and_no_execution_are_not_passes(self):
        execution = self.bundle['units'][0]['execution']
        execution['exit_code'] = 1
        self.assertEqual(check(self.report(), 'K08')['status'], 'failed')
        execution['status'] = 'not_run'
        self.assertEqual(check(self.report(), 'K08')['status'], 'not_run')

    def test_independent_claim_rejects_visible_answer_or_missing_transfer(self):
        assessment = self.bundle['units'][0]['chain']['assessment']
        assessment['help'] = 'answer_visible'
        self.assertEqual(check(self.report(), 'K09')['status'], 'failed')
        assessment['help'] = 'none'
        assessment['new_input'] = False
        self.assertEqual(check(self.report(), 'K09')['status'], 'failed')

    def test_abstract_cannot_support_a_methods_dependent_claim(self):
        self.bundle['claims'][0]['claim_type'] = 'empirical_effect'
        self.bundle['source_reads'][0]['extent'] = 'abstract'
        self.assertEqual(check(self.report(), 'K10')['status'], 'uncertain')

    def test_source_version_change_invalidates_only_affected_review_context(self):
        before = quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root)
        self.bundle['source_reads'][0]['version'] = 'new version'
        after = quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root)
        self.assertNotEqual(before, after)
        self.assertEqual(check(self.report(), 'K12')['status'], 'uncertain')

    def test_unchanged_source_recheck_does_not_invalidate_content_review(self):
        before = quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root)
        self.bundle['source_reads'][0]['accessed_at'] = '2026-11-11'
        self.assertEqual(before, quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root))
        self.assertEqual(check(self.report(), 'K11')['status'], 'passed')

    def test_new_execution_receipt_does_not_force_unrelated_semantic_rewrite(self):
        before = quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
        self.bundle['units'][0]['execution']['command'] = 'synthetic repeat command'
        self.assertEqual(before, quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root))

    def test_a_manual_priority_cannot_downgrade_reproduced_error(self):
        self.bundle['claims'][0]['oracle']['expected'] = [99]
        self.bundle['candidates'] = [{'id': 'manual-wrong-tier', 'criterion_id': 'K07',
                                     'object_id': 'claim:axis', 'severity': 'minor', 'confidence': 'unresolved',
                                     'hypothesis': 'Synthetic fix', 'action': 'Synthetic correction'}]
        result = quality.plan_work(self.bundle, self.root)
        self.assertEqual(result['ranked'][0]['id'], 'manual-wrong-tier')
        self.assertEqual(result['ranked'][0]['priority'], 'P0')

    def test_unrelated_html_region_does_not_invalidate_local_content_review(self):
        before = quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root)
        path = self.root / 'curriculum/student-plan.html'
        path.write_text(path.read_text().replace('2\uc8fc\ucc28', '2\uc8fc\ucc28 [synthetic unrelated edit]', 1))
        self.assertEqual(before, quality.object_fingerprint(self.bundle, 'K06', 'claim:axis', self.root))

    def test_impact_is_transitive_and_cycles_terminate(self):
        self.bundle['dependencies'].append({'id': 'unrelated', 'revision': 'v1', 'sha256': '0' * 64, 'depends_on': []})
        result = quality.impact(self.bundle, ['source:numpy'])
        self.assertEqual(result['affected'], ['claim:axis', 'source:numpy', 'unit:axis'])
        self.assertEqual(result['unaffected'], ['unrelated'])
        self.bundle['dependencies'][0]['depends_on'] = ['unit:axis']
        self.assertEqual(len(quality.impact(self.bundle, ['source:numpy'])['affected']), 3)

    def test_missing_dependency_is_rejected(self):
        self.bundle['dependencies'][0]['depends_on'] = ['missing']
        with self.assertRaisesRegex(ValueError, 'Missing dependency'):
            quality.validate(self.bundle)

    def test_research_cycle_cannot_cover_unread_or_unrelated_claims(self):
        self.bundle['research_cycles'][0]['source_ids'] = ['missing']
        self.assertEqual(check(self.report(), 'K11')['status'], 'uncertain')
        self.bundle['research_cycles'] = []
        self.assertEqual(check(self.report(), 'K11')['status'], 'not_run')

    def test_calibration_missed_fault_is_visible(self):
        self.bundle['units'][0]['calibration'][1]['observed'] = 'passed'
        refresh_reviews(self.bundle, self.root)
        result = check(self.report(), 'K15')
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['measurement']['controls'][0]['missed_faults'], 1)

    def test_learning_claim_requires_separate_learner_evidence(self):
        self.bundle['target']['learning_outcomes'] = 'improved'
        self.assertEqual(check(self.report(), 'K15')['status'], 'failed')

    def candidate(self, identifier='candidate:style', criterion='K05', severity='minor'):
        return {'id': identifier, 'criterion_id': criterion, 'object_id': 'unit:axis', 'severity': severity,
                'confidence': 'confirmed', 'hypothesis': 'Synthetic typography hypothesis', 'action': 'Synthetic scoped style edit'}

    def test_reproduced_wrong_answer_precedes_manual_style_candidate(self):
        self.bundle['claims'][0]['oracle']['expected'] = [99]
        self.bundle['candidates'] = [self.candidate()]
        result = quality.plan_work(self.bundle, self.root)
        self.assertEqual(result['status'], 'continue')
        self.assertEqual(result['ranked'][0]['criterion_id'], 'K07')
        self.assertEqual(result['ranked'][0]['priority'], 'P0')

    def test_rejected_exact_proposal_is_skipped_and_distinct_action_remains(self):
        item = self.candidate()
        self.bundle['candidates'] = [item, {**item, 'id': 'copy'}]
        key = quality.candidate_key(self.bundle, item, self.root)
        self.bundle['attempts'] = [{'key': key, 'outcome': 'rejected', 'reason': 'Synthetic no benefit.'}]
        result = quality.plan_work(self.bundle, self.root)
        self.assertFalse(result['ranked'])
        self.assertEqual(len(result['skipped']), 2)
        self.bundle['candidates'][1]['action'] = 'A different explicit action'
        self.assertEqual(len(quality.plan_work(self.bundle, self.root)['ranked']), 1)

    def test_changed_dependency_reopens_proposal_without_erasing_history(self):
        item = self.candidate()
        self.bundle['candidates'] = [item]
        key = quality.candidate_key(self.bundle, item, self.root)
        self.bundle['attempts'] = [{'key': key, 'outcome': 'rejected', 'reason': 'Synthetic rejection.'}]
        self.bundle['source_reads'][0]['version'] = 'new'
        result = quality.plan_work(self.bundle, self.root)
        self.assertNotEqual(result['ranked'][0]['key'], key)
        self.assertEqual(len(self.bundle['attempts']), 1)

    def test_30_minute_checkpoint_and_each_finite_limit(self):
        self.bundle['checkpoint']['minutes_since'] = 30
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'checkpoint_due')
        self.bundle['checkpoint']['minutes_since'] = 0
        self.bundle['checkpoint']['elapsed_total'] = 90
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'finite_budget_exhausted')
        self.bundle['checkpoint']['elapsed_total'] = 0
        self.bundle['checkpoint']['no_progress_count'] = 3
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'finite_budget_exhausted')

    def test_policy_and_budget_changes_require_current_agreement(self):
        self.bundle['budget']['max_attempts'] = 9
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'priority_policy_requires_agreement')
        agree(self.bundle, self.root)
        self.bundle['budget']['max_attempts'] = None
        agree(self.bundle, self.root)
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'finite_budget_requires_agreement')

    def test_explicit_stop_and_missing_candidate_do_not_fake_completion(self):
        self.bundle['policy']['stop_requested'] = True
        self.assertEqual(quality.plan_work(self.bundle, self.root)['reason'], 'operator_stop')
        self.bundle['policy']['stop_requested'] = False
        self.bundle['units'][0]['execution']['status'] = 'not_run'
        result = quality.plan_work(self.bundle, self.root)
        self.assertNotEqual(result['reason'], 'recorded_checks_ready_for_independent_final_review')

    def test_self_review_cannot_pass_semantic_checks(self):
        self.bundle['reviews'][0]['reviewer_id'] = self.bundle['author_id']
        self.assertEqual(check(self.report(), 'K02')['status'], 'uncertain')

    def test_paths_and_malformed_json_fail_without_mutation(self):
        with self.assertRaises(ValueError):
            quality.safe_file(self.root, '../outside')
        with self.assertRaises(ValueError):
            quality.clean_json({'overflow': float('inf')})
        with self.assertRaises(UnicodeError):
            quality.clean_json({'text': '\ud800'})
        path = self.root / 'duplicate.json'
        path.write_text('{"schema_version":1,"schema_version":2}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            quality.load(path)

    def test_actual_cli_is_read_only_and_reports_invalid_input_as_json(self):
        path = self.root / 'bundle.json'
        path.write_text(json.dumps(self.bundle))
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/quality.py'), 'evaluate', str(path), '--root', str(self.root)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['synthetic'])
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        path.write_text('{"synthetic":1e999}')
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/quality.py'), 'evaluate', str(path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['reason'], 'invalid_quality_input')
        self.assertEqual(result.stderr, '')

    def bound_workflow(self, report):
        state = quality.load(ROOT / 'examples/workflow.json')
        state['scope']['task_kind'] = 'lesson_production'
        state['scope']['lesson_production_allowed'] = True
        state['agreement']['budget_fingerprint'] = workflow.budget_fingerprint(state)
        state['context']['artifact']['sha256'] = report['artifact_sha256']
        state['context']['inputs'] += [
            {'id': 'quality:bundle', 'revision': report['revision'], 'sha256': report['bundle_sha256']},
            {'id': 'quality:criteria', 'revision': report['specification_revision'], 'sha256': report['specification_sha256']},
            {'id': 'quality:evaluator', 'revision': 'quality-v1', 'sha256': report['evaluator_sha256']},
        ]
        state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(state)
        return state

    def test_committed_example_and_actual_cli_binding_stay_current(self):
        bundle = quality.load(ROOT / 'examples/quality.json')
        report = quality.evaluate(bundle)
        self.assertTrue(report['ready_for_review'])
        self.assertTrue(report['synthetic'])
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'),
                                 'decide', str(ROOT / 'examples/quality-workflow.json'),
                                 '--quality', str(ROOT / 'examples/quality.json')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['status'], 'continue')
        self.assertTrue(output['synthetic'])

    def test_workflow_requires_bound_current_quality_report(self):
        report = self.report()
        state = self.bound_workflow(report)
        self.assertEqual(workflow.decide(state)['reason'], 'quality_assessment_required')
        self.assertEqual(workflow.decide(state, report)['status'], 'continue')
        state['context']['inputs'][-3]['sha256'] = '0' * 64
        self.assertEqual(workflow.decide(state, report)['reason'], 'quality_context_not_bound')

    def test_real_work_cannot_use_synthetic_quality_and_failed_report_cannot_complete(self):
        report = self.report()
        state = self.bound_workflow(report)
        state['synthetic'] = False
        self.assertEqual(workflow.decide(state, report)['reason'], 'synthetic_quality_cannot_validate_real_work')
        state['synthetic'] = True
        state['stop']['goal_claimed'] = True
        report['ready_for_review'] = False
        self.assertEqual(workflow.decide(state, report)['reason'], 'quality_checks_not_passed')


if __name__ == '__main__':
    unittest.main()
