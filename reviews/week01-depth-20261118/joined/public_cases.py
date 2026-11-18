"""Cross-check only the public student notebook and its public teacher solutions."""
import contextlib
import csv
import hashlib
import io
import json
import linecache
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / "lessons/week01"
STUDENT = LESSON / "week01_foundations.ipynb"
TEACHER = LESSON / "week01_foundations_teacher.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(name):
    with (LESSON / "data" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def numeric(value):
    return None if value == "" else int(value)


def reference(rows, areas, cutoff, bins):
    selected, bins_members = [], [[] for _ in range(len(bins)-1)]
    groups = defaultdict(list)
    for row in rows:
        lunch = numeric(row["meal_count"])
        if lunch is None or lunch < cutoff:
            continue
        selected.append(row["slip"])
        value = numeric(row["closing_count"])
        groups[areas[row["station"]]].append(value)
        if value is not None:
            for i, (lo, hi) in enumerate(zip(bins, bins[1:])):
                if lo <= value < hi or (i == len(bins)-2 and value == hi):
                    bins_members[i].append(row["slip"])
                    break
    summaries = {}
    for area, group in groups.items():
        observed = [x for x in group if x is not None]
        summaries[area] = [len(group), len(observed),
                           sum(observed) if observed else None,
                           sum(observed)/len(observed) if observed else None]
    return selected, summaries, bins_members


def check(condition, name):
    if not condition:
        raise AssertionError(name)


def equal_numeric(actual, expected):
    return bool(pd.isna(actual)) if expected is None else math.isclose(float(actual), expected)


def main():
    public = json.loads(STUDENT.read_text(encoding="utf-8"))
    teacher = TEACHER.read_text(encoding="utf-8")
    env = {"__name__": "__main__"}
    figures = []
    executed = []
    traces = {}
    artist_sources = []
    active = ""
    def record_figure(*args, **kwargs):
        figure = plt.gcf()
        charts = []
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        for ax in figure.axes:
            heights = [float(p.get_height()) for p in ax.patches]
            bbox = ax.get_tightbbox(renderer).transformed(figure.transFigure.inverted())
            charts.append(dict(pane_bounds=[round(v, 5) for v in bbox.extents],
                               xlabel=ax.get_xlabel(), ylabel=ax.get_ylabel(),
                               heights=heights, ticks=list(map(float, ax.get_yticks())),
                               limits=list(map(float, ax.get_ylim()))))
        figures.append(charts)
        artist_sources.append(active)
        plt.close(figure)

    plt.show = record_figure
    with contextlib.redirect_stdout(io.StringIO()), contextlib.chdir(ROOT):
        for cell in public["cells"]:
            if cell["cell_type"] != "code":
                continue
            check(not cell.get("outputs") and cell.get("execution_count") is None,
                  "Student copy must start clean: "+cell["id"])
            executed.append(cell["id"])
            code = "".join(cell["source"])
            active = cell["id"]
            filename = "student:" + active
            linecache.cache[filename] = (len(code), None, code.splitlines(True), filename)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                exec(compile(code, filename, "exec"), env)
            if active in {"trace-example", "trace-independent"}:
                traces[active] = output.getvalue()
        blocks = re.findall(r"^```python\s*\n(.*?)^```\s*$", teacher, re.M|re.S)
        check(bool(blocks), "Public teacher solution code was not located")
        for i, block in enumerate(blocks, 1):
            active = f"teacher:block:{i}"
            exec(compile(block, active, "exec"), env)
    answer = env["count_at_least"]
    strict = env["count_over"]
    for values, cutoff, strictly, inclusive in [
        ([], 0, 0, 0), ([None], 0, 0, 0), ([0], 0, 0, 1),
        ([1,None,3,3,4], 3, 1, 3), ([0,4,7], 9, 0, 0)
    ]:
        check(strict(values, cutoff) == strictly, "student strict threshold")
        check(answer(values, cutoff) == inclusive, "teacher inclusive threshold")
    for fn in [strict, answer]:
        try:
            fn([3], -1)
        except ValueError:
            pass
        else:
            raise AssertionError("Negative threshold was accepted")

    for name, expected in {
        "trace-example": ("in scan_batch", "return count_over(values, 4)", "in count_over", "books > limit", "TypeError"),
        "trace-independent": ("in last_box", "return code_at(codes, len(codes))", "in code_at", "return codes[position]", "IndexError")
    }.items():
        check(all(token in traces[name] for token in expected), "missing traceback frame or operation")
    check([env["fixed_last_box"](x) for x in (["M", "N", "R"], ["Q"], [])] == ["R", "Q", None],
          "teacher repair on a different length, one item and the empty list")

    base = read_csv("foundations_returns.csv")
    lookup = read_csv("foundations_boxes.csv")
    rows = read_csv("foundations_returns_transfer.csv")
    zones = {row["box_id"]:row["zone"] for row in lookup}
    initial = [[int(row[k]) for k in ("open_books","break_books","lunch_books")]
               for row in base if row["record_id"] in {"R1","R2"}]
    averages = lambda vectors: [sum(v)/len(v) for v in vectors]
    check(np.allclose(env["by_period"], averages(zip(*initial))), "axis=0")
    check(np.allclose(env["by_record"], averages(initial)), "axis=1")
    v = [[0,9],[6,3],[0,3]]
    changed_axes = [averages(zip(*v)), averages(v)]
    check(changed_axes == [[2,5],[4.5,4.5,1.5]], "U/V/W")
    public_math = [sum((x-3)**2 for x in vec)/3 for vec in ([0,3,6],[2,3,4])]
    dot = [sum(x*y for x,y in zip([3,0,4], times)) for times in ([2,5,1],[1,5,2])]
    check(public_math == [6,2/3] and dot == [10,11], "variance or weight order")
    array = np.array([[1,4],[3,0],[2,5]])
    check(array.reshape(2,3)[0,1] == 4 and array.T[0,1] == 3,"reshape vs transpose")
    check(np.array_equal(array+np.array([1,2,3]).reshape(3,1),[[2,5],[5,2],[5,8]]),"per row")
    try:
        array + np.array([1,2,3])
    except ValueError:
        pass
    else:
        raise AssertionError("incompatible trailing dimension passed")
    view = array[:,0]
    copied = view.copy()
    view[0] = 99
    check(array[0,0] == 99 and copied[0] == 1, "basic slice and independent copy")

    linked = env["linked"]
    summary_fn = env["summarize_returns"]
    edges = [0,3,6,9,12,15]
    transfers = {}
    for cutoff in (4,6):
        selected, metrics = summary_fn(linked, cutoff)
        ids, stats, members = reference(rows, zones, cutoff, edges)
        check(selected["slip"].tolist() == ids, "selected IDs")
        check(set(metrics.index) == set(stats), "zone membership")
        for zone, expected in stats.items():
            actual = metrics.loc[zone, ["rows","observed","sum_books","mean_books"]].tolist()
            check(all(equal_numeric(a,e) for a,e in zip(actual,expected)), "zone statistics")
        transfers[str(cutoff)] = dict(selected=ids, stats=stats, histogram_members=members)
    attach = env["attach_zones"]
    frame = env["new"]
    lookup_frame = pd.DataFrame(lookup)
    normal = attach(frame, lookup_frame)
    pd.testing.assert_frame_equal(normal, attach(frame, lookup_frame.iloc[::-1]))
    malformed = frame.copy()
    malformed.loc[malformed.index[0],"station"] = "MISSING-BOX"
    variants = [(frame.drop(columns="meal_count"),lookup_frame,KeyError,"meal_count"),
                (frame,pd.concat([lookup_frame,lookup_frame.iloc[[0]]]),pd.errors.MergeError,None),
                (malformed,lookup_frame,ValueError,"T1")]
    for body, locations, exc, message in variants:
        try:
            attach(body, locations)
        except exc as error:
            check(message is None or message in str(error), "error does not identify value")
        else:
            raise AssertionError("corrupt table accepted")
    bad_keys = frame.copy()
    bad_keys.loc[bad_keys["slip"] == "T1", "station"] = "MISSING-BOX"
    bad_keys.loc[bad_keys["slip"] == "T2", "station"] = pd.NA
    right_null = pd.concat([lookup_frame, pd.DataFrame({"box_id":[pd.NA], "zone":["invented"]})])
    try:
        attach(bad_keys, right_null)
    except ValueError as error:
        check(error.args[1] == ["T1", "T2"], "unmatched and null station IDs must both survive")
    else:
        raise AssertionError("null keys gave a spurious zone")
    empty = frame.copy()
    for region in ("B","C"):
        empty.loc[empty["station"]==region, "closing_count"] = np.nan
    _, abstained = summary_fn(attach(empty,lookup_frame), 4)
    check(abstained.loc["West","observed"] == 0 and
          pd.isna(abstained.loc["West","mean_books"]), "all-unobserved group")
    teacher_figures = [fig for src,fig in zip(artist_sources,figures) if src.startswith("teacher:")]
    final_figure = next(fig for fig in teacher_figures if len(fig) == 4)
    for i,cutoff in enumerate(("4","6")):
        hist, bar = final_figure[2*i:2*i+2]
        ref = transfers[cutoff]
        check(all(x.is_integer() for x in hist["ticks"]), "fractional tick for a number of records")
        check(hist["heights"] == [len(m) for m in ref["histogram_members"]], "actual hist artists")
        check(np.allclose(bar["heights"], [ref["stats"][z][-1] for z in ("East","West")]),
              "actual bar artists")
        check(all(c["xlabel"] and c["ylabel"] for c in (hist,bar)), "missing axes")
    check(final_figure[0]["limits"]==final_figure[2]["limits"] and
          final_figure[1]["limits"]==final_figure[3]["limits"], "incomparable scale")
    for top, bottom in zip(final_figure[:2], final_figure[2:]):
        check(top["pane_bounds"][1] > bottom["pane_bounds"][3], "axis label collision between rows")
    for chart in final_figure:
        check(all(0 <= v <= 1 for v in chart["pane_bounds"]), "cropped figure labels")
    return {"status":"passed", "student_sha256":sha(STUDENT), "teacher_sha256":sha(TEACHER),
            "data_sha256":{p.name:sha(p) for p in (LESSON/"data").glob("foundations_*.csv")},
            "python":sys.version.split()[0], "libraries":{k:v.__version__ for k,v in
                (("numpy",np),("pandas",pd),("matplotlib",matplotlib),("seaborn",sns))},
            "executed_student_code_ids":executed, "executed_teacher_blocks":len(blocks),
            "reference_input":"Only repository-public examples and reviewer-created boundary modifications of the public copies.",
            "tracebacks":traces, "axis_results":changed_axes, "variances":public_math,"dot_order_results":dot,
            "transfer":transfers, "figure_sources":artist_sources, "teacher_transfer_artists":final_figure,
            "negative_cases":["negative Python limits","incompatible array trailing dimension","missing required column",
                              "duplicate lookup key","unmatched station ID","both-side null ID plus a simultaneous unknown station","all missing outcomes in one observed group"],
            "scope":"In-process Python with displayed artist heights inspected in memory. Jupyter transport has a separate receipt. No learner response."}

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
