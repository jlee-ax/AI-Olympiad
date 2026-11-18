"""Independent public-input regression checks for the Week 1 classification course.

Run from the checkout using the environment for the student notebook. All labels
used as answers here are public training labels or the small fixtures below.
"""
import argparse
from contextlib import redirect_stderr, redirect_stdout
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import tempfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_SHA256 = "99ffffc9972351e91d05a4bf80e5d3c63996aa7231a338959cd49e288c63f11a"
OFFICIAL_TRAIN = "https://huggingface.co/datasets/IOAI-official/IOAI2025/blob/main/Individual-Contest/Antique/training_set/training_set.csv"
FEATURES = [f"feature{i}" for i in range(1, 6)]
SOURCE_KNOWN = [[47, -1], [142, 1], [183, 1], [380, -1]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(value):
    if isinstance(value, (np.ndarray, pd.Series, pd.Index)):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, (list, tuple)):
        return [plain(x) for x in value]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def same(expected, actual):
    if isinstance(expected, (float, int)) and not isinstance(expected, bool):
        return (isinstance(actual, (int, float)) and not isinstance(actual, bool)
                and math.isclose(expected, actual, rel_tol=1e-10, abs_tol=1e-10))
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(same(a, b) for a, b in zip(expected, actual))
    if isinstance(expected, dict) and isinstance(actual, dict):
        return expected.keys() == actual.keys() and all(same(v, actual[k]) for k, v in expected.items())
    return type(expected) is type(actual) and expected == actual


class Checks:
    def __init__(self):
        self.cases = []

    def result(self, name, expected, operation):
        try:
            actual = plain(operation())
        except Exception as exc:
            actual = {"type": type(exc).__name__, "message": str(exc)}
        expected = plain(expected)
        self.cases.append({"case": name, "expected": expected, "actual": actual, "passed": same(expected, actual)})

    def rejection(self, name, operation, permitted=(ValueError, KeyError)):
        try:
            operation()
        except permitted as exc:
            passed, actual = True, {"type": type(exc).__name__, "message": str(exc)}
        except Exception as exc:
            passed, actual = False, {"type": type(exc).__name__, "message": str(exc)}
        else:
            passed, actual = False, "accepted"
        self.cases.append({"case": name, "expected": {"reject": [c.__name__ for c in permitted]},
                           "actual": actual, "passed": passed})


def official_rows(path, checks):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames
        rows = list(reader)
    checks.result("source.raw_sha256", OFFICIAL_SHA256, lambda: digest(path))
    checks.result("source.header", FEATURES + ["Authenticated"], lambda: header)
    checks.result("source.rows_and_unknown", [500, 496],
                  lambda: [len(rows), sum(row["Authenticated"] == "0" for row in rows)])
    checks.result("source.known_physical_rows_excluding_header", SOURCE_KNOWN,
                  lambda: [[i, int(row["Authenticated"])] for i, row in enumerate(rows, 1)
                           if int(row["Authenticated"]) != 0])
    checks.result("source.finite_numeric_measurements", 2500,
                  lambda: sum(math.isfinite(float(row[key])) for key in FEATURES for row in rows))
    return rows


def oracle_distances(row, candidates, fields):
    return [sum((float(row[field]) - float(item[field])) ** 2 for field in fields) for item in candidates]


def oracle_pick(row, references, fields, label_col="Authenticated"):
    eligible = [item for item in references if int(item[label_col]) in {-1, 1}]
    if not eligible:
        return None
    distances = oracle_distances(row, eligible, fields)
    return eligible[min(range(len(distances)), key=distances.__getitem__)]

def describe_vector(vector):
    array = np.asarray(vector)
    return {"shape": list(array.shape), "values": plain(array)}


def frame(points, labels=None, *, index=None):
    result = pd.DataFrame([list(point) + [0.0] * (5 - len(point)) for point in points],
                          columns=FEATURES, index=index)
    if labels is not None:
        result["Authenticated"] = labels
    return result


def read_submission(blob, sizes):
    """Independent reader for the specified two headerless, single-column CSVs."""
    import zipfile

    if not isinstance(blob, bytes):
        raise ValueError("Expected ZIP bytes")
    names = ["submissionA.csv", "submissionB.csv"]
    with zipfile.ZipFile(io.BytesIO(blob)) as submission:
        if sorted(submission.namelist()) != sorted(names):
            raise ValueError("Expected exactly the two named files, once each")
        result = {}
        for name, count in zip(names, sizes, strict=True):
            reader = csv.reader(io.StringIO(submission.read(name).decode("utf-8-sig")))
            rows = list(reader)
            if len(rows) != count or any(len(row) != 1 or row[0] not in {"-1", "1", "+1"} for row in rows):
                raise ValueError("Each required row must contain only one signed class in " + name)
            result[name] = [int(row[0]) for row in rows]
    return result


def output_signature(labels, row_numbers):
    values = np.asarray(labels)
    if values.shape != (len(row_numbers),) or not np.isin(values, [-1, 1]).all():
        raise ValueError("Predictions must retain one signed class per physical row")
    pairs = [f"{idx}:{int(value)}" for idx, value in zip(row_numbers, values, strict=True)]
    return {"rows": len(pairs), "negative": int((values == -1).sum()),
            "positive": int((values == 1).sum()),
            "ordered_row_and_prediction_sha256": hashlib.sha256("\n".join(pairs).encode()).hexdigest()}


