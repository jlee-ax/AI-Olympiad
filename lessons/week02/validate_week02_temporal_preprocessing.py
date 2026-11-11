#!/usr/bin/env python3
"""Execute and check the Week 2 supplement without a Jupyter socket."""
import argparse
import ast
import base64
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import sys

if not __debug__:
    raise RuntimeError("Optimized Python disables QA assertions; run without -O/PYTHONOPTIMIZE.")

import IPython
from IPython.core.interactiveshell import InteractiveShell
import matplotlib
import nbformat
import numpy as np
import pandas as pd
import sklearn
from packaging.version import Version
from sklearn.base import clone
from sklearn.metrics import roc_curve
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "week02_temporal_preprocessing.ipynb"
HTML = ROOT / "week02_temporal_preprocessing.html"
GUIDE = ROOT / "week02_temporal_preprocessing_teacher.md"
EXERCISE_TEMPLATE = "# 새 자료를 직접 입력하고 코드를 작성하세요."


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_report_path(path):
    """Refuse every existing target and symlink before executing notebook code."""
    path = Path(os.path.abspath(path))
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("Report path must not contain a symlink: " + str(component))
    if os.path.lexists(path):
        raise FileExistsError("Report must use a NEW file path: " + str(path))
    if not path.parent.is_dir():
        raise ValueError("Report parent must be an existing directory: " + str(path.parent))
    return path


