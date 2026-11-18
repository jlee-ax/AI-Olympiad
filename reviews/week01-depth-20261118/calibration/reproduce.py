"""Replay external answers with the generated NVIDIA custom verifier and aggregate the separate external metrics."""
import argparse
import ast
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
ARMS = {"J": "without", "R": "with"}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, content):
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def independent_probes():
    labels = {"R": "West", "T": "East"}
    x, y = [3, 9, 5], [7]
    neighbors = sorted((abs(coord - 1), color) for coord, color in [(0, "red"), (4, "blue"), (6, "blue")])
    def vote(k):
        return Counter(color for _, color in neighbors[:k]).most_common(1)[0][0]
    def starts(axis):
        return sum(i + 3 <= axis for i in range(0, axis, 2))
    rooms = [[2, 2, 2], [10]]
    def means(room_rows):
        room_mean = sum(Fraction(sum(row), len(row)) for row in room_rows) / len(room_rows)
        visit_mean = Fraction(sum(map(sum, room_rows)), sum(map(len, room_rows)))
        return float(room_mean), float(visit_mean)
    before, after = means(rooms), means([rooms[0] + [2], rooms[1]])
    history = {1: 3, 2: 8, 3: 20, 4: 9}
    mask = [1, 1, 0]
    def masked(values):
        valid = [v for v, used in zip(values, mask) if used]
        return sum(valid) / len(valid)
    clusters = {0: [], 10: []}
    for v in [1, 3, 9, 11]:
        center = min(clusters, key=lambda c: abs(v - c))
        clusters[center].append(v)
    errors = {"X": [0, 0, 5], "Y": [2, 2, 2]}
    def best(power):
        return min(errors, key=lambda model: sum(v ** power for v in errors[model]) / len(errors[model]))
    received = [("P9", "거리표"), ("F1", "그래프"), ("K4", "마스크")]
    return {
        "c17": [labels.get(k) for k in ["T", "R", "T", "X"]],
        "c42": [min(x), max(x), len(y)], "c08": [vote(1), vote(3)],
        "c33": [starts(6), starts(8)], "c37": [before[0], after[0]],
        "c54": [history[max(t for t in history if t < target)] for target in (3, 4)],
        "c69": [masked([0, 4, 99]), masked([0, 4, -8])],
        "c71": [sum(v >= 4 for v in values) for values in [[4, 2, 4], []]],
        "c26": [sum(v) / len(v) for v in clusters.values()], "c58": [before[1], after[1]],
        "c93": [best(1), best(2)], "c80": [key for key, _ in received],
    }


def replay_answer(task, answer):
    tests = task / "tests"
    runner = tests / "skill_evaluator/custom_grader_runner.py"
    with tempfile.TemporaryDirectory(prefix="koai-depth-verifier-") as temp:
        work = Path(temp)
        output = work / "workspace/output"
        verifier = work / "logs/verifier"
        output.mkdir(parents=True)
        verifier.mkdir(parents=True)
        save(output / "answer.json", answer)
        environment = {
            "PATH": os.defpath, "PYTHONDONTWRITEBYTECODE": "1",
            "HARBOR_LOGS_DIR": str(verifier.parent), "HARBOR_VERIFIER_DIR": str(verifier),
            "HARBOR_TESTS_DIR": str(tests), "HARBOR_WORKSPACE_DIR": str(output.parent),
        }
        subprocess.run([sys.executable, "-I", str(runner), "--mode", "custom_only"],
                       cwd=work, env=environment, check=True, capture_output=True, timeout=30)
        return read(verifier / "reward.json")["koai_case_facts_correct"]


def inspect_imports(tools_dir, known_modules):
    inventory = {}
    for path in sorted(tools_dir.glob("*.py")):
        imported = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        project = sorted(imported & known_modules)
        missing = [name for name in project if not (tools_dir / (name + ".py")).is_file()]
        if missing:
            raise ValueError(f"{path.name}: missing local modules {missing}")
        inventory[path.stem] = {
            "project_modules": project,
            "third_party_imports": sorted(imported - known_modules - sys.stdlib_module_names),
        }
    return inventory


