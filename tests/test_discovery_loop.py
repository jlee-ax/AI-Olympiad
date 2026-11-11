"""Real file I/O with explicitly synthetic semantic assertions; no learner evidence."""
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
import discovery_loop as loop
import quality
import workflow
from test_quality import normal_bundle
import test_review_preflight as joined_tests


def configuration(synthetic=True, readiness='scoped_foundation'):
    return {'schema_version': 1, 'synthetic': synthetic,
            'scope': {'id': 'unit:foundation', 'lesson_path': 'lesson.txt', 'lesson_revision': 'fixture-v1',
                      'readiness': readiness, 'boundary': 'One introductory unit; later course demands remain staged.'},
            'frontier': [{'id': 'probe:external', 'question': 'Which observable reasoning is required outside the lesson?',
                          'required_kinds': ['official_problem']}],
            'policy': {'max_events': 80, 'max_rounds': 12, 'max_no_progress': 5, 'max_elapsed_minutes': 180}}


class DiscoveryLoopTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'source.txt').write_text('Synthetic external task.\nExplain the flume invariant.\nPredict an unseen transformation without supplied answers.\n')
        (self.root / 'lesson.txt').write_text('Interpret the input.\nExplain why the invariant is preserved.\nPredict a new case and justify the answer without support.\n')
        (self.root / 'plan.txt').write_text('Later unit owns advanced transfer after the foundation.\n')
        self.state = loop.initialize(configuration())
        self.counter = 0

    def event(self, op, **data):
        self.counter += 1
        return {'id': 'event:' + str(self.counter), 'op': op,
                'data': {'reason': 'Synthetic observable control.', **data}}

    def apply(self, op, **data):
        event = self.event(op, **data)
        self.state = loop.step(self.state, event, self.root)
        return event['id']

    def source(self, sid='source:external', revision='fixture-v1', kind='official_problem'):
        return {'id': sid, 'uri': 'https://example.invalid/synthetic-external-task', 'path': 'source.txt',
                'revision': revision, 'kind': kind, 'attribution': 'Synthetic official attribution, not authenticated.'}

    def demand(self, did='demand:flume'):
        return {'id': did, 'statement': 'Preserve the flume invariant on an unseen transformation.',
                'prerequisites': ['Interpret the input'], 'learning_demand': 'Explain why the transformation preserves the invariant.',
                'assessment_demand': 'Predict and justify a new transformation without supplied answers.'}

    def seed_demand(self, demand=None, frontier='probe:external', source=None):
        source = source or self.source()
        self.apply('discover', frontier_id=frontier, query='Original task and external reasoning', actor='discoverer',
                   outcome='found', candidates=[source])
        rid = self.apply('read', source_id=source['id'], actor='reader', start_line=1, end_line=3)
        self.apply('trace', frontier_id=frontier, read_ids=[rid], actor='extractor',
                   rationale='The task needs an invariant, not just terminology.', counterevidence='Synthetic example only, no population result.',
                   uninvestigated=[], demands=[demand or self.demand()])
        return rid

    def compare(self, did='demand:flume', overall='covered', assessment='met', **extra):
        data = {'demand_id': did, 'reviewer': 'independent-reviewer', 'judgment': overall,
                'rationale': 'Synthetic direct comparison of observable demands.', 'start_line': 1, 'end_line': 3}
        if overall not in ('deferred', 'out_of_scope'):
            data['dimensions'] = [{'id': name, 'judgment': assessment if name == 'assessment' else 'met',
                                   'observed_behavior': 'Synthetic observed lesson behavior for ' + name,
                                   'rationale': 'Synthetic independent content judgment, not authenticated.',
                                   'start_line': n, 'end_line': n}
                                  for n, name in enumerate(('prerequisites', 'learning', 'assessment'), 1)]
        data.update(extra)
        return self.apply('compare', **data)

    def report(self):
        return loop.inspect(self.state, self.root)

    def ready(self):
        self.seed_demand()
        self.compare()
        self.assertTrue(self.report()['ready_for_review'])

    def test_external_demand_enters_queue_before_declared_lesson_checks_can_close_it(self):
        self.assertEqual(self.report()['next_action'], 'discover_original_sources')
        self.seed_demand()
        report = self.report()
        self.assertEqual(report['queue'][0]['demand_id'], 'demand:flume')
        self.assertEqual(report['queue'][0]['next_action'], 'compare_actual_lesson')
        before = copy.deepcopy(self.state)
        self.compare(assessment='gap')
        report = self.report()
        self.assertIn('dimension_assessment_gap', report['queue'][0]['reasons'])
        self.assertFalse(report['ready_for_review'])
        self.assertEqual(self.state['events'][:-1], before['events'])
        self.compare()
        self.assertEqual(self.report()['status'], 'recorded_ready')

    def test_next_action_advances_discovery_read_trace_and_compare_stages(self):
        self.apply('discover', frontier_id='probe:external', query='Find original external demand', actor='discoverer',
                   outcome='found', candidates=[self.source()])
        self.assertEqual(self.report()['next_action'], 'read_discovered_sources')
        rid = self.apply('read', source_id='source:external', actor='reader', start_line=1, end_line=3)
        self.assertEqual(self.report()['next_action'], 'trace_source_requirements')
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Observable external task.',
                   counterevidence='No learner outcome claim.', uninvestigated=[], demands=[self.demand()])
        self.assertEqual(self.report()['next_action'], 'compare_actual_lesson')
        self.compare(assessment='gap')
        self.assertEqual(self.report()['next_action'], 'research_or_refine_and_recompare')

    def test_new_arbitrary_frontier_invalidates_previous_ready_and_manifest(self):
        self.ready()
        old = loop.manifest(self.state)
        self.apply('frontier', probe={'id': 'probe:heldout', 'question': 'Track the ordering of opaque tokens.',
                                      'required_kinds': ['official_problem']})
        self.assertFalse(self.report()['ready_for_review'])
        self.assertNotEqual(loop.manifest(self.state), old)
        d = self.demand('demand:unseen-token-order')
        d['statement'] = 'Recover the order of an unseen opaque token sequence.'
        self.seed_demand(d, frontier='probe:heldout')
        self.assertEqual(self.report()['queue'][0]['demand_id'], d['id'])
        self.compare(did=d['id'], assessment='uncertain')
        self.assertFalse(self.report()['ready_for_review'])

    def test_new_candidate_is_an_obligation_even_after_same_kind_was_traced(self):
        self.ready()
        new_source = self.source('source:additional', revision='different-declared-version')
        self.apply('discover', frontier_id='probe:external', query='A second original source', actor='discoverer',
                   outcome='found', candidates=[new_source])
        codes = {b['code'] for b in self.report()['blockers']}
        self.assertIn('discovered_source_unread', codes)
        self.assertIn('discovered_source_untraced', codes)

    def test_empty_extraction_does_not_close_frontier(self):
        rid = self.seed_demand()
        # A separate valid initial session with an empty trace cannot claim readiness.
        fresh = loop.initialize(configuration())
        for event in self.state['events'][:2]:
            data = copy.deepcopy(event['data'])
            if event['op'] == 'read':
                data.update(start_line=1, end_line=3)
            fresh = loop.step(fresh, {'id': event['id'], 'op': event['op'], 'data': data}, self.root)
        event = self.event('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor',
                           rationale='No relevant demand found in the sampled reading.', counterevidence='Other sections remain possible.',
                           uninvestigated=[], demands=[])
        fresh = loop.step(fresh, event, self.root)
        self.assertIn('frontier_no_demands_requires_review', {b['code'] for b in loop.inspect(fresh, self.root)['blockers']})

    def test_uninvestigated_question_persists_and_expands_to_new_obligation(self):
        rid = self.seed_demand()
        self.compare()
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='A new question surfaced.',
                   counterevidence='No resolution yet.', uninvestigated=['Opaque parity remains unchecked.'], demands=[])
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Routine re-read.',
                   counterevidence='No additional evidence.', uninvestigated=[], demands=[])
        report = self.report()
        self.assertEqual(report['next_action'], 'expand_frontier')
        qid = report['open_questions'][0]['id']
        self.apply('frontier', probe={'id': 'probe:parity', 'question': 'Resolve opaque parity.',
                                      'required_kinds': ['official_problem']}, resolves=[qid])
        self.assertEqual(self.report()['open_questions'], [])
        self.assertFalse(self.report()['ready_for_review'])
        self.assertIn('probe:parity', [b['id'] for b in self.report()['blockers']])

    def test_background_question_also_blocks_required_official_frontier(self):
        self.ready()
        source = self.source('source:background', kind='background')
        self.apply('discover', frontier_id='probe:external', query='Counterexample investigation', actor='discoverer', outcome='found', candidates=[source])
        rid = self.apply('read', source_id=source['id'], actor='reader', start_line=1, end_line=3)
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Potential counterexample.',
                   counterevidence='Needs external check.', uninvestigated=['Background exception unresolved.'], demands=[])
        self.assertFalse(self.report()['ready_for_review'])
        self.assertIn('uninvestigated_requirement', {b['code'] for b in self.report()['blockers']})

    def test_custom_dimension_cannot_replace_learning_and_independent_assessment(self):
        demand = self.demand()
        demand['dimensions'] = [{'id': 'terminology', 'required_behavior': 'Recognize the term.'}]
        self.seed_demand(demand)
        dimensions = [{'id': 'terminology', 'judgment': 'met', 'observed_behavior': 'The term occurs.',
                       'rationale': 'Synthetic shallow observation.', 'start_line': 1, 'end_line': 1}]
        with self.assertRaisesRegex(ValueError, 'every demand-specific'):
            self.compare(dimensions=dimensions)
        dimensions = [{'id': x['id'], 'judgment': 'gap' if x['id'] == 'assessment' else 'met',
                       'observed_behavior': 'Only guided recognition.', 'rationale': 'No unaided task evidence.',
                       'start_line': 1, 'end_line': 3} for x in loop.demand_dimensions(demand)]
        self.compare(dimensions=dimensions)
        self.assertIn('dimension_assessment_gap', self.report()['queue'][0]['reasons'])

    def test_foundational_deferred_placement_is_scoped_and_course_claim_stays_blocked(self):
        self.seed_demand()
        self.compare(overall='deferred', scope_basis='This unit builds the entry prerequisite before later transfer.',
                     placement={'unit_id': 'later:transfer', 'path': 'plan.txt', 'start_line': 1, 'end_line': 1,
                                'owner': 'course-reviewer', 'rationale': 'Accountable planned later unit, not observed mastery.'})
        self.assertTrue(self.report()['ready_for_review'])
        state = copy.deepcopy(self.state)
        state['seed']['scope']['readiness'] = 'course'
        # This is a separate explicit baseline, not a silent modification of a bound session.
        fresh = loop.initialize(state['seed'])
        for old in state['events']:
            data = copy.deepcopy(old['data'])
            if old['op'] == 'read':
                data.update(start_line=1, end_line=3)
            if old['op'] == 'compare':
                data.update(start_line=1, end_line=3)
                receipt = data['placement'].pop('receipt')
                data['placement'].update(path=receipt['path'], start_line=1, end_line=1)
            fresh = loop.step(fresh, {'id': old['id'], 'op': old['op'], 'data': data}, self.root)
        self.assertIn('deferred_is_not_course_readiness', loop.inspect(fresh, self.root)['queue'][0]['reasons'])
        (self.root / 'plan.txt').write_text('Changed placement after review.\n')
        self.assertFalse(self.report()['ready_for_review'])

    def test_source_change_can_be_explicitly_retraced_and_superseded(self):
        self.ready()
        (self.root / 'source.txt').write_text('Revised external source.\nThe invariant now has a restriction.\nPredict under that restriction.\n')
        self.assertFalse(self.report()['ready_for_review'])
        source = self.source('source:external-v2', revision='fixture-v2')
        self.seed_demand(self.demand('demand:flume-v2'), source=source)
        self.apply('supersede_source', old_source_id='source:external', new_source_id=source['id'], reviewer='independent-reviewer')
        self.apply('supersede', old_demand_id='demand:flume', new_demand_id='demand:flume-v2', reviewer='independent-reviewer',
                   dimension_dispositions=[{'old_dimension_id': name, 'new_dimension_id': name, 'judgment': 'preserved',
                                            'rationale': 'Synthetic explicit before/after preservation review.'}
                                           for name in ('prerequisites', 'learning', 'assessment')])
        self.compare(did='demand:flume-v2')
        report = self.report()
        self.assertTrue(report['ready_for_review'], report)
        self.assertTrue(report['historical_stale_read_ids'])
        self.assertEqual(len(report['demands']), 2)

    def test_immutable_old_source_cannot_keep_active_demand_current_after_supersession(self):
        self.ready()
        source = self.source('source:new-version', revision='fixture-v2')
        self.apply('discover', frontier_id='probe:external', query='Updated governing version', actor='discoverer', outcome='found', candidates=[source])
        rid = self.apply('read', source_id=source['id'], actor='reader', start_line=1, end_line=3)
        successor = self.demand('demand:version-two')
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Updated version requires a new context.',
                   counterevidence='Original snapshot remains immutable.', uninvestigated=[], demands=[successor])
        self.compare(did=successor['id'])
        self.apply('supersede_source', old_source_id='source:external', new_source_id=source['id'], reviewer='independent-reviewer')
        report = self.report()
        self.assertFalse(report['ready_for_review'])
        old = next(q for q in report['queue'] if q['demand_id'] == 'demand:flume')
        self.assertIn('source_superseded_retrace_required', old['reasons'])
        self.assertEqual(report['historical_stale_read_ids'], [])

    def test_lesson_change_reopens_current_dimensions_and_recompare_can_resolve(self):
        self.ready()
        (self.root / 'lesson.txt').write_text('Updated input interpretation.\nUpdated invariant derivation.\nUpdated independent transfer problem.\n')
        self.assertIn('lesson_changed_review_required', self.report()['queue'][0]['reasons'])
        self.compare()
        self.assertTrue(self.report()['ready_for_review'])

    def test_pause_resume_and_previous_comparison_can_be_repeated(self):
        self.ready()
        self.apply('pause', reason='Checkpoint')
        self.assertEqual(self.report()['status'], 'paused')
        with self.assertRaisesRegex(ValueError, 'Paused'):
            self.compare()
        self.apply('resume', reason='Continue within the same cumulative budget')
        self.apply('pause', reason='Checkpoint')
        self.assertEqual(self.report()['status'], 'paused')
        self.apply('resume', reason='Continue within the same cumulative budget')
        self.compare(assessment='gap')
        self.assertFalse(self.report()['ready_for_review'])
        self.compare()
        self.assertTrue(self.report()['ready_for_review'])

    def test_retry_is_idempotent_but_alias_searches_do_not_count_as_progress(self):
        self.ready()
        event = self.event('discover', frontier_id='probe:external', query='Original task and external reasoning',
                           actor='discoverer', outcome='found', candidates=[self.source()])
        self.state = loop.step(self.state, event, self.root)
        self.assertEqual(self.report()['usage']['no_progress'], 1)
        self.assertEqual(loop.step(self.state, event, self.root), self.state)
        for n in range(2):
            self.apply('discover', frontier_id='probe:external', query='Search same source again', actor='discoverer',
                       outcome='found', candidates=[self.source('source:alias' + str(n))])
        self.assertEqual(self.report()['usage']['no_progress'], 3)

    def test_duplicate_demand_has_explicit_alias_and_does_not_expand_queue(self):
        rid = self.seed_demand()
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Unchanged reading.',
                   counterevidence='Same scoped evidence.', uninvestigated=[], demands=[self.demand('demand:alias')])
        report = self.report()
        self.assertEqual(len(report['demands']), 1)
        self.assertEqual(report['demand_aliases']['demand:alias'], 'demand:flume')
        self.compare(did='demand:alias')
        self.assertTrue(self.report()['ready_for_review'])

    def test_finite_no_result_round_and_elapsed_limits_survive_json_restart(self):
        self.state['seed']['policy']['max_no_progress'] = 2
        self.state = loop.initialize(self.state['seed'])
        for n in range(2):
            self.apply('discover', frontier_id='probe:external', query='Unavailable original source ' + str(n),
                       actor='discoverer', outcome='unavailable', candidates=[], minutes=4)
        self.state = json.loads(json.dumps(self.state))
        report = self.report()
        self.assertEqual(report['status'], 'stopped')
        self.assertEqual(report['usage']['elapsed_minutes'], 8)
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            self.apply('resume')
        for key in ('max_events', 'max_rounds', 'max_elapsed_minutes'):
            with self.subTest(limit=key):
                cfg = configuration()
                cfg['policy'][key] = 1
                state = loop.initialize(cfg)
                event = self.event('discover', frontier_id='probe:external', query='Budget control', actor='discoverer',
                                   outcome='no_results', candidates=[], minutes=1)
                self.assertEqual(loop.inspect(loop.step(state, event, self.root), self.root)['status'], 'stopped')

    def test_history_and_seed_shrink_are_detected_and_paths_are_confined(self):
        self.ready()
        broken = copy.deepcopy(self.state)
        broken['events'].pop(1)
        with self.assertRaisesRegex(ValueError, 'Broken event chain'):
            loop.inspect(broken, self.root)
        broken = copy.deepcopy(self.state)
        broken['seed']['frontier'] = []
        with self.assertRaises(ValueError):
            loop.inspect(broken, self.root)
        for name in ('../escape', '/etc/passwd'):
            with self.subTest(path=name), self.assertRaises(ValueError):
                loop.read_span(self.root, name, 1, 1)
        (self.root / 'outside').symlink_to(ROOT / 'AGENTS.md')
        with self.assertRaises(ValueError):
            loop.read_span(self.root, 'outside', 1, 1)

    def test_arbitrary_semantic_assertion_is_explicitly_a_declaration(self):
        (self.root / 'lesson.txt').write_text('Mention flume.\nMention flume.\nMention flume.\n')
        self.ready()  # Deliberately false semantic declarations remain beyond a mechanical validator.
        report = self.report()
        self.assertTrue(any('semantic' in line and 'human or model' in line for line in report['limits']))
        self.assertIn('sampled frontier', report['bounded_scope_condition'])
        self.compare(assessment='gap')  # An actual reviewer distinguishes naming from unaided transfer.
        self.assertFalse(self.report()['ready_for_review'])

    def test_new_read_ids_do_not_invent_new_demands_or_allow_alias_id_reuse(self):
        self.seed_demand()
        for n in range(2):
            rid = self.apply('read', source_id='source:external', actor='reader', start_line=1, end_line=3)
            self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Same exact evidence.',
                       counterevidence='No changed source content.', uninvestigated=[], demands=[self.demand('alias:' + str(n))])
        self.assertEqual(len(self.report()['demands']), 1)
        self.assertEqual(self.report()['usage']['no_progress'], 2)
        changed = self.demand('alias:0')
        changed['assessment_demand'] = 'A different substantive task.'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Try alias ID mutation.',
                       counterevidence='The alias must remain immutable.', uninvestigated=[], demands=[changed])

    def test_prefix_budget_exhaustion_cannot_be_erased_by_raw_append(self):
        self.ready()
        config = copy.deepcopy(self.state['seed'])
        config['policy']['max_no_progress'] = 1
        state = loop.initialize(config)
        # Replay the same authorized prefix under its explicit smaller budget.
        for old in self.state['events']:
            data = copy.deepcopy(old['data'])
            if old['op'] == 'read':
                data.update(start_line=1, end_line=3)
            if old['op'] == 'compare':
                data.update(start_line=1, end_line=3)
                for dimension in data['dimensions']:
                    dimension.update(start_line=dimension['receipt']['start_line'], end_line=dimension['receipt']['end_line'])
            state = loop.step(state, {'id': old['id'], 'op': old['op'], 'data': data}, self.root)
        duplicate = self.event('discover', frontier_id='probe:external', query='Same source', actor='discoverer', outcome='found', candidates=[self.source()])
        state = loop.step(state, duplicate, self.root)
        self.assertEqual(loop.inspect(state, self.root)['status'], 'stopped')
        raw = self.event('trace', frontier_id='probe:external', read_ids=[state['events'][1]['id']], actor='extractor',
                         rationale='Raw post-stop append tries to reset progress.', counterevidence='No worker authorized this.',
                         uninvestigated=[], demands=[self.demand('demand:post-stop')])
        previous = state['events'][-1]['sha256']
        state['events'].append({**raw, 'previous_sha256': previous, 'sha256': loop.digest({'previous_sha256': previous, **raw})})
        with self.assertRaisesRegex(ValueError, 'after finite budget exhaustion'):
            loop.inspect(state, self.root)

    def test_unresolved_dimension_retirement_is_reviewable_and_recoverable(self):
        rid = self.seed_demand()
        self.compare(assessment='gap')
        updated = self.demand('demand:successor')
        updated['statement'] += ' Explicit successor revision.'
        self.apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor', rationale='Refined requirement.',
                   counterevidence='Old assessment gap remains until mapped.', uninvestigated=[], demands=[updated])
        with self.assertRaisesRegex(ValueError, 'every old demand dimension'):
            self.apply('supersede', old_demand_id='demand:flume', new_demand_id=updated['id'], reviewer='independent-reviewer')
        mappings = [{'old_dimension_id': name, 'new_dimension_id': name, 'judgment': 'unresolved' if name == 'assessment' else 'preserved',
                     'rationale': 'Synthetic explicit before/after review.'} for name in ('prerequisites', 'learning', 'assessment')]
        self.apply('supersede', old_demand_id='demand:flume', new_demand_id=updated['id'], reviewer='independent-reviewer', dimension_dispositions=mappings)
        self.compare(did=updated['id'])
        self.assertIn('supersession_unresolved', {b['code'] for b in self.report()['blockers']})
        for item in mappings:
            item['judgment'] = 'preserved'
        self.apply('review_supersession', old_demand_id='demand:flume', new_demand_id=updated['id'], reviewer='independent-reviewer', dimension_dispositions=mappings)
        report = self.report()
        self.assertTrue(report['ready_for_review'])
        self.assertEqual(len(report['retirement_reviews']), 2)
        self.assertEqual(report['retirement_reviews'][0]['prior_comparison']['dimensions'][-1]['judgment'], 'gap')

    def test_malformed_discovery_report_returns_blocked_instead_of_api_exception(self):
        state = loop.load(ROOT / 'examples/workflow.json')
        state['context']['inputs'].append({'id': 'review:discovery', 'revision': loop.VERSION, 'sha256': '0' * 64})
        for value in ([], {}, {'schema_version': 1, 'authority': 'advisory_only', 'session_sha256': '0' * 64,
                               'ready_for_review': True, 'scope': {}, 'comparisons': ['bad']}):
            self.assertEqual(workflow.decide(state, discovery_report=value)['reason'], 'invalid_discovery_report')

    def test_cli_real_reads_prints_next_state_without_mutating_inputs(self):
        config = self.root / 'config.json'
        config.write_text(json.dumps(configuration()))
        run = lambda *args: subprocess.run([sys.executable, '-B', str(ROOT / 'tools/discovery_loop.py'), *args,
                                           '--root', str(self.root)], capture_output=True, text=True)
        result = run('init', str(config))
        self.assertEqual(result.returncode, 0, result.stderr)
        session = self.root / 'session.json'
        session.write_text(result.stdout)
        before = session.read_bytes()
        event = self.root / 'event.json'
        event.write_text(json.dumps(self.event('discover', frontier_id='probe:external', query='Find external problem',
                                               actor='discoverer', outcome='found', candidates=[self.source()])))
        result = run('step', str(session), '--event', str(event))
        self.assertEqual(result.returncode, 0, result.stderr)
        session.write_text(result.stdout)
        event.write_text(json.dumps(self.event('read', source_id='source:external', start_line=2, end_line=3, actor='reader')))
        before = session.read_bytes()
        result = run('step', str(session), '--event', str(event))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(session.read_bytes(), before)
        receipt = json.loads(result.stdout)['events'][-1]['data']['receipt']
        self.assertEqual(receipt['excerpt'], 'Explain the flume invariant.\nPredict an unseen transformation without supplied answers.\n')
        self.assertEqual(receipt['sha256'], hashlib.sha256((self.root / 'source.txt').read_bytes()).hexdigest())

    def test_real_workflow_cannot_continue_or_claim_completion_without_discovery(self):
        state = loop.load(ROOT / 'examples/quality-workflow.json')
        state['synthetic'] = False
        for goal in (False, True):
            state['stop']['goal_claimed'] = goal
            self.assertEqual(workflow.decide(state)['reason'], 'discovery_missing')
        path = self.root / 'workflow.json'
        path.write_text(json.dumps(state))
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), 'decide', str(path)], capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)['reason'], 'discovery_missing')

    def test_quality_preserves_sixteen_checks_but_real_missing_discovery_is_not_ready(self):
        for relative in (quality.CATALOG, quality.CONTRACT, 'curriculum/student-plan.html', quality.UNIT_SPECIFICATIONS, quality.THEORY_SPECIFICATION):
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        bundle = normal_bundle(self.root)
        self.assertTrue(quality.evaluate(bundle, self.root)['ready_for_review'])
        bundle['synthetic'] = False
        report = quality.evaluate(bundle, self.root)
        self.assertEqual(len(report['checks']), 16)
        self.assertEqual(report['discovery_gate'], 'discovery_missing')
        self.assertFalse(report['ready_for_review'])


