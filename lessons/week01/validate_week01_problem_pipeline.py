#!/usr/bin/env python3
"""Validate the synthetic week-01 pipeline without modifying its teaching files.

Run with the course venv Python. --write PATH optionally stores a JSON receipt.
Execution uses an in-process IPython kernel, never a network/socket kernel.
"""
import argparse
import ast
import hashlib
import io
import itertools
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("PYDEVD_DISABLE_FILE_VALIDATION", "1")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import nbformat
import numpy as np
import pandas as pd
import sklearn
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent
NB = ROOT / "week01_problem_pipeline.ipynb"
HTML = ROOT / "week01_problem_pipeline.html"
TEACHER = ROOT / "week01_problem_pipeline_teacher.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def must_reject(action, expected=ValueError):
    try:
        action()
    except expected:
        return
    raise AssertionError("Expected an error but action was accepted")


def visible_outputs(cell):
    result = []
    for output in cell.outputs:
        if output.output_type == "stream":
            result.append(("stream", output.name, output.text))
        elif output.output_type in ("display_data", "execute_result"):
            result.append(("display", output.data.get("text/plain", "")))
        else:
            result.append((output.output_type, str(output)))
    return result


def make_model():
    return Pipeline([("fill", SimpleImputer(strategy="mean")),
                     ("classifier", NearestCentroid())])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", help="Optional JSON receipt path")
    args = parser.parse_args()
    hashes_before = {p.name: sha(p) for p in (NB, HTML, TEACHER)}
    book = nbformat.read(NB, as_version=4)
    nbformat.validate(book)
    saved = nbformat.read(NB, as_version=4)
    rendered, _ = HTMLExporter().from_notebook_node(book)
    assert rendered == HTML.read_text(encoding="utf-8"), "HTML differs from fresh export"
    checks = []

    def passed(name):
        checks.append(name)

    with tempfile.TemporaryDirectory(prefix="week01-pipeline-validator-") as temp:
        os.environ["IPYTHONDIR"] = temp
        manager = InProcessKernelManager()
        manager.start_kernel()
        shell = manager.kernel.shell
        client = manager.client()
        client.start_channels()
        try:
            executed = []
            for index, cell in enumerate(book.cells):
                if cell.cell_type != "code":
                    continue
                client.execute(cell.source, store_history=True)
                reply = client.get_shell_msg(timeout=90)
                if reply["content"]["status"] != "ok":
                    raise AssertionError(f"Cell {index} failed: {reply['content']}")
                cell.execution_count = reply["content"]["execution_count"]
                cell.outputs = []
                while True:
                    message = client.get_iopub_msg(timeout=90)
                    if message["msg_type"] == "status" and message["content"].get("execution_state") == "idle":
                        break
                    if message["msg_type"] in ("stream", "display_data", "execute_result", "error"):
                        cell.outputs.append(nbformat.v4.output_from_msg(message))
                assert not any(o.output_type == "error" for o in cell.outputs)
                assert visible_outputs(cell) == visible_outputs(saved.cells[index]), (
                    f"Stored and newly executed outputs differ in cell {index}")
                executed.append(index)
            passed("fresh_inprocess_sequential_execution_and_saved_outputs")
            ns = shell.user_ns

            # The student answer remains a comment, not our solution.
            answer = next(c for c in saved.cells
                          if c.cell_type == "code" and c.source.startswith("# 새 명세에 맞는"))
            assert not ast.parse(answer.source).body and answer.outputs == []
            passed("student_answer_cell_is_empty")

            train = ns["training"]
            known = ns["known_train"]
            model = ns["model"]
            features = ns["feature_cols"]
            assert known["row_id"].tolist() == ["T1", "T2", "T3", "T4"]
            assert train.loc[train["row_id"] == "T5", "label"].item() == 0
            assert set(known["label"]) == {-1, 1}
            assert np.allclose(model["fill"].statistics_, [5, 3])
            assert np.allclose(model["classifier"].centroids_, [[2, 2], [8, 4]])
            passed("known_targets_and_train_only_imputer_and_centroids")

            original_probe = int(model.predict(pd.DataFrame([[5.25, 3]], columns=features))[0])
            x_changed = known.copy()
            x_changed.loc[x_changed["row_id"] == "T4", "texture"] = 11
            model_x = make_model().fit(x_changed[features], x_changed["label"])
            assert np.allclose(model_x["classifier"].centroids_[1], [9, 4])
            assert int(model_x.predict(pd.DataFrame([[5.25, 3]], columns=features))[0]) == -1
            assert original_probe == 1
            y_changed = known.copy()
            y_changed.loc[y_changed["row_id"] == "T3", "label"] = -1
            model_y = make_model().fit(y_changed[features], y_changed["label"])
            assert not np.allclose(model_y["classifier"].centroids_, model["classifier"].centroids_)
            assert int(model_y.predict(pd.DataFrame([[5.25, 3]], columns=features))[0]) == -1
            passed("train_feature_and_target_perturbations_change_fit_and_prediction")

            altered_unknown = train.copy()
            altered_unknown.loc[altered_unknown["row_id"] == "T5", ["texture", "color"]] = [1000, 1000]
            known_again = altered_unknown[altered_unknown["label"].isin([-1, 1])]
            only_known = make_model().fit(known_again[features], known_again["label"])
            assert np.allclose(only_known["fill"].statistics_, model["fill"].statistics_)
            assert np.allclose(only_known["classifier"].centroids_, model["classifier"].centroids_)
            passed("unknown_training_row_not_relabelled_or_fitted_in_this_demo")

            valid = ns["validation"]
            assert model.predict(valid[features]).tolist() == [-1, 1, 1, 1]
            assert ns["accuracy"] == 3 / 4
            stats = model["fill"].statistics_.copy()
            centers = model["classifier"].centroids_.copy()
            valid_mutant = valid.copy()
            valid_mutant.loc[0, "texture"] = 2000
            valid_mutant["label"] = -valid_mutant["label"]
            model.predict(valid_mutant[features])
            assert np.array_equal(stats, model["fill"].statistics_)
            assert np.array_equal(centers, model["classifier"].centroids_)
            passed("validation_changes_do_not_refit_training_state")

            predict_pairs = ns["predict_pairs"]
            align = ns["align_predictions"]
            inspect = ns["inspect_archive"]
            archive_texts = ns["archive_texts"]
            csv_text = ns["csv_text"]
            A, B = ns["A"], ns["B"]
            ids_A, ids_B = ns["order_A"], ns["order_B"]
            pairs_A, pairs_B = ns["pairs_A"], ns["pairs_B"]
            expected_A = [-1, 1, -1]
            expected_B = [-1, 1]
            for permutation in itertools.permutations(range(len(A))):
                shuffled = A.iloc[list(permutation)].copy()
                assert align(ids_A, predict_pairs(model, shuffled)) == expected_A
            swapped_columns = A[["row_id", "color", "texture"]].copy()
            assert predict_pairs(model, swapped_columns) == pairs_A
            assert predict_pairs(model, A.assign(later_report=[1, 1, 1])) == pairs_A
            assert predict_pairs(model, A.assign(later_report=[-1, -1, -1])) == pairs_A
            passed("all_six_input_row_permutations_recover_same_id_predictions")
            passed("named_feature_order_and_future_extra_column")

            must_reject(lambda: predict_pairs(model, A.drop(columns=["color"])))
            duplicate = pd.concat([A, A.iloc[[0]]], ignore_index=True)
            must_reject(lambda: predict_pairs(model, duplicate))
            missing_id = A.copy()
            missing_id.loc[0, "row_id"] = None
            must_reject(lambda: predict_pairs(model, missing_id))
            infinite = A.copy()
            infinite["texture"] = infinite["texture"].astype(float)
            infinite.loc[0, "texture"] = np.inf
            must_reject(lambda: predict_pairs(model, infinite))
            assert align(["A"], [("A", 1)]) == [1]
            assert align([11], [(11, -1)]) == [-1]
            for absent in (None, np.nan, pd.NA, "", "  "):
                must_reject(lambda absent=absent: align([absent], [(absent, 1)]))
                must_reject(lambda absent=absent: align(["A"], [(absent, 1)]))
                must_reject(lambda absent=absent: align([absent], [("A", 1)]))
                missing_row_id = A.copy()
                missing_row_id["row_id"] = missing_row_id["row_id"].astype(object)
                missing_row_id.loc[0, "row_id"] = absent
                must_reject(lambda missing_row_id=missing_row_id: predict_pairs(model, missing_row_id))
            must_reject(lambda: align(ids_A, pairs_A + [pairs_A[0]]))
            must_reject(lambda: align(ids_A, pairs_A[:-1]))
            must_reject(lambda: align(ids_A, [("A05", 0), ("A08", 1), ("A02", -1)]))
            must_reject(lambda: align(ids_A, [("A05", True), ("A08", 1), ("A02", -1)]))
            passed("missing_feature_duplicate_missing_id_inf_bad_label_and_missing_pair_rejected")

            blob = ns["archive_bytes"]
            assert inspect(blob, ids_A, pairs_A, ids_B, pairs_B) == {
                "submissionA.csv": expected_A, "submissionB.csv": expected_B}
            assert ns["verified"] == {
                "submissionA.csv": expected_A, "submissionB.csv": expected_B}
            assert not ns["practice_zip"].exists()
            assert not ns["practice_zip"].parent.exists()
            wrong_order = archive_texts(csv_text([1, -1, -1]), csv_text(expected_B))
            with_header = archive_texts("label\n" + csv_text(expected_A), csv_text(expected_B))
            missing_row = archive_texts(csv_text(expected_A[:-1]), csv_text(expected_B))
            invalid_label = archive_texts("0\n1\n-1\n", csv_text(expected_B))
            extra_column = archive_texts("-1,x\n1,x\n-1,x\n", csv_text(expected_B))
            for mutant in (wrong_order, with_header, missing_row, invalid_label, extra_column):
                must_reject(lambda mutant=mutant: inspect(mutant, ids_A, pairs_A, ids_B, pairs_B))
            passed("actual_temporary_zip_reopened_validated_and_removed")
            passed("same_length_order_header_missing_row_bad_label_extra_column_rejected")

            # Independent task: one valid model is checked as an example, not a required choice.
            ex_train = ns["exercise_train"]
            ex_valid = ns["exercise_validation"]
            ex_input = ns["exercise_input"]
            ex_cols = ["vibration", "sound", "heat"]
            ex_known = ex_train[ex_train["label"].isin([0, 1])].copy()
            ex = make_model().fit(ex_known[ex_cols], ex_known["label"])
            assert ex_known["item"].tolist() == ["R1", "R2", "R3", "R4"]
            assert ex_train.loc[ex_train["item"] == "R5", "label"].item() == -1
            assert np.allclose(ex["fill"].statistics_, [4, 4, 2])
            assert np.allclose(ex["classifier"].centroids_, [[1, 3, 1], [7, 5, 3]])
            assert ex.predict(ex_valid[ex_cols]).tolist() == [0, 1, 1]
            assert ex.predict(ex_input[ex_cols]).tolist() == [1, 0, 0]
            output = pd.DataFrame({"item": ex_input["item"], "signal": ex.predict(ex_input[ex_cols])})
            text = output.to_csv(index=False, lineterminator="\n")
            assert text == "item,signal\nJ3,1\nJ1,0\nJ2,0\n"
            other = Pipeline([("fill", SimpleImputer(strategy="mean")),
                              ("classifier", DecisionTreeClassifier(max_depth=1, random_state=0))])
            other.fit(ex_known[ex_cols], ex_known["label"])
            assert set(other.predict(ex_input[ex_cols])).issubset({0, 1})
            passed("independent_new_schema_mean_and_optional_centroid_answer")
            passed("independent_alternative_tree_is_valid_and_not_forced_to_centroid")

            student_text = "\n".join(c.source for c in saved.cells if c.cell_type == "markdown")
            assert "미상 0→−1" in student_text and "복제품 −1→0" in student_text
            assert "120분" not in student_text and "5~7시간" not in student_text
            assert "교사는 독립 수행 전에" not in student_text
            teacher_text = TEACHER.read_text(encoding="utf-8")
            assert "접근 통제가 아닙니다" in teacher_text
            assert "총 부담이 늘 수" in teacher_text
            passed("label_mapping_student_scope_and_teacher_workload_boundary")
        finally:
            client.stop_channels()
            manager.shutdown_kernel()
            shell._atexit_once()

    assert hashes_before == {p.name: sha(p) for p in (NB, HTML, TEACHER)}
    passed("source_files_unchanged_by_validation")
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_script_sha256": sha(Path(__file__)),
        "source_sha256": hashes_before,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "execution": "fresh InProcessKernelManager; all code cells sequentially; saved outputs compared",
        "total_cells": len(book.cells),
        "code_cells_executed": len(executed),
        "normal_and_error_checks": checks,
        "observed_example": {
            "train_imputer": [5, 3], "class_centers": [[2, 2], [8, 4]],
            "training_change_probe": {"input": [5.25, 3], "original": 1, "changed": -1},
            "validation_predictions": [-1, 1, 1, 1], "validation_accuracy": 0.75,
            "ordered_submission_A": [-1, 1, -1], "ordered_submission_B": [-1, 1],
            "temporary_submission_zip_removed": True
        },
        "independent_answer_is_centroid_example_not_required_model": True,
        "limits": [
            "finite synthetic examples; no official Antique data or submission executed",
            "student independent work, actual learning and workload unobserved",
            "ordinary socket Jupyter and Colab not verified",
            "HTML regenerated and compared; full browser visual rendering not inspected",
            "a CSV without IDs cannot by itself prove the ID-to-prediction mapping is correct"
        ]
    }
    if args.write:
        destination = Path(args.write)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
