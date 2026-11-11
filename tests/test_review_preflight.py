"""Joined functional checks; fixtures are explicitly synthetic, never learner evidence."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        canonical = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                                            separators=(',', ':')).encode()).hexdigest()
        judgment = {'judgment': 'met', 'rationale': 'Synthetic recorded content review only.',
                    'evidence': [{'path': 'lesson.txt', 'sha256': digest, 'locator': 'Synthetic reviewed content.'}]}
        self.semantic_review = {'schema_version': 1, 'synthetic': True,
                                'graph_sha256': canonical(self.graph), 'path_spec_sha256': canonical(self.paths),
                                'reviewer': {'id': 'synthetic-content-reviewer', 'method': 'Synthetic content review; design only.'},
                                'comparisons': [{'comparison_id': 'comparison:synthetic', 'path_id': 'path:synthetic',
                                                 **{name: copy.deepcopy(judgment) for name in
                                                    ('problem_specific_key', 'feedback', 'independent_assessment')}}]}
        self.state['context']['inputs'].extend(preflight.context_manifests(self.depth, self.graph, self.paths,
                                                                        self.semantic_review, self.state['sources']))
        self.refresh_state()

    def refresh_state(self):
        # Record a fresh synthetic agreement/review, including the full catalog.
        self.state['context']['inputs'] = [item for item in self.state['context']['inputs']
                                          if item['id'] != 'review:source-catalog']
        self.state['context']['inputs'].extend([item for item in preflight.context_manifests(
            self.depth, self.graph, self.paths, self.semantic_review, self.state['sources'])
            if item['id'] == 'review:source-catalog'])
        self.state['frozen'] = workflow.measurement(self.state)
        self.state['agreement']['criteria_fingerprint'] = workflow.criteria_fingerprint(self.state)
        self.state['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(self.state)

    def add_local_source(self, sid, name, reference=False, uri=None):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Pinned synthetic version: ' + sid, encoding='utf-8')
        manifest = {'id': sid, 'revision': 'synthetic-v1', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        self.state['sources'].append({**manifest, 'uri': name if uri is None else uri})
        if reference:
            self.state['context']['references'].append(manifest)
        return path

    def run_check(self):
        return preflight.preflight(self.root, self.depth, self.graph, self.paths, self.state,
                                   semantic_review=self.semantic_review)

    def test_complete_join_and_missing_path_or_unrelated_comparison(self):
        result = self.run_check()
        self.assertEqual(result['status'], 'consistent_recorded_context', result)
        self.assertEqual(result['workflow']['status'], 'continue')
        self.assertTrue(result['bindings'][0]['matched'])
        self.paths['paths'][0]['comparison_id'] = 'another-comparison'
        result = self.run_check()
        self.assertIn(result['status'], ('blocked', 'invalid'))
        self.assertIn('comparison_path_missing', {x['code'] for x in result['blockers']})
        self.paths = {}
        self.assertIn(self.run_check()['status'], ('blocked', 'invalid'))

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
        self.refresh_state()
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
        (self.root / 'source.txt').write_text('Source version two.', encoding='utf-8')
        result = self.run_check()
        self.assertIn('stale_recalled_source', {x['code'] for x in result['blockers']})
        self.assertEqual(len(self.state['history']), 1)

    def test_every_declared_local_reference_is_checked_even_when_not_recalled(self):
        files = [self.add_local_source('source:context-only', 'context-only.txt', reference=True),
                 self.add_local_source('source:catalog-only', 'catalog-only.txt')]
        self.refresh_state()
        before = copy.deepcopy(self.state)
        result = self.run_check()
        self.assertEqual(result['status'], 'consistent_recorded_context', result)
        self.assertEqual({item['source_id'] for item in result['bindings'] if item['kind'] == 'declared_source'},
                         {'source:context-only', 'source:catalog-only'})
        for path in files:
            original = path.read_bytes()
            with self.subTest(path=path.name, case='changed'):
                path.write_bytes(original + b'changed')
                result = self.run_check()
                self.assertEqual(result['status'], 'blocked', result)
                self.assertIn({'code': 'stale_declared_source', 'detail': path.name}, result['blockers'])
                path.write_bytes(original)
            with self.subTest(path=path.name, case='missing'):
                path.unlink()
                result = self.run_check()
                self.assertEqual(result['status'], 'blocked', result)
                self.assertIn('unreadable_declared_source', {item['code'] for item in result['blockers']})
                path.write_bytes(original)
        self.assertEqual(self.state, before)
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')

    def test_unused_catalog_rebinding_requires_a_fresh_aggregate_review(self):
        self.add_local_source('source:catalog-only', 'catalog-v1.txt')
        self.refresh_state()
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
        replacement = self.root / 'catalog-v2.txt'
        replacement.write_bytes(b'A different declared source version.')
        source = self.state['sources'][-1]
        source.update(uri='catalog-v2.txt', revision='synthetic-v2',
                      sha256=hashlib.sha256(replacement.read_bytes()).hexdigest())
        result = self.run_check()
        self.assertEqual(result['workflow']['status'], 'continue')
        self.assertIn('review_context_not_bound', {item['code'] for item in result['blockers']})
        self.state['context']['inputs'] = [item for item in self.state['context']['inputs']
                                          if item['id'] != 'review:source-catalog']
        self.state['context']['inputs'].extend([item for item in result['required_inputs']
                                               if item['id'] == 'review:source-catalog'])
        result = self.run_check()
        self.assertEqual(result['workflow']['reason'], 'stale_verification')
        self.assertEqual(result['status'], 'blocked')
        self.refresh_state()
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')

    def test_superseded_records_keep_immutable_local_source_versions(self):
        old_path = self.add_local_source('source:historical', 'versions/source-v1.txt')
        self.add_local_source('source:current', 'versions/source-v2.txt')
        first = self.state['records'][0]
        first['source_refs'] = [{'source_id': 'source:historical', 'locator': 'Pinned version one.'}]
        self.state['records'].append({**copy.deepcopy(first), 'id': 'record:current',
                                      'text': 'A separately pinned replacement source.',
                                      'source_refs': [{'source_id': 'source:current', 'locator': 'Pinned version two.'}],
                                      'supersedes': [first['id']]})
        self.state['reviews'][-1]['checks'][0]['evidence_record_ids'] = ['record:current']
        self.refresh_state()
        result = self.run_check()
        self.assertEqual(result['status'], 'consistent_recorded_context', result)
        self.assertEqual(result['recall']['record_ids'], ['record:current'])
        kinds = {item.get('source_id'): item['kind'] for item in result['bindings']}
        self.assertEqual(kinds['source:historical'], 'declared_source')
        self.assertEqual(kinds['source:current'], 'recalled_source')
        old_path.write_bytes(old_path.read_bytes() + b'changed historical bytes')
        result = self.run_check()
        self.assertIn('stale_declared_source', {item['code'] for item in result['blockers']})
        self.assertEqual(len(self.state['records']), 2)

    def test_local_file_uris_and_colon_names_are_hashed(self):
        for sid, name, uri in [('source:colon', 'notes:version.txt', 'notes:version.txt'),
                               ('source:space', 'notes version.txt', 'notes version.txt'),
                               ('source:file-relative', 'relative.txt', 'file:relative.txt'),
                               ('source:file-absolute', 'encoded name.txt', (self.root / 'encoded name.txt').as_uri())]:
            with self.subTest(uri=uri):
                path = self.add_local_source(sid, name, uri=uri)
                self.refresh_state()
                self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
                original = path.read_bytes()
                path.write_bytes(original + b'changed')
                result = self.run_check()
                self.assertIn('stale_declared_source', {item['code'] for item in result['blockers']})
                path.write_bytes(original)

    def test_local_sources_cannot_escape_the_selected_root(self):
        source = {'id': 'source:escape', 'revision': 'synthetic-v1', 'sha256': 'a' * 64, 'uri': '../outside.txt'}
        self.state['sources'].append(source)
        for uri in ('../outside.txt', '/etc/hosts', 'file:///etc/hosts', 'file:../outside.txt',
                    'file:%2e%2e/outside.txt', 'file://remote-host/path', 'file:source.txt?revision=1',
                    'file:source.txt#fragment', 'file:%ZZ', 'file:', 'https:missing-host', 'https://',
                    'https://example.org:bad/path', 'https://[malformed'):
            with self.subTest(uri=uri):
                source['uri'] = uri
                result = self.run_check()
                self.assertEqual(result['status'], 'blocked', result)
                self.assertIn('unreadable_declared_source', {item['code'] for item in result['blockers']})
                self.assertNotIn('source:escape', {item.get('source_id') for item in result['bindings']})
        with tempfile.TemporaryDirectory() as outside:
            escaped = Path(outside) / 'secret.txt'
            escaped.write_bytes(b'not inside root')
            (self.root / 'escape').symlink_to(escaped)
            source['uri'] = 'escape'
            self.assertIn('unreadable_declared_source', {item['code'] for item in self.run_check()['blockers']})
            source['uri'] = (self.root / 'escape').as_uri()
            self.assertIn('unreadable_declared_source', {item['code'] for item in self.run_check()['blockers']})

    def test_remote_sources_and_pathless_manifests_are_explicitly_unverified(self):
        self.state['sources'].append({'id': 'source:remote', 'revision': 'remote-v1', 'sha256': 'a' * 64,
                                      'uri': 'https://example.invalid/source.json'})
        # A manifest id is not a filesystem path and must not be guessed into one.
        self.state['context']['inputs'].append({'id': 'missing-input.txt', 'revision': 'v1', 'sha256': 'b' * 64})
        self.refresh_state()
        with mock.patch('urllib.request.urlopen', side_effect=AssertionError('No remote fetch is permitted')):
            result = self.run_check()
        self.assertEqual(result['status'], 'consistent_recorded_context', result)
        self.assertIn({'id': 'source:remote', 'uri': 'https://example.invalid/source.json',
                       'reason': 'external_uri_not_fetched'}, result['unverified_sources'])
        self.assertNotIn('missing-input.txt', {item['path'] for item in result['bindings']})

    def test_semantic_review_is_required_and_bound_to_the_aggregate_context(self):
        result = preflight.preflight(self.root, self.depth, self.graph, self.paths, self.state)
        self.assertEqual(result['status'], 'blocked', result)
        self.assertIn('missing_semantic_review', {item['code'] for item in result['blockers']})
        self.semantic_review['comparisons'][0]['feedback']['rationale'] = 'A revised content judgment requires review.'
        result = self.run_check()
        self.assertIn('review_context_not_bound', {item['code'] for item in result['blockers']})
        self.state['context']['inputs'] = [item for item in self.state['context']['inputs']
                                          if item['id'] != 'review:semantic-review']
        self.state['context']['inputs'].extend([item for item in preflight.context_manifests(
            self.depth, self.graph, self.paths, self.semantic_review) if item['id'] == 'review:semantic-review'])
        self.assertEqual(self.run_check()['workflow']['reason'], 'stale_verification')
        self.refresh_state()
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
        self.semantic_review['comparisons'][0]['feedback']['judgment'] = 'uncertain'
        result = self.run_check()
        self.assertIn('semantic_review_uncertain', {item['code'] for item in result['blockers']})

    def test_changed_review_declarations_cannot_reuse_old_aggregate_review(self):
        self.depth['comparisons'][0]['rationale'] = 'A newly recorded rationale needs review.'
        result = self.run_check()
        self.assertIn('review_context_not_bound', {x['code'] for x in result['blockers']})
        self.state['context']['inputs'] = [x for x in self.state['context']['inputs'] if not x['id'].startswith('review:')]
        self.state['context']['inputs'].extend(preflight.context_manifests(self.depth, self.graph, self.paths, self.semantic_review, self.state['sources']))
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
        entries = {'depth.json': self.depth, 'graph.json': self.graph, 'paths.json': self.paths, 'state.json': self.state,
                   'semantic-review.json': self.semantic_review}
        for name, value in entries.items():
            (self.root / name).write_text(json.dumps(value), encoding='utf-8')
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        command = [sys.executable, '-B', str(ROOT / 'tools/review_preflight.py'), '--root', str(self.root),
                   '--depth', 'depth.json', '--graph', 'graph.json', '--state', 'state.json',
                   '--semantic-review', 'semantic-review.json']
        result = subprocess.run(command + ['--paths', 'paths.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'consistent_recorded_context')
        result = subprocess.run(command[:-2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'blocked')
        result = subprocess.run(command[:-2] + ['--paths', 'paths.json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('missing_semantic_review', {item['code'] for item in json.loads(result.stdout)['blockers']})
        self.assertEqual({p.name: p.read_bytes() for p in self.root.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
