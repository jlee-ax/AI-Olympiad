"""Independent, version-bound checks of the Week 1 dependency repair and its arithmetic.

Run from the repository with a full checkout. The checked old route assigned these
classification sections as required homework. Its data loader remains usable.
"""
from contextlib import ExitStack, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
from unittest.mock import patch

import numpy as np
import pandas as pd


BASELINE = "e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352"
DIRECT = Path("lessons/week01")
PREFIX = "week01_"


class LaterToolReached(Exception):
    pass


def cells(name, original=False):
    path = DIRECT / (PREFIX + name + ".ipynb")
    raw = subprocess.check_output(["git", "show", f"{BASELINE}:{path.as_posix()}"]) if original else path.read_bytes()
    return json.loads(raw)["cells"]


def run_cell(cell, state):
    with redirect_stdout(StringIO()):
        exec(compile("".join(cell["source"]), cell["id"], "exec"), state)


def selected(name, ids):
    notebook = {c["id"]: c for c in cells(name)}
    state = {}
    for identifier in ids:
        run_cell(notebook[identifier], state)
    return state


def required_classifier(original):
    state = {}
    for cell in cells("problem_pipeline", original):
        if cell["id"] == "bb177697":
            break
        if cell["cell_type"] == "code":
            try:
                run_cell(cell, state)
            except LaterToolReached:
                if original and cell["id"] == "1566ce2a":
                    return cell["id"]
                raise
    if original:
        raise AssertionError("The frozen predecessor unexpectedly finished its required classifier arithmetic")
    assert state["val_predictions"].tolist() == [-1, 1, 1, 1]
    assert state["accuracy"] == 0.75
    return state


def check_arithmetic(integrated, companion):
    data = pd.DataFrame({
        "x": [0, 6, 4, 10], "y": [np.nan, 2, 6, 10], "label": [0, -3, 0, -3],
    }, index=[31, 2, 97, 5])
    holdout = pd.DataFrame({"y": [6, np.nan, 6], "x": [5, 7, 5.5]}, index=["tie", "missing", "border"])
    columns = ["x", "y"]

    def classify(frame):
        means_a = integrated["observed_column_means"](frame[columns])
        labels_a, centers_a = integrated["class_means"](frame[columns].fillna(means_a), frame["label"])
        predictions_a = [
            int(integrated["nearest_class"](row, labels_a, centers_a))
            for row in holdout[columns].fillna(means_a).to_numpy()
        ]
        means_b, centers_b = companion["training_averages"](frame, columns)
        distances_b = companion["squared_distances"](holdout, means_b, centers_b)
        assert labels_a.tolist() == centers_b.index.tolist() == [-3, 0]
        np.testing.assert_allclose(centers_a, centers_b)
        np.testing.assert_allclose(means_a, means_b)
        assert distances_b.index.tolist() == holdout.index.tolist()
        assert predictions_a == list(distances_b.idxmin(axis=1))
        return list(means_b), centers_b.to_numpy().tolist(), distances_b.to_numpy().tolist(), predictions_a

    measured = classify(data)
    expected = ([5, 6], [[8, 6], [2, 6]], [[9, 9], [1, 25], [6.25, 12.25]], [-3, -3, -3])
    assert measured == expected, (measured, expected)
    assert classify(data.iloc[[2, 1, 3, 0]]) == expected

    changed = data.copy()
    changed.loc[5, "x"] = 14
    updated = classify(changed)
    assert updated[0] == [6, 6]
    assert updated[1] == [[10, 6], [2, 6]]
    assert updated[3][-1] == 0
    score_before = np.mean(np.array(measured[3]) == [-3, -3, -3])
    score_after = np.mean(np.array(measured[3]) == [-3, 0, -3])
    assert score_before == 1 and score_after == 2 / 3

    unseen = data.copy()
    unseen["y"] = np.nan
    for compute in (lambda: integrated["observed_column_means"](unseen[columns]),
                    lambda: companion["training_averages"](unseen, columns)):
        try:
            compute()
        except ValueError:
            continue
        raise AssertionError("A mean cannot be inferred for an entirely missing training feature")
    return {"training_means": measured[0], "centers_in_label_order_minus3_then_0": measured[1],
            "distances": measured[2], "predictions": measured[3],
            "changed_training_last_prediction": updated[3][-1],
            "heldout_key_only_correct_counts": [3, 2]}


def main():
    with ExitStack() as guard:
        for path in ("sklearn.impute.SimpleImputer", "sklearn.neighbors.NearestCentroid", "sklearn.pipeline.Pipeline"):
            guard.enter_context(patch(path, side_effect=LaterToolReached(path)))
        rejected_cell = required_classifier(original=True)
        companion = required_classifier(original=False)
        foundation = selected("python_tables", ["3468f4e4"])
        assert foundation["H"].tolist() == [[0, 15], [13, 15], [14, 16]]
        integrated = selected("integrated", ["484f22ba", "deep-leaf-grid", "4d60619c", "ae89f4b6", "8e809e64"])
        assert list(integrated["predictions"]) == [1, 0, 0]
        numeric = check_arithmetic(integrated, companion)
    print(json.dumps({"old_required_model_call": rejected_cell,
                      "current_required_worked_accuracy": companion["accuracy"],
                      "original_digits_feature_landing": foundation["H"].tolist(),
                      "new_independent_input": numeric}, sort_keys=True))


if __name__ == "__main__":
    main()
