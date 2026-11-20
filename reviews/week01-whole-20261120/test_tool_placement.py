"""Exercise the normal prerequisite scanner on the real, previously accepted Week 1 route."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = "e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352"
REVIEW = "reviews/week01-whole-20261120"
MANIFEST = "lessons/week01/lesson-manifest.json"
SCANNER = ROOT / "tools" / "course_tool_prerequisites.py"


def read(path, revision=None):
    if revision:
        content = subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)
    else:
        content = (ROOT / path).read_bytes()
    return json.loads(content)


def learner_books(revision=None):
    members = read(MANIFEST, revision)["current_release"]["members"]
    return {("main" if key == "integrated" else key): read(item["student"], revision)
            for key, item in members.items()}


class ActualStudyRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (ROOT / REVIEW / "e3e00a4-author-route.json").read_bytes()
        cls.previous_decision = read(f"{REVIEW}/native-textbook-review.json", ARCHIVE)
        if hashlib.sha256(raw).hexdigest() != cls.previous_decision["route_file_sha256"]:
            raise AssertionError("This is not the previously accepted author's route")
        cls.route = json.loads(raw)["route"]
        js = (
            "import {loadCourse} from './tools/course.mjs';"
            "const course=loadCourse(process.cwd(),'curriculum/course-harness.json',"
            "'curriculum/contract.json').course;"
            "console.log(JSON.stringify(course.weeks[1].tool_prerequisites));"
        )
        cls.rules = json.loads(subprocess.check_output(
            ["node", "--input-type=module", "-e", js], cwd=ROOT, text=True))
        cls.prior = cls.assess(learner_books(ARCHIVE))

    @classmethod
    def assess(cls, notebooks):
        # Supply the same authored cell fields as the real controller. Saved output and
        # private grading material have no bearing on what the learner is asked to do.
        projected = {book: {"cells": [{field: cell[field] for field in ("id", "cell_type", "source")}
                                      for cell in notebook["cells"]]}
                     for book, notebook in notebooks.items()}
        payload = {"week": 1, "rules": cls.rules, "route": cls.route, "notebooks": projected}
        run = subprocess.run([sys.executable, "-I", str(SCANNER)], cwd=ROOT, check=True,
                             text=True, input=json.dumps(payload), capture_output=True)
        return json.loads(run.stdout)

    def test_old_passing_book_depended_on_later_models_in_required_homework(self):
        self.assertEqual(self.previous_decision["decision"], "accepted")
        first, = (unit for unit in self.route["units"] if "pipeline/1566ce2a" in unit["cells"])
        self.assertEqual((first["tier"], first["minutes"]), ("homework", 50))
        actual = [hit for hit in self.prior["blocked"] if hit["topic"] == "KOAI-04"]
        self.assertIn("pipeline/1566ce2a", {hit["cell"] for hit in actual})
        self.assertTrue(any("NearestCentroid" in hit["api"] for hit in actual))
        self.assertTrue(all(hit["tier"] != "conditional" for hit in actual))

    def test_data_loads_and_conditional_demonstration_are_distinguished(self):
        uses = self.prior["findings"]
        self.assertTrue(any(hit["cell"].startswith("tables/") and hit["kind"] == "data_only"
                            and hit["api"].endswith("load_digits") for hit in uses))
        self.assertTrue(any(hit["cell"].startswith("main/") and hit["kind"] == "conditional"
                            and "NearestCentroid" in hit["api"] for hit in uses))

    def test_published_learner_path_has_no_premature_required_model(self):
        current = self.assess(learner_books())
        self.assertEqual(current["blocked"], [])
        self.assertTrue(any(hit["kind"] == "data_only" and hit["api"].endswith("load_digits")
                            for hit in current["findings"]))


if __name__ == "__main__":
    unittest.main()
