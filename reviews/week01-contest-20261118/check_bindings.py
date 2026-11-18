"""Replay the real R6 entry and stale-input controls in a disposable local clone."""
import argparse
import json
from contextlib import contextmanager
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import topic_depth_basis as basis


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True).stdout


def check(root, operation='check', *, case=None, error=None):
    args = [sys.executable, '-B', str(root / 'tools/topic_depth.py'), operation, '--root', str(root)]
    if case:
        args.extend(['--case', case])
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1) or not result.stdout:
        raise ValueError('The native gate did not return a verdict: ' + result.stderr)
    report = json.loads(result.stdout)
    if error:
        if result.returncode != 1 or report.get('ready') or not any(error in e for e in report['errors']):
            raise ValueError('Expected a blocked verdict containing ' + repr(error) + ': ' + str(report))
    elif (result.returncode or not report['ready'] or report['case'] != basis.CONTEST
          or report['subject_round'] != len(report['history']) or not report['normal_entry']['href']):
        raise ValueError('The actual registered contest entry has no current accepted review: ' + str(report))
    return report


@contextmanager
def changed(path, contents):
    original = path.read_bytes()
    try:
        path.write_bytes(contents)
        yield
    finally:
        path.write_bytes(original)


def reject_route(root, message):
    result = subprocess.run([sys.executable, '-B', str(root / 'tools/lesson_route.py'), 'inspect',
                             '--root', str(root), '--route', basis.CONTEST + '/route.json'],
                            capture_output=True, text=True)
    if result.returncode != 1 or message not in result.stdout:
        raise ValueError('Expected route to reject ' + repr(message) + ': ' + str(result))


def verify(source):
    source = source.resolve()
    with tempfile.TemporaryDirectory(prefix='koai-r6-bindings-') as temp:
        clone = Path(temp) / 'checkout'
        head = git(source, 'rev-parse', 'HEAD').decode().strip()
        subprocess.run(['git', 'clone', '--quiet', '--shared', '--no-checkout', str(source), str(clone)], check=True)
        git(clone, 'checkout', '--quiet', '--detach', head)
        # A local clone transfers local branches. GitHub PR checkouts can instead
        # advertise the student plan's branch only under refs/remotes/origin.
        refs = git(source, 'for-each-ref', '--format=%(refname) %(objectname)', 'refs/remotes/origin').decode()
        for line in refs.splitlines():
            name, commit = line.split()
            if name != 'refs/remotes/origin/HEAD':
                git(clone, 'update-ref', name, commit)
        git(clone, 'remote', 'set-url', 'origin', git(source, 'remote', 'get-url', 'origin').decode().strip())
        contract = json.loads((clone / basis.CONTEST / 'contract.json').read_bytes())
        normal = check(clone)
        check(clone, 'inspect')
        if normal['contract_sha256'] != basis.sha((clone / basis.CONTEST / 'contract.json').read_bytes()):
            raise ValueError('The normal check selected a different criteria version')
        entry = clone / contract['lesson_path']
        # First prove the actual advertised reference above. Then model a clean
        # deployment with both refs advanced to this same already-verified HEAD.
        href = urlsplit(normal['normal_entry']['href'])
        _, marker, reference_and_path = href.path.partition('/blob/')
        suffix = '/' + contract['lesson_path']
        if not marker or not reference_and_path.endswith(suffix):
            raise ValueError('Expected the enrolled R6 plan to advertise its GitHub branch')
        branch = reference_and_path[:-len(suffix)]
        git(clone, 'check-ref-format', 'refs/heads/' + branch)
        git(clone, 'update-ref', 'refs/heads/' + branch, head)
        git(clone, 'update-ref', 'refs/remotes/origin/' + branch, head)
        check(clone)
        prior = git(clone, 'show', basis.R5_COMMIT + ':' + contract['lesson_path'])
        if basis.sha(prior) != contract['baseline']['sha256'] or entry.read_bytes() == prior:
            raise ValueError('The successor and predecessor must have distinct pinned material')
        with changed(entry, prior):
            for operation in ('check', 'inspect'):
                rolled_back = check(clone, operation, error='Selected material has no reviewed iteration')
                if rolled_back['subject_round'] is not None or not any('Normal student material column' in msg
                                                                     for msg in rolled_back['errors']):
                    raise ValueError('The current reference and foreign old notebook must both report their evidence')
        check(clone, case=basis.FOUNDATIONS, error='This study is archived')
        for path in contract['companion_paths']:
            companion = clone / path
            with changed(companion, companion.read_bytes() + b'\n'):
                check(clone, error='Active companion differs from reviewed snapshot')
                check(clone, 'inspect', error='Active companion differs from reviewed snapshot')
        plan = clone / normal['normal_entry']['plan']
        link = normal['normal_entry']['href'].encode()
        current = plan.read_bytes()
        if current.count(link) != 1:
            raise ValueError('Expected a unique normal student entry link in the current plan')
        altered = current.replace(link, b'wrong-week-material.ipynb', 1)
        with changed(plan, altered):
            check(clone, error='Source bytes differ')
        # Change the curriculum plan digest too, isolating the actual anchor check
        # from the independent source digest that also fails on a retargeted link.
        policy_path = clone / 'curriculum/contract.json'
        policy = json.loads(policy_path.read_bytes())
        policy['baseline']['sha256'] = basis.sha(altered)
        with changed(plan, altered), changed(policy_path, json.dumps(policy).encode()):
            reject_route(clone, 'Normal student material column')
        route_path = clone / basis.CONTEST / 'route.json'
        route = json.loads(route_path.read_bytes())
        route['workload_review']['sha256'] = '0' * 64
        with changed(route_path, json.dumps(route).encode()):
            reject_route(clone, 'stale workload review')
        route = json.loads(route_path.read_bytes())
        extension = next(u['optional_repeat'] for u in route['units'] if 'optional_repeat' in u)
        extension['cells'] = ['not-in-this-unit']
        with changed(route_path, json.dumps(route).encode()):
            reject_route(clone, 'Invalid optional repeat of existing work')
        route = json.loads(route_path.read_bytes())
        archive = clone / basis.CONTEST / 'rounds' / f'{normal["subject_round"]:04d}' / 'round.json'
        rows = json.loads(archive.read_bytes())['topics'].values()
        reference = next(c for row in rows for c in row.get('unassessed_reference', []))
        unit = next(u for u in route['units'] if reference in u['cells'])
        unit.update(status='conditional', homework_minutes=1, homework_range=[1, 1])
        with changed(route_path, json.dumps(route).encode()):
            reject_route(clone, 'Uncharged reference must stay outside the timed student route')
        final = check(clone)
        if normal['manifest'] != final['manifest']:
            raise ValueError('Restoring the exact changes failed to restore the reviewed binding')
        return {'case': normal['case'], 'round': normal['subject_round'], 'entry': normal['lesson_path'],
                'subject_sha256': normal['subject_sha256'], 'contract_sha256': normal['contract_sha256'],
                'controls': ['clean detached checkout', 'old subject', 'retired study', *contract['companion_paths'],
                             'retargeted curriculum link', 'changed workload receipt', 'foreign repeat cells',
                             'charged reference appendix', 'restored originals'], 'status': 'verified'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.root), ensure_ascii=False, indent=2))
