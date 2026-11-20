"""Seal an executed Week 1 candidate for review; only the two registered public files are returned."""
import base64
import copy
import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess

import validate_bundle as bundle

ROOT = Path.cwd()
PREVIOUS = "e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352"
REVIEWS = "reviews/week01-whole-20261120/"
ROUTE = REVIEWS + "e3e00a4-author-route.json"
CRITERIA = REVIEWS + "prerequisite-review-criteria.json"
DELIVERY = "reviews/week01-prerequisites-20261120/delivery.json"
EDITION = "week01-tool-prerequisites-20261120"
CONTROLS = [
    "tools/course.mjs", "tools/course_core.mjs", "tools/course_run.mjs",
    "tools/course_tool_prerequisites.mjs", "tools/course_tool_prerequisites.py",
    "skills/koai-evaluate/SKILL.md", REVIEWS + "test_tool_placement.py",
    REVIEWS + "check_model_prerequisites.py", ROUTE, CRITERIA,
]


def original(path):
    return subprocess.check_output(["git", "show", PREVIOUS + ":" + path], cwd=ROOT)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


class Downloads(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "download" in attrs:
            self.links.append((attrs["download"], attrs["href"]))


def check_downloads(members):
    results = {}
    for name, group in members.items():
        html = ROOT / group["html"]
        notebook = ROOT / group["student"]
        parser = Downloads()
        parser.feed(html.read_text(encoding="utf-8"))
        parser.close()
        (filename, address), = parser.links
        urltype, payload = address.split(",", 1)
        assert filename == notebook.name and urltype == "data:application/octet-stream;base64", name
        downloaded = base64.b64decode(payload, validate=True)
        assert downloaded == notebook.read_bytes(), name
        results[name] = {"suggested_filename": filename, "payload_byte_count": len(downloaded),
                         "payload_sha256": bundle.digest(downloaded)}
    return results


def seal():
    old_manifest = json.loads(original(bundle.MANIFEST))
    old_checkpoint_bytes = original(bundle.CHECKPOINT)
    old_checkpoint = json.loads(old_checkpoint_bytes)
    manifest = copy.deepcopy(old_manifest)
    release = manifest["current_release"]
    release["revision"] = EDITION
    for name in CONTROLS:
        assert (ROOT / name).is_file(), name
    release["shared_assessments"] = list(dict.fromkeys([*release["shared_assessments"], *CONTROLS]))
    _, files, identity = bundle.measure(ROOT, release)
    assert all(files.values())
    release.update(files=files, course_scope=bundle.course_scope(ROOT), bundle_sha256=identity)

    # The material review, controller and renderer supplied separate results before sealing.
    # Their documents have no dependency on this manifest or checkpoint.
    native = bundle.read_json(ROOT / REVIEWS / "native-textbook-review.json")
    review = bundle.read_json(ROOT / REVIEWS / "independent-receipt.json")
    delivery = bundle.read_json(ROOT / DELIVERY)
    assert native["schema"] == "week01_native_prerequisite_review_v2"
    assert native["previous_teaching_edition"] == PREVIOUS
    assert native["decision"] == "accepted" and review["verdict"] == "pass"
    assert native["previous_candidate_sha256"] != native["candidate_sha256"]
    assert native["route_file_sha256"] == files[ROUTE]
    rejected = [row for row in native["native_phases"] if row["kind"] == "invalid_candidate"]
    assert len(rejected) == 1 and rejected[0]["candidate_sha256"] == native["previous_candidate_sha256"]
    assert rejected[0]["blocked_tool_findings"] and native["tool_prerequisites"]["assessment"]["blocked"] == []
    assert all(item["total"] == item["passed"] and item["total"] >= 3 for item in native["final_probe_totals"].values())
    assert len(native["final_probe_totals"]) == 4
    assert native["resume"]["calls"] == native["status"]["calls"] == 0
    assert all(native["material_bindings"][role]["published_notebook_sha256"] == files[group["student"]]
               for role, group in release["members"].items())
    assert (ROOT / REVIEWS / "independent-receipt.json").read_bytes() != original(REVIEWS + "independent-receipt.json")
    assert delivery["schema"] == 1 and delivery["previous_head"] == PREVIOUS
    expected_stems = {Path(group["student"]).stem for group in release["members"].values()}
    assert set(delivery["publications"]) == expected_stems
    browser = {record["notebook"]: record for record in delivery["standard_jupyter_browser"]}
    assert set(browser) == expected_stems
    for group in release["members"].values():
        path = ROOT / group["student"]
        key = path.stem
        published = delivery["publications"][key]
        assert published["notebook_sha256"] == files[group["student"]], key
        assert published["html_sha256"] == files[group["html"]], key
        assert published["authored_sha256"] == bundle.authored_cells_sha256(path), key
        assert sorted(browser[key]["browser_widths"]) == [390, 1280], key
    assert all(control["previous"]["disposition"] == "blocked"
               and control["current"]["disposition"] == "passed"
               and control["current"]["negative_control_after_student_cells"] == "blocked"
               for control in delivery["runtime_estimator_controls"].values())
    assert set(delivery["runtime_estimator_controls"]) == {
        Path(release["members"][role]["student"]).stem for role in ("integrated", "pipeline")
    }
    embedded = check_downloads(release["members"])
    changed = {role for role, group in release["members"].items()
               if files[group["student"]] != old_manifest["current_release"]["files"][group["student"]]}
    assert changed == {"integrated", "pipeline"}

    evidence = copy.deepcopy(old_checkpoint["evidence"])
    evidence.extend([{"kind":"native_author_route","path":ROUTE},
                     {"kind":"independent_review_criteria","path":CRITERIA},
                     {"kind":"executed_distribution","path":DELIVERY}])
    for entry in evidence:
        entry["sha256"] = bundle.digest((ROOT / entry["path"]).read_bytes())
    previous_evidence = {entry["kind"]:entry["sha256"] for entry in old_checkpoint["evidence"]
                         if entry["kind"] in {"independent_material_review", "native_course_review"}}
    checkpoint = {
        "format_version": old_checkpoint["format_version"],
        "date": datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
        "revision": EDITION, "bundle_sha256": identity,
        "coverage": {"members": list(release["members"]), "registered_raw_files": len(files),
                     "week_one_curriculum_inputs": list(release["course_scope"])},
        "evidence": evidence,
        "superseded_technical_release": {"commit": PREVIOUS, "bundle_sha256": old_checkpoint["bundle_sha256"],
                                         "checkpoint_sha256": bundle.digest(old_checkpoint_bytes),
                                         "archived_evidence": previous_evidence},
        "rejected_predecessor_control": old_checkpoint["rejected_predecessor_control"],
        "current_prerequisite_control": {
            "original_commit": PREVIOUS, "original_route_sha256": files[ROUTE],
            "original_candidate_sha256": rejected[0]["candidate_sha256"],
            "original_disposition": "invalid_candidate",
            "original_required_dependency": rejected[0]["reason"],
            "corrected_candidate_sha256": native["candidate_sha256"],
            "changed_student_books": sorted(changed),
            "unchanged_student_books": sorted(set(release["members"]) - changed),
            "four_book_findings": native["tool_prerequisites"]["assessment"],
            "native_review_checks": native["final_review_check_count"],
            "executed_independent_probes": native["final_probe_totals"],
        },
        "verified_embedded_notebooks": embedded,
        "teaching_data_provenance_at_previous_commit": {"commit":PREVIOUS,
                                                       "records":old_checkpoint["primary_teaching_data"]},
        "scope": "Four teaching resources and their actual required and optional route were independently checked. The controller tests exercise a fresh sample from each declared task. Completion time, student learning and undisclosed exam requirements remain unobserved.",
    }
    outputs = [(bundle.MANIFEST, encode(manifest)), (bundle.CHECKPOINT, encode(checkpoint))]
    for path, raw in outputs:
        (ROOT / path).write_bytes(raw)
    state = bundle.status(ROOT)
    assert state["status"] == "current", state
    return [(Path(path).name, raw) for path, raw in outputs]
