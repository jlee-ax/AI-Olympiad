"""Check that the archived teacher solution identifies records with unusable box keys.

These two follow-up controls are independent of the thirteen original public
table controls. Run at repository root with --round N and pandas installed.
"""
import argparse
import csv
import json
from pathlib import Path
import platform
import re
import tempfile

import pandas as pd

from check_public_tables import CASE, LOOKUP, TEACHER, TRANSFER, sha, teacher_functions


def report_outcome(attach, frame, lookup, expected_ids):
    try:
        result = attach(frame, lookup)
    except (ValueError, KeyError, TypeError) as exc:
        message = str(exc)
        ids = [rid for rid in frame["slip"] if re.search(r"(?<!\w)" + re.escape(rid) + r"(?!\w)", message)]
        return {"passed": set(ids) == set(expected_ids), "expected_record_ids": expected_ids,
                "actual": {"type": type(exc).__name__, "message": message, "reported_record_ids": ids}}
    rows = result.loc[result["slip"].isin(expected_ids), ["slip", "zone"]].to_dict("records")
    return {"passed": False, "expected_record_ids": expected_ids,
            "actual": {"type": "returned table", "affected_rows": rows}}


def all_blank_csv(path, destination):
    with path.open(encoding="utf-8", newline="") as infile, destination.open("w", encoding="utf-8", newline="") as output:
        source = csv.DictReader(infile)
        writer = csv.DictWriter(output, fieldnames=source.fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in source:
            row["station"] = ""
            writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--round", type=int, required=True, dest="number")
    args = parser.parse_args()
    root = args.root.resolve()
    folder = root / CASE / "rounds" / f"{args.number:04d}"
    rpath, notebook = folder / "round.json", folder / "candidate.ipynb"
    record = json.loads(rpath.read_text(encoding="utf-8"))
    if sha(notebook) != record["candidate_sha256"]:
        raise ValueError("Candidate differs from the archived round")
    selected = {}
    inputs = {}
    for ref in record["companions"]:
        name = Path(ref["path"]).name
        if name not in {TRANSFER, LOOKUP, TEACHER}:
            continue
        path = root / ref["snapshot"]
        if sha(path) != ref["sha256"]:
            raise ValueError("Companion differs from the archived round: " + name)
        selected[name] = path
        inputs[ref["path"]] = {"snapshot": ref["snapshot"], "sha256": ref["sha256"]}
    attach, _ = teacher_functions(selected[TEACHER])
    lookup = pd.read_csv(selected[LOOKUP])

    with tempfile.TemporaryDirectory(prefix="week01-key-forms-") as work:
        csv_path = Path(work) / "all_station_blank.csv"
        all_blank_csv(selected[TRANSFER], csv_path)
        absent = pd.read_csv(csv_path)
        a = report_outcome(attach, absent, lookup, absent["slip"].tolist())
        a.update(case="all_station_fields_blank_in_physical_csv", station_dtype=str(absent["station"].dtype),
                 lookup_key_dtype=str(lookup["box_id"].dtype), derived_csv_sha256=sha(csv_path),
                 rows=len(absent), missing_station_count=int(absent["station"].isna().sum()))

    edited = pd.read_csv(selected[TRANSFER])
    edited.loc[edited["slip"] == "T1", "station"] = ""
    both_empty = pd.concat([lookup, pd.DataFrame([{"box_id": "", "zone": "East"}])], ignore_index=True)
    b = report_outcome(attach, edited, both_empty, ["T1"])
    b.update(case="empty_strings_in_both_key_columns_after_edit", station_dtype=str(edited["station"].dtype),
             lookup_key_dtype=str(both_empty["box_id"].dtype), assigned_key="", assigned_zone="East")
    passed = a["passed"] and b["passed"]
    result = {"round": args.number, "round_sha256": sha(rpath), "candidate_sha256": sha(notebook),
              "inputs": inputs, "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
              "checks": [a, b], "status": "passed" if passed else "failed"}
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
