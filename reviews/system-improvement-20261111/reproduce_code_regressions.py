#!/usr/bin/env python3
"""Compare pinned pre-fix implementations with current code on identical controls."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'tests')]
import contest_depth
import quality
import workflow
from test_contest_depth import synthetic_bundle

BASE = '64f24aabdad2b1976740d88d4a0ba74a4ed89766'

def main():
    def read(name):
        return json.loads((ROOT / name).read_text())
    cases = []
    def record(name, before, after, expected):
        cases.append({'case': name, 'before': before, 'after': after, 'expected_after': expected,
                      'passed': after == expected and before != after})
    with tempfile.TemporaryDirectory(prefix='koai-original-code-') as folder:
        modules = {}
        for name in ('workflow', 'contest_depth'):
            path = Path(folder) / (name + '.py')
            source = subprocess.check_output(['git', 'show', BASE + ':tools/' + name + '.py'], cwd=ROOT)
            path.write_bytes(source)
            spec = importlib.util.spec_from_file_location('old_' + name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            modules[name] = module
        state = read('examples/quality-workflow.json')
        report = quality.evaluate(read('examples/quality.json'))
        next(x for x in state['context']['inputs'] if x['id'] == 'quality:bundle')['note'] = 'A human annotation only.'
        record('quality_manifest_annotation', modules['workflow'].decide(state, report)['reason'],
               workflow.decide(state, report)['reason'], 'verified_candidate_within_budget')
        state = read('examples/workflow.json')
        state['frozen']['rubric']['note'] = 'A human annotation only.'
        record('frozen_manifest_annotation', modules['workflow'].decide(state)['reason'],
               workflow.decide(state)['reason'], 'verified_candidate_within_budget')
        bundle = synthetic_bundle()
        second = copy.deepcopy(bundle['comparisons'][0]); second['id'] = 'foundation'
        bundle['comparisons'].append(second)
        bundle['unknowns'] = [{'description': 'Only one selected comparison is unresolved.',
                               'comparison_ids': ['comparison:synthetic']}]
        status = lambda module: [x['status'] for x in module.inspect(bundle)['comparisons']]
        record('scoped_unknown_neighbor', status(modules['contest_depth']), status(contest_depth), ['uncertain', 'met'])
        bundle = synthetic_bundle(); bundle['time_allocations'][0]['outside_class_minutes'] = None
        count = lambda module: sum(x['code'] == 'incomplete_time' for x in module.inspect(bundle)['findings'])
        record('outside_time_not_class_failure', count(modules['contest_depth']), count(contest_depth), 0)
    output = {'baseline_code_commit': BASE, 'synthetic_controls': True, 'cases': cases,
              'status': 'passed' if all(x['passed'] for x in cases) else 'failed',
              'limits': 'These controls verify implementation behavior, not source truth or educational judgment.'}
    print(json.dumps(output, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if output['status'] == 'passed' else 1

if __name__ == '__main__':
    raise SystemExit(main())
