#!/usr/bin/env python3
"""Re-execute and validate the integrated lesson without editing its inputs."""
import argparse
import ast
import hashlib
import itertools
import json
import math
import os
import re
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

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / "lessons/week01"
NB = LESSON / "week01_integrated.ipynb"
HTML = LESSON / "week01_integrated.html"
TEACHER = LESSON / "week01_integrated_teacher.md"
PRESERVED = Path("/workspace/scratch/d500e5cb2076/ai-olympiad-week01-integration/lessons/week01")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_text(cell):
    result = []
    for output in cell.outputs:
        if output.output_type == "stream":
            result.append(("stream", output.name, output.text))
        elif output.output_type in ("display_data", "execute_result"):
            result.append(("display", output.data.get("text/plain", "")))
        else:
            result.append((output.output_type, str(output)))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", help="Optional JSON results path")
    args = parser.parse_args()
    sources = [NB, HTML, TEACHER,
               LESSON / "week01_python_tables.ipynb",
               LESSON / "week01_axes_linear_bridge.ipynb",
               LESSON / "week01_problem_pipeline.ipynb",
               PRESERVED / "week01_python_tables.ipynb",
               PRESERVED / "week01_python_tables.html",
               PRESERVED / "lesson-manifest.json",
               PRESERVED / "teacher-notes.txt",
               PRESERVED / "validation.json"]
    before = {str(path): sha(path) for path in sources}
    book = nbformat.read(NB, as_version=4)
    saved = nbformat.read(NB, as_version=4)
    nbformat.validate(book)
    fresh_html, _ = HTMLExporter().from_notebook_node(book)
    assert fresh_html == HTML.read_text(encoding="utf-8")
    checks = []
    def passed(name):
        checks.append(name)

    with tempfile.TemporaryDirectory(prefix="week01-integrated-qa-") as temp:
        os.environ["IPYTHONDIR"] = temp
        os.environ["MPLCONFIGDIR"] = temp
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
                reply = client.get_shell_msg(timeout=120)
                if reply["content"]["status"] != "ok":
                    raise AssertionError(f"cell {index}: {reply['content']}")
                cell.execution_count = reply["content"]["execution_count"]
                cell.outputs = []
                while True:
                    msg = client.get_iopub_msg(timeout=120)
                    if msg["msg_type"] == "status" and msg["content"].get("execution_state") == "idle":
                        break
                    if msg["msg_type"] in ("stream", "display_data", "execute_result", "error"):
                        cell.outputs.append(nbformat.v4.output_from_msg(msg))
                assert not any(o.output_type == "error" for o in cell.outputs)
                assert output_text(cell) == output_text(saved.cells[index]), f"saved output differs: {index}"
                executed.append(index)
            passed("fresh_inprocess_all_cells_and_saved_text_outputs")
            ns = shell.user_ns

            answer = next(c for c in saved.cells if c.cell_type == "code"
                          and c.source.startswith("# 스스로 선택한 모델"))
            assert not ast.parse(answer.source).body and answer.outputs == []
            passed("student_answer_blank")

            df = ns["plants"]
            mean = ns["observed_mean"]
            assert df.shape == (6, 5)
            assert df["pot_id"].tolist() == ["P01", "P02", "P03", "P04", "P05", "P06"]
            assert df.loc[df["water_ml"].isna(), "pot_id"].tolist() == ["P03"]
            assert df.loc[df["water_ml"] == 0, "pot_id"].tolist() == ["P01"]
            assert mean(df["water_ml"].tolist()) == 24
            assert mean([0, None, np.nan, 6]) == 3
            assert mean([0]) == 0 and mean([]) is None and mean([None, np.nan]) is None
            assert mean([1_000_000] * 10_000) == 1_000_000
            assert mean([-1_000_000, 1_000_000, None, np.nan]) == 0
            values = [0, None, 6]
            assert mean(values) == 3 and values == [0, None, 6]
            passed("real_csv_nan_none_zero_empty_and_no_input_mutation")

            heights = ns["three_heights"]
            assert heights.mean() == 10 and np.isclose(heights.var(ddof=0), 8/3)
            grid = ns["light_by_day"]
            assert grid.shape == (3, 2)
            assert np.allclose(grid.mean(axis=0), [11/3, 11/3])
            assert np.array_equal(grid.mean(axis=1), [2, 3, 6])
            assert np.array_equal(ns["reshaped"], [[2, 2, 3], [3, 6, 6]])
            assert np.array_equal(ns["transposed"], [[2, 3, 6], [2, 3, 6]])
            assert np.array_equal(grid + np.array([1, 2]), [[3, 4], [4, 5], [7, 8]])
            try:
                grid + np.array([1, 2, 3])
            except ValueError:
                pass
            else:
                raise AssertionError("incompatible broadcast accepted")
            passed("mean_variance_axis_reshape_transpose_and_broadcast")

            saved_pngs = [o.data["image/png"] for c in saved.cells if c.cell_type == "code"
                          for o in c.outputs if "image/png" in o.get("data", {})]
            fresh_pngs = [o.data["image/png"] for c in book.cells if c.cell_type == "code"
                          for o in c.outputs if "image/png" in o.get("data", {})]
            assert len(saved_pngs) == len(fresh_pngs) == 1 and saved_pngs[0] == fresh_pngs[0]
            ax = ns["ax"]
            observed = sorted(tuple(map(float, row)) for coll in ax.collections for row in coll.get_offsets())
            expected = sorted((float(a), float(b)) for a,b in zip(df["light_h"], df["height_cm"]))
            assert observed == expected
            assert {text.get_text() for text in ax.texts} == set(df["pot_id"])
            assert ax.get_xlabel() == "하루 빛 시간 (h)" and ax.get_ylabel() == "일주일 뒤 높이 (cm)"
            passed("stored_png_reproduces_and_scatter_matches_each_id_and_unit")

            assert ns["fixed_height"] == 9 and ns["p02"]["height_cm"] - ns["fixed_height"] == 1
            assert ns["x_train"].columns.tolist() == ["water_ml"]
            assert ns["y_train"].tolist() == [0, 0, 1, 1]
            assert np.allclose(ns["fill"].statistics_, [20])
            assert np.allclose(ns["model"].centroids_.ravel(), [10, 30])
            assert ns["predictions"].tolist() == [0, 1]
            assert ns["y_validation"].tolist() == [1, 1] and ns["validation_accuracy"] == 0.5
            assert (ns["original_prediction"], ns["changed_prediction"]) == (1, 0)
            passed("fixed_formula_and_actual_fit_are_distinct_and_correct")

            # Any one row becoming extreme in validation cannot alter learned state.
            fill = ns["fill"]
            model = ns["model"]
            stats, centers = fill.statistics_.copy(), model.centroids_.copy()
            altered_val = ns["x_validation"].copy()
            altered_val.loc[altered_val.index[0], "water_ml"] = 2000
            model.predict(fill.transform(altered_val))
            assert np.array_equal(stats, fill.statistics_) and np.array_equal(centers, model.centroids_)
            assert mean(df["water_ml"].tolist()) == 24 and fill.statistics_[0] == 20
            passed("validation_extreme_does_not_refit_and_full_mean_differs")

            # Reorder training rows with labels; then show that moving only labels changes state.
            train = ns["training"]
            y = ns["y_train"]
            for order in itertools.permutations(range(4)):
                ptrain = train.iloc[list(order)]
                ptarget = y.iloc[list(order)]
                test_fill = SimpleImputer(strategy="mean")
                xx = test_fill.fit_transform(ptrain[["water_ml"]])
                fitted = NearestCentroid().fit(xx, ptarget)
                assert np.allclose(test_fill.statistics_, stats)
                assert np.allclose(fitted.centroids_, centers)
            reversed_labels = y.iloc[::-1]
            misaligned = NearestCentroid().fit(ns["filled_train"], reversed_labels)
            assert not np.allclose(misaligned.centroids_, centers)
            passed("24_train_row_and_label_permutations_preserve_state_but_wrong_alignment_does_not")

            checked = ns["checked"]
            assert checked["pot_id"].tolist() == ["P05", "P06"]
            assert checked["prediction"].tolist() == [0, 1]
            assert ns["file_check"].equals(checked)
            assert not ns["result_path"].exists() and not ns["result_path"].parent.exists()
            wrong = checked.copy()
            wrong["prediction"] = wrong["prediction"].iloc[::-1].to_numpy()
            assert wrong["pot_id"].tolist() == checked["pot_id"].tolist()
            assert not wrong["prediction"].equals(checked["prediction"])
            passed("in_memory_and_physical_csv_roundtrip_order_and_cleanup")

            # Independently validate one optional model, then a different allowed model.
            ex_train = ns["exercise_train"]
            ex_valid = ns["exercise_validation"]
            ex_input = ns["exercise_input"]
            known = ex_train[ex_train["label"].isin(["정상", "점검"])].copy()
            assert known["unit"].tolist() == ["T1", "T2", "T3", "T4"]
            assert ex_train.loc[ex_train["unit"] == "T5", "label"].item() == "?"
            independent = Pipeline([("fill", SimpleImputer(strategy="mean")),
                                    ("model", NearestCentroid())])
            independent.fit(known[["signal"]], known["label"])
            assert np.allclose(independent["fill"].statistics_, [2])
            center_map = dict(zip(independent["model"].classes_,
                                  independent["model"].centroids_.ravel()))
            assert center_map == {"정상": 1.0, "점검": 3.0}
            assert independent.predict(ex_valid[["signal"]]).tolist() == ["정상", "점검", "정상"]
            assert independent.predict(ex_input[["signal"]]).tolist() == ["점검", "정상", "정상"]
            frame = pd.DataFrame({"sample_id": ex_input["unit"],
                                  "prediction": independent.predict(ex_input[["signal"]])})
            frame = frame.set_index("sample_id").loc[ns["exercise_order"]].reset_index()
            assert frame["sample_id"].tolist() == ["N7", "N3", "N1"]
            assert frame["prediction"].tolist() == ["정상", "점검", "정상"]
            alternative = Pipeline([("fill", SimpleImputer(strategy="mean")),
                                    ("model", DecisionTreeClassifier(max_depth=1, random_state=0))])
            alternative.fit(known[["signal"]], known["label"])
            assert set(alternative.predict(ex_input[["signal"]])).issubset({"정상", "점검"})
            passed("new_specification_optional_centroid_and_alternative_classifier")

            markdown = "\n".join(c.source for c in saved.cells if c.cell_type == "markdown")
            assert not re.search(r"\d+\s*(?:[~∼–-]\s*\d+)?\s*(?:분|시간)(?![가-힣])|편성|실측|소요\s*시간|필수\s*자습", markdown)
            assert "축·ID 교량의 필수 문제" in markdown and "필수 A와 B" in markdown
            assert "20ml" in markdown and "ddof" in markdown
            assert "별도 새 커널" in markdown and "바로 아래 새 입력 코드" in markdown
            assert all(s in markdown for s in ("from pathlib import Path", "csv_text =", "new_csv_text ="))
            assert "두 행의 일부 값을 바꾼" in markdown and "2주에는" in markdown
            assert "ml에서 L로 일관되게" in markdown
            assert "과제 A" in markdown and "과제 B" in markdown and "과제 C" in markdown and "과제 D·E" in markdown
            assert "미상 표본까지 활용" in markdown
            assert all((LESSON / name).is_file() for name in
                       ("week01_python_tables.ipynb", "week01_axes_linear_bridge.ipynb",
                        "week01_problem_pipeline.ipynb"))
            passed("student_operational_text_and_responsible_followup_links")
        finally:
            client.stop_channels()
            manager.shutdown_kernel()
            shell._atexit_once()

    assert before == {str(path): sha(path) for path in sources}
    passed("existing_lessons_and_preserved_workspace_bytes_unchanged")
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validator_sha256": sha(Path(__file__)),
        "source_sha256": before,
        "python": sys.version.split()[0],
        "numpy": np.__version__, "pandas": pd.__version__, "scikit_learn": sklearn.__version__,
        "method": "fresh in-process IPython kernel; sequential cells; saved outputs and chart compared",
        "total_cells": len(book.cells), "code_cells": len(executed),
        "checks": checks,
        "example": {"observed_water_mean": 24, "training_fill": 20,
                    "class_centers": [10, 30], "validation_predictions": [0, 1],
                    "validation_truth": [1, 1], "validation_accuracy": 0.5,
                    "training_change_probe": [1, 0], "temporary_csv_removed": True},
        "independent_centroid_example_only": {"training_mean": 2,
                    "centers": {"정상": 1, "점검": 3},
                    "validation_predictions": ["정상", "점검", "정상"],
                    "validation_accuracy": 2/3},
        "visual_check": "Stored scatter PNG was viewed separately; labels, units, shapes, legend visible.",
        "limits": ["No actual student work, learning outcome or time observed",
                   "Main path does not automatically complete linked mandatory exercises",
                   "No official Antique or Robot dataset/model submission executed",
                   "Ordinary socket Jupyter/Colab and full HTML browser rendering unverified"]
    }
    if args.write:
        Path(args.write).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
