"""Synthetic Git-backed matched-route cases, including a committed adverse judgment."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_topic_depth import (CASE, KEY, LESSON, commit, create_freeze, git, initialize, make_maps,
                              notebook, review_round, save, write_round)
import lesson_route as route
import quality

OLD = 'lessons/week01/old.ipynb'
CORE = 'lessons/week01/core.ipynb'
CORE_DATA = 'lessons/week01/tables.csv'
CORE_KEY = 'lessons/week01/core-key.md'
OLD_KEY = 'lessons/week01/old-key.md'
PLAN = 'curriculum/student-plan.html'
ROUTE, LEGACY = 'audit/route.json', 'audit/incumbent.json'
PROTOCOL, RESULTS = 'audit/protocol.json', 'audit/results.json'
INPUT, OUTPUT = 'audit/revealed/input.csv', 'audit/work/case.json'
CASES = ['F1', 'F2', 'F3', 'F4']


def cell(cid, content):
    return {'id': cid, 'cell_type': 'markdown', 'metadata': {}, 'source': content}


def unit(uid, path, cells, status, cls=0, hw=0):
    return {'id': uid, 'path': path, 'cells': cells, 'status': status, 'reason': 'After a failed tracing exercise.'
            if status == 'conditional' else 'Task placement used by this fixture.',
            'class_minutes': cls, 'homework_minutes': hw, 'class_range': [cls, cls], 'homework_range': [hw, hw]}


class LessonRoute(unittest.TestCase):
    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def hashes(self, names):
        return {p: quality.file_digest(self.root / p) for p in names}

    def set_plan(self, entry, decoy=None):
        link = '../' + entry
        row = ('<tr id="week-1" data-theory-minutes="20" data-noncoding-minutes="20" '
               'data-coding-minutes="80" data-self-min-hours="5" data-self-max-hours="7">')
        if decoy:
            row += f'<td><a href="{link}">Reference</a></td>'
            link = decoy
        self.put(PLAN, f'<table>{row}<td><a href="{link}">Open the lesson</a></td></tr></table>')
        save(self.root / quality.CONTRACT, {'baseline': {'path': PLAN, 'sha256': self.hashes([PLAN])[PLAN]},
                                           'class_minutes': 120, 'weeks': [{'week': 1, 'required_self_study_hours': [5, 7]}]})

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.start = initialize(self.root)
        old = {'nbformat': 4, 'cells': [cell('original', 'Read and predict the count.')]}
        save(self.root / OLD, old)
        self.put(OLD_KEY, 'Instructor explanation.\n')
        self.set_plan(OLD)
        base = commit(self.root, 'lessons', 'curriculum')
        legacy = {'schema_version': 1, 'id': 'old', 'entry': OLD, 'basis_commit': base,
                  'files': self.hashes([OLD, OLD_KEY]), 'units': [unit('old', OLD, ['original'], 'required')],
                  'companions': {OLD: {'teacher': [OLD_KEY], 'data': []}}, 'links': [],
                  'timing': 'Historical range estimated. Combined work unmeasured.'}
        save(self.root / LEGACY, legacy)
        self.set_plan(LESSON)
        self.sealed = 'new_group,count\nA,2\n'
        self.protocol = {'schema_version': 1, 'id': 'matched', 'maker': 'independent protocol writer',
                         'case_ids': CASES, 'inputs': {INPUT: hashlib.sha256(self.sealed.encode()).hexdigest()},
                         'required_cases': CASES, 'replacement_rule': 'matched-giwt-v1',
                         'candidate_before_revision': {'commit': self.start, 'sha256': None}}
        save(self.root / PROTOCOL, self.protocol)
        create_freeze(self.root, self.start)
        self.freeze = commit(self.root, CASE, 'curriculum', PROTOCOL)
        candidate = notebook()
        href = 'core.ipynb#practise'
        for i in (0, 2):
            candidate['cells'][i]['source'] = [f'Read [the actual practice]({href}).']
        active = write_round(self.root, 1, candidate, make_maps())
        review_round(active)
        shutil.copyfile(active.parent / 'candidate.ipynb', self.root / LESSON)
        shutil.copyfile(active.parent / 'key.md', self.root / KEY)
        save(self.root / CORE, {'nbformat': 4, 'cells': [cell('title', '# Title'),
             cell('try', '<a name="practise"></a>\n\nChoose the group and test it.'),
             cell('remedy', 'Retry the tracing exercise.'), cell('later', 'Future model evaluation.')]})
        self.put(CORE_DATA, 'group,count\nB,3\n')
        self.put(CORE_KEY, 'Teacher calculations.\n')
        self.put(INPUT, self.sealed)
        save(self.root / OUTPUT, {'case': 'F1', 'count': 2})
        ids = [c['id'] for c in candidate['cells']]
        self.route = {'schema_version': 1, 'id': 'new', 'entry': LESSON, 'depth': {'case': CASE, 'round': 1},
                      'files': self.hashes([LESSON, KEY, CORE, CORE_DATA, CORE_KEY]),
                      'units': [unit('book', LESSON, ids, 'required', 120),
                                unit('practice', CORE, ['try'], 'required', hw=330),
                                unit('retry', CORE, ['remedy'], 'conditional', hw=40),
                                unit('future', CORE, ['later'], 'deferred')],
                      'companions': {LESSON: {'teacher': [KEY], 'data': []},
                                     CORE: {'teacher': [CORE_KEY], 'data': [CORE_DATA]}},
                      'links': [{'from': 'book', 'cell': ids[i], 'to': 'practice', 'href': href} for i in (0, 2)]}
        save(self.root / ROUTE, self.route)
        report, _, _ = route.inspect_route(self.root, ROUTE)
        self.result = {'schema_version': 1, 'freeze_commit': self.freeze, 'depth_sha256': report['depth_sha256'],
                       'decision': 'replace', 'finding': 'Compare the matched independent judgments.'}
        self.result.update({s: {'path': p, 'sha256': self.hashes([p])[p]}
                            for s, p in [('candidate', ROUTE), ('incumbent', LEGACY), ('protocol', PROTOCOL)]})
        self.readers = {}
        for name, labels in [('one', {'candidate': 'B', 'incumbent': 'A'}), ('two', {'candidate': 'A', 'incumbent': 'B'})]:
            checks = {v: dict.fromkeys(route.CHECKS, True) for v in labels.values()}
            original = {'reviewer': name, 'protocol_sha256': self.result['protocol']['sha256'],
                        'depth_sha256': self.result['depth_sha256'], 'checks': checks,
                        'subjects': {v: self.result[s]['sha256'] for s, v in labels.items()}, 'cases': {}}
            for i, cid in enumerate(CASES):
                row = {}
                for side, key in labels.items():
                    bits = dict.fromkeys(route.BITS, 1)
                    if i == 3:
                        bits['T'] = 0
                    if side == 'incumbent' and i < 2:
                        bits['G'] = 0
                    row[key] = {'bits': bits, 'fatal': False, 'verdict': 'pass' if all(bits.values()) else 'revise',
                                'cells': {'practice': ['try']} if side == 'candidate' else {'old': ['original']},
                                'finding': 'The required new example asks students to choose a group.'}
                if i == 0:
                    row['outputs'] = self.hashes([OUTPUT])
                original['cases'][cid] = row
            self.readers[name] = (original, labels)
        self.save_assessments()

    def save_assessments(self):
        paths = []
        for name, (original, labels) in self.readers.items():
            original_path = 'audit/originals/' + name + '.json'
            path = 'audit/assessments/' + name + '.json'
            save(self.root / original_path, {'route_evidence': original})
            save(self.root / path, {'schema_version': 1, 'reviewer': name, 'labels': labels,
                                    'original': {'path': original_path, 'sha256': self.hashes([original_path])[original_path]}})
            paths.append(path)
        self.result['assessments'] = self.hashes(paths)
        save(self.root / RESULTS, self.result)

    def check(self):
        return route.compare(self.root, ROUTE, LEGACY, PROTOCOL, RESULTS)

    def test_normal_entry_matches_named_ordinal_and_paired_rule_with_one_partial(self):
        script = Path(route.__file__)
        proc = subprocess.run([sys.executable, '-B', str(script), 'check', '--root', str(self.root), '--route', ROUTE,
                               '--incumbent', LEGACY, '--protocol', PROTOCOL, '--results', RESULTS], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(report['matched_rule_result']['scores'], {'F1': 4, 'F2': 4, 'F3': 4, 'F4': 3})
        self.assertEqual(report['candidate']['minutes']['homework'], {'required': 330, 'conditional': 40, 'deferred': 0})
        self.assertEqual(report['unit_coverage']['candidate']['retry'], 'uncited')
        self.assertEqual(report['case_states']['F4']['candidate'], 'revise')
        self.route['depth']['round'] = 2
        save(self.root / ROUTE, self.route)
        with self.assertRaisesRegex(ValueError, 'ordinal'):
            route.inspect_route(self.root, ROUTE)

    def test_cannot_gain_an_unlinked_section_or_an_optional_only_path(self):
        units, books, owners = route.study_units(self.root, self.route, None)
        source = books[LESSON]['return-why']
        for decoration in ('`[read](core.ipynb#practise)`', '~~~\n[read](core.ipynb#practise)\n~~~',
                           '<!-- [read](core.ipynb#practise) -->', '![image](core.ipynb#practise)',
                           '<a href="core.ipynb#practise"></a>'):
            source['source'] = decoration
            with self.subTest(decoration=decoration), self.assertRaisesRegex(ValueError, 'visible student link'):
                route.route_links(self.route, units, books, owners)
        source['source'] = '[read](core.ipynb#wrong)'
        self.route['links'][0]['href'] = 'core.ipynb#wrong'
        with self.assertRaisesRegex(ValueError, 'misses the declared section'):
            route.route_links(self.route, units, books, owners)
        source['source'] = '[read](other.ipynb#practise)'
        self.route['links'][0]['href'] = 'other.ipynb#practise'
        with self.assertRaisesRegex(ValueError, 'different notebook'):
            route.route_links(self.route, units, books, owners)
        self.route['links'] = []
        with self.assertRaisesRegex(ValueError, 'Unreachable'):
            route.route_links(self.route, units, books, owners)
        self.set_plan(LESSON, decoy='../elsewhere.ipynb')
        with self.assertRaisesRegex(ValueError, 'material column'):
            route.inspect_route(self.root, ROUTE)

    def test_historical_plan_and_students_come_from_git_even_when_live_paths_change(self):
        (self.root / OLD_KEY).unlink()
        save(self.root / OLD, {'nbformat': 4, 'cells': [cell('new', 'Reused live name.')]})
        report, units, _ = route.inspect_route(self.root, LEGACY, incumbent=True)
        self.assertEqual(units['old']['cells'], ['original'])
        self.assertIn('archived plan', report['normal_entry']['basis'])
        self.assertEqual(self.check()['status'], 'comparison_recorded')

    def test_legacy_remote_link_checks_repository_path_and_known_ref(self):
        git(self.root, 'remote', 'add', 'origin', 'https://github.com/example/school.git')
        prefix = 'https://github.com/example/school/blob/'
        old = quality.load(self.root / LEGACY)
        for url, valid in [(prefix + 'retired-course-branch/' + OLD, True),
                           ('https://github.com/another/school/blob/main/' + OLD, False),
                           (prefix + 'retired-course-branch/elsewhere.ipynb', False),
                           (prefix + self.start + '/' + OLD, False)]:
            self.set_plan(OLD, decoy=url)
            old['basis_commit'] = commit(self.root, 'curriculum')
            save(self.root / LEGACY, old)
            with self.subTest(url=url):
                if valid:
                    report = route.inspect_route(self.root, LEGACY, incumbent=True)[0]
                    self.assertIn('old named branch unavailable', report['normal_entry']['basis'])
                else:
                    with self.assertRaisesRegex(ValueError, 'material column'):
                        route.inspect_route(self.root, LEGACY, incumbent=True)

    def test_required_work_cannot_depend_on_a_conditional_jump(self):
        units, books, owners = route.study_units(self.root, self.route, None)
        # The required later unit is reachable only through this conditional landing.
        units['practice']['status'] = 'conditional'
        units['retry']['status'] = 'required'
        with self.assertRaisesRegex(ValueError, 'Unreachable required units: retry'):
            route.route_links(self.route, units, books, owners)

    def test_changed_data_and_duplicate_or_false_minutes_block_the_route(self):
        original = (self.root / CORE_DATA).read_text()
        self.put(CORE_DATA, 'group,count\nC,100\n')
        with self.assertRaisesRegex(ValueError, 'stale route file'):
            route.inspect_route(self.root, ROUTE)
        self.put(CORE_DATA, original)
        bad = copy.deepcopy(self.route)
        bad['units'][1]['cells'].append('remedy')
        save(self.root / ROUTE, bad)
        with self.assertRaisesRegex(ValueError, 'Multiply allocated'):
            route.inspect_route(self.root, ROUTE)
        self.route['units'][0].update(class_minutes=110, class_range=[110, 110])
        self.route['units'][1].update(class_minutes=10, class_range=[10, 10])
        save(self.root / ROUTE, self.route)
        with self.assertRaisesRegex(ValueError, 'Entry class allocation'):
            route.inspect_route(self.root, ROUTE)

    def test_entry_total_cannot_hide_a_swap_between_reviewed_topics(self):
        book = self.route['units'][0]
        remaining = book['cells'][2:]
        book.update(cells=book['cells'][:2], class_minutes=10, class_range=[10, 10])
        self.route['units'].append(unit('other', LESSON, remaining, 'required', cls=110))
        self.route['links'][1]['from'] = 'other'
        save(self.root / ROUTE, self.route)
        with self.assertRaisesRegex(ValueError, 'reviewed class cells'):
            route.inspect_route(self.root, ROUTE)

    def test_branch_overrun_and_delayed_feedback_are_visible(self):
        self.route['units'][2]['homework_range'] = [20, 100]
        save(self.root / ROUTE, self.route)
        with self.assertRaisesRegex(ValueError, 'workload overrun'):
            route.inspect_route(self.root, ROUTE)
        self.route['overrun'] = 'When remediation is needed the upper estimate reaches 430 minutes.'
        save(self.root / ROUTE, self.route)
        self.assertEqual(route.inspect_route(self.root, ROUTE)[0]['budget'], 'overrun')
        roles = self.route['companions'][CORE]
        roles['after_attempt'], roles['data'] = roles['data'], []
        save(self.root / ROUTE, self.route)
        with self.assertRaisesRegex(ValueError, 'delayed feedback'):
            route.inspect_route(self.root, ROUTE)

    def test_earlier_eval_relabelled_subject_old_holdout_or_output_cannot_carry(self):
        self.put(INPUT, 'different\n')
        with self.assertRaisesRegex(ValueError, 'frozen evaluation input'):
            self.check()
        self.put(INPUT, self.sealed)
        before = (self.root / OUTPUT).read_bytes()
        self.put(OUTPUT, '{}')
        with self.assertRaisesRegex(ValueError, 'case output'):
            self.check()
        (self.root / OUTPUT).write_bytes(before)
        self.readers['one'][0]['depth_sha256'] = '0' * 64
        self.save_assessments()
        with self.assertRaisesRegex(ValueError, 'older evaluation or depth criteria'):
            self.check()
        self.readers['one'][0]['depth_sha256'] = self.result['depth_sha256']
        self.readers['one'][1].update(candidate='A', incumbent='B')
        self.save_assessments()
        with self.assertRaisesRegex(ValueError, 'blind subject'):
            self.check()

    def test_adverse_original_blocks_replacement_and_survives_selective_omission(self):
        forced = self.readers['one'][0]['cases']['F1']['B']
        forced.update(verdict='revise', fatal=True, finding='The joined table counts the same student twice.')
        forced['bits']['T'] = 0
        self.save_assessments()
        report = self.check()
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['case_states']['F1']['candidate'], 'conflict')
        self.result['decision'] = 'retain'
        self.save_assessments()
        self.assertEqual(self.check()['status'], 'comparison_recorded')
        commit(self.root, 'audit')
        receipt = 'audit/assessments/one.json'
        del self.result['assessments'][receipt]
        save(self.root / RESULTS, self.result)
        with self.assertRaisesRegex(ValueError, 'every independent assessment'):
            self.check()
        (self.root / receipt).unlink()
        with self.assertRaisesRegex(ValueError, 'removed or rewritten'):
            self.check()

    def test_uncertain_and_missing_cases_and_unsafe_checks_never_promote(self):
        for name, (original, labels) in self.readers.items():
            original['cases']['F1'][labels['candidate']]['bits']['W'] = '?'
            original['cases']['F1'][labels['candidate']]['verdict'] = 'uncertain'
            original['checks'][labels['candidate']]['execution'] = False
        self.save_assessments()
        report = self.check()
        self.assertEqual(report['status'], 'blocked')
        self.assertEqual(report['case_states']['F1']['candidate'], 'uncertain')
        self.assertTrue(any('execution' in e for e in report['errors']))
        self.result['decision'] = 'hold'
        del self.readers['one'][0]['cases']['F4']
        self.save_assessments()
        report = self.check()
        self.assertEqual(report['case_states']['F4']['candidate'], 'pending')
        self.assertEqual(report['status'], 'blocked')

    def test_a_required_case_cannot_silently_borrow_conditional_only_evidence(self):
        for original, labels in self.readers.values():
            original['cases']['F1'][labels['candidate']]['cells'] = {'retry': ['remedy']}
        self.save_assessments()
        report = self.check()
        self.assertEqual(report['status'], 'blocked')
        self.assertNotIn('F1', report['eligible_cases'])
        self.assertTrue(any('conditional support' in v for v in report['errors']))

    def test_shared_blind_digest_binds_workload_and_later_disclosed_packet(self):
        evidence, workload, packet = 'audit/comparison/evidence.json', 'audit/workload.json', 'audit/packet.txt'
        save(self.root / workload, {'estimate': 370})
        commit(self.root, workload)
        save(self.root / workload, {'estimate': 410})
        packet_bytes = b'blinded display transcript'
        index = {'schema_version': 1, 'files': {**self.hashes([workload]), packet: hashlib.sha256(packet_bytes).hexdigest()}}
        save(self.root / evidence, index)
        anchor = commit(self.root, evidence, workload)
        (self.root / packet).write_bytes(packet_bytes)
        digest = self.hashes([evidence])[evidence]
        self.result['evidence'] = {'path': evidence, 'sha256': digest}
        for original, _ in self.readers.values():
            original['evidence_sha256'] = digest
        self.save_assessments()
        self.assertEqual(self.check()['evidence_commit'], anchor)
        del self.result['evidence']
        self.save_assessments()
        with self.assertRaisesRegex(ValueError, 'shared reader evidence'):
            self.check()
        self.result['evidence'] = {'path': evidence, 'sha256': digest}
        self.save_assessments()
        self.put(packet, 'wrong blind display')
        with self.assertRaisesRegex(ValueError, 'stale shared comparison evidence'):
            self.check()

    def test_frozen_allocation_cannot_be_swapped_after_blind_judgments(self):
        path = 'audit/comparison/assignment.json'
        assignment = {'A': 'incumbent', 'B': 'candidate', 'salt': 'synthetic only',
                      'order': {'one': ['B', 'A'], 'two': ['A', 'B']}}
        save(self.root / path, assignment)
        digest = self.hashes([path])[path]
        labels, orders, _ = route.disclosed_allocation(self.root, self.root / RESULTS, self.result, digest)
        context = {s: self.result[s]['sha256'] for s in ('candidate', 'incumbent', 'protocol')}
        context['depth'] = self.result['depth_sha256']
        route.reviewer_cases(self.root, 'audit/assessments/one.json', context, True, labels, orders)
        with self.assertRaisesRegex(ValueError, 'frozen label or reader'):
            route.reviewer_cases(self.root, 'audit/assessments/two.json', context, True, labels, orders)
        assignment['A'], assignment['B'] = assignment['B'], assignment['A']
        save(self.root / path, assignment)
        with self.assertRaisesRegex(ValueError, 'stale blind assignment'):
            route.disclosed_allocation(self.root, self.root / RESULTS, self.result, digest)

    def test_limited_pilot_can_name_agreed_bits_in_a_partial_case(self):
        self.result.update(decision='pilot', pilot_cases=['F4'], pilot_bits={'F4': ['G', 'I']})
        self.save_assessments()
        self.assertEqual(self.check()['status'], 'comparison_recorded')
        self.result['pilot_bits']['F4'].append('T')
        self.save_assessments()
        self.assertEqual(self.check()['status'], 'blocked')

    def test_a_late_freeze_cannot_relabel_already_committed_student_changes(self):
        self.result['freeze_commit'] = commit(self.root, CORE)
        save(self.root / RESULTS, self.result)
        with self.assertRaisesRegex(ValueError, 'changed before protocol freeze'):
            self.check()

    def test_only_assigned_student_cells_can_support_an_independent_judgment(self):
        side = self.readers['two'][0]['cases']['F2']['A']
        for cells, error in [({'future': ['later']}, 'deferred evidence'),
                             ({'book': ['try']}, 'outside the assigned unit'), ({}, 'requires actual student cells')]:
            side['cells'] = cells
            self.save_assessments()
            with self.subTest(cells=cells), self.assertRaisesRegex(ValueError, error):
                self.check()


if __name__ == '__main__':
    unittest.main()
