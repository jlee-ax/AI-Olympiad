"""Check the registered Week 1 release and its independently frozen checkpoint."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LESSON = "lessons/week01/"
MANIFEST = LESSON + "lesson-manifest.json"
CHECKPOINT = "reviews/week01-whole-20261120/bundle-checkpoint.json"
COURSE_FILES = ("curriculum/student-plan.html", "curriculum/contract.json", "curriculum/course-harness.json")
STEMS = {
    "integrated": "week01_integrated",
    "tables": "week01_python_tables",
    "axes": "week01_axes_linear_bridge",
    "pipeline": "week01_problem_pipeline",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8"))


def file_at(root, name):
    relative = Path(name)
    if (not name or relative.is_absolute() or ".." in relative.parts or
            str(relative) != name or not (root / relative).resolve().is_relative_to(root)):
        raise ValueError(f"Invalid release path {name!r}")
    path = root / relative
    if any(parent.is_symlink() for parent in (path, *path.parents) if parent.is_relative_to(root)):
        raise ValueError(f"Symlink in release path {name!r}")
    return path


def read_json(path):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON property {key!r} in {path}")
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=reject_duplicates)


def members(release, root):
    notes = release["members"]
    if release["format_version"] != 1 or release["entry"] != "integrated" or not STEMS.keys() <= notes.keys():
        raise ValueError("Register the integrated entry and all three existing Week 1 companions")
    groups = {}
    all_data = set()
    owned = set()
    member_assessments = set()
    for role, group in notes.items():
        if role == "shared" or not re.fullmatch(r"[a-z][a-z0-9_-]*", role) or not group["assessments"]:
            raise ValueError("A Week 1 member needs a name and assessed work")
        primary = [group[k] for k in ("student", "teacher", "html")]
        if role in STEMS:
            stem = STEMS[role]
            teacher = "teacher-notes.txt" if role == "tables" else stem + "_teacher.md"
            if primary != [LESSON + stem + ".ipynb", LESSON + teacher, LESSON + stem + ".html"]:
                raise ValueError("Existing Week 1 member identity changed: " + role)
        expected_types = ({".ipynb"}, {".md", ".markdown", ".txt", ".ipynb"}, {".html"})
        if any(Path(name).parent.as_posix() != LESSON.rstrip("/") or Path(name).suffix.lower() not in types
               for name, types in zip(primary, expected_types)):
            raise ValueError("Each student, guide and handout must be an in-week file: " + role)
        if owned.intersection(primary):
            raise ValueError("Two members alias the same student, teacher or handout: " + role)
        owned.update(primary)
        paths = [*primary, *group["data"], *group["assessments"]]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate registered path for " + role)
        if member_assessments.intersection(group["assessments"]):
            raise ValueError("Aliased member assessment. Register cross-member checks as shared assessments")
        member_assessments.update(group["assessments"])
        all_data.update(group["data"])
        groups[role] = paths
    folder = root / LESSON
    data = {p.relative_to(root).as_posix() for p in [*(folder / "data").glob("*.csv"), *folder.glob("*.csv")]}
    if data != all_data:
        raise ValueError("Unregistered or absent Week 1 CSV inputs: " + ", ".join(sorted(data ^ all_data)))
    for suffix in (".ipynb", ".html"):
        actual = {p.relative_to(root).as_posix() for p in folder.glob("*" + suffix)}
        declared = {name for name in owned if Path(name).suffix == suffix}
        if actual != declared:
            raise ValueError("Week 1 file inventory changed: " + ", ".join(sorted(actual ^ declared)))
    shared = release["shared_assessments"]
    if len(shared) != len(set(shared)) or LESSON + "validate_bundle.py" not in shared:
        raise ValueError("Missing or duplicate shared assessment registration")
    groups["shared"] = shared
    return groups


def course_scope(root):
    plan = file_at(root, COURSE_FILES[0]).read_text(encoding="utf-8")
    rows = re.findall(r'<tr\b[^>]*\bid=["\']week-1["\'][^>]*>[\s\S]*?</tr>', plan, re.I)
    contract = read_json(file_at(root, COURSE_FILES[1]))
    weeks = [week for week in contract["weeks"] if week["week"] == 1]
    if len(rows) != 1 or len(weeks) != 1:
        raise ValueError("Week 1 needs one active plan row and one contract allocation")
    scope = {k: contract[k] for k in ("competition_year", "division", "syllabus_label", "class_minutes")}
    scope.update(week=weeks[0], topics=[t for t in contract["topics"] if 1 in t["scheduled_weeks"]])
    designs = read_json(file_at(root, COURSE_FILES[2]))
    selected = [item for item in designs["weeks"] if item["week"] == 1]
    if len(selected) != 1:
        raise ValueError("Week 1 needs a single course decision and transfer interface")
    local_design = {"week": selected[0], "sources": {key: designs["sources"][key] for key in selected[0]["sources"]}}
    policies = designs.get("tool_prerequisites", [])
    if policies:
        topics = {topic["id"]: topic for topic in contract["topics"]}
        # Week 1 availability depends on both the rule and the curriculum placement of
        # the concept behind it. Other weeks' lesson prose and time budgets stay separate.
        source_weeks = {rule["topic"]: sorted(topics[rule["topic"]]["scheduled_weeks"]) for rule in policies}
        graph = {row["week"]: row["prerequisites"] for row in designs["weeks"]}
        reachable = set()
        remaining = [1]
        while remaining:
            number = remaining.pop()
            if number not in reachable:
                reachable.add(number)
                remaining.extend(graph[number])
        local_design["tool_prerequisites"] = {
            "rules": policies, "scheduled_weeks": source_weeks,
            "dependencies": [[number, sorted(graph[number])] for number in sorted(reachable)],
        }
    return {COURSE_FILES[0] + "#week-1": digest(rows[0].encode()),
            COURSE_FILES[1] + "#week-1": fingerprint(scope),
            COURSE_FILES[2] + "#week-1": fingerprint(local_design)}


def measure(root, release):
    """Compute from disk so an edited companion invalidates even an unchanged manifest."""
    groups = members(release, root)
    files = {}
    for name in sorted({path for paths in groups.values() for path in paths}):
        path = file_at(root, name)
        files[name] = digest(path.read_bytes()) if path.is_file() else None
    identity = {key: release[key] for key in ("format_version", "entry", "members", "shared_assessments")}
    if "subject_review" in release:
        identity["subject_review"] = release["subject_review"]
    identity["files"] = files
    identity["course_scope"] = course_scope(root)
    return groups, files, fingerprint(identity)


def authored_cells_sha256(path):
    """The canonical renderer projection, using nbformat's multiline text convention."""
    cells = read_json(path)["cells"]
    for cell in cells:
        cell.pop("execution_count", None)
        cell.pop("outputs", None)
        cell["metadata"].pop("execution", None)
        cell["source"] = "".join(cell["source"])
        for attachment in cell.get("attachments", {}).values():
            for mime, payload in attachment.items():
                if not (mime == "application/json" or mime.endswith("+json")) and isinstance(payload, list):
                    attachment[mime] = "".join(payload)
    return digest(json.dumps(cells, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def has_subject_evidence(review, cell_ids):
    """Check cited locations and the presence of the reader's observations."""
    if not isinstance(review, dict):
        return False
    for kind, fields in (("teaching", ("finding",)), ("application", ("case", "observed"))):
        item = review.get(kind)
        if not isinstance(item, dict):
            return False
        cells = item.get("cells")
        if not isinstance(cells, list) or not cells or any(c not in cell_ids for c in cells):
            return False
        if any(not isinstance(item.get(k), str) or not item[k].strip() for k in fields):
            return False
    application = review["application"]
    return application["case"].strip() != application["observed"].strip()


def subject_review(root, release, evidence, report, unresolved):
    policy = release.get("subject_review")
    if not isinstance(report.get("reviewer"), str) or not report["reviewer"].strip():
        unresolved.append("The independent teaching decision needs an identified reviewer")
    baseline = [item for item in evidence if item["kind"] == "independent_rejected_baseline"]
    if not isinstance(policy, dict) or len(baseline) != 1:
        unresolved.append("A substantive independent review and its known rejected teaching edition are required")
        return {}
    previous = baseline[0]
    rejected = read_json(file_at(root, previous["path"]))
    if (previous["sha256"] != policy.get("rejected_baseline_sha256")
            or rejected.get("baseline_commit") != policy.get("previous_commit")
            or rejected.get("verdict") != "revise"
            or report.get("rejected_baseline_sha256") != previous["sha256"]):
        unresolved.append("The independent teaching decision is missing its reviewed predecessor")
    old_bindings = rejected.get("bindings", {})
    previous_names = {stem + ".ipynb" for stem in STEMS.values()}
    if not previous_names <= old_bindings.keys():
        unresolved.append("The rejected edition does not cover the four existing teaching resources")
    return old_bindings


def native_decision(root, release, evidence, current, errors, unresolved):
    records = [item for item in evidence if item["kind"] == "native_course_review"]
    if len(records) != 1:
        unresolved.append("The independent native Week 1 course decision is missing")
        return
    report = read_json(file_at(root, records[0]["path"]))
    candidate = report.get("candidate_sha256", "")
    decisions = [phase for phase in report.get("native_phases", [])
                 if phase.get("candidate_sha256") == candidate and "verdict" in phase]
    last = decisions[-1] if decisions else {}
    checks = last.get("review_checks", {})
    if (not re.fullmatch(r"[a-f0-9]{64}", candidate)
            or report.get("decision") != "accepted" or last.get("kind") != "accepted"
            or last.get("verdict") != "pass" or not checks or set(checks.values()) != {"pass"}):
        unresolved.append("The registered candidate needs a passing native course decision")
    design = COURSE_FILES[2] + "#week-1"
    if report.get("governing_week_one_sha256") != release["course_scope"][design]:
        errors.append("The native decision used a different Week 1 course design")
    governed = read_json(file_at(root, COURSE_FILES[2])).get("tool_prerequisites", [])
    if governed:
        scan = report.get("tool_prerequisites", {})
        assessment = scan.get("assessment", {})
        if (checks.get("tool_prerequisites") != "pass"
                or scan.get("judgment", {}).get("verdict") != "pass"
                or not isinstance(assessment, dict)
                or assessment.get("blocked") != []
                or not isinstance(assessment.get("review_cells"), list)):
            unresolved.append("The required route needs a current tool-prerequisite inspection and an independent decision")
        else:
            needed = set(assessment["review_cells"])
            judgment = scan["judgment"]
            decisions = judgment.get("decisions", {})
            if (not isinstance(decisions, dict) or set(decisions) != needed
                    or not needed <= set(judgment.get("cells", []))
                    or any(not isinstance(item, dict)
                           or item.get("disposition") not in {"uses_prior_only", "example_only"}
                           or not str(item.get("reason", "")).strip() for item in decisions.values())):
                unresolved.append("The native reviewer did not resolve every flagged student tool dependency")
        routes = [item.get("path") for item in evidence if item["kind"] == "native_author_route"]
        if (len(routes) != 1 or routes[0] not in current
                or report.get("route_file_sha256") != current[routes[0]]):
            errors.append("The native review used a different allocation of required and optional work")
        for path in ("tools/course.mjs", "tools/course_core.mjs", "tools/course_run.mjs",
                     "tools/course_tool_prerequisites.mjs", "tools/course_tool_prerequisites.py",
                     "skills/koai-evaluate/SKILL.md"):
            if path not in current or report.get("program_sha256", {}).get(path) != current[path]:
                errors.append("The native prerequisite decision used a different course program: " + path)
    reviewed = report.get("material_bindings", {})
    if set(reviewed) != set(release["members"]):
        unresolved.append("The native course decision must cover every registered Week 1 member")
        return
    for role, member in release["members"].items():
        binding = reviewed[role]
        if (binding.get("published_notebook_sha256") != current[member["student"]]
                or binding.get("authored_cells_sha256") != authored_cells_sha256(file_at(root, member["student"]))
                or binding.get("guide_sha256") != current[member["teacher"]]):
            errors.append("The native decision refers to different student or instructor material: " + role)


def review_bindings(root, release, checkpoint, current, errors, unresolved=None):
    if unresolved is None:
        unresolved = []
    evidence = checkpoint["evidence"]
    reviews = [item for item in evidence if item["kind"] == "independent_material_review"]
    if len(reviews) != 1 or not evidence:
        raise ValueError("One independent Week 1 whole-bundle review is required")
    for record in evidence:
        path = file_at(root, record["path"])
        if not path.is_file() or digest(path.read_bytes()) != record["sha256"]:
            errors.append("Checkpoint evidence changed: " + record["path"])
    if errors:
        return {}
    retained = {e["member"]: e for e in evidence if e["kind"] == "functional_execution"}
    if not {"tables", "pipeline"} <= retained.keys():
        raise ValueError("The current tables and pipeline execution receipts are required")
    for member, record in retained.items():
        group = release["members"][member]
        receipt = read_json(file_at(root, record["path"]))
        tested = receipt["source_sha256"]
        if receipt.get("canonical_renderer_sha256") != current.get("tools/check_week01_render.py"):
            errors.append("The functional receipt used a different renderer: " + member)
        if record["validator"] not in group["assessments"]:
            raise ValueError("Unregistered validation program for " + member)
        required = [group["student"], group["teacher"], group["html"], record["validator"], *group["data"]]
        if any(tested.get(name.removeprefix(LESSON)) != current[name] for name in required):
            errors.append("The functional receipt refers to different inputs: " + member)
    report = read_json(file_at(root, reviews[0]["path"]))
    old_bindings = subject_review(root, release, evidence, report, unresolved)
    native_decision(root, release, evidence, current, errors, unresolved)
    bindings = report["bindings"]
    wanted = {Path(group["student"]).name for group in release["members"].values()}
    if set(bindings) != wanted:
        raise ValueError("Independent report must identify every registered student notebook")
    if "data_bindings" in report:
        data = {name: current[name] for group in release["members"].values() for name in group["data"]}
        if report["data_bindings"] != data:
            errors.append("Independent report data bindings are stale")
    verdicts = {"overall": report["verdict"]}
    for group in release["members"].values():
        name = Path(group["student"]).name
        checked = bindings[name]
        verdicts[name] = checked["verdict"]
        source = file_at(root, group["student"])
        ids = {cell["id"] for cell in read_json(source)["cells"]}
        if not has_subject_evidence(checked.get("subject_review"), ids):
            unresolved.append("Missing independent teaching or unseen application evidence: " + name)
        prior = old_bindings.get(name, {})
        if prior.get("verdict") == "revise" and prior.get("authored_cells_sha256") == authored_cells_sha256(source):
            unresolved.append("The previously rejected student material was resubmitted unchanged: " + name)
        for path, keys in ((group["student"], ("published_notebook_sha256",)),
                           (group["html"], ("html_sha256", "published_html_sha256"))):
            if any(key in checked and checked[key] != current[path] for key in keys):
                errors.append("Independent publication binding is stale: " + path)
        if (not re.fullmatch(r"[a-f0-9]{64}", checked["raw_notebook_sha256"])
                or checked["guide_path"] not in {group["teacher"], Path(group["teacher"]).name}
                or checked["authored_cells_sha256"] != authored_cells_sha256(file_at(root, group["student"]))
                or checked["guide_sha256"] != current[group["teacher"]]):
            errors.append("Independent student or guide evidence is stale: " + name)
    if any(v not in {"pass", "revise", "uncertain"} for v in verdicts.values()):
        raise ValueError("Unknown independent material-review verdict")
    return verdicts


def status(root):
    root = root.resolve(strict=True)
    release = read_json(file_at(root, MANIFEST))["current_release"]
    checkpoint = read_json(file_at(root, CHECKPOINT))
    groups, current, bundle = measure(root, release)
    expected = release["files"]
    changed = sorted(p for p in set(current) | set(expected)
                     if current.get(p) is None or current.get(p) != expected.get(p))
    errors = []
    changed_scope = [name for name, value in course_scope(root).items()
                     if release["course_scope"].get(name) != value]
    if changed_scope:
        errors.append("Week 1 curriculum scope changed: " + ", ".join(changed_scope))
    if changed or release["bundle_sha256"] != bundle:
        errors.append("Registered Week 1 artifacts or assessment inputs changed")
    if checkpoint["bundle_sha256"] != bundle:
        errors.append("The frozen checkpoint belongs to different Week 1 material")
    unresolved = []
    verdicts = review_bindings(root, release, checkpoint, current, errors, unresolved)
    if not errors:
        if (measure(root, release)[2] != bundle
                or read_json(file_at(root, MANIFEST))["current_release"] != release
                or read_json(file_at(root, CHECKPOINT)) != checkpoint):
            errors.append("Release inputs or checkpoint changed during verification")
    state = "stale" if errors else "current"
    if not errors and (unresolved or any(v != "pass" for v in verdicts.values())):
        state = "review_blocked"
        errors.extend(unresolved or ["The independent reviewer has unresolved findings"])
    return {"status": state, "bundle_sha256": bundle, "review_verdicts": verdicts,
            "members": {k: sorted(set(v) & set(changed)) for k, v in groups.items()},
            "changed_files": changed, "changed_course_scope": changed_scope, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = status(args.root)
    except (OSError, KeyError, TypeError, ValueError) as error:
        result = {"status": "invalid", "error": str(error)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "current" else 1


if __name__ == "__main__":
    sys.exit(main())
