"""Replay the student recovery notebook and its return to the public main CSV exercise.

Run with a fresh Python process and pandas installed. The worked cells run verbatim.
The final recovery and two main checkpoint responses are this auditor's own answers.
"""
import argparse
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import platform
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = Path("lessons/week01")
ROUND_CASE = Path("reviews/week01-depth-20261118/rounds")
SUPPLEMENT_NAME = "week01_foundations_repair.ipynb"
MAIN_NAME = "week01_foundations.ipynb"
SUPPLEMENT_SHA = "8b0f1b4e672adb8214524c243eade54024e888d710a7875def09cc4d7b527df9"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_cells(path):
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def body(cell):
    return "".join(cell["source"])


def source_by_id(cells, name):
    return body(next(cell for cell in cells if cell["id"] == name))


def as_values(frame, name, value):
    return [[key, None if pd.isna(item) else str(item)]
            for key, item in frame[[name, value]].itertuples(index=False, name=None)]


def prepare_and_join(left, right, name, left_key, right_key, cleaner):
    left = left.assign(**{left_key: cleaner(left[left_key])})
    right = right.assign(**{right_key: cleaner(right[right_key])})
    known = right.loc[right[right_key].notna()]
    return left.merge(known, left_on=left_key, right_on=right_key, how="left",
                      indicator=True, validate="many_to_one")


