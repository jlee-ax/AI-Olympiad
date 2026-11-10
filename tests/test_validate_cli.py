import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / 'tools' / 'validate.py'


class ValidateCliTest(unittest.TestCase):
    def run_validator(self, *args):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *map(str, args)],
            capture_output=True, text=True, check=False,
        )

    def test_missing_argument_returns_usage_error(self):
        result = self.run_validator()
        self.assertEqual(result.returncode, 2)
        self.assertIn('usage:', result.stderr)

    def test_missing_file_returns_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_validator(Path(directory) / 'missing.json')
        self.assertEqual(result.returncode, 2)
        self.assertIn('error:', result.stderr)

    def test_invalid_json_returns_input_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'graph.json'
            path.write_text('{', encoding='utf-8')
            result = self.run_validator(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn('error:', result.stderr)

    def test_structural_errors_return_one(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'graph.json'
            path.write_text(json.dumps({'nodes': [], 'edges': [None]}), encoding='utf-8')
            result = self.run_validator(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn('ERROR:', result.stdout)

    def test_dependency_warning_does_not_fail(self):
        graph = {
            'nodes': [{'id': 'a', 'type': 'skill', 'status': 'proposed', 'label': 'A'}],
            'edges': [{'from': 'a', 'to': 'a', 'type': 'depends_on'}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'graph.json'
            path.write_text(json.dumps(graph), encoding='utf-8')
            result = self.run_validator(path)
        self.assertEqual(result.returncode, 0)
        self.assertIn('WARNING: dependency cycle detected:', result.stdout)


if __name__ == '__main__':
    unittest.main()
