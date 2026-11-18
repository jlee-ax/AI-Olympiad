"""Replay the independent Week 1 cases against a frozen review round.

Run with python independent/verify_round.py path/to/rounds/0001. The notebook's
ordinary Restart/Run All is a separate check. This script exercises selected
candidate expressions and teacher functions, then compares them to independently
derived answers. No student data is used.
"""

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, pvariance

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal_numbers(actual, expected):
    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def correct_count(values, threshold):
    total = 0
    for v in values:
        if v is not None and v >= threshold:
            total += 1
    return total


def capture_plot_values(frame, edges):
    categories = ["Ridge", "Bay", "Glen"]
    fig, (hist_ax, group_ax) = plt.subplots(1, 2)
    try:
        hist, _, _ = hist_ax.hist(frame["closing_count"].dropna(), bins=edges)
        sns.barplot(data=frame, x="zone", y="closing_count", order=categories,
                    errorbar=None, ax=group_ax)
        fig.canvas.draw()
        return hist.astype(int).tolist(), [bar.get_height() for bar in group_ax.patches]
    finally:
        plt.close(fig)


def check_table(original_records, area_csv, teacher):
    # Only the two measurements used in these descriptive summaries are mapped.
    # Earlier periods are deliberately unmeasured. The binary future outcome is
    # a separate prediction target, not a count or a feature in these summaries.
    results = []
    for changed in (False, True):
        text = original_records.replace("b,z6,4,0,\n", "b,z6,4,0,10\n") if changed else original_records
        raw = list(csv.DictReader(io.StringIO(text)))
        codes = {r["area_code"]: r["area_name"] for r in csv.DictReader(io.StringIO(area_csv))}
        first = [int(r["first_s"]) for r in raw if r["first_s"]]
        data = pd.read_csv(io.StringIO(text))
        records = data.rename(columns={"observation": "slip", "zone_code": "station",
                                       "first_s": "closing_count", "second_s": "meal_count"})
        records["morning_count"] = pd.NA
        records["pause_count"] = pd.NA
        lookup = pd.read_csv(io.StringIO(area_csv)).rename(
            columns={"area_code": "box_id", "area_name": "zone"})
        try:
            records.merge(lookup, on="station", how="left")
        except KeyError as error:
            assert error.args == ("station",)
        else:
            raise AssertionError("The one-name example must fail for two different key names")
        linked = teacher["attach_zones"](records, lookup.iloc[::-1])
        assert linked["zone"].tolist() == [codes[r["zone_code"]] for r in raw]
        assert len(linked) == len(raw) == 6
        selected, grouped = teacher["summarize_returns"](linked, 0)
        g = grouped.loc[["Ridge", "Bay", "Glen"]]
        assert g["rows"].tolist() == [3, 2, 1]
        assert g["observed"].tolist() == [3, 2 if changed else 1, 1]
        assert (selected["closing_count"] == 0).sum() == 1
        expected_means = [16 / 3, 7 if changed else 4, 0]
        equal_numbers(g["mean_books"], expected_means)
        equal_numbers([selected["closing_count"].mean(), selected["closing_count"].var(ddof=0)],
                      [mean(first), pvariance(first)])
        equal_numbers([mean(first), pvariance(first)], [5 if changed else 4, 35 / 3 if changed else 8])
        assert mean(int(row["second_s"]) for row in raw) == 4
        hist, heights = capture_plot_values(selected, [0, 4, 8, 12])
        equal_numbers(heights, expected_means)
        assert hist == [2, 2, 2 if changed else 1]
        bins, _ = np.histogram(first, bins=[0, 6, 12])
        assert bins.tolist() == [3, 3 if changed else 2]
        results.append({"observed": len(first), "group_rows": g["rows"].tolist(),
                        "group_observed": g["observed"].tolist(), "group_means": heights,
                        "mean": mean(first), "population_variance": pvariance(first),
                        "histogram": hist, "changed_bins": bins.tolist()})
    return results


