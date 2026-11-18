"""Reproduce the frozen Week 1 tasks and the third round's accepted repairs.

python reviews/week01-depth-20261118/independent/verify_round3.py reviews/week01-depth-20261118/rounds/0003
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
from verify_round2 import expect_error, measure_teacher_figure


def test_ids(teacher, cells):
    namespace = {"pd": pd, "np": np}
    nodes = []
    for block in re.findall(r"```python\n(.*?)\n```", teacher, re.S):
        nodes.extend(n for n in ast.parse(block).body if isinstance(n, ast.FunctionDef))
    nodes.extend(n for n in ast.parse(cells["trace-independent"]).body
                 if isinstance(n, ast.FunctionDef) and n.name == "code_at")
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "archived-functions", "exec"), namespace)
    join, read = namespace["attach_zones"], namespace["read_returns"]
    assert [namespace["fixed_last_box"](x) for x in [[], ["K"], ["M","R","T"]]] == [None,"K","T"]
    header = "slip,station,morning_count,pause_count,meal_count,closing_count\n"
    left_text = header + "obs-11,R,3,2,6,1\nobs-17,B,1,1,4,0\nobs-20,R,4,0,1,6\n"
    right = pd.DataFrame({"zone":["Blue","Red"],"box_id":["B","R"]})
    left = read(io.StringIO(left_text))
    normal = join(left, right)
    pd.testing.assert_frame_equal(normal, join(left, right.iloc[::-1]))
    assert normal.slip.tolist() == ["obs-11","obs-17","obs-20"]
    assert normal.zone.tolist() == ["Red","Blue","Red"]
    representations = {}
    for label, null in (("None",None),("numpy.nan",np.nan),("pandas.NA",pd.NA),
                        ("empty string",""),("whitespace","   ")):
        l = left.copy()
        l.loc[l.slip=="obs-11","station"] = null
        l.loc[l.slip=="obs-20","station"] = "Unknown"
        r = pd.concat([right, pd.DataFrame({"box_id":[null,null],"zone":["invented1","invented2"]})], ignore_index=True)
        before_l, before_r = l.copy(), r.copy()
        error = expect_error(ValueError, join, l, r)
        assert error == ("구역을 찾지 못한 기록",["obs-11","obs-20"])
        pd.testing.assert_frame_equal(l,before_l)
        pd.testing.assert_frame_equal(r,before_r)
        pd.testing.assert_frame_equal(join(left,r),normal)
        representations[label] = error[1]
    csv_all_missing = header + "001,,2,4,3,5\n002,,4,0,2,0\n"
    right_blank = pd.DataFrame({"box_id":["","R"],"zone":["invented","Red"]})
    typed = read(io.StringIO(csv_all_missing))
    inferred = pd.read_csv(io.StringIO(csv_all_missing),dtype={"slip":"string"})
    reported = {}
    for label,example in (("declared reader",typed),("inferred float key",inferred)):
        error = expect_error(ValueError,join,example,right_blank)
        assert error == ("구역을 찾지 못한 기록",["001","002"])
        assert example["closing_count"].tolist() == [5,0]
        reported[label] = error[1]
    candidates = read(io.StringIO(header + "001,007,0,1,0,2\n002,7,1,2,0,0\nNA,NA,1,3,1,2\n"))
    three_zones = pd.DataFrame({"box_id":["7","NA","007"],"zone":["single","named","padded"]})
    matched = join(candidates,three_zones)
    assert matched.slip.tolist() == ["001","002","NA"]
    assert matched.zone.tolist() == ["padded","single","named"]
    bad_slip = left.copy()
    bad_slip.loc[bad_slip.slip=="obs-17","slip"] = " "
    assert expect_error(ValueError,join,bad_slip,right) == ("기록 이름이 빈 입력 순번",[2])
    duplicate_slip = left.copy()
    duplicate_slip.loc[duplicate_slip.slip=="obs-17","slip"] = " obs-11 "
    assert expect_error(ValueError,join,duplicate_slip,right) == ("중복된 기록 이름",["obs-11"])
    assert expect_error(KeyError,join,left.drop(columns=["meal_count"]),right)==("meal_count",)
    expect_error(pd.errors.MergeError,join,left,pd.concat([right,right.loc[right.box_id=="R"]]))
    no_zone = right.copy()
    no_zone.loc[no_zone.box_id=="R","zone"] = pd.NA
    assert expect_error(ValueError,join,left,no_zone)==("구역 이름이 빈 기록",["obs-11","obs-20"])
    pd.testing.assert_frame_equal(join(left,right),normal)
    return {"mixed_blank_and_unknown":representations,"all_blank_csv":reported,
            "preserved_ids":matched.slip.tolist(),"corresponding_zones":matched.zone.tolist(),
            "blank_slip_position":2,"duplicate_after_normalization":["obs-11"],
            "duplicate_known_key":"MergeError","missing_required_column":"meal_count",
            "known_key_missing_zone":["obs-11","obs-20"],"public_fix_last_box":[None,"K","T"]}


def replay(round_dir):
    round_dir=round_dir.resolve()
    info=json.loads((round_dir/"round.json").read_text())
    repository=next(q for q in round_dir.parents if all((q/i["snapshot"]).is_file() for i in info["companions"]))
    with TemporaryDirectory() as temp:
        stage=Path(temp)
        for name in ("candidate.ipynb","round.json"):
            shutil.copyfile(round_dir/name,stage/name)
        inputs=stage/"inputs"
        inputs.mkdir()
        for item in info["companions"]:
            src=repository/item["snapshot"]
            assert digest(src)==item["sha256"]
            shutil.copyfile(src,inputs/src.name)
        sealed=check_round(stage)
        teacher=(inputs/"week01_foundations_teacher.md").read_text()
        cells={c["id"]:"".join(c["source"]) for c in json.loads((stage/"candidate.ipynb").read_bytes())["cells"]}
        ids=test_ids(teacher,cells)
        bounds=measure_teacher_figure(teacher,inputs)
        assert bounds["right_axis_labels_overlap_px"]==0
        assert bounds["right_upper_label_extends_beyond_canvas_top_px"]==0
    return {"frozen_inputs_replay":sealed,"id_and_error_checks":ids,"teacher_plot_layout":bounds}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round_directory",type=Path)
    print(json.dumps(replay(parser.parse_args().round_directory),ensure_ascii=False,indent=2))
