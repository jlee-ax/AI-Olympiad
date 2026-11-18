"""Git-backed lesson registration, student navigation and independent source refreshes."""
from html.parser import HTMLParser
import hashlib
import json
import posixpath
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

import quality

# Routing is independent of editable notebook/bundle metadata. Other projects can use --case.
WEEK1_ENTRY = 'lessons/week01/week01_foundations.ipynb'
FOUNDATIONS = 'reviews/week01-depth-20261118'
CONTEST = 'reviews/week01-contest-20261118'
R5_COMMIT = '85211bc61260e8281f90aa15f6119255e1a07f53'
ACTIVE = {WEEK1_ENTRY: CONTEST}
ARCHIVED = {FOUNDATIONS: WEEK1_ENTRY}
TIERS = ('class', 'homework', 'optional')
VERDICTS = ('pass', 'revise', 'uncertain')
ERRORS = (ValueError, OSError, KeyError, TypeError, AttributeError, RecursionError, OverflowError)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and value.strip(), 'Missing ' + label)
    return value


def array(value, label, required=False):
    require(isinstance(value, list) and (value or not required), 'Invalid list: ' + label)
    return value


def names(value, label, required=False):
    values = array(value, label, required)
    for item in values:
        text(item, label)
    require(len(values) == len(set(values)), 'Duplicate ' + label)
    return values


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def version(record):
    require(type(record.get('schema_version')) is int and record['schema_version'] == 1,
            'Expected topic depth schema_version 1')


def minutes(record):
    require(isinstance(record, dict) and set(record) == set(TIERS) and
            all(type(n) is int and n >= 0 for n in record.values()), 'Invalid topic minutes')
    return record


def local(root, name):
    """Accept canonical, repository-relative regular paths without symlink aliases."""
    text(name, 'path')
    p = Path(name)
    require(not p.is_absolute() and p.parts and name == p.as_posix() and '..' not in p.parts,
            'Expected a canonical repository-relative path: ' + name)
    path = root / p
    require(path.resolve() == path, 'Symlink outside the evidence chain: ' + name)
    return path


def git(root, *args, check=True):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=False)
    if check and result.returncode:
        raise ValueError('Git evidence unavailable: ' + result.stderr.decode(errors='replace').strip())
    return result


def git_file(root, commit, path):
    listing = git(root, 'ls-tree', '-z', commit, '--', path).stdout.split(b'\0')
    if not listing[0]:
        return None
    info, actual = listing[0].split(b'\t', 1)
    mode, kind, blob = info.split()
    require(actual.decode() == path and mode in (b'100644', b'100755') and kind == b'blob',
            'Git evidence is not a regular file: ' + path)
    return git(root, 'cat-file', 'blob', blob.decode()).stdout


def commits(root, start, end, *paths):
    return git(root, 'log', '--topo-order', '--reverse', '--format=%H',
               start + '..' + end, '--', *paths).stdout.decode().splitlines()


def stored_bytes(root, name, historical=None):
    if historical is None:
        return local(root, name).read_bytes()
    path = Path(text(name, 'archived path'))
    require(path.parts and not path.is_absolute() and '..' not in path.parts and name == path.as_posix(),
            'Expected a canonical archived path')
    raw = git_file(root, historical, name)
    require(raw is not None, 'Historical file missing: ' + name)
    return raw


def stored_json(root, name, historical=None):
    if historical is None:
        return quality.load(local(root, name))
    value = json.loads(stored_bytes(root, name, historical).decode('utf-8'), object_pairs_hook=quality._pairs)
    quality.clean_json(value)
    return value


