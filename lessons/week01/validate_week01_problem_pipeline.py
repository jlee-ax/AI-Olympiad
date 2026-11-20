#!/usr/bin/env python3
"""Validate the synthetic week-01 pipeline without modifying its teaching files.

Run with the course venv Python. --write PATH optionally stores a JSON receipt.
Execution uses an in-process IPython kernel, never a network/socket kernel.
"""
import argparse
import contextlib
import ast
import hashlib
import io
import itertools
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")
os.environ.setdefault("PYDEVD_DISABLE_FILE_VALIDATION", "1")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import nbformat
import numpy as np
import pandas as pd
import sklearn
from ipykernel.inprocess.manager import InProcessKernelManager
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent
NB = ROOT / "week01_problem_pipeline.ipynb"
HTML = ROOT / "week01_problem_pipeline.html"
TEACHER = ROOT / "week01_problem_pipeline_teacher.md"
DEVICE_KEY = ROOT / "data/pipeline_device_validation.csv"
sys.path.insert(0, str(ROOT.parents[1] / "tools"))
from check_week01_render import verify


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


def check_device_gate(source, student, directory):
    """Run the real release cell with an unattended learner, then with changed inputs."""
    items = student["exercise_validation"]["item"].tolist()
    assert items == ["V1", "V2", "V3"]
    scope = {"pd": pd, "np": np, "Path": Path, "display": lambda value: None,
             "exercise_validation": student["exercise_validation"], "first_device_predictions": None,
             "recorded_device_predictions": None, "device_key_path": DEVICE_KEY}
    def run():
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(source, "<device-score-release>", "exec"), scope)
    with patch.object(pd, "read_csv", side_effect=AssertionError("Opened the key before a first prediction")):
        run()
    assert scope["recorded_device_predictions"] is None and scope["device_comparison"] is None
    key = pd.read_csv(DEVICE_KEY)
    assert key.to_dict("records") == [{"item":"V3","label":0},{"item":"V1","label":0},{"item":"V2","label":1}]
    missing = directory / "not-released.csv"
    scope["device_key_path"] = missing
    good = pd.DataFrame([("V2",1),("V3",0),("V1",0)], columns=["item","prediction"])
    for invalid in (good.iloc[:2], pd.concat([good, good.iloc[:1]]), good.assign(item=["V2","V3","other"]),
                    good.assign(prediction=[False, True, False]), good.rename(columns={"prediction":"label"})):
        scope["first_device_predictions"] = invalid
        must_reject(run)
        assert scope["recorded_device_predictions"] is None
    scope["first_device_predictions"] = good
    run()
    assert scope["recorded_device_predictions"] == (("V1",0),("V2",1),("V3",0))
    assert scope["device_comparison"] is None
    scope["device_key_path"] = DEVICE_KEY
    scope["first_device_predictions"] = good.iloc[::-1]
    run()
    comparison = scope["device_comparison"]
    assert comparison["item"].tolist() == items
    assert comparison["prediction"].eq(comparison["label"]).sum() == 3
    assert np.sum(comparison["prediction"].to_numpy() == key["label"].to_numpy()) == 1
    scope["first_device_predictions"] = good.assign(prediction=[0,0,0])
    must_reject(run)
    scope["first_device_predictions"] = good
    changed_key = directory / "changed-device-key.csv"
    scope["device_key_path"] = changed_key
    for invalid_key in (key.iloc[:2], pd.concat([key, key.iloc[:1]]), key.assign(item=["V3","V1","other"]),
                        key.assign(label=[0,0,2]), key.rename(columns={"label":"prediction"})):
        invalid_key.to_csv(changed_key, index=False)
        must_reject(run)
    assert scope["recorded_device_predictions"] == (("V1",0),("V2",1),("V3",0))


