"""Verify a pre-edit depth contract and replay independent topic judgments from actual bytes."""
import argparse
import json
import re
from pathlib import Path

import quality
from topic_depth_basis import (ACTIVE, ERRORS, TIERS, VERDICTS, array, basis_chain, commits,
                               excerpt, git_file, immutable, local, minutes, names, registered, require,
                               sha, text, version)


def cell_map(notebook):
    require(notebook.get('nbformat') == 4, 'Expected a version 4 candidate notebook')
    cells = {}
    for cell in array(notebook['cells'], 'candidate cells', True):
        cid = text(cell.get('id'), 'cell id')
        require(re.fullmatch(r'[A-Za-z0-9_-]{1,64}', cid) and cid not in cells, 'Invalid or duplicate cell ' + cid)
        require(cell.get('cell_type') in ('markdown', 'code', 'raw'), 'Unknown cell type')
        src = cell.get('source')
        require(isinstance(src, str) or isinstance(src, list) and all(isinstance(s, str) for s in src),
                'Invalid cell source: ' + cid)
        cells[cid] = cell
    return cells


def mapped_topics(freeze, record, nb, dependencies):
    topics = freeze['topics']
    maps = record['topics']
    require(isinstance(maps, dict) and set(maps) == set(topics), 'Map every frozen topic exactly once')
    cells = cell_map(nb)
    ranks = {cid: i for i, cid in enumerate(cells)}
    owner, tiers = {}, {}
    for tid, row in maps.items():
        ledger = minutes(row['minutes'])
        for tier in TIERS:
            sequence = names(row[tier], tid + '.' + tier)
            require(bool(sequence) == bool(ledger[tier]), 'Cells and minutes disagree: ' + tid + '.' + tier)
            for cid in sequence:
                require(cid in cells and cid not in owner, 'Unidentified or multiply assigned cell: ' + cid)
                owner[cid], tiers[cid] = tid, tier
            require(sequence == sorted(sequence, key=ranks.get), 'Cell map differs from notebook order: ' + tid)
        for role in ('support', 'assessment'):
            role_cells = names(row[role], tid + '.' + role, True)
            require(all(owner.get(cid) == tid for cid in role_cells), 'Foreign ' + role + ' cell for ' + tid)
            if topics[tid]['minutes']['class'] or topics[tid]['minutes']['homework']:
                require(any(tiers[cid] != 'optional' for cid in role_cells),
                        'Required foundation or assessment is available only as optional: ' + tid)
        planned = topics[tid]['minutes']
        require(not planned['class'] or ledger['class'], 'A planned in-class topic has no class support: ' + tid)
        require(planned['class'] or planned['homework'] or not (ledger['class'] or ledger['homework']),
                'Optional material entered compulsory work: ' + tid)
        for task in row['assessment']:
            require(any(ranks[support] <= ranks[task] and TIERS.index(tiers[support]) <= TIERS.index(tiers[task])
                        for support in row['support']), 'Foundation must precede assessment: ' + tid)
        require(set(row['prerequisite_uses']) == set(topics[tid]['prerequisites']),
                'Map every prerequisite first use for ' + tid)
    require(set(owner) == set(cells), 'Unmapped student cells: ' + ', '.join(sorted(set(cells) - set(owner))))
    for tier in TIERS:
        actual = sum(row['minutes'][tier] for row in maps.values())
        expected = sum(row['minutes'][tier] for row in topics.values())
        require(actual == expected if tier == 'class' else actual <= expected, 'Outside frozen ' + tier + ' budget')
    bindings = {}
    # Relative order between a topic and its prerequisites matters. Unrelated cell insertions do not.
    for tid in freeze['order']:
        row = maps[tid]
        for dep, use in row['prerequisite_uses'].items():
            require(owner.get(use) == tid, 'Foreign prerequisite-use cell: ' + tid)
            eligible = [cid for cid in maps[dep]['support'] if ranks[cid] < ranks[use] and
                        (tiers[use] == 'optional' or tiers[cid] != 'optional') and
                        (tiers[use] != 'class' or tiers[cid] == 'class')]
            require(eligible, 'Missing prerequisite support before first use: ' + dep + ' -> ' + tid)
        # Exact cell content (including outputs, code and accessibility metadata) binds in-place edits.
        relevant = [[cid, cells[cid]] for cid in cells if owner[cid] == tid]
        bindings[tid] = quality.digest({'contract_topic': topics[tid], 'mapping': row, 'cells': relevant,
                                        'notebook_metadata': {k: v for k, v in nb.items() if k != 'cells'},
                                        'companions': dependencies,
                                        'prerequisites': {k: bindings[k] for k in topics[tid]['prerequisites']}})
    return bindings, owner, list(cells)


