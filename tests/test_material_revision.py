"""Run the revision loop against copies of the actual Week 1 notebook; review identities are test controls."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import test_discovery_loop as discovery_fixtures
import test_quality as fixtures
from test_quality import quality, workflow
import discovery_loop as loop
import material_revision as edits

ROOT = fixtures.ROOT
INTRO, EXAMPLE, AXES = 'e3783955', 'd942743f', 'a3f9c114'


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def action(kind, before, after, condition):
    return {'kind': kind, 'before': before, 'after': after, 'reason': condition,
            'alternative': 'Retaining the draft leaves the documented gap.', 'postcondition': condition}


class ReviewScope(unittest.TestCase):
    setUp = fixtures.QualityTest.setUp

    def test_foundation_handoff_requires_a_real_later_plan_region_and_review_but_full_claim_retains_practice(self):
        b, u = self.bundle, self.bundle['units'][0]
        u.update(stage='foundation', claimed_depth='concept', continuation={
            'week': 2, 'owner_unit': 'W2-preprocess', 'practical_task': 'Apply axis reduction to new training columns.',
            'topic_ids': ['KOAI-02', 'KOAI-06'], 'plan_locator': '#week-2'})
        u['mode_evidence']['practical'] = 'not_run'
        b['dependencies'][-1]['locators'].append('#week-2')
        fixtures.refresh_reviews(b, self.root)
        r = fixtures.check(quality.evaluate(b, self.root), 'K02')
        self.assertEqual(r['status'], 'passed')
        self.assertEqual(r['measurement']['deferred_practical'][0]['week'], 2)
        for change in ({'week': 1}, {'topic_ids': []}, {'plan_locator': '#week-90'}, {'practical_task': ''}):
            other = copy.deepcopy(b)
            other['units'][0]['continuation'].update(change)
            self.assertEqual(fixtures.check(quality.evaluate(other, self.root), 'K02')['status'], 'failed')
        b['target']['coverage_claim'] = 'full_syllabus'
        self.assertEqual(fixtures.check(quality.evaluate(b, self.root), 'K02')['status'], 'failed')

    def test_introductory_reading_exempts_only_a_genuinely_non_executable_notebook(self):
        b, unit = self.bundle, self.bundle['units'][0]
        ids = ('support','reading','task')
        notebook={'cells':[{'id':k,'cell_type':'markdown','metadata':{},'source':[k]} for k in ids],
                  'nbformat':4,'nbformat_minor':5,'metadata':{}}
        save(self.root / 'reading.ipynb',notebook)
        b['artifact'].update(path='reading.ipynb',sha256=quality.file_digest(self.root / 'reading.ipynb'))
        unit.update(stage='foundation',claimed_depth='concept',continuation={'week':2,'owner_unit':'W2-preprocess',
                    'practical_task':'Apply reductions to held-out columns.','topic_ids':['KOAI-02','KOAI-06'],
                    'plan_locator':'#week-2'},locator='cell:reading',execution={})
        unit['mode_evidence']['practical']='not_run'
        unit['chain'].pop('coding')
        for role in unit['chain'].values():role['locator']='cell:reading'
        for k in unit['explanation_regions']:
            unit['explanation_regions'][k]=['cell:reading']
            b['reviews'][-1]['subchecks'][k]['artifact_locators']=['cell:reading']
        unit['prerequisites'][0]['support_before_use'].update(locator='cell:support',first_use='cell:reading')
        b['claims'][0]['locator']='cell:reading'
        b['dependencies'][-1]['locators'].append('#week-2')
        fixtures.refresh_reviews(b,self.root)
        report=quality.evaluate(b,self.root)
        self.assertEqual(fixtures.check(report,'K08')['measurement']['non_executable_foundations'],['unit:axis'])
        self.assertEqual([fixtures.check(report,k)['status'] for k in ('K02','K03','K04','K05','K08')],['passed']*5)
        notebook['cells'].append({'id':'actual-code','cell_type':'code','source':['1/0'],'metadata':{},'outputs':[]})
        save(self.root / 'reading.ipynb',notebook)
        self.assertEqual(fixtures.check(quality.evaluate(b,self.root),'K08')['status'],'not_run')


class DiscoveryScope(unittest.TestCase):
    def test_background_can_remain_open_and_empty_required_probe_needs_independent_resolution(self):
        f = discovery_fixtures.DiscoveryLoopTest()
        f.setUp()
        self.addCleanup(f.doCleanups)
        f.ready()
        f.apply('frontier', probe={'id': 'reading', 'purpose': 'background', 'scope_reason': 'Historical note only.',
                                   'question': 'Who developed this notation?', 'required_kinds': ['background']})
        self.assertTrue(f.report()['ready_for_review'])
        self.assertTrue(f.report()['background_notes'])
        with self.assertRaises(ValueError):
            f.apply('frontier', probe={'id': 'hidden', 'purpose': 'background', 'scope_reason': 'Escape',
                                       'question': 'Applicable scope?', 'required_kinds': ['official_scope']})
        f.apply('frontier', probe={'id': 'secondary', 'question': 'Does this reference impose another target?',
                                   'required_kinds': ['research']})
        source = f.source('technical', kind='research')
        f.apply('discover', frontier_id='secondary', actor='reader', query='primary reference', outcome='found', candidates=[source])
        rid = f.apply('read', source_id='technical', actor='reader', start_line=1, end_line=2)
        tid = f.apply('trace', frontier_id='secondary', actor='extractor', read_ids=[rid], uninvestigated=[],
                      rationale='Applies to a different domain.', counterevidence='Bound to one task.', demands=[])
        self.assertFalse(f.report()['ready_for_review'])
        exclude = dict(frontier_id='secondary', trace_ids=[tid], scope_basis='Other domain has no obligation here.')
        with self.assertRaises(ValueError):
            f.apply('exclude_probe', reviewer='extractor', **exclude)
        f.apply('exclude_probe', reviewer='independent', **exclude)
        self.assertTrue(f.report()['ready_for_review'])
        (f.root / 'source.txt').write_text('Changed source content.\n')
        self.assertFalse(f.report()['ready_for_review'])

    def test_independent_exclusion_of_a_tangential_question_reopens_on_changed_source(self):
        f = discovery_fixtures.DiscoveryLoopTest()
        f.setUp()
        self.addCleanup(f.doCleanups)
        rid = f.seed_demand()
        f.compare()
        f.apply('trace', frontier_id='probe:external', actor='reader', read_ids=[rid], demands=[],
                rationale='Same source and task.', counterevidence='Bounded selection.',
                uninvestigated=['Who coined the term?'])
        qid = f.report()['open_questions'][0]['id']
        data = dict(question_id=qid, read_ids=[rid], scope_basis='The terminology history has no bearing on this task.')
        with self.assertRaises(ValueError):
            f.apply('exclude_question', reviewer=' Reader ', **data)
        f.apply('exclude_question', reviewer='reviewer', **data)
        self.assertTrue(f.report()['ready_for_review'])
        (f.root / 'source.txt').write_text('Version changed.')
        self.assertFalse(f.report()['ready_for_review'])
        self.assertIn(qid, [q['id'] for q in f.report()['open_questions']])


class NotebookRoute(unittest.TestCase):
    def setUp(self):
        fixtures.QualityTest.setUp(self)
        self.original = quality.load(ROOT / 'lessons/week01/week01_integrated.ipynb')
        self.intro = next(c for c in self.original['cells'] if c['id'] == INTRO)
        draft = copy.deepcopy(self.original)
        draft['cells'] = [c for c in draft['cells'] if c['id'] != INTRO]
        draft['cells'].insert(5, {'id': 'redundant', 'cell_type': 'markdown', 'metadata': {},
                                  'source': ['결과를 출력합니다. 아래 결과를 출력합니다.']})
        self.baseline = self.root / 'draft.ipynb'
        save(self.baseline, draft)
        self.initial = self.baseline.read_bytes()
        b, u = self.bundle, self.bundle['units'][0]
        b['artifact'].update(path=self.baseline.name, sha256=quality.file_digest(self.baseline))
        u['locator'] = 'cell:' + AXES
        u['execution']['artifact_sha256'] = b['artifact']['sha256']
        for role in u['chain'].values():
            role['locator'] = u['locator']
        u['prerequisites'][0]['support_before_use'].update(locator=u['locator'], first_use=u['locator'])
        for tid in u['explanation_regions']:
            u['explanation_regions'][tid] = [u['locator']]
            b['reviews'][-1]['subchecks'][tid]['artifact_locators'] = [u['locator']]
        b['claims'][0]['locator'] = u['locator']
        fixtures.refresh_reviews(b, self.root)
        b['research_cycles'][0]['object_contexts'] = {'claim:axis': quality.object_fingerprint(b, 'K10', 'claim:axis', self.root)}
        self.f = discovery_fixtures.DiscoveryLoopTest()
        self.f.root, self.f.counter = self.root, 0
        (self.root / 'source.txt').write_text('Source note: NumPy mean divides a sum by the element count.\nThe missing-value policy determines which observations count.\nCheck the stated contract on a new case.\n')
        cfg = discovery_fixtures.configuration()
        cfg['scope'].update(lesson_path=self.baseline.name, artifact_path=self.baseline.name,
                            artifact_sha256=b['artifact']['sha256'])
        self.f.state = loop.initialize(cfg)
        self.f.seed_demand(demand=dict(id='demand:denominator', statement='Account for missing and observed zero.',
                              prerequisites=['Know which rows count.'], learning_demand='Explain the denominator.',
                              assessment_demand='Justify the result for a new input, including no observations.'))
        self.intent = {'actions': [action('add', [], [INTRO], 'Restore the omitted denominator and empty-input explanation.'),
                                   action('remove', ['redundant'], [], 'Remove the repeated display instruction.'),
                                   action('keep', [AXES], [AXES], 'Preserve the subsequent axis foundation.')],
                       'routes': {'prerequisites': {'before': [], 'after': [INTRO, EXAMPLE]},
                                  'learning': {'before': [], 'after': [INTRO, EXAMPLE]},
                                  'assessment': {'before': [EXAMPLE], 'after': [INTRO, EXAMPLE]}}}
        self.f.compare(did='demand:denominator', overall='gap', edit=self.intent,
                       dimensions=[dict(id=key, judgment='met' if key == 'assessment' else 'gap', observed_behavior='Seeded omission.',
                                        rationale='Inspect the changed notebook.', start_line=1, end_line=3) for key in self.intent['routes']])
        self.bpath = self.root / 'bundle.json'
        self.spath = self.root / 'discovery.json'
        b['discovery'] = {'path': self.spath.name}
        self.bind()
        self.patch = {'work_key': self.plan['ranked'][0]['key'], 'author': 'fixture-editor', 'operations': [
            {'op': 'insert', 'id': INTRO, 'cell_type': 'markdown', 'before': EXAMPLE, 'source': ''.join(self.intro['source'])},
            {'op': 'remove', 'id': 'redundant'}]}
        save(self.root / 'patch.json', self.patch)

    def bind(self):
        save(self.spath, self.f.state)
        save(self.bpath, self.bundle)
        self.report = quality.evaluate(self.bundle, self.root)
        self.plan = quality.plan_work(self.bundle, self.root, report=self.report)
        self.w = fixtures.QualityTest.bound_workflow(self, self.report)
        self.w['context']['inputs'].append(loop.manifest(self.f.state))
        save(self.root / 'workflow.json', self.w)

    def execute(self, command, review=None):
        return edits.run(command, self.root, self.w, self.bundle, self.patch, 'candidate.ipynb', review)

    def cli(self, *args):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools' / args[0]), *args[1:]],
                                cwd=self.root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_real_notebook_repair_verification_resume_and_release_are_distinct(self):
        self.assertEqual(self.plan['next_candidate'], 'repair:demand:denominator')
        for phase, expected in [('repair', 'scoped_repair_only'), ('decide', 'discovery_unresolved')]:
            self.assertEqual(self.cli('workflow.py', phase, 'workflow.json', '--root', '.', '--quality', 'bundle.json')['reason'], expected)
        call = ['bundle.json', 'patch.json', 'candidate.ipynb', '--root', '.']
        created = self.cli('material_revision.py', 'apply', 'workflow.json', *call)
        self.assertEqual(created['diff']['added'], [INTRO])
        self.assertEqual(created['diff']['removed'], ['redundant'])
        self.assertEqual(self.execute('apply')['status'], 'already_created')
        path = self.root / 'candidate.ipynb'
        candidate = quality.load(path)
        self.assertEqual(candidate['cells'], self.original['cells'])
        # Run the trusted function actually delivered; no optional dependencies in the regression environment.
        import ast
        import math
        from types import SimpleNamespace
        code = ''.join(next(c['source'] for c in candidate['cells'] if c['id'] == EXAMPLE))
        tree = ast.parse(code)
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'observed_mean')
        ns = {'pd': SimpleNamespace(isna=lambda v: v is None or isinstance(v, float) and math.isnan(v))}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), '<reviewed lesson function>', 'exec'), ns)
        results = [ns['observed_mean'](x) for x in ([None, -3, 0, 9], [float('nan')], [])]
        self.assertEqual(results, [2, None, None])
        receipt = self.root / 'fresh-results.json'
        save(receipt, {'candidate_sha256': created['candidate_sha256'], 'cases': [
            {'id':'mixed','input':[None,-3,0,9], 'actual':results[0], 'expected':2},
            {'id':'empty','input':[], 'actual':results[2], 'expected':None}],
                       'note': 'Controlled test with a minimal isna adapter for the stated domain.'})
        evidence = [{'path': receipt.name, 'sha256': quality.file_digest(receipt), 'locator': 'outputs', 'observation': str(results)}]
        checks = {'route:' + k: v['after'] for k,v in self.intent['routes'].items()}
        checks.update({'action:' + str(i): a['after'] or [EXAMPLE] for i,a in enumerate(self.intent['actions'])})
        checks.update(new_input=[EXAMPLE], boundary=[EXAMPLE], regression=[AXES])
        review = {'candidate_sha256': created['candidate_sha256'], 'reviewer': 'fixture-verifier',
                  'work_key': self.patch['work_key'], 'checks': {k:{'status':'passed','finding':'Synthetic review control.',
                  'cells':v, 'evidence':evidence} for k,v in checks.items()}}
        for key, case in [('new_input', 'mixed'), ('boundary', 'empty')]:
            review['checks'][key]['case_id'] = case
        reused = copy.deepcopy(review)
        reused['checks']['boundary']['case_id'] = 'mixed'
        with self.assertRaisesRegex(ValueError, 'distinct'):
            self.execute('verify', reused)
        fail = copy.deepcopy(review)
        fail['checks']['boundary']['status'] = 'failed'
        self.assertEqual(self.execute('verify', fail)['status'], 'rejected')
        with self.assertRaises(ValueError):
            self.execute('verify', {**review, 'reviewer': self.patch['author']})
        save(self.root / 'review.json', review)
        self.assertEqual(self.cli('material_revision.py','verify','workflow.json',*call,'--review','review.json')['status'], 'reviewed_candidate')
        event = self.f.event('advance_lesson', revision='candidate-v2', workflow_path='workflow.json', quality_path='bundle.json',
                             patch_path='patch.json', review_path='review.json', candidate_path=path.name)
        old_state = self.f.state
        self.f.state = loop.step(old_state, event, self.root)
        self.assertEqual(self.f.state['events'][:-1], old_state['events'])
        self.assertEqual(loop.step(self.f.state, event, self.root), self.f.state)
        self.assertEqual(self.f.report()['scope']['artifact_sha256'], created['candidate_sha256'])
        self.assertFalse(self.f.report()['ready_for_review'])
        self.f.compare(did='demand:denominator')
        self.assertTrue(self.f.report()['ready_for_review'])
        self.assertEqual(self.baseline.read_bytes(), self.initial)

    def test_skips_duplicates_and_blocks_stale_source_changed_baseline_unapproved_scope_and_budget(self):
        def repair():
            return workflow.decide(self.w, self.report, repair_plan=self.plan)
        self.w['scope']['lesson_production_allowed'] = False
        self.assertEqual(repair()['reason'], 'lesson_production_not_authorized')
        self.bind()
        self.w['stop']['requested'] = True
        self.w['stop']['reason'] = 'test'
        self.assertEqual(repair()['reason'], 'operator_stop')
        self.bind()
        self.w['usage']['iterations_used'] = self.w['limits']['max_iterations']
        self.assertEqual(repair()['reason'], 'iteration_budget_exhausted')
        self.bundle['attempts'].append({'key':self.patch['work_key'], 'outcome':'rejected','reason':'Preserved earlier rejection.'})
        self.assertIsNone(quality.plan_work(self.bundle,self.root)['next_candidate'])
        self.bundle['attempts'].clear()
        (self.root / 'source.txt').write_text('Changed underlying data.\n')
        self.assertIsNone(quality.plan_work(self.bundle,self.root)['next_candidate'])
        self.baseline.write_bytes(self.initial + b' ')
        self.assertEqual(quality.plan_work(self.bundle,self.root)['reason'], 'baseline_or_artifact_binding_failed')

    def test_harmful_edits_unregistered_changes_and_overwrite_attempts_are_rejected(self):
        self.patch['operations'].append({'op':'remove','id':AXES})
        with self.assertRaises(ValueError):
            self.execute('apply')
        self.patch['operations'].pop()
        self.patch['operations'].append({'op':'replace','id':EXAMPLE,'source':'return 0 # incorrect'})
        with self.assertRaises(ValueError):
            self.execute('apply')
        self.patch['operations'].pop()
        (self.root / 'candidate.ipynb').write_bytes(b'another writer')
        with self.assertRaisesRegex(ValueError,'already exists'):
            self.execute('apply')
        self.assertEqual((self.root / 'candidate.ipynb').read_bytes(),b'another writer')

def week_two_fixture():
    real = quality.load(ROOT / 'lessons/week02/week02_temporal_preprocessing.ipynb')
    start = copy.deepcopy(real)
    point, code, check = '9d29f53a', 'e7e69eb4', '31911a77'
    cells = edits.notebook_index(start)
    extra = {**copy.deepcopy(cells[point]), 'id':'repeat'}
    start['cells'].append(extra)
    item = {'key':'k', 'intent': {'actions': [
        action('merge',[point,'repeat'],[point],'Consolidate two preprocessing explanations.'),
        action('deepen',[point],[point],'Compare two futures while the training fit stays fixed.'),
        action('replace',[check],['new-check'],'Use distinct later values with the same fitted training range.'),
        action('reorder',[code],[code],'Place pipeline construction immediately before the later-data check.'),
        action('keep',['af3d2268'],['af3d2268'],'Keep the independent purpose of the score.')],
        'routes':{'learning':{'before':[point,code,check],'after':[point,code,'new-check']}}}}
    # Misplace the pipeline before its conceptual prerequisite in the baseline so the explicit reorder has a real effect.
    start['cells'].remove(cells[code])
    start['cells'].insert(start['cells'].index(cells[point]),cells[code])
    item['intent']['routes']['learning']['before']=[code,point,check]
    text=''.join(cells[point]['source'])+'\n훈련 범위가 고정된 상태에서 서로 다른 두 미래값이 결과에 주는 영향을 비교해 봅시다.'
    new_code=(''.join(cells[check]['source']) + '\n' +
              'from sklearn.preprocessing import MinMaxScaler\n'
              'scale = MinMaxScaler().fit([[2.], [6.]])\n'
              'observed = scale.transform([[10.], [-2.], [2.]]).ravel().tolist()\n'
              'assert observed == [2.0, -1.0, 0.0]\n')
    operations=[{'op':'remove','id':'repeat'}, {'op':'replace','id':point,'source':text},
                {'op':'insert','id':'new-check','cell_type':'code','before':check,'source':new_code},
                {'op':'move','id':code,'before':'new-check'}, {'op':'remove','id':check}]
    return start, item, operations, new_code


class EditOperations(unittest.TestCase):
    def test_new_explanation_merge_replacement_reorder_and_protection_on_week_two_copy(self):
        point, code, check = '9d29f53a', 'e7e69eb4', '31911a77'
        start, item, operations, new_code = week_two_fixture()
        out, diff = edits.build(start,item,{'work_key':'k','author':'editor','operations':operations},{point,check,code})
        self.assertEqual(diff['removed'],[check,'repeat'])
        self.assertEqual(diff['added'],['new-check'])
        self.assertEqual(diff['modified'],[point])
        self.assertEqual(diff['moved'],[code])
        self.assertEqual(''.join(edits.notebook_index(out)['new-check']['source']),new_code)
        # A registered old key may disappear only when the post-edit route accounts for it.
        broken=copy.deepcopy(item)
        broken['intent']['routes']['learning']['before'].remove(check)
        with self.assertRaisesRegex(ValueError,'successor route'):
            edits.build(start,broken,{'work_key':'k','author':'editor','operations':operations},{check})
        broken=copy.deepcopy(item)
        broken['intent']['routes']['learning']['after']=['new-check',point]
        with self.assertRaisesRegex(ValueError,'out of order'):
            edits.build(start,broken,{'work_key':'k','author':'editor','operations':operations},{check})
        # Within-notebook move uses the same order proof on the actual cells.
        item['intent']['actions'][3]['kind']='move'
        self.assertEqual(edits.build(start,item,{'work_key':'k','author':'editor','operations':operations},{check})[1],diff)
