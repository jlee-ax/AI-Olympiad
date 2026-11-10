"""Regression controls for recorded review history and scoped evidence gates."""
import copy
import json
import unittest

import test_quality as fixtures
from test_quality import agree, check
import quality


class QualityFollowupTest(unittest.TestCase):
    setUp = fixtures.QualityTest.setUp
    report = fixtures.QualityTest.report

    def append_current_records(self):
        current = copy.deepcopy(self.bundle['reviews'])
        for review in current:
            review['id'] += ':current'
            review['context_fingerprint'] = quality.object_fingerprint(
                self.bundle, review['criterion_id'], review['object_id'], self.root)
        self.bundle['reviews'].extend(current)
        cycle = copy.deepcopy(self.bundle['research_cycles'][-1])
        cycle['id'] += ':current'
        cycle['object_contexts'] = {oid: quality.object_fingerprint(self.bundle, 'K10', oid, self.root)
                                    for oid in cycle['object_ids']}
        self.bundle['research_cycles'].append(cycle)

    def test_new_review_replaces_stale_context_without_erasing_history(self):
        self.bundle['claims'][0]['statement'] += ' A clarified synthetic domain.'
        self.append_current_records()
        before = copy.deepcopy(self.bundle['reviews'])
        self.assertEqual(check(self.report(), 'K12')['status'], 'passed')
        self.assertEqual(self.bundle['reviews'], before)

    def test_new_research_cycle_replaces_stale_context_without_erasing_history(self):
        self.bundle['source_reads'][0]['version'] = 'synthetic-v2'
        self.append_current_records()
        before = copy.deepcopy(self.bundle['research_cycles'])
        self.assertEqual(check(self.report(), 'K11')['status'], 'passed')
        self.assertEqual(self.bundle['research_cycles'], before)

    def test_latest_failed_review_is_not_replaced_by_an_older_pass(self):
        self.append_current_records()
        next(r for r in reversed(self.bundle['reviews']) if r['criterion_id'] == 'K06')['status'] = 'failed'
        self.assertEqual(check(self.report(), 'K06')['status'], 'failed')

    def test_latest_abstaining_cycle_is_not_replaced_by_an_older_pass(self):
        self.append_current_records()
        self.bundle['research_cycles'][-1]['disposition'] = 'abstain'
        self.assertEqual(check(self.report(), 'K11')['status'], 'uncertain')

    def test_unrelated_correct_oracle_cannot_replace_required_unit_kind(self):
        self.bundle['units'][0]['id'] = 'W1-array'
        self.bundle['target']['objective_ids'] = ['W1-array']
        self.bundle['dependencies'][-1]['id'] = 'W1-array'
        self.bundle['claims'][0]['oracle'] = {
            'kind': 'weighted_sum', 'weights': [.5, .5], 'values': [2, 4], 'expected': 3}
        self.assertNotEqual(check(self.report(), 'K07')['status'], 'passed')

    def test_non_numerical_unit_does_not_require_an_unrelated_oracle(self):
        self.bundle['units'][0]['id'] = 'W1-python'
        self.bundle['target']['objective_ids'] = ['W1-python']
        self.bundle['dependencies'][-1]['id'] = 'W1-python'
        del self.bundle['claims'][0]['oracle']
        self.assertEqual(check(self.report(), 'K07')['status'], 'passed')

    def test_linked_role_region_changes_invalidate_local_fingerprint(self):
        for role, week in [('theory', 5), ('noncoding', 2), ('coding', 3), ('assessment', 4)]:
            with self.subTest(role=role):
                self.bundle['units'][0]['chain'][role]['locator'] = '#week-' + str(week)
                before = quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
                path = self.root / 'curriculum/student-plan.html'
                text = path.read_text()
                path.write_text(text.replace(str(week) + '\uc8fc\ucc28', str(week) + '\uc8fc\ucc28 [synthetic edit]', 1))
                after = quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
                self.assertNotEqual(before, after)
                path.write_text(text)

    def test_agreed_weekly_homework_cap_rejects_the_pinned_required_work(self):
        self.bundle['policy']['maximum_required_homework_minutes'] = 1
        agree(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K03')['status'], 'failed')

    def test_homework_cap_boundary_allows_accounted_required_work(self):
        self.bundle['policy']['maximum_required_homework_minutes'] = 420
        self.bundle['lesson_allocations'][0]['outside_work'] = [
            {'id': 'required-week-1', 'required': True, 'minutes': 420},
            {'id': 'optional-extra', 'required': False, 'minutes': 30}]
        agree(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K03')['status'], 'passed')


    def test_latest_stale_review_does_not_fall_back_to_a_current_pass(self):
        review = copy.deepcopy(self.bundle['reviews'][0])
        review.update(id='latest:stale', context_fingerprint='0' * 64)
        self.bundle['reviews'].append(review)
        self.assertEqual(check(self.report(), 'K02')['status'], 'uncertain')
        self.assertIn('latest:stale', check(self.report(), 'K12')['measurement']['stale_review_ids'])

    def test_out_of_scope_review_history_does_not_veto_current_objects(self):
        review = copy.deepcopy(self.bundle['reviews'][0])
        review.update(id='historical:removed-unit', object_id='retired:unit', context_fingerprint='0' * 64)
        self.bundle['reviews'].append(review)
        result = check(self.report(), 'K12')
        self.assertEqual(result['status'], 'passed')
        self.assertIn('historical:removed-unit', result['measurement']['historical_review_ids'])

    def test_multi_object_cycle_reuses_the_unchanged_object_only(self):
        other = copy.deepcopy(self.bundle['claims'][0])
        other['id'] = 'claim:other'
        self.bundle['claims'].append(other)
        node = copy.deepcopy(self.bundle['dependencies'][1])
        node['id'] = other['id']
        self.bundle['dependencies'].append(node)
        self.bundle['dependencies'][2]['depends_on'].append(other['id'])
        self.bundle['units'][0]['claim_ids'].append(other['id'])
        cycle = self.bundle['research_cycles'][0]
        cycle['object_ids'].append(other['id'])
        cycle['object_contexts'][other['id']] = quality.object_fingerprint(self.bundle, 'K10', other['id'], self.root)
        self.bundle['claims'][0]['statement'] += ' Updated meaning.'
        update = copy.deepcopy(cycle)
        update.update(id='cycle:one-object-update', object_ids=['claim:axis'])
        update['object_contexts'] = {'claim:axis': quality.object_fingerprint(self.bundle, 'K10', 'claim:axis', self.root)}
        self.bundle['research_cycles'].append(update)
        result = check(self.report(), 'K11')
        self.assertEqual(result['status'], 'passed')
        selected = {x['object_id']: x['cycle_id'] for x in result['measurement']['active_by_object']}
        self.assertEqual(selected['claim:axis'], update['id'])
        self.assertEqual(selected['claim:other'], cycle['id'])

    def test_latest_cycle_must_cover_the_claims_actual_support(self):
        self.bundle['research_cycles'][0]['source_ids'] = []
        self.assertEqual(check(self.report(), 'K11')['status'], 'uncertain')

    def test_another_units_oracle_cannot_cover_a_missing_required_kind(self):
        other = copy.deepcopy(self.bundle['units'][0])
        other['id'] = 'W2-metrics'
        other['oracle_kinds'] = []
        self.bundle['units'].append(other)
        node = copy.deepcopy(self.bundle['dependencies'][-1])
        node['id'] = other['id']
        self.bundle['dependencies'].append(node)
        self.bundle['target']['objective_ids'].append(other['id'])
        result = check(self.report(), 'K07')
        row = next(x for x in result['measurement']['unit_requirements'] if x['unit_id'] == 'W2-metrics')
        self.assertEqual(row['required_kinds'], ['binary_metrics'])
        self.assertEqual(row['missing_kinds'], ['binary_metrics'])
        self.assertEqual(row['status'], 'not_run')
        self.assertNotEqual(result['status'], 'passed')

    def test_unknown_synthetic_unit_needs_an_explicit_oracle_contract(self):
        del self.bundle['units'][0]['oracle_kinds']
        self.assertEqual(check(self.report(), 'K07')['status'], 'uncertain')

    def test_unit_fingerprint_includes_actual_upstream_claim_data(self):
        before = quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
        self.bundle['claims'][0]['assumptions'].append('A newly stated substantive restriction')
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root))

    def test_unit_fingerprint_includes_the_upstream_claim_region(self):
        self.bundle['claims'][0]['locator'] = '#week-5'
        before = quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root)
        path = self.root / 'curriculum/student-plan.html'
        path.write_text(path.read_text().replace('5\uc8fc\ucc28', '5\uc8fc\ucc28 [synthetic claim edit]', 1))
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K05', 'unit:axis', self.root))

    def test_notebook_code_and_assessment_sources_are_bound_beyond_primary_cell(self):
        cells = [{'id': cid, 'cell_type': 'markdown', 'source': [cid + ' synthetic source'], 'metadata': {}}
                 for cid in ['overview', 'formula', 'theory', 'hand', 'code', 'assessment']]
        path = self.root / 'synthetic.ipynb'
        path.write_text(json.dumps({'cells': cells, 'nbformat': 4, 'nbformat_minor': 5, 'metadata': {}}))
        self.bundle['artifact']['path'] = path.name
        unit = self.bundle['units'][0]
        unit['locator'] = 'cell:overview'
        self.bundle['claims'][0]['locator'] = 'cell:formula'
        unit['explanation_regions'] = {tid: ['cell:theory'] for tid in unit['explanation_checks']}
        for role, cid in [('theory', 'theory'), ('noncoding', 'hand'), ('coding', 'code'), ('assessment', 'assessment')]:
            unit['chain'][role]['locator'] = 'cell:' + cid
        for cid in ['code', 'assessment']:
            before = quality.object_fingerprint(self.bundle, 'K09', unit['id'], self.root)
            next(c for c in cells if c['id'] == cid)['source'].append('Changed substantive source')
            path.write_text(json.dumps({'cells': cells}))
            self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K09', unit['id'], self.root))

    def test_unit_requirement_revision_invalidates_affected_review_and_agreement(self):
        unit = self.bundle['units'][0]
        unit['id'] = 'W1-array'
        self.bundle['target']['objective_ids'] = [unit['id']]
        self.bundle['dependencies'][-1]['id'] = unit['id']
        before = quality.object_fingerprint(self.bundle, 'K05', unit['id'], self.root)
        agreement = quality.agreement_fingerprint(self.bundle, self.root)
        path = self.root / quality.UNIT_SPECIFICATIONS
        specs = quality.load(path)
        next(x for x in specs['units'] if x['id'] == unit['id'])['oracle_kinds'].append('weighted_sum')
        path.write_text(json.dumps(specs))
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K05', unit['id'], self.root))
        self.assertNotEqual(agreement, quality.agreement_fingerprint(self.bundle, self.root))
        self.assertNotEqual(check(self.report(), 'K07')['status'], 'passed')

    def test_current_required_ledger_cannot_exceed_cap_even_when_baseline_fits(self):
        self.bundle['policy']['maximum_required_homework_minutes'] = 500
        self.bundle['lesson_allocations'][0]['outside_work'][0]['minutes'] = 501
        agree(self.bundle, self.root)
        self.assertEqual(check(self.report(), 'K03')['status'], 'failed')

    def test_configured_cap_requires_a_current_work_ledger(self):
        del self.bundle['lesson_allocations'][0]['outside_work']
        self.assertEqual(check(self.report(), 'K03')['status'], 'not_run')

    def test_relabeling_required_work_as_optional_does_not_hide_it(self):
        self.bundle['lesson_allocations'][0]['outside_work'][0]['required'] = False
        self.assertEqual(check(self.report(), 'K03')['status'], 'failed')

    def test_unset_homework_cap_is_explicitly_unassessed(self):
        self.bundle['policy']['maximum_required_homework_minutes'] = None
        agree(self.bundle, self.root)
        result = check(self.report(), 'K03')
        self.assertEqual(result['measurement']['outside_work'][0]['cap_status'], 'not_agreed_not_assessed')
        self.assertIsNone(result['measurement']['outside_work'][0]['weekly_cap_minutes'])

    def test_negative_boolean_or_fractional_homework_caps_are_invalid(self):
        for cap in [-1, True, 2.5]:
            with self.subTest(cap=cap), self.assertRaisesRegex(ValueError, 'homework cap'):
                self.bundle['policy']['maximum_required_homework_minutes'] = cap
                quality.validate(self.bundle)

    def test_theory_needs_an_independent_review_beyond_execution(self):
        self.bundle['reviews'] = [r for r in self.bundle['reviews'] if r['criterion_id'] != 'K16']
        self.assertEqual(check(self.report(), 'K08')['status'], 'passed')
        self.assertEqual(check(self.report(), 'K16')['status'], 'not_run')
        self.assertFalse(self.report()['ready_for_review'])

    def test_missing_theory_subcheck_is_not_run_even_with_overall_pass(self):
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
        del review['subchecks']['T02']
        self.assertEqual(check(self.report(), 'K16')['status'], 'not_run')

    def test_failed_theory_subcheck_cannot_be_overridden_by_overall_pass(self):
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
        review['subchecks']['T04']['status'] = 'failed'
        self.assertEqual(check(self.report(), 'K16')['status'], 'failed')

    def test_theory_subcheck_needs_all_registered_regions_and_evidence(self):
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
        review['subchecks']['T03']['artifact_locators'] = []
        self.assertEqual(check(self.report(), 'K16')['status'], 'uncertain')
        review['subchecks']['T03']['artifact_locators'] = ['#week-1']
        review['subchecks']['T03']['evidence'] = []
        self.assertEqual(check(self.report(), 'K16')['status'], 'uncertain')

    def test_theory_self_review_and_stale_rubric_cannot_pass(self):
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
        review['reviewer_id'] = self.bundle['author_id']
        self.assertEqual(check(self.report(), 'K16')['status'], 'uncertain')
        review['reviewer_id'] = 'synthetic-independent-reviewer'
        path = self.root / quality.THEORY_SPECIFICATION
        rubric = quality.load(path)
        rubric['checks'][0]['pass'] += ' A revised required condition.'
        path.write_text(json.dumps(rubric))
        self.assertEqual(check(self.report(), 'K16')['status'], 'uncertain')
        self.assertEqual(check(self.report(), 'K14')['status'], 'uncertain')

    def test_registered_explanation_region_change_invalidates_theory_review(self):
        self.bundle['units'][0]['explanation_regions']['T03'] = ['#week-2']
        review = next(r for r in self.bundle['reviews'] if r['criterion_id'] == 'K16')
        review['subchecks']['T03']['artifact_locators'] = ['#week-2']
        review['context_fingerprint'] = quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root)
        self.assertEqual(check(self.report(), 'K16')['status'], 'passed')
        path = self.root / 'curriculum/student-plan.html'
        path.write_text(path.read_text().replace('2\uc8fc\ucc28', '2\uc8fc\ucc28 [synthetic diagram edit]', 1))
        self.assertEqual(check(self.report(), 'K16')['status'], 'uncertain')

    def test_non_numerical_python_does_not_require_an_invented_formula(self):
        unit = self.bundle['units'][0]
        unit['id'] = 'W1-python'
        self.bundle['target']['objective_ids'] = [unit['id']]
        self.bundle['dependencies'][-1]['id'] = unit['id']
        unit['explanation_checks'] = []  # Cannot weaken the versioned T04/T05 contract.
        unit['explanation_regions'] = {tid: ['#week-1'] for tid in ['T04', 'T05']}
        for review in self.bundle['reviews']:
            if review['object_id'] == 'unit:axis':
                review['object_id'] = unit['id']
            if review['criterion_id'] == 'K16':
                review['subchecks'] = {tid: review['subchecks'][tid] for tid in ['T04', 'T05']}
            review['context_fingerprint'] = quality.object_fingerprint(self.bundle, review['criterion_id'], review['object_id'], self.root)
        result = check(self.report(), 'K16')
        self.assertEqual(result['status'], 'passed')
        self.assertEqual({x['id'] for x in result['measurement']['units'][0]['checks']}, {'T04', 'T05'})

    def test_workflow_rejects_a_report_that_omits_the_theory_gate(self):
        report = self.report()
        state = fixtures.QualityTest.bound_workflow(self, report)
        report['checks'] = [c for c in report['checks'] if c['id'] != 'K16']
        self.assertEqual(fixtures.workflow.decide(state, report)['reason'], 'quality_checks_not_passed')


    def representation_notebook(self):
        cells = [
            {'id': 'body', 'cell_type': 'markdown', 'source': ['Synthetic attachment reference'],
             'attachments': {'synthetic.txt': {'text/plain': 'version one'}}},
            {'id': 'code', 'cell_type': 'code', 'source': ['synthetic source'], 'execution_count': 1,
             'outputs': [{'output_type': 'execute_result', 'execution_count': 1, 'data': {'text/plain': 'value one'}}]},
        ]
        path = self.root / 'representation.ipynb'
        path.write_text(json.dumps({'cells': cells}))
        self.bundle['artifact']['path'] = path.name
        unit = self.bundle['units'][0]
        unit['locator'] = 'cell:body'
        self.bundle['claims'][0]['locator'] = 'cell:body'
        unit['explanation_regions'] = {tid: ['cell:body'] for tid in unit['explanation_checks']}
        for role in unit['chain']:
            unit['chain'][role]['locator'] = 'cell:code' if role == 'coding' else 'cell:body'
        return path, cells

    def test_representation_attachment_bytes_invalidate_content_review(self):
        path, cells = self.representation_notebook()
        before = quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root)
        cells[0]['attachments']['synthetic.txt']['text/plain'] = 'version two'
        path.write_text(json.dumps({'cells': cells}))
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root))

    def test_representation_output_changes_matter_but_execution_counters_do_not(self):
        path, cells = self.representation_notebook()
        before = quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root)
        cells[1]['execution_count'] = 2
        cells[1]['outputs'][0]['execution_count'] = 2
        path.write_text(json.dumps({'cells': cells}))
        self.assertEqual(before, quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root))
        cells[1]['outputs'][0]['data']['text/plain'] = 'different displayed result'
        path.write_text(json.dumps({'cells': cells}))
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root))

    def test_representation_asset_dependency_uses_actual_file_bytes(self):
        path = self.root / 'synthetic-diagram.svg'
        path.write_text('<svg><text>synthetic version one</text></svg>')
        self.bundle['dependencies'].append({'id': 'asset:diagram', 'path': path.name, 'revision': 'synthetic-v1',
                                            'sha256': quality.file_digest(path), 'depends_on': []})
        self.bundle['dependencies'][2]['depends_on'].append('asset:diagram')
        before = quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root)
        path.write_text('<svg><text>synthetic version two</text></svg>')
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root))

    def test_representation_svg_attributes_inside_html_region_are_bound(self):
        path = self.root / 'curriculum/student-plan.html'
        text = path.read_text()
        end = text.index('</tr>', text.index('id="week-1"'))
        text = text[:end] + '<td><svg><rect id="synthetic-rect" width="10"/></svg></td>' + text[end:]
        path.write_text(text)
        before = quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root)
        path.write_text(text.replace('id="synthetic-rect" width="10"', 'id="synthetic-rect" width="20"'))
        self.assertNotEqual(before, quality.object_fingerprint(self.bundle, 'K16', 'unit:axis', self.root))


if __name__ == '__main__':
    unittest.main()
