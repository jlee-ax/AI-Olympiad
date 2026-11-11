#!/usr/bin/env python3
"""Reproduce old/new plan binding and check that later drift is detected."""
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import quality

OLD = ROOT / 'reviews/week01-integration-20261111/plan-revision'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / 'curriculum').mkdir()
        plan = root / 'curriculum/student-plan.html'
        contract = root / 'curriculum/contract.json'
        shutil.copyfile(OLD / 'student-plan-v1.html', plan)
        shutil.copyfile(OLD / 'contract-v1.json', contract)
        old = quality.baseline(root)
        assert old['status'] == 'passed', old

        shutil.copyfile(ROOT / 'curriculum/student-plan.html', plan)
        changed = quality.baseline(root)
        assert changed['status'] == 'failed'
        assert changed['errors'] == ['Student HTML does not match the pinned baseline']

        shutil.copyfile(ROOT / 'curriculum/contract.json', contract)
        current = quality.baseline(root)
        assert current['status'] == 'passed', current
        plan.write_text(plan.read_text().replace('통합 Jupyter', '수정 Jupyter', 1))
        tampered = quality.baseline(root)
        assert tampered['status'] == 'failed'
        assert 'Student HTML does not match the pinned baseline' in tampered['errors']

        previous = json.loads((OLD / 'contract-v1.json').read_text())
        revised = json.loads((ROOT / 'curriculum/contract.json').read_text())
        assert previous['weeks'] == revised['weeks'] and previous['topics'] == revised['topics']
        assert previous['baseline']['sha256'] == digest(OLD / 'student-plan-v1.html')
        assert revised['baseline']['sha256'] == digest(ROOT / 'curriculum/student-plan.html')
        old_template = json.loads((OLD / 'quality-template-v1.json').read_text())
        new_template = json.loads((ROOT / 'templates/quality.json').read_text())
        old_result = quality.plan_work(old_template, ROOT)
        new_result = quality.plan_work(new_template, ROOT)
        assert old_result['reason'] == 'baseline_or_artifact_binding_failed'
        assert new_result['reason'] == 'priority_policy_requires_agreement'
        assert not new_template['policy']['agreed']
        unchanged = json.loads(json.dumps(old_template))
        unchanged['revision'] = new_template['revision']
        unchanged['artifact']['revision'] = new_template['artifact']['revision']
        unchanged['artifact']['sha256'] = new_template['artifact']['sha256']
        assert unchanged == new_template
        print(json.dumps({
            'old_snapshot': old['status'], 'changed_plan_old_pin': changed['status'],
            'new_revision': current['status'], 'later_drift': tampered['status'],
            'previous_plan_sha256': previous['baseline']['sha256'],
            'new_plan_sha256': revised['baseline']['sha256'],
            'weeks_and_topics_unchanged': True,
            'old_template_with_current_plan': old_result['reason'],
            'new_template_unagreed': new_result['reason'],
            'template_policy_and_budget_unchanged': True,
            'scope': 'Plan binding and schedule structure only; no historical review or learner outcome is promoted.'
        }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