def exercise_student(ns, official, checks):
    distance, nearest = ns["squared_distances"], ns["nearest_anchor"]
    scale, batch = ns["fit_scale"], ns["predict_batch"]
    accuracy, archive = ns["accuracy_on_labels"], ns["make_submission"]
    q = np.array([0.0, 0.0])
    points = np.array([[0.0, 0.0], [0.0, 3.0], [2.0, 2.0]])
    checks.result("distance.each_candidate_axis_and_metric", {"shape": [3], "values": [0, 9, 8]},
                  lambda: describe_vector(distance(points, q)))
    checks.result("rank.unknown_exact_match_then_L2_winner", 2,
                  lambda: nearest(points, np.array([0, -1, 1]), q))
    checks.result("distance.axis_on_new_query", [25, 10, 5],
                  lambda: distance(points, np.array([3.0, 4.0])))
    tied = np.array([[0., 0.], [8., 8.], [-3., 4.], [3., 4.]])
    labels = np.array([0, -1, -1, 1])
    checks.result("rank.strict_first_tie_uses_original_position", 2, lambda: nearest(tied, labels, q))
    checks.result("rank.reordering_tied_opposites_changes_label", [2, 1],
                  lambda: first_result(nearest, tied[[0, 1, 3, 2]], labels[[0, 1, 3, 2]], q))
    checks.result("rank.no_known_anchors", None, lambda: nearest(points, np.zeros(3, dtype=int), q))
    checks.result("rank.empty_reference_table", None,
                  lambda: nearest(np.empty((0, 2)), np.array([], dtype=int), q))
    checks.result("distance.empty_reference_table", {"shape": [0], "values": []},
                  lambda: describe_vector(distance(np.empty((0, 2)), q)))
    checks.result("rank.zero_is_valid_measurement", 1,
                  lambda: nearest(np.array([[0., 3.], [2., 0.]]), np.array([1, -1]), q))
    checks.result("scaling.training_means_population_sd_and_constant", [[2, 2, 2], [2, 1, 2]],
                  lambda: scale(np.array([[0., 2., 4.], [4., 2., 0.]])))

    train = frame([(0, 0), (4, 1)], [-1, 1], index=[85, 12])
    one = frame([(3, .1)], index=[504])
    several = frame([(3, .1), (0, 1000)], index=[504, 2])
    checks.result("batch.raw_winner_before_rescaling", {"shape": [1], "values": [1]},
                  lambda: describe_vector(batch(train, one, "raw")))
    checks.result("batch.training_scaled_winner_and_constant_columns", [-1],
                  lambda: batch(train, one, "scaled"))
    checks.result("batch.unseen_outlier_cannot_change_prior_prediction", [-1, 1],
                  lambda: batch(train, several, "scaled"))
    calibration = pd.concat([train, frame([(0, 1000)], [0], index=[71])])
    checks.result("batch.unknown_training_x_used_for_scale_but_not_as_anchor", [1],
                  lambda: batch(calibration, one, "scaled"))
    checks.result("batch.majority_tie_is_positive", [1, 1],
                  lambda: batch(train, several, "majority"))
    m = frame([(9, 9), (10, 10), (5, 5), (1, 1), (0, 0), (2, 2), (3, 3)], [0, 0, 0, 1, -1, -1, 0])
    checks.result("batch.majority_ignores_unknown_and_uses_negative_class", [-1, -1],
                  lambda: batch(m, several, "majority"))
    unknown = m.assign(Authenticated=0)
    for method in ("majority", "raw", "scaled"):
        checks.rejection("batch.no_anchors_" + method, lambda method=method: batch(unknown, one, method), (ValueError,))

    keyed = frame([(0, 7), (6, 1)], [-1, 1], index=[42, 4])
    order = frame([(6, 1), (1, 6), (6, .9)], index=[90, 10, 3])
    permuted = order.loc[:, ["feature2", "feature1", "feature5", "feature3", "feature4"]]
    checks.result("batch.named_feature_order_and_unsorted_query_ids", {"shape": [3], "values": [1, -1, 1]},
                  lambda: describe_vector(batch(keyed, permuted, "raw")))
    checks.result("batch.permuted_query_rows_preserve_predictand_order", [-1, 1, 1],
                  lambda: batch(keyed, permuted.iloc[[1, 2, 0]], "raw"))
    checks.rejection("batch.missing_named_feature", lambda: batch(keyed, permuted.drop(columns="feature3"), "raw"))
    checks.result("score.only_known_truth_is_in_denominator", 2 / 3,
                  lambda: accuracy(np.array([1, 0, -1, -1]), np.array([1, 1, 1, -1])))
    for name, truth, pred in [
        ("all_unknown", [0, 0], [1, -1]), ("empty", [], []),
        ("unequal_length", [1, -1], [1]), ("illegal_prediction", [1, -1], [1, 0]),
        ("illegal_true_class", [1, 7], [-1, 1]),
    ]:
        checks.rejection("score." + name, lambda y=truth, p=pred: accuracy(np.asarray(y), np.asarray(p)),
                         (TypeError, ValueError))

    pa, pb, lengths = np.array([-1, 1, -1]), np.array([1, -1]), (3, 2)
    checks.result("export.independent_parser_headerless_ids_in_given_order",
                  {"submissionA.csv": [-1, 1, -1], "submissionB.csv": [1, -1]},
                  lambda: read_submission(archive(pa, pb, lengths), lengths))
    checks.rejection("export.reject_zero_predicted_class", lambda: archive(np.array([-1, 0, -1]), pb, lengths))
    checks.rejection("export.reject_missing_rows", lambda: archive(pa, pb[:1], lengths))
    checks.rejection("export.reject_prediction_plus_truth_column",
                     lambda: archive(pd.DataFrame({"prediction": pa, "Authenticated": [1, -1, 1]}), pb, lengths),
                     (TypeError, ValueError))

    data = pd.DataFrame(official).apply(pd.to_numeric)
    tests = data["Authenticated"].ne(0)
    folds = [[46, 141], [182, 379]]
    for method, required in {
        "majority": {"labels": [1, 1, 1, 1], "correct": 2, "evaluated": 4, "accuracy": .5},
        "raw": {"labels": [-1, -1, -1, -1], "correct": 2, "evaluated": 4, "accuracy": .5},
        "scaled": {"labels": [-1, -1, 1, -1], "correct": 3, "evaluated": 4, "accuracy": .75},
    }.items():
        def two_balanced_folds(method=method):
            predictions, truth = [], []
            for positions in folds:
                train_part = data.drop(index=positions)
                assert len(train_part) == 498 and (train_part["Authenticated"] == 0).sum() == 496
                x_test = data.loc[positions, FEATURES]
                predictions.extend(np.asarray(batch(train_part, x_test, method)).tolist())
                truth.extend(data.loc[positions, "Authenticated"].tolist())
            return {"labels": predictions, "correct": sum(a == b for a, b in zip(truth, predictions)),
                    "evaluated": len(truth), "accuracy": accuracy(np.array(truth), np.array(predictions))}
        checks.result("extra.reviewer_only_two_balanced_folds_" + method, required, two_balanced_folds)
    # This comparison is agreement with an independent rule, without truth for the 496 rows.
    unknown_positions = np.flatnonzero(~tests.to_numpy())
    references = [o for o in official if int(o["Authenticated"]) != 0]
    desired = [int(oracle_pick(official[i], references, FEATURES)["Authenticated"]) for i in unknown_positions]
    physical = (unknown_positions + 1).tolist()
    checks.result("official.all_496_raw_predictions_keyed_to_physical_rows",
                  output_signature(desired, physical),
                  lambda: output_signature(batch(data, data.loc[~tests, FEATURES], "raw"), physical))


