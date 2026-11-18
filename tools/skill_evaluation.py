"""Check KOAI cases and prepare paired tasks with NVIDIA SkillEvaluator (see skill-evaluation.md)."""
import argparse
from hashlib import sha256
from importlib.metadata import version
from importlib.util import find_spec
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from quality import load as strict_json

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ('koai-ground', 'koai-recall', 'koai-orchestrate', 'koai-evaluate', 'koai-reflect')
CONTROLS = {'normal', 'fault', 'off_scope'}
UPSTREAM_REVISION = 'e3ede733f4d57578a1630b0579ea236b8cf8a727'
PINNED_PYTHON_SHA256 = '7170e3407f7c9328b2ba798b358ac1cfff4f167d70d6962624d5f1cf99751d61'
GRADER = ROOT / 'benchmarks/skill-evaluation/grader.py'
COMMON = {path: path for path in (
    'curriculum/contract.json', 'curriculum/student-plan.html', 'templates/workflow.json', 'examples/workflow.json',
    'lessons/week01/week01_integrated.ipynb', 'lessons/week02/week02_temporal_preprocessing.ipynb',
    'skills/references/criteria.json', 'skills/references/evidence.md',
    'skills/references/quality-specification.md', 'skills/references/source-readings.json',
    'skills/references/workflow.md', 'tools/workflow.py', 'tools/quality.py',
    'tools/validate.py', 'tools/graph_paths.py', 'tools/lesson_validation.py',
    'tools/review_preflight.py', 'tools/contest_depth.py', 'tools/discovery_loop.py',
    'tools/README.md', 'tools/review-preflight.md', 'tools/graph-paths.md', 'tools/discovery-loop.md',
    'tools/MANUAL-CYCLE.md', 'tests/fixtures/candidate-graph-missing-path.json',
    'examples/graph-path.json', 'examples/graph-path-source.txt',
)}
COMMON['case-inputs/handoff.json'] = 'benchmarks/skill-evaluation/handoff.json'

# Only these declarative Agent Skills fields are accepted for the KOAI answer-file contract.
FIELDS = {'id', 'prompt', 'expected_output', 'assertions', 'expected_skill',
          'should_trigger', 'koai_control', 'koai_facts'}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def manifest(folder):
    return {path.relative_to(folder).as_posix(): digest(path)
            for path in sorted(folder.rglob('*')) if path.is_file()}


def fingerprint(mapping):
    return sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest()


def provenance(target):
    package = Path(find_spec('skillevaluator').origin).parent
    sources = {file.relative_to(package).as_posix(): digest(file) for file in package.rglob('*.py')}
    package_hash = fingerprint(sources)
    bundle = {path: val for path, val in manifest(target).items() if not path.startswith('evals/')}
    return {'skill_bundle_sha256': fingerprint(bundle), 'skillevaluator_version': version('skillevaluator'),
            'skillevaluator_python_sha256': package_hash, 'reference_revision': UPSTREAM_REVISION,
            'matches_reference_python': package_hash == PINNED_PYTHON_SHA256}


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def canonical(text):
    return ' '.join(text.casefold().split())


def load_cases(path, skill):
    from skillevaluator.tier3.dataset_utils import load_dataset_entries

    raw = strict_json(path)
    if (not isinstance(raw, dict) or raw.get('skill_name') != skill
            or not isinstance(raw.get('evals'), list) or not raw['evals']):
        raise ValueError('Expected a nonempty Agent Skills JSON evals list for ' + skill)
    ids, prompts, controls = set(), set(), set()
    for case in raw['evals']:
        if not isinstance(case, dict) or set(case) != FIELDS:
            raise ValueError('Each KOAI case must use the documented declarative fields.')
        case_id, prompt, control = case['id'], case['prompt'], case['koai_control']
        if not isinstance(case_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,95}', case_id) or case_id in ids:
            raise ValueError(f'Invalid or repeated case ID: {case_id!r}')
        if not isinstance(prompt, str) or not prompt.strip() or canonical(prompt) in prompts:
            raise ValueError(f'{case_id}: empty or repeated prompt')
        if not isinstance(control, str) or control not in CONTROLS:
            raise ValueError(f'{case_id}: invalid koai_control')
        positive = control != 'off_scope'
        if case['should_trigger'] is not positive or case['expected_skill'] != (skill if positive else None):
            raise ValueError(f'{case_id}: trigger or expected skill disagrees with control')
        if not isinstance(case['expected_output'], str) or not case['expected_output'].strip():
            raise ValueError(f'{case_id}: missing expected output')
        if not isinstance(case['assertions'], list) or not case['assertions'] or not all(
            isinstance(item, str) and item.strip() for item in case['assertions']
        ):
            raise ValueError(f'{case_id}: missing observable assertions')
        if not isinstance(case['koai_facts'], dict) or not case['koai_facts']:
            raise ValueError(f'{case_id}: missing answer fields')
        ids.add(case_id)
        prompts.add(canonical(prompt))
        controls.add(control)
    if controls != CONTROLS:
        raise ValueError('Missing controls: ' + ', '.join(sorted(CONTROLS - controls)))
    return load_dataset_entries(path)


