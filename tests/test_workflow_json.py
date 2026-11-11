"""Functional regressions for the standalone workflow CLI's JSON boundary."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import workflow

COMMANDS = ('validate', 'fingerprint', 'recall', 'decide')


class WorkflowJsonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = json.loads((ROOT / 'examples/workflow.json').read_text(encoding='utf-8'))
        cls.encoded = json.dumps(cls.state)

    def run_cli(self, command, source, text=None):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'tools/workflow.py'), command, str(source)],
                              input=text, capture_output=True, text=True, check=False)

    def assert_rejected(self, text, error_fragment):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            path.write_text(text, encoding='utf-8')
            before = path.read_bytes()
            for command in COMMANDS:
                for source in ('stdin', 'file'):
                    with self.subTest(command=command, source=source):
                        run = self.run_cli(command, '/dev/stdin' if source == 'stdin' else path,
                                           text if source == 'stdin' else None)
                        self.assertEqual(run.returncode, 2, run.stderr)
                        self.assertEqual(run.stderr, '')
                        output = json.loads(run.stdout)
                        self.assertEqual(output['status'], 'blocked')
                        self.assertEqual(output['reason'], 'unreadable_state')
                        self.assertEqual(output['authority'], 'advisory_only')
                        self.assertIn(error_fragment, output['errors'][0])
                        self.assertNotIn('context_fingerprint', output)
                        self.assertNotIn('records', output)
                        self.assertEqual(path.read_bytes(), before)

    def test_all_commands_reject_duplicate_keys_in_files_and_stdin(self):
        cases = {
            'root': self.encoded.replace('"synthetic": true', '"synthetic": false, "synthetic": true', 1),
            'same_value': self.encoded.replace('"synthetic": true', '"synthetic": true, "synthetic": true', 1),
            'nested': self.encoded.replace('"requested": false', '"requested": true, "requested": false', 1),
            'array_object': self.encoded.replace('"id": "input:synthetic-design"',
                                                '"id": "discarded", "id": "input:synthetic-design"', 1),
            'decorative_nested': self.encoded.replace('"history": []',
                                                     '"history": [], "note": [{"key": 1, "key": 2}]', 1),
            'escaped': self.encoded.replace('"synthetic": true',
                                            '"\\u0073ynthetic": false, "synthetic": true', 1),
            'non_ascii': self.encoded.replace('"history": []',
                                              '"history": [], "note": {"é": 1, "\\u00e9": 2}', 1),
            'surrogate_pair': self.encoded.replace('"history": []',
                                                   '"history": [], "note": {"😀": 1, "\\ud83d\\ude00": 2}', 1),
        }
        for name, text in cases.items():
            with self.subTest(case=name):
                self.assert_rejected(text, 'Duplicate JSON key: ')

    def test_malformed_duplicate_keys_have_safe_json_diagnostics(self):
        for key in ('\\ud800', 'line\\nbreak', '\\u0000'):
            text = self.encoded.replace('"history": []',
                                        '"history": [], "note": {"' + key + '": 1, "' + key + '": 2}', 1)
            with self.subTest(key=key):
                self.assert_rejected(text, 'Duplicate JSON key: ' + ascii(json.loads('"' + key + '"')))

    def test_malformed_key_syntax_remains_a_controlled_input_error(self):
        cases = {
            'unquoted: 1': 'Expecting property name enclosed in double quotes',
            '1: "numeric key"': 'Expecting property name enclosed in double quotes',
            '"\\uZZZZ": 1': 'Invalid \\uXXXX escape',
            '"unterminated: 1': 'Unterminated string starting at',
        }
        for fragment, diagnostic in cases.items():
            text = '{' + fragment + '}'
            with self.subTest(fragment=fragment):
                self.assert_rejected(text, diagnostic)

    def test_unique_keys_preserve_cli_and_api_results(self):
        neighbors = {
            'normal': self.encoded,
            'unique_escape': self.encoded.replace('"synthetic": true', '"\\u0073ynthetic": true', 1),
            'sibling_and_distinct_unicode': self.encoded.replace(
                '"history": []',
                '"history": [], "note": [{"key": 1}, {"key": 2}], "é": 1, "e\\u0301": 2', 1),
        }
        expected = {
            'fingerprint': {name: function(self.state) for name, function in (
                ('context_fingerprint', workflow.context_fingerprint),
                ('criteria_fingerprint', workflow.criteria_fingerprint),
                ('budget_fingerprint', workflow.budget_fingerprint))},
            'recall': workflow.recall_records(self.state),
            'decide': workflow.decide(self.state),
        }
        self.assertEqual(workflow.validate_state(self.state), ([], []))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            for name, text in neighbors.items():
                path.write_text(text, encoding='utf-8')
                before = path.read_bytes()
                for command in COMMANDS:
                    for source in ('stdin', 'file'):
                        with self.subTest(case=name, command=command, source=source):
                            run = self.run_cli(command, '/dev/stdin' if source == 'stdin' else path,
                                               text if source == 'stdin' else None)
                            self.assertEqual(run.returncode, 0, run.stderr)
                            self.assertEqual(run.stderr, '')
                            output = json.loads(run.stdout)
                            self.assertEqual(output['authority'], 'advisory_only')
                            if command == 'decide':
                                self.assertEqual(output, expected['decide'])
                            else:
                                self.assertEqual(output['status'], 'valid')
                                self.assertEqual(output['reason'], 'structural_checks_only')
                                if command == 'fingerprint':
                                    self.assertEqual({key: output[key] for key in expected[command]}, expected[command])
                                elif command == 'recall':
                                    self.assertEqual(output['records'], expected[command])
                            self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