class DiscoveryPreflightTest(unittest.TestCase):
    """Exercise joined synthetic fixtures without weakening real discovery defaults."""
    setUp = joined_tests.ReviewPreflightTest.setUp
    refresh_state = joined_tests.ReviewPreflightTest.refresh_state
    run_check = joined_tests.ReviewPreflightTest.run_check
    def test_current_discovery_graph_binding_passes_and_new_demand_stales_aggregate(self):
        import review_preflight
        cfg = configuration()
        cfg['scope']['lesson_path'] = 'lesson.txt'
        session = loop.initialize(cfg)
        (self.root / 'source.txt').write_text('Synthetic official task requiring an explanation and unseen transfer.\n')
        source = {'id': 'source:task', 'uri': 'https://example.invalid/task', 'path': 'source.txt', 'revision': 'fixture-v1',
                  'kind': 'official_problem', 'attribution': 'Synthetic task.'}
        events = [
            {'id': 'd:1', 'op': 'discover', 'data': {'frontier_id': 'probe:external', 'query': 'External problem demand', 'actor': 'searcher', 'outcome': 'found', 'candidates': [source]}},
            {'id': 'd:2', 'op': 'read', 'data': {'source_id': source['id'], 'actor': 'reader', 'start_line': 1, 'end_line': 1}},
            {'id': 'd:3', 'op': 'trace', 'data': {'frontier_id': 'probe:external', 'read_ids': ['d:2'], 'actor': 'extractor', 'rationale': 'Observable task requirements.', 'counterevidence': 'Synthetic only.', 'uninvestigated': [], 'demands': [{'id': 'demand:new', 'statement': 'An external requirement.', 'prerequisites': [], 'learning_demand': 'Explain.', 'assessment_demand': 'Unaided transfer.'}]}},
            {'id': 'd:4', 'op': 'compare', 'data': {'demand_id': 'demand:new', 'reviewer': 'reviewer', 'judgment': 'covered', 'rationale': 'Synthetic review.', 'start_line': 1, 'end_line': 1,
                'dimensions': [{'id': name, 'judgment': 'met', 'observed_behavior': 'Synthetic matching behavior.', 'rationale': 'Synthetic evidence.', 'start_line': 1, 'end_line': 1} for name in ('learning', 'assessment')]}}
        ]
        for event in events:
            event['data']['reason'] = 'Synthetic joined control.'
            session = loop.step(session, event, self.root)
        def joined():
            return review_preflight.preflight(self.root, self.depth, self.graph, self.paths, self.state,
                                             semantic_review=self.semantic_review, discovery_state=session)
        self.assertIn('discovery_demand_path_missing', {b['code'] for b in joined()['blockers']})
        self.paths['paths'][0]['discovery_demand_id'] = 'demand:new'
        self.semantic_review['path_spec_sha256'] = loop.digest(self.paths)
        self.state['context']['inputs'] = [item for item in self.state['context']['inputs'] if not item['id'].startswith('review:')]
        self.state['context']['inputs'].extend(review_preflight.context_manifests(self.depth, self.graph, self.paths,
            self.semantic_review, self.state['sources'], session))
        self.refresh_state()
        self.assertEqual(joined()['status'], 'consistent_recorded_context', joined())
        additional = copy.deepcopy(events[2])
        additional['id'] = 'd:5'
        additional['data']['demands'][0].update(id='demand:another', statement='A newly observed independent requirement.')
        session = loop.step(session, additional, self.root)
        result = joined()
        self.assertEqual(result['status'], 'blocked')
        codes = {b['code'] for b in result['blockers']}
        self.assertIn('review_context_not_bound', codes)
        self.assertIn('discovery_needs_work', codes)

    def test_real_and_explicit_legacy_inspection_cannot_reuse_narrow_success(self):
        self.assertEqual(self.run_check()['status'], 'consistent_recorded_context')
        self.depth['synthetic'] = self.paths['synthetic'] = self.semantic_review['synthetic'] = self.state['synthetic'] = False
        result = self.run_check()
        self.assertIn('discovery_missing', {b['code'] for b in result['blockers']})
        import review_preflight
        result = review_preflight.preflight(self.root, self.depth, self.graph, self.paths, self.state,
                                             semantic_review=self.semantic_review, legacy_scope=True)
        self.assertEqual(result['review_scope'], 'legacy_inspection_not_ready')
        self.assertNotEqual(result['status'], 'consistent_recorded_context')


if __name__ == '__main__':
    unittest.main()
