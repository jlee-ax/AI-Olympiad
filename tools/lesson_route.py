#!/usr/bin/env python3
"""Check a student route and replay a matched, predeclared material comparison."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import posixpath
import re
from urllib.parse import unquote, urlsplit

import quality
import topic_depth
from topic_depth_basis import (ERRORS, Navigation, advertised_ref, array, committed_inputs, commits, git, git_file, immutable,
                               local, names, normal_entry, require, sha, stored_bytes, stored_json, text)

SIDES = ('candidate', 'incumbent')
STATES = ('required', 'conditional', 'deferred')
VERDICTS = ('pass', 'revise', 'uncertain')
BITS = ('G', 'I', 'W', 'T')
CHECKS = {'preservation', 'prerequisites', 'execution', 'workload', 'serious_faults_absent'}


def schema(record):
    require(type(record.get('schema_version')) is int and record['schema_version'] == 1,
            'Expected lesson route schema_version 1')


def pinned_files(root, mapping, label, historical=None):
    require(isinstance(mapping, dict) and mapping, 'Missing ' + label)
    for name, expected in mapping.items():
        actual = sha(stored_bytes(root, name, historical))
        require(actual == expected, 'Missing or stale ' + label + ': ' + name)


def ancestor(root, commit):
    require(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}', commit) and
            git(root, 'merge-base', '--is-ancestor', commit, 'HEAD', check=False).returncode == 0,
            'Expected a full ancestor commit')
    return commit


def markdown_navigation(cell):
    # nbconvert already uses Mistune. Its Markdown renderer excludes code, images and
    # comments from hyperlinks, including when the text looks like a literal link.
    try:
        import mistune
    except ImportError as error:
        raise ValueError('Install Mistune 3 in the lesson environment to check Markdown links') from error
    nav = Navigation()
    if cell['cell_type'] == 'markdown':
        source = ''.join(cell['source'])
        nav.feed(mistune.create_markdown(escape=False)(source))
        nav.close()
    return nav


def study_units(root, manifest, historical):
    files = manifest['files']
    pinned_files(root, files, 'route file', historical)
    units, books, owners = {}, {}, {}
    for unit in array(manifest['units'], 'route units', True):
        uid = text(unit['id'], 'unit id')
        require(uid not in units and unit['status'] in STATES, 'Unknown status or duplicate unit: ' + uid)
        text(unit['reason'], 'reason or conditional trigger for ' + uid)
        path = unit['path']
        require(path in files and path.endswith('.ipynb'), 'Unbound student notebook: ' + uid)
        if path not in books:
            books[path] = topic_depth.cell_map(stored_json(root, path, historical))
        cells = names(unit['cells'], uid + ' cells', True)
        selected = set(cells)
        require(cells == [cid for cid in books[path] if cid in selected], 'Missing or out-of-order cells: ' + uid)
        for cid in cells:
            require((path, cid) not in owners, 'Multiply allocated student cell: ' + path + '#' + cid)
            owners[path, cid] = uid
        units[uid] = unit

    companions = manifest['companions']
    require(isinstance(companions, dict) and set(companions) == set(books), 'Declare companions for every route notebook')
    for path, roles in companions.items():
        require(isinstance(roles, dict) and {'teacher', 'data'} <= roles.keys() <= {'teacher', 'data', 'after_attempt'},
                'Unknown or missing companion role for ' + path)
        used = set()
        for role, entries in roles.items():
            bound = set(names(entries, path + ' ' + role, role == 'teacher'))
            require(bound <= files.keys() and bound.isdisjoint(books) and bound.isdisjoint(used),
                    'Unbound or ambiguous companion: ' + path + ' ' + role)
            used.update(bound)
    teacher = {p for roles in companions.values() for p in roles['teacher']}
    visible = {p for roles in companions.values() for role in ('data', 'after_attempt') for p in roles.get(role, [])}
    require(teacher.isdisjoint(visible), 'Teacher-only material also appears in the student packet')
    return units, books, owners


def route_links(manifest, units, books, owners):
    entry = manifest['entry']
    require(entry in books, 'Unmapped student entry')
    first = owners.get((entry, next(iter(books[entry]))))
    require(first in units and units[first]['status'] == 'required', 'Normal entry must start in required material')
    ranks = {p: {cid: n for n, cid in enumerate(cells)} for p, cells in books.items()}
    starts = {uid: ranks[u['path']][u['cells'][0]] for uid, u in units.items()}
    edges = defaultdict(set)
    for uid, unit in units.items():
        # A later unit in an opened notebook can be followed in reading order.
        edges[uid].update(other for other, target in units.items() if target['path'] == unit['path']
                          and starts[other] > starts[uid])
    rendered = {}

    def nav(path, cid):
        key = (path, cid)
        if key not in rendered:
            rendered[key] = markdown_navigation(books[path][cid])
        return rendered[key]

    for link in array(manifest['links'], 'navigation links'):
        source, target = units[link['from']], units[link['to']]
        path, cid = source['path'], link['cell']
        href = unquote(text(link['href'], 'student link'))
        require(cid in source['cells'] and href in nav(path, cid).columns[0], 'Missing visible student link in ' + cid)
        dest = urlsplit(href)
        require(not dest.scheme and not dest.netloc and not dest.query and not dest.path.startswith('/'),
                'Student link must open a local notebook')
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), dest.path)) if dest.path else path
        require(resolved == target['path'], 'Student link opens a different notebook: ' + href)
        landing = target['cells'][0]
        if not dest.fragment:
            correct = landing == next(iter(books[resolved]))
        elif dest.fragment.startswith('cell-id='):
            correct = dest.fragment == 'cell-id=' + landing
        else:
            matches = [cell for cell in books[resolved] if dest.fragment in nav(resolved, cell).anchors]
            correct = matches == [landing]
        require(correct, 'Student link misses the declared section: ' + href)
        edges[link['from']].add(link['to'])

    for path, roles in manifest['companions'].items():
        for feedback in roles.get('after_attempt', []):
            hrefs = (urlsplit(href) for cid in books[path] if (path, cid) in owners
                     and units[owners[path, cid]]['status'] != 'deferred' for href in nav(path, cid).columns[0])
            require(any(not u.scheme and not u.netloc and not u.query and not u.fragment and
                        posixpath.normpath(posixpath.join(posixpath.dirname(path), u.path)) == feedback for u in hrefs),
                    'Missing student link to delayed feedback: ' + feedback)

    for allowed in ({'required'}, {'required', 'conditional'}):
        reached, pending = set(), [first]
        while pending:
            uid = pending.pop()
            if uid not in reached and units[uid]['status'] in allowed:
                reached.add(uid)
                pending.extend(edges[uid] - reached)
        missing = {uid for uid, unit in units.items() if unit['status'] in allowed} - reached
        require(not missing, 'Unreachable ' + '/'.join(sorted(allowed)) + ' units: ' + ', '.join(sorted(missing)))


def candidate_depth(root, manifest, units, owners):
    entry, depth = manifest['entry'], manifest['depth']
    case, ordinal = depth['case'], depth['round']
    require(type(ordinal) is int and ordinal > 0, 'Invalid reviewed ordinal')
    require(topic_depth.registered(entry) in (None, case), 'Wrong registered depth case')
    result = topic_depth.checked(root, case, target=entry)
    require(result['ready'], 'Topic depth blocked: ' + ', '.join(result['errors']))
    require(result['lesson_path'] == entry and result['subject_round'] == ordinal,
            'Route differs from the reviewed entry or ordinal')
    round_path = f'{case}/rounds/{ordinal:04d}/round.json'
    record = quality.load(local(root, round_path))
    required, optional = set(), set()
    for row in record['topics'].values():
        for cid in row.get('unassessed_reference', []):
            require(units[owners[entry, cid]]['status'] == 'deferred',
                    'Uncharged reference must stay outside the timed student route: ' + cid)
        required.update(row['class'] + row['homework'])
        optional.update(row['optional'])
    require({cid for (path, cid) in owners if path == entry} == required | optional, 'Unmapped entry cells')
    require({cid for (path, cid), uid in owners.items() if path == entry and units[uid]['status'] == 'required'} == required,
            'Required entry work differs from the reviewed round')
    for tier in ('class', 'homework'):
        allocated = sum(u[tier + '_minutes'] for u in units.values() if u['path'] == entry and u['status'] == 'required')
        reviewed = sum(row['minutes'][tier] for row in record['topics'].values())
        require(allocated == reviewed, 'Entry ' + tier + ' allocation differs from the reviewed round')
        topic_units = [({owners[entry, cid] for cid in row[tier]}, row['minutes'][tier])
                       for row in record['topics'].values()]
        for uid, u in units.items():
            if u['path'] == entry and u['status'] == 'required':
                minimum = sum(n for ids, n in topic_units if ids == {uid})
                maximum = sum(n for ids, n in topic_units if uid in ids)
                require(minimum <= u[tier + '_minutes'] <= maximum,
                        'Entry time cannot belong to the reviewed ' + tier + ' cells: ' + uid)
    declared = {p for paths in manifest['companions'][entry].values() for p in paths}
    for companion in record['companions']:
        require(companion['path'] in declared and manifest['files'][companion['path']] == companion['sha256'],
                'Unbound reviewed entry companion: ' + companion['path'])
    return result['manifest']['sha256'], round_path


def inspect_route(root, name, *, incumbent=False):
    path = local(root, name)
    manifest = quality.load(path)
    schema(manifest)
    rid = text(manifest['id'], 'route identity')
    historical = ancestor(root, manifest['basis_commit']) if incumbent else None
    week = manifest.get('week', 1)
    require(type(week) is int and week > 0, 'Invalid route week')
    (class_limit, minimum, maximum), navigation = normal_entry(root, manifest['entry'], week, historical)
    units, books, owners = study_units(root, manifest, historical)
    route_links(manifest, units, books, owners)
    report = {'id': rid, 'week': week, 'route_sha256': quality.file_digest(path), 'entry': manifest['entry'],
              'normal_entry': navigation,
              'units': {uid: u['status'] for uid, u in units.items()}}
    if incumbent:
        report['timing'] = text(manifest['timing'], 'historical timing limitation')
        report['basis_commit'] = historical
    else:
        totals = {tier: {status: 0 for status in STATES} for tier in ('class', 'homework')}
        bounds = {tier: {status: [0, 0] for status in STATES} for tier in totals}
        complete_ranges = True
        for uid, unit in units.items():
            for tier in totals:
                value = unit[tier + '_minutes']
                require(type(value) is int and value >= 0, 'Invalid ' + tier + ' minutes: ' + uid)
                totals[tier][unit['status']] += value
                interval = unit.get(tier + '_range')
                if interval is None:
                    complete_ranges = False
                    interval = [value, value]
                require(isinstance(interval, list) and len(interval) == 2 and all(type(v) is int for v in interval)
                        and 0 <= interval[0] <= value <= interval[1]
                        and (unit['status'] != 'deferred' or interval[1] == 0), 'Invalid time range: ' + uid)
                for i in (0, 1):
                    bounds[tier][unit['status']][i] += interval[i]
            if 'optional_repeat' in unit:
                repeat = unit['optional_repeat']
                cells = names(repeat['cells'], 'optional repeat cells: ' + uid, True)
                extra = repeat['homework_minutes']
                text(repeat['reason'], 'optional repeat trigger: ' + uid)
                require(unit['status'] == 'required' and set(cells) <= set(unit['cells']) and
                        type(extra) is int and extra > 0, 'Invalid optional repeat of existing work: ' + uid)
                totals['homework']['conditional'] += extra
                for limit in (0, 1):
                    bounds['homework']['conditional'][limit] += extra
            charged = unit['class_minutes'] + unit['homework_minutes']
            require((charged == 0) == (unit['status'] == 'deferred'), 'Status and charged minutes disagree: ' + uid)
        report['depth_sha256'], report['round_path'] = candidate_depth(root, manifest, units, owners)
        if 'workload_review' in manifest:
            receipt = manifest['workload_review']
            review_path = Path(text(receipt['path'], 'independent workload review'))
            require(review_path.parent == Path(report['round_path']).parent / 'reviews' and review_path.suffix == '.json',
                    'Workload estimate must cite this iteration’s independent material review')
            pinned_files(root, {receipt['path']: receipt['sha256']}, 'workload review')
            report['workload_review'] = receipt
        required_class, required_home = totals['class']['required'], totals['homework']['required']
        require(required_class >= class_limit, 'Weekly required class allocation is incomplete')
        if required_home < minimum:
            text(manifest.get('shorter_homework_reason'), 'rationale for a shorter homework plan')
        within = (sum(v[1] for v in bounds['class'].values()) <= class_limit and
                  sum(v[1] for v in bounds['homework'].values()) <= maximum)
        if not within:
            text(manifest.get('overrun'), 'explanation for weekly workload overrun')
        report.update(minutes=totals, ranges=bounds, complete_ranges=complete_ranges,
                      planned_limits={'class': class_limit, 'homework': [minimum, maximum]},
                      budget='within' if within else 'overrun', overrun=manifest.get('overrun'),
                      shorter_homework_reason=manifest.get('shorter_homework_reason'))
    return report, units, manifest


def frozen_protocol(root, name, commit, round_path, candidate):
    protocol = quality.load(local(root, name))
    schema(protocol)
    text(protocol['id'], 'protocol id')
    text(protocol['maker'], 'protocol maker')
    cases = set(names(protocol['case_ids'], 'frozen cases', True))
    mandatory = set(names(protocol.get('required_cases', protocol['case_ids']), 'mandatory cases'))
    groups = protocol.get('groups', {})
    require(isinstance(groups, dict) and groups.keys() <= {'safety', 'burden', 'regression', 'replication'},
            'Unknown protocol case group')
    for group, members in groups.items():
        mandatory.update(names(members, group + ' cases'))
    conditional = set(names(protocol.get('conditional_cases', []), 'conditional cases'))
    require(mandatory and mandatory | conditional <= cases, 'Unknown or missing mandatory protocol cases')
    require(git_file(root, commit, name) == local(root, name).read_bytes(), 'Protocol differs from public freeze')
    require(git_file(root, commit, round_path) is None, 'Finalist round already existed at protocol freeze')
    if 'candidate_before_revision' in protocol:
        baseline = protocol['candidate_before_revision']
        start = ancestor(root, baseline['commit'])
        require(git(root, 'merge-base', '--is-ancestor', start, commit, check=False).returncode == 0,
                'Protocol predates its proposed material baseline')
        original = git_file(root, start, candidate['entry'])
        require((None if original is None else sha(original)) == baseline['sha256'], 'Wrong pre-revision notebook')
        material = set(candidate['companions'])
        for roles in candidate['companions'].values():
            material.update(path for paths in roles.values() for path in paths)
        require(not commits(root, start, commit, *sorted(material)), 'Student material changed before protocol freeze')
    inputs = protocol['inputs']
    pinned_files(root, inputs, 'frozen evaluation input')
    for path, digest in inputs.items():
        old = git_file(root, commit, path)
        require(old is None or sha(old) == digest, 'Different evaluation input at freeze: ' + path)
    # Inputs may be revealed for the first time after the blind reads.
    immutable(root, commit, [name, *inputs])
    rule = protocol.get('replacement_rule')
    require(rule in (None, 'matched-giwt-v1'), 'Unknown frozen replacement rule')
    if rule:
        require(len(protocol.get('required_cases', protocol['case_ids'])) == 4, 'GIWT requires four matched tasks')
    return protocol, cases, mandatory, conditional, rule, set(protocol.get('required_cases', protocol['case_ids']))


def match_ref(root, reference, expected):
    require(reference['path'] == expected and quality.file_digest(local(root, expected)) == reference['sha256'],
            'Wrong path or stale evidence: ' + expected)


def disclosed_allocation(root, results_path, result, digest):
    if not digest:
        return {}, {}, []
    default = (results_path.parent / 'comparison/assignment.json').relative_to(root).as_posix()
    ref = result.get('assignment', {'path': default, 'sha256': digest})
    require(ref['sha256'] == digest, 'Assignment does not match the frozen commitment')
    pinned_files(root, {ref['path']: digest}, 'blind assignment')
    assignment = quality.load(local(root, ref['path']))
    text(assignment['salt'], 'assignment salt')
    labels = {role: label for label, role in assignment.items() if isinstance(role, str) and role in SIDES}
    require(set(labels) == set(SIDES) and set(assignment) == set(labels.values()) | {'salt', 'order'},
            'Blind assignment must identify both routes')
    orders = assignment['order']
    require(isinstance(orders, dict) and len(orders) >= 2, 'Incomplete assigned reader list')
    for reader, order in orders.items():
        text(reader, 'assigned reader')
        require(isinstance(order, list) and len(order) == 2 and set(order) == set(labels.values()),
                'Invalid assigned presentation order')
    require(len({tuple(v) for v in orders.values()}) == 2, 'Readers must have counterbalanced assigned orders')
    return labels, orders, [ref['path']]


def shared_evidence(root, result, freeze):
    ref = result.get('evidence')
    if ref is None:
        return None
    path, digest = ref['path'], ref['sha256']
    pinned_files(root, {path: digest}, 'shared evidence map')
    index = quality.load(local(root, path))
    schema(index)
    files = index['files']
    require(path not in files, 'Evidence map cannot bind itself')
    pinned_files(root, files, 'shared comparison evidence')
    anchor = committed_inputs(root, freeze, {path: digest}, 'Shared evidence map was not committed before rating')
    for name, expected in files.items():
        original = git_file(root, anchor, name)
        require(original is None or sha(original) == expected, 'Different shared evidence at its freeze: ' + name)
    immutable(root, anchor, [path, *files])
    return anchor


def reviewer_cases(root, path, context, rule, assigned, orders):
    wrapper = quality.load(local(root, path))
    schema(wrapper)
    reviewer = text(wrapper['reviewer'], 'reviewer name').strip()
    require(not rule or 'original' in wrapper, 'The matched GIWT rule requires a blind original')
    if 'original' in wrapper:
        ref = wrapper['original']
        require(ref['path'] != path, 'Original cannot be its own wrapper')
        pinned_files(root, {ref['path']: ref['sha256']}, 'original blind assessment')
        original = quality.load(local(root, ref['path']))
        source = original.get('route_evidence', original)
        labels = wrapper['labels']
        require(set(labels) == set(SIDES) and all(isinstance(v, str) and v.strip() for v in labels.values())
                and len(set(labels.values())) == 2, 'Expected two distinct blind route labels')
        require(source['reviewer'] == reviewer and source['subjects'] == {labels[s]: context[s] for s in SIDES},
                'Original reviewer or blind subject hashes differ')
    else:
        source = wrapper
        labels = {s: s for s in SIDES}
        require(all(source[s + '_sha256'] == context[s] for s in SIDES), 'Assessment refers to older route bytes')
    require(source.get('evidence_sha256') == context.get('evidence'), 'Unbound or stale shared reader evidence')
    if assigned:
        require(labels == assigned and reviewer in orders, 'Blind debrief differs from the frozen label or reader assignment')
        require('order' not in source or source['order'] == orders[reviewer], 'Reader declared a different presentation order')
    require(source['protocol_sha256'] == context['protocol'] and source['depth_sha256'] == context['depth'],
            'Assessment refers to older evaluation or depth criteria')
    checks = {}
    if rule:
        native = source['checks']
        require(isinstance(native, dict) and set(native) == set(labels.values()), 'Missing matched route checks')
        for side, label in labels.items():
            values = native[label]
            require(isinstance(values, dict) and set(values) == CHECKS and
                    all(type(v) is bool or v == '?' for v in values.values()), 'Invalid route safety or burden check')
            checks[side] = values
    originals = [wrapper['original']['path']] if 'original' in wrapper else []
    return reviewer, source['cases'], labels, originals, checks


def observation(row, units, case, giwt):
    verdict = row['verdict']
    require(verdict in VERDICTS, 'Unknown case verdict: ' + case)
    text(row['finding'], 'specific case finding for ' + case)
    cited = row['cells']
    require(isinstance(cited, dict) and (verdict != 'pass' or cited), 'A pass requires actual student cells: ' + case)
    conditional = []
    for uid, cells in cited.items():
        require(uid in units and units[uid]['status'] != 'deferred', 'Unknown or deferred evidence in ' + case)
        require(set(names(cells, case + ' evidence cells', True)) <= set(units[uid]['cells']),
                'Assessment cites cells outside the assigned unit: ' + case + ' ' + uid)
        if units[uid]['status'] == 'conditional':
            conditional.append(uid)
    item = {'verdict': verdict, 'cells': cited, 'conditional_units': sorted(conditional), 'finding': row['finding']}
    if giwt:
        bits, fatal = row['bits'], row['fatal']
        require(isinstance(bits, dict) and set(bits) == set(BITS) and
                all((type(v) is int and v in (0, 1)) or v == '?' for v in bits.values()) and
                type(fatal) is bool, 'Invalid GIWT evidence: ' + case)
        score = list(bits.values()).count(1)
        grade = 'insufficient' if fatal or score < 2 else ('sufficient' if score == 4 else 'partial')
        require((verdict == 'pass') == (grade == 'sufficient') and (not score or cited),
                'GIWT score disagrees with the verdict or lacks student cells: ' + case)
        item.update(bits=bits, fatal=fatal, grade=grade, score=score)
    return item


def consensus(votes, reader_count):
    if len(votes) < max(2, reader_count):
        return 'pending'
    judgments = {(v['verdict'], v.get('fatal'), tuple(v.get('bits', {}).get(k) for k in BITS)) for v in votes}
    return judgments.pop()[0] if len(judgments) == 1 else 'conflict'


def giwt_result(rows, cases, checks, conditional):
    reasons, gains, losses, grades, agreed = [], {}, {}, {}, {}
    for cid in sorted(cases):
        vectors = {}
        for side in SIDES:
            votes = list(rows[cid][side].values())
            agree = {key: {item['bits'][key] for item in votes} for key in BITS}
            vectors[side] = {key: next(iter(values)) if len(values) == 1 else 'conflict'
                             for key, values in agree.items()}
            if len(votes) < 2 or len({(v['fatal'], v['verdict']) for v in votes}) != 1 or any(len(v) != 1 for v in agree.values()):
                reasons.append(cid + ' ' + side + ': pending or conflicting case evidence')
            if side == 'candidate' and any(item['fatal'] or (item['conditional_units'] and cid not in conditional)
                                           for item in votes):
                reasons.append(cid + ': fatal judgment or untriggered conditional support')
        agreed[cid] = vectors
        old, new = vectors['incumbent'], vectors['candidate']
        grades[cid] = sum(v == 1 for v in new.values())
        losses[cid] = [k for k in BITS if old[k] == 1 and new[k] != 1]
        gains[cid] = [k for k in BITS if old[k] == 0 and new[k] == 1]
    if any(losses.values()):
        reasons.append('Previously supported evidence lost')
    if min(grades.values()) < 3 or list(grades.values()).count(4) < 3:
        reasons.append('Need at least three bits per case and three fully supported cases')
    if sum(bool(v) for v in gains.values()) < 2 or not any(set(v) & {'G', 'W', 'T'} for v in gains.values()):
        reasons.append('Need agreed gains in two cases, including G, W or T')
    for reader, sides in checks.items():
        for name, value in sides['candidate'].items():
            if value is not True:
                reasons.append(reader + ': ' + name + ' unresolved or adverse')
    return {'agreed_bits': agreed, 'scores': grades, 'gains': gains, 'losses': losses, 'blockers': reasons}


def compare(root, route_name, incumbent_name, protocol_name, results_name):
    records = {s: inspect_route(root, n, incumbent=s == 'incumbent')
               for s, n in zip(SIDES, (route_name, incumbent_name))}
    candidate, incumbent = (records[s][0] for s in SIDES)
    require(candidate['week'] == incumbent['week'] and candidate['id'] != incumbent['id'],
            'Comparands must be different routes for the same week')
    results_path = local(root, results_name)
    result = quality.load(results_path)
    schema(result)
    for key, path in [('candidate', route_name), ('incumbent', incumbent_name), ('protocol', protocol_name)]:
        match_ref(root, result[key], path)
    require(result['depth_sha256'] == candidate['depth_sha256'], 'Stale reviewed depth basis')
    freeze = ancestor(root, result['freeze_commit'])
    protocol, cases, mandatory, conditional, rule, matched = frozen_protocol(
        root, protocol_name, freeze, candidate['round_path'], records['candidate'][2])
    require(git_file(root, freeze, route_name) != local(root, route_name).read_bytes(),
            'Candidate route was already frozen before the protocol')
    assessment_dir = local(root, (results_path.parent / 'assessments').relative_to(root).as_posix())
    assigned, orders, allocation_files = disclosed_allocation(root, results_path, result, protocol.get('allocation_sha256'))
    expected = {f.relative_to(root).as_posix() for f in assessment_dir.glob('*.json')}
    receipts = result['assessments']
    require(isinstance(receipts, dict) and set(receipts) == expected, 'Bind every independent assessment in assessments/')
    context = {**{s: records[s][0]['route_sha256'] for s in SIDES}, 'depth': candidate['depth_sha256'],
               'protocol': result['protocol']['sha256']}
    evidence_anchor = shared_evidence(root, result, freeze)
    if evidence_anchor:
        context['evidence'] = result['evidence']['sha256']
    rows = {cid: {s: {} for s in SIDES} for cid in sorted(cases)}
    author = quality.load(local(root, candidate['round_path']))['author'].strip().casefold()
    checks = {}
    reviewers, archived = set(), {assessment_dir.relative_to(root).as_posix(), *allocation_files}
    if receipts:
        pinned_files(root, receipts, 'assessment')
    for receipt in sorted(receipts):
        reviewer, judgments, labels, originals, safety = reviewer_cases(root, receipt, context, rule, assigned, orders)
        checks[reviewer] = safety
        archived.update(originals)
        if evidence_anchor:
            require(all(git_file(root, evidence_anchor, p) is None for p in [receipt, *originals]),
                    'Independent assessment already existed at the shared evidence freeze')
        require(reviewer.casefold() != author, 'Candidate author cannot provide independent assessment')
        require(reviewer.casefold() not in reviewers, 'Independent assessments repeat the same reviewer')
        reviewers.add(reviewer.casefold())
        require(isinstance(judgments, dict) and set(judgments) <= cases, 'Unknown assessment case')
        for cid, row in judgments.items():
            require(set(row) == set(labels.values()) | ({'outputs'} if 'outputs' in row else set()),
                    'Assess both routes on each case: ' + cid)
            if 'outputs' in row:
                pinned_files(root, row['outputs'], 'case output for ' + cid)
                archived.update(row['outputs'])
            for side in SIDES:
                rows[cid][side][reviewer] = observation(row[labels[side]], records[side][1], cid, rule and cid in matched)
    immutable(root, freeze, sorted(archived))
    states = {cid: {s: consensus(side[s].values(), len(reviewers)) for s in SIDES} for cid, side in rows.items()}
    eligible = {cid for cid in cases if states[cid]['candidate'] == 'pass' and
                (cid in conditional or all(not o['conditional_units'] for o in rows[cid]['candidate'].values()))}
    decision = result['decision']
    require(decision in ('retain', 'hold', 'pilot', 'replace'), 'Unknown branch recommendation')
    finding = text(result['finding'], 'recommendation rationale')
    errors = []
    # Every row from each reader must be present, including the adverse and optional ones.
    if (len(reviewers) < 2 or (orders and reviewers != {r.casefold() for r in orders}) or
            any(len(v[s]) != len(reviewers) for v in rows.values() for s in SIDES)):
        errors.append('Pending a complete matched assessment from each of at least two different readers')
    appraisal = giwt_result(rows, matched, checks, conditional) if rule else None
    if decision == 'replace':
        if candidate['budget'] != 'within' or (rule and not candidate['complete_ranges']):
            errors.append('Replacement needs a complete workload within the weekly budget')
        if rule and appraisal['blockers']:
            errors.extend(appraisal['blockers'])
        if not (mandatory - matched if rule else mandatory) <= eligible:
            errors.append('Replacement requires affirmative agreement on mandatory cases')
    if decision == 'pilot':
        pilot = set(names(result.get('pilot_cases'), 'bounded pilot cases', True))
        pilot_bits = result.get('pilot_bits', {})
        require(isinstance(pilot_bits, dict) and pilot_bits.keys() <= pilot and (not pilot_bits or rule),
                'Pilot bits must belong to named matched cases')
        for cid, bits in pilot_bits.items():
            chosen = set(names(bits, 'pilot bits for ' + cid, True))
            require(cid in matched and chosen <= set(BITS), 'Unknown pilot case or bit')
            votes = list(rows[cid]['candidate'].values())
            supported = (len(votes) >= 2 and all(not v['fatal'] and (not v['conditional_units'] or cid in conditional)
                         and all(v['bits'][k] == 1 for k in chosen) for v in votes))
            if not supported:
                errors.append('Pilot bits lack affirmative agreement: ' + cid)
        if not pilot - pilot_bits.keys() <= eligible:
            errors.append('Pilot claims require affirmative agreement on the named cases')
    coverage = {}
    for side in SIDES:
        cited = {uid for pair in rows.values() for obs in pair[side].values() for uid in obs['cells']}
        coverage[side] = {uid: ('cited' if uid in cited else 'uncited') for uid in records[side][1]}
    return {'status': 'comparison_recorded' if not errors else 'blocked', 'errors': errors, 'decision': decision,
            'finding': finding, 'pilot_cases': result.get('pilot_cases', []), 'pilot_bits': result.get('pilot_bits', {}),
            'candidate': candidate,
            'incumbent': incumbent, 'protocol_sha256': context['protocol'], 'freeze_commit': freeze,
            'assessments': receipts, 'evidence': result.get('evidence'), 'evidence_commit': evidence_anchor,
            'allocation_sha256': protocol.get('allocation_sha256'), 'assigned_orders': orders,
            'case_states': states, 'eligible_cases': sorted(eligible),
            'mandatory_cases': sorted(mandatory), 'unit_coverage': coverage, 'observations': rows,
            'replacement_rule': rule, 'matched_rule_result': appraisal, 'reviewer_checks': checks,
            'scope': 'Branch material comparison. Learner outcomes and observed completion time are unmeasured.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'check'))
    parser.add_argument('--root', type=Path, default=quality.ROOT)
    parser.add_argument('--route', required=True, help='Candidate route manifest, relative to root')
    for name in ('incumbent', 'protocol', 'results'):
        parser.add_argument('--' + name, help='Repository-relative ' + name + ' manifest')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == 'check' and not all((args.incumbent, args.protocol, args.results)):
        parser.error('check requires --incumbent, --protocol and --results')
    if args.command == 'inspect' and (args.protocol or args.results):
        parser.error('use check to verify protocol or result manifests')
    try:
        if args.command == 'check':
            report = compare(root, args.route, args.incumbent, args.protocol, args.results)
        else:
            report, _, _ = inspect_route(root, args.route)
            if args.incumbent:
                report['incumbent'] = inspect_route(root, args.incumbent, incumbent=True)[0]
            report['status'] = 'route_verified'
    except ERRORS as err:
        report = {'status': 'blocked', 'errors': [str(err)]}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(report['status'] == 'blocked')


if __name__ == '__main__':
    raise SystemExit(main())
