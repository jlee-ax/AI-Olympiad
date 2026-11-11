"""Preserving source worktrees while combining current tools/specs with a lesson."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import lesson_validation as validation


class LessonValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tools = self.root / 'tool-input'
        self.lesson = self.root / 'lesson-input'
        self.output = self.root / 'output'
        for base, directories in ((self.tools, validation.TOOL_DIRS), (self.lesson, validation.LESSON_DIRS)):
            for name in directories:
                (base / name).mkdir(parents=True)
                (base / name / 'fixture.txt').write_text('Tool bytes' if base == self.tools else 'Lesson bytes')
        (self.lesson / 'lessons/lesson.txt').write_text('Student content.')
        bundle = self.lesson / 'reviews/week01/final-followup/quality.json'
        bundle.parent.mkdir(parents=True)
        bundle.write_text(json.dumps({'artifact': {'path': 'lessons/lesson.txt', 'sha256': '0' * 64}, 'units': [], 'operator_notes': {}}))

    def prepare(self):
        return validation.prepare(self.tools, self.lesson, self.output)

    def execution_fixture(self):
        book = self.lesson / 'lessons/week01/week01_python_tables.ipynb'
        book.parent.mkdir(parents=True, exist_ok=True)
        book.write_text(json.dumps({'cells': [{'id': 'code', 'cell_type': 'code', 'source': 'pass'}]}))
        bundle_path = self.lesson / 'reviews/week01/final-followup/quality.json'
        bundle = json.loads(bundle_path.read_text())
        bundle['artifact']['path'] = str(book.relative_to(self.lesson))
        bundle['units'] = [{'id': 'unit', 'execution': {'status': 'not_run'}}]
        bundle['reviews'] = [{'id': 'historical-review', 'status': 'passed'}]
        bundle_path.write_text(json.dumps(bundle))

    def run_execution(self, mutate_receipt=None, after_command=None):
        manifest = self.prepare()
        scripts = []
        def subprocess_run(argv, **kwargs):
            script = argv[2]
            scripts.append(script)
            book = self.output / 'lessons/week01/week01_python_tables.ipynb'
            receipt_path = book.parent / 'validation.json'
            if script == 'lessons/week01/validate_week01.py':
                notebook = json.loads(book.read_text())
                notebook['cells'][0].update(execution_count=1, outputs=[{'output_type': 'stream', 'text': 'ran'}])
                book.write_text(json.dumps(notebook))
                candidate = {
                    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
                    'execution_method': 'fresh IPython InProcessKernelManager per run',
                    'notebook_sha256': validation.sha(book),
                    'code_cells': 1, 'executed_code_cells': 1, 'error_outputs': 0,
                    'source_projection_unchanged_by_execution': True,
                    'student_answers': 'blank_not_assessed', 'student_mastery': 'not_observed',
                }
                for field in ('nbformat_validation', 'top_to_bottom_execution', 'actual_function_and_state_assertions',
                              'teacher_modification_key_tests', 'independent_fraction_arithmetic',
                              'csv_mask_shape_missing_and_merge_checks', 'standalone_without_csv_files'):
                    candidate[field] = 'passed'
                if mutate_receipt:
                    mutate_receipt(candidate, book)
                receipt_path.write_text(json.dumps(candidate))
            if after_command:
                after_command(script, argv, book, receipt_path)
            return subprocess.CompletedProcess(argv, 0, '{}', '')
        with patch.object(subprocess, 'run', side_effect=subprocess_run):
            report = validation.run(self.output, execute=True)
        self.assertEqual(validation.check_inputs(manifest), [])
        return report, scripts

    def test_prepare_exact_copy_and_read_only_input_run(self):
        manifest = self.prepare()
        self.assertEqual(validation.check_inputs(manifest), [])
        self.assertEqual((self.output / 'tools/fixture.txt').read_bytes(), (self.tools / 'tools/fixture.txt').read_bytes())
        self.assertFalse((self.output / '.git').exists())
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{"status":"uncertain"}', '')):
            report = validation.run(self.output, execute=False)
        self.assertEqual(report['status'], 'passed')
        self.assertIsNone(report['execution'])
        self.assertEqual(validation.check_inputs(manifest), [])
        current = json.loads((self.output / 'validation-current/quality.json').read_text())
        self.assertEqual(current['artifact']['sha256'], validation.sha(self.output / 'lessons/lesson.txt'))
        self.assertEqual(current['units'], [])

    def test_existing_or_inside_output_never_overwritten(self):
        self.output.mkdir()
        keep = self.output / 'keep.txt'; keep.write_text('Keep')
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(keep.read_text(), 'Keep')
        with self.assertRaises(ValueError): validation.prepare(self.tools, self.lesson, self.lesson / 'output')
        self.assertFalse((self.lesson / 'output').exists())

    def test_symlink_and_missing_layer_rejected_before_copy(self):
        link = self.tools / 'tools/link'; link.symlink_to(self.lesson / 'lessons/lesson.txt')
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())
        link.unlink()
        (self.tools / 'tests/fixture.txt').unlink(); (self.tools / 'tests').rmdir()
        with self.assertRaises(ValueError): self.prepare()
        self.assertFalse(self.output.exists())

    def test_changed_missing_and_new_input_file_require_fresh_copy(self):
        manifest = self.prepare()
        path = self.lesson / 'lessons/lesson.txt'
        path.write_text('User changed data.')
        self.assertIn('lesson:lessons/lesson.txt', validation.check_inputs(manifest))
        with self.assertRaises(ValueError): validation.run(self.output)
        self.assertEqual(path.read_text(), 'User changed data.')
        path.unlink()
        self.assertIn('lesson:lessons/lesson.txt', validation.check_inputs(manifest))
        (self.tools / 'tools/new.txt').write_text('New tool')
        self.assertIn('tool:added:tools/new.txt', validation.check_inputs(manifest))

    def test_tampered_copy_is_not_executed(self):
        self.prepare()
        (self.output / 'tools/fixture.txt').write_text('Different tool')
        with patch.object(subprocess, 'run') as run:
            with self.assertRaises(ValueError): validation.run(self.output)
            run.assert_not_called()

    def test_zero_exit_with_only_old_execution_receipt_is_not_promoted(self):
        self.execution_fixture()
        book = self.lesson / 'lessons/week01/week01_python_tables.ipynb'
        (book.parent / 'validation.json').write_text(json.dumps({'checked_at_utc': '2000-01-01T00:00:00Z'}))
        self.prepare()
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '{}', '')) as commands:
            report = validation.run(self.output, execute=True)
        self.assertIn('lessons/week01/validate_week01.py', [call.args[0][2] for call in commands.call_args_list])
        self.assertEqual(report['status'], 'failed')
        self.assertIsNone(report['execution'])
        self.assertTrue(report['execution_errors'])
        self.assertTrue((book.parent / 'validation.json').exists())
        self.assertFalse((self.output / 'lessons/week01/validation.json').exists())
        current = json.loads((self.output / 'validation-current/quality.json').read_text())
        self.assertEqual(current['units'][0]['execution']['status'], 'not_run')

    def test_current_receipt_and_output_only_execution_are_accepted(self):
        self.execution_fixture()
        report, scripts = self.run_execution()
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['execution_errors'], [])
        self.assertEqual(report['unexpected_copy_changes'], [])
        self.assertEqual(scripts.index('reviews/week01/contest-depth/check_depth.py'),
                         scripts.index('lessons/week01/validate_week01.py') + 1)
        current = json.loads((self.output / 'validation-current/quality.json').read_text())
        execution = current['units'][0]['execution']
        self.assertEqual(execution['status'], 'passed')
        self.assertEqual(execution['artifact_sha256'], report['execution']['notebook_sha256'])
        self.assertIsInstance(execution['command'], str)
        self.assertIn('validate_week01.py --inprocess', execution['command'])
        self.assertEqual(current['reviews'], [{'id': 'historical-review', 'status': 'passed'}])
        self.assertEqual(json.loads((self.output / 'validation-current/run.json').read_text()), report)

    def test_invalid_fresh_receipt_fields_are_not_promoted(self):
        self.execution_fixture()
        cases = [
            ('notebook_sha256', '0' * 64),
            ('code_cells', 0), ('executed_code_cells', 0), ('error_outputs', 1),
            ('code_cells', True), ('executed_code_cells', True), ('error_outputs', False),
            ('source_projection_unchanged_by_execution', False),
            ('student_answers', 'filled'), ('student_mastery', 'observed'),
            ('execution_method', ''), ('execution_method', 'reused kernel'),
            ('execution_method', None),
            ('checked_at_utc', '2000-01-01T00:00:00+00:00'),
            ('checked_at_utc', (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()),
            ('checked_at_utc', datetime.now().isoformat()),
            ('checked_at_utc', 'invalid timestamp'),
        ]
        cases.extend((field, 'failed') for field in (
            'nbformat_validation', 'top_to_bottom_execution', 'actual_function_and_state_assertions',
            'teacher_modification_key_tests', 'independent_fraction_arithmetic',
            'csv_mask_shape_missing_and_merge_checks', 'standalone_without_csv_files'))
        for index, (field, value) in enumerate(cases):
            self.output = self.root / ('invalid-receipt-' + str(index))
            with self.subTest(field=field, value=value):
                report, _ = self.run_execution(lambda candidate, book: candidate.update({field: value}))
                self.assertEqual(report['status'], 'failed')
                self.assertIsNone(report['execution'])
                self.assertTrue(report['execution_errors'])
                current = json.loads((self.output / 'validation-current/quality.json').read_text())
                self.assertEqual(current['units'][0]['execution']['status'], 'not_run')

    def test_source_edit_is_rejected_even_with_matching_receipt_hash(self):
        self.execution_fixture()
        def edit_source(candidate, book):
            notebook = json.loads(book.read_text())
            notebook['cells'][0]['source'] = 'changed source'
            book.write_text(json.dumps(notebook))
            candidate['notebook_sha256'] = validation.sha(book)
        report, _ = self.run_execution(edit_source)
        self.assertEqual(report['status'], 'failed')
        self.assertIsNone(report['execution'])
        self.assertTrue(report['execution_errors'])

    def test_runtime_protected_copy_changes_are_reported(self):
        cases = (('tools/fixture.txt', False), ('skills/fixture.txt', False), ('reviews/fixture.txt', False),
                 ('tools/new_tool.py', True), ('skills/new_spec.json', True))
        for index, (relative, added) in enumerate(cases):
            self.output = self.root / ('runtime-copy-change-' + str(index))
            manifest = self.prepare()
            def subprocess_run(argv, **kwargs):
                if argv[2] == 'tools/quality.py' and 'validation-current/quality.json' in str(argv):
                    (self.output / relative).write_text('runtime tampering')
                return subprocess.CompletedProcess(argv, 0, '{}', '')
            with self.subTest(path=relative), patch.object(subprocess, 'run', side_effect=subprocess_run):
                report = validation.run(self.output)
                self.assertEqual(report['status'], 'failed')
                self.assertIn(('added:' if added else '') + relative, report['unexpected_copy_changes'])
                self.assertEqual(validation.check_inputs(manifest), [])

    def test_late_execution_artifact_or_receipt_edit_cannot_pass(self):
        self.execution_fixture()
        for index, (stage, target) in enumerate((('depth', 'notebook'), ('depth', 'receipt'),
                                                  ('quality', 'notebook'), ('quality', 'receipt'))):
            self.output = self.root / ('late-change-' + str(index))
            def after_command(script, argv, book, receipt):
                matching = (script == 'reviews/week01/contest-depth/check_depth.py' if stage == 'depth' else
                            script == 'tools/quality.py' and 'validation-current/quality.json' in str(argv))
                if matching:
                    path = book if target == 'notebook' else receipt
                    data = json.loads(path.read_text())
                    if target == 'notebook':
                        data['cells'][0]['source'] = 'edited after validation'
                    else:
                        data['student_mastery'] = 'observed'
                    path.write_text(json.dumps(data))
            with self.subTest(stage=stage, target=target):
                report, _ = self.run_execution(after_command=after_command)
                self.assertEqual(report['status'], 'failed')
                self.assertTrue(report['execution_errors'])

    def test_execution_receipt_cannot_bind_another_bundle_artifact(self):
        self.execution_fixture()
        bundle_path = self.lesson / 'reviews/week01/final-followup/quality.json'
        bundle = json.loads(bundle_path.read_text())
        bundle['artifact']['path'] = 'lessons/lesson.txt'
        bundle_path.write_text(json.dumps(bundle))
        report, _ = self.run_execution()
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(report['execution_errors'])
        current = json.loads((self.output / 'validation-current/quality.json').read_text())
        self.assertEqual(current['units'][0]['execution']['status'], 'not_run')

    def test_source_root_cannot_be_run(self):
        with self.assertRaises(FileNotFoundError): validation.run(self.lesson)


if __name__ == '__main__': unittest.main()