def write_new_report(path, rendered):
    # Check again because another actor may have created the target while QA ran.
    path = new_report_path(path)
    owned = None
    try:
        with path.open("x", encoding="utf-8") as stream:
            owned = os.fstat(stream.fileno())
            stream.write(rendered)
    except BaseException:
        if owned is not None:
            try:
                current = path.lstat()
                if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                    path.unlink()
            except FileNotFoundError:
                pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=Path, help="exclusively create the JSON record at a NEW file path")
    args = parser.parse_args(argv)
    output = new_report_path(args.write) if args.write is not None else None
    inputs = {path: path.read_bytes() for path in (NOTEBOOK, HTML, GUIDE)}
    nb = nbformat.reads(inputs[NOTEBOOK].decode("utf-8"), as_version=4)
    nbformat.validate(nb)
    assert Version(sklearn.__version__) >= Version("1.3")
    exercises = [c for c in nb.cells if "independent-exercise" in c.metadata.get("tags", [])]
    if len(exercises) != 1:
        raise ValueError("Exactly one independent-exercise cell is required.")
    exercise = exercises[0]
    if (exercise.cell_type != "code" or exercise.source.strip() != EXERCISE_TEMPLATE
            or ast.parse(exercise.source).body):
        raise ValueError("Only the original blank exercise comment template is allowed.")
    if exercise.execution_count is not None or exercise.outputs:
        raise ValueError("Exercise must be unexecuted and have no saved outputs.")
    examples = [c for c in nb.cells if c.cell_type == "code" and c is not exercises[0]]
    assert all(c.execution_count is not None for c in examples)
    assert not any(o.output_type == "error" for c in examples for o in c.outputs)
    images = [o.data["image/png"] for c in examples for o in c.outputs
              if o.output_type in ("display_data", "execute_result") and "image/png" in o.data]
    assert len(images) == 1
    assert base64.b64decode(images[0]).startswith(bytes.fromhex("89504e470d0a1a0a"))
    text = "\n".join(c.source for c in nb.cells)
    assert not re.search(r"\d+\s*(?:분|시간)", text)
    html = inputs[HTML].decode("utf-8")
    assert "data:image/png;base64," in html
    for marker in ("과거 기록에서 예측까지", "새 입력으로 직접 확인하기",
                   "Validation ROC", "OneHotEncoder"):
        assert marker in html

    shell = InteractiveShell.instance()
    stdout = io.StringIO()
    stderr = io.StringIO()
    code_indices = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        code_indices.append(i)
        cell_stdout = io.StringIO()
        with contextlib.redirect_stdout(cell_stdout), contextlib.redirect_stderr(stderr):
            result = shell.run_cell(cell.source, store_history=False)
        if result.error_before_exec:
            raise RuntimeError(f"cell {i}: {result.error_before_exec}")
        if result.error_in_exec:
            raise RuntimeError(f"cell {i}: {result.error_in_exec}")
        printed = cell_stdout.getvalue()
        stdout.write(printed)
        stored = "".join(o.text for o in cell.outputs
                         if o.output_type == "stream" and o.name == "stdout")
        assert printed == stored, f"stored stream differs from fresh execution at cell {i}"
    ns = shell.user_ns
    make = ns["make_features"]
    cases = []

    def passed(name):
        cases.append(name)

    # Original worked example, independently specified numerical expectations.
    expected_recent = [8, 12, 1, 7]
    assert np.allclose(ns["val_x"].recent, expected_recent)
    assert np.isclose(ns["train_x"].loc["a4", "mean3"], 4)
    assert np.isclose(ns["train_x"].loc["a5", "std3"], np.sqrt(8/9))
    assert np.allclose(ns["scores"], [1.5, 2.5, 0, 1.5])
    assert np.allclose(ns["fpr"], [0, .5, .5, 1])
    assert np.allclose(ns["tpr"], [0, 0, 1, 1])
    assert np.allclose(ns["ax"].lines[0].get_xdata(), ns["fpr"])
    assert np.allclose(ns["ax"].lines[0].get_ydata(), ns["tpr"])
    passed("worked example, tie, ROC points and plotted axes")

    # Unsorted records, strict past, group isolation, missing history, duplicates.
    raw = pd.DataFrame([
        ("X", 1, 99.), ("Z", 3, 9.), ("Z", 2, np.nan), ("Z", 1, 3.),
        ("W", 2, np.nan),
    ], columns=["unit", "time", "reading"])
    targets = pd.DataFrame([
        ("z3", "Z", 3, "red", 1), ("w3", "W", 3, "blue", -1),
    ], columns=["id", "unit", "time", "kind", "label"])
    x = make(raw, targets)
    assert x.loc["z3", "recent"] == 3 and pd.isna(x.loc["z3", "mean3"])
    assert pd.isna(x.loc["w3", "recent"])
    changed = raw.copy()
    changed.loc[(changed.unit == "Z") & (changed.time == 3), "reading"] = 10000
    changed.loc[(changed.unit == "X") & (changed.time == 1), "reading"] = -10000
    pd.testing.assert_frame_equal(x, make(changed, targets))
    try:
        make(pd.concat([raw, raw.iloc[[0]]], ignore_index=True), targets)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate unit/time did not fail")
    passed("unsorted past-only records, cross-group and future mutations, duplicate rejection")

    # Independent exercise: all values differ from the worked records.
    r = pd.DataFrame([
        ("M",1,5.),("M",2,7.),("M",3,9.),("M",4,np.nan),
        ("N",1,np.nan),("N",2,np.nan),("N",3,np.nan),("N",4,1.),
        ("P",1,7.),("P",2,9.),("P",3,11.),("P",4,np.nan),("P",6,17.),
        ("Q",1,np.nan),("Q",2,0.),("Q",3,np.nan),("Q",4,np.nan),("Q",6,11.),
    ], columns=["unit", "time", "reading"]).sample(frac=1, random_state=9)
    tr = pd.DataFrame([
        ("m4","M",4,"gold",-1),("m5","M",5,"gold",1),
        ("n4","N",4,"silver",-1),("n5","N",5,"silver",1),
    ], columns=targets.columns)
    va = pd.DataFrame([
        ("p6","P",6,"bronze",1),("p7","P",7,"bronze",-1),
        ("q6","Q",6,"gold",1),("q7","Q",7,"gold",-1),
    ], columns=targets.columns)
    assert set(tr.unit).isdisjoint(va.unit) and tr.time.max() < va.time.min()
    tx, vx = make(r, tr), make(r, va)
    assert np.allclose(tx.recent, [9,9,np.nan,1], equal_nan=True)
    assert np.allclose(vx.recent, [11,17,0,11])
    assert np.allclose([tx.loc["m4","mean3"], tx.loc["m4","std3"]], [7,np.sqrt(8/3)])
    assert np.allclose([vx.loc["p6","mean3"], vx.loc["p6","std3"]], [9,np.sqrt(8/3)])
    pipe = clone(ns["transformer"])
    pipe.fit(tx)
    encode = lambda x: pd.DataFrame(pipe.transform(x), index=x.index,
                                     columns=pipe.get_feature_names_out())
    enc = encode(vx)
    numeric = pipe.named_transformers_["num"]
    imputer, scale = numeric.named_steps["median"], numeric.named_steps["range"]
    cat = pipe.named_transformers_["cat"]
    assert imputer.statistics_[0] == 9 and scale.data_min_[0] == 1 and scale.data_max_[0] == 9
    assert np.allclose(enc["num__recent"], [5/4, 2, -1/8, 5/4])
    assert cat.categories_[0].tolist() == ["gold", "silver"]
    assert enc.loc["p6", ["cat__kind_gold", "cat__kind_silver"]].tolist() == [0, 0]
    assert enc.loc["q6", ["cat__kind_gold", "cat__kind_silver"]].tolist() == [1, 0]
    prior = (imputer.statistics_.copy(), scale.data_min_.copy(), scale.data_max_.copy(),
             cat.categories_[0].copy())
    r2 = r.copy()
    r2.loc[(r2.unit == "P") & (r2.time == 6), "reading"] = 25
    vx2 = make(r2, va)
    enc2 = encode(vx2)
    assert vx2.loc["p6","recent"] == 11 and vx2.loc["p7","recent"] == 25
    assert np.isclose(enc2.loc["p7","num__recent"], 3)
    assert all(np.array_equal(a,b) for a,b in zip(prior,
        (imputer.statistics_, scale.data_min_, scale.data_max_, cat.categories_[0])))
    passed("new exercise: forward-fill, window, median, range, unknown, train-stat invariance")

    # Fitting separate validation encoders can silently swap semantic columns.
    train_cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(tx[["kind"]])
    val_cat = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(vx[["kind"]])
    assert len(train_cat.categories_[0]) == len(val_cat.categories_[0]) == 2
    assert train_cat.get_feature_names_out().tolist() != val_cat.get_feature_names_out().tolist()
    bad_mixed = OneHotEncoder(handle_unknown="ignore").fit(pd.concat([tx, vx])[["kind"]])
    assert "bronze" in bad_mixed.categories_[0] and "bronze" not in cat.categories_[0]
    passed("same-width wrong encoder and validation-fit leakage mutations")

    # Assert exact floating-point equality at each specified threshold.
    scores = enc["num__recent"].to_numpy()
    y = va.label.to_numpy()
    assert scores.tolist() == [5/4, 2., -1/8, 5/4]
    count, rates = ns["counts_at"], ns["rates"]
    expected = [
        (2., (0,1,1,2), (1/4,0,0,0,1/2,0)),
        (5/4, (1,2,0,1), (1/4,1/3,1/2,2/5,1,1/2)),
        (-1/8, (2,2,0,0), (1/2,1/2,1,2/3,1,1)),
    ]
    for threshold, expected_counts, expected_rates in expected:
        c = count(y, scores, threshold)
        assert tuple(c[k] for k in ("TP","FP","TN","FN")) == expected_counts
        got = rates(c)
        assert np.allclose([got[k] for k in ("accuracy","precision","recall","F1","FPR","TPR")], expected_rates)
    f, t, th = roc_curve(y, scores, pos_label=1, drop_intermediate=False)
    assert np.allclose(f, [0,.5,1,1]) and np.allclose(t, [0,0,.5,1])
    assert len(th) == 4  # equal P6 and Q7 scores cross together
    assert rates(count(np.array([-1,-1]), np.array([.1,.2]), 1))["precision"] is None
    assert rates(count(np.array([-1,-1]), np.array([.1,.2]), 1))["TPR"] is None
    assert rates(count(np.array([1,1]), np.array([.1,.2]), 1))["FPR"] is None
    assert rates(count(np.array([-1,-1]), np.array([.1,.2]), 1))["F1"] is None
    passed("new exercise ROC, F1, tie, positive/negative denominator edge cases")

    # Actual truth/prediction arrays: check correct and deliberately wrong formulas.
    weight_score = ns["weighted_accuracy"]
    actual = np.array(["B"] * 6 + ["T"] * 2)
    guess_u = np.array(["B"] * 8)
    guess_v = np.array(["B"] * 3 + ["T"] * 5)
    acc_u, acc_v = (actual == guess_u).mean(), (actual == guess_v).mean()
    weighted_u = weight_score(actual, guess_u, target_weight=4)
    weighted_v = weight_score(actual, guess_v, target_weight=4)
    for guess, expected in ((guess_u, 6/14), (guess_v, 11/14)):
        assert np.isclose(weight_score(actual, guess, target_weight=4),
                          expected, rtol=0, atol=1e-12)
        assert np.isclose(weight_score(actual[::-1], guess[::-1], target_weight=4),
                          expected, rtol=0, atol=1e-12)
    worked_forward = weight_score(ns["actual"], ns["guess_a"])
    worked_reverse = weight_score(ns["actual"][::-1], ns["guess_a"][::-1])
    assert np.isclose(worked_forward, 1/2, rtol=0, atol=1e-12)
    assert np.isclose(worked_reverse, 1/2, rtol=0, atol=1e-12)
    assert acc_u > acc_v and weighted_u < weighted_v
    for guess, correct_score in ((guess_u, weighted_u), (guess_v, weighted_v)):
        matches = actual == guess
        wrong_weights = np.where(guess == "T", 4, 1)
        wrong_prediction_based = float((wrong_weights * matches).sum() / wrong_weights.sum())
        truth_weights = np.where(actual == "T", 4, 1)
        wrong_correct_only_denominator = float((truth_weights * matches).sum() / truth_weights[matches].sum())
        assert not np.isclose(wrong_prediction_based, correct_score, rtol=0, atol=1e-12)
        assert not np.isclose(wrong_correct_only_denominator, correct_score, rtol=0, atol=1e-12)
    for bad_actual, bad_prediction in (([], []), (["B"], ["B", "T"]), (["?"], ["T"])):
        try:
            weight_score(bad_actual, bad_prediction)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid weighted-score input accepted")
    for bad_weight in (np.nan, np.inf, -np.inf, 0, -1, True, "5"):
        try:
            weight_score(["B", "T"], ["B", "T"], target_weight=bad_weight)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid target weight accepted: {bad_weight}")
    assert np.isclose(weight_score(["B", "T"], ["B", "T"], target_weight=2.5), 1, rtol=0, atol=1e-12)
    assert np.isclose(weight_score(["T", "T"], ["T", "T"], target_weight=1e308), 1, rtol=0, atol=1e-12)
    passed("new weighted score: truth-based weights, all-row denominator, ranking, mutations and finite positive-weight bounds")

    report = {
        "status": "passed",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution": "fresh process; nbformat validation; sequential InteractiveShell execution, no Jupyter socket",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "packages": {"nbformat": nbformat.__version__, "IPython": IPython.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__,
                     "scikit-learn": sklearn.__version__, "matplotlib": matplotlib.__version__},
        "notebook_cells": len(nb.cells),
        "code_cell_indices": code_indices,
        "weighted_worked_forward_and_reverse": [worked_forward, worked_reverse],
        "weighted_comparison": {"rtol": 0, "atol": 1e-12},
        "student_exercise_ast_empty": True,
        "student_exercise_template_checked_before_execution": True,
        "student_answer_verification": "blank distribution state only; student answers and achievement are not automatically evaluated",
        "student_exercise_outputs_empty": True,
        "saved_executed_example_cells": len(examples),
        "saved_png_outputs": len(images),
        "html_png_embedded": True,
        "saved_streams_match_fresh_execution": True,
        "saved_output_observations": "example cells have stored execution counts and no error outputs; one PNG is present; the distributed exercise is unexecuted with no saved output; original capture method is not verified",
        "checks": cases,
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "sha256": {**{p.name: hashlib.sha256(data).hexdigest() for p, data in inputs.items()},
                   Path(__file__).name: sha(Path(__file__).resolve())},
        "limits": [
            "Synthetic finite cases only; student answers, learning and completion time not observed.",
            "HTML structural checks only; visual review is not performed by this validator.",
            "HTML MathJax availability was not verified.",
            "Final test dataset is not created or held out by this script.",
            "This is not OS isolation; arbitrary trusted notebook Python can access absolute paths.",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    for path, before in inputs.items():
        if path.read_bytes() != before:
            raise RuntimeError("Input changed during validation; refusing result: " + str(path))
    if output is not None:
        write_new_report(output, rendered)
    print(rendered)


if __name__ == "__main__":
    main()
