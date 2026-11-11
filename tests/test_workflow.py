"""Synthetic contract regressions: no lessons, network, or mutable fixtures."""
import contextlib
import copy
import io
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import workflow


def load(name='examples/workflow.json'):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def reviewed(state):
    state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(state)
    return state


def receipt(state, outcome='accepted'):
    state['history'].append({'id': f'receipt:{len(state["history"])}',
                             'context_fingerprint': workflow.context_fingerprint(state),
                             'outcome': outcome, 'reason': 'Synthetic completed attempt.'})


def add_record(state, identifier='evidence:new', text='Synthetic new evidence.', supersedes=None):
    record = copy.deepcopy(state['records'][0])
    record.update(id=identifier, text=text, supersedes=supersedes or [])
    state['records'].append(record)
    return record


class WorkflowTest(unittest.TestCase):
    def test_quality_bindings_ignore_decorative_metadata_but_require_exact_manifest(self):
        import quality
        state = load('examples/quality-workflow.json')
        report = quality.evaluate(quality.load(ROOT / 'examples/quality.json'))
        self.assertEqual(workflow.decide(state, report)['reason'], 'verified_candidate_within_budget')
        before = workflow.context_fingerprint(state)
        for manifest in state['context']['inputs']:
            if manifest['id'].startswith('quality:'):
                manifest['note'] = 'Decorative metadata.'
        self.assertEqual(workflow.validate_state(state)[0], [])
        self.assertEqual(workflow.context_fingerprint(state), before)
        self.assertEqual(workflow.decide(state, report)['reason'], 'verified_candidate_within_budget')
        for field, value in (('id', 'quality:other'), ('revision', 'different-revision'),
                             ('sha256', '0' * 64)):
            with self.subTest(field=field):
                changed = copy.deepcopy(state)
                bundle = next(item for item in changed['context']['inputs'] if item['id'] == 'quality:bundle')
                bundle[field] = value
                self.assertEqual(workflow.decide(changed, report)['reason'], 'quality_context_not_bound')

    def test_frozen_baseline_compares_declared_measurement_fields(self):
        state = load()
        before = workflow.context_fingerprint(state)
        for key in ('rubric', 'evaluator'):
            state['frozen'][key]['note'] = 'Saved human annotation.'
        state['frozen']['note'] = 'Baseline annotation.'
        self.assertEqual(workflow.validate_state(state)[0], [])
        self.assertEqual(workflow.context_fingerprint(state), before)
        self.assertEqual(workflow.decide(state)['reason'], 'verified_candidate_within_budget')
        for key in ('rubric', 'evaluator'):
            for field, value in (('id', 'other'), ('revision', 'other'), ('sha256', '0' * 64)):
                with self.subTest(key=key, field=field):
                    changed = copy.deepcopy(state)
                    changed['frozen'][key][field] = value
                    self.assertEqual(workflow.decide(changed)['reason'], 'baseline_change_required')

    def test_serialized_state_preserves_dedup_and_rejects_stale_review(self):
        state = load()
        receipt(state)
        duplicate = copy.deepcopy(state['records'][0])
        duplicate.update(id='evidence:restart-copy', created_at='2026-11-11T00:00:00Z')
        state['records'].append(duplicate)
        restored = json.loads(json.dumps(state))
        self.assertEqual(workflow.decide(restored)['reason'], 'no_new_evidence')
        self.assertEqual(len(workflow.recall_records(restored)), 1)
        add_record(restored, text='Synthetic evidence after restart.')
        self.assertEqual(workflow.decide(restored)['reason'], 'stale_verification')

    def test_template_is_valid_and_pauses_without_inventing_budget(self):
        state = load('templates/workflow.json')
        self.assertEqual(workflow.validate_state(state), ([], []))
        self.assertEqual(workflow.decide(state)['reason'], 'operator_agreement_required')
        self.assertIsNone(state['limits']['max_iterations'])
        self.assertFalse(state['scope']['lesson_production_allowed'])
        self.assertFalse(state['scope']['recurring_allowed'])

    def test_synthetic_example_is_advisory_only(self):
        result = workflow.decide(load())
        self.assertEqual((result['status'], result['authority'], result['synthetic']),
                         ('continue', 'advisory_only', True))

    def test_criteria_and_finite_budget_must_be_agreed(self):
        for mutate, expected in (
            (lambda s: s['agreement'].update(criteria_agreed=False), 'criteria_agreement_required'),
            (lambda s: s['agreement'].update(criteria_fingerprint='0' * 64), 'criteria_agreement_stale'),
            (lambda s: s['limits'].update(max_iterations=None), 'budget_unset'),
            (lambda s: s['agreement'].update(budget_fingerprint=None), 'budget_agreement_required'),
            (lambda s: s['limits'].update(max_iterations=9), 'budget_agreement_required'),
        ):
            with self.subTest(expected=expected):
                state = load()
                mutate(state)
                self.assertEqual(workflow.decide(state)['reason'], expected)

    def test_changed_inputs_skill_or_artifact_invalidate_review_and_reuse(self):
        for field in ('inputs', 'skills', 'artifact'):
            with self.subTest(field=field):
                state = load()
                receipt(state)
                manifest = state['context'][field][0] if field != 'artifact' else state['context'][field]
                manifest['sha256'] = 'a' * 64
                result = workflow.decide(state)
                self.assertEqual((result['status'], result['reason']), ('blocked', 'stale_verification'))
                self.assertFalse(result['verification']['passed'])

    def test_revision_changes_invalidate_even_with_same_content_hash(self):
        state = load()
        state['context']['skills'][0]['revision'] = 'synthetic-v2'
        self.assertEqual(workflow.decide(state)['reason'], 'stale_verification')

    def test_measurement_versions_are_frozen(self):
        for field in ('rubric', 'evaluator', 'references'):
            with self.subTest(field=field):
                state = load()
                manifest = state['context'][field][0] if field == 'references' else state['context'][field]
                manifest['revision'] = 'synthetic-v2'
                if field == 'references':
                    state['sources'][0]['revision'] = 'synthetic-v2'
                self.assertEqual(workflow.decide(state)['reason'], 'baseline_change_required')

    def test_frozen_check_set_and_finish_condition_cannot_drift(self):
        for key, value in (('required_checks', ['easier-check']), ('finish_condition', 'Changed target')):
            state = load()
            state['context'][key] = value
            self.assertEqual(workflow.decide(state)['reason'], 'baseline_change_required')

    def test_failed_unrun_missing_or_unsupported_checks_cannot_complete(self):
        for mode in ('failed', 'not_run', 'missing', 'no_evidence'):
            with self.subTest(mode=mode):
                state = load()
                state['stop']['goal_claimed'] = True
                checks = state['reviews'][-1]['checks']
                if mode == 'missing':
                    checks.clear()
                elif mode == 'no_evidence':
                    checks[0]['evidence_record_ids'] = []
                else:
                    checks[0]['status'] = mode
                result = workflow.decide(state)
                self.assertEqual((result['status'], result['reason']), ('blocked', 'checks_not_passed'))
                self.assertFalse(result['verification']['passed'])

    def test_decision_or_skill_record_is_not_check_evidence(self):
        for kind in ('decision', 'skill', 'observation'):
            state = load()
            state['records'][0]['kind'] = kind
            reviewed(state)
            result = workflow.decide(state)
            self.assertEqual(result['reason'], 'checks_not_passed')
            self.assertEqual(result['verification']['checks'][0]['status'], 'unsupported')

    def test_new_failure_overrides_old_completed_receipt(self):
        for conclusion, status in (('accepted', 'failed'), ('changes_requested', 'passed')):
            state = load()
            receipt(state)
            newer = copy.deepcopy(state['reviews'][0])
            newer.update(id='review:newer', conclusion=conclusion)
            newer['checks'][0]['status'] = status
            state['reviews'].append(newer)
            result = workflow.decide(state)
            self.assertEqual(result['status'], 'blocked')
            self.assertNotEqual(result['reason'], 'no_new_evidence')

    def test_reviewer_must_be_distinct_from_recorded_author(self):
        state = load()
        state['reviews'][0]['reviewer']['id'] = state['context']['author']['id']
        self.assertEqual(workflow.decide(state)['reason'], 'reviewer_not_independent')
        state = load()
        state['reviews'][0]['author_id'] = 'different-author'
        self.assertEqual(workflow.decide(state)['reason'], 'reviewer_not_independent')

    def test_same_model_family_is_disclosed_not_faked_as_independence(self):
        state = load()
        state['reviews'][0]['reviewer']['model_family'] = state['context']['author']['model_family']
        result = workflow.decide(state)
        self.assertEqual(result['status'], 'continue')
        self.assertTrue(any('same model family' in warning for warning in result['warnings']))

    def test_no_new_evidence_is_noop_and_exact_duplicates_do_not_retrigger(self):
        state = load()
        receipt(state)
        self.assertEqual(workflow.decide(state)['status'], 'noop')
        original_fingerprint = workflow.context_fingerprint(state)
        duplicate = copy.deepcopy(state['records'][0])
        duplicate.update(id='evidence:duplicate', created_at='2026-11-11T00:00:00Z')
        state['records'].append(duplicate)
        self.assertEqual(workflow.context_fingerprint(state), original_fingerprint)
        self.assertEqual(len(workflow.recall_records(state)), 1)
        self.assertEqual(workflow.decide(state)['status'], 'noop')

    def test_new_source_linked_evidence_requires_fresh_review(self):
        state = load()
        receipt(state)
        add_record(state)
        self.assertEqual(workflow.decide(state)['reason'], 'stale_verification')
        reviewed(state)
        self.assertEqual(workflow.decide(state)['status'], 'continue')

    def test_supersession_excludes_old_answers_and_retains_history(self):
        state = load()
        before = copy.deepcopy(state['records'][0])
        add_record(state, text='Corrected synthetic fact.', supersedes=[before['id']])
        records = workflow.recall_records(state)
        self.assertEqual([record['id'] for record in records], ['evidence:new'])
        self.assertEqual(workflow.recall_records(state, 'declared'), [])
        self.assertEqual(workflow.recall_records(state, 'corrected fact')[0]['id'], 'evidence:new')
        self.assertEqual(state['records'][0], before)
        self.assertEqual(records[0]['source_details'][0]['uri'], 'synthetic://workflow/fixture-v1')

    def test_duplicate_of_superseded_payload_does_not_resurrect_it(self):
        state = load()
        duplicate = copy.deepcopy(state['records'][0])
        duplicate['id'] = 'evidence:old-copy'
        add_record(state, text='Corrected synthetic fact.', supersedes=[state['records'][0]['id']])
        state['records'].append(duplicate)
        self.assertEqual([record['id'] for record in workflow.recall_records(state)], ['evidence:new'])

    def test_explicit_reversion_is_possible_without_deleting_old_records(self):
        state = load()
        original_text = state['records'][0]['text']
        add_record(state, text='Correction.', supersedes=[state['records'][0]['id']])
        add_record(state, identifier='evidence:reversion', text=original_text, supersedes=['evidence:new'])
        self.assertEqual([record['id'] for record in workflow.recall_records(state)], ['evidence:reversion'])

    def test_unrelated_supersession_cannot_revive_a_corrected_payload(self):
        state = load()
        old_text = state['records'][0]['text']
        add_record(state, identifier='evidence:correction', text='Corrected synthetic fact.',
                   supersedes=[state['records'][0]['id']])
        add_record(state, identifier='evidence:unrelated', text='Unrelated synthetic fact.')
        add_record(state, identifier='evidence:bad-reversion', text=old_text,
                   supersedes=['evidence:unrelated'])
        self.assertTrue(any('own correction chain' in error for error in workflow.validate_state(state)[0]))
        self.assertEqual(workflow.decide(state)['reason'], 'invalid_state')

    def test_reference_metadata_and_repeated_refs_do_not_create_new_evidence(self):
        state = load()
        receipt(state)
        before = workflow.context_fingerprint(state)
        duplicate = copy.deepcopy(state['records'][0])
        duplicate['id'] = 'evidence:decorated-copy'
        duplicate['source_refs'][0]['note'] = 'Unrecognized metadata is not evidence.'
        duplicate['source_refs'].append(copy.deepcopy(duplicate['source_refs'][0]))
        state['records'].append(duplicate)
        state['sources'][0]['extra'] = 'Decorative source metadata.'
        state['context']['author']['extra'] = 'Decorative author metadata.'
        self.assertEqual(workflow.context_fingerprint(state), before)
        self.assertEqual(len(workflow.recall_records(state)), 1)
        self.assertEqual(workflow.decide(state)['reason'], 'no_new_evidence')

    def test_superseded_support_is_stale_even_if_review_fingerprint_is_current(self):
        state = load()
        add_record(state, supersedes=[state['records'][0]['id']])
        reviewed(state)
        result = workflow.decide(state)
        self.assertEqual(result['reason'], 'checks_not_passed')
        self.assertEqual(result['verification']['checks'][0]['status'], 'stale')

    def test_unknown_source_and_branching_supersession_are_rejected(self):
        state = load()
        state['records'][0]['source_refs'][0]['source_id'] = 'missing'
        self.assertTrue(workflow.validate_state(state)[0])
        state = load()
        add_record(state, supersedes=[state['records'][0]['id']])
        add_record(state, identifier='evidence:branch', supersedes=[state['records'][0]['id']])
        self.assertTrue(any('branching' in error for error in workflow.validate_state(state)[0]))

    def test_reference_catalog_version_mismatch_is_rejected(self):
        state = load()
        state['sources'][0]['sha256'] = 'b' * 64
        self.assertTrue(any('version mismatch' in error for error in workflow.validate_state(state)[0]))

    def test_checkpoint_pauses_at_30_minutes_without_mutation(self):
        state = load()
        state['usage']['minutes_since_checkpoint'] = 30
        before = copy.deepcopy(state)
        result = workflow.decide(state)
        self.assertEqual((result['status'], result['reason']), ('pause', 'checkpoint_due'))
        self.assertEqual(state, before)
        state['usage']['minutes_since_checkpoint'] = 29
        self.assertEqual(workflow.decide(state)['status'], 'continue')

    def test_all_finite_stop_predicates(self):
        for used, limit, expected in (
            ('iterations_used', 'max_iterations', 'iteration_budget_exhausted'),
            ('elapsed_minutes', 'max_elapsed_minutes', 'elapsed_budget_exhausted'),
            ('no_progress_count', 'max_no_progress', 'no_progress_limit'),
        ):
            state = load()
            state['usage'][used] = state['limits'][limit]
            result = workflow.decide(state)
            self.assertEqual((result['status'], result['reason']), ('stop', expected))
        state = load()
        state['stop'].update(requested=True, reason='Synthetic operator stop.')
        self.assertEqual(workflow.decide(state)['reason'], 'operator_stop')

    def test_receipts_lower_bound_iteration_and_no_progress_counters(self):
        state = load()
        for _ in range(3):
            receipt(state)
        self.assertEqual(state['usage']['iterations_used'], 0)
        self.assertEqual(workflow.decide(state)['reason'], 'iteration_budget_exhausted')
        state = load()
        for _ in range(2):
            receipt(state, 'rejected')
        self.assertEqual(workflow.decide(state)['reason'], 'no_progress_limit')

    def test_goal_boolean_alone_is_not_verified_completion(self):
        state = load()
        state['stop']['goal_claimed'] = True
        state['reviews'] = []
        self.assertEqual(workflow.decide(state)['status'], 'blocked')
        state = load()
        state['stop']['goal_claimed'] = True
        self.assertEqual(workflow.decide(state)['reason'], 'verified_completion_claim')

    def test_production_and_recurring_require_explicit_recorded_flags(self):
        for task, flag, reason in (
            ('lesson_production', 'lesson_production_allowed', 'lesson_production_not_authorized'),
            ('recurring', 'recurring_allowed', 'recurring_not_authorized'),
        ):
            state = load()
            state['scope']['task_kind'] = task
            self.assertEqual(workflow.decide(state)['reason'], reason)
            state['scope'][flag] = True
            self.assertEqual(workflow.decide(state)['reason'], 'budget_agreement_required')
            state['agreement']['budget_fingerprint'] = workflow.budget_fingerprint(state)
            self.assertEqual(workflow.decide(state)['reason'], 'quality_assessment_required')
            reviewed(state)
            result = workflow.decide(state)
            self.assertEqual((result['status'], result['reason']), ('pause', 'quality_assessment_required'))

    def test_fingerprints_ignore_list_order_but_bind_declared_content(self):
        state = load()
        item = copy.deepcopy(state['context']['inputs'][0])
        item['id'] = 'input:second'
        state['context']['inputs'].append(item)
        before = workflow.context_fingerprint(state)
        state['context']['inputs'].reverse()
        self.assertEqual(workflow.context_fingerprint(state), before)
        state['context']['inputs'][0]['sha256'] = 'c' * 64
        self.assertNotEqual(workflow.context_fingerprint(state), before)

    def test_api_is_deterministic_and_does_not_mutate_state(self):
        state = load()
        original = copy.deepcopy(state)
        first = workflow.decide(state)
        self.assertEqual(first, workflow.decide(state))
        workflow.recall_records(state)
        workflow.validate_state(state)
        self.assertEqual(state, original)

    def test_malformed_shapes_missing_keys_and_booleans_are_handled(self):
        cases = [None, [], {}]
        for key in load():
            state = load()
            del state[key]
            cases.append(state)
        for section, key, value in (
            ('limits', 'max_iterations', True), ('usage', 'elapsed_minutes', -1),
            ('context', 'inputs', [None]), ('context', 'author', []),
            ('agreement', 'criteria_agreed', 'yes'),
        ):
            state = load()
            state[section][key] = value
            cases.append(state)
        for state in cases:
            with self.subTest(state=state):
                self.assertEqual(workflow.decide(state)['reason'], 'invalid_state')

    def test_nonfinite_numbers_and_lone_surrogates_are_structural_errors(self):
        cases = []
        for value in (float('inf'), float('-inf'), float('nan'), '\ud800'):
            state = load()
            state['context']['author']['extra'] = value
            cases.append(state)
        state = load()
        state['records'][0]['text'] = '\ud800'
        cases.append(state)
        state = load()
        state['sources'][0]['\ud800'] = 'bad key'
        cases.append(state)
        for state in cases:
            self.assertEqual(workflow.decide(state)['reason'], 'invalid_state')

    def test_cli_rejects_json_overflow_and_surrogates_without_traceback(self):
        state = load()
        encoded = json.dumps(state)
        bad_texts = [
            encoded.replace('"synthetic-author"', '"\\ud800"'),
            encoded.replace('"max_iterations": 3', '"max_iterations": 1e999'),
            encoded.replace('"model_family": "synthetic-family-a"',
                            '"model_family": "synthetic-family-a", "extra": 1e999'),
        ]
        for command in ('validate', 'decide', 'fingerprint', 'recall'):
            for bad_text in bad_texts:
                output = io.StringIO()
                with patch.object(Path, 'read_text', return_value=bad_text), contextlib.redirect_stdout(output):
                    status = workflow.main([command, 'synthetic-state.json'])
                self.assertEqual(status, 2)
                self.assertEqual(json.loads(output.getvalue())['reason'], 'invalid_state')

    def test_actual_cli_rejects_invalid_synthetic_values_without_echoing_them(self):
        encoded = json.dumps(load())
        bad_texts = [encoded.replace('"synthetic": true', '"synthetic": "\\ud800"'),
                     encoded.replace('"synthetic": true', '"synthetic": 1e999')]
        for command in ('validate', 'decide', 'fingerprint', 'recall'):
            for bad_text in bad_texts:
                run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), command, '/dev/stdin'],
                                     input=bad_text, capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(run.stderr, '')
                output = json.loads(run.stdout)
                self.assertEqual(output['reason'], 'invalid_state')
                self.assertIsNone(output['synthetic'])
                self.assertNotIn('Infinity', run.stdout)

    def test_cli_commands_are_json_and_leave_files_unchanged(self):
        tracked = [ROOT / 'examples/workflow.json', ROOT / 'templates/workflow.json', ROOT / 'tools/workflow.py']
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked}
        for command in ('validate', 'decide', 'fingerprint', 'recall'):
            with self.subTest(command=command):
                run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), command,
                                      str(ROOT / 'examples/workflow.json')],
                                     env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                     capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, 0, run.stderr)
                output = json.loads(run.stdout)
                self.assertEqual(output['authority'], 'advisory_only')
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in tracked})

    def test_cli_quality_cycle_survives_restart_and_rechecks_changed_evidence(self):
        import tempfile
        state = load('examples/quality-workflow.json')
        next(item for item in state['context']['inputs'] if item['id'] == 'quality:bundle')['note'] = 'metadata'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            def decide_on_disk():
                path.write_text(json.dumps(state), encoding='utf-8')
                before = path.read_bytes()
                run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), 'decide', str(path),
                                      '--quality', str(ROOT / 'examples/quality.json')],
                                     capture_output=True, text=True, check=False)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(path.read_bytes(), before)
                return json.loads(run.stdout)

            self.assertEqual(decide_on_disk()['reason'], 'verified_candidate_within_budget')
            receipt(state)
            duplicate = copy.deepcopy(state['records'][0])
            duplicate['id'] = 'evidence:restart-copy'
            state['records'].append(duplicate)
            state = json.loads(json.dumps(state))
            self.assertEqual(decide_on_disk()['reason'], 'no_new_evidence')
            add_record(state, text='Synthetic evidence after restart.')
            self.assertEqual(decide_on_disk()['reason'], 'stale_verification')
            reviewed(state)
            self.assertEqual(decide_on_disk()['reason'], 'verified_candidate_within_budget')
            state['usage']['minutes_since_checkpoint'] = state['limits']['checkpoint_minutes']
            self.assertEqual(decide_on_disk()['reason'], 'checkpoint_due')

    def test_cli_missing_file_is_a_json_error(self):
        run = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), 'decide',
                              str(ROOT / 'examples/nonexistent-synthetic-state.json')],
                             capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['reason'], 'unreadable_state')


if __name__ == '__main__':
    unittest.main()
