#!/usr/bin/env python3
"""Apply the new checks to copies of the pinned real Week 1 records.

The seven-role declarations below are a declaration-only projection, not observed
learner independence or an automated judgment of lesson adequacy. No source or
lesson worktree is changed. Run with --lesson-root pointing at commit 204743d.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import contest_depth
import graph_paths
import review_preflight
from validate import validate


def project_declared_paths(depth, original, root):
    """Reproduce the declaration-only projection; generic feedback is not semantically complete."""
    prefix = 'reviews/week01/contest-depth/'
    notebook = json.loads((root / depth['target']['artifact']).read_text(encoding='utf-8'))
    cells = {c['id'] for c in notebook['cells']}
    graph = copy.deepcopy(original)
    paths = {'schema_version': 1, 'synthetic': False, 'required_demands': [], 'paths': []}
    # These actual locations were read; each task remains bounded to a foundation.
    locations = {
        'axis-choice': ('e594ea69', 'depth-reshape-compare', 'depth-reshape-code', 'depth-reshape-response'),
        'function-spec': ('7208718e', 'depth-function-spec', 'depth-function-code', 'depth-function-response'),
        'written-format': ('e594ea69', 'ebbfd3db', '3468f4e4', '71068cea'),
        'variance-units': ('409e1675', '9ce91662', 'c6ef56e6', '9ce91662'),
    }
    for index, comparison in enumerate(depth['comparisons']):
        cid = comparison['id']
        prereq, theory, code, assessment = locations[cid]
        if not {prereq, theory, code, assessment, 'guided-feedback-and-support'} <= cells:
            raise ValueError('Audited notebook locator is absent')
        roles = {role: f'audit:{cid}:{role}' for role in graph_paths.ROLES}
        for role, identifier in roles.items():
            graph['nodes'].append({'id': identifier, 'type': 'evidence', 'status': 'verified',
                                   'label': f'Declared {cid} {role}; task design only'})
        graph['edges'].extend({'from': roles[a], 'to': roles[b], 'type': 'supports'}
                              for a, b in zip(graph_paths.ROLES, graph_paths.ROLES[1:]))
        paths['required_demands'].append(roles['demand'])
        provenance = {}
        for role, locator in [('source', f'problem_sources; comparisons[{index}].scope_refs/problem_refs'),
                              ('demand', f'comparisons[{index}].competency/rationale'),
                              ('prerequisite', 'cell:' + prereq), ('theory_explanation', 'cell:' + theory),
                              ('coding_practice', 'cell:' + code), ('independent_assessment', 'cell:' + assessment),
                              ('feedback', 'cell:guided-feedback-and-support')]:
            name = prefix + 'candidate-depth.json' if role in ('source', 'demand') else depth['target']['artifact']
            provenance[role] = {'path': name, 'sha256': hashlib.sha256((root / name).read_bytes()).hexdigest(),
                                'locator': locator, 'revision': '204743d94a4176ace81c64f138567c2cc12041d1',
                                'origin': 'Recorded source read and comparison, not authenticated source truth' if role in ('source', 'demand') else 'Actual Week 1 notebook; task design, learner performance unobserved'}
        paths['paths'].append({'id': 'path:' + cid, 'comparison_id': cid, 'roles': roles, 'provenance': provenance,
                               'assessment': {'independent': True, 'allowed_support': comparison['allowed_support'],
                                              'answer_conditions': comparison['answer_conditions']}})
    return graph, paths


def problem_feedback_paths(paths, root):
    """Bind the actual problem-specific teacher key, preserving all other declarations."""
    corrected = copy.deepcopy(paths)
    locators = {'axis-choice': 'lines:115-119', 'function-spec': 'lines:120-138',
                'written-format': 'lines:53-59', 'variance-units': 'lines:141-147'}
    name = 'lessons/week01/teacher-notes.txt'
    digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
    for item in corrected['paths']:
        item['provenance']['feedback'].update(path=name, sha256=digest, locator=locators[item['comparison_id']],
                                               origin='Actual teacher key and rationale; learner performance unobserved')
    return corrected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lesson-root', type=Path, required=True)
    args = parser.parse_args()
    source = args.lesson_root.resolve()
    read = lambda name: json.loads((source / name).read_text(encoding='utf-8'))
    prefix = 'reviews/week01/contest-depth/'
    depth = read(prefix + 'candidate-depth.json')
    original = read(prefix + 'candidate-graph.json')
    state = read('reviews/week01/final-followup/workflow.json')
    baseline = contest_depth.inspect(read(prefix + 'baseline-depth.json'))
    candidate = contest_depth.inspect(depth)
    cases = []
    def record(name, expected, actual, **evidence):
        cases.append({'case': name, 'expected': expected, 'actual': actual,
                      'passed': expected == actual, **evidence})

    record('historical_graph_structure', 'valid', 'invalid' if validate(original)[0] else 'valid')
    with tempfile.TemporaryDirectory(prefix='koai-real-review-') as folder:
        root = Path(folder)
        for name in [depth['target']['artifact'], 'lessons/week01/teacher-notes.txt',
                     prefix + 'candidate-depth.json', 'lessons/week01/lesson-manifest.json']:
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, dest)
        missing = graph_paths.inspect_paths(original, {}, root)
        record('historical_graph_missing_path_declaration', 'gap', missing['status'])
        graph, paths = project_declared_paths(depth, original, root)
        good = graph_paths.inspect_paths(graph, paths, root)
        record('real_record_projection_with_all_four_declared_paths', 'declared_path_complete', good['status'],
               scope='All four recorded comparison paths only; does not cover every notebook objective or prove independent performance.')
        followup = ROOT / 'reviews/system-followup-20261111'
        generic_review = json.loads((followup / 'generic-feedback-semantic-review.json').read_text(encoding='utf-8'))
        generic = graph_paths.inspect_semantic_review(graph, paths, generic_review, root)
        record('known_wrong_generic_feedback_is_mechanical_complete_but_semantic_gap', 'gap', generic['status'],
               mechanical_status=generic['mechanical_status'], comparisons=generic['comparisons'], findings=generic['findings'])
        corrected_paths = problem_feedback_paths(paths, root)
        corrected_review = json.loads((followup / 'problem-feedback-semantic-review.json').read_text(encoding='utf-8'))
        corrected = graph_paths.inspect_semantic_review(graph, corrected_paths, corrected_review, root)
        record('actual_problem_specific_keys_preserve_variance_independence_uncertainty', 'uncertain', corrected['status'],
               mechanical_status=corrected['mechanical_status'], comparisons=corrected['comparisons'], findings=corrected['findings'])
        record('mechanical_completeness_without_current_review_is_not_semantic_pass', 'gap',
               graph_paths.inspect_semantic_review(graph, corrected_paths, None, root)['status'])
        broken = copy.deepcopy(graph)
        broken['edges'].pop()
        record('same_real_projection_missing_feedback_edge', 'gap', graph_paths.inspect_paths(broken, paths, root)['status'])
        before = (root / depth['target']['artifact']).read_bytes()
        (root / depth['target']['artifact']).write_bytes(before + b'\n')
        record('same_real_projection_changed_notebook_bytes', 'stale', graph_paths.inspect_paths(graph, paths, root)['status'])
        (root / depth['target']['artifact']).write_bytes(before)
        record('restored_exact_notebook_bytes', 'declared_path_complete', graph_paths.inspect_paths(graph, paths, root)['status'])
        # Copy every available declared local source, including unrecalled/superseded evidence.
        for entry in state['sources']:
            name = entry['uri']
            candidate_path = source / name
            if '://' not in name and candidate_path.is_file():
                dest = root / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(candidate_path, dest)
        report = review_preflight.preflight(root, depth, graph, paths, state)
        record('actual_old_workflow_is_not_silently_rebound', 'blocked', report['status'],
               blockers=report['blockers'], workflow=report['workflow'])
        used = {ref['source_id'] for recalled in review_preflight.workflow.recall_records(state)
                for ref in recalled['source_refs']}
        source_register = next(item for item in state['sources'] if item['id'] == 'source-register')
        register_binding = next(item for item in report['bindings'] if item.get('source_id') == 'source-register')
        record('actual_context_only_register_is_omitted_by_legacy_active_recall_filter', False,
               source_register['id'] in used, legacy_checked_ids=sorted(used), binding=register_binding,
               scope='Reproduces the previous active-source selection rule; no aggregate old-tool pass is claimed.')
        register_copy = root / source_register['uri']
        register_bytes = register_copy.read_bytes()
        actual_digest = hashlib.sha256(register_bytes).hexdigest()
        actual_stale = actual_digest != source_register['sha256']
        record('actual_context_only_register_current_binding', actual_stale,
               any(item['code'] == 'stale_declared_source' and item['detail'] == source_register['uri']
                   for item in report['blockers']), binding=register_binding,
               scope='The baseline may be stale before integration and match after its source version is restored.')
        register_copy.write_bytes(register_bytes + b'\nChanged only on the temporary copy.\n')
        changed_register = review_preflight.preflight(root, depth, graph, paths, state)
        record('actual_context_only_register_changed_copy_blocks', True,
               any(item['code'] == 'stale_declared_source' and item['detail'] == source_register['uri']
                   for item in changed_register['blockers']))
        register_copy.write_bytes(register_bytes)
        review_source = next(item for item in state['sources'] if item['id'] == 'independent-material-review')
        review_binding = next(item for item in report['bindings'] if item.get('source_id') == review_source['id'])
        record('actual_superseded_unrecalled_material_review_current_bytes_are_checked', True,
               review_binding['matched'], binding=review_binding, actively_recalled=review_source['id'] in used)
        review_copy = root / review_source['uri']
        review_bytes = review_copy.read_bytes()
        review_copy.write_bytes(review_bytes + b'\nChanged only on the temporary copy.\n')
        changed = review_preflight.preflight(root, depth, graph, paths, state)
        changed_binding = next(item for item in changed['bindings'] if item.get('source_id') == review_source['id'])
        record('actual_superseded_unrecalled_material_review_changed_copy_blocks', True,
               any(item['code'] == 'stale_declared_source' and item['detail'] == review_source['uri']
                   for item in changed['blockers']), binding=changed_binding)
        review_copy.unlink()
        unavailable = review_preflight.preflight(root, depth, graph, paths, state)
        missing_blockers = [item for item in unavailable['blockers']
                            if item['code'] == 'unreadable_declared_source' and review_source['uri'] in item['detail']]
        record('actual_superseded_unrecalled_material_review_missing_copy_blocks', True,
               bool(missing_blockers), blockers=missing_blockers)
        review_copy.write_bytes(review_bytes)
        generic_joined = review_preflight.preflight(root, depth, graph, paths, state, semantic_review=generic_review)
        record('actual_joined_preflight_preserves_generic_feedback_gap', 'gap',
               generic_joined['semantic_review']['status'], blockers=generic_joined['blockers'])
        corrected_joined = review_preflight.preflight(root, depth, graph, corrected_paths, state,
                                                    semantic_review=corrected_review)
        record('actual_joined_preflight_preserves_corrected_feedback_uncertainty', 'uncertain',
               corrected_joined['semantic_review']['status'], blockers=corrected_joined['blockers'])
        (root / 'depth.json').write_text(json.dumps(depth))
        (root / 'graph.json').write_text(json.dumps(graph))
        (root / 'paths.json').write_text(json.dumps(paths))
        (root / 'state.json').write_text(json.dumps(state))
        proc = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/review_preflight.py'), '--root', str(root),
                               '--depth', 'depth.json', '--graph', 'graph.json', '--paths', 'paths.json', '--state', 'state.json'],
                              capture_output=True, text=True)
        record('actual_copy_joined_cli_blocks_stale_context', 1, proc.returncode)
    record('actual_baseline_depth', 'gap', baseline['status'], gaps=baseline['gaps'])
    record('actual_candidate_preserves_uncertainty', 'uncertain', candidate['status'],
           findings=candidate['findings'], comparisons=candidate['comparisons'])
    proc = subprocess.run([sys.executable, '-B', str(source / prefix / 'check_depth.py')],
                          cwd=source, capture_output=True, text=True)
    record('actual_quiz_array_function_variance_counterexamples', 0, proc.returncode,
           result=json.loads(proc.stdout) if proc.returncode == 0 else proc.stderr)
    output = {'lesson_commit': '204743d94a4176ace81c64f138567c2cc12041d1',
              'artifact_sha256': depth['target']['artifact_sha256'], 'cases': cases,
              'status': 'passed' if all(case['passed'] for case in cases) else 'failed',
              'limits': ['Graph repair tests explicit records on copies; no historical record or learner result is fabricated.',
                         'The four recorded comparisons do not cover the entire lesson; see whole-week01-review.md.',
                         'Passing controls preserve expected gaps/uncertainty and are not a semantic or whole-lesson pass.',
                         'The old real workflow remains paused pending genuine criteria decisions/current reviews.',
                         'No notebook re-execution, browser layout test, educator calibration or learner observation is claimed by this run.']}
    print(json.dumps(output, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if output['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
