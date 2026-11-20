"""Prove that each actual Week 1 input participates in the frozen release decision."""
from concurrent.futures import ThreadPoolExecutor
import csv
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lessons/week01"))
import validate_bundle as bundle


def snapshot(destination):
    release = bundle.read_json(ROOT / bundle.MANIFEST)["current_release"]
    checkpoint = bundle.read_json(ROOT / bundle.CHECKPOINT)
    names = {bundle.MANIFEST, bundle.CHECKPOINT, *bundle.COURSE_FILES, *release["files"],
             *(e["path"] for e in checkpoint["evidence"])}
    for name in names:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    return release


def false_edit(path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".ipynb":
        book = json.loads(text)
        cell = next(c for c in book["cells"] if c["cell_type"] == "markdown")
        cell["source"] = "".join(cell["source"]) + "\n모든 입력의 정답은 첫 번째 행입니다."
        return json.dumps(book, ensure_ascii=False).encode()
    if path.suffix == ".csv":
        rows = list(csv.reader(io.StringIO(text)))
        assert len(rows) > 1
        out = io.StringIO()
        csv.writer(out, lineterminator="\n").writerows(rows + [rows[1]])
        return out.getvalue().encode()
    if path.suffix == ".html":
        return text.replace("</body>", "<p>Always return row zero.</p></body>", 1).encode()
    if path.suffix == ".py":
        source = text.replace("if __name__ ==", "raise AssertionError('changed assessment')\n\nif __name__ ==", 1)
        if source == text:
            source += "\nraise AssertionError('changed assessment')\n"
        return source.encode()
    if path.suffix in {".yml", ".yaml"}:
        return (text + "\ninvalid_workflow: true\n").encode()
    return (text + "\nIncorrect key: always award full credit for the first row.\n").encode()


class WeekOneBindingTests(unittest.TestCase):
    def test_independent_projection_matches_the_canonical_renderer(self):
        import nbformat
        sys.path.insert(0, str(ROOT / "tools"))
        from check_week01_render import source_digest
        release = bundle.read_json(ROOT / bundle.MANIFEST)["current_release"]
        for group in release["members"].values():
            source = ROOT / group["student"]
            with self.subTest(member=source.name):
                self.assertEqual(bundle.authored_cells_sha256(source), source_digest(nbformat.read(source, 4)))

    def test_change_and_restore_every_registered_file(self):
        with tempfile.TemporaryDirectory(prefix="week01-changes-") as tmp:
            copy = Path(tmp)
            release = snapshot(copy)
            baseline = bundle.status(copy)
            self.assertEqual(baseline["status"], "current", baseline)
            for name in release["files"]:
                with self.subTest(path=name):
                    path = copy / name
                    original = path.read_bytes()
                    changed = false_edit(path)
                    self.assertNotEqual(changed, original)
                    path.write_bytes(changed)
                    stale = bundle.status(copy)
                    self.assertEqual(stale["status"], "stale", stale)
                    self.assertEqual(stale["changed_files"], [name])
                    self.assertNotEqual(stale["bundle_sha256"], baseline["bundle_sha256"])
                    path.write_bytes(original)
                    self.assertEqual(bundle.status(copy), baseline)

    def test_manifest_refresh_cannot_refresh_the_separate_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix="week01-checkpoint-") as tmp:
            copy = Path(tmp)
            release = snapshot(copy)
            path = copy / release["members"]["axes"]["teacher"]
            path.write_bytes(false_edit(path))
            manifest_path = copy / bundle.MANIFEST
            manifest = bundle.read_json(manifest_path)
            _, files, new_id = bundle.measure(copy, release)
            manifest["current_release"].update(files=files, bundle_sha256=new_id)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = bundle.status(copy)
            self.assertEqual(result["changed_files"], [])
            self.assertEqual(result["status"], "stale")
            self.assertTrue(any("checkpoint" in problem for problem in result["errors"]))

    def test_changed_evidence_and_missing_data_are_blocking(self):
        with tempfile.TemporaryDirectory(prefix="week01-evidence-") as tmp:
            copy = Path(tmp)
            release = snapshot(copy)
            checkpoint = bundle.read_json(copy / bundle.CHECKPOINT)
            evidence = copy / checkpoint["evidence"][0]["path"]
            original = evidence.read_bytes()
            evidence.write_bytes(original + b"\n")
            self.assertEqual(bundle.status(copy)["status"], "stale")
            evidence.write_bytes(original)
            key = copy / release["members"]["pipeline"]["data"][0]
            key.unlink()
            with self.assertRaisesRegex(ValueError, "CSV inputs"):
                bundle.status(copy)

    def test_refreshed_evidence_cannot_claim_other_publications_or_renderers(self):
        with tempfile.TemporaryDirectory(prefix="week01-evidence-rebind-") as tmp:
            copy = Path(tmp)
            snapshot(copy)
            checkpoint_path = copy / bundle.CHECKPOINT
            for kind, field in (("independent_material_review", "html_sha256"),
                                ("functional_execution", "canonical_renderer_sha256")):
                with self.subTest(kind=kind):
                    checkpoint = bundle.read_json(checkpoint_path)
                    evidence = next(e for e in checkpoint["evidence"] if e["kind"] == kind)
                    path = copy / evidence["path"]
                    original = path.read_bytes()
                    record = json.loads(original)
                    bound = next(iter(record["bindings"].values())) if "bindings" in record else record
                    bound[field] = "0" * 64
                    path.write_text(json.dumps(record), encoding="utf-8")
                    true_id = evidence["sha256"]
                    evidence["sha256"] = bundle.digest(path.read_bytes())
                    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                    self.assertEqual(bundle.status(copy)["status"], "stale")
                    path.write_bytes(original)
                    evidence["sha256"] = true_id
                    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                    self.assertEqual(bundle.status(copy)["status"], "current")

    def test_only_the_week_one_curriculum_changes_the_bundle(self):
        with tempfile.TemporaryDirectory(prefix="week01-plan-") as tmp:
            copy = Path(tmp)
            snapshot(copy)
            plan = copy / bundle.COURSE_FILES[0]
            original = plan.read_text(encoding="utf-8")
            for week in (2, 1):
                label = f"<p>{week}주차</p>"
                self.assertEqual(original.count(label), 1)
                edited = original.replace(label, f"<p>{week}주차 변경</p>")
                plan.write_text(edited, encoding="utf-8")
                result = bundle.status(copy)
                expected = [] if week == 2 else [bundle.COURSE_FILES[0] + "#week-1"]
                self.assertEqual(result["changed_course_scope"], expected)
                self.assertEqual(result["status"], "current" if week == 2 else "stale")
            plan.write_text(original, encoding="utf-8")
            contract_path = copy / bundle.COURSE_FILES[1]
            original_contract = contract_path.read_bytes()
            for week in (2, 1):
                contract = json.loads(original_contract)
                block = next(row for row in contract["weeks"] if row["week"] == week)
                block["theory_minutes"] += 1
                contract_path.write_text(json.dumps(contract), encoding="utf-8")
                result = bundle.status(copy)
                expected = [] if week == 2 else [bundle.COURSE_FILES[1] + "#week-1"]
                self.assertEqual(result["changed_course_scope"], expected)
                self.assertEqual(result["status"], "current" if week == 2 else "stale")
            contract_path.write_bytes(original_contract)
            self.assertEqual(bundle.status(copy)["status"], "current")

    def test_concurrent_checkouts_change_and_restore_independently(self):
        with tempfile.TemporaryDirectory(prefix="week01-branches-") as tmp:
            left, right = (Path(tmp) / part for part in ("left", "right"))
            release = snapshot(left)
            snapshot(right)
            student = release["members"]["tables"]["student"]
            teacher = release["members"]["pipeline"]["teacher"]
            originals = [(left / student).read_bytes(), (right / teacher).read_bytes()]

            def check(branch, name):
                path = branch / name
                path.write_bytes(false_edit(path))
                return bundle.status(branch)["changed_files"]
            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = (pool.submit(check, branch, name)
                                 for branch, name in ((left, student), (right, teacher)))
                self.assertEqual(first.result(), [student])
                self.assertEqual(second.result(), [teacher])
            (left / student).write_bytes(originals[0])
            unrelated = left / "lessons/week02/unrelated.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("An unrelated Week 2 edit.", encoding="utf-8")
            self.assertEqual(bundle.status(left)["status"], "current")
            self.assertEqual(bundle.status(right)["changed_files"], [teacher])
            (right / teacher).write_bytes(originals[1])
            self.assertEqual(bundle.status(left), bundle.status(right))

    def test_unresolved_independent_verdict_blocks_even_with_current_hashes(self):
        with tempfile.TemporaryDirectory(prefix="week01-negative-verdict-") as tmp:
            copy = Path(tmp)
            snapshot(copy)
            checkpoint_path = copy / bundle.CHECKPOINT
            checkpoint = bundle.read_json(checkpoint_path)
            evidence = next(e for e in checkpoint["evidence"] if e["kind"] == "independent_material_review")
            review_path = copy / evidence["path"]
            original = review_path.read_bytes()
            for state in ("revise", "uncertain"):
                for individual in (False, True):
                    with self.subTest(state=state, individual=individual):
                        review = json.loads(original)
                        scope = next(iter(review["bindings"].values())) if individual else review
                        scope["verdict"] = state
                        review_path.write_text(json.dumps(review), encoding="utf-8")
                        evidence["sha256"] = bundle.digest(review_path.read_bytes())
                        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                        report = bundle.status(copy)
                        self.assertEqual(report["changed_files"], [])
                        self.assertEqual(report["status"], "review_blocked")

    def test_new_supplement_requires_unique_registration_and_a_fresh_review(self):
        # These tiny artificial resources and review entries exist only in this temporary test fixture.
        with tempfile.TemporaryDirectory(prefix="week01-extension-") as tmp:
            copy = Path(tmp)
            snapshot(copy)
            manifest_path = copy / bundle.MANIFEST
            manifest = bundle.read_json(manifest_path)
            release = manifest["current_release"]
            folder = copy / bundle.LESSON
            name = "supplement-fixture"
            student = folder / (name + ".ipynb")
            student.write_text(json.dumps({"nbformat":4,"nbformat_minor":5,"metadata":{},"cells":[
                {"id":"example","cell_type":"markdown","metadata":{},"source":["연습 문제."]}]}), encoding="utf-8")
            guide = folder / (name + ".md")
            guide.write_text("Fixture teacher guidance.", encoding="utf-8")
            handout = folder / (name + ".html")
            handout.write_text("<html lang='ko'><body>연습 문제.</body></html>", encoding="utf-8")
            check = folder / "fixture-assessment.py"
            check.write_text("assert 2 + 3 == 5", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inventory"):
                bundle.status(copy)
            group = {k: p.relative_to(copy).as_posix() for k, p in
                     (("student", student), ("teacher", guide), ("html", handout))}
            group.update(data=[], assessments=[check.relative_to(copy).as_posix()])
            release["members"][name] = group
            original_guide = group["teacher"]
            group["teacher"] = release["members"]["tables"]["teacher"]
            with self.assertRaisesRegex(ValueError, "alias"):
                bundle.measure(copy, release)
            group["teacher"] = original_guide
            own_assessments = group["assessments"]
            group["assessments"] = release["members"]["axes"]["assessments"]
            with self.assertRaisesRegex(ValueError, "Aliased member assessment"):
                bundle.measure(copy, release)
            group["assessments"] = own_assessments
            _, files, identity = bundle.measure(copy, release)
            release.update(files=files, bundle_sha256=identity)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(bundle.status(copy)["status"], "stale")
            checkpoint_path = copy / bundle.CHECKPOINT
            checkpoint = bundle.read_json(checkpoint_path)
            checkpoint["bundle_sha256"] = identity
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "every registered"):
                bundle.status(copy)
            evidence = next(e for e in checkpoint["evidence"] if e["kind"] == "independent_material_review")
            report_path = copy / evidence["path"]
            report = bundle.read_json(report_path)
            report["bindings"][student.name] = {"verdict":"pass","raw_notebook_sha256":bundle.digest(student.read_bytes()),
                "authored_cells_sha256":bundle.authored_cells_sha256(student),"guide_path":group["teacher"],
                "guide_sha256":bundle.digest(guide.read_bytes())}
            report_path.write_text(json.dumps(report), encoding="utf-8")
            evidence["sha256"] = bundle.digest(report_path.read_bytes())
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            self.assertEqual(bundle.status(copy)["status"], "current")


if __name__ == "__main__":
    unittest.main()
