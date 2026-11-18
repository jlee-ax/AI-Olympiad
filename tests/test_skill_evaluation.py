"""Offline case, grader and optional real NVIDIA integration regressions."""
from copy import deepcopy
from importlib.util import find_spec, module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import skill_evaluation as gate
import workflow

spec = spec_from_file_location('koai_project_grader', gate.GRADER)
grader = module_from_spec(spec)
spec.loader.exec_module(grader)
NATIVE = find_spec('skillevaluator') is not None


def public(skill):
    return json.loads((ROOT / 'skills' / skill / 'evals/evals.json').read_text())


def run_gate(skill, *args):
    return subprocess.run([sys.executable, '-B', str(ROOT / 'tools/skill_evaluation.py'),
                           'check', skill, *map(str, args)], capture_output=True, text=True)


class CaseTests(unittest.TestCase):
    def test_handoff_decisions_and_supersession(self):
        handoff = gate.strict_json(ROOT / gate.COMMON['case-inputs/handoff.json'])
        self.assertEqual(workflow.validate_state(handoff), ([], []))
        cases = public('koai-orchestrate')['evals']
        for case, used, limit in [(cases[0], 'minutes_since_checkpoint', 'checkpoint_minutes'),
                                  (cases[1], 'iterations_used', 'max_iterations')]:
            state = deepcopy(handoff)
            state['usage'][used] = state['limits'][limit]
            decision = workflow.decide(state)
            for field in ('status', 'reason'):
                self.assertEqual(decision[field], case['koai_facts'][field])
        records = workflow.recall_records(handoff)
        self.assertIn('evidence:axis-b', {item['id'] for item in records})
        self.assertNotIn('evidence:axis-a', {item['id'] for item in records})

    def test_ground_uses_pinned_contract(self):
        contract = gate.strict_json(ROOT / 'curriculum/contract.json')
        ground = public('koai-ground')['evals']
        self.assertEqual(ground[0]['koai_facts']['target_year'], contract['competition_year'])
        case = ground[1]['koai_facts']
        week2 = next(week for week in contract['weeks'] if week['week'] == 2)
        self.assertEqual(case['total_minutes'], sum(week2[key + '_minutes'] for key in ('coding', 'noncoding', 'theory')))
        self.assertEqual(case['written_minutes'], week2['written_minutes_within_noncoding'])

    def test_grader_numeric_and_invalid_controls(self):
        case = public('koai-evaluate')['evals'][1]
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'answer.json'
            for content, score in [
                ('{"fit_mean":4.0,"centered_validation":96.0,"leakage":true}', 1),
                ('{"fit_mean":"4","centered_validation":96,"leakage":true}', 0),
                ('{"fit_mean":4.01,"centered_validation":96,"leakage":true}', 0),
                ('{"fit_mean":4,"centered_validation":96,"leakage":1}', 0),
                ('{"fit_mean":4,"centered_validation":96,"leakage":false,"leakage":true}', 0),
                ('{"fit_mean":4,"centered_validation":96,"leakage":true,"other":1e400}', 0),
                ('{"fit_mean":4,"centered_validation":96,"leakage":true,"other":NaN}', 0),
                ('{"fit_mean":4,"centered_validation":96,"leakage":true,"other":Infinity}', 0),
                ('{' * 65537, 0), ('broken', 0),
            ]:
                with self.subTest(content=content[:50]):
                    file.write_text(content)
                    self.assertEqual(grader.grade(case, file)['custom_metrics']['koai_case_facts_correct'], score)

    def test_missing_answer_symlink_and_missing_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / 'answer.json'
            case = public('koai-recall')['evals'][0]
            self.assertEqual(grader.grade(case, file)['overall'], 0)
            (root / 'other').write_text(json.dumps(case['koai_facts']))
            file.symlink_to(root / 'other')
            self.assertEqual(grader.grade(case, file)['overall'], 0)
            with self.assertRaises(ValueError):
                grader.grade({}, file)

    def test_review_rejects_duplicates_and_reused_public_inputs(self):
        case = public('koai-ground')['evals'][0]
        public_path = ROOT / 'skills/koai-ground/evals/evals.json'
        entry = dict(case, question=case['prompt'])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'suite.json'
            receipt = Path(tmp) / 'review.json'
            record = {'status': 'reviewed', 'author': 'author-A', 'reviewer': 'reviewer-B'}
            receipt.write_text(json.dumps(record))
            self.assertTrue(gate.review_blockers(receipt, path, public_path, [entry], {}))
            receipt.write_text('{"status":"draft","status":"reviewed","author":"A","reviewer":"B"}')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                gate.review_blockers(receipt, path, public_path, [entry], {})