def affected_topics(freeze, previous, bindings, owner, ordered):
    if not previous:
        return set(bindings)
    affected = {tid for tid in bindings if previous['bindings'][tid] != bindings[tid]}
    # Only reverse ordering of surviving cells reopens both sides. A new cell does
    # not invalidate everything below it just because absolute indices shifted.
    old = {cid: i for i, cid in enumerate(previous['cell_order'])}
    common = [cid for cid in ordered if cid in old]
    for i, first in enumerate(common):
        for second in common[i + 1:]:
            if old[first] > old[second]:
                affected.update((owner[first], owner[second], previous['owners'][first], previous['owners'][second]))
    for tid in freeze['order']:
        if affected.intersection(freeze['topics'][tid]['prerequisites']):
            affected.add(tid)
    return affected


def companions(root, case, number, freeze, record):
    expected = freeze['contract']['companion_paths']
    rows = array(record['companions'], 'companion snapshots')
    require(len(rows) == len(expected) and {r['path'] for r in rows} == set(expected),
            'Snapshot every registered companion file')
    result = {}
    for row in rows:
        name = row['snapshot']
        archived = re.fullmatch(re.escape(case) + r'/rounds/([0-9]{4})/(.+)', name)
        require(archived and 1 <= int(archived[1]) <= number, 'Foreign companion snapshot: ' + name)
        require(quality.file_digest(local(root, name)) == row['sha256'], 'Stale companion snapshot: ' + name)
        result[row['path']] = row['sha256']
    return result


def counterevidence(root, directory, reviewer, observation, previous, current, tid):
    receipt = observation.get('counterevidence')
    if not receipt:
        return False
    path = local(root, receipt['path'])
    require(path.parent == directory / 'counterevidence' and path.suffix == '.json',
            'Counterevidence must use this iteration archive')
    data = quality.load(path)
    require(quality.file_digest(path) == receipt['sha256'] and data['topic'] == tid and
            data['contract_sha256'] == current['contract_sha256'] and
            data['candidate_sha256'] == current['candidate_sha256'] and
            data['prior_reviews'] == previous['reviews'] and data['cells'] == observation['cells'] and
            data['reviewer'].strip().casefold() == reviewer and
            data['round_sha256'] == quality.file_digest(directory / 'round.json'),
            'Foreign counterevidence for ' + tid)
    text(data.get('finding'), 'counterevidence finding')
    return True


def cell_evidence(cell):
    source = cell['source'] if isinstance(cell['source'], str) else ''.join(cell['source'])
    lines = [line.rstrip() for line in source.splitlines() if line.strip()]
    return quality.digest([cell['cell_type'], lines])


def companion_evidence(root, record, item):
    snapshots = {row['path']: row['snapshot'] for row in record['companions']}
    spans = []
    for span in array(item.get('companion_spans', []), 'reviewed companion excerpts'):
        require(span['path'] in snapshots, 'Foreign companion evidence')
        raw = local(root, snapshots[span['path']]).read_bytes()
        fragment = excerpt(raw, span['lines']).strip()
        require(raw.count(fragment) == 1, 'Include enough context to identify one companion excerpt')
        spans.append({'path': span['path'], 'fragment': fragment.decode('utf-8'), 'lines': span['lines']})
    return spans