def review_blockers(receipt, source, public, entries, hashes):
    reasons = []
    if source.is_relative_to(ROOT):
        reasons.append('The checked-in suite is public development material.')
    public_cases = [case for path in sorted(public.parents[2].glob('*/evals/evals.json'))
                    for case in strict_json(path)['evals']]
    public_ids = {row['id'] for row in public_cases}
    public_prompts = {canonical(row['prompt']) for row in public_cases}
    if any(row['id'] in public_ids or canonical(row['question']) in public_prompts for row in entries):
        reasons.append('The suite reuses public case IDs or prompts.')
    if receipt is None:
        reasons.append('No independent review record supplied.')
        return reasons
    if not receipt.is_file():
        raise ValueError('The supplied independent review record is missing.')
    record = strict_json(receipt)
    if not isinstance(record, dict):
        raise ValueError('Independent review record must be an object.')
    author, reviewer = record.get('author'), record.get('reviewer')
    if (record.get('status') != 'reviewed' or not isinstance(author, str) or not author.strip()
            or not isinstance(reviewer, str) or not reviewer.strip() or canonical(author) == canonical(reviewer)):
        raise ValueError('Expected a reviewed record naming distinct author and reviewer.')
    if any(record.get(key) != value for key, value in hashes.items()):
        raise ValueError('The review record does not match the dataset, common inputs or grader.')
    return reasons


def common_sources(skill):
    files = dict(COMMON)
    # Keep the repository tools' canonical curriculum paths usable in both arms.
    # The evaluated role's procedural guides are treatment-owned when testing it.
    references = ROOT / 'skills/koai-evaluate/references'
    for path in sorted(references.iterdir()):
        if skill != 'koai-evaluate' or path.suffix == '.json':
            relative = path.relative_to(ROOT).as_posix()
            files[relative] = relative
    if skill == 'koai-evaluate':
        for relative in COMMON:
            if relative.startswith('skills/references/'):
                files[relative.replace('skills/', 'candidate/', 1)] = relative
    return files


def snapshot(repo, skill):
    folder = 'candidate' if skill == 'koai-evaluate' else 'skills'
    target = repo / folder / skill
    original = ROOT / 'skills' / skill
    copy_file(original / 'SKILL.md', target / 'SKILL.md')
    for folder in ('agents', 'references'):
        if (original / folder).is_dir():
            shutil.copytree(original / folder, target / folder)
    for relative, source in common_sources(skill).items():
        copy_file(ROOT / source, repo / relative)
    # The native adapter finds the full-context root by looking for a Git root.
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    return target


def assess(target, source, public, receipt):
    from skillevaluator.tier3.dataset_coverage import summarize_dataset
    from skillevaluator.tier3.dataset_sufficiency import assess_dataset_sufficiency
    from skillevaluator.tier3.dataset_utils import find_eval_file

    selected = target / 'evals/evals.json'
    if source is not None and source.is_file():
        copy_file(source, selected)
        copy_file(GRADER, selected.parent / 'grader.py')
        (selected.parent / 'config.yaml').write_text('schema_version: 1\ngrading:\n  mode: default_plus_custom\n')
    native = subprocess.run([sys.executable, '-m', 'skillevaluator.cli', 'tier3', 'validate', str(target), '--strict'],
                            text=True, capture_output=True)
    native_errors = (native.stdout + native.stderr).strip().splitlines()[-8:]
    report = {'skill': target.name, 'native_strict_exit': native.returncode, 'case_count': 0,
              'live_agent_runs': 0, 'evidence': 'input_validation', 'status': 'invalid', **provenance(target)}
    if find_eval_file(target) is None:
        report['errors'] = ['No dataset found. An exit code alone does not establish that cases exist.']
        return report, []
    if not report['matches_reference_python']:
        report['errors'] = ['The installed NVIDIA Python source differs from the tested revision.']
        return report, []
    if native.returncode:
        report['errors'] = ['NVIDIA strict validation failed.', *native_errors]
        return report, []
    try:
        entries = load_cases(selected, target.name)
        coverage = summarize_dataset(entries)
        policy = assess_dataset_sufficiency(distinct_cases=len(entries), negative_cases=coverage['negative_cases'],
                                            pass_rate_interval=None, paired_cases=None)
        size = next(check for check in policy['checks'] if check['name'] == 'coverage')
        hashes = {'dataset_sha256': digest(selected), 'grader_sha256': digest(GRADER),
                  'context_sha256': fingerprint({key: digest(target.parents[1] / key) for key in common_sources(target.name)})}
        blockers = review_blockers(receipt, source, public, entries, hashes)
    except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
        report['errors'] = [str(exc)]
        return report, []
    if not size['met']:
        blockers.append(size['reason'])
    if coverage['gaps']:
        report['errors'] = coverage['gaps']
        return report, []
    report.update(case_count=len(entries), coverage=coverage, coverage_policy=size, **hashes,
                  status='provisional' if blockers else 'reviewed_inputs', review_blockers=blockers)
    return report, entries


