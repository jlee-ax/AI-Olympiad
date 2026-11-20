"""Test the material's two plant tables and replay the published training cells on changed rows."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import pandas as pd


DEFAULT_LESSON = Path(__file__).resolve().parents[2] / "lessons" / "week01"

# Follow the published link up to the first worked decision at each landing.
LANDINGS = {
    "tables-paper": None,
    "tables-python": "81129230",
    "tables-features": "3468f4e4",
    "bridge-axes": "5ebb633b",
    "bridge-scores": "retrieval-norm-code",
    "pipeline-contract": "622155d2",
    "pipeline-submit": "order-by-hand",
}


def run_landing(lesson, target, anchor):
    """Start this branch in a new process, without any preceding notebook cells."""
    from ipykernel.inprocess.manager import InProcessKernelManager
    from IPython.utils.capture import capture_output

    cells = json.loads((lesson / target).read_text(encoding="utf-8"))["cells"]
    matches = [i for i, cell in enumerate(cells) if cell["cell_type"] == "markdown"
               and f'id="{anchor}"' in "".join(cell["source"])]
    assert len(matches) == 1, (target, anchor, matches)
    start = matches[0]
    if LANDINGS[anchor] is None:
        prompt = "".join(cells[start]["source"])
        assert all(kind in prompt for kind in ("선택형 1", "선택형 2", "서술형"))
        return []
    end = next(i for i in range(start, len(cells)) if cells[i]["id"] == LANDINGS[anchor])
    executed = []
    manager = InProcessKernelManager()
    manager.start_kernel()
    try:
        with contextlib.chdir(lesson), capture_output():
            for cell in cells[start:end + 1]:
                if cell["cell_type"] == "code":
                    result = manager.kernel.shell.run_cell("".join(cell["source"]), store_history=False, silent=True)
                    result.raise_error()
                    executed.append(cell["id"])
        return executed
    finally:
        manager.shutdown_kernel()


def check_landings(lesson, notebook):
    links = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] == "markdown":
            for target, anchor in re.findall(r"\]\((week01_[a-z_]+\.ipynb)#([a-z0-9-]+)\)", "".join(cell["source"])):
                assert links.setdefault(anchor, target) == target
    assert set(LANDINGS) <= set(links), sorted(set(LANDINGS) - set(links))
    result = {}
    for anchor in LANDINGS:
        target = links[anchor]
        child = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--lesson", str(lesson.resolve()),
                                "--landing", target, anchor], capture_output=True, text=True)
        if child.returncode:
            raise RuntimeError(f"Fresh entry failed at {target}#{anchor}\n{child.stderr}")
        result[anchor] = json.loads(child.stdout)
    return result


def check(lesson):
    raw = json.loads((lesson / "week01_integrated.ipynb").read_text(encoding="utf-8"))
    code = {cell["id"]: "".join(cell["source"]) for cell in raw["cells"] if cell["cell_type"] == "code"}

    def run_cell(identifier, namespace):
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(code[identifier], f"integrated/{identifier}", "exec"), namespace)

    prepared = {}
    run_cell("484f22ba", prepared)
    run_cell("deep-leaf-grid", prepared)
    run_cell("deep-count-code", prepared)
    plants = prepared["plants"]
    file_plants = pd.read_csv(lesson / "data" / "week1_plants.csv")
    core_table = plants.set_index("pot_id", verify_integrity=True)
    companion_table = file_plants.set_index("pot_id", verify_integrity=True)
    assert set(core_table.index) == set(companion_table.index)
    assert core_table.loc["P05", ["water_ml", "height_cm"]].tolist() == [10, 14]
    assert companion_table.loc["P05", ["water_ml", "height_cm"]].tolist() == [20, 10]
    # A shape/ID-only check would accept both and change P05's example class.
    assert bool(core_table.at["P05", "height_cm"] >= 12) != bool(companion_table.at["P05", "height_cm"] >= 12)

    def fit(frame):
        ns = {**prepared, "plants": frame.copy()}
        run_cell("4d60619c", ns)
        run_cell("ae89f4b6", ns)
        return ns

    baseline = fit(plants)
    nonpositional = plants.iloc[[5, 1, 4, 3, 2, 0]]
    reordered = fit(nonpositional)
    unlisted = plants.iloc[[0]].assign(pot_id="P99", water_ml=700, height_cm=200)
    with_extra = fit(pd.concat([unlisted, nonpositional], ignore_index=True))
    changed_held_out = plants.copy()
    changed_held_out.loc[changed_held_out["pot_id"] == "P05", "water_ml"] = 800
    for candidate in (baseline, reordered, with_extra, fit(changed_held_out)):
        assert candidate["training"]["pot_id"].tolist() == ["P01", "P02", "P03", "P04"]
        assert candidate["validation"]["pot_id"].tolist() == ["P05", "P06"]
        np.testing.assert_allclose(candidate["fill"].statistics_, [20])
        np.testing.assert_allclose(candidate["model"].centroids_, [[1, 0.5], [3, 2.5]])
    run_cell("8e809e64", reordered)
    assert reordered["result"][["pot_id", "prediction"]].values.tolist() == [["P05", 0], ["P06", 1]]
    # The statement's output order survives subsequent changes to either working table.
    reordered["validation"] = reordered["validation"].iloc[::-1].reset_index(drop=True)
    reordered["result"] = reordered["result"].iloc[::-1].reset_index(drop=True)
    run_cell("f40633df", reordered)
    exported = reordered["checked"][["pot_id", "prediction"]].values.tolist()
    assert exported == [["P05", 0], ["P06", 1]], f"The exported ID order or pairing changed: {exported}"
    predictions = reordered["result"]
    for invalid in (predictions.iloc[:1], pd.concat([predictions, predictions.iloc[:1]]),
                    predictions.assign(pot_id=["P99", "P05"])):
        try:
            run_cell("f40633df", {**reordered, "result": invalid})
        except ValueError:
            continue
        raise AssertionError("The export accepted a missing, repeated or unregistered prediction ID")
    for invalid, expected in (
        (plants[plants["pot_id"] != "P03"], KeyError),
        (pd.concat([plants, plants[plants["pot_id"] == "P02"]]), ValueError),
    ):
        try:
            fit(invalid)
        except expected:
            continue
        raise AssertionError(f"Expected {expected.__name__} before model fitting")
    return {"direct_student_entries": check_landings(lesson, raw),
            "data_sources": ["integrated plant literal", "data/week1_plants.csv"],
            "shared_pot_ids": len(core_table), "P05_classes_at_12_cm": [1, 0],
            "export_after_two_working_tables_move": exported,
            "missing_duplicate_or_foreign_prediction_id": "rejected",
            "training_water_fill_ml": float(reordered["fill"].statistics_[0]),
            "missing_training_id": "rejected", "duplicate_pot_id": "rejected",
            "unlisted_row_and_changed_validation_reading": "training parameters preserved"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", type=Path, default=DEFAULT_LESSON)
    parser.add_argument("--landing", nargs=2, metavar=("NOTEBOOK", "ANCHOR"))
    args = parser.parse_args()
    if args.landing:
        target, anchor = args.landing
        if anchor not in LANDINGS or not re.fullmatch(r"week01_[a-z_]+\.ipynb", target):
            parser.error("Unknown lesson landing")
        result = run_landing(args.lesson.resolve(), target, anchor)
    else:
        result = check(args.lesson)
    print(json.dumps(result, ensure_ascii=False, indent=2))
