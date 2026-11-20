"""Integration tests for the notebook, material edit and native fixture boundaries."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from course_diff import check
from skill_evaluation import common_sources


def note(cells):
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": cells}


def cell(name, body, code=False):
    item = {"id": name, "cell_type": "code" if code else "markdown", "source": body, "metadata": {}}
    if code:
        item.update(outputs=[], execution_count=None)
    return item


class MaterialEdits(unittest.TestCase):
    def setUp(self):
        self.old = {"notebooks": {"main": note([cell("axis", "Use the feature axis."),
                                                cell("example", "Old worked case.")])},
                    "teacher": note([cell("answer", "pass", True)])}
        self.new = copy.deepcopy(self.old)
        self.new["notebooks"]["main"]["cells"].pop()
        self.new["edits"] = {"main": {"actions": [
            {"kind": "remove", "before": ["example"], "after": [],
             "reason": "The same worked case appears twice.", "alternative": "Retain the repeated exercise.",
             "postcondition": "The axis decision remains on the student route."}],
            "routes": {"axis-choice": {"before": ["axis", "example"], "after": ["axis"]}}}}

    def test_removal_with_successor(self):
        result = check({"previous": self.old, "candidate": self.new})
        self.assertEqual(result["changes"]["main"]["removed"], ["example"])

    def test_hidden_loss_of_foundation(self):
        self.new["edits"]["main"]["routes"]["axis-choice"]["before"] = ["axis"]
        with self.assertRaisesRegex(ValueError, "without a successor"):
            check({"previous": self.old, "candidate": self.new})

    def test_malformed_edit_shape_cannot_authorize_an_unrelated_change(self):
        self.new["edits"]["main"]["actions"][0]["after"] = ["axis"]
        with self.assertRaisesRegex(ValueError, "contradicts action"):
            check({"previous": self.old, "candidate": self.new})

    def test_native_context_is_opt_in_and_free_of_grading_objects(self):
        for skill in ["koai-ground", "koai-recall", "koai-orchestrate", "koai-evaluate", "koai-reflect"]:
            baseline = common_sources(skill)
            richer = common_sources(skill, course_context=True)
            key = "case-inputs/course-public-inputs.json"
            self.assertEqual(richer.keys() - baseline.keys(), {key})
            self.assertEqual({name: richer[name] for name in baseline}, baseline)
            packet = json.loads((ROOT / richer[key]).read_text())
            self.assertEqual(len(packet["tasks"]), 5)
            for task in packet["tasks"]:
                self.assertEqual(set(task), {"event", "task", "locator", "public_input", "requested_output", "scoring_unit"})


@unittest.skipUnless(all(importlib.util.find_spec(m) for m in ("nbclient", "nbformat", "ipykernel")),
                     "Install nbclient, nbformat and ipykernel for native notebook execution")
class NativeNotebooks(unittest.TestCase):
    def setUp(self):
        from course_kernel import main
        self.run_request = main
        self.student = note([cell("student", "value = 9\nassert value > 0", True)])
        self.teacher = note([cell("ref", "def answer(v):\n    return v['x'] * 2", True)])

    def test_fresh_jupyter_executes_unseen_inputs(self):
        req = {"notebooks": {"main": self.student}, "teacher": self.teacher,
               "probes": {"ordinary": {"entrypoint": "answer", "inputs": [{"x": 4}, {"x": -3}, {"x": 0}]}}}
        self.assertEqual(self.run_request(req), {"ok": True, "output": {"ordinary": [8, -6, 0]}})
        self.assertEqual(self.student["cells"][0]["outputs"], [])

    def test_student_cannot_depend_on_teacher_kernel_state(self):
        bad = note([cell("student", "assert answer({'x': 1}) == 2", True)])
        from nbclient.exceptions import CellExecutionError
        with self.assertRaises(CellExecutionError):
            self.run_request({"notebooks": {"main": bad}, "teacher": self.teacher, "probes": {}})


if __name__ == "__main__":
    unittest.main()