class Navigation(HTMLParser):
    """Collect named, visible text links and landing points, optionally in a curriculum row."""
    void = set('area base br col embed hr img input link meta param source track wbr'.split())

    def __init__(self, row_id=None):
        super().__init__()
        self.row_id = row_id
        self.in_row = row_id is None
        self.in_cell = row_id is None
        self.columns = [[]]
        self.attrs = None
        self.hidden = []
        self.anchor = None
        self.heading = None
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.row_id and tag == 'tr':
            self.in_row = attrs.get('id') == self.row_id
            if self.in_row:
                require(self.attrs is None, 'Duplicate student plan week')
                self.attrs = attrs
        if not self.in_row:
            return
        if self.hidden or tag in ('script', 'style', 'template', 'pre', 'del', 's') or (
                'hidden' in attrs or attrs.get('aria-hidden') == 'true' or
                re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', attrs.get('style') or '', re.I)):
            if tag not in self.void:
                self.hidden.append(tag)
            return
        if self.row_id and tag in ('td', 'th'):
            self.in_cell = True
            self.columns.append([])
        if not self.in_cell:
            return
        if tag == 'a':
            self.anchor = [attrs.get('href'), []]
            self.anchors.update(value for value in (attrs.get('id'), attrs.get('name')) if value)
        elif re.fullmatch('h[1-6]', tag):
            self.heading = []

    def handle_data(self, data):
        if self.in_row and not self.hidden:
            if self.anchor is not None:
                self.anchor[1].append(data)
            if self.heading is not None:
                self.heading.append(data)

    def handle_endtag(self, tag):
        if not self.in_row:
            return
        if self.hidden:
            if self.hidden[-1] == tag:
                self.hidden.pop()
            return
        if tag == 'a' and self.anchor is not None:
            href, label = self.anchor
            if href and ''.join(label).strip():
                self.columns[-1].append(unquote(href))
            self.anchor = None
        elif re.fullmatch('h[1-6]', tag) and self.heading is not None:
            heading = ''.join(self.heading).strip()
            self.anchors.add(heading.replace(' ', '-'))
            self.heading = None
        elif self.row_id and tag in ('td', 'th'):
            self.in_cell = False
            self.anchor = None
        elif self.row_id and tag == 'tr':
            self.in_row = self.in_cell = False


def normal_entry(root, entry, week, historical):
    contract = stored_json(root, quality.CONTRACT, historical)
    plan = contract['baseline']['path']
    raw = stored_bytes(root, plan, historical)
    require(raw is not None and sha(raw) == contract['baseline']['sha256'], 'Student plan differs from curriculum')
    nav = Navigation('week-' + str(week))
    nav.feed(raw.decode('utf-8'))
    nav.close()
    require(nav.attrs is not None, 'Missing student plan week')
    origin = git(root, 'config', '--get', 'remote.origin.url', check=False).stdout.decode().strip()
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([^/]+/[^/]+?)(?:\.git)?/?', origin)
    for href in nav.columns[-1]:
        url = urlsplit(href)
        if url.query or url.fragment:
            continue
        if not url.scheme and not url.netloc and posixpath.normpath(posixpath.join(posixpath.dirname(plan), url.path)) == entry:
            proof = 'relative path in the archived plan' if historical else 'relative path in the current plan'
            break
        if match and (url.scheme, url.netloc) == ('https', 'github.com'):
            prefix = '/' + match[1] + '/blob/'
            if url.path.startswith(prefix) and url.path.endswith('/' + entry):
                ref = url.path[len(prefix):-(len(entry) + 1)]
                proof = advertised_ref(root, ref, entry, historical)
                if proof:
                    break
    else:
        raise ValueError('Normal student material column does not open the declared entry')
    attrs = nav.attrs
    class_minutes = sum(int(attrs['data-' + key + '-minutes']) for key in ('theory', 'noncoding', 'coding'))
    hours = [int(attrs['data-self-' + key + '-hours']) for key in ('min', 'max')]
    weeks = [w for w in contract['weeks'] if w['week'] == week]
    require(len(weeks) == 1 and class_minutes == contract['class_minutes'] and
            weeks[0]['required_self_study_hours'] == hours, 'Student plan workload differs from curriculum')
    require(week != 1 or (class_minutes, hours) == (120, [5, 7]), 'Unexpected Week 1 time budget')
    return (class_minutes, hours[0] * 60, hours[1] * 60), {'plan': plan, 'plan_sha256': sha(raw),
                                                          'href': href, 'basis': proof}


def advertised_ref(root, ref, entry, historical):
    if not ref or ref.startswith('-') or git(root, 'check-ref-format', 'refs/heads/' + ref, check=False).returncode:
        return None
    if not historical:
        branch = git(root, 'symbolic-ref', '-q', '--short', 'HEAD', check=False).stdout.decode().strip()
        if branch == ref:
            return 'link names the current working branch'
    expected = stored_bytes(root, entry, historical)
    known = False
    for name in (ref, 'refs/remotes/origin/' + ref):
        resolved = git(root, 'rev-parse', '--verify', name + '^{commit}', check=False)
        if resolved.returncode:
            continue
        known = True
        head = resolved.stdout.decode().strip()
        revisions = [head]
        if historical and not re.fullmatch(r'[0-9a-f]{40}', ref):
            revisions += git(root, 'rev-list', head, '--', entry).stdout.decode().splitlines()
        if any(git_file(root, r, entry) == expected for r in revisions):
            return 'entry bytes verified in the advertised Git reference'
    if historical and not known and not re.fullmatch(r'[0-9a-f]{40}', ref):
        return 'archived curriculum plan and entry blob (old named branch unavailable locally)'
    return None


def registered(path):
    """Recognize an active entry or its archived candidates even if no bundle declares a gate."""
    if not isinstance(path, str):
        return None
    if path in ACTIVE:
        return ACTIVE[path]
    for case in (*ACTIVE.values(), *ARCHIVED):
        if re.fullmatch(re.escape(case) + r'/rounds/[0-9]{4}/candidate\.ipynb', path):
            return case
    return None


def topology(topics):
    """Prerequisite-first order; a deferred or missing cycle can never gain an automatic pass."""
    done = set()
    order = []
    for tid, item in topics.items():
        deps = names(item.get('prerequisites'), 'prerequisites of ' + tid)
        require(set(deps) <= topics.keys(), 'Unknown prerequisite: ' + tid)
    while len(order) < len(topics):
        available = [tid for tid, item in topics.items()
                     if tid not in done and set(item['prerequisites']) <= done]
        require(available, 'Cyclic prerequisite graph')
        order.extend(available)
        done.update(available)
    return order


def contract_topics(root, case, c):
    version(c)
    lesson = c['lesson_path']
    local(root, lesson)
    require(lesson.endswith('.ipynb'), 'Contract needs a student notebook')
    registered_lessons = {**ARCHIVED, **{case_name: path for path, case_name in ACTIVE.items()}}
    if case in registered_lessons or lesson in registered_lessons.values():
        require(registered_lessons.get(case) == lesson, 'Foreign contract for a registered lesson')
    text(c.get('author'), 'contract author')
    text(c.get('audience'), 'entry audience')
    require(type(c['class_minutes']) is int and c['class_minutes'] > 0, 'Invalid class limit')
    if case in registered_lessons:
        require(c['class_minutes'] == 120, 'The registered class requires 120 minutes')
    srcs = array(c['source_inputs'], 'pinned sources', True)
    for src in srcs:
        text(src['locator'], 'source locator')
        local(root, src['path'])
        require(isinstance(src['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', src['sha256']), 'Invalid source digest')
    companions = names(c['companion_paths'], 'companion paths')
    for name in companions:
        local(root, name)
        require(name != lesson and not name.startswith(case + '/') and
                name not in [s['path'] for s in srcs], 'Source/companion path collision: ' + name)
    topics = {}
    for item in array(c['topics'], 'topics', True):
        tid = text(item['id'], 'topic id')
        require(tid not in topics, 'Duplicate topic ' + tid)
        for field in ('objective', 'entry', 'minimum', 'ceiling', 'assessment'):
            text(item.get(field), tid + '.' + field)
        minutes(item['minutes'])
        basis = array(item['sources'], 'source bindings for ' + tid, True)
        require(all(type(i) is int and 0 <= i < len(srcs) for i in basis) and len(set(basis)) == len(basis),
                'Unknown or repeated source binding: ' + tid)
        topics[tid] = item
    order = topology(topics)
    require(sum(t['minutes']['class'] for t in topics.values()) == c['class_minutes'],
            'Frozen class allocations differ from class limit')
    if case == CONTEST:
        require(c.get('maximum_home_minutes') == 420 and
                sum(t['minutes']['homework'] + t['minutes']['optional'] for t in topics.values()) <= 420,
                'Required and optional R6 workload must fit the 420-minute cap')
        training = c['public_training']
        require(training['path'] in companions and re.fullmatch(r'[0-9a-f]{64}', training['sha256']),
                'Bind the exact public Antique input as a companion')
    return topics, order


def frozen(root, case):
    directory = local(root, case)
    require(git(root, 'rev-parse', '--show-toplevel').stdout.decode().strip() == str(root),
            'The review root must be the root of its own Git checkout')
    require(git(root, 'rev-parse', '--is-shallow-repository').stdout.strip() == b'false',
            'Full Git history is required to verify a pre-edit freeze')
    cname, rname = case + '/contract.json', case + '/freeze-review.json'
    cpath, rpath = local(root, cname), local(root, rname)
    c, review = quality.load(cpath), quality.load(rpath)
    version(review)
    topics, order = contract_topics(root, case, c)
    lesson, srcs = c['lesson_path'], c['source_inputs']
    author = c['author'].strip().casefold()
    digest = quality.file_digest(cpath)
    require(review['stage'] == 'freeze' and review['contract_sha256'] == digest
            and review['verdict'] == 'pass', 'Missing current independent approval of the freeze')
    require(text(review['reviewer'], 'freeze reviewer').strip().casefold() != author,
            'The contract author cannot approve the freeze')
    text(review.get('finding'), 'freeze judgment')
    require(set(review['topics']) == set(topics), 'Freeze review must cover every topic')
    for tid, judgment in review['topics'].items():
        for field in ('foundation', 'ceiling', 'workload'):
            text(judgment.get(field), 'freeze review ' + tid + '.' + field)
    additional_freezes = {}
    history_dir = local(root, case + '/criteria-history')
    for old in sorted(history_dir.iterdir()) if history_dir.exists() else []:
        relative = old.relative_to(root).as_posix()
        old_c = local(root, relative + '/contract.json')
        old_r = local(root, relative + '/freeze-review.json')
        old_review = quality.load(old_r)
        old_digest = quality.file_digest(old_c)
        require(old_review['contract_sha256'] == old_digest and old_review['stage'] == 'freeze' and
                old_review['verdict'] in VERDICTS, 'Foreign or incomplete criteria history: ' + relative)
        require(old_digest != digest or old_review['verdict'] == 'pass',
                'Competing freeze judgments for the same contract')
        additional_freezes.update({old_c.relative_to(root).as_posix(): old_digest,
                                  old_r.relative_to(root).as_posix(): quality.file_digest(old_r)})
    reviewers_dir = local(root, case + '/freeze-reviews')
    for extra in sorted(reviewers_dir.iterdir()) if reviewers_dir.exists() else []:
        local(root, extra.relative_to(root).as_posix())
        other = quality.load(extra)
        require(other['stage'] == 'freeze' and other['contract_sha256'] == digest and
                other['verdict'] == 'pass' and text(other['reviewer'], 'freeze reviewer').strip().casefold() != author and
                set(other['topics']) == set(topics), 'Competing or pending freeze review: ' + extra.name)
        additional_freezes[extra.relative_to(root).as_posix()] = quality.file_digest(extra)
    base = c['baseline']
    if case == FOUNDATIONS:
        require(base['sha256'] is None, 'The first foundations study requires proof of original authorship')
    if case == CONTEST:
        require(base['commit'] == R5_COMMIT and c.get('predecessor') == {'case': FOUNDATIONS, 'round': 5},
                'The contest study must start at the pinned R5 public commit and reviewed ordinal')
        previous = git_file(root, R5_COMMIT, FOUNDATIONS + '/rounds/0005/candidate.ipynb')
        require(previous is not None and base['sha256'] == sha(previous), 'Foreign predecessor notebook for R6')
        immutable(root, R5_COMMIT, [FOUNDATIONS])
    start = base['commit']
    require(isinstance(start, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', start) and
            git(root, 'cat-file', '-t', start).stdout.strip() == b'commit' and
            git(root, 'merge-base', '--is-ancestor', start, 'HEAD', check=False).returncode == 0,
            'Baseline must be a full ancestor commit in this checkout')
    original = git_file(root, start, lesson)
    require((original is None and base['sha256'] is None) or
            (original is not None and sha(original) == base['sha256']), 'Baseline bytes disagree with Git')
    # Both files must exist in the same ancestor tree, before editing the active path or archiving a draft.
    inputs = {cname: digest, rname: quality.file_digest(rpath), **additional_freezes}
    for src in srcs:
        inputs[src['path']] = src['sha256']
    anchor = committed_inputs(root, start, inputs, 'Commit the exact contract, its independent review and source inputs before editing')
    require(git_file(root, anchor, lesson) == original and
            not commits(root, start, anchor, lesson, case + '/rounds', *c['companion_paths']) and
            not git(root, 'ls-tree', '-r', anchor, '--', case + '/rounds').stdout,
            'Student material or an archived draft preceded the reviewed freeze')
    immutable(root, anchor, [cname, rname, case + '/freeze-reviews', case + '/criteria-history'])
    return {'contract': c, 'sha256': digest, 'topics': topics, 'order': order, 'anchor': anchor,
            'directory': directory, 'after_round': 0, 'reopen': [], 'reviewer': review['reviewer'],
            'review_sha256': quality.file_digest(rpath)}


def immutable(root, anchor, paths):
    # New files can be appended. A staged deletion or an already-committed rewrite also fails.
    for args in (['log', '--full-history', '-m', '--format=', '--name-only', '--no-renames',
                  '--diff-filter=MDT', anchor + '..HEAD'],
                 ['diff', '--name-only', '--no-renames', '--diff-filter=MDT', 'HEAD']):
        changed = git(root, *args, '--', *paths).stdout.decode().strip()
        require(not changed, 'Committed iteration evidence was removed or rewritten: ' + changed)


def committed_inputs(root, start, inputs, error):
    for revision in [start, *commits(root, start, 'HEAD', *inputs)]:
        if all((raw := git_file(root, revision, name)) is not None and sha(raw) == expected
               for name, expected in inputs.items()):
            return revision
    raise ValueError(error)


def excerpt(raw, span):
    lines = raw.splitlines(keepends=True)
    require(isinstance(span, list) and len(span) == 2 and all(type(i) is int for i in span) and
            1 <= span[0] <= span[1] <= len(lines), 'Invalid source refresh line span')
    value = b''.join(lines[span[0] - 1:span[1]])
    require(value.strip(), 'Empty source refresh excerpt')
    return value


def source_refresh(root, case, directory, previous):
    prefix = directory.relative_to(root).as_posix()
    cpath = local(root, prefix + '/contract.json')
    rpath = local(root, prefix + '/review.json')
    c, review = quality.load(cpath), quality.load(rpath)
    version(review)
    topics, order = contract_topics(root, case, c)
    old = previous['contract']
    fixed = ['lesson_path', 'baseline', 'companion_paths', 'class_minutes']
    if case == CONTEST:
        fixed += ['predecessor', 'public_training', 'maximum_home_minutes']
    for key in fixed:
        require(c[key] == old[key], 'A source refresh cannot replace frozen identity or class limits: ' + key)
    srcs, old_srcs = c['source_inputs'], old['source_inputs']
    require([s['path'] for s in srcs] == [s['path'] for s in old_srcs] and topics.keys() == previous['topics'].keys(),
            'Source refreshes retain topic IDs and source paths; a different scope needs a newly registered case')
    digest = quality.file_digest(cpath)
    require(digest != previous['sha256'] and c != old, 'Duplicate source/criteria refresh')
    require(review['stage'] == 'refresh' and review['previous_contract_sha256'] == previous['sha256']
            and review['contract_sha256'] == digest and review['previous_review_sha256'] == previous['review_sha256'],
            'Foreign source refresh or missing previous review')
    reviewer = text(review.get('reviewer'), 'refresh reviewer').strip().casefold()
    require(reviewer not in {c['author'].strip().casefold(), old['author'].strip().casefold()},
            'Criteria editor cannot approve the source refresh')
    text(review.get('finding'), 'refresh finding')
    after = review['after_round']
    require(type(after) is int and previous['after_round'] <= after <= 9999, 'Out-of-order source refresh')
    inputs = {prefix + '/contract.json': digest, prefix + '/review.json': quality.file_digest(rpath)}
    folder = local(root, prefix + '/reviews')
    for receipt in sorted(folder.iterdir()) if folder.exists() else []:
        name = receipt.relative_to(root).as_posix()
        other = quality.load(local(root, name))
        require({k: v for k, v in other.items() if k != 'reviewer'} ==
                {k: v for k, v in review.items() if k != 'reviewer'} and
                text(other['reviewer'], 'refresh reviewer').strip().casefold() not in {reviewer, c['author'].strip().casefold()},
                'Competing or pending source refresh: ' + name)
        inputs[name] = quality.file_digest(receipt)
    inputs.update({s['path']: s['sha256'] for s in srcs})
    if after:
        prior = case + '/rounds/' + f'{after:04d}'
        round_path = local(root, prior + '/round.json')
        require(quality.file_digest(round_path) == review['previous_round_sha256'] and
                reviewer != quality.load(round_path)['author'].strip().casefold(), 'Foreign or self-reviewed prior iteration')
        prior_receipts = {f.name: quality.file_digest(local(root, f.relative_to(root).as_posix()))
                          for f in sorted(local(root, prior + '/reviews').iterdir())}
        require(prior_receipts and prior_receipts == review['prior_reviews'], 'Account for all preceding reviews at refresh')
        inputs[prior + '/round.json'] = review['previous_round_sha256']
        inputs.update({prior + '/reviews/' + name: value for name, value in prior_receipts.items()})
    else:
        require(review['previous_round_sha256'] is None and review['prior_reviews'] == {}, 'Foreign initial refresh history')
    anchor = committed_inputs(root, previous['anchor'], inputs, 'Commit the reviewed source refresh before the next draft')
    next_dir = case + '/rounds/' + f'{after + 1:04d}'
    require(not commits(root, previous['anchor'], anchor, next_dir) and
            not git(root, 'ls-tree', '-r', anchor, '--', next_dir).stdout, 'Candidate preceded refreshed depth criteria')
    allowed = {old['baseline']['sha256']}
    for i in range(1, after + 1):
        name = case + '/rounds/' + f'{i:04d}' + '/candidate.ipynb'
        raw = git_file(root, anchor, name)
        require(raw is not None, 'Prior candidate was absent at refresh: ' + name)
        allowed.add(sha(raw))
    for revision in commits(root, previous['anchor'], anchor, c['lesson_path']):
        raw = git_file(root, revision, c['lesson_path'])
        require((None if raw is None else sha(raw)) in allowed, 'Direct new lesson edits preceded refreshed criteria')
    require(set(review['topics']) == set(topics), 'Independently assess the refresh for every frozen topic')
    changes = {i for i, src in enumerate(srcs) if src != old_srcs[i]}
    versions = {i: (git_file(root, previous['anchor'], old_srcs[i]['path']), git_file(root, anchor, srcs[i]['path']))
                for i in changes}
    reopened = set()
    for tid in order:
        item = review['topics'][tid]
        text(item.get('finding'), 'refresh judgment for ' + tid)
        decision = item['decision']
        require(decision in ('carry', 'reopen'), 'Unsettled source refresh for ' + tid)
        before, after_topic = previous['topics'][tid], topics[tid]
        needs = changes.intersection(set(before['sources']) | set(after_topic['sources']))
        require(set(item['sources']) == {str(i) for i in needs}, 'Review every changed source used by ' + tid)
        if decision == 'carry':
            require(before == after_topic and c['audience'] == old['audience'],
                    'Changed topic criteria or audience require a new material judgment: ' + tid)
        for i in needs:
            spans = array(item['sources'][str(i)], 'affected source excerpts for ' + tid, True)
            for span in spans:
                original = excerpt(versions[i][0], span['old_lines'])
                updated = excerpt(versions[i][1], span['new_lines'])
                require(decision == 'reopen' or (original == updated and old_srcs[i]['locator'] == srcs[i]['locator']),
                        'Changed source meaning cannot be carried forward: ' + tid)
        if decision == 'reopen' or reopened.intersection(after_topic['prerequisites']):
            reopened.add(tid)
    return {'contract': c, 'topics': topics, 'order': order, 'sha256': digest, 'anchor': anchor, 'after_round': after,
            'reopen': sorted(reopened), 'reviewer': review['reviewer'], 'review_sha256': quality.file_digest(rpath)}


def basis_chain(root, case):
    first = frozen(root, case)
    records = [first]
    directory = local(root, case + '/refreshes')
    immutable(root, first['anchor'], [case + '/refreshes'])
    for number, path in enumerate(sorted(directory.iterdir()) if directory.exists() else [], 1):
        require(path.is_dir() and path.name == f'{number:04d}', 'Nonconsecutive source refresh history')
        records.append(source_refresh(root, case, path, records[-1]))
    for src in records[-1]['contract']['source_inputs']:
        require(quality.file_digest(local(root, src['path'])) == src['sha256'],
                'Source bytes differ: ' + src['path'] + '; append an independent source refresh')
    return records