def first_result(nearest, points, labels, query):
    position = nearest(points, labels, query)
    return [position, labels[position]]

def course_folds(ns, official, checks):
    table = pd.DataFrame(official).apply(pd.to_numeric)
    by_features = {tuple(values): i for i, values in enumerate(table[FEATURES].to_numpy(), 1)}
    all_rows = set(by_features.values())
    expected_ids = [r for r, _ in SOURCE_KNOWN]
    truth = [c for _, c in SOURCE_KNOWN]
    checks.rejection("fold.rejected_nonclass_prediction", lambda: ns["score_folds"](table, lambda _t, _q: [0]), (ValueError,))
    checks.rejection("fold.rejected_multiple_predictions", lambda: ns["score_folds"](table, lambda _t, _q: [1, -1]), (ValueError,))
    expected_labels = {"majority": [1, -1, -1, 1], "raw": [-1, -1, -1, -1],
                       "scaled": [-1, -1, 1, -1]}
    for method, predictions in expected_labels.items():
        trace = []

        def model(train_part, query):
            held = [by_features[tuple(v)] for v in query.loc[:, FEATURES].to_numpy()]
            train_ids = {by_features[tuple(v)] for v in train_part.loc[:, FEATURES].to_numpy()}
            trace.append({"held": held, "train_rows": len(train_part),
                          "known_anchors": int(train_part["Authenticated"].isin([-1, 1]).sum()),
                          "unknown": int(train_part["Authenticated"].eq(0).sum()),
                          "exact_training_complement": train_ids == all_rows - set(held),
                          "features_only": set(query.columns) == set(FEATURES)})
            return ns["predict_batch"](train_part, query, method)

        def run_folds():
            scored = ns["score_folds"](table.copy(), model)
            return {"columns": list(scored.columns), "row": scored["row"].tolist(),
                    "truth": scored["truth"].tolist(), "prediction": scored["prediction"].tolist(),
                    "accuracy": ns["accuracy_on_labels"](scored["truth"], scored["prediction"])}

        score = {"majority": 0.0, "raw": 0.5, "scaled": 0.75}[method]
        checks.result("official.course_four_held_out_rows_" + method,
                      {"columns": ["row", "truth", "prediction"], "row": expected_ids,
                       "truth": truth, "prediction": predictions, "accuracy": score}, run_folds)
        checks.result("official.course_model_receives_only_permitted_rows_" + method,
                      [{"held": [rid], "train_rows": 499, "known_anchors": 3, "unknown": 496,
                        "exact_training_complement": True, "features_only": True}
                       for rid in expected_ids], lambda: trace)


def reject_bad_policies(ns, checks):
    import zipfile

    pts, query = np.array([[0., 3.], [2., 2.]]), np.array([0., 0.])
    checks.result("negative_control.manhattan_gives_a_different_answer", {"course": 1, "wrong_L1": 0},
                  lambda: {"course": ns["nearest_anchor"](pts, np.array([-1, 1]), query),
                           "wrong_L1": np.abs(pts - query).sum(axis=1).argmin()})
    truth, pred = [1, 0, -1, -1], [1, 1, 1, -1]
    checks.result("negative_control.counting_unknown_in_accuracy_changes_answer",
                  {"course": 2 / 3, "wrong_all_rows": .5},
                  lambda: {"course": ns["accuracy_on_labels"](np.array(truth), np.array(pred)),
                           "wrong_all_rows": sum(a == b for a, b in zip(truth, pred)) / len(truth)})
    correct = ns["make_submission"](np.array([1, -1]), np.array([-1]), (2, 1))
    bad = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(correct)) as source, zipfile.ZipFile(bad, "w") as faulty:
        faulty.writestr("submissionA.csv", "1,-1\n-1,1\n")
        faulty.writestr("submissionB.csv", source.read("submissionB.csv"))
    checks.rejection("negative_control.reader_rejects_truth_beside_prediction",
                     lambda: read_submission(bad.getvalue(), (2, 1)), (ValueError,))


