"""Replay the sealed inputs, then the second manuscript's declared error cases.

From the repository root:
python reviews/week01-depth-20261118/independent/verify_round2.py reviews/week01-depth-20261118/rounds/0002
"""
import argparse
import ast
import io
import json
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from verify_round import check_round, digest


def expect_error(kind, function, *args):
    try:
        function(*args)
    except kind as error:
        return error.args
    raise AssertionError(f"Expected {kind.__name__}")


def fresh_key_cases(teacher_text, cells):
    collector = {}
    for block in re.findall(r"```python\n(.*?)\n```", teacher_text, re.S):
        for node in ast.parse(block).body:
            if isinstance(node, ast.FunctionDef):
                collector[node.name] = node
    student = ast.parse(cells["trace-independent"])
    code_at = next(s for s in student.body if isinstance(s, ast.FunctionDef) and s.name == "code_at")
    functions = [collector["attach_zones"], collector["fixed_last_box"], code_at]
    env = {"pd": pd}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "edited-teaching-functions", "exec"), env)
    assert [env["fixed_last_box"](vals) for vals in [[], ["K"], ["M","R","T"]]] == [None,"K","T"]
    join = env["attach_zones"]
    left_text = ("slip,station,morning_count,pause_count,meal_count,closing_count\n"
                 "obs-11,R,3,2,6,1\nobs-17,B,1,1,4,0\nobs-20,R,4,0,1,6\n")
    right_text = "zone,box_id\nBlue,B\nRed,R\n"
    left = pd.read_csv(io.StringIO(left_text))
    right = pd.read_csv(io.StringIO(right_text))
    normal = join(left, right)
    assert list(zip(normal.slip, normal.zone)) == [("obs-11", "Red"), ("obs-17", "Blue"), ("obs-20", "Red")]
    na_cases = {}
    for label, null in (("None", None), ("numpy.nan", np.nan), ("pandas.NA", pd.NA)):
        l = left.copy()
        l.loc[l.slip == "obs-11", "station"] = null
        l.loc[l.slip == "obs-20", "station"] = "Unknown"
        missing_keys = pd.DataFrame({"box_id": [null, null], "zone": ["False1", "False2"]})
        r = pd.concat([missing_keys, right.iloc[::-1]], ignore_index=True)
        args = expect_error(ValueError, join, l, r)
        assert args == ("구역을 찾지 못한 기록", ["obs-11", "obs-20"])
        na_cases[label] = args[1]
        pd.testing.assert_frame_equal(join(left, r), normal)
    literal_blank_csv = ("slip,station,morning_count,pause_count,meal_count,closing_count\n"
                         "v1,,2,4,3,5\nv2,R,4,0,2,2\n")
    r = pd.read_csv(io.StringIO("zone,box_id\nfalse,\nRed,R\n"))
    args = expect_error(ValueError, join, pd.read_csv(io.StringIO(literal_blank_csv)), r)
    assert args == ("구역을 찾지 못한 기록", ["v1"])
    assert expect_error(KeyError, join, left.drop(columns=["meal_count"]), right) == ("meal_count",)
    repeated = pd.concat([right, right.loc[right.box_id == "R"]])
    expect_error(pd.errors.MergeError, join, left, repeated)
    no_name = right.copy()
    no_name.loc[no_name.box_id == "R", "zone"] = pd.NA
    assert expect_error(ValueError, join, left, no_name) == ("구역 이름이 빈 기록", ["obs-11","obs-20"])
    known_only = left.copy()
    known_only.loc[known_only.slip == "obs-20", "closing_count"] = pd.NA
    valid = join(known_only, right)
    assert len(valid) == 3 and valid.closing_count.isna().sum() == 1
    pd.testing.assert_frame_equal(join(left, right.iloc[::-1]), normal)
    # Supplementary observations on representations outside the published mutation.
    # These are recorded without prescribing behaviour or changing the pass standard.
    literal_text = left.copy()
    literal_text.loc[literal_text.slip == "obs-11", "station"] = ""
    literal_lookup = pd.concat([right, pd.DataFrame({"box_id":[""],"zone":["False"]})])
    try:
        blank = join(literal_text, literal_lookup)
        literal_outcome = {"accepted": True, "assigned": blank.loc[blank.slip == "obs-11", "zone"].tolist()}
    except ValueError as error:
        literal_outcome = {"accepted": False, "diagnostic": str(error)}
    empty_left = pd.read_csv(io.StringIO(literal_blank_csv.replace("v2,R", "v2,")))
    try:
        all_blank = join(empty_left, right)
        all_blank_outcome = {"accepted": True, "rows": len(all_blank)}
    except ValueError as error:
        all_blank_outcome = {"accepted": False, "diagnostic": str(error)}
    return {"declared_cases": {"mixed_unknown_and_null": na_cases, "blank_field_read_from_csv": ["v1"],
                               "existing_key_missing_zone": ["obs-11","obs-20"],
                               "missing_required_field": "meal_count", "duplicate_known_key": "MergeError",
                               "normal_after_errors": normal.slip.tolist(), "last_box_fixed": [None,"K","T"]},
            "additional_observations_outside_fixed_cases": {"programmatic_empty_string": literal_outcome,
                                                            "all_missing_csv_key_column": all_blank_outcome}}