def verify_fixtures(prepared):
    # -I prevents the checkout and user site from satisfying a broken task import.
    verify_imports = """import importlib, sys
from pathlib import Path
folder = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(folder))
for name in sys.argv[2:]:
    module = importlib.import_module(name)
    assert Path(module.__file__).resolve() == folder / (name + '.py'), name
"""
    known_modules = {p.stem for p in (ROOT.parents[2] / "tools").glob("*.py")}
    common, verifier_files, inventory = None, None, None
    checked = {"with": [], "without": []}
    linked_guides = {"with": [], "without": []}
    for arm in ("without", "with"):
        for task in sorted(entry for entry in (prepared / arm).iterdir() if entry.is_dir()):
            repo = task / "environment/repo"
            tools_dir = repo / "tools"
            native_dir = task / "tests/skill_evaluator"
            files = {f.relative_to(repo).as_posix(): digest(f) for f in repo.rglob("*") if f.is_file()
                     and not f.relative_to(repo).as_posix().startswith("candidate/koai-evaluate/")}
            native_files = {f.stem: digest(f) for f in native_dir.glob("*.py")}
            if "(topic-depth.md)" in (tools_dir / "material-revision.md").read_text():
                guide = tools_dir / "topic-depth.md"
                if not guide.is_file() or "tools/topic_depth.py check" not in guide.read_text():
                    raise ValueError("Missing linked depth guide in " + arm + "/" + task.name)
                linked_guides[arm].append(task.name)
            if any(key.startswith("reviews/week01-depth-20261118/") or "week01_foundations" in key
                   or key.startswith("lessons/week01/data/foundations_") for key in files):
                raise ValueError("Unrequested production lesson or review material in " + arm + "/" + task.name)
            if common is None:
                common, verifier_files = files, native_files
                inventory = inspect_imports(tools_dir, known_modules)
            if files != common or native_files != verifier_files:
                raise ValueError("Common or verifier files differ: " + arm + "/" + task.name)
            for folder, names in ((tools_dir, inventory), (native_dir, verifier_files)):
                result = subprocess.run([sys.executable, "-I", "-B", "-c", verify_imports, str(folder),
                                         *sorted(names)], cwd=repo, capture_output=True, text=True, timeout=30)
                if result.returncode:
                    raise ValueError(f"Import failed in {arm}/{task.name}/{folder.name}: {result.stderr}")
            checked[arm].append(task.name)
    if checked["with"] != checked["without"] or len(checked["with"]) != 12:
        raise ValueError("The calibration set requires the same 12 tasks in both arms")
    if sha256(json.dumps(common, sort_keys=True).encode()).hexdigest() != read(prepared / "preparation.json")["context_sha256"]:
        raise ValueError("Common file hashes do not match the recorded context")
    return {"scope": "offline fixture imports, including the NVIDIA verifier as standalone staged modules",
            "tested_local_imports": sorted(inventory), "python_import_dependencies": inventory,
            "verified_NVIDIA_staged_modules_sha256": verifier_files,
            "successful_cases": checked, "linked_general_guide": linked_guides,
            "production_foundations_or_review_inputs_exposed": False,
            "common_file_count": len(common), "common_file_sha256": common}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prepared", type=Path, help="NVIDIA paired task preparation directory")
    parser.add_argument("out", type=Path, help="New, non-existing report directory")
    args = parser.parse_args()
    prepared = args.prepared.resolve()
    for name, expected in read(ROOT / "frozen-sha256.json").items():
        if digest(ROOT / name) != expected:
            raise ValueError("Frozen source changed: " + name)
    prep = read(prepared / "preparation.json")
    if prep["dataset_sha256"] != digest(ROOT / "native-suite.json") or not prep["shared_sha256_equal"]:
        raise ValueError("Unexpected dataset or mismatched arms")
    historical = read(ROOT / "native-preparation.json")
    release = read(ROOT / "release-packaging/preparation.json")
    for name in ("skill_bundle_sha256", "skillevaluator_python_sha256", "grader_sha256"):
        if prep[name] != historical[name] or prep[name] != release[name]:
            raise ValueError("Changed task or verifier identity: " + name)
    contexts = {historical["context_sha256"], release["context_sha256"]}
    if prep["context_sha256"] not in contexts:
        raise ValueError("Common sources match neither the retained original nor the release packaging")
    answers = {row["id"]: row for row in read(ROOT / "answer-key.json")["items"]}
    if independent_probes() != {cid: item["probe"] for cid, item in answers.items()}:
        raise ValueError("Independent numerical derivation differs from frozen answer key")
    adjudication = read(ROOT / "blind-adjudication.json")
    manual = {(row["reader"], row["id"]): row for row in adjudication["cases"]}
    args.out.mkdir(exist_ok=False)
    save(args.out / "fixture-check.json", verify_fixtures(prepared))
    rows, observations, controls = [], [], []
    for reader, arm in ARMS.items():
        raw_file = ROOT / f"reader-{reader}.json"
        if digest(raw_file) != adjudication["reader_sha256"][reader]:
            raise ValueError("Changed reviewer answer: " + reader)
        for answer in read(raw_file):
            cid = answer["id"]
            task = prepared / arm / ("depth-" + cid)
            exact = replay_answer(task, answer)
            decision = manual[reader, cid]
            combined = bool(exact and decision["basis_semantically_supported"] and decision["edit_consistent"])
            rows.append({"reader": reader, "case": cid, "koai_case_facts_correct": exact, "complete": combined})
            if cid != "c80":
                observations.append({"case_id": cid, "attempt": 1, "arm": arm + "_skill",
                                     "custom_metrics": {"editorial_review_complete": int(combined),
                                                        "selection_and_probe_correct": exact}})
            if reader == "J" and cid in ("c37", "c58", "c26"):
                changed = dict(answer)
                if cid == "c37":
                    changed.update(selection="B")
                    label, expected = "wrong selection, correct probe", 0.0
                elif cid == "c58":
                    changed.update(probe=[6, 6])
                    label, expected = "correct selection, wrong probe", 0.0
                else:
                    changed.update(basis="", edit="")
                    label, expected = "missing both semantic fields, correct selection and probe", 1.0
                value = replay_answer(task, changed)
                if value != expected:
                    raise ValueError("Verifier sensitivity control failed: " + label)
                controls.append({"id": cid, "change": label, "custom_result": value,
                                 "meets_complete_educational_rubric": False})
    save(args.out / "replay.json", {
        "mode": "generated NVIDIA custom_grader_runner.py --mode custom_only; external answer replay",
        "project_grader_sha256": prep["grader_sha256"],
        "native_runner_sha256": digest(prepared / "with/depth-c17/tests/skill_evaluator/custom_grader_runner.py"),
        "native_default_grades": 0, "native_agent_trials": 0, "independently_recomputed_probes": len(answers),
        "real_external_answer_replays": len(rows), "results": rows, "sensitivity_controls": controls,
    })
    metric_definition = {"version": "1", "unit": "fraction",
                         "direction": "higher_is_better", "aggregation": "mean"}
    save(args.out / "external-input.json", {
        "schema_version": "1",
        "evaluation": {"dataset_id": "koai-novice-depth-finite-review", "dataset_version": "1",
                       "skill_id": "koai-evaluate", "skill_version": prep["skill_bundle_sha256"],
                       "agent": "Codex conversation subagent", "agent_version": "unspecified",
                       "model": "gpt-6.2-astra (requested)", "environment": "separate conversation sessions"},
        "provenance": {"producer": "anonymous semantic adjudication and generated rule-based verifier replay",
                       "run_id": "koai-20261118-blind-depth", "created_at": read(ROOT / "arm-map.json")["disclosed_at"]},
        "metric_definitions": {k: metric_definition for k in
                               ("editorial_review_complete", "selection_and_probe_correct")},
        "observations": observations,
    })
    cli = Path(sys.executable).with_name("skillevaluator")
    subprocess.run([str(cli), "tier3", "import-metrics", str(args.out / "external-input.json"),
                    "--output-dir", str(args.out / "native-import")], check=True, timeout=60)


if __name__ == "__main__":
    main()
