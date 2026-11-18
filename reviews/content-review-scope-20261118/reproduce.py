"""Historical synthetic diagnostics for the recorded pre-migration control code.

This executes existing reducers. It does not execute learners or approve lessons.
Run from any directory; stdout is JSON. It is not a production acceptance gate.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tools')]
import quality
import workflow
import discovery_loop as loop
import test_quality
import test_discovery_loop


def rebound(bundle, root):
    # These are the repository's declared synthetic fixture reviews, not approvals.
    test_quality.agree(bundle, root)
    test_quality.refresh_reviews(bundle, root)
    bundle['research_cycles'][0]['object_contexts'] = {
        'claim:axis': quality.object_fingerprint(bundle, 'K10', 'claim:axis', root)}


def quality_cases():
    fixture = test_quality.QualityTest()
    fixture.setUp()
    result = []
    try:
        def run(name, change, criterion=None, expected=None):
            bundle = copy.deepcopy(fixture.bundle)
            change(bundle)
            rebound(bundle, fixture.root)
            report = quality.evaluate(bundle, fixture.root)
            statuses = {row['id']: row['status'] for row in report['checks']}
            if criterion is None:
                assert all(value == 'passed' for value in statuses.values())
                assert report['ready_for_review']
            else:
                assert statuses[criterion] == expected
                assert all(value == 'passed' for key, value in statuses.items() if key != criterion)
                assert not report['ready_for_review']
            result.append({'case': name, 'synthetic_control': True,
                           'ready_for_review': report['ready_for_review'], 'statuses': statuses,
                           'findings': [{'criterion': row['criterion_id'], 'status': row['status']}
                                        for row in report['findings']]})

        run('baseline_untested_learning_outcomes', lambda bundle: None)
        def no_learner(bundle):
            bundle['units'][0]['prerequisites'][0].update(observed='', status='unknown', evidence=[])
        run('lesson_design_without_learner_response', no_learner, 'K04', 'not_run')
        run('lesson_design_without_per_unit_calibration',
            lambda bundle: bundle['units'][0].update(calibration=[]), 'K15', 'not_run')
        run('controls_correct_without_agreed_calibration_tolerance',
            lambda bundle: bundle['policy'].update(calibration_tolerance=None), 'K15', 'uncertain')
        def introduction(bundle):
            unit = bundle['units'][0]
            unit.update(claimed_depth='concept', stage='foundation',
                        continuation={'stage': 'later_guided_practice', 'locator': '#week-2'})
            unit['mode_evidence']['practical'] = 'not_run'
        run('introductory_stage_for_practical_syllabus_topic', introduction, 'K02', 'failed')
        run('unsupported_learning_improvement_claim',
            lambda bundle: bundle['target'].update(learning_outcomes='improved'), 'K15', 'failed')
    finally:
        fixture.doCleanups()
    return result


def background_case():
    fixture = test_discovery_loop.DiscoveryLoopTest()
    fixture.setUp()
    try:
        fixture.ready()
        before = fixture.report()
        fixture.apply('frontier', probe={
            'id': 'probe:background-extension',
            'question': 'Nonessential background reading considered while editing one unit.',
            'required_kinds': ['background']})
        fixture.apply('discover', frontier_id='probe:background-extension',
                      query='background extension', actor='synthetic-reader',
                      outcome='no_results', candidates=[])
        after = fixture.report()
        assert before['ready_for_review'] and not after['ready_for_review']
        assert {row['code'] for row in after['blockers']} == {
            'frontier_unresolved', 'frontier_no_demands_requires_review'}
        return {'case': 'background_question_blocks_otherwise_ready_material',
                'synthetic_control': True, 'before_ready': before['ready_for_review'],
                'after_ready': after['ready_for_review'], 'blockers': after['blockers'],
                'next_action': after['next_action']}
    finally:
        fixture.doCleanups()


def repair_route_case():
    fixture = test_quality.QualityTest()
    fixture.setUp()
    root = fixture.root
    try:
        (root / 'source.txt').write_text(
            'Synthetic external operation.\nA new capability is required.\nUse changed input.\n')
        config = test_discovery_loop.configuration()
        config['scope']['lesson_path'] = 'curriculum/student-plan.html'
        state = loop.initialize(config)
        serial = 0
        def apply(op, **data):
            nonlocal state, serial
            serial += 1
            event = {'id': 'event:' + str(serial), 'op': op, 'data': {
                'reason': 'Synthetic control for repair-route inspection.', **data}}
            state = loop.step(state, event, root)
            return event['id']
        source = {'id': 'source:new', 'uri': 'https://example.invalid/synthetic',
                  'path': 'source.txt', 'revision': 'synthetic-v1', 'kind': 'official_problem',
                  'attribution': 'Synthetic control, not an actual official source.'}
        apply('discover', frontier_id='probe:external', query='new capability',
              actor='searcher', outcome='found', candidates=[source])
        rid = apply('read', source_id=source['id'], actor='reader', start_line=1, end_line=3)
        apply('trace', frontier_id='probe:external', read_ids=[rid], actor='extractor',
              rationale='Synthetic missing demand.', counterevidence='No real curriculum judgment.',
              uninvestigated=[], demands=[{'id': 'demand:absent-capability',
                  'statement': 'Missing capability beyond registered units.', 'prerequisites': [],
                  'learning_demand': 'Explain the new operation.', 'assessment_demand': 'Check changed input.'}])
        apply('compare', demand_id='demand:absent-capability', reviewer='separate-reviewer',
              judgment='gap', rationale='Synthetic gap despite valid existing records.',
              start_line=1, end_line=3, dimensions=[{
                  'id': name, 'judgment': 'gap', 'observed_behavior': 'Absent operation in synthetic control.',
                  'rationale': 'Synthetic gap.', 'start_line': 1, 'end_line': 3}
                  for name in ('learning', 'assessment')])
        (root / 'discovery.json').write_text(json.dumps(state))
        bundle = fixture.bundle
        bundle['discovery'] = {'path': 'discovery.json'}
        rebound(bundle, root)
        report = quality.evaluate(bundle, root)
        plan = quality.plan_work(bundle, root)
        discovered = loop.inspect(state, root)
        controller = quality.load(ROOT / 'examples/workflow.json')
        controller['context']['inputs'].append(loop.manifest(state))
        controller['context']['artifact']['sha256'] = quality.file_digest(root / bundle['artifact']['path'])
        controller['agreement']['budget_fingerprint'] = workflow.budget_fingerprint(controller)
        controller['agreement']['criteria_fingerprint'] = workflow.criteria_fingerprint(controller)
        decision = workflow.decide(controller, quality_report=report, discovery_report=discovered)
        assert all(row['status'] == 'passed' for row in report['checks'])
        assert discovered['queue'] and plan['next_candidate'] is None
        assert (decision['status'], decision['reason']) == ('blocked', 'discovery_unresolved')
        return {'case': 'discovered_gap_has_no_selected_edit_and_blocks_workflow',
                'synthetic_control': True, 'all_registered_K01_K16_pass': True,
                'discovery_queue': discovered['queue'],
                'quality_plan': {key: plan[key] for key in (
                    'status', 'reason', 'next_candidate', 'next_discovery_action')},
                'workflow_decision': {key: decision[key] for key in ('status', 'reason')}}
    finally:
        fixture.doCleanups()


def main():
    cases = quality_cases() + [background_case(), repair_route_case()]
    sources = ['tools/quality.py', 'tools/discovery_loop.py', 'tools/workflow.py',
               'tests/test_quality.py', 'tests/test_discovery_loop.py']
    result = {'reference_commit': 'd886411d9ddbce4de3e41232a62d37d126b788cc',
              'purpose': 'Isolate control behavior using declared synthetic fixture reviews; no lesson or learner approval.',
              'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources},
              'cases': cases}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