def run(round_number, supplement):
    round_dir = ROOT / ROUND_CASE / f"{round_number:04d}"
    record_path = round_dir / "round.json"
    main = round_dir / "candidate.ipynb"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if sha(main) != record["candidate_sha256"] or sha(supplement) != SUPPLEMENT_SHA:
        raise ValueError("Student main or designated public supplement bytes changed")
    inputs = {p["path"]: p for p in record["companions"]}
    data_paths = {}
    for name in ("foundations_returns_transfer.csv", "foundations_boxes.csv"):
        entry = inputs[str(PUBLIC / "data" / name)]
        archived = ROOT / entry["snapshot"]
        if sha(archived) != entry["sha256"]:
            raise ValueError("Changed public input: " + name)
        data_paths[name] = archived
    public_data = {n: {"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for n, p in data_paths.items()}

    main_cells, repair_cells = read_cells(main), read_cells(supplement)
    main_anchor = source_by_id(main_cells, "transfer-faults")
    return_prompt = source_by_id(repair_cells, "repair-return")
    checks = []

    def check(name, expected, found):
        checks.append({"case": name, "expected": expected, "actual": found, "passed": found == expected})

    main_links = re.findall(r"\]\(([^)]+)\)", main_anchor)
    return_links = re.findall(r"\]\(([^)]+)\)", return_prompt)
    check("links.out_from_checkpoint", [SUPPLEMENT_NAME], main_links)
    check("links.return_to_unique_original_checkpoint", [MAIN_NAME + "#merge-recheck", "transfer-faults"],
          return_links + [c["id"] for c in main_cells if '<a id="merge-recheck">' in body(c)])
    check("links.failure_trigger_and_different_station_on_return", [True, True, True], [
        "어느 이름에서 어긋났는지 찾지 못한 경우" in main_anchor,
        "다른 반납함" in main_anchor, "다른 반납함" in return_prompt])

    namespace = {"__name__": "__main__"}
    execution = []
    for cell in repair_cells:
        if cell["cell_type"] == "code":
            output = io.StringIO()
            with redirect_stdout(output):
                exec(compile(body(cell), f"{SUPPLEMENT_NAME}:{cell['id']}", "exec"), namespace)
            execution.append({"cell": cell["id"], "stdout": output.getvalue().strip()})
    check("delivered.code_cell_order", ["repair-read", "repair-duplicates", "repair-match", "repair-fresh"],
          [e["cell"] for e in execution])
    # This value is the notebook's own worked result. The key, area and visit are checked separately.
    known = namespace["known"]
    duplicates = known[known["code"].duplicated(keep=False)]
    check("worked.both_conflicting_lookup_rows", [["B1", "West"], ["B1", "North"]], as_values(duplicates, "code", "area"))
    check("worked.affected_visit_before_correction", ["M21"],
          namespace["left"].loc[namespace["left"]["place"].isin(duplicates["code"]), "ticket"].tolist())
    paired = namespace["paired"]
    check("worked.rows_and_corrected_areas", [["M14", "East"], ["M07", None], ["M21", "West"], ["M12", None]],
          as_values(paired, "ticket", "area"))
    check("worked.actual_unlinked_identifiers", ["M07", "M12"], namespace["unlinked"])

    fresh = namespace["fresh_visits"]
    places = namespace["fresh_places"]
    clean = namespace["text_id"]
    codes = places.assign(code=clean(places["code"])).dropna(subset=["code"])
    ambiguous = codes.loc[codes["code"].duplicated(keep=False), "code"].unique().tolist()
    check("independent.duplicate_and_affected_visit_before_correction", [["G2"], ["J9"]],
          [ambiguous, fresh.loc[clean(fresh["place"]).isin(ambiguous), "ticket"].tolist()])
    try:
        prepare_and_join(fresh, places, "ticket", "place", "code", clean)
    except pd.errors.MergeError as exc:
        duplicate_result = type(exc).__name__
    else:
        duplicate_result = "accepted"
    check("independent.ambiguous_lookup_rejected", "MergeError", duplicate_result)
    # Independently transcribe the two records explicitly verified by the custodian in repair-return.
    confirmed = pd.DataFrame({"code": ["G1", "G2"], "area": ["North", "South"]})
    repaired = prepare_and_join(fresh, confirmed, "ticket", "place", "code", clean)
    check("independent.corrected_areas_and_retained_visits", [["J6", "North"], ["J2", None], ["J9", "South"]],
          as_values(repaired, "ticket", "area"))
    check("independent.blank_unlinked_and_original_count", [["J2"], 3], [
        repaired.loc[repaired["_merge"] == "left_only", "ticket"].tolist(), len(repaired)])

    journal = pd.read_csv(data_paths["foundations_returns_transfer.csv"])
    boxes = pd.read_csv(data_paths["foundations_boxes.csv"])
    restored = prepare_and_join(journal, boxes, "slip", "station", "box_id", clean)
    expected_ids = [f"T{i}" for i in range(1, 9)]
    check("main.normal_before_and_after", [expected_ids, 8, True, True], [
        restored["slip"].tolist(), len(restored), bool(restored["slip"].is_unique),
        bool(restored["_merge"].eq("both").all())])
    for station, expected in (("A", ["T2", "T4", "T7"]), ("B", ["T1", "T5"])):
        damaged = boxes[boxes["box_id"] != station]
        audit = prepare_and_join(journal, damaged, "slip", "station", "box_id", clean)
        check("main.station_" + station + "_removed_real_ids", [expected, expected_ids],
              [audit.loc[audit["_merge"] == "left_only", "slip"].tolist(), audit["slip"].tolist()])
    again = prepare_and_join(journal, boxes, "slip", "station", "box_id", clean)
    check("main.restoration_after_distinct_second_checkpoint", [[rid, zone] for rid, zone in zip(
        expected_ids, ["West", "East", "West", "East", "West", "West", "East", "West"])],
        as_values(again, "slip", "zone"))
    passed = all(c["passed"] for c in checks)
    return {"round": round_number, "round_sha256": sha(record_path), "candidate_sha256": sha(main),
            "supplement": {"path": str(supplement.relative_to(ROOT)), "sha256": sha(supplement)},
            "public_data": public_data, "runtime": {"python": platform.python_version(), "pandas": pd.__version__},
            "execution": execution, "checks": checks, "status": "passed" if passed else "failed",
            "scope": "Fresh Python process executes the delivered four code cells in order. The auditor supplied the independent fresh solution and the return answers on the original CSVs. Link targets were resolved in the actual notebook sources. Learner work, timing and a browser click were not observed."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--supplement", type=Path, default=ROOT / PUBLIC / SUPPLEMENT_NAME)
    args = parser.parse_args()
    result = run(args.round, args.supplement.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    raise SystemExit(result["status"] != "passed")