def finding_changed(debt, fingerprints, tiers, ordered, companions):
    cited = debt['cell_fingerprints']
    if any(fingerprints.get(cid) != value or tiers.get(cid) != debt['tiers'][cid] for cid, value in cited.items()):
        return True
    if [cid for cid in ordered if cid in cited] != debt['order']:
        return True
    # Moving an intact excerpt or editing an unrelated footnote does not answer the adverse finding.
    return any(span['fragment'].encode() not in companions[span['path']] for span in debt['companion_spans'])


def review_round(root, directory, freeze, record, owner, bindings, previous, author, changed, cells):
    path = directory / 'reviews'
    required = changed | ({tid for tid in bindings if previous['decisions'][tid] != 'pass'} if previous else set())
    observations = {tid: [] for tid in bindings}
    hashes, reports = {}, {tid: [] for tid in bindings}
    debt = {tid: list(previous['outstanding'][tid]) if previous else [] for tid in bindings}
    fingerprints = {cid: cell_evidence(cell) for cid, cell in cells.items()}
    tiers = {cid: tier for row in record['topics'].values() for tier in TIERS for cid in row[tier]}
    snapshots = {row['path']: local(root, row['snapshot']).read_bytes() for row in record['companions']}
    reviewers = set()
    for review_path in sorted(path.iterdir()) if path.exists() else []:
        local(root, review_path.relative_to(root).as_posix())
        require(review_path.is_file() and review_path.suffix == '.json', 'Unrecognized pending review: ' + str(review_path))
        report = quality.load(review_path)
        version(report)
        require(report['stage'] == 'candidate' and report['round_sha256'] == quality.file_digest(directory / 'round.json')
                and report['candidate_sha256'] == record['candidate_sha256'] and
                report['contract_sha256'] == freeze['sha256'], 'Foreign or stale independent review: ' + review_path.name)
        reviewer = text(report['reviewer'], 'candidate reviewer').strip().casefold()
        require(reviewer not in {author, freeze['contract']['author'].strip().casefold()} and reviewer not in reviewers,
                'Candidate review must be independent and unique within the round')
        reviewers.add(reviewer)
        if 'external_receipt' in report:
            receipt = report['external_receipt']
            path = local(root, receipt['path'])
            require(path.parent == directory / 'external' and path.suffix == '.json' and
                    quality.file_digest(path) == receipt['sha256'], 'Foreign external reviewer receipt')
            original = quality.load(path)
            require(all(original[k] == report[k] for k in
                        ('stage', 'reviewer', 'round_sha256', 'candidate_sha256', 'contract_sha256', 'topics')),
                    'External receipt does not attest these topic judgments')
        hashes[review_path.name] = quality.file_digest(review_path)
        require(isinstance(report['topics'], dict) and report['topics'] and report['topics'].keys() <= bindings.keys(),
                'Review the actual candidate topics')
        for tid, item in report['topics'].items():
            verdict = item['verdict']
            require(verdict in VERDICTS, 'Unknown topic verdict')
            locators = names(item['cells'], 'reviewed cells', True)
            require(all(owner.get(cid) == tid for cid in locators), 'Foreign review cells for ' + tid)
            if verdict == 'pass':
                for role in ('support', 'assessment'):
                    require(set(locators) & set(record['topics'][tid][role]),
                            'Passing review lacks a ' + role + ' locator: ' + tid)
            for key in ('foundation', 'ceiling', 'workload', 'finding'):
                text(item.get(key), 'candidate review ' + tid + '.' + key)
            neutral = False
            if item.get('counterevidence'):
                require(previous is not None, 'Counterevidence needs a previous round')
                neutral = counterevidence(root, directory, reviewer, item, previous, record, tid)
            reports[tid].append({'reviewer': report['reviewer'], 'verdict': verdict, 'cells': locators,
                                 'finding': item['finding'], 'foundation': item['foundation'],
                                 'ceiling': item['ceiling'], 'workload': item['workload']})
            spans = companion_evidence(root, record, item)
            if verdict != 'pass':
                finding = {'reviewer': reviewer, 'finding': item['finding'], 'companion_spans': spans,
                           'cell_fingerprints': {cid: fingerprints[cid] for cid in locators},
                           'order': [cid for cid in cells if cid in locators], 'tiers': {cid: tiers[cid] for cid in locators}}
                if finding not in debt[tid]:
                    debt[tid].append(finding)
            observations[tid].append((reviewer, verdict, neutral))
    decisions, agents = {}, {}
    for tid, judgments in observations.items():
        votes = {item[1] for item in judgments}
        agents[tid] = [item[0] for item in judgments]
        if not votes:
            decisions[tid] = 'pending' if tid in required else 'pass'
        elif len(votes) > 1:
            decisions[tid] = 'conflict'
        else:
            decisions[tid] = next(iter(votes))
        if decisions[tid] == 'pass' and debt[tid]:
            outstanding = [f for f in debt[tid] if not finding_changed(f, fingerprints, tiers, cells, snapshots)]
            if outstanding:
                conflicted = set(previous['reviewers'][tid]) | {f['reviewer'] for f in outstanding}
                require(any(neutral and reviewer not in conflicted for reviewer, _, neutral in judgments),
                        'An unchanged adverse finding needs independent adjudication and current counterevidence: ' + tid)
            debt[tid] = []
        if not judgments and previous:
            agents[tid] = previous['reviewers'][tid]
    return {'required_topics': sorted(required), 'decisions': decisions, 'reviews': hashes,
            'adjudicated': sorted(tid for tid, group in observations.items() if any(entry[2] for entry in group)),
            'reviewers': agents, 'bindings': bindings, 'findings': reports, 'outstanding': debt,
            'status': 'reviewed' if all(s == 'pass' for s in decisions.values()) else 'open'}


