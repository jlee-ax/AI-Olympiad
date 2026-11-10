import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate import validate


def node(n): return {'id': n, 'type': 'skill', 'status': 'proposed', 'label': n}
def edge(a, b, t='depends_on'): return {'from': a, 'to': b, 'type': t}


class ValidateTest(unittest.TestCase):
    def test_feedback_cycle_is_valid(self):
        graph = {'nodes': [node('a'), node('b')], 'edges': [edge('a', 'b', 'informs'), edge('b', 'a', 'informs')]}
        self.assertEqual(validate(graph), ([], []))
    def test_dependency_cycle_is_warning(self):
        errors, warnings = validate({'nodes': [node('a'), node('b')], 'edges': [edge('a', 'b'), edge('b', 'a')]})
        self.assertFalse(errors); self.assertTrue(warnings)
    def test_missing_and_duplicate_ids_rejected(self):
        errors, _ = validate({'nodes': [node('a'), node('a')], 'edges': [edge('a', 'missing')]})
        self.assertEqual(len(errors), 2)
    def test_bad_shapes_do_not_crash(self):
        for data in (None, {}, {'nodes': [None], 'edges': [None]}, {'nodes': [], 'edges': [{'from': [], 'to': {}, 'type': 'depends_on'}]}):
            self.assertTrue(validate(data)[0])
    def test_no_mutation(self):
        data = {'nodes': [node('a')], 'edges': [edge('a', 'a')]}
        original = copy.deepcopy(data); validate(data); self.assertEqual(data, original)
    def test_long_dependency_chain(self):
        data = {'nodes': [node(str(i)) for i in range(1500)], 'edges': [edge(str(i), str(i+1)) for i in range(1499)]}
        self.assertEqual(validate(data), ([], []))

if __name__ == '__main__': unittest.main()
