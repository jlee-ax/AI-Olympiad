"""Build and independently exercise the two revised student artifacts on the temporary review branch."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import nbformat
from bs4 import BeautifulSoup
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_week01_render as canonical

BASELINE = "e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352"
LESSON = canonical.LESSON
BOOKS = ("week01_integrated", "week01_problem_pipeline")
BASE = Path(os.environ["RUNNER_TEMP"]) / "week01-prerequisite-proof"
PUBLIC = BASE / "public"
REPORT = "reviews/week01-prerequisites-20261120/delivery.json"
STEM_PATH = "lessons/week01/"
RECEIPTS = {
    STEM_PATH + "validation.json": BASE / "tables-validation.json",
    STEM_PATH + "week01_problem_pipeline_validation.json": BASE / "pipeline-validation.json",
}
EDITION = [STEM_PATH + stem + ext for stem in BOOKS for ext in (".ipynb", ".html")]
PERMITTED = [*EDITION, *RECEIPTS, REPORT]
MARKER = "WEEK01_EARLY_ESTIMATOR_USE"
PROFILE = '''
import sys as _sys
from sklearn.base import BaseEstimator as _BaseEstimator
def _week01_model_guard(frame, event, arg):
    if (event == "call" and frame.f_code.co_name in
            {"fit", "partial_fit", "fit_transform", "fit_predict", "transform", "predict",
             "predict_proba", "decision_function", "score", "score_samples"}
            and frame.f_globals.get("__name__", "").startswith("sklearn.")
            and isinstance(frame.f_locals.get("self"), _BaseEstimator)):
        obj = frame.f_locals["self"]
        raise RuntimeError("WEEK01_EARLY_ESTIMATOR_USE " + type(obj).__name__ + "." + frame.f_code.co_name)
_sys.setprofile(_week01_model_guard)
'''
CONTROL = '''
from sklearn.impute import SimpleImputer as _GuardControl
try:
    _GuardControl().fit([[1.0], [2.0]])
except RuntimeError as _error:
    assert "WEEK01_EARLY_ESTIMATOR_USE" in str(_error)
else:
    raise AssertionError("The estimator call guard was inactive after the learner cells")
'''


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def execute(stem, manuscript, *, guard=False):
    student = copy.deepcopy(manuscript)
    for cell in student.cells:
        if cell.cell_type == "code":
            cell.outputs, cell.execution_count = [], None
            cell.metadata.pop("execution", None)
    if guard:
        student.cells.insert(0, nbformat.v4.new_code_cell(PROFILE, id="week01-ci-install-guard"))
        student.cells.append(nbformat.v4.new_code_cell(CONTROL, id="week01-ci-check-guard"))
    csvs = sorted(LESSON.rglob("*.csv"))
    with tempfile.TemporaryDirectory(prefix="week01-delivery-", dir=BASE) as tmp:
        directory, scratch = Path(tmp) / "input", Path(tmp) / "scratch"
        directory.mkdir()
        scratch.mkdir()
        # Each book sees only its own manuscript and the shipped data.
        supplied = {stem + ".ipynb": canonical.serialized_notebook(manuscript)}
        supplied.update({p.relative_to(LESSON).as_posix(): p.read_bytes() for p in csvs})
        for relative, data in supplied.items():
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        try:
            result = NotebookClient(student, kernel_name="python3", timeout=120, allow_errors=False,
                                    record_timing=False).execute(
                cwd=str(directory), env={**os.environ, "TMPDIR": str(scratch)})
        except CellExecutionError as exc:
            if not guard or exc.ename != "RuntimeError" or not exc.evalue.startswith(MARKER + " "):
                raise
            cells = [c.id for c in student.cells if any(o.get("output_type") == "error"
                     and o.get("evalue") == exc.evalue for o in c.get("outputs", []))]
            if len(cells) != 1 or cells[0] in {"week01-ci-check-guard", "week01-ci-install-guard"}:
                raise ValueError("Could not locate the rejected learner call")
            return {"disposition": "blocked", "cell": cells[0], "operation": exc.evalue[len(MARKER) + 1:]}
        if any(scratch.rglob("*.zip")) or {p.relative_to(directory).as_posix(): p.read_bytes()
                for p in directory.rglob("*") if p.is_file()} != supplied:
            raise ValueError(f"{stem}: the notebook changed an input or left an unexpected output")
    if guard:
        return {"disposition": "passed", "negative_control_after_student_cells": "blocked"}
    if canonical.source_digest(manuscript) != canonical.source_digest(result):
        raise ValueError(f"{stem}: authored cells changed on execution")
    return result


def prepare():
    BASE.mkdir(parents=True, exist_ok=True)
    registry = canonical.registered_handouts(LESSON)
    generated = BASE / "editions"
    generated.mkdir(exist_ok=True)
    bindings = {}
    for stem in BOOKS:
        path = LESSON / (stem + ".ipynb")
        raw = path.read_bytes()
        book = nbformat.reads(raw.decode("utf-8"), as_version=4)
        authored = canonical.source_digest(book)
        html = LESSON / registry[stem]
        previous = BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser")
        meta = previous.select_one('meta[name="koai-notebook-source-sha256"]')
        aligned = bool(meta and meta.get("content") == authored)
        if aligned:
            try:
                canonical.verify_download(previous, path.name, raw)
            except ValueError:
                aligned = False
        if not aligned:
            fresh = execute(stem, book)
            canonical.write_fresh_edition(fresh, stem, generated)
        bindings[stem] = {"incoming_notebook_sha256": fingerprint(raw), "authored_sha256": authored,
                          "installed_from": "matching published pair" if aligned else "fresh cleared kernel"}
    for new in sorted(generated.iterdir()):
        if new.name not in {Path(p).name for p in EDITION}:
            raise ValueError("Unexpected generated file: " + new.name)
        shutil.copyfile(new, LESSON / new.name)
    write_json(BASE / "bootstrap.json", bindings)


def controls():
    results = {}
    for stem in BOOKS:
        relative = STEM_PATH + stem + ".ipynb"
        old = subprocess.check_output(["git", "show", BASELINE + ":" + relative])
        old_book = nbformat.reads(old.decode("utf-8"), as_version=4)
        baseline = execute(stem, old_book, guard=True)
        if baseline["disposition"] != "blocked":
            raise ValueError(f"{stem}: the real historical estimator dependency was not detected")
        current = nbformat.read(ROOT / relative, as_version=4)
        changed = canonical.source_digest(old_book) != canonical.source_digest(current)
        now = execute(stem, current, guard=True) if changed else baseline
        if changed and now["disposition"] != "passed":
            raise ValueError(f"{stem}: {now}")
        results[stem] = {"previous": baseline, "current": now, "changed_manuscript": changed}
    write_json(BASE / "estimator-controls.json", results)


def inventory():
    render = read_json(BASE / "four-books.json")
    assert len(render) == 4 and all(r["browser_widths"] == [1280, 390] for r in render)
    bound = canonical.registered_handouts(LESSON)
    publications = {}
    for stem, handout in bound.items():
        notebook = LESSON / (stem + ".ipynb")
        data = notebook.read_bytes()
        html = LESSON / handout
        canonical.verify_download(BeautifulSoup(html.read_text(encoding="utf-8"), "html.parser"), notebook.name, data)
        publications[stem] = {
            "notebook_sha256": fingerprint(data), "html_sha256": fingerprint(html.read_bytes()),
            "authored_sha256": canonical.source_digest(nbformat.reads(data.decode("utf-8"), as_version=4)),
        }
    tables = read_json(RECEIPTS[STEM_PATH + "validation.json"])
    pipeline = read_json(RECEIPTS[STEM_PATH + "week01_problem_pipeline_validation.json"])
    for receipt in (tables, pipeline):
        for relative, expected in receipt["source_sha256"].items():
            assert fingerprint((LESSON / relative).read_bytes()) == expected, relative
        assert receipt["canonical_renderer_sha256"] == fingerprint((ROOT / "tools/check_week01_render.py").read_bytes())
    receipt = {
        "schema": 1, "tested_head": subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip(),
        "previous_head": BASELINE, "run": os.environ["GITHUB_RUN_ID"], "attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "standard_jupyter_browser": render, "publications": publications,
        "bootstrap": read_json(BASE / "bootstrap.json"),
        "runtime_estimator_controls": read_json(BASE / "estimator-controls.json"),
        "independent_required_route": read_json(BASE / "independent-material.json"),
        "source_bound_tables_checks": tables["executed_code_cells"],
        "source_bound_pipeline_checks": pipeline["normal_and_error_checks"],
        "distribution": "Each download was verified byte-for-byte in offline Chromium at both widths.",
        "guard_scope": "An additional live profile blocks sklearn BaseEstimator training, transform, prediction or scoring calls in both changed books. It permits the real load_digits dependency. Unexecuted paths and unrelated third-party implementations are outside this experiment.",
    }
    assert set(publications) == {r["notebook"] for r in render}
    for name in PERMITTED:
        dest = PUBLIC / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if name == REPORT:
            write_json(dest, receipt)
        else:
            shutil.copyfile(RECEIPTS.get(name, ROOT / name), dest)
    files = {}
    for name in PERMITTED:
        data = (PUBLIC / name).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
        files[name] = {"bytes": len(data), "sha256": fingerprint(data), "git_blob": git_blob}
    write_json(PUBLIC / "manifest.json", files)
    print("W1_MANIFEST " + json.dumps(files, sort_keys=True, separators=(",",":")))


def relay():
    mode_file = ROOT / ".course-delivery-ci/mode.txt"
    mode = mode_file.read_text(encoding="ascii").strip() if mode_file.is_file() else "export"
    if mode not in {"verify", "export"}:
        raise ValueError("Unknown delivery export mode")
    if mode == "verify":
        return
    for name in PERMITTED:
        data = (PUBLIC / name).read_bytes()
        # Divisible by three so base64 segments can be concatenated verbatim.
        size = 6144
        for i in range(0, len(data), size):
            encoded = base64.b64encode(data[i:i + size]).decode("ascii")
            print("W1_BYTES " + json.dumps([name, i // size, encoded], separators=(",",":")))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "controls", "inventory", "relay"))
    {"prepare": prepare, "controls": controls, "inventory": inventory, "relay": relay}[parser.parse_args().phase]()
