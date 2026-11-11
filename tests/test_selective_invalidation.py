"""Selective invalidation controls; all review/lesson records are synthetic."""
import copy
import json
import subprocess
import sys
import unittest

import test_quality as fixtures
from test_quality import check
import quality
import workflow


class SelectiveInvalidationTest(unittest.TestCase):
    setUp = fixtures.QualityTest.setUp
    report = fixtures.QualityTest.report

    def configure_scoped_lessons(self):
        bundle = self.bundle
        first = bundle['units'][0]
        second = copy.deepcopy(first)
        second.update(id='unit:other', week=2, syllabus_ids=['KOAI-19'],
                      claim_ids=['claim:other'], plan_dependency_ids=['unit:other'])
        claim = copy.deepcopy(bundle['claims'][0])
        claim.update(id='claim:other', source_ids=['source:other'])
        bundle['units'].append(second)
        bundle['claims'].append(claim)
        bundle['target']['objective_ids'].append(second['id'])
        source = copy.deepcopy(bundle['source_reads'][0])
        source['id'] = 'source:other'
        bundle['source_reads'].append(source)
        bundle['dependencies'].extend([
            {'id': 'source:other', 'revision': 'v1', 'sha256': '1' * 64, 'depends_on': []},
            {'id': 'claim:other', 'revision': 'v1', 'sha256': '2' * 64, 'depends_on': ['source:other']},
            {'id': 'unit:other', 'revision': 'v1', 'sha256': '3' * 64, 'depends_on': ['claim:other'],
             'path': 'curriculum/student-plan.html', 'locators': ['#week-2', '#scope-19', '#plan-context']}])
        for review in list(bundle['reviews']):
            duplicate = copy.deepcopy(review)
            duplicate.update(id=review['id'] + ':other',
                             object_id='claim:other' if review['object_id'] == 'claim:axis' else 'unit:other')
            bundle['reviews'].append(duplicate)
        cells = []
        for obj, cid in [(first, 'axis'), (second, 'other')]:
            obj['locator'] = 'cell:unit-' + cid
            for role in obj['chain'].values():
                role['locator'] = obj['locator']
            obj['explanation_regions'] = {tid: [obj['locator']] for tid in obj['explanation_checks']}
            target = next(x for x in bundle['claims'] if x['id'] in obj['claim_ids'])
            target['locator'] = 'cell:claim-' + cid
            for name in [obj['locator'][5:], target['locator'][5:]]:
                cells.append({'id': name, 'cell_type': 'markdown', 'metadata': {}, 'source': [name]})
        cells.append({'id': 'unrelated', 'cell_type': 'markdown', 'metadata': {}, 'source': ['unrelated']})
        self.lesson = self.root / 'lesson.ipynb'
        self.lesson.write_text(json.dumps({'cells': cells, 'metadata': {}, 'nbformat': 4, 'nbformat_minor': 5}))
        bundle['artifact'].update(path=self.lesson.name, sha256=quality.file_digest(self.lesson))
        for review in bundle['reviews']:
            if review['criterion_id'] == 'K16':
                unit = next(x for x in bundle['units'] if x['id'] == review['object_id'])
                for value in review['subchecks'].values():
                    value['artifact_locators'] = [unit['locator']]
        fixtures.refresh_reviews(bundle, self.root)

    def freshness(self, criterion='K05', object_id='unit:axis'):
        review = next(r for r in reversed(self.bundle['reviews'])
                      if r['criterion_id'] == criterion and r['object_id'] == object_id)
        return quality.review_freshness(self.bundle, review, self.root)

    def change_plan(self, old, new):
        path = self.root / 'curriculum/student-plan.html'
        text = path.read_text()
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1))

    def test_related_week_and_scope_changes_expire_only_declared_unit_reviews(self):
        for old in ['<p>1주차</p>', '데이터 처리용 NumPy·pandas']:
            with self.subTest(region=old):
                self.configure_scoped_lessons()
                path = self.root / 'curriculum/student-plan.html'
                original = path.read_text()
                self.change_plan(old, old + ' [synthetic change]')
                affected = self.freshness()
                self.assertEqual(affected['status'], 'review_required')
                self.assertEqual(self.freshness('K05', 'unit:other')['status'], 'current')
                self.assertEqual(self.freshness('K06', 'claim:axis')['status'], 'current')
                self.assertTrue(any(item['after']['path'] == 'curriculum/student-plan.html'
                                    for item in affected['changed_bindings'] if item['after']))
                path.write_text(original)
                # Reset fixture to avoid appending the second lesson twice.
                self.bundle = fixtures.normal_bundle(self.root)

    def test_unrelated_week_scope_css_and_contract_repin_preserve_reviews(self):
        self.configure_scoped_lessons()
        self.change_plan('<p>10주차</p>', '<p>10주차 [unrelated]</p>')
        self.change_plan('body { margin: 16px;', 'body { margin: 17px;')
        path = self.root / quality.CONTRACT
        contract = quality.load(path)
        contract['baseline']['sha256'] = quality.file_digest(self.root / contract['baseline']['path'])
        path.write_text(json.dumps(contract))
        for node in self.bundle['dependencies']:
            if node.get('locators'):
                node.update(revision='whole-plan-repin', sha256=contract['baseline']['sha256'])
        self.assertEqual(self.freshness()['status'], 'current')
        self.assertEqual(self.freshness('K05', 'unit:other')['status'], 'current')

    def test_global_unidentified_plan_rows_expire_bound_units_but_not_claims(self):
        self.configure_scoped_lessons()
        self.change_plan('AI 선행학습은 필수 조건이 아니다.', 'AI 선행학습은 필수 조건이다.')
        for oid in ['unit:axis', 'unit:other']:
            affected = self.freshness('K05', oid)
            self.assertEqual(affected['status'], 'review_required')
            self.assertIn('#plan-context', [x['after']['locator'] for x in affected['changed_bindings'] if x['after']])
        self.assertEqual(self.freshness('K06', 'claim:axis')['status'], 'current')

    def test_new_visible_plan_guidance_outside_rows_is_not_an_unbound_boundary(self):
        self.configure_scoped_lessons()
        path = self.root / 'curriculum/student-plan.html'
        path.write_text(path.read_text().replace('</main>', '<p>New global student requirement.</p></main>'))
        self.assertEqual(self.freshness()['status'], 'review_required')
        self.assertEqual(self.freshness('K05', 'unit:other')['status'], 'review_required')
        self.assertEqual(self.freshness('K06', 'claim:axis')['status'], 'current')

    def test_missing_legacy_binding_is_not_a_content_rereview_campaign(self):
        del self.bundle['units'][0]['plan_dependency_ids']
        self.bundle['dependencies'][-1].pop('path')
        self.bundle['dependencies'][-1].pop('locators')
        fixtures.refresh_reviews(self.bundle, self.root)
        history = copy.deepcopy(self.bundle['reviews'])
        result = check(self.report(), 'K12')['measurement']
        self.assertEqual(result['stale_review_ids'], [])
        self.assertTrue(result['binding_tasks'])
        self.assertTrue(all(x['status'] == 'binding_required' for x in result['binding_tasks']))
        self.assertEqual(self.bundle['reviews'], history)
        plan = quality.plan_work(self.bundle, self.root)
        self.assertTrue(any(x.get('work_kind') == 'binding_or_impact_confirmation' for x in plan['ranked']))
        self.assertFalse(any(x['criterion_id'] in quality.REVIEW_CRITERIA and x['object_id'] == 'unit:axis'
                             for x in plan['ranked'] if x['id'].startswith('finding:')))

    def test_new_binding_capture_does_not_make_old_review_current(self):
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K05')
        review.pop('dependency_scope_fingerprint')
        old = copy.deepcopy(self.bundle['reviews'])
        captured = quality.plan_bindings(self.bundle, 'unit:axis', self.root)
        self.assertFalse(captured['issues'])
        self.assertEqual(self.freshness()['status'], 'impact_confirmation_required')
        self.assertEqual(quality._review(self.bundle, 'K05', 'unit:axis', self.root), 'uncertain')
        self.assertEqual(self.bundle['reviews'], old)
        current = copy.deepcopy(review)
        current.update(id='new-independent-scope-review',
                       dependency_scope_fingerprint=captured['scope_fingerprint'])
        self.bundle['reviews'].append(current)
        self.assertEqual(self.freshness()['status'], 'current')
        self.assertEqual(len(self.bundle['reviews']), len(old) + 1)

    def test_missing_or_disconnected_plan_regions_require_binding(self):
        node = self.bundle['dependencies'][-1]
        node['locators'].remove('#plan-context')
        self.assertEqual(self.freshness()['status'], 'binding_required')
        self.bundle['units'][0]['plan_dependency_ids'] = ['unconnected-plan']
        self.bundle['dependencies'].append({'id': 'unconnected-plan', 'revision': 'v1', 'sha256': '0' * 64,
                                           'depends_on': [], 'path': node['path'], 'locators': node['locators']})
        self.assertIn('plan_dependency_not_connected', [x['code'] for x in self.freshness()['binding_issues']])

    def test_missing_locator_never_hashes_to_a_current_review(self):
        self.bundle['dependencies'][-1]['locators'].append('#not-present')
        with self.assertRaisesRegex(ValueError, 'Dependency locators not found'):
            quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
        self.assertNotEqual(self.freshness()['status'], 'current')

    def test_local_dependency_and_lesson_cell_changes_are_selective(self):
        self.configure_scoped_lessons()
        source = self.root / 'source.txt'
        source.write_text('read version one')
        self.bundle['dependencies'][0]['path'] = source.name
        fixtures.refresh_reviews(self.bundle, self.root)
        source.write_text('read version two')
        self.assertEqual(self.freshness()['status'], 'review_required')
        self.assertEqual(self.freshness('K06', 'claim:axis')['status'], 'review_required')
        self.assertEqual(self.freshness('K05', 'unit:other')['status'], 'current')
        fixtures.refresh_reviews(self.bundle, self.root)
        data = quality.load(self.lesson)
        data['cells'][0]['source'].append('changed lesson behavior')
        self.lesson.write_text(json.dumps(data))
        self.assertEqual(self.freshness()['status'], 'review_required')
        self.assertEqual(self.freshness('K05', 'unit:other')['status'], 'current')

    def test_local_review_and_subcheck_evidence_changes_appear_in_k12(self):
        for location in ['evidence', 'subcheck']:
            with self.subTest(location=location):
                extra = self.root / (location + '.txt')
                extra.write_text('current independent evidence')
                review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
                evidence = [{'path': extra.name, 'sha256': quality.file_digest(extra),
                             'locator': 'specific observed result', 'observation': 'synthetic control'}]
                if location == 'evidence':
                    review['evidence'] = evidence
                else:
                    review['subchecks']['T03']['evidence'] = evidence
                extra.write_text('changed evidence')
                result = check(self.report(), 'K12')['measurement']
                item = next(x for x in result['review_freshness'] if x['review_id'] == review['id'])
                self.assertEqual(item['status'], 'review_required')
                self.assertIn(review['id'], result['stale_review_ids'])
                self.assertTrue(any(b['path'] == extra.name for x in item['reasons'] for b in x.get('bindings', [])))
                extra.write_text('current independent evidence')

    def test_known_evidence_drift_and_legacy_binding_task_are_both_reported(self):
        del self.bundle['units'][0]['plan_dependency_ids']
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K05')
        receipt = self.root / review['evidence'][0]['path']
        receipt.write_text('changed known evidence')
        item = self.freshness()
        self.assertEqual(item['status'], 'review_required')
        self.assertEqual(item['binding_status'], 'binding_required')
        result = check(self.report(), 'K12')['measurement']
        self.assertIn(review['id'], result['stale_review_ids'])
        self.assertIn(review['id'], [x['review_id'] for x in result['binding_tasks']])

    def test_failed_latest_record_remains_visible_when_its_evidence_changes(self):
        latest = copy.deepcopy(next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K06'))
        latest.update(id='latest-failure', status='failed')
        self.bundle['reviews'].append(latest)
        receipt = self.root / latest['evidence'][0]['path']
        receipt.write_text('changed failed-review evidence')
        result = self.freshness('K06', 'claim:axis')
        self.assertEqual(result['status'], 'review_required')
        self.assertEqual(result['recorded_status'], 'failed')
        self.assertEqual(result['review_id'], 'latest-failure')
        self.assertNotEqual(quality._review(self.bundle, 'K06', 'claim:axis', self.root), 'passed')

    def test_missing_source_retains_selective_diagnostics_through_all_cli_paths(self):
        import test_review_preflight as preflight_fixtures
        self.configure_scoped_lessons()
        source = self.root / 'only-axis-source.txt'
        source.write_text('current scoped source')
        self.bundle['dependencies'][0]['path'] = source.name
        self.bundle['candidates'] = [{'id': 'existing-source-investigation', 'criterion_id': 'K06',
            'object_id': 'claim:axis', 'severity': 'major', 'confidence': 'unresolved',
            'hypothesis': 'Verify the declared local source', 'action': 'Read and compare the exact support.'}]
        self.bundle['research_cycles'].append({'id': 'cycle:other', 'object_ids': ['claim:other'],
            'trigger': 'synthetic control', 'queries': ['synthetic'], 'source_ids': ['source:other'],
            'disposition': 'unchanged', 'reason': 'synthetic fixture', 'object_contexts': {}})
        for cycle in self.bundle['research_cycles']:
            cycle['object_contexts'] = {oid: quality.object_fingerprint(self.bundle, 'K10', oid, self.root)
                                        for oid in cycle['object_ids']}
        fixtures.refresh_reviews(self.bundle, self.root)
        source.unlink()
        report = self.report()
        self.assertFalse(report['ready_for_review'])
        self.assertEqual(check(report, 'K11')['status'], 'uncertain')
        self.assertEqual(check(report, 'K13')['status'], 'uncertain')
        planned = quality.plan_work(self.bundle, self.root)
        self.assertEqual(next(x for x in planned['ranked'] if x['id'] == 'existing-source-investigation')['context_status'], 'unavailable')
        harness = preflight_fixtures.ReviewPreflightTest()
        harness.setUp()
        self.addCleanup(harness.doCleanups)
        inputs = {'quality.json': self.bundle, 'state.json': harness.state,
                  'depth.json': harness.depth, 'graph.json': harness.graph,
                  'paths.json': harness.paths, 'semantic.json': harness.semantic_review}
        for name, value in inputs.items():
            (self.root / name).write_text(json.dumps(value))
        commands = [
            ([str(fixtures.ROOT / 'tools/quality.py'), 'evaluate', str(self.root / 'quality.json')], 0),
            ([str(fixtures.ROOT / 'tools/quality.py'), 'plan', str(self.root / 'quality.json')], 0),
            ([str(fixtures.ROOT / 'tools/workflow.py'), 'decide', str(self.root / 'state.json'),
              '--quality', str(self.root / 'quality.json')], 0),
            ([str(fixtures.ROOT / 'tools/review_preflight.py'), '--depth', 'depth.json', '--graph', 'graph.json',
              '--paths', 'paths.json', '--state', 'state.json', '--quality', 'quality.json',
              '--semantic-review', 'semantic.json'], 1)]
        before = {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        for args, expected_exit in commands:
            with self.subTest(command=args[0]):
                result = subprocess.run([sys.executable, '-B', *args, '--root', str(self.root)], capture_output=True, text=True)
                self.assertEqual(result.returncode, expected_exit, result.stdout + result.stderr)
                output = json.loads(result.stdout)
                rows = output['selective_review']['review_freshness']
                axis = next(x for x in rows if x['object_id'] == 'claim:axis' and x['criterion_id'] == 'K06')
                other = next(x for x in rows if x['object_id'] == 'claim:other' and x['criterion_id'] == 'K06')
                self.assertEqual(axis['status'], 'review_required')
                self.assertEqual(other['status'], 'current')
                self.assertTrue(any(x.get('path') == source.name and x.get('error') for x in axis['current_bindings']))
                self.assertFalse(output.get('ready_for_review', False))
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    def test_workflow_early_pause_exposes_advisory_freshness(self):
        state = quality.load(fixtures.ROOT / 'templates/workflow.json')
        report = self.report()
        result = workflow.decide(state, report)
        self.assertEqual(result['reason'], 'operator_agreement_required')
        self.assertEqual(result['selective_review'], report['selective_review'])

    def test_cli_capture_is_read_only_and_exposes_bindings(self):
        path = self.root / 'quality.json'
        path.write_text(json.dumps(self.bundle))
        original = path.read_bytes()
        result = subprocess.run([sys.executable, str(fixtures.ROOT / 'tools/quality.py'), 'review-context', str(path),
                                 '--root', str(self.root), '--criterion', 'K05', '--object', 'unit:axis'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        captured = json.loads(result.stdout)
        self.assertFalse(captured['plan_bindings']['issues'])
        self.assertTrue(captured['context_bindings'])
        self.assertEqual(path.read_bytes(), original)
        self.assertIn('no review or approval', captured['limit'])


if __name__ == '__main__':
    unittest.main()