@unittest.skipUnless(NATIVE, 'Requires the pinned NVIDIA SkillEvaluator installation')
class NativeIntegrationTests(unittest.TestCase):
    def test_missing_exit_zero_is_blocked_and_workspace_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / 'debug'
            cmd = [sys.executable, '-B', str(ROOT / 'tools/skill_evaluation.py'), 'prepare', 'koai-ground',
                   str(dest), '--suite', str(root / 'missing.json'), '--pilot']
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            self.assertEqual((result.returncode, data['native_strict_exit'], data['status']), (1, 0, 'invalid'))
            self.assertTrue((dest / 'preparation.json').is_file())
            sentinel = dest / 'other-work.txt'
            sentinel.write_text('preserve')
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(sentinel.read_text(), 'preserve')

    def test_invalid_dataset_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'suite.json'
            for change in ['empty', 'control', 'duplicate_id', 'duplicate_prompt', 'wrong_trigger', 'key', 'duplicate_field']:
                cases = public('koai-ground')
                rows = cases['evals']
                if change == 'empty':
                    cases['evals'] = []
                elif change == 'control':
                    rows.pop(1)
                elif change == 'duplicate_id':
                    rows[1]['id'] = rows[0]['id']
                elif change == 'duplicate_prompt':
                    rows[1]['prompt'] = rows[0]['prompt'].upper()
                elif change == 'wrong_trigger':
                    rows[-1]['should_trigger'] = True
                elif change == 'key':
                    rows[0]['koai_facts'] = {}
                text = json.dumps(cases)
                if change == 'duplicate_field':
                    text = text.replace('"target_year": 2027', '"target_year": 1931, "target_year": 2027')
                path.write_text(text)
                with self.subTest(change=change), self.assertRaises(ValueError):
                    gate.load_cases(path, 'koai-ground')
            path.write_text('{"skill_name":"koai-ground", "evals":[]}')
            p = run_gate('koai-ground', '--suite', path, '--pilot')
            self.assertEqual((p.returncode, json.loads(p.stdout)['status']), (1, 'invalid'))

    def test_eligibility_and_frozen_review(self):
        p = run_gate('koai-ground')
        initial = json.loads(p.stdout)
        self.assertEqual((p.returncode, initial['status'], initial['case_count']), (1, 'provisional', 3))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            suite, receipt = root / 'private.json', root / 'review.json'
            items = []
            templates = public('koai-ground')['evals']
            for i in range(10):
                case = deepcopy(templates[i % 3])
                case.update(id=f'synthetic-gate-{i}', prompt=f'Gate regression control {i}: record value = {i}.',
                            expected_output=f'Value {i}.', assertions=['Records the supplied number.'], koai_facts={'value': i})
                items.append(case)
            suite.write_text(json.dumps({'skill_name': 'koai-ground', 'evals': items}))
            provisional = run_gate('koai-ground', '--suite', suite, '--pilot')
            summary = json.loads(provisional.stdout)
            self.assertEqual((provisional.returncode, summary['status']), (0, 'provisional'))
            record = {key: summary[key] for key in ('dataset_sha256', 'context_sha256', 'grader_sha256')}
            record.update(status='reviewed', author='synthetic-author', reviewer='synthetic-reviewer')
            receipt.write_text(json.dumps(record))
            eligible = run_gate('koai-ground', '--suite', suite, '--review', receipt)
            self.assertEqual((eligible.returncode, json.loads(eligible.stdout)['status']), (0, 'reviewed_inputs'))
            self.assertEqual(json.loads(eligible.stdout)['live_agent_runs'], 0)
            for changed in [dict(record, reviewer=record['author']), dict(record, dataset_sha256='0' * 64)]:
                receipt.write_text(json.dumps(changed))
                p = run_gate('koai-ground', '--suite', suite, '--review', receipt, '--pilot')
                self.assertNotEqual(p.returncode, 0)

    def test_real_harbor_pair_and_standard_reward_merge(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / 'pair'
            cmd = [sys.executable, '-B', str(ROOT / 'tools/skill_evaluation.py'), 'prepare', 'koai-evaluate',
                   str(dest), '--pilot']
            p = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            report = json.loads(p.stdout)
            self.assertEqual((report['pairs_prepared'], report['live_agent_runs']), (3, 0))
            self.assertTrue(report['matches_reference_python'])
            cases = gate.load_cases(ROOT / 'skills/koai-evaluate/evals/evals.json', 'koai-evaluate')
            target = dest / report['prepared_skill']
            common = {key: gate.digest(dest / 'repo' / key) for key in gate.common_sources(target.name)}
            tasks = [dest / 'without' / row['id'] for row in cases]
            (tasks[0] / 'environment/repo/unexpected.txt').write_text('unexpected material')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                gate.verify_arm(tasks, cases, target, common, False)
            tests = dest / 'with/evaluate-temporal-center/tests'
            (root / 'workspace/output').mkdir(parents=True)
            (root / 'verifier').mkdir()
            workspace = root / 'workspace'
            # Nonstandard receipt filenames also exercise the official environment overrides.
            reward_json = root / 'verifier/result.json'
            reward_txt = root / 'verifier/result.txt'
            env = {**os.environ, 'HARBOR_WORKSPACE_DIR': str(workspace), 'HARBOR_TESTS_DIR': str(tests),
                   'HARBOR_VERIFIER_DIR': str(reward_json.parent), 'HARBOR_REWARD_JSON': str(reward_json),
                   'HARBOR_REWARD_TXT': str(reward_txt)}
            for value, expected in [(4.0, 1), ('4', 0)]:
                (workspace / 'output/answer.json').write_text(json.dumps({'fit_mean': value, 'centered_validation': 96.0,
                                                                           'leakage': True}))
                # A controlled standard reward tests native merge behavior without an agent or judge.
                (root / 'verifier/skill_evaluator_reward.json').write_text('{"overall":0.625,"accuracy":0.75}')
                reward_txt.write_text('0.625\n')
                subprocess.run([sys.executable, '-I', str(tests / 'skill_evaluator/custom_grader_runner.py'),
                                '--mode', 'default_plus_custom'], env=env, check=True, capture_output=True)
                self.assertEqual(json.loads(reward_json.read_text()),
                                 {'overall': 0.625, 'accuracy': 0.75, 'koai_case_facts_correct': expected})
                self.assertEqual(reward_txt.read_text(), '0.625\n')


if __name__ == '__main__':
    unittest.main()