def verify_arm(paths, entries, target, common, with_skill):
    expected = {row['id']: row for row in entries}
    seen = set()
    skill_hash = digest(target / 'SKILL.md')
    prefix = target.relative_to(target.parents[1]).as_posix() + '/'
    bundle = {key: val for key, val in manifest(target).items() if not key.startswith('evals/')}
    verifier_hashes = {digest(target / 'evals/evals.json'), digest(GRADER)}
    for task in paths:
        tests, env = task / 'tests', task / 'environment'
        entry = strict_json(tests / 'entry.json')
        case_id = entry['id']
        if case_id in seen or case_id not in expected:
            raise ValueError('Unexpected or duplicate Harbor case: ' + case_id)
        seen.add(case_id)
        row = expected[case_id]
        if ((task / 'instruction.md').read_text(encoding='utf-8') != row['question'] + '\n'
                or json.dumps(entry.get('koai_facts'), sort_keys=True) != json.dumps(row['koai_facts'], sort_keys=True)
                or entry.get('has_skill') is not with_skill
                or not entry.get('custom_grader') or entry.get('grading_mode') != 'default_plus_custom'
                or digest(tests / 'grader.py') != digest(GRADER)):
            raise ValueError('Harbor prompt, arm or verifier mismatch: ' + case_id)
        repo_files = manifest(env / 'repo')
        common_files = {key: val for key, val in repo_files.items() if not key.startswith(prefix)}
        installed = manifest(env / 'skills')
        visible = {part + '/' + key: val for part, files in (
            ('repo', repo_files), ('skills', installed), ('input', manifest(env / 'input')),
            ('repo-linked-root', manifest(env / 'repo-linked-root'))) for key, val in files.items()}
        treatment = {prefix + key: val for key, val in bundle.items()} if with_skill else {}
        expected_install = {target.name + '/' + key: val for key, val in bundle.items()} if with_skill else {}
        if common_files != common or repo_files != {**common, **treatment} or installed != expected_install:
            raise ValueError('Shared fixture or installed skill mismatch: ' + case_id)
        if (skill_hash in visible.values()) is not with_skill:
            raise ValueError('Target instructions in the wrong arm: ' + case_id)
        if verifier_hashes.intersection(visible.values()) or any(
            set(Path(key).parts).intersection({'evals', 'eval', 'entry.json', 'grader.py'}) for key in visible
        ):
            raise ValueError('Evaluator material in an agent input: ' + case_id)
        # The native builder may add skill-owned files only to the treatment arm.
        if manifest(env / 'input') or manifest(env / 'repo-linked-root'):
            raise ValueError('Unexpected secondary agent input: ' + case_id)
    if seen != set(expected):
        raise ValueError('Harbor did not generate every case exactly once in each arm.')


def run(args):
    from skillevaluator.tier3.harbor.adapter import generate_harbor_tasks

    public = ROOT / 'skills' / args.skill / 'evals/evals.json'
    source = args.suite.resolve() if args.suite else public
    dest = args.destination.resolve() if args.destination else None
    if dest and (dest.is_relative_to(ROOT) or dest.exists() or not dest.parent.is_dir()):
        raise ValueError('Choose a new destination outside this checkout with an existing parent.')
    # A failed preparation stays private and intact for diagnosis; never delete a caller's files.
    if dest:
        dest.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix='koai-skill-check-') as temporary:
        work = dest if dest else Path(temporary)
        target = snapshot(work / 'repo', args.skill)
        report, entries = assess(target, source, public, args.review)
        allowed = bool(entries) and (report['status'] == 'reviewed_inputs' or args.pilot)
        if dest and allowed:
            common = {key: digest(work / 'repo' / key) for key in common_sources(args.skill)}
            for arm, enabled in [('with', True), ('without', False)]:
                paths = generate_harbor_tasks(target, work / arm, with_skill=enabled, copy_repo=True,
                                              grading_mode='default_plus_custom')
                verify_arm(paths, entries, target, common, enabled)
            report.update(evidence='paired_task_preparation', pairs_prepared=len(entries),
                          shared_files_per_arm=len(common), shared_sha256_equal=True,
                          target_available={'with': True, 'without': False}, verifier_inputs_exposed=False,
                          prepared_skill=target.relative_to(work).as_posix())
        if dest:
            with (work / 'preparation.json').open('x', encoding='utf-8') as output:
                output.write(json.dumps(report, indent=2) + '\n')
        return report, 0 if allowed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('check', 'prepare'):
        action = commands.add_parser(command)
        action.add_argument('skill', choices=SKILLS)
        action.add_argument('--suite', type=Path, help='An external KOAI Agent Skills JSON dataset.')
        action.add_argument('--review', type=Path, help='Independent review of these exact inputs.')
        action.add_argument('--pilot', action='store_true', help='Allow provisional inputs for a technical check.')
        if command == 'prepare':
            action.add_argument('destination', type=Path)
        else:
            action.set_defaults(destination=None)
    try:
        report, code = run(parser.parse_args())
    except (ImportError, OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        report, code = {'status': 'error', 'error': str(exc), 'live_agent_runs': 0}, 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
