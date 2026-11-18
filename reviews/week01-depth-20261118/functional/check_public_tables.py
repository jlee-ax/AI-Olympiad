"""Replay public table examples and missing-identity controls against one archived lesson.

Run from the repository with pandas installed. --round 1 retains the original
failure and exits 1. A round passes only if the actual student and teacher code
produce the expected identities, group statistics, and error outcomes.
"""
import argparse
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import tempfile

import pandas as pd


CASE = Path("reviews/week01-depth-20261118")
DATASET = "foundations_returns.csv"
LOOKUP = "foundations_boxes.csv"
TRANSFER = "foundations_returns_transfer.csv"
TEACHER = "week01_foundations_teacher.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def teacher_functions(path):
    fence = chr(96) * 3
    blocks = re.findall(fence + r"python\n(.*?)\n" + fence, path.read_text(encoding="utf-8"), re.S)
    scope = {"pd": pd}
    for block in blocks:
        module = ast.parse(block)
        functions = [stmt for stmt in module.body if isinstance(stmt, ast.FunctionDef)]
        if functions:
            module.body = functions
            exec(compile(module, str(path), "exec"), scope)
    return scope["attach_zones"], scope["summarize_returns"]


def clean_summary(table):
    result = {}
    for zone, row in table.iterrows():
        values = [row["rows"], row["observed"], row["sum_books"], row["mean_books"]]
        result[zone] = [None if pd.isna(x) else float(x) for x in values]
    return result


def identity_pairs(joined, id_column):
    return list(zip(joined[id_column].tolist(), joined["zone"].tolist()))


def run_checks(folder, paths, candidate):
    notebook = json.loads(candidate.read_text(encoding="utf-8"))
    cell = next(c for c in notebook["cells"] if c["id"] == "real-merge")
    code = compile("".join(cell["source"]), str(candidate) + ":real-merge", "exec")
    attach, summarize = teacher_functions(paths[TEACHER])
    frame = pd.read_csv(paths[TRANSFER])
    lookup = pd.read_csv(paths[LOOKUP])
    original = pd.read_csv(paths[DATASET])
    results = []

    def check(label, expected, actual):
        results.append({"case": label, "expected": expected, "actual": actual, "passed": actual == expected})

    def rejected(label, operation, kinds, *, missing_column=None, record_id=None, id_column="slip"):
        try:
            result = operation()
        except Exception as exc:
            found = {"type": type(exc).__name__, "message": str(exc)}
            passed = isinstance(exc, kinds) and (missing_column is None or exc.args == (missing_column,))
        else:
            found = {"returned_rows": len(result)}
            if record_id is not None:
                found["accepted_zone"] = result.loc[result[id_column] == record_id, "zone"].tolist()
            passed = False
        expected = {"reject": [kind.__name__ for kind in kinds]}
        if missing_column is not None:
            expected["missing_column"] = missing_column
        results.append({"case": label, "expected": expected, "actual": found, "passed": passed})

    def student_join(records, boxes):
        boxes.to_csv(folder / LOOKUP, index=False)
        scope = {"data_dir": folder, "pd": pd, "returns": records.copy()}
        with redirect_stdout(io.StringIO()):
            exec(code, scope)
        return scope["joined"]

    original_pairs = list(zip(["R1", "R2", "R3", "R4", "R5", "R6"],
                              ["East", "West", "East", "West", "West", "West"]))
    check("student.original_keys", original_pairs, identity_pairs(student_join(original, lookup), "record_id"))
    transfer_pairs = list(zip(["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"],
                              ["West", "East", "West", "East", "West", "West", "East", "West"]))
    joined = attach(frame, lookup)
    check("teacher.transfer_keys", transfer_pairs, identity_pairs(joined, "slip"))
    check("teacher.reversed_lookup", transfer_pairs, identity_pairs(attach(frame, lookup.iloc[::-1]), "slip"))

    # Independent figures from the public rows; the summary order is selected rows,
    # nonmissing closing counts, sum of those counts, and mean of the same counts.
    for threshold, selected_ids, west_summary in (
        (4, ["T1", "T3", "T4", "T6", "T8"], [4, 3, 13, 13 / 3]),
        (6, ["T4", "T6", "T8"], [2, 2, 6, 3]),
    ):
        selected, totals = summarize(joined, threshold)
        check(f"teacher.cutoff_{threshold}", {"ids": selected_ids, "zones": {"East": [1, 1, 0, 0], "West": west_summary}},
              {"ids": selected.slip.tolist(), "zones": clean_summary(totals)})

    no_closing = joined.copy()
    no_closing.loc[no_closing["slip"] == "T4", "closing_count"] = None
    _, totals = summarize(no_closing, 6)
    check("teacher.all_missing_group", [1, 0, None, None], clean_summary(totals).get("East"))
    empty, totals = summarize(joined, 100)
    check("teacher.empty_selection", [0, 0], [len(empty), len(totals)])

    rejected("teacher.missing_column", lambda: attach(frame.drop(columns="meal_count"), lookup),
             (KeyError,), missing_column="meal_count")
    duplicate = pd.concat([lookup, lookup.iloc[[0]]], ignore_index=True)
    rejected("teacher.duplicate_lookup", lambda: attach(frame, duplicate), (ValueError,))
    unknown = frame.copy()
    unknown.loc[unknown["slip"] == "T1", "station"] = "Z"
    rejected("teacher.unmatched_key", lambda: attach(unknown, lookup), (ValueError,), record_id="T1")
    blank = frame.copy()
    blank.loc[blank["slip"] == "T1", "station"] = None
    rejected("teacher.missing_left_key", lambda: attach(blank, lookup), (ValueError,), record_id="T1")

    # pandas matches null keys to one another. Neither blank identifies an actual box.
    missing_lookup = pd.concat([lookup, pd.DataFrame([{"box_id": None, "zone": "East"}])], ignore_index=True)
    rejected("teacher.missing_keys_on_both_sides", lambda: attach(blank, missing_lookup),
             (ValueError,), record_id="T1")
    missing_original = original.copy()
    missing_original.loc[missing_original["record_id"] == "R2", "box_id"] = None
    rejected("student.missing_keys_on_both_sides", lambda: student_join(missing_original, missing_lookup),
             (AssertionError, ValueError), record_id="R2", id_column="record_id")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--round", type=int, required=True, dest="number")
    args = parser.parse_args()
    root = args.root.resolve()
    folder = root / CASE / "rounds" / f"{args.number:04d}"
    record_file = folder / "round.json"
    record = json.loads(record_file.read_text(encoding="utf-8"))
    candidate = folder / "candidate.ipynb"
    if sha(candidate) != record["candidate_sha256"]:
        raise ValueError("Candidate differs from the archived round")
    paths = {}
    receipts = {}
    for item in record["companions"]:
        name = Path(item["path"]).name
        path = root / item["snapshot"]
        digest = sha(path)
        if digest != item["sha256"]:
            raise ValueError("Companion differs from the archived round: " + item["path"])
        paths[name] = path
        receipts[item["path"]] = {"snapshot": item["snapshot"], "sha256": digest}
    with tempfile.TemporaryDirectory(prefix="week01-public-tables-") as temp:
        results = run_checks(Path(temp), paths, candidate)
    passed = all(item["passed"] for item in results)
    report = {"round": args.number, "round_sha256": sha(record_file),
              "candidate_sha256": sha(candidate), "companions": receipts,
              "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
              "checks": results, "status": "passed" if passed else "failed"}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