def replay(root, case, bases, through=None, history=None):
    immutable(root, bases[0]['anchor'], [case + '/rounds'])
    folder = local(root, case + '/rounds')
    directories = sorted(folder.iterdir()) if folder.exists() else []
    history = [] if history is None else history
    for number, directory in enumerate(directories, 1):
        local(root, directory.relative_to(root).as_posix())
        require(directory.is_dir() and directory.name == f'{number:04d}', 'Nonconsecutive iteration directory')
        if through is not None and number > through:
            break
        rpath = local(root, directory.relative_to(root).as_posix() + '/round.json')
        record = quality.load(rpath)
        version(record)
        freeze = next(b for b in reversed(bases) if b['after_round'] < number)
        previous = history[-1] if history else None
        require(record['contract_sha256'] == freeze['sha256'], 'Foreign iteration contract')
        require(record['previous'] == (previous['round_sha256'] if previous else None) and
                record.get('prior_reviews', {}) == (previous['reviews'] if previous else {}),
                'Iteration must bind the previous record and every prior independent review')
        if previous:
            require(previous['reviews'] and 'pending' not in previous['decisions'].values(),
                    'A previous iteration is still awaiting independent review')
        candidate = local(root, directory.relative_to(root).as_posix() + '/candidate.ipynb')
        require(record['candidate_sha256'] == quality.file_digest(candidate), 'Candidate bytes differ from iteration')
        author = text(record['author'], 'candidate author').strip().casefold()
        files = companions(root, case, number, freeze, record)
        notebook = quality.load(candidate)
        bindings, owner, ordered = mapped_topics(freeze, record, notebook, files)
        changed = affected_topics(freeze, previous, bindings, owner, ordered)
        for basis in bases[1:]:
            if basis['after_round'] == number - 1:
                changed.update(basis['reopen'])
        for tid in freeze['order']:
            if changed.intersection(freeze['topics'][tid]['prerequisites']):
                changed.add(tid)
        verdict = review_round(root, directory, freeze, record, owner, bindings, previous, author, changed, cell_map(notebook))
        changes = array(record['changes'], 'iteration rationale', True)
        declared = set()
        for change in changes:
            tid = change['topic']
            require(tid in bindings and tid not in declared, 'Unknown or duplicate change rationale')
            for key in ('action', 'reason', 'alternative'):
                text(change.get(key), tid + '.' + key)
            declared.add(tid)
        require(set(verdict['required_topics']) <= declared, 'Missing change or no-change rationale for reopened topics')
        require(changed or verdict['adjudicated'] or 'pending' in verdict['decisions'].values(),
                'An identical candidate and basis need independent counterevidence for a new iteration')
        history.append({**verdict, 'number': number, 'round_sha256': quality.file_digest(rpath),
                        'candidate_sha256': record['candidate_sha256'], 'companions': files, 'author': author,
                        'cell_order': ordered, 'owners': owner})
    return history


