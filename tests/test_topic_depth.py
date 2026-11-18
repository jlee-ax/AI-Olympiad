"""Git-backed production-path controls. All reviewers and material judgments here are synthetic."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_material_revision as revisions
from test_quality import ROOT, quality, workflow
import discovery_loop
import material_revision
import topic_depth as depth

LESSON, CASE = next(iter(depth.ACTIVE.items()))
TOPICS = ('return', 'table', 'graph', 'reading')
KEY = 'lessons/week01/key.md'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True, text=True, capture_output=True).stdout.strip()


def commit(root, *paths):
    git(root, 'add', '--', *paths)
    git(root, '-c', 'user.name=Test Author', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
    return git(root, 'rev-parse', 'HEAD')


def initialize(root, lesson=LESSON):
    git(root, 'init', '-q')
    if not (root / 'source.txt').exists():
        (root / 'source.txt').write_text('Synthetic fixture: show the denominator, then use it on an unseen table.\n')
    paths = ['source.txt']
    if (root / lesson).exists():
        paths.append(lesson)
    return commit(root, *paths)


def create_freeze(root, start, lesson=LESSON, topic_ids=TOPICS, companions=(KEY,)):
    cpath = root / CASE / 'contract.json'
    rpath = cpath.with_name('freeze-review.json')
    deps = {'table': ['return'], 'graph': ['table']}
    topics = [{'id': tid, 'objective': 'Explain and apply ' + tid, 'entry': 'Basic coding.',
               'minimum': 'Demonstrate ' + tid + ' on an unseen input.',
               'ceiling': 'Defer the general proof to a later course.', 'assessment': 'Predict then check.',
               'prerequisites': deps.get(tid, []), 'sources': [0],
               'minutes': {'class': 120 // len(topic_ids), 'homework': 0, 'optional': 0}}
              for tid in topic_ids]
    contract = {'schema_version': 1, 'lesson_path': lesson, 'author': 'contract author',
                'baseline': {'commit': start, 'sha256': quality.file_digest(root / lesson)
                             if (root / lesson).exists() else None}, 'audience': 'Novice coders.',
                'class_minutes': 120, 'source_inputs': [{'path': 'source.txt',
                'sha256': quality.file_digest(root / 'source.txt'), 'locator': 'first paragraph'}],
                'companion_paths': list(companions), 'topics': topics}
    save(cpath, contract)
    review = {'schema_version': 1, 'stage': 'freeze', 'reviewer': 'independent contract test control',
              'contract_sha256': quality.file_digest(cpath), 'verdict': 'pass', 'finding': 'Fixture contract.',
              'topics': {tid: {'foundation': 'Direct prediction and verification.', 'ceiling': 'General proof deferred.',
                               'workload': 'Scoped planned time.'} for tid in topic_ids}}
    save(rpath, review)
    return cpath, rpath


def notebook():
    return {'nbformat': 4, 'nbformat_minor': 5, 'metadata': {}, 'cells': [
        {'id': tid + suffix, 'cell_type': 'markdown', 'metadata': {},
         'source': ['Trace a concrete ' + tid if suffix == '-why' else 'Apply ' + tid + ' to a new input.']}
        for tid in TOPICS for suffix in ('-why', '-task')]}


def make_maps():
    parents = {'table': 'return', 'graph': 'table'}
    return {tid: {'class': [tid + '-why', tid + '-task'], 'homework': [], 'optional': [],
                  'support': [tid + '-why'], 'assessment': [tid + '-task'],
                  'prerequisite_uses': {parents[tid]: tid + '-why'} if tid in parents else {},
                  'minutes': {'class': 30, 'homework': 0, 'optional': 0}} for tid in TOPICS}


def write_round(root, number, candidate, maps, *, archive_key=True, author='fixture editor', changes=None):
    folder = root / CASE / 'rounds' / f'{number:04d}'
    npath, rpath = folder / 'candidate.ipynb', folder / 'round.json'
    if candidate is not None:
        save(npath, candidate)
    row = {'schema_version': 1, 'author': author, 'contract_sha256': quality.file_digest(root / CASE / 'contract.json'),
           'previous': None, 'prior_reviews': {}, 'candidate_sha256': quality.file_digest(npath),
           'companions': [], 'topics': maps, 'changes': [
               {'topic': tid, 'action': 'Write or reconsider the identified cell.',
                'reason': 'The test case changes this staged topic.', 'alternative': 'Keep the previous explanation.'}
               for tid in (maps if changes is None else changes)]}
    if number > 1:
        prev = folder.with_name(f'{number-1:04d}')
        row['previous'] = quality.file_digest(prev / 'round.json')
        row['prior_reviews'] = {p.name: quality.file_digest(p) for p in (prev / 'reviews').glob('*.json')}
    if archive_key:
        key = folder / 'key.md'
        key.write_text('Fixture key for the exact assignment.\n')
        row['companions'] = [{'path': KEY, 'snapshot': key.relative_to(root).as_posix(), 'sha256': quality.file_digest(key)}]
    save(rpath, row)
    return rpath


def review_round(record, topics=None, reviewer='independent fixture', verdict='pass', name='editorial.json'):
    row = quality.load(record)
    items = {tid: {'verdict': verdict, 'cells': list(dict.fromkeys(row['topics'][tid]['support'] + row['topics'][tid]['assessment'])),
                   'foundation': 'Concrete support before the unseen prediction.',
                   'ceiling': 'No additional compulsory task beyond the agreed problem.',
                   'workload': 'Review of mapped material and estimated time.',
                   'finding': 'Controlled judgment for a routing test.'} for tid in (topics if topics is not None else row['topics'])}
    review = {'schema_version': 1, 'stage': 'candidate', 'contract_sha256': row['contract_sha256'],
              'candidate_sha256': row['candidate_sha256'], 'round_sha256': quality.file_digest(record),
              'reviewer': reviewer, 'topics': items}
    path = record.parent / 'reviews' / name
    save(path, review)
    return path


class TopicDepth(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.start = initialize(self.root)
        self.cpath, self.rpath = create_freeze(self.root, self.start)
        self.maps, self.nb = make_maps(), notebook()

    def freeze(self):
        return commit(self.root, CASE + '/contract.json', CASE + '/freeze-review.json')

    def draft(self, number=1, changes=None):
        return write_round(self.root, number, self.nb, self.maps, changes=changes)

    def active(self, record):
        path = self.root / LESSON
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(record.parent / 'candidate.ipynb', path)
        shutil.copyfile(record.parent / 'key.md', self.root / KEY)

    def cli(self, command):
        process = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/topic_depth.py'), command,
                                  '--root', str(self.root)], capture_output=True, text=True)
        return process.returncode, json.loads(process.stdout)

    def result(self):
        return depth.checked(self.root, CASE)

    def assertBlocked(self, fragment):
        result = self.result()
        self.assertFalse(result['ready'], result)
        self.assertIn(fragment, ' '.join(result['errors']))

    def test_from_scratch_freeze_needs_committed_independent_criteria_before_student_material(self):
        self.assertNotEqual(self.cli('freeze')[0], 0)
        actual = self.freeze()
        self.assertEqual(self.cli('freeze')[1]['freeze_commit'], actual)
        self.assertBlocked('No reviewed candidate')

    def test_a_contract_committed_with_or_after_the_first_draft_cannot_claim_a_freeze(self):
        record = self.draft()
        self.active(record)
        commit(self.root, CASE, LESSON, KEY)
        self.assertBlocked('preceded')
        (self.root / LESSON).unlink()
        commit(self.root, LESSON)
        self.assertBlocked('preceded')

    def test_full_history_proof_survives_a_pull_request_merge_commit(self):
        git(self.root, 'branch', 'target-branch', self.start)
        self.freeze()
        first = self.draft()
        review_round(first)
        self.active(first)
        tip = commit(self.root, CASE + '/rounds', LESSON, KEY)
        git(self.root, 'switch', '-q', 'target-branch')
        (self.root / 'unrelated.txt').write_text('An independent mainline change.')
        commit(self.root, 'unrelated.txt')
        git(self.root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
            'merge', '--no-ff', '--quiet', '-m', 'temporary PR integration ref', tip)
        self.assertTrue(self.result()['ready'], self.result())

    def test_false_git_anchor_and_cyclic_prerequisites_are_blocked(self):
        contract, reviewer = quality.load(self.cpath), quality.load(self.rpath)
        for field, edit, expected in [('baseline', {'commit': '0' * 40, 'sha256': None}, 'Git'),
                                      ('topics', copy.deepcopy(contract['topics']), 'Cyclic')]:
            with self.subTest(field=field):
                invalid = copy.deepcopy(contract)
                invalid[field] = edit
                if field == 'topics':
                    invalid[field][0]['prerequisites'] = ['graph']
                save(self.cpath, invalid)
                save(self.rpath, {**reviewer, 'contract_sha256': quality.file_digest(self.cpath)})
                self.assertBlocked(expected)

    def test_conflicting_or_self_approved_freezes_and_stale_source_do_not_open_authorship(self):
        review = quality.load(self.rpath)
        save(self.rpath, {**review, 'reviewer': ' CONTRACT Author '})
        self.assertBlocked('author')
        save(self.rpath, review)
        extra = self.cpath.parent / 'freeze-reviews/second.json'
        save(extra, {**review, 'reviewer': 'outside B', 'verdict': 'uncertain'})
        self.assertBlocked('Competing')
        extra.unlink()
        self.freeze()
        (self.root / 'source.txt').write_text('Different source bytes.')
        self.assertBlocked('Source bytes differ')

    def test_active_direct_edit_missing_metadata_changed_key_and_unpublished_draft_fail(self):
        self.freeze()
        record = self.draft()
        self.active(record)
        self.assertBlocked('Unresolved')
        review_round(record)
        self.assertEqual(self.cli('check')[0], 0)
        self.nb['cells'][0]['source'] = ['Same ID, incorrect edited explanation.']
        save(self.root / LESSON, self.nb)
        self.assertBlocked('Selected notebook differs')
        self.active(record)
        (self.root / KEY).write_text('Foreign answer key.')
        self.assertBlocked('Active companion')
        archived = record.parent.relative_to(self.root).as_posix() + '/candidate.ipynb'
        self.assertTrue(depth.checked(self.root, CASE, target=archived, stage=True)['ready'])
        self.active(record)
        (record.parent.with_name('0002')).mkdir()
        self.assertNotEqual(self.cli('check')[0], 0)

    def test_in_place_edits_reopen_only_affected_topics_and_transitive_dependents(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        self.nb['cells'][0]['source'] = ['New return semantics in the same existing cell ID.']
        second = self.draft(2, ['return', 'table', 'graph'])
        self.active(second)
        review_round(second, ['return'])
        prior = self.result()['history'][-1]
        self.assertEqual(prior['required_topics'], ['graph', 'return', 'table'])
        self.assertEqual(prior['decisions']['reading'], 'pass')
        self.assertEqual(prior['decisions']['table'], 'pending')
        review_round(second, ['graph', 'table'], reviewer='second fixture', name='dependent.json')
        self.assertTrue(self.result()['ready'])

    def test_new_local_cell_leaves_independent_topic_current_and_cross_topic_reorder_is_reviewed(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        self.nb['cells'].insert(5, {'id': 'graph-step', 'metadata': {}, 'cell_type': 'markdown', 'source': 'Try another scale.'})
        self.maps['graph']['class'].insert(1, 'graph-step')
        second = self.draft(2, ['graph'])
        review_round(second, ['graph'])
        self.active(second)
        self.assertTrue(self.result()['ready'])
        reading = self.nb['cells'][-2:]
        self.nb['cells'] = self.nb['cells'][:4] + reading + self.nb['cells'][4:-2]
        third = self.draft(3, ['graph', 'reading'])
        self.active(third)
        self.assertEqual(self.result()['history'][-1]['required_topics'], ['graph', 'reading'])
        review_round(third, ['graph', 'reading'])
        self.assertTrue(self.result()['ready'])

    def test_changed_prerequisite_use_and_time_allocation_invalidate_prior_judgments(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        self.maps['table']['prerequisite_uses']['return'] = 'table-task'
        self.maps['graph']['minutes']['class'] = 29
        self.maps['reading']['minutes']['class'] = 31
        second = self.draft(2)
        self.active(second)
        self.assertEqual(self.result()['history'][-1]['required_topics'], ['graph', 'reading', 'table'])
        review_round(second, ['graph', 'reading', 'table'])
        self.assertTrue(self.result()['ready'])
        self.maps['table']['prerequisite_uses'].clear()
        self.draft(3)
        self.assertBlocked('every prerequisite')

    def test_missing_support_excess_compulsory_homework_and_unclassified_cells_are_blocking(self):
        self.freeze()
        base = self.draft()
        self.active(base)
        for faulty, expected in [('support', 'Invalid list'), ('time', 'Outside frozen homework budget'),
                                 ('unmapped', 'Unmapped student cells'), ('before', 'before first use')]:
            with self.subTest(faulty=faulty):
                maps, nb = make_maps(), notebook()
                if faulty == 'support':
                    maps['table']['support'] = []
                if faulty == 'time':
                    maps['graph']['homework'] = ['extra']
                    maps['graph']['minutes']['homework'] = 90
                    nb['cells'].append({'id': 'extra', 'cell_type': 'markdown', 'metadata': {}, 'source': 'Extra derivation.'})
                if faulty == 'unmapped':
                    nb['cells'].append({'id': 'extra', 'cell_type': 'markdown', 'metadata': {}, 'source': 'Hidden work.'})
                if faulty == 'before':
                    nb['cells'][:4] = nb['cells'][2:4] + nb['cells'][:2]
                write_round(self.root, 1, nb, maps)
                self.assertBlocked(expected)

    def test_foreign_candidate_external_judgment_missing_role_and_competing_votes(self):
        self.freeze()
        record = self.draft()
        self.active(record)
        path = review_round(record)
        correct = quality.load(path)
        for field in ('candidate_sha256', 'round_sha256', 'contract_sha256'):
            save(path, {**correct, field: 'a' * 64})
            self.assertBlocked('Foreign or stale')
        save(path, {**correct, 'reviewer': 'Fixture Editor'})
        self.assertBlocked('independent')
        partial = copy.deepcopy(correct)
        partial['topics']['table']['cells'] = ['table-task']
        save(path, partial)
        self.assertBlocked('support locator')
        save(path, correct)
        review_round(record, ['graph'], reviewer='external critique', verdict='revise', name='critique.json')
        self.assertEqual(self.result()['history'][0]['decisions']['graph'], 'conflict')
        second = self.draft(2, ['graph'])
        review_round(second, ['graph'])
        self.assertBlocked('unchanged adverse finding')
        self.nb['cells'][4]['source'] = ['Repair the incorrect worked example in this cell.']
        second = self.draft(2, ['graph'])
        review_round(second, ['graph'])
        self.active(second)
        self.assertTrue(self.result()['ready'])

    def test_prior_adverse_reviews_cannot_be_removed_silently_or_rewritten_in_git(self):
        self.freeze()
        first = self.draft()
        path = review_round(first)
        bad = review_round(first, ['graph'], reviewer='second independent', verdict='revise', name='second.json')
        self.active(first)
        commit(self.root, CASE + '/rounds', LESSON, KEY)
        bad.unlink()
        self.assertBlocked('removed or rewritten')
        git(self.root, 'restore', '--', bad.relative_to(self.root).as_posix())
        self.nb['cells'][4]['source'] = ['Correct the counterexample.']
        second = self.draft(2, ['graph'])
        review_round(second, ['graph'])
        self.active(second)
        altered = quality.load(second)
        del altered['prior_reviews'][bad.name]
        save(second, altered)
        self.assertBlocked('every prior independent review')
        altered = quality.load(path)
        altered['topics']['return']['finding'] = 'Post hoc amendment.'
        save(path, altered)
        commit(self.root, path.relative_to(self.root).as_posix())
        self.assertBlocked('removed or rewritten')

    def test_unarchived_commit_cannot_be_hidden_by_restoring_approved_work(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        self.active(first)
        commit(self.root, CASE + '/rounds', LESSON, KEY)
        self.nb['cells'][0]['source'] = ['Incorrect version published directly.']
        save(self.root / LESSON, self.nb)
        commit(self.root, LESSON)
        self.active(first)
        commit(self.root, LESSON)
        self.assertBlocked('Unarchived student revision')


    def refresh_fixture(self):
        source = self.root / 'source.txt'
        source.write_text('Return and table foundation.\nGraph interpretation.\nWeek 9 only.\n')
        c, review = quality.load(self.cpath), quality.load(self.rpath)
        c['source_inputs'][0]['sha256'] = quality.file_digest(source)
        save(self.cpath, c)
        save(self.rpath, {**review, 'contract_sha256': quality.file_digest(self.cpath)})
        commit(self.root, 'source.txt', CASE)
        first = self.draft()
        review_round(first)
        self.active(first)
        commit(self.root, CASE + '/rounds', LESSON, KEY)
        return first

    def refresh(self, first, *, graph='carry', criterion=False):
        up = self.root / CASE / 'refreshes/0001'
        old = quality.load(self.cpath)
        new = copy.deepcopy(old)
        new['source_inputs'][0]['sha256'] = quality.file_digest(self.root / 'source.txt')
        if criterion:
            item = next(t for t in new['topics'] if t['id'] == 'graph')
            item['minimum'] = 'Explain two axis labels on an unseen plot.'
            item['prerequisites'].append('return')
        save(up / 'contract.json', new)
        prior = {r.name: quality.file_digest(r) for r in (first.parent / 'reviews').iterdir()}
        review = {'schema_version': 1, 'stage': 'refresh', 'reviewer': 'independent refresh reviewer',
                  'previous_contract_sha256': quality.file_digest(self.cpath),
                  'contract_sha256': quality.file_digest(up / 'contract.json'),
                  'previous_review_sha256': quality.file_digest(self.rpath),
                  'after_round': 1, 'previous_round_sha256': quality.file_digest(first), 'prior_reviews': prior,
                  'finding': 'Compare the pinned source excerpts against the accepted material.',
                  'topics': {tid: {'decision': graph if tid == 'graph' else 'carry', 'finding': 'Review of the actual relevant excerpt.',
                                   'sources': {'0': [{'old_lines': [2, 2], 'new_lines': [2, 2]}] if tid == 'graph'
                                               else [{'old_lines': [1, 1], 'new_lines': [1, 1]}]}}
                             for tid in TOPICS}}
        save(up / 'review.json', review)
        return up

    def test_independently_reviewed_unrelated_week_edit_preserves_all_prior_material_judgments(self):
        first = self.refresh_fixture()
        source = self.root / 'source.txt'
        source.write_text(source.read_text().replace('Week 9 only.', 'Revised week 9 extension.'))
        self.assertBlocked('Source bytes differ')
        new = self.refresh(first)
        self.assertBlocked('Commit the reviewed source refresh')
        head = commit(self.root, 'source.txt', CASE + '/refreshes')
        result = self.result()
        self.assertTrue(result['ready'], result)
        self.assertEqual(result['basis_history'][-1]['anchor'], head)
        self.assertEqual(result['basis_history'][-1]['reopen'], [])
        self.assertEqual(result['history'][0]['round_sha256'], quality.file_digest(first))
        self.assertNotEqual(quality.file_digest(self.cpath), quality.file_digest(new / 'contract.json'))

    def test_a_changed_relevant_source_and_prerequisite_reopen_only_the_affected_target(self):
        first = self.refresh_fixture()
        p = self.root / 'source.txt'
        p.write_text(p.read_text().replace('Graph interpretation.', 'Interpret changed axes independently.'))
        new = self.refresh(first, graph='reopen', criterion=True)
        commit(self.root, 'source.txt', CASE + '/refreshes')
        self.assertBlocked('New depth basis')
        self.maps['graph']['prerequisite_uses']['return'] = 'graph-why'
        second = self.draft(2, ['graph'])
        self.assertBlocked('Foreign iteration contract')
        row = quality.load(second)
        row['contract_sha256'] = quality.file_digest(new / 'contract.json')
        save(second, row)
        self.active(second)
        self.assertEqual(self.result()['history'][-1]['required_topics'], ['graph'])
        review_round(second, ['graph'])
        self.assertTrue(self.result()['ready'])
        # Historical records still refer to the first basis.
        self.assertEqual(quality.load(first)['contract_sha256'], quality.file_digest(self.cpath))

    def test_changed_excerpts_cannot_be_declared_unchanged_and_late_refresh_cannot_bless_earlier_draft(self):
        first = self.refresh_fixture()
        p = self.root / 'source.txt'
        p.write_text(p.read_text().replace('Graph interpretation.', 'New compulsory graph reasoning.'))
        self.refresh(first)
        commit(self.root, 'source.txt', CASE + '/refreshes')
        self.assertBlocked('cannot be carried')

    def test_refreeze_must_precede_the_revised_draft_even_when_round_hashes_are_real(self):
        first = self.refresh_fixture()
        p = self.root / 'source.txt'
        p.write_text(p.read_text().replace('Graph interpretation.', 'New compulsory graph reasoning.'))
        self.nb['cells'][4]['source'] = ['New graph explanation.']
        self.draft(2)
        self.refresh(first, graph='reopen')
        commit(self.root, 'source.txt', CASE)
        self.assertBlocked('preceded refreshed')

    def test_unchanged_dispute_requires_neutral_evidence_pinned_to_this_receipt_and_round(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        review_round(first, ['graph'], reviewer='original adverse reader', verdict='uncertain', name='adverse.json')
        second = self.draft(2, ['graph'])
        self.active(second)
        review = review_round(second, ['graph'], reviewer='neutral adjudicator')
        judgment = quality.load(review)
        topic = judgment['topics']['graph']
        receipt = second.parent / 'counterevidence/cell-proof.json'
        evidence = {'contract_sha256': judgment['contract_sha256'], 'candidate_sha256': judgment['candidate_sha256'],
                    'round_sha256': judgment['round_sha256'], 'prior_reviews': quality.load(second)['prior_reviews'],
                    'topic': 'graph', 'cells': topic['cells'], 'reviewer': 'neutral adjudicator',
                    'finding': 'Separate independent solution to the disputed plot.'}
        save(receipt, {**evidence, 'reviewer': 'somebody else'})
        topic['counterevidence'] = {'path': receipt.relative_to(self.root).as_posix(), 'sha256': quality.file_digest(receipt)}
        save(review, judgment)
        self.assertBlocked('Foreign counterevidence')
        save(receipt, evidence)
        topic['counterevidence']['sha256'] = quality.file_digest(receipt)
        save(review, judgment)
        self.assertTrue(self.result()['ready'])
        copy = self.root / 'foreign.json'
        shutil.copyfile(receipt, copy)
        topic['counterevidence']['path'] = 'foreign.json'
        save(review, judgment)
        self.assertBlocked('this iteration archive')

    def test_separate_external_receipt_must_attest_exact_current_reviewer_and_verdicts(self):
        self.freeze()
        first = self.draft()
        self.active(first)
        review = review_round(first)
        row = quality.load(review)
        path = first.parent / 'external/model.json'
        save(path, {**row, 'reviewer': 'other reader'})
        row['external_receipt'] = {'path': path.relative_to(self.root).as_posix(), 'sha256': quality.file_digest(path)}
        save(review, row)
        self.assertBlocked('does not attest')
        save(path, {k: v for k, v in row.items() if k != 'external_receipt'})
        row['external_receipt']['sha256'] = quality.file_digest(path)
        save(review, row)
        self.assertTrue(self.result()['ready'])

    def test_duplicate_material_cannot_pad_iterations(self):
        self.freeze()
        first = self.draft()
        review_round(first)
        self.active(first)
        second = self.draft(2)
        review_round(second)
        self.assertBlocked('identical candidate')


    def test_unrelated_teacher_footnote_cannot_clear_a_prior_external_negative_finding(self):
        self.freeze()
        first = self.draft()
        self.active(first)
        review_round(first, ['return', 'table', 'reading'])
        review_round(first, ['graph'], reviewer='specialist', verdict='revise', name='adverse.json')
        second = self.draft(2)
        key = second.parent / 'key.md'
        key.write_text(key.read_text() + 'Unrelated teacher footnote.\n')
        row = quality.load(second)
        row['companions'][0]['sha256'] = quality.file_digest(key)
        save(second, row)
        review_round(second, reviewer='specialist')
        self.active(second)
        self.assertBlocked('unchanged adverse finding')

    def test_only_a_changed_cited_key_excerpt_can_resolve_its_adverse_judgment_and_old_ordinal_stays_historical(self):
        self.freeze()
        first = self.draft()
        key = first.parent / 'key.md'
        key.write_text('Answer: 9\nFootnote unchanged.\n')
        row = quality.load(first)
        row['companions'][0]['sha256'] = quality.file_digest(key)
        save(first, row)
        review_round(first, ['return', 'table', 'reading'])
        negative = review_round(first, ['graph'], reviewer='specialist', verdict='revise', name='adverse.json')
        r = quality.load(negative)
        r['topics']['graph']['companion_spans'] = [{'path': KEY, 'lines': [1, 1]}]
        save(negative, r)
        second = self.draft(2)
        key2 = second.parent / 'key.md'
        key2.write_text('Answer: 5\nFootnote unchanged.\n')
        row2 = quality.load(second)
        row2['companions'][0]['sha256'] = quality.file_digest(key2)
        save(second, row2)
        review_round(second, reviewer='specialist')
        self.active(second)
        self.assertTrue(self.result()['ready'])
        target = first.parent.relative_to(self.root).as_posix() + '/candidate.ipynb'
        old = depth.checked(self.root, CASE, target=target)
        self.assertEqual(old['subject_round'], 1)
        self.assertFalse(old['ready'])
        self.assertIn('Historical iteration', ' '.join(old['errors']))


class ExistingRevisionRoute(unittest.TestCase):
    def bind(self, fixture):
        fixture.bind()
        manifest = fixture.report.get('topic_depth', {}).get('manifest')
        if manifest:
            fixture.w['context']['inputs'].append(manifest)
            fixture.w['reviews'][-1]['context_fingerprint'] = workflow.context_fingerprint(fixture.w)
            save(fixture.root / 'workflow.json', fixture.w)

    def test_quality_lookup_cannot_hide_a_registered_entry_behind_a_symlink(self):
        fixture = revisions.NotebookRoute()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = fixture.root
        with patch.dict(depth.ACTIVE, {'draft.ipynb': CASE}, clear=True):
            start = initialize(root, 'draft.ipynb')
            create_freeze(root, start, 'draft.ipynb', ('quantity',), companions=())
            commit(root, CASE)
            moved = root / 'unguarded.ipynb'
            fixture.baseline.rename(moved)
            fixture.baseline.symlink_to(moved)
            report = quality.evaluate(fixture.bundle, root)
            self.assertEqual(report['artifact_path'], 'draft.ipynb')
            self.assertFalse(report['topic_depth']['ready'])
            self.assertIn('Symlink', ' '.join(report['topic_depth']['errors']))

    def test_depth_alone_drives_an_authorized_typed_repair_when_all_sixteen_checks_and_discovery_pass(self):
        fixture = revisions.NotebookRoute()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.f.compare(did='demand:denominator')
        root = fixture.root
        with patch.dict(depth.ACTIVE, {'draft.ipynb': CASE}, clear=True):
            start = initialize(root, 'draft.ipynb')
            create_freeze(root, start, 'draft.ipynb', ('quantity',), companions=())
            commit(root, CASE)
            registered = root / CASE / 'rounds/0001/candidate.ipynb'
            registered.parent.mkdir(parents=True)
            shutil.copyfile(fixture.baseline, registered)
            ids = [c['id'] for c in quality.load(registered)['cells']]
            maps = {'quantity': {'class': ids, 'homework': [], 'optional': [], 'prerequisite_uses': {},
                                 'support': ['redundant'], 'assessment': [ids[-1]],
                                 'minutes': {'class': 120, 'homework': 0, 'optional': 0}}}
            first = write_round(root, 1, None, maps, archive_key=False)
            self.bind(fixture)
            self.assertTrue(all(x['status'] == 'passed' for x in fixture.report['checks']))
            self.assertTrue(fixture.report['discovery']['ready_for_review'])
            self.assertEqual(fixture.plan['ranked'][0]['work_kind'], 'review_topic_depth')
            review_round(first, verdict='uncertain')
            self.bind(fixture)
            self.assertEqual(fixture.plan['ranked'][0]['work_kind'], 'resolve_topic_depth')
            extra = review_round(first, verdict='revise', reviewer='another reviewer', name='competing.json')
            self.bind(fixture)
            self.assertEqual(fixture.plan['ranked'][0]['work_kind'], 'adjudicate_topic_depth')
            extra.unlink()  # Uncommitted alternative test case.
            review_round(first, verdict='revise')
            self.bind(fixture)
            self.assertFalse(fixture.report['ready_for_review'])
            self.assertEqual(fixture.plan['reason'], 'scoped_topic_depth_work')
            decision = workflow.decide(fixture.w, fixture.report, repair_plan=fixture.plan)
            self.assertEqual(decision['reason'], 'scoped_repair_only')
            item = decision['candidate']
            self.assertEqual((item['id'], item['work_kind']), ('depth:quantity', 'revise_topic_depth'))
            stale = copy.deepcopy(fixture.w)
            stale['context']['inputs'] = [m for m in stale['context']['inputs'] if m['id'] != 'review:topic-depth']
            self.assertEqual(workflow.decide(stale, fixture.report, repair_plan=fixture.plan)['reason'],
                             'topic_depth_context_not_bound')
            self.assertEqual(workflow.decide(fixture.w, fixture.report)['reason'], 'topic_depth_review_required')
            intent = {'actions': [revisions.action('deepen', ['redundant'], ['redundant'], 'Repair the cited support.')],
                      'routes': {'quantity': {'before': ['redundant', ids[-1]], 'after': ['redundant', ids[-1]]}}}
            patch_data = {'author': 'fixture editor', 'work_key': item['key'], 'intent': intent,
                          'operations': [{'op': 'replace', 'id': 'redundant', 'source': 'Trace the eligible values before aggregation.'}]}
            output = CASE + '/rounds/0002/candidate.ipynb'
            (root / output).parent.mkdir()
            result = material_revision.run('apply', root, fixture.w, fixture.bundle, patch_data, output)
            self.assertEqual(result['status'], 'created')
            record = write_round(root, 2, None, maps, author='fixture editor', archive_key=False)
            review_round(record)
            # Verifying the original repair uses the subject of the selected historical baseline.
            # Appending the new candidate and its independent reviews does not change the first work key.
            self.bind(fixture)
            self.assertEqual(fixture.plan['ranked'][0]['key'], item['key'])
            self.assertTrue(depth.checked(root, CASE, target=output)['ready'])
            save(root / 'results.json', {'candidate_sha256': result['candidate_sha256'], 'cases': [
                {'id': 'mixed', 'input': [2, 4], 'expected': 3, 'actual': sum([2, 4])/2},
                {'id': 'zero', 'input': [0], 'expected': 0, 'actual': sum([0])}]})
            evidence = [{'path': 'results.json', 'sha256': quality.file_digest(root / 'results.json'),
                         'locator': 'cases', 'observation': 'Controlled input and boundary results.'}]
            checks = {key: {'status': 'passed', 'cells': ['redundant', ids[-1]],
                            'finding': 'Controlled independent review.', 'evidence': evidence}
                      for key in ('action:0', 'route:quantity', 'new_input', 'boundary', 'regression')}
            checks['new_input']['case_id'], checks['boundary']['case_id'] = 'mixed', 'zero'
            ordinary = {'reviewer': 'material verifier', 'candidate_sha256': result['candidate_sha256'],
                        'work_key': item['key'], 'checks': checks}
            save(root / 'depth-patch.json', patch_data)
            save(root / 'depth-material.json', ordinary)
            event = fixture.f.event('advance_lesson', revision='depth-corrected', workflow_path='workflow.json',
                                    quality_path='bundle.json', patch_path='depth-patch.json',
                                    review_path='depth-material.json', candidate_path=output)
            step = discovery_loop.step(fixture.f.state, event, root)
            self.assertEqual(step['events'][-1]['data']['verification']['candidate_sha256'], result['candidate_sha256'])

    def test_typed_edit_quality_decision_and_actual_discovery_advance_enforce_the_same_depth_judgment(self):
        fixture = revisions.NotebookRoute()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = fixture.root
        # This specimen uses an existing baseline; the production Week 1 entry uses a proven absent baseline.
        with patch.dict(depth.ACTIVE, {'draft.ipynb': CASE}, clear=True):
            (root / 'source.txt').rename(root / 'discovery-source.tmp')
            start = initialize(root, 'draft.ipynb')
            cpath, rpath = create_freeze(root, start, 'draft.ipynb', ('quantity',), companions=())
            # Keep the existing discovery receipt's original bytes and pin those same bytes for the topic contract.
            (root / 'discovery-source.tmp').replace(root / 'source.txt')
            contract = quality.load(cpath)
            contract['source_inputs'][0]['sha256'] = quality.file_digest(root / 'source.txt')
            save(cpath, contract)
            save(rpath, {**quality.load(rpath), 'contract_sha256': quality.file_digest(cpath)})
            self.bind(fixture)
            self.assertEqual(workflow.decide(fixture.w, fixture.report, repair_plan=fixture.plan)['reason'],
                             'topic_depth_freeze_required')
            commit(root, 'source.txt', CASE)
            out = CASE + '/rounds/0001/candidate.ipynb'
            (root / out).parent.mkdir(parents=True)
            self.bind(fixture)
            run = lambda mode, review=None: material_revision.run(mode, root, fixture.w, fixture.bundle,
                                                                  fixture.patch, out, review)
            built = run('apply')
            self.assertEqual(built['status'], 'created')
            with self.assertRaisesRegex(ValueError, 'registered iteration'):
                material_revision.run('apply', root, fixture.w, fixture.bundle, fixture.patch, 'unguarded.ipynb')
            ids = [c['id'] for c in quality.load(root / out)['cells']]
            maps = {'quantity': {'class': ids, 'homework': [], 'optional': [], 'prerequisite_uses': {},
                                 'support': [revisions.INTRO], 'assessment': [revisions.EXAMPLE],
                                 'minutes': {'class': 120, 'homework': 0, 'optional': 0}}}
            record = write_round(root, 1, None, maps, archive_key=False, author=fixture.patch['author'])
            cases = root / 'fixture-execution.json'
            save(cases, {'candidate_sha256': built['candidate_sha256'],
                         'cases': [{'id': 'first', 'input': [3, 5], 'expected': 4, 'actual': sum([3, 5])/2},
                                   {'id': 'boundary', 'input': [0], 'expected': 0, 'actual': sum([0])}]})
            evidence = [{'path': cases.name, 'sha256': quality.file_digest(cases), 'locator': 'cases',
                         'observation': 'Synthetic execution control.'}]
            required = {'route:' + key: val['after'] for key, val in fixture.intent['routes'].items()}
            required.update({'action:' + str(i): a['after'] or [revisions.EXAMPLE] for i, a in enumerate(fixture.intent['actions'])})
            required.update(new_input=[revisions.EXAMPLE], boundary=[revisions.EXAMPLE], regression=[revisions.AXES])
            checks = {key: {'status': 'passed', 'finding': 'Controlled existing revision check.', 'cells': locs,
                            'evidence': evidence} for key, locs in required.items()}
            checks['new_input']['case_id'], checks['boundary']['case_id'] = 'first', 'boundary'
            review = {'candidate_sha256': built['candidate_sha256'], 'reviewer': 'material reviewer',
                      'work_key': fixture.patch['work_key'], 'checks': checks}
            save(root / 'material-review.json', review)
            event = fixture.f.event('advance_lesson', revision='reviewed', workflow_path='workflow.json',
                                    quality_path='bundle.json', patch_path='patch.json', review_path='material-review.json',
                                    candidate_path=out)
            with self.assertRaisesRegex(ValueError, 'Topic depth review required'):
                discovery_loop.step(fixture.f.state, event, root)
            review_round(record)
            self.assertEqual(run('verify', review)['status'], 'reviewed_candidate')
            advanced = discovery_loop.step(fixture.f.state, event, root)
            self.assertIn('topic_depth', advanced['events'][-1]['data']['verification'])
            forged = copy.deepcopy(advanced['events'][-1])
            forged['data']['candidate_path'] = 'unregistered.ipynb'
            with self.assertRaisesRegex(ValueError, 'Registered advances'):
                discovery_loop.apply_event(discovery_loop.replay(fixture.f.state), forged, fixture.f.state['seed'])
            foreign = review_round(record, reviewer='new independent reviewer', verdict='uncertain', name='new.json')
            with self.assertRaisesRegex(ValueError, 'Topic depth review required'):
                discovery_loop.step(fixture.f.state, event, root)
            with self.assertRaisesRegex(ValueError, 'Topic depth review required'):
                discovery_loop.step(advanced, event, root)
            self.assertTrue(foreign.exists())


if __name__ == '__main__':
    unittest.main()
