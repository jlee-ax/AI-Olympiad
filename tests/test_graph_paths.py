"""Synthetic controls plus an exact historical candidate graph regression."""
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
import graph_paths as paths
from validate import validate

CANDIDATE = ROOT / 'tests' / 'fixtures' / 'candidate-graph-missing-path.json'
CLI = ROOT / 'tools' / 'graph_paths.py'


def fixture(root):
    """Fictional tasks and evidence: byte-binding controls, no educational review."""
    document = root / 'lesson.txt'
    document.write_bytes(b'Fictional source, demand, prerequisite, explanation, code, task and feedback.\n')
    digest = hashlib.sha256(document.read_bytes()).hexdigest()
    roles = {role: 'synthetic:' + role for role in paths.ROLES}
    graph = {'nodes': [{'id': value, 'type': 'artifact', 'status': 'proposed', 'label': value}
                       for value in roles.values()],
             'edges': [{'from': roles[a], 'to': roles[b], 'type': 'supports'}
                       for a, b in zip(paths.ROLES, paths.ROLES[1:])]}
    spec = {'schema_version': 1, 'synthetic': True, 'required_demands': [roles['demand']],
            'paths': [{'id': 'synthetic:path', 'comparison_id': 'synthetic:comparison', 'roles': roles,
                       'assessment': {'independent': True, 'allowed_support': 'Fictional: no hints.',
                                      'answer_conditions': 'Fictional: key withheld until submission.'},
                       'provenance': {role: {'path': 'lesson.txt', 'sha256': digest,
                                            'locator': 'Fictional ' + role, 'revision': 'synthetic-v1',
                                            'origin': 'Fictional fixture, not an actual source.'}
                                      for role in paths.ROLES}}]}
    return graph, spec


def codes(result):
    return {entry['code'] for entry in result['errors'] + result['findings']}


def semantic_fixture(graph, spec):
    """Fictional recorded review; no real semantic judgment is fabricated."""
    binding = spec['paths'][0]['provenance']['feedback']
    return {'schema_version': 1, 'synthetic': spec['synthetic'],
            'graph_sha256': paths.canonical_sha256(graph),
            'path_spec_sha256': paths.canonical_sha256(spec),
            'reviewer': {'id': 'fictional-reviewer', 'method': 'Fictional fixture; no content review occurred.'},
            'comparisons': [{'path_id': item['id'], 'comparison_id': item['comparison_id'],
                             **{dimension: {'judgment': 'met', 'rationale': 'Fictional control only.',
                                           'evidence': [{key: binding[key] for key in ('path', 'sha256', 'locator')}]}
                                for dimension in paths.SEMANTIC_DIMENSIONS}}
                            for item in spec['paths']]}


class SemanticReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph, self.spec = fixture(self.root)
        self.review = semantic_fixture(self.graph, self.spec)

    def inspect(self):
        return paths.inspect_semantic_review(self.graph, self.spec, self.review, self.root)

    def test_explicit_current_synthetic_review_preserves_boundary_and_inputs(self):
        before = copy.deepcopy((self.graph, self.spec, self.review))
        result = self.inspect()
        self.assertEqual(result['status'], 'recorded_design_met')
        self.assertEqual(result['verification']['semantics'], 'recorded_judgment_only')
        self.assertEqual(result['verification']['learner_independence'], 'not_observed')
        self.assertEqual(before, (self.graph, self.spec, self.review))
        self.assertEqual(result, self.inspect())

    def test_declaration_complete_cannot_supply_a_missing_content_review(self):
        self.assertEqual(paths.inspect_paths(self.graph, self.spec, self.root)['status'], 'declared_path_complete')
        result = paths.inspect_semantic_review(self.graph, self.spec, None, self.root)
        self.assertEqual(result['status'], 'gap')
        self.assertIn('missing_semantic_review', codes(result))

    def test_known_wrong_generic_feedback_does_not_become_semantically_complete(self):
        # The mechanical checker cannot read meaning from an arbitrary locator.
        binding = self.spec['paths'][0]['provenance']['feedback']
        binding['locator'] = 'Generic recap; contains no answer or repair for this task.'
        self.review = semantic_fixture(self.graph, self.spec)
        feedback = self.review['comparisons'][0]['feedback']
        feedback.update(judgment='gap', rationale='Reviewer found generic recap unrelated to the required problem.')
        self.assertEqual(paths.inspect_paths(self.graph, self.spec, self.root)['status'], 'declared_path_complete')
        self.assertEqual(self.inspect()['status'], 'gap')
        self.assertIn('reviewed_feedback_gap', codes(self.inspect()))

    def test_uncertain_independent_design_remains_uncertain(self):
        self.review['comparisons'][0]['independent_assessment']['judgment'] = 'uncertain'
        self.assertEqual(self.inspect()['status'], 'uncertain')

    def test_each_dimension_and_every_path_requires_a_current_review(self):
        for dimension in paths.SEMANTIC_DIMENSIONS:
            with self.subTest(dimension=dimension):
                review = copy.deepcopy(self.review)
                del review['comparisons'][0][dimension]
                result = paths.inspect_semantic_review(self.graph, self.spec, review, self.root)
                self.assertIn('missing_semantic_dimension', codes(result))
        self.review['comparisons'] = []
        self.assertIn('missing_comparison_review', codes(self.inspect()))

    def test_graph_or_path_changes_invalidate_review_even_with_current_files(self):
        self.graph['nodes'][0]['label'] = 'Changed source meaning.'
        self.assertEqual(self.inspect()['status'], 'stale')
        self.review['graph_sha256'] = paths.canonical_sha256(self.graph)
        self.spec['paths'][0]['assessment']['allowed_support'] = 'Changed support condition.'
        self.assertEqual(self.inspect()['status'], 'stale')

    def test_changed_key_outside_path_bindings_is_stale(self):
        key = self.root / 'key.txt'
        key.write_bytes(b'Fictional problem-specific key.')
        self.review['comparisons'][0]['problem_specific_key']['evidence'] = [
            {'path': key.name, 'sha256': hashlib.sha256(key.read_bytes()).hexdigest(), 'locator': 'key'}]
        self.assertEqual(self.inspect()['status'], 'recorded_design_met')
        key.write_bytes(b'Changed key.')
        self.assertEqual(paths.inspect_paths(self.graph, self.spec, self.root)['status'], 'declared_path_complete')
        self.assertEqual(self.inspect()['status'], 'stale')
        self.assertIn('stale_review_evidence', codes(self.inspect()))

    def test_scope_duplicate_unknown_and_synthetic_mismatch_are_invalid(self):
        for mutate in (lambda r: r['comparisons'].append(copy.deepcopy(r['comparisons'][0])),
                       lambda r: r['comparisons'][0].update(comparison_id='unrelated'),
                       lambda r: r.update(synthetic=False)):
            with self.subTest(mutate=mutate):
                review = copy.deepcopy(self.review)
                mutate(review)
                self.assertEqual(paths.inspect_semantic_review(self.graph, self.spec, review, self.root)['status'], 'invalid')

    def test_review_evidence_requires_locator_safe_regular_file_and_digest(self):
        for name in ('/etc/hosts', '../lesson.txt'):
            review = copy.deepcopy(self.review)
            review['comparisons'][0]['feedback']['evidence'][0]['path'] = name
            self.assertEqual(paths.inspect_semantic_review(self.graph, self.spec, review, self.root)['status'], 'invalid')
        for name in ('missing.txt', '.'):
            review = copy.deepcopy(self.review)
            review['comparisons'][0]['feedback']['evidence'][0]['path'] = name
            self.assertIn('unavailable_review_evidence', codes(paths.inspect_semantic_review(self.graph, self.spec, review, self.root)))
        self.review['comparisons'][0]['feedback']['evidence'][0]['locator'] = ''
        self.assertEqual(self.inspect()['status'], 'gap')

    def test_malformed_review_never_crashes(self):
        for review in ([], {'schema_version': True}, {'extra': float('nan')}, {'extra': chr(0xD800)}):
            with self.subTest(review=review):
                self.assertEqual(paths.inspect_semantic_review(self.graph, self.spec, review, self.root)['status'], 'invalid')


class GraphPathsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph, self.spec = fixture(self.root)

    def inspect(self):
        return paths.inspect_paths(self.graph, self.spec, self.root)

    def test_complete_synthetic_path_is_advisory_current_and_immutable(self):
        before = copy.deepcopy((self.graph, self.spec))
        result = self.inspect()
        self.assertEqual(result['status'], 'declared_path_complete')
        self.assertEqual(result['authority'], 'advisory_only')
        self.assertTrue(result['synthetic'])
        self.assertEqual(len(result['paths'][0]['edges']), 6)
        self.assertEqual(len(result['bindings']), 7)
        self.assertEqual({entry['status'] for entry in result['bindings']}, {'current'})
        self.assertEqual(set(result['verification'].values()), {'not_checked'})
        self.assertIn('undeclared learning requirements', ' '.join(result['limitations']))
        self.assertEqual(before, (self.graph, self.spec))
        self.assertEqual(result, self.inspect())

    def test_real_candidate_is_structurally_valid_but_has_no_declared_path(self):
        graph = json.loads(CANDIDATE.read_text(encoding='utf-8'))
        self.assertEqual(len(graph['nodes']), 12)
        self.assertEqual(len(graph['edges']), 21)
        self.assertEqual(validate(graph), ([], []))
        result = paths.inspect_paths(graph, {}, self.root)
        self.assertEqual(result['status'], 'gap')
        self.assertIn('missing_path_declarations', codes(result))

    def test_real_candidate_cannot_supply_explicit_absent_roles(self):
        self.graph = json.loads(CANDIDATE.read_text(encoding='utf-8'))
        self.spec['paths'][0]['roles']['source'] = 'sample:2026'
        result = self.inspect()
        self.assertEqual(result['status'], 'gap')
        self.assertIn('missing_node', codes(result))
        self.assertIn('missing_edge', codes(result))

    def test_each_missing_adjacent_edge_blocks(self):
        original = copy.deepcopy(self.graph['edges'])
        for i in range(6):
            with self.subTest(edge=i):
                self.graph['edges'] = original[:i] + original[i + 1:]
                result = self.inspect()
                self.assertEqual(result['status'], 'gap')
                self.assertIn('missing_edge', codes(result))

    def test_each_role_is_required(self):
        original = copy.deepcopy(self.spec['paths'][0]['roles'])
        for role in paths.ROLES:
            with self.subTest(role=role):
                self.spec['paths'][0]['roles'] = {key: val for key, val in original.items() if key != role}
                self.assertEqual(self.inspect()['status'], 'gap')

    def test_supports_and_informs_require_forward_orientation(self):
        for kind in ('supports', 'informs'):
            for edge in self.graph['edges']:
                edge['type'] = kind
            self.assertEqual(self.inspect()['status'], 'declared_path_complete')
            edge = self.graph['edges'][0]
            edge['from'], edge['to'] = edge['to'], edge['from']
            self.assertIn('missing_edge', codes(self.inspect()))
            edge['from'], edge['to'] = edge['to'], edge['from']

    def test_depends_on_requires_consumer_to_prerequisite_orientation(self):
        for edge in self.graph['edges']:
            edge['from'], edge['to'] = edge['to'], edge['from']
            edge['type'] = 'depends_on'
        self.assertEqual(self.inspect()['status'], 'declared_path_complete')
        edge = self.graph['edges'][0]
        edge['from'], edge['to'] = edge['to'], edge['from']
        self.assertIn('missing_edge', codes(self.inspect()))

    def test_revises_does_not_supply_learning_edge(self):
        self.graph['edges'][0]['type'] = 'revises'
        self.assertIn('missing_edge', codes(self.inspect()))

    def test_unrelated_transitive_path_cannot_replace_direct_declared_edge(self):
        removed = self.graph['edges'].pop(0)
        self.graph['nodes'].append({'id': 'unrelated', 'type': 'skill', 'status': 'proposed', 'label': 'Unrelated'})
        self.graph['edges'].extend([{'from': removed['from'], 'to': 'unrelated', 'type': 'supports'},
                                    {'from': 'unrelated', 'to': removed['to'], 'type': 'supports'}])
        self.assertIn('missing_edge', codes(self.inspect()))

    def test_empty_scope_and_empty_declarations_never_pass(self):
        for field in ('required_demands', 'paths'):
            with self.subTest(field=field):
                spec = copy.deepcopy(self.spec)
                spec[field] = []
                self.assertNotEqual(paths.inspect(self.graph, spec, self.root)['status'], 'declared_path_complete')

    def test_uncovered_additional_demand_blocks(self):
        self.graph['nodes'].append({'id': 'extra:demand', 'type': 'decision', 'status': 'proposed', 'label': 'Extra'})
        self.spec['required_demands'].append('extra:demand')
        self.assertIn('uncovered_demand', codes(self.inspect()))

    def test_collapsed_role_and_inactive_nodes_block(self):
        self.spec['paths'][0]['roles']['feedback'] = self.spec['paths'][0]['roles']['source']
        self.assertIn('collapsed_roles', codes(self.inspect()))
        self.graph, self.spec = fixture(self.root)
        for status in ('blocked', 'superseded'):
            self.graph['nodes'][0]['status'] = status
            self.assertIn('inactive_node', codes(self.inspect()))

    def test_assessment_conditions_are_required_declarations(self):
        assessment = self.spec['paths'][0].pop('assessment')
        self.assertIn('missing_assessment_conditions', codes(self.inspect()))
        self.spec['paths'][0]['assessment'] = assessment
        assessment['independent'] = False
        self.assertIn('assisted_assessment', codes(self.inspect()))
        assessment['independent'] = 'yes'
        self.assertEqual(self.inspect()['status'], 'invalid')
        assessment['independent'] = True
        del assessment['allowed_support']
        self.assertEqual(self.inspect()['status'], 'gap')

    def test_all_role_provenance_and_metadata_are_required(self):
        declaration = self.spec['paths'][0]
        del declaration['provenance']['feedback']
        self.assertIn('missing_provenance', codes(self.inspect()))
        self.graph, self.spec = fixture(self.root)
        del self.spec['paths'][0]['provenance']['source']['locator']
        self.assertEqual(self.inspect()['status'], 'gap')

    def test_stale_file_blocks_and_restored_exact_bytes_pass(self):
        document = self.root / 'lesson.txt'
        original = document.read_bytes()
        document.write_bytes(original + b'Changed theory.\n')
        result = self.inspect()
        self.assertEqual(result['status'], 'stale')
        self.assertEqual({entry['status'] for entry in result['bindings']}, {'stale'})
        document.write_bytes(original)
        self.assertEqual(self.inspect()['status'], 'declared_path_complete')

    def test_only_changed_neighbor_binding_becomes_stale(self):
        neighbor = self.root / 'neighbor.txt'
        neighbor.write_bytes(b'Neighbor feedback.\n')
        binding = self.spec['paths'][0]['provenance']['feedback']
        binding.update(path='neighbor.txt', sha256=hashlib.sha256(neighbor.read_bytes()).hexdigest())
        self.assertEqual(self.inspect()['status'], 'declared_path_complete')
        neighbor.write_bytes(b'Changed feedback.\n')
        result = self.inspect()
        self.assertEqual(result['status'], 'stale')
        self.assertEqual([item['role'] for item in result['bindings'] if item['status'] == 'stale'], ['feedback'])
        self.assertEqual(sum(item['status'] == 'current' for item in result['bindings']), 6)

    def test_missing_or_directory_binding_never_passes(self):
        binding = self.spec['paths'][0]['provenance']['source']
        for filename in ('missing.txt', '.'):
            binding['path'] = filename
            self.assertIn('unavailable_file', codes(self.inspect()))

    def test_fifo_is_not_opened(self):
        import os
        fifo = self.root / 'not-a-file'
        os.mkfifo(fifo)
        self.spec['paths'][0]['provenance']['source']['path'] = fifo.name
        self.assertIn('unavailable_file', codes(self.inspect()))

    def test_absolute_parent_and_symlink_escape_are_invalid(self):
        binding = self.spec['paths'][0]['provenance']['source']
        for filename in ('/etc/hosts', '../lesson.txt'):
            binding['path'] = filename
            self.assertIn('unsafe_path', codes(self.inspect()))
        (self.root / 'escape').symlink_to(ROOT / 'README.md')
        binding['path'] = 'escape'
        self.assertIn('unsafe_path', codes(self.inspect()))

    def test_invalid_digest_and_bad_schema_are_invalid(self):
        self.spec['paths'][0]['provenance']['source']['sha256'] = 'A' * 64
        self.assertIn('invalid_sha256', codes(self.inspect()))
        self.graph, self.spec = fixture(self.root)
        self.spec['schema_version'] = True
        self.assertEqual(self.inspect()['status'], 'invalid')

    def test_duplicate_ids_and_unknown_roles_are_invalid(self):
        self.spec['paths'].append(copy.deepcopy(self.spec['paths'][0]))
        self.assertIn('duplicate_path', codes(self.inspect()))
        self.spec['paths'].pop()
        self.spec['paths'][0]['roles']['theory'] = 'typo'
        self.assertIn('unknown_role', codes(self.inspect()))

    def test_malformed_objects_report_invalid_without_crashing(self):
        for graph, spec in ((None, {}), ({'nodes': [], 'edges': [None]}, {}), (self.graph, []),
                            (self.graph, {'paths': [None], 'required_demands': [{}]})):
            with self.subTest(graph=graph, spec=spec):
                self.assertEqual(paths.inspect_paths(graph, spec, self.root)['status'], 'invalid')

    def test_shared_json_containers_are_valid_but_cycles_are_invalid(self):
        binding = self.spec['paths'][0]['provenance']['source']
        self.spec['paths'][0]['provenance'] = {role: binding for role in paths.ROLES}
        self.assertEqual(self.inspect()['status'], 'declared_path_complete')
        self.spec['extra'] = self.spec
        self.assertEqual(self.inspect()['status'], 'invalid')

    def test_huge_integer_returns_api_report_without_crashing(self):
        self.graph['extra'] = 10 ** 5000
        limit = getattr(sys, 'get_int_max_str_digits', lambda: 0)()
        expected = 'invalid' if 0 < limit < 5001 else 'declared_path_complete'
        self.assertEqual(self.inspect()['status'], expected)

    def test_malformed_path_status_matches_aggregate(self):
        self.spec['paths'] = [False]
        result = self.inspect()
        self.assertEqual(result['status'], 'invalid')
        self.assertEqual(result['paths'][0]['status'], 'invalid')

    def test_nonfinite_and_surrogate_api_values_are_invalid(self):
        for value in (float('nan'), float('inf'), '\ud800'):
            self.spec['extra'] = value
            self.assertEqual(self.inspect()['status'], 'invalid')

    def test_legacy_feedback_cycle_remains_accepted(self):
        source = self.spec['paths'][0]['roles']['source']
        feedback = self.spec['paths'][0]['roles']['feedback']
        self.graph['edges'].append({'from': feedback, 'to': source, 'type': 'informs'})
        self.assertEqual(validate(self.graph), ([], []))
        self.assertEqual(self.inspect()['status'], 'declared_path_complete')


class GraphPathsCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph, self.spec = fixture(self.root)
        self.graph_file, self.spec_file = self.root / 'graph.json', self.root / 'paths.json'
        self.graph_file.write_text(json.dumps(self.graph), encoding='utf-8')
        self.spec_file.write_text(json.dumps(self.spec), encoding='utf-8')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)],
                              cwd=ROOT, text=True, capture_output=True, check=False)

    def test_complete_missing_edge_stale_and_invalid_exit_codes(self):
        before = (self.graph_file.read_bytes(), self.spec_file.read_bytes())
        args = (self.graph_file, '--spec', self.spec_file, '--root', self.root)
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'declared_path_complete')
        self.assertEqual(before, (self.graph_file.read_bytes(), self.spec_file.read_bytes()))
        (self.root / 'lesson.txt').write_bytes(b'Changed material.')
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'stale')
        self.graph['edges'].pop()
        self.graph_file.write_text(json.dumps(self.graph), encoding='utf-8')
        fixture(self.root)
        result = self.run_cli(*args)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'gap')
        self.spec_file.write_text('{', encoding='utf-8')
        self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_semantic_review_cli_preserves_gap_uncertainty_and_exit_codes(self):
        review = semantic_fixture(self.graph, self.spec)
        review_file = self.root / 'semantic-review.json'
        args = (self.graph_file, '--spec', self.spec_file, '--root', self.root, '--semantic-review', review_file)
        for judgment, expected_status, expected_exit in (('met', 'recorded_design_met', 0),
                                                         ('uncertain', 'uncertain', 1), ('gap', 'gap', 1)):
            review['comparisons'][0]['feedback']['judgment'] = judgment
            review_file.write_text(json.dumps(review), encoding='utf-8')
            result = self.run_cli(*args)
            self.assertEqual(result.returncode, expected_exit, result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], expected_status)
        review_file.write_text('{', encoding='utf-8')
        self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_real_candidate_without_spec_is_gap_not_legacy_failure(self):
        result = self.run_cli(CANDIDATE)
        self.assertEqual(result.returncode, 1)
        self.assertIn('missing_path_declarations', codes(json.loads(result.stdout)))
        legacy = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / 'validate.py'), str(CANDIDATE)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(legacy.returncode, 0)
        self.assertEqual(legacy.stdout.strip(), '0 error(s), 0 warning(s)')

    def test_embedded_spec_and_graph_parent_default_root(self):
        self.graph['path_spec'] = self.spec
        self.graph_file.write_text(json.dumps(self.graph), encoding='utf-8')
        self.assertEqual(self.run_cli(self.graph_file).returncode, 0)

    def test_duplicate_keys_nonfinite_surrogate_and_missing_input_are_invalid(self):
        for text in ('{"schema_version":1,"schema_version":1}', '{"x":NaN}', '{"x":"\\ud800"}'):
            with self.subTest(text=text):
                self.spec_file.write_text(text, encoding='utf-8')
                result = self.run_cli(self.graph_file, '--spec', self.spec_file)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(self.run_cli(self.root / 'missing.json').returncode, 2)
        self.assertEqual(self.run_cli().returncode, 2)


if __name__ == '__main__':
    unittest.main()