def execute_student(path):
    import atexit
    from IPython.utils.capture import capture_output
    from ipykernel.inprocess.manager import InProcessKernelManager

    notebook = json.loads(path.read_text(encoding="utf-8"))
    manager = InProcessKernelManager()
    manager.start_kernel()
    shell = manager.kernel.shell
    # Close the temporary history/session before deleting its directory, exactly once.
    atexit.unregister(shell.atexit_operations)
    with capture_output():
        shell.run_line_magic("matplotlib", "inline")
    executed, plots = [], []
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        with capture_output() as outputs:
            result = shell.run_cell("".join(cell["source"]), store_history=True)
        if result.error_before_exec or result.error_in_exec:
            problem = result.error_before_exec or result.error_in_exec
            raise RuntimeError(f"Student cell {cell['id']} raised {type(problem).__name__}: {problem}")
        executed.append(cell["id"])
        if any("image/png" in item.data for item in outputs.outputs):
            plots.append(cell["id"])
    return manager, shell.user_ns, {"cell_ids": executed, "rendered_figure_cells": plots}

def check_default_figures(ns, normal, checks):
    checks.result("notebook.blank_entry_shows_only_two_prelock_plots",
                  ["unlabeled-projection", "draw-boundary"], lambda: normal["rendered_figure_cells"])
    checks.result("notebook.blank_model_keeps_official_row_labels_and_scores_closed", [True, True, True],
                  lambda: ["내 식" not in ns["rules"], "comparison" not in ns, "known_paintings" not in ns])
    def scatter():
        positions = np.asarray(ns["ax"].collections[0].get_offsets())
        expected = ns["paintings"].loc[ns["paintings"]["Authenticated"] == 0, ["feature1", ns.get("vertical", "feature3")]]
        return [list(positions.shape), bool(np.allclose(positions, expected))]
    checks.result("notebook.unlabelled_projection_contains_exact_496_points", [[496, 2], True], scatter)

    def boundaries():
        lines = ns["boundary_figure"].axes[0].get_lines()
        matches = []
        for line, m in zip(lines, (1, 10), strict=True):
            u, v = line.get_xdata(), line.get_ydata()
            left = (m * u) ** 2 + (v - 5) ** 2
            right = (m * (u - 4)) ** 2 + v ** 2
            matches.append(bool(len(u) > 1 and np.allclose(left, right)))
        return matches
    checks.result("notebook.both_plotted_boundaries_are_equidistant_in_their_units", [True, True], boundaries)


def marked_teacher_blocks(path):
    markup = path.read_text(encoding="utf-8")
    fence = chr(96) * 3
    blocks = re.findall(r"^" + fence + r"python[ \t]*\n(.*?)^" + fence + r"[ \t]*$", markup, re.M | re.S)
    result = {}
    for block in blocks:
        line = block.splitlines()[0].strip()
        if line.startswith("# exercise:"):
            key = line.split(":", 1)[1].strip()
            if key in result:
                raise ValueError("Repeated exercise block: " + key)
            result[key] = block
    return result


def match_teacher(ns, checks):
    match_icon = ns["match_icon"]
    provided = ns["query_icon"], ns["gallery"]
    checks.result("teacher.matching_given_original_and_reversed", [12, 12],
                  lambda: [match_icon(*provided), match_icon(provided[0], list(reversed(provided[1])))])
    q = (601, "M", (0, 0))
    gallery = [(8, "M", (0, 0)), (91, "F", (0, 2)), (7, "F", (2, 0)), (20, "F", (0, 3))]
    checks.result("teacher.matching_fresh_tie_smallest_candidate_id", [7, 7],
                  lambda: [match_icon(q, gallery), match_icon(q, gallery[::-1])])
    checks.result("teacher.matching_no_opposite_and_empty", [None, None],
                  lambda: [match_icon(q, [(17, "M", (0, 0))]), match_icon(q, [])])
    checks.result("teacher.matching_query_and_gallery_names_are_separate", 601,
                  lambda: match_icon(q, [(13, "M", (0, 0)), (601, "F", (0, 0)), (12, "F", (3, 7))]))
    checks.result("teacher.matching_fresh_squared_not_manhattan", 46,
                  lambda: match_icon((3, "F", (0, 0)), [(20, "M", (0, 3)), (46, "M", (2, 2))]))


