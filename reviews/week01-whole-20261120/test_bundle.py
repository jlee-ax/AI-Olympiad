"""Prove that each actual Week 1 input participates in the frozen release decision."""
from concurrent.futures import ThreadPoolExecutor
import csv
import io
import json
from pathlib import Path
import shutil
import subprocess
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

    def test_week_one_tool_policy_and_placement_change_while_unrelated_topics_remain_current(self):
        with tempfile.TemporaryDirectory(prefix="week01-tool-policy-") as directory:
            copy = Path(directory)
            snapshot(copy)
            contract_path = copy / bundle.COURSE_FILES[1]
            design_path = copy / bundle.COURSE_FILES[2]
            contract_raw = contract_path.read_bytes()
            design_raw = design_path.read_bytes()
            rules = json.loads(design_raw)["tool_prerequisites"]
            monitored = {rule["topic"] for rule in rules}
            for relevant in (True, False):
                contract = json.loads(contract_raw)
                topic = next(row for row in contract["topics"]
                             if (row["id"] in monitored) == relevant and 1 not in row["scheduled_weeks"])
                topic["scheduled_weeks"] = [2] if topic["scheduled_weeks"] != [2] else [3]
                contract_path.write_text(json.dumps(contract), encoding="utf-8")
                result = bundle.status(copy)
                self.assertEqual(result["status"], "stale" if relevant else "current")
                if relevant:
                    self.assertEqual(result["changed_course_scope"], [bundle.COURSE_FILES[2] + "#week-1"])
            contract_path.write_bytes(contract_raw)
            design = json.loads(design_raw)
            design["tool_prerequisites"][0]["data_only"].append("example.another_loader")
            design_path.write_text(json.dumps(design), encoding="utf-8")
            self.assertEqual(bundle.status(copy)["status"], "stale")
            design_path.write_bytes(design_raw)
            self.assertEqual(bundle.status(copy)["status"], "current")

    def test_other_week_design_does_not_change_week_one_minimum(self):
        with tempfile.TemporaryDirectory(prefix="week01-design-") as directory:
            copy = Path(directory)
            snapshot(copy)
            path = copy / bundle.COURSE_FILES[2]
            original = path.read_bytes()
            for week, expected in ((2, "current"), (1, "stale")):
                course = json.loads(original)
                next(row for row in course["weeks"] if row["week"] == week)["minimum"] = "Only reorder row IDs"
                path.write_text(json.dumps(course), encoding="utf-8")
                result = bundle.status(copy)
                self.assertEqual(result["status"], expected)
                if week == 1:
                    self.assertEqual(result["changed_course_scope"], [bundle.COURSE_FILES[2] + "#week-1"])
            path.write_bytes(original)

    def test_pass_without_observed_teaching_and_transfer_is_unresolved(self):
        with tempfile.TemporaryDirectory(prefix="week01-meaning-") as directory:
            copy = Path(directory)
            snapshot(copy)
            checkpoint_path = copy / bundle.CHECKPOINT
            frozen = checkpoint_path.read_bytes()
            for change in ("missing", "unobserved", "uncited", "bare_verdict", "different_predecessor"):
                with self.subTest(change=change):
                    checkpoint = json.loads(frozen)
                    item = next(e for e in checkpoint["evidence"] if e["kind"] == "independent_material_review")
                    path = copy / item["path"]
                    original = path.read_bytes()
                    report = json.loads(original)
                    entry = next(iter(report["bindings"].values()))
                    if change == "missing":
                        entry.pop("subject_review")
                    elif change == "unobserved":
                        entry["subject_review"]["application"]["observed"] = ""
                    elif change == "uncited":
                        entry["subject_review"]["teaching"]["cells"] = ["no-such-teaching-cell"]
                    elif change == "bare_verdict":
                        entry["subject_review"]["teaching"]["finding"] = "pass"
                        entry["subject_review"]["application"].update(case="pass", observed="pass")
                    else:
                        report["rejected_baseline_sha256"] = "0" * 64
                    path.write_text(json.dumps(report), encoding="utf-8")
                    item["sha256"] = bundle.digest(path.read_bytes())
                    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                    result = bundle.status(copy)
                    self.assertEqual(result["changed_files"], [])
                    self.assertEqual(result["review_verdicts"]["overall"], "pass")
                    self.assertEqual(result["status"], "review_blocked")
                    path.write_bytes(original)
                    checkpoint_path.write_bytes(frozen)
            self.assertEqual(bundle.status(copy)["status"], "current")

    def test_missing_rejected_or_misbound_native_decision_cannot_release(self):
        with tempfile.TemporaryDirectory(prefix="week01-native-review-") as directory:
            copy = Path(directory)
            snapshot(copy)
            checkpoint_path = copy / bundle.CHECKPOINT
            original_checkpoint = checkpoint_path.read_bytes()
            for change in ("missing", "rejected_candidate", "missing_tool_review", "blocked_tool_use",
                           "unresolved_tool_use", "different_program", "different_route", "different_guide"):
                with self.subTest(change=change):
                    checkpoint = json.loads(original_checkpoint)
                    entry = next(e for e in checkpoint["evidence"] if e["kind"] == "native_course_review")
                    path = copy / entry["path"]
                    original_native = path.read_bytes()
                    native = json.loads(original_native)
                    if change == "missing":
                        checkpoint["evidence"].remove(entry)
                    elif change == "rejected_candidate":
                        prior = next(p for p in native["native_phases"] if p["kind"] in {"rejected", "invalid_candidate"})
                        self.assertNotEqual(prior["candidate_sha256"], native["candidate_sha256"])
                        if prior["kind"] == "rejected":
                            self.assertEqual(prior["verdict"], "revise")
                        else:
                            self.assertTrue(prior["blocked_tool_findings"])
                        native["candidate_sha256"] = prior["candidate_sha256"]
                    elif change == "missing_tool_review":
                        native["native_phases"][-1]["review_checks"].pop("tool_prerequisites")
                    elif change == "blocked_tool_use":
                        native["tool_prerequisites"]["assessment"]["blocked"].append({"kind": "premature"})
                    elif change == "unresolved_tool_use":
                        assessed = native["tool_prerequisites"]
                        source = "pipeline/1566ce2a"
                        assessed["assessment"]["review_cells"] = [source]
                        assessed["judgment"]["cells"].append(source)
                        assessed["judgment"]["decisions"] = {source: {"disposition": "unresolved", "reason": "Ungrounded method"}}
                    elif change == "different_program":
                        native["program_sha256"]["tools/course_tool_prerequisites.mjs"] = "0" * 64
                    elif change == "different_route":
                        native["route_file_sha256"] = "0" * 64
                    else:
                        native["material_bindings"]["axes"]["guide_sha256"] = "0" * 64
                    if change != "missing":
                        path.write_text(json.dumps(native), encoding="utf-8")
                        entry["sha256"] = bundle.digest(path.read_bytes())
                    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
                    result = bundle.status(copy)
                    self.assertEqual(result["changed_files"], [])
                    stale = change in {"different_program", "different_route", "different_guide"}
                    self.assertEqual(result["status"], "stale" if stale else "review_blocked")
                    path.write_bytes(original_native)
                    checkpoint_path.write_bytes(original_checkpoint)
            self.assertEqual(bundle.status(copy)["status"], "current")

    def test_real_predecessor_and_its_passing_technical_receipt_require_new_review(self):
        with tempfile.TemporaryDirectory(prefix="week01-rejected-commit-") as directory:
            copy = Path(directory)
            current = snapshot(copy)
            policy = current["subject_review"]
            commit = policy["previous_commit"]
            def at_commit(name):
                return subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT)
            technical = json.loads(at_commit(bundle.CHECKPOINT))
            old_manifest = json.loads(at_commit(bundle.MANIFEST))
            old = old_manifest["current_release"]
            names = {*old["files"], *bundle.COURSE_FILES, *(item["path"] for item in technical["evidence"])}
            for name in names:
                dest = copy / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(at_commit(name))
            # Use the newly reviewed negative control and actual previously accepted records.
            # Refresh only the temporary registration so a mere stale hash cannot explain the result.
            published = bundle.read_json(ROOT / bundle.CHECKPOINT)
            rejected = next(e for e in published["evidence"] if e["kind"] == "independent_rejected_baseline")
            technical["evidence"].append(rejected.copy())
            negative = bundle.read_json(copy / rejected["path"])
            before = next(e for e in technical["evidence"] if e["kind"] == "independent_material_review")
            self.assertEqual(negative["predecessor_receipt_sha256"], before["sha256"])
            self.assertEqual(bundle.read_json(copy / before["path"])["verdict"], "pass")
            for name, item in negative["bindings"].items():
                notebook = copy / bundle.LESSON / name
                self.assertEqual(bundle.digest(notebook.read_bytes()), item["raw_notebook_sha256"])
                self.assertEqual(bundle.authored_cells_sha256(notebook), item["authored_cells_sha256"])
                self.assertEqual(bundle.digest((copy / item["guide_path"]).read_bytes()), item["guide_sha256"])
                ids = {cell["id"] for cell in bundle.read_json(notebook)["cells"]}
                self.assertTrue(bundle.has_subject_evidence(item["subject_review"], ids))
            old["subject_review"] = policy
            _, files, identity = bundle.measure(copy, old)
            old.update(files=files, course_scope=bundle.course_scope(copy), bundle_sha256=identity)
            technical["bundle_sha256"] = identity
            (copy / bundle.MANIFEST).write_text(json.dumps(old_manifest), encoding="utf-8")
            (copy / bundle.CHECKPOINT).write_text(json.dumps(technical), encoding="utf-8")
            result = bundle.status(copy)
            self.assertEqual(result["changed_files"], [])
            self.assertEqual(result["changed_course_scope"], [])
            self.assertEqual(result["review_verdicts"]["overall"], "pass")
            self.assertEqual(result["status"], "review_blocked")
            for name in negative["bindings"]:
                self.assertIn("The previously rejected student material was resubmitted unchanged: " + name, result["errors"])

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
                "guide_sha256":bundle.digest(guide.read_bytes()), "subject_review":{
                    "teaching":{"cells":["example"],"finding":"The fixture introduces summation."},
                    "application":{"cells":["example"],"case":"Apply the rule to 2 and 3.","observed":"Their sum is 5."}}}
            report_path.write_text(json.dumps(report), encoding="utf-8")
            evidence["sha256"] = bundle.digest(report_path.read_bytes())
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            self.assertEqual(bundle.status(copy)["status"], "review_blocked")
            # Extend the fixture's native decision to cover its new member as well.
            course_entry = next(e for e in checkpoint["evidence"] if e["kind"] == "native_course_review")
            course_path = copy / course_entry["path"]
            native = bundle.read_json(course_path)
            native["material_bindings"][name] = {
                "published_notebook_sha256": bundle.digest(student.read_bytes()),
                "authored_cells_sha256": bundle.authored_cells_sha256(student),
                "guide_sha256": bundle.digest(guide.read_bytes()),
            }
            course_path.write_text(json.dumps(native), encoding="utf-8")
            course_entry["sha256"] = bundle.digest(course_path.read_bytes())
            checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
            self.assertEqual(bundle.status(copy)["status"], "current")


if __name__ == "__main__":
    unittest.main()
