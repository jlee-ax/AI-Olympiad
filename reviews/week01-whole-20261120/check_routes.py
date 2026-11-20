"""Follow the integrated textbook, measure its source data and replay numerical decisions on changed inputs."""
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
    "tables-csv": "02c6cde1",
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
    table = prepared["source_table"]
    names = prepared["feature_names"]
    digits = prepared["digits"]
    assert digits.data.shape == (1797, 64)
    assert (digits.images[:, 2, 2] == table[names[0]]).all()
    assert (digits.images[:, 4, 2] == table[names[1]]).all()
    assert digits.data.iloc[0, 18] == digits.images[0, 2, 2] == 15
    assert table.loc[[10, 20, 26], names].to_numpy().tolist() == [[16, 16]] * 3
    assert table.loc[[10, 20, 26], "digit"].tolist() == [0, 0, 6]
    assert np.sum((digits.images[10] - digits.images[26]) ** 2) == 1756

    arithmetic = prepared.copy()
    run_cell("d942743f", arithmetic)
    average = arithmetic["observed_mean"]
    assert average([0, None, -2, 8, np.nan]) == 2 and average([None]) is None
    assert table.loc[10, names[0]] == 16
    run_cell("9d537595", arithmetic)
    run_cell("32ed7e09", arithmetic)
    assert arithmetic["reshaped"][0].tolist() == [15, 8, 3]
    assert arithmetic["transposed"][0].tolist() == [15, 3, 0]
    run_cell("similarity-matrix-code", arithmetic)
    np.testing.assert_allclose(arithmetic["dot_scores"], [[4, 2, 2], [0, 1, 2]])
    np.testing.assert_allclose(arithmetic["cosine_scores"], [[2**-0.5, 1, 2**-0.5], [0, 2**-0.5, 1]])

    def fit(frame):
        ns = {**prepared, "source_table": frame.copy()}
        run_cell("4d60619c", ns)
        run_cell("ae89f4b6", ns)
        return ns

    baseline = fit(table)
    changed_input = table.copy()
    changed_input.loc[21, names] = [14, 12]
    extra = table.iloc[[0]].copy()
    extra.index = pd.Index([9001], name=table.index.name)
    extra.loc[9001, names] = [1, 16]
    reordered = fit(pd.concat([extra, table.iloc[::-1]]))
    for candidate in (baseline, reordered, fit(changed_input)):
        assert candidate["training"].index.tolist() == [0, 1, 10, 11]
        assert candidate["validation"].index.tolist() == [21, 70, 72]
        np.testing.assert_allclose(candidate["fill"].statistics_, [6, 9.25])
        np.testing.assert_allclose(candidate["model"].centroids_, [[10.5, 12], [1.5, 6.5]])
    run_cell("8e809e64", reordered)
    keys = ["image_index", "prediction"]
    assert reordered["result"][keys].values.tolist() == [[21, 1], [70, 0], [72, 0]]
    assert reordered["result"]["correct"].tolist() == [True, False, True]
    changed_label = table.copy()
    changed_label.loc[70, "digit"] = 0
    relabeled = fit(changed_label)
    run_cell("8e809e64", relabeled)
    np.testing.assert_array_equal(relabeled["predictions"], reordered["predictions"])
    assert relabeled["result"]["correct"].all()
    run_cell("3512f7de", reordered)
    assert reordered["model"].predict([[7, 9]]).item() == 0
    assert reordered["changed_model"].predict([[7, 9]]).item() == 1
    # Reordering either working table must preserve the published image/prediction pairs.
    reordered["validation"] = reordered["validation"].iloc[::-1]
    reordered["result"] = reordered["result"].iloc[::-1]
    run_cell("f40633df", reordered)
    exported = reordered["checked"][keys].values.tolist()
    assert exported == [[21, 1], [70, 0], [72, 0]]
    predicted = reordered["result"]
    for invalid in (predicted.iloc[:1], pd.concat([predicted, predicted.iloc[:1]]),
                    predicted.assign(image_index=[72, 70, 9001])):
        try:
            run_cell("f40633df", {**reordered, "result": invalid})
        except ValueError:
            continue
        raise AssertionError("The export accepted a missing, repeated or foreign image index")
    for invalid, error in ((table.drop(index=10), KeyError),
                           (pd.concat([table, table.loc[[1]]]), ValueError)):
        try:
            fit(invalid)
        except error:
            continue
        raise AssertionError(f"Expected {error.__name__} before model fitting")
    return {"direct_student_entries": check_landings(lesson, raw),
            "real_digits_rows_and_features": list(digits.data.shape),
            "equal_two_features_different_labels": [10, 26],
            "full_feature_squared_distance": 1756,
            "training_means_after_independent_changes": [6, 9.25],
            "trained_centers": reordered["model"].centroids_.tolist(),
            "export_after_two_working_tables_move": exported,
            "invalid_data_and_prediction_identity": "rejected",
            "changing_held_out_label": "predictions fixed, measured accuracy changed",
            "training_counterfactual_probe": [0, 1]}


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