def inspect(root, case, *, target=None, final=True, stage=False):
    root = Path(root).resolve()
    bases = basis_chain(root, case)
    freeze = bases[0]
    lesson = freeze['contract']['lesson_path']
    result = {'status': 'blocked', 'freeze_commit': freeze['anchor'], 'contract_sha256': bases[-1]['sha256'],
              'basis_history': [{k: b[k] for k in ('sha256', 'anchor', 'after_round', 'reopen', 'review_sha256')}
                                for b in bases], 'lesson_path': lesson, 'history': [], 'errors': [], 'ready': False,
              'scope': 'Independent material judgments and planned workload; learner outcomes unmeasured.'}
    history = []
    try:
        replay(root, case, bases, history=history)
    except ERRORS as error:
        result['errors'].append(str(error))
    result['history'] = [{k: v for k, v in row.items() if k not in ('cell_order', 'owners', 'outstanding')} for row in history]
    selected = local(root, target or lesson)
    selected_sha = quality.file_digest(selected) if selected.is_file() else None
    ordinal = re.fullmatch(re.escape(case) + r'/rounds/([0-9]{4})/candidate\.ipynb', target or lesson)
    subject = next((r for r in reversed(history) if r['candidate_sha256'] == selected_sha and
                    (not ordinal or r['number'] == int(ordinal[1]))), None)
    result['subject_round'] = subject['number'] if subject else None
    result['subject_sha256'] = selected_sha
    recorded = history[:subject['number']] if subject else []
    evidence = {'case': case, 'target': target or lesson, 'subject_sha256': selected_sha,
                'basis': result['basis_history'], 'rounds': [[r['round_sha256'], r['reviews']] for r in recorded],
                'implementation': [quality.file_digest(Path(__file__)),
                                   quality.file_digest(Path(__file__).with_name('topic_depth_basis.py'))]}
    result['manifest'] = {'id': 'review:topic-depth', 'revision': 'topic-depth-v1', 'sha256': quality.digest(evidence)}
    if not history:
        result['errors'].append('No reviewed candidate')
        return result
    last = history[-1]
    pending = {tid for basis in bases[1:] if basis['after_round'] == len(history) for tid in basis['reopen']}
    result['reopened_by_basis'] = sorted(pending)
    if pending:
        result['errors'].append('New depth basis requires independent material review: ' + ', '.join(sorted(pending)))
    if last['status'] != 'reviewed':
        result['errors'].append('Unresolved topic judgments')
    if final:
        if ordinal and int(ordinal[1]) != last['number']:
            result['errors'].append('Historical iteration is not the current release candidate')
        if selected_sha != last['candidate_sha256']:
            result['errors'].append('Selected notebook differs from the last reviewed iteration')
        require(not stage or ordinal, 'Staged verification requires a registered archived candidate')
        for name, digest in ([] if stage else last['companions'].items()):
            path = local(root, name)
            if not path.is_file() or quality.file_digest(path) != digest:
                result['errors'].append('Active companion differs from reviewed snapshot: ' + name)
        archived = {item['candidate_sha256'] for item in history}
        for revision in commits(root, freeze['anchor'], 'HEAD', lesson):
            raw = git_file(root, revision, lesson)
            if raw is None or sha(raw) not in archived:
                result['errors'].append('Unarchived student revision in Git: ' + revision)
    result['ready'] = not result['errors']
    result['status'] = 'reviewed' if result['ready'] else 'blocked'
    return result