def measure_teacher_figure(teacher_text, inputs):
    # The measured boxes describe the rendered teacher reference, separate
    # from the numeric acceptance checks and the student's template figures.
    from contextlib import redirect_stdout
    import matplotlib.pyplot as plt
    import seaborn as sns
    env = {"data_dir": inputs, "pd": pd, "np": np, "plt": plt, "sns": sns}
    blocks = re.findall(r"```python\n(.*?)\n```", teacher_text, re.S)
    with redirect_stdout(io.StringIO()):
        for block in blocks:
            if "def attach_zones" in block or "edges = [0, 3" in block:
                exec(compile(block, "public-teacher-plot", "exec"), env)
    fig, axes = env["fig"], env["axes"]
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        top = axes[0, 1].yaxis.label.get_window_extent(renderer)
        bottom = axes[1, 1].yaxis.label.get_window_extent(renderer)
        return {"canvas_pixels": list(fig.canvas.get_width_height()),
                "right_axis_labels_overlap_px": float(max(0, bottom.y1 - top.y0)),
                "right_upper_label_extends_beyond_canvas_top_px": float(max(0, top.y1 - fig.bbox.y1))}
    finally:
        plt.close(fig)


def replay(round_dir):
    round_dir = round_dir.resolve()
    info = json.loads((round_dir / "round.json").read_text())
    # The archive reuses unchanged companions from the earlier round. Preserve
    # the original R1 replay unchanged, materializing the exact referenced bytes.
    repository = next(parent for parent in round_dir.parents
                      if all((parent / item["snapshot"]).is_file() for item in info["companions"]))
    with TemporaryDirectory() as t:
        staged = Path(t)
        (staged / "inputs").mkdir()
        for name in ("round.json", "candidate.ipynb"):
            shutil.copyfile(round_dir / name, staged / name)
        for item in info["companions"]:
            path = repository / item["snapshot"]
            assert digest(path) == item["sha256"]
            shutil.copyfile(path, staged / "inputs" / path.name)
        fixed = check_round(staged)
        teacher_text = (staged / "inputs" / "week01_foundations_teacher.md").read_text()
        cells = {c["id"]: "".join(c["source"]) for c in json.loads((staged / "candidate.ipynb").read_bytes())["cells"]}
        more = fresh_key_cases(teacher_text, cells)
        visual = measure_teacher_figure(teacher_text, staged / "inputs")
    return {"frozen_inputs_replay": fixed, **more, "teacher_plot_layout": visual}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_directory", type=Path)
    print(json.dumps(replay(parser.parse_args().round_directory), ensure_ascii=False, indent=2))
