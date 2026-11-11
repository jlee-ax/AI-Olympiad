#!/usr/bin/env python3
"""Prepare and run an isolated copy of current tools/specs and a lesson snapshot.

This protects the input worktrees from writes; it is not an OS security sandbox.
Only explicitly requested notebook code is executed, inside the copied workspace.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MARKER = '.lesson-validation.json'
TOOL_DIRS = ('tools', 'skills', 'templates', 'examples', 'tests')
LESSON_DIRS = ('lessons', 'reviews', 'curriculum')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root, directories):
    result = {}
    for directory in directories:
        folder = root / directory
        if folder.is_symlink() or not folder.is_dir():
            raise ValueError('Required input directory is absent or symlinked: ' + str(folder))
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise ValueError('Symlink input is not copied: ' + str(path))
            if path.is_file():
                result[str(path.relative_to(root))] = sha(path)
    return result


def prepare(tool_root, lesson_root, output):
    tool_root, lesson_root, output = (Path(x).resolve() for x in (tool_root, lesson_root, output))
    if output.exists() or any(output.is_relative_to(r) for r in (tool_root, lesson_root)):
        raise ValueError('Output must be new and outside both input worktrees')
    tool_files = snapshot(tool_root, TOOL_DIRS)
    lesson_files = snapshot(lesson_root, LESSON_DIRS)
    manifest = {'schema_version': 1, 'tool_root': str(tool_root), 'lesson_root': str(lesson_root),
                'output_root': str(output), 'tool_files': tool_files, 'lesson_files': lesson_files,
                'limit': 'Input preservation and versioned copy, not an OS execution boundary.'}
    output.mkdir(parents=True)
    for root, directories in ((tool_root, TOOL_DIRS), (lesson_root, LESSON_DIRS)):
        for directory in directories:
            shutil.copytree(root / directory, output / directory)
    for files in (tool_files, lesson_files):
        for name, expected in files.items():
            if sha(output / name) != expected:
                raise ValueError('Copied bytes differ: ' + name)
    (output / MARKER).write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    return manifest


def check_inputs(manifest):
    changed = []
    for layer in ('tool', 'lesson'):
        root = Path(manifest[layer + '_root'])
        try:
            current = snapshot(root, TOOL_DIRS if layer == 'tool' else LESSON_DIRS)
        except (OSError, ValueError) as exc:
            changed.append(layer + ':' + str(exc))
            continue
        expected_files = manifest[layer + '_files']
        for name in sorted(set(current) - set(expected_files)):
            changed.append(layer + ':added:' + name)
        for name, expected in expected_files.items():
            path = root / name
            if not path.is_file() or path.is_symlink() or sha(path) != expected:
                changed.append(layer + ':' + name)
    return changed


def run(root, python=sys.executable, execute=False, dependency_path=None):
    root = Path(root).resolve()
    marker = root / MARKER
    manifest = json.loads(marker.read_text())
    if manifest['output_root'] != str(root):
        raise ValueError('Marker does not identify this prepared workspace')
    if check_inputs(manifest):
        raise ValueError('Inputs changed since preparation; prepare a fresh workspace')
    for files in (manifest['tool_files'], manifest['lesson_files']):
        for name, expected in files.items():
            path = root / name
            if path.is_symlink() or not path.is_file() or sha(path) != expected:
                raise ValueError('Prepared copy changed before execution: ' + name)
    output = root / 'validation-current'
    if output.is_symlink():
        raise ValueError('Validation output cannot be a symlink')
    output.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', MPLCONFIGDIR=str(output / 'mpl'),
               IPYTHONDIR=str(output / 'ipython'), JUPYTER_RUNTIME_DIR=str(output / 'jupyter'))
    if dependency_path:
        dep = Path(dependency_path).resolve(strict=True)
        if not dep.is_dir():
            raise ValueError('Dependency path must be a directory')
        env['PYTHONPATH'] = str(dep)
    receipts = []
    def command(name, args):
        proc = subprocess.run([str(python), '-B', *args], cwd=root, env=env, capture_output=True, text=True, timeout=600)
        (output / (name + '.stdout')).write_text(proc.stdout)
        (output / (name + '.stderr')).write_text(proc.stderr)
        receipts.append({'name': name, 'argv': [str(python), '-B', *args], 'exit_code': proc.returncode,
                         'stdout_sha256': sha(output / (name + '.stdout')), 'stderr_sha256': sha(output / (name + '.stderr'))})
        return proc
    command('latest-baseline', ['tools/quality.py', 'baseline', '--root', str(root)])
    historical = 'reviews/week01/final-followup/quality.json'
    command('latest-tool-historical-bundle', ['tools/quality.py', 'evaluate', historical, '--root', str(root)])
    execution, execution_errors, accepted_hashes = None, [], None
    if execute and json.loads((root / historical).read_text())['artifact']['path'] != 'lessons/week01/week01_python_tables.ipynb':
        execution_errors.append('Requested bundle artifact is not the Week 1 notebook being executed')
        execute = False
    if execute:
        # Both scripts execute reviewed lesson/key code; neither runs by default.
        notebook_path = root / 'lessons/week01/week01_python_tables.ipynb'
        before_book = json.loads(notebook_path.read_text())
        projection = lambda book: [{k: c.get(k) for k in ('id', 'cell_type', 'source', 'attachments')} for c in book['cells']]
        code_count = sum(c['cell_type'] == 'code' for c in before_book['cells'])
        receipt = root / 'lessons/week01/validation.json'
        receipt.unlink(missing_ok=True)  # Never accept a copied historical receipt.
        started = datetime.now(timezone.utc)
        proc = command('fresh-notebook', ['lessons/week01/validate_week01.py', '--inprocess'])
        if proc.returncode == 0:
            try:
                candidate = json.loads(receipt.read_text())
                after_book = json.loads(notebook_path.read_text())
                timestamp = datetime.fromisoformat(candidate['checked_at_utc'])
                if timestamp.tzinfo is None or not started - timedelta(seconds=5) <= timestamp <= datetime.now(timezone.utc) + timedelta(seconds=5):
                    raise ValueError('Execution receipt is not current')
                required_passes = ('nbformat_validation', 'top_to_bottom_execution', 'actual_function_and_state_assertions',
                                   'teacher_modification_key_tests', 'independent_fraction_arithmetic',
                                   'csv_mask_shape_missing_and_merge_checks', 'standalone_without_csv_files')
                if any(candidate.get(k) != 'passed' for k in required_passes):
                    raise ValueError('Execution checks did not pass')
                if (candidate.get('notebook_sha256') != sha(notebook_path) or
                    type(candidate.get('executed_code_cells')) is not int or type(candidate.get('code_cells')) is not int or
                    candidate.get('executed_code_cells') != code_count or candidate.get('code_cells') != code_count or
                    type(candidate.get('error_outputs')) is not int or candidate.get('error_outputs') != 0 or
                    candidate.get('execution_method') != 'fresh IPython InProcessKernelManager per run' or
                    candidate.get('source_projection_unchanged_by_execution') is not True or
                    candidate.get('student_answers') != 'blank_not_assessed' or candidate.get('student_mastery') != 'not_observed' or
                    projection(before_book) != projection(after_book)):
                    raise ValueError('Execution receipt does not match actual artifact/counts/source/learner scope')
                execution = candidate
                accepted_hashes = (sha(notebook_path), sha(receipt))
            except (OSError, ValueError, TypeError, KeyError) as exc:
                execution_errors.append(str(exc))
        command('actual-depth-checks', ['reviews/week01/contest-depth/check_depth.py'])
        if accepted_hashes and (sha(notebook_path), sha(receipt)) != accepted_hashes:
            execution_errors.append('Notebook/receipt changed after accepted execution during depth checks')
            execution = None
    bundle = json.loads((root / historical).read_text())
    notebook = root / bundle['artifact']['path']
    bundle['revision'] = 'week01-current-validation-copy'
    bundle['artifact']['sha256'] = sha(notebook)
    if execution:
        receipt_path = 'lessons/week01/validation.json'
        for unit in bundle['units']:
            # Execution describes examples/assertions, never unfilled learner work.
            unit['execution'] = {'status': 'passed', 'artifact_sha256': sha(notebook),
                                 'command': ' '.join(next(r['argv'] for r in receipts if r['name'] == 'fresh-notebook')), 'environment': execution['execution_method'],
                                 'exit_code': 0, 'clean_run': True, 'new_input': True,
                                 'assertions': [{'name': str(execution['code_cells']) + ' supplied code cells and changed-input assertions; learner cells blank', 'status': 'passed'}],
                                 'evidence': [{'path': receipt_path, 'sha256': sha(root / receipt_path), 'locator': 'full receipt',
                                               'observation': 'Actual copied-artifact execution; no learner solution or mastery observed.'}]}
    bundle.setdefault('operator_notes', {})['current_validation'] = 'Current artifact/execution binding only. Historical content reviews are retained; no automatic promotion to a fresh semantic pass.'
    current = output / 'quality.json'
    current.write_text(json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    command('latest-tool-current-bundle', ['tools/quality.py', 'evaluate', str(current), '--root', str(root)])
    current_result_invalidated = False
    if accepted_hashes and (sha(notebook_path), sha(receipt)) != accepted_hashes:
        execution_errors.append('Final notebook/receipt no longer matches accepted execution')
        execution = None
        current_result_invalidated = True
        bundle['artifact']['sha256'] = sha(notebook)
        for unit in bundle['units']:
            unit['execution']['status'] = 'not_run'
            unit['execution']['evidence'] = []
        bundle['operator_notes']['current_validation'] += ' Execution evidence invalidated by later changes; reevaluation required.'
        current.write_text(json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    changed = check_inputs(manifest)
    mutable = {'lessons/week01/week01_python_tables.ipynb', 'lessons/week01/week01_python_tables.html',
               'lessons/week01/validation.json'} if execute else set()
    changed_copy = []
    for name in sorted(set(snapshot(root, TOOL_DIRS)) - set(manifest['tool_files'])):
        changed_copy.append('added:' + name)
    for files in (manifest['tool_files'], manifest['lesson_files']):
        for name, expected in files.items():
            path = root / name
            if name not in mutable and (path.is_symlink() or not path.is_file() or sha(path) != expected):
                changed_copy.append(name)
    report = {'status': 'passed' if not changed and not changed_copy and not execution_errors and all(r['exit_code'] == 0 for r in receipts) else 'failed',
              'execution_errors': execution_errors, 'current_quality_result_invalidated': current_result_invalidated,
              'receipts': receipts, 'input_changes': changed, 'unexpected_copy_changes': changed_copy,
              'copied_artifact_sha256': sha(notebook), 'execution': execution,
              'current_bundle': str(current.relative_to(root)),
              'limits': ['Command exit zero means evaluation ran, not that educational criteria passed.',
                         'Historical reviews remain historical; current-context semantic review and observations are separate.',
                         'This workspace does not add network isolation, a worker, a scheduler, student answers or learner evidence.']}
    (output / 'run.json').write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare')
    for name in ('tool-root', 'lesson-root', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p = sub.add_parser('run')
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--python', default=sys.executable)
    p.add_argument('--dependency-path', type=Path)
    p.add_argument('--execute-notebook', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = prepare(args.tool_root, args.lesson_root, args.output) if args.command == 'prepare' else run(args.root, args.python, args.execute_notebook, args.dependency_path)
        if args.command == 'prepare':
            result = {'status': 'prepared', 'output_root': result['output_root'], 'tool_file_count': len(result['tool_files']), 'lesson_file_count': len(result['lesson_files'])}
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result = {'status': 'invalid', 'error': str(exc)}
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if result['status'] in ('prepared', 'passed') else 1


if __name__ == '__main__':
    raise SystemExit(main())