def checked(root, case, **options):
    try:
        return inspect(root, case, **options)
    except ERRORS as error:
        return {'status': 'blocked', 'ready': False, 'errors': [str(error)]}


def work_items(report):
    depth = report.get('topic_depth')
    if not depth or depth['ready']:
        return []
    history = depth.get('history', [])
    ordinal = depth.get('subject_round')
    latest = history[ordinal - 1] if ordinal else {}
    states = dict(latest.get('decisions', {}))
    for tid in depth.get('reopened_by_basis', []):
        states[tid] = 'pending'
    if latest.get('candidate_sha256') != report['artifact_sha256']:
        states = {}
    kinds = {'revise': 'revise_topic_depth', 'uncertain': 'resolve_topic_depth',
             'conflict': 'adjudicate_topic_depth', 'pending': 'review_topic_depth'}
    items = []
    for tid, status in states.items():
        if status == 'pass':
            continue
        findings = latest.get('findings', {}).get(tid, [])
        items.append({'id': 'depth:' + tid, 'topic': tid, 'judgment': status, 'findings': findings,
                      'work_kind': kinds[status], 'priority': 'P1' if status == 'revise' else 'P2'})
    if not items:
        items.append({'id': 'depth:evidence', 'work_kind': 'restore_topic_depth_evidence',
                      'findings': depth['errors'], 'priority': 'P3'})
    context = {'artifact': report['artifact_sha256'], 'contract': depth.get('contract_sha256'),
               'basis': depth.get('basis_history'), 'round': latest.get('round_sha256'),
               'reviews': latest.get('reviews'), 'errors': depth['errors'],
               'gate': [quality.file_digest(Path(__file__)), quality.file_digest(Path(__file__).with_name('topic_depth_basis.py'))]}
    for item in items:
        if 'topic' in item:
            context['errors'] = []
        item['key'] = quality.digest({'depth_work': item, 'context': context})
        item['affected_ids'] = [item['topic']] if 'topic' in item else []
    return items


def before_revision(root, baseline, output, digest):
    case = registered(baseline) or registered(output)
    if not case:
        return None
    require(registered(baseline) == case, 'A registered candidate needs its actual preceding baseline')
    match = re.fullmatch(re.escape(case) + r'/rounds/([0-9]{4})/candidate\.ipynb', output)
    require(match and int(match[1]) > 0, 'Place the candidate in the registered iteration archive')
    number = int(match[1])
    archived = re.fullmatch(re.escape(case) + r'/rounds/([0-9]{4})/candidate\.ipynb', baseline)
    require(not archived or int(archived[1]) == number - 1, 'Use the immediately preceding archived candidate')
    bases = basis_chain(root, case)
    freeze = bases[0]
    history = replay(root, case, bases, through=number - 1)
    require(len(history) == number - 1, 'Missing earlier iteration')
    previous = history[-1] if history else None
    require(not previous or (previous['reviews'] and 'pending' not in previous['decisions'].values()),
            'Review the previous iteration before editing')
    require(digest == (previous['candidate_sha256'] if previous else freeze['contract']['baseline']['sha256']),
            'Editing requires the actual preceding, frozen baseline')
    return case


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'inspect', 'check'))
    parser.add_argument('--root', type=Path, default=quality.ROOT)
    parser.add_argument('--case', default=None, help='Registered cases are required by default')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    cases = [args.case] if args.case else list(ACTIVE.values())
    results = {}
    for case in cases:
        if args.command == 'freeze':
            try:
                bases = basis_chain(root, case)
                f = bases[-1]
                results[case] = {'status': 'frozen', 'freeze_commit': bases[0]['anchor'], 'basis_commit': f['anchor'], 'contract_sha256': f['sha256'],
                                 'lesson_path': f['contract']['lesson_path'], 'topics': f['order']}
            except ERRORS as error:
                results[case] = {'status': 'blocked', 'errors': [str(error)]}
        else:
            results[case] = checked(root, case, final=args.command == 'check')
    output = results[cases[0]] if len(cases) == 1 else results
    print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if all(r['status'] in ('frozen', 'reviewed') for r in results.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