def run_registered_student_path(path, manager, ns, teacher_ns, checks):
    from IPython.utils.capture import capture_output

    notebook_cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    cells = {c["id"]: c for c in notebook_cells}
    prose = "\n".join("".join(c["source"]) for c in notebook_cells if c["cell_type"] == "markdown")
    pattern = r"(?:다수결.{0,45}(?:0\s*/\s*4|네 점 모두 틀렸)|(?:^|\s)0\s*/\s*4(?:\s|$))"
    checks.result("guidance.original_static_majority_answer_no_longer_printed", False,
                  lambda: re.search(pattern, prose) is not None)
    checks.result("notebook.archived_blank_template_has_no_saved_result_outputs", [],
                  lambda: [c["id"] for c in notebook_cells if c.get("outputs")])
    ns["rules"]["내 식"] = teacher_ns["teacher_rule"]
    images = []
    printed = ""
    for cell_id in ("reveal-result", "inspect-after-lock"):
        with capture_output() as captured:
            result = manager.kernel.shell.run_cell("".join(cells[cell_id]["source"]), store_history=True)
        if result.error_before_exec or result.error_in_exec:
            raise ValueError(f"Post-registration student cell failed: {cell_id}")
        if any("image/png" in item.data for item in captured.outputs):
            images.append(cell_id)
        if cell_id == "reveal-result":
            printed = captured.stdout
    checks.result("registered.printed_scores_match_four_held_out_rows",
                  {"majority": "0/4", "raw": "2/4", "scaled": "3/4", "내 식": "3/4"},
                  lambda: dict(re.findall(r"^(majority|raw|scaled|내 식)\s+(\d+/\d+)", printed, re.M)))
    comparison = ns["comparison"]
    checks.result("registered.real_score_rows_and_baselines",
                  {"rows": [47, 142, 183, 380], "truth": [-1, 1, 1, -1],
                   "majority": [1, -1, -1, 1], "raw": [-1, -1, -1, -1], "scaled": [-1, -1, 1, -1]},
                  lambda: {"rows": comparison.index.tolist(), "truth": comparison["감정값"].tolist(),
                           **{k: comparison[k].tolist() for k in ("majority", "raw", "scaled")}})
    checks.result("registered.teacher_classifier_official_predictions", [-1, -1, 1, -1],
                  lambda: comparison["내 식"].tolist())
    checks.result("registered.post_lock_chart_displays_four_labeled_paintings",
                  {"plot": ["inspect-after-lock"], "counts": {"authentic": 2, "replica": 2}, "plotted_points": 4},
                  lambda: {"plot": images, "counts": ns["known_paintings"]["class_name"].value_counts().to_dict(),
                           "plotted_points": sum(len(o.get_offsets()) for o in ns["ax"].collections)})
    return {"registered": "teacher_rule", "figure_cells": images, "four_public_predictions": comparison["내 식"].tolist()}