def check_teacher_audit(guide, student, directory):
    blocks = re.findall(r"^\x60\x60\x60python\s*\n(.*?)^\x60\x60\x60\s*$", guide, flags=re.MULTILINE | re.DOTALL)
    namespace = {name: student[name].copy(deep=True) for name in ("exercise_train","exercise_validation","exercise_input")}
    with contextlib.chdir(directory):
        for block in blocks:
            exec(compile(block, "<published teacher guide>", "exec"), namespace)
        rows = namespace["audit_rows"]
        original = pd.read_csv("audit.csv", dtype=str, keep_default_na=False)
        assert original.to_dict("list") == {"item":["J3","J1","J2"],"signal":["1","0","0"]}
        wrong = original.assign(signal=original["signal"].tolist()[::-1])
        wrong.to_csv("reversed.csv", index=False)
        must_reject(lambda: namespace["verify_audit"]("reversed.csv", original["item"], rows))
        # Pandas alone can treat the extra leading field as an unlabelled index or skip a blank record.
        for name, text in {
            "extra.csv": "item,signal\n99,J3,1\n98,J1,0\n97,J2,0\n",
            "blank.csv": "item,signal\nJ3,1\n\nJ1,0\nJ2,0\n",
        }.items():
            Path(name).write_text(text, encoding="utf-8")
            must_reject(lambda: namespace["verify_audit"](name, original["item"], rows))
        quoted = pd.DataFrame({"item": ['M,1', 'M"2'], "signal": [1,0]})
        quoted.to_csv("quoted.csv", index=False)
        namespace["verify_audit"]("quoted.csv", quoted["item"], quoted)
        unknown = namespace["exercise_input"].copy()
        unknown.loc[unknown["item"]=="J1",["vibration","sound","heat"]] = [7,5,3]
        shifted = namespace["predict_devices"](unknown,"signal").set_index("item")
        assert shifted.at["J1","signal"] == 1
        must_reject(lambda: namespace["predict_devices"](unknown.drop(columns=["heat"]),"signal"))
        must_reject(lambda: namespace["predict_devices"](pd.concat([unknown,unknown.iloc[:1]]),"signal"))
        validation = namespace["first_device_predictions"].merge(pd.read_csv(DEVICE_KEY), on="item", validate="one_to_one")
        assert validation.loc[validation["prediction"]!=validation["label"],"item"].tolist() == ["V3"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", help="Optional JSON receipt path")
    args = parser.parse_args()
    bound = (NB, HTML, TEACHER, DEVICE_KEY, Path(__file__).resolve())
    hashes_before = {str(p.relative_to(ROOT)): sha(p) for p in bound}
    renderer_path = ROOT.parents[1] / 'tools/check_week01_render.py'
    renderer_sha256 = sha(renderer_path)
    book = nbformat.read(NB, as_version=4)
    nbformat.validate(book)
    saved = nbformat.read(NB, as_version=4)
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
                if cell.id == "worked-score":
                    assert "label" not in shell.user_ns["validation"]
                    assert "worked_validation_key" not in shell.user_ns
                if cell.id == "device-score-release":
                    assert "label" not in shell.user_ns["exercise_validation"]
                    assert shell.user_ns["first_device_predictions"] is None
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
            answer = next(c for c in saved.cells if c.id == "06ceb97e")
            assert not ast.parse(answer.source).body and answer.outputs == []
            scored_answer = next(c for c in saved.cells if c.id == "device-score-work")
            assert not ast.parse(scored_answer.source).body and scored_answer.outputs == []
            passed("student_answer_cell_is_empty")
            ordering = next(c for c in saved.cells if c.id == "order-by-hand")
            separate = {}
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(ordering.source, "<independent section 4>", "exec"), separate)
            assert [separate["by_id"][k] for k in separate["requested_rows"]] == [-1,1,-1]
            passed("section_4_ordering_works_with_an_empty_namespace")

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
            assert ns["worked_first"].columns.tolist() == ["row_id","prediction"]
            assert ns["val_view"].loc[~ns["val_view"]["correct"],"row_id"].tolist() == ["V3"]
            stats = model["fill"].statistics_.copy()
            centers = model["classifier"].centroids_.copy()
            valid_mutant = valid.copy()
            valid_mutant.loc[0, "texture"] = 2000
            assert "label" not in valid_mutant
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
            assert "label" not in ex_valid and "label" not in ex_input
            assert ns["first_device_predictions"] is None and ns["recorded_device_predictions"] is None
            assert ns["device_comparison"] is None and "key_rows" not in ns
            passed("blank_learner_answer_and_feature_only_device_inputs")
            gate = next(c for c in saved.cells if c.id == "device-score-release")
            check_device_gate(gate.source, ns, Path(temp))
            passed("first_predictions_before_key_id_order_freezing_and_invalid_tables")
            check_teacher_audit(TEACHER.read_text(encoding="utf-8"), ns, Path(temp))
            passed("real_teacher_csv_changed_order_changed_inputs_and_reversed_predictions")
        finally:
            client.stop_channels()
            manager.shutdown_kernel()
            shell._atexit_once()

    render_check = verify(saved, book, HTML.read_text(encoding="utf-8"), stem=NB.stem)
    assert hashes_before == {str(p.relative_to(ROOT)): sha(p) for p in bound}
    assert renderer_sha256 == sha(renderer_path)
    passed("source_files_unchanged_by_validation")
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_script_sha256": sha(Path(__file__)),
        "source_sha256": hashes_before,
        "canonical_renderer_sha256": renderer_sha256,
        "render_validation": render_check,
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
            "Canonical HTML compared; browser and figure checks have a separate delivery receipt",
            "a CSV without IDs cannot by itself prove the ID-to-prediction mapping is correct"
        ]
    }
    if args.write:
        destination = Path(args.write)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