def check_round(folder):
    info = json.loads((folder / "round.json").read_text())
    notebook_path = folder / "candidate.ipynb"
    assert digest(notebook_path) == info["candidate_sha256"]
    inputs = folder / "inputs"
    for item in info["companions"]:
        assert digest(inputs / Path(item["snapshot"]).name) == item["sha256"]
    cells = {c["id"]: "".join(c["source"]) for c in json.loads(notebook_path.read_bytes())["cells"]}
    teacher_text = (inputs / "week01_foundations_teacher.md").read_text()
    functions = []
    for code in re.findall(r"```python\n(.*?)\n```", teacher_text, re.S):
        functions.extend(s for s in ast.parse(code).body if isinstance(s, ast.FunctionDef))
    teacher = {"np": np, "pd": pd}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "teacher-functions", "exec"), teacher)
    assert {"count_at_least", "attach_zones", "summarize_returns"} <= set(teacher)

    values = [0, None, 3, 7, 7]
    python_results = [teacher["count_at_least"](seq, q) for seq, q in [(values, 7), (values, 0), ([], 0)]]
    assert python_results == [correct_count(values, 7), correct_count(values, 0), correct_count([], 0)] == [2, 4, 0]
    # Compare the worked cell's strict boundary with the required inclusive edit.
    fn = next(s for s in ast.parse(cells["python-example"]).body if isinstance(s, ast.FunctionDef))
    ns = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "python-example", "exec"), ns)
    assert ns["count_over"](values, 7) == 0
    try:
        teacher["count_at_least"](values, -1)
    except ValueError:
        pass
    else:
        raise AssertionError("The stated invalid criterion should raise ValueError")

    raw = [[2, 8], [4, 4], [6, 0]]
    a = np.array(raw)
    array_env = {"counts": a}
    # Run the exact two reduction assignments from the candidate on a different shape.
    for node in ast.parse(cells["reduce-period"]).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in {"by_period", "by_record"}:
                exec(compile(ast.Module(body=[node], type_ignores=[]), "reduce-period", "exec"), array_env)
    assert array_env["by_period"].tolist() == list(map(mean, zip(*raw))) == [4, 4]
    assert array_env["by_record"].tolist() == list(map(mean, raw)) == [5, 4, 3]
    assert array_env["by_period"].shape == (2,) and array_env["by_record"].shape == (3,)
    equal_numbers(a.var(axis=0), [pvariance(col) for col in zip(*raw)])
    equal_numbers(a.var(axis=0), [8 / 3, 32 / 3])
    # Here the evaluator adapted the taught operations and supplied aligned test weights.
    assert (a @ [1, -0.5]).tolist() == [-2, 2, 6]
    assert a.T.tolist() == [[2, 4, 6], [8, 4, 0]]
    assert a.reshape(2, 3).tolist() == [[2, 8, 4], [4, 6, 0]]
    assert (a + [1, -2])[0].tolist() == [3, 6]
    try:
        a + np.array([1, 2, 3])
    except ValueError:
        pass
    else:
        raise AssertionError("Unaligned row offsets should fail")
    assert (a + np.array([1, 2, 3]).reshape(3, 1)).tolist() == [[3, 9], [6, 6], [9, 3]]

    # Verify the public transfer results, independently of the teacher's pandas grouping.
    public_text = (inputs / "foundations_returns_transfer.csv").read_text()
    area_text = (inputs / "foundations_boxes.csv").read_text()
    raw_records = list(csv.DictReader(io.StringIO(public_text)))
    key = {row["box_id"]: row["zone"] for row in csv.DictReader(io.StringIO(area_text))}
    frame = pd.read_csv(io.StringIO(public_text))
    lk = pd.read_csv(io.StringIO(area_text))
    linked = teacher["attach_zones"](frame, lk)
    pd.testing.assert_frame_equal(linked, teacher["attach_zones"](frame, lk.iloc[::-1]))
    published = []
    for q in (4, 6):
        chosen = [r for r in raw_records if r["meal_count"] and int(r["meal_count"]) >= q]
        groups = defaultdict(list)
        for row in chosen:
            groups[key[row["station"]]].append(row)
        selected, summary = teacher["summarize_returns"](linked, q)
        assert selected["slip"].tolist() == [x["slip"] for x in chosen]
        for z, rows in groups.items():
            valid = [int(r["closing_count"]) for r in rows if r["closing_count"]]
            equal_numbers(summary.loc[z, ["rows", "observed", "sum_books", "mean_books"]],
                          [len(rows), len(valid), sum(valid), mean(valid)])
        published.append({"cutoff": q, "selected": selected["slip"].tolist(),
                          "west_observed": int(summary.loc["West", "observed"]),
                          "west_mean": float(summary.loc["West", "mean_books"])})
    assert math.isclose(published[0]["west_mean"], 13/3) and published[1]["west_mean"] == 3
    assert published[0]["west_observed"] == 3 and published[1]["west_observed"] == 2

    records = ("zone_code,observation,second_s,following_pass,first_s\n"
               "r,z8,8,0,2\nb,z7,4,1,4\nr,z5,0,1,6\nb,z6,4,0,\n"
               "g,z1,2,0,0\nr,z4,6,1,8\n")
    areas = "area_code,area_name\nb,Bay\nr,Ridge\ng,Glen\n"
    return {"round_sha256": digest(folder / "round.json"), "candidate_sha256": digest(notebook_path),
            "frozen_oracle_sha256": "f8e0926c4f4c6744eaa4bffacddd92372da64adc9347fc50fc4b00197114945f",
            "python": python_results, "means_by_axis": [array_env["by_period"].tolist(), array_env["by_record"].tolist()],
            "public_transfer": published, "independent_transfer": check_table(records, areas, teacher)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_directory", type=Path)
    print(json.dumps(check_round(parser.parse_args().round_directory), indent=2, ensure_ascii=False))