def run(root, notebook, teacher, public_csv, details=False):
    import os
    import platform
    import shutil
    from contextlib import chdir

    initial = {p: digest(p) for p in (notebook, teacher, public_csv)}
    checks = Checks()
    records = official_rows(public_csv, checks)
    normal, reference = {}, {}
    manager = None
    with tempfile.TemporaryDirectory(prefix="week01-public-course-") as temporary:
        directory = Path(temporary)
        lesson_dir = directory / "lessons/week01"
        data_dir = lesson_dir / "data"
        data_dir.mkdir(parents=True)
        shutil.copyfile(public_csv, data_dir / "antique_training.csv")
        env = {"PYDEVD_DISABLE_FILE_VALIDATION": os.environ.get("PYDEVD_DISABLE_FILE_VALIDATION")}
        os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
        for key in ("IPYTHONDIR", "MPLCONFIGDIR", "JUPYTER_CONFIG_DIR", "JUPYTER_RUNTIME_DIR"):
            where = directory / key.lower()
            where.mkdir()
            env[key] = os.environ.get(key)
            os.environ[key] = str(where)
        try:
            with chdir(lesson_dir):
                manager, ns, normal = execute_student(notebook)
                normal["provided_data_files"] = [p.name for p in data_dir.iterdir() if p.is_file()]
                check_default_figures(ns, normal, checks)
                check_input_practice(notebook, ns, checks)
                check_worked_numbers(ns, checks)
                checks.result("plot_choice.unlabeled_vertical_feature4",
                              {"figure_rendered": True, "axis": "feature4", "observations": 496,
                               "coordinates_match_named_column": True},
                              lambda: changed_feature_chart(notebook, manager, ns, "unlabeled-projection", "vertical", "feature4"))
                required = ["squared_distances", "nearest_anchor", "fit_scale", "predict_batch",
                            "accuracy_on_labels", "make_submission"]
                checks.result("notebook.public_worked_helpers_available", required,
                              lambda: [name for name in required if callable(ns.get(name))])
                if all(callable(ns.get(name)) for name in required):
                    exercise_student(ns, records, checks)
                    reject_bad_policies(ns, checks)
                reference, teacher_ns = execute_teacher(teacher, ns, checks)
                normal["after_teacher_registration"] = run_registered_student_path(notebook, manager, ns, teacher_ns, checks)
                checks.result("plot_choice.registered_class_feature5",
                              {"figure_rendered": True, "axis": "feature5", "observations": 4,
                               "coordinates_match_named_column": True},
                              lambda: changed_feature_chart(notebook, manager, ns, "inspect-after-lock", "chosen_feature", "feature5"))
                scored_scope = ns if callable(ns.get("score_folds")) else teacher_ns
                checks.result("course.actual_fold_helper_available", True,
                              lambda: callable(scored_scope.get("score_folds")))
                if callable(scored_scope.get("score_folds")):
                    course_folds(scored_scope, records, checks)
        finally:
            if manager is not None:
                manager.kernel.shell.atexit_operations()
                manager.shutdown_kernel()
            for key, value in env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    display_path = lambda p: str(p.relative_to(root)) if p.is_relative_to(root) else p.name
    if any(digest(p) != fingerprint for p, fingerprint in initial.items()):
        raise ValueError("An audited course input changed during execution; replay the stable files")
    failures = [case for case in checks.cases if not case["passed"]]
    evidence = {c["case"]: c["actual"] for c in checks.cases
                if c["case"].startswith(("official.course_four_", "official.all_496", "extra.", "registered.", "practice.", "plot_choice.",
                                        "guidance.", "teaching_numbers.",
                                        "teacher.", "negative_control.", "source.known_physical",
                                        "export.independent_parser", "scaling."))}
    report = {"status": "failed" if failures else "passed",
              "inputs": {display_path(p): fingerprint for p, fingerprint in initial.items()},
              "official_public_source": OFFICIAL_TRAIN,
              "runtime": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__},
              "normal_execution": normal, "teacher_execution": reference,
              "case_count": len(checks.cases), "passed_count": len(checks.cases) - len(failures),
              "evidence": evidence, "failures": failures,
              "scope": "Blank student answer slots were run as supplied. Course evaluation uses four held-out publicly known training rows. The two balanced folds are an additional reviewer diagnostic. The 496 unknown labels provide no accuracy denominator. Learner achievement and hidden-contest accuracy were not observed. All corrupt submissions use reviewer-made public fixtures."}
    report["checker_sha256"] = digest(Path(__file__).resolve())
    report["execution_counts"] = {"blank_student_code_cells": len(normal["cell_ids"]),
                                  "default_figure_cells": len(normal["rendered_figure_cells"]),
                                  "public_teacher_code_blocks": len(reference["executed_marked_exercises"]),
                                  "student_cells_replayed_after_rule_registration": 2,
                                  "figure_cells_rerun_with_a_changed_public_feature": 2}
    if details:
        report["checks"] = checks.cases
    else:
        report["passed_cases"] = [c["case"] for c in checks.cases if c["passed"]]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--round", type=int, dest="round_id", help="Replay the formal candidate and companions archived in this round")
    parser.add_argument("--notebook", type=Path)
    parser.add_argument("--teacher", type=Path)
    parser.add_argument("--public", type=Path, dest="public_csv")
    parser.add_argument("--prove-detection", action="store_true", help="Also run two known wrong policies on disposable copies of this candidate")
    parser.add_argument("--details", action="store_true", help="Include expected and actual values for every check")
    args = parser.parse_args()
    root = args.root.resolve()
    def under(path, default):
        return (root / (path or default)).resolve()
    try:
        binding = None
        if args.round_id is not None:
            if any([args.notebook, args.teacher, args.public_csv]):
                raise ValueError("Use either a formal round or explicit input overrides")
            notebook, teacher, dataset, binding = archived_sources(root, args.round_id)
        else:
            notebook = under(args.notebook, "lessons/week01/week01_foundations.ipynb")
            teacher = under(args.teacher, "lessons/week01/week01_foundations_teacher.md")
            dataset = under(args.public_csv, "lessons/week01/data/antique_training.csv")
        report = run(root, notebook, teacher, dataset, args.details)
        if binding:
            report["archive_binding"] = binding
        if args.prove_detection and report["status"] == "passed":
            report["wrong_policy_runs"] = prove_detection(root, notebook, teacher, dataset)
    except Exception as exc:
        report = {"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report["status"] == "passed" else 1

def execute_teacher(path, ns, checks):
    blocks = marked_teacher_blocks(path)
    required = ["classifier", "matching"]
    missing = [name for name in required if name not in blocks]
    if missing:
        raise ValueError("Missing marked executable teacher exercise: " + ", ".join(missing))
    scope = dict(ns)
    scope["rules"] = dict(ns["rules"])
    receipts = []
    for name in required:
        block = blocks[name]
        out = io.StringIO()
        with redirect_stderr(out), redirect_stdout(out):
            exec(compile(block, f"{path.name}#exercise-{name}", "exec"), scope)
        receipts.append({"exercise": name, "source_sha256": hashlib.sha256(block.encode()).hexdigest()})
    match_teacher(scope, checks)
    classifier_teacher(scope, checks)
    return {"executed_marked_exercises": receipts}, scope

def classifier_teacher(ns, checks):
    teacher, batch = ns["teacher_rule"], ns["predict_batch"]
    published = frame([(0,), (1,), (-6,), (6,)], [-1, -1, 1, 1])
    checks.result("teacher.given_centroids_disagree_with_nearest_anchor", {"center": [1], "nearest": [-1]},
                  lambda: {"center": teacher(published, frame([(0,)])),
                           "nearest": batch(published, frame([(0,)]), "raw")})
    # Class centers on this fresh one-dimensional input are 3 (negative) and 1 (positive).
    fresh = frame([(1,), (5,), (-10,), (12,), (300,)], [-1, -1, 1, 1, 0], index=[95, 8, 70, 4, 50])
    tests = frame([(1,), (3,), (2,)], index=[80, 5, 40]).loc[:, list(reversed(FEATURES))]
    checks.result("teacher.fresh_class_centers_report_in_query_order_and_positive_at_exact_tie", [1, -1, 1],
                  lambda: teacher(fresh, tests))
    checks.result("teacher.one_known_class_returns_that_class", [-1, -1, -1],
                  lambda: teacher(fresh[fresh["Authenticated"].ne(1)], tests))
    checks.rejection("teacher.no_known_class", lambda: teacher(fresh[fresh["Authenticated"].eq(0)], tests),
                     (ValueError,))
    # With one anchor of each class, prototypes equal those anchors. An extreme query cannot change the model.
    train = frame([(0, 0), (4, 1)], [-1, 1])
    checks.result("teacher.scaler_learns_only_from_training", [[-1], [-1, 1]],
                  lambda: [teacher(train, frame([(3, .1)])), teacher(train, frame([(3, .1), (0, 1000)]))])


def check_input_practice(path, ns, checks):
    """Run an auditor answer on the unfilled, public source-reconstruction exercises."""
    measure, notes = ns["measure"], ns["notes"]

    def aligned(remarks):
        joined = measure.merge(remarks, how="left", left_on="painting", right_on="work_id",
                               validate="many_to_one", indicator=True)
        return [[p, None if pd.isna(a) else a, None if pd.isna(b) else b,
                 None if pd.isna(label) else label, str(origin)]
                for p, a, b, label, origin in
                joined[["painting", "f_a", "f_b", "verdict", "_merge"]].itertuples(index=False, name=None)]

    rows = [["K7", 0, 5, -1, "both"], ["M2", 4, None, 0, "both"],
            ["P8", 3, 4, 1, "both"], ["D1", 1, 2, None, "left_only"]]
    checks.result("practice.public_csv_ids_zero_missing_and_absent_note", rows, lambda: aligned(notes))
    checks.result("practice.reversed_record_lookup_preserves_painting_id", rows,
                  lambda: aligned(notes.iloc[::-1]))
    practice = ns["practice_table"]
    hand = practice([[0, 3], [2, 2], [0, 0]], [-1, 1, 0])
    q = practice([[0, 0], [0, 3]])
    checks.result("practice.hand_table_keeps_labels_zero_features_and_row_order",
                  {"train_columns": FEATURES + ["Authenticated"], "query_columns": FEATURES,
                   "train": [[0, 3, 0, 0, 0, -1], [2, 2, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0]],
                   "predictions": [1, -1]},
                  lambda: {"train_columns": list(hand.columns), "query_columns": list(q.columns),
                           "train": hand.to_numpy(), "predictions": ns["predict_batch"](hand, q, "raw")})
    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    prompt = "".join(next(c["source"] for c in cells if c["id"] == "orientation-dot"))
    records = re.findall(r"\[\s*\d+(?:\s*,\s*\d+){3}\s*\]", prompt)
    if len(records) != 2:
        raise ValueError("Expected the two public four-value sensor exports")
    row_major, column_major = [np.array(json.loads(line)).reshape(2, 2) for line in records]
    restored = column_major.T

    def verify_original():
        d = restored - ns["query"]
        return {"restored": restored.tolist(), "first_format": row_major.tolist(),
                "dot": [v @ v for v in d], "distance": ns["squared_distances"](restored, ns["query"]),
                "if_transpose_omitted": ns["squared_distances"](column_major, ns["query"])}
    checks.result("practice.actual_sensor_exports_transpose_and_dot",
                  {"restored": [[0, 5], [4, 0]], "first_format": [[0, 5], [4, 0]],
                   "dot": [10, 17], "distance": [10, 17], "if_transpose_omitted": [9, 20]}, verify_original)
    checks.result("practice.changed_query_exposes_wrong_sensor_orientation",
                  {"correct_distances": [13, 10], "wrong_distances": [10, 13], "winners": [1, 0]},
                  lambda: {"correct_distances": ns["squared_distances"](restored, [3, 3]),
                           "wrong_distances": ns["squared_distances"](column_major, [3, 3]),
                           "winners": [ns["nearest_anchor"](a, [-1, 1], [3, 3]) for a in [restored, column_major]]})

def changed_feature_chart(path, manager, ns, cell_id, variable, replacement):
    from IPython.utils.capture import capture_output

    cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
    source = "".join(next(c["source"] for c in cells if c["id"] == cell_id))
    pattern = r'(?m)^(\s*' + variable + r'\s*=\s*)["\']feature\d+["\']'
    source, changed = re.subn(pattern, lambda m: m[1] + repr(replacement), source, count=1)
    if changed != 1:
        raise ValueError("Could not change the documented feature selector in " + cell_id)
    with capture_output() as captured:
        run = manager.kernel.shell.run_cell(source, store_history=True)
    if run.error_before_exec or run.error_in_exec:
        raise ValueError("Edited chart failed: " + cell_id)
    shown = any("image/png" in item.data for item in captured.outputs)
    ax = ns["ax"]
    if variable == "vertical":
        expected = ns["unknown_x"][["feature1", replacement]].to_numpy()
        actual = np.asarray(ax.collections[0].get_offsets())
        return {"figure_rendered": shown, "axis": ax.get_ylabel(), "observations": len(actual),
                "coordinates_match_named_column": bool(np.allclose(actual, expected))}
    grouped = {name: [] for name in ("replica", "authentic")}
    ticks = [tick.get_text() for tick in ax.get_yticklabels()]
    for artist in ax.collections:
        for xpos, ypos in np.asarray(artist.get_offsets()):
            grouped[ticks[round(float(ypos))]].append(float(xpos))
    actual = {name: sorted(values) for name, values in grouped.items()}
    expected = {name: sorted(group[replacement].tolist())
                for name, group in ns["known_paintings"].groupby("class_name")}
    return {"figure_rendered": shown, "axis": ax.get_xlabel(), "observations": sum(map(len, actual.values())),
            "coordinates_match_named_column": same(expected, actual)}


def check_worked_numbers(ns, checks):
    ds, fit = ns["squared_distances"], ns["fit_scale"]
    anchors = ns["small_x"][1:]
    q = ns["query"]
    center, width = fit(anchors)
    checks.result("teaching_numbers.example_unit_change", {"original": [10, 17], "times_ten": [901, 116],
                  "center": [2, 2.5], "width": [2, 2.5], "scaled_d2": [2.41, 2.81]},
                  lambda: {"original": ds(anchors, q), "times_ten": ds(anchors * [10, 1], q * [10, 1]),
                           "center": center, "width": width, "scaled_d2": ds((anchors-center)/width, (q-center)/width)})
    x = np.array([[2., 7.], [4., 7.], [6., 7.]])
    sample = np.array([5., 8.])
    for factor, raw in ((1, [10, 2]), (100, [90001, 10001])):
        def verify(factor=factor):
            values, query = x * [factor, 1], sample * [factor, 1]
            means, widths = fit(values)
            known = values[[0, 2]]
            return {"raw": ds(known, query), "scaled": ds((known-means)/widths, (query-means)/widths)}
        checks.result("teaching_numbers.constant_column_with_multiplier_" + str(factor),
                      {"raw": raw, "scaled": [4.375, 1.375]}, verify)

    paints = ns["paintings"]
    train = paints.drop(index=182)
    x = train[FEATURES].to_numpy()
    q = paints.loc[182, FEATURES].to_numpy()
    labels = train["Authenticated"].to_numpy()
    center, width = fit(x)
    checks.result("guidance.row_183_raw_and_scaled_neighbor_ids", [47, 142],
                  lambda: [int(train.index[ns["nearest_anchor"](a, labels, point)]) + 1
                           for a, point in [(x, q), ((x-center)/width, (q-center)/width)]])
    training = [0., 2.] + [-.1]*5 + [1.5]*5
    moved = []
    for value, skip in ((0., 0), (2., 1), (.9, None)):
        others = [v for i, v in enumerate(training) if i != skip]
        neighbors = sorted(others, key=lambda v: abs(v-value))[:5]
        moved.append((value + sum(neighbors)) / 6)
    checks.result("teaching_numbers.optional_cloud_hand_result",
                  {"coordinates": [-1/12, 19/12, 7/5], "before_after_classes": [-1, 1]},
                  lambda: {"coordinates": moved, "before_after_classes": [[-1, 1][ns["nearest_anchor"](
                      [[a], [b]], [-1, 1], [v])] for a, b, v in [(0., 2., .9), tuple(moved)]]})

def prove_detection(root, notebook, teacher, public_csv):
    """Run two known, deliberately wrong policies on disposable copies of this candidate."""
    import subprocess
    import sys

    variants = [
        ("last_equal_distance", "anchor-loop", "if distance < best_distance:", "if distance <= best_distance:",
         "rank.strict_first_tie_uses_original_position"),
        ("scale_fitted_on_query", "predict-model", "center, width = fit_scale(x)",
         "center, width = fit_scale(np.concatenate([x, q], axis=0))",
         "batch.unseen_outlier_cannot_change_prior_prediction"),
    ]
    outcomes = []
    with tempfile.TemporaryDirectory(prefix="week01-wrong-policies-") as tmp:
        for name, cell_id, old, wrong, marker in variants:
            trial = json.loads(notebook.read_text(encoding="utf-8"))
            cell = next(c for c in trial["cells"] if c["id"] == cell_id)
            source = "".join(cell["source"])
            if source.count(old) != 1:
                raise ValueError("Unable to locate this candidate's known test mutation: " + name)
            cell["source"] = source.replace(old, wrong).splitlines(keepends=True)
            altered = Path(tmp) / (name + ".ipynb")
            altered.write_text(json.dumps(trial, ensure_ascii=False), encoding="utf-8")
            ran = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--root", str(root),
                                  "--notebook", str(altered), "--teacher", str(teacher), "--public", str(public_csv)],
                                 check=False, capture_output=True, text=True)
            attempt = json.loads(ran.stdout)
            failures = [item["case"] for item in attempt.get("failures", [])]
            if ran.returncode != 1 or marker not in failures:
                raise ValueError("Expected wrong policy to fail its specific control: " + name)
            outcomes.append({"incorrect_policy": name, "exit_status": ran.returncode, "detected_by": failures})
    return outcomes

def archived_sources(root, number):
    case = root / "reviews/week01-contest-20261118"
    folder = case / "rounds" / f"{number:04d}"
    record_path = folder / "round.json"
    contract_path = case / "contract.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    notebook = folder / "candidate.ipynb"
    if digest(contract_path) != record["contract_sha256"] or digest(notebook) != record["candidate_sha256"]:
        raise ValueError("Archived candidate or contract differs from the formal round")
    sources = {contract["lesson_path"]: record["candidate_sha256"]}
    inputs = {}
    for entry in record["companions"]:
        archived = root / entry["snapshot"]
        if digest(archived) != entry["sha256"]:
            raise ValueError("Archived companion differs: " + entry["path"])
        sources[entry["path"]] = entry["sha256"]
        inputs[Path(entry["path"]).name] = archived
    binding = {"round": number, "record": str(record_path.relative_to(root)), "round_sha256": digest(record_path),
               "contract_sha256": record["contract_sha256"], "published_sources": sources}
    return notebook, inputs["week01_foundations_teacher.md"], inputs["antique_training.csv"], binding

if __name__ == "__main__":
    raise SystemExit(main())
