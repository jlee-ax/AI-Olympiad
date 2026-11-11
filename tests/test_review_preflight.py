"""Joined functional checks; fixtures are explicitly synthetic, never learner evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import review_preflight as preflight
import workflow
from test_contest_depth import synthetic_bundle

ROLES = ('source', 'demand', 'prerequisite', 'theory_explanation', 'coding_practice',
         'independent_assessment', 'feedback')


class ReviewPreflightTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'lesson.txt').write_text('Synthetic introductory lesson, no learning claims.', encoding='utf-8')
        digest = hashlib.sha256((self.root / 'lesson.txt').read_bytes()).hexdigest()
        self.depth = synthetic_bundle()
        self.depth['target'].update(artifact='lesson.txt', artifact_sha256=digest)
        self.state = json.loads((ROOT / 'examples/workflow.json').read_text())
        self.state['context']['artifact']['sha256'] = digest
        self.state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(self.state)
        self.graph = {'nodes': [{'id': r, 'type': 'evidence', 'status': 'verified', 'label': r} for r in ROLES],
                      'edges': [{'from': a, 'to': b, 'type': 'supports'} for a, b in zip(ROLES, ROLES[1:])]}
        self.paths = {'schema_version': 1, 'synthetic': True, 'required_demands': ['demand'], 'paths': [{
            'id': 'path:synthetic', 'comparison_id': 'comparison:synthetic', 'roles': {r: r for r in ROLES},
            'provenance': {r: {'path': 'lesson.txt', 'sha256': digest, 'locator': 'synthetic fixture',
                                'revision': 'synthetic-v1', 'origin': 'synthetic author'} for r in ROLES},
            'assessment': {'independent': True, 'allowed_support': 'None in the fixture.',
                           'answer_conditions': 'Answers withheld in the fixture.'}}]}
        self.state['context']['inputs'].extend(preflight.context_manifests(self.depth, self.graph, self.paths))
        self.state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(self.state)

    def run_check(self):
        return preflight.preflight(self.root, self.depth, self.graph, self.paths, self.state)

    def test_complete_join_and_missing_path_or_unrelated_comparison(self):
        result = self.run_check()
        self.assertEqual(result['status'], 'consistent_recorded_context', result)
        self.assertEqual(result['workflow']['status'], 'continue')
        self.assertTrue(result['bindings'][0]['matched'])
        self.paths['paths'][0]['comparison_id'] = 'another-comparison'
        result = self.run_check()
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('comparison_path_missing', {x['code'] for x in result['blockers']})
        self.paths = {}
        self.assertEqual(self.run_check()['status'], 'blocked')

    def test_missing_edge_and_nonindependent_assessment_block(self):
        old = copy.deepcopy(self.graph)
        self.graph['edges'].pop(3)
        self.assertEqual(self.run_check()['status'], 'blocked')
        self.graph = old
        self.paths['paths'][0]['assessment']['independent'] = False
        self.assertEqual(self.run_check()['status'], 'blocked')

    def test_actual_file_change_and_old_state_block_without_mutation(self):
        before = copy.deepcopy((self.depth, self.graph, self.paths, self.state))
        (self.root / 'lesson.txt').write_text('Changed lesson bytes.', encoding='utf-8')
        result = self.run_check()
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('stale_artifact', {x['code'] for x in result['blockers']})
        self.assertIn('workflow_artifact_stale', {x['code'] for x in result['blockers']})
        self.assertEqual((self.depth, self.graph, self.paths, self.state), before)

    def test_recall_detects_changed_local_source_and_restart_preserves_noop(self):
        receipt = {'id': 'synthetic-receipt', 'context_fingerprint': workflow.context_fingerprint(self.state),
                   'outcome': 'accepted', 'reason': 'Synthetic completed attempt only.'}
        self.state['history'].append(receipt)
        self.state = json.loads(json.dumps(self.state))
        self.assertEqual(self.run_check()['workflow']['status'], 'noop')
        source = self.state['sources'][0]
        source['uri'] = 'source.txt'
        (self.root / 'source.txt').write_text('Source version one.', encoding='utf-8')
        source['sha256'] = hashlib.sha256((self.root / 'source.txt').read_bytes()).hexdigest()
        # A changed reference config requires a new synthetic baseline/agreement,
        # then a fresh review. The old attempt remains immutable history.
        self.state['context']['references'][0]['sha256'] = source['sha256']
        self.state['frozen'] = workflow.measurement(self.state)
        self.state['agreement']['criteria_fingerprint'] = workflow.criteria_fingerprint(self.state)
        self.state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(self.state)
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
        (self.root / 'source.txt').write_text('Source version two.', encoding='utf-8')
        result = self.run_check()
        self.assertIn('stale_recalled_source', {x['code'] for x in result['blockers']})
        self.assertEqual(len(self.state['history']), 1)

    def test_changed_review_declarations_cannot_reuse_old_aggregate_review(self):
        self.depth['comparisons'][0]['rationale'] = 'A newly recorded rationale needs review.'
        result = self.run_check()
        self.assertIn('review_context_not_bound', {x['code'] for x in result['blockers']})
        self.state['context']['inputs'] = [x for x in self.state['context']['inputs'] if not x['id'].startswith('review:')]
        self.state['context']['inputs'].extend(preflight.context_manifests(self.depth, self.graph, self.paths))
        result = self.run_check()
        self.assertEqual(result['workflow']['reason'], 'stale_verification')
        self.assertEqual(result['status'], 'blocked')
        self.state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(self.state)
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')

    def test_unresolvable_local_path_does_not_raise(self):
        (self.root / 'loop').symlink_to('loop')
        self.depth['target']['artifact'] = 'loop'
        result = self.run_check()
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('unreadable_artifact', {x['code'] for x in result['blockers']})

    def test_malformed_nested_objects_are_invalid(self):
        self.depth['target'] = []
        self.assertEqual(self.run_check()['status'], 'invalid')

    def test_nonarray_comparisons_never_raise_or_pass(self):
        for value in (None, 1, 'bad', {}):
            self.depth['comparisons'] = value
            self.assertIn(self.run_check()['status'], ('blocked', 'invalid'))

    def test_cli_reads_all_inputs_and_returns_blocked_exit(self):
        entries = {'depth.json': self.depth, 'graph.json': self.graph, 'paths.json': self.paths, 'state.json': self.state}
        for name, value in entries.items():
            (self.root / name).write_text(json.dumps(value), encoding='utf-8')
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        command = [sys.executable, '-B', str(ROOT / 'tools/review_preflight.py'), '--root', str(self.root),
                   '--depth', 'depth.json', '--graph', 'graph.json', '--state', 'state.json']
        result = subprocess.run(command + ['--paths', 'paths.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'consistent_recorded_context')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'blocked')
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
