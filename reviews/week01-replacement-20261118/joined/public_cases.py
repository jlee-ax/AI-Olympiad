"""Public examples and independent boundary calculations for the replacement Week 1 route."""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import linecache
import os
import re
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LESSON = ROOT/"lessons/week01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grouped(rows, lookup, cutoff):
    selected, measured, stats = [], [], {}
    for record in rows:
        lunch, closing = record["meal_count"], record["closing_count"]
        if not lunch or int(lunch)<cutoff: continue
        selected.append(record["slip"])
        group = stats.setdefault(lookup[record["station"]], [])
        if closing:
            measured.append((record["slip"],int(closing)))
            group.append(int(closing))
        else:
            group.append(None)
    summary={}
    for zone, values in stats.items():
        observed=[v for v in values if v is not None]
        summary[zone]=[len(values),len(observed),sum(observed),sum(observed)/len(observed)]
    return selected,measured,summary


def check_entry(student, teacher, supplement):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import seaborn as sns

    plots=[]
    def show(*args,**kwargs):
        fig=plt.gcf()
        fig.canvas.draw()
        renderer=fig.canvas.get_renderer()
        panels=[]
        for ax in fig.axes:
            bounds=ax.get_tightbbox(renderer).transformed(fig.transFigure.inverted()).extents.tolist()
            panels.append({"heights":[float(v.get_height()) for v in ax.patches],
                "xlabel":ax.get_xlabel(),"ylabel":ax.get_ylabel(),"ticks":list(map(float,ax.get_yticks())),
                "bounds":[round(v,5) for v in bounds]})
        plots.append(panels)
        plt.close(fig)
    plt.show=show

    def execute(nbpath):
        env={"__name__":"__main__"}
        logs={}
        nb=json.loads(nbpath.read_text())
        for cell in nb["cells"]:
            if cell["cell_type"]!="code":
                continue
            assert cell["execution_count"] is None and not cell["outputs"]
            code="".join(cell["source"])
            filename="student:"+cell["id"]
            linecache.cache[filename]=(len(code),None,code.splitlines(keepends=True),filename)
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                exec(compile(code,filename,"exec"),env)
            logs[cell["id"]]=buf.getvalue()
        return env,logs

    with contextlib.chdir(ROOT):
        env,logs=execute(student)
        renv,rlogs=execute(supplement)
        blocks=re.findall(r"^```python\s*\n(.*?)^```\s*$",teacher.read_text(),re.S|re.M)
        for idx, block in enumerate(blocks,1):
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(block,"teacher:"+str(idx),"exec"),env)
    assert "books > limit" in logs["trace-example"] and "TypeError" in logs["trace-example"]
    assert "codes[position]" in logs["trace-independent"] and "IndexError" in logs["trace-independent"]
    check_inputs=[[],[None],[0],[0,3,3,None,6]]
    assert [env["count_over"](xs,3) for xs in check_inputs]==[0,0,0,1]
    assert [env["count_at_least"](xs,3) for xs in check_inputs]==[0,0,0,3]
    assert env["count_at_least"]([0],0)==1
    assert [env["fixed_last_box"](xs) for xs in ([],["R"],["Q","X","M"])]==[None,"R","M"]
    assert env["by_period"].tolist()==[5,2,5] and env["by_record"].tolist()==[4,4]
    machine=env["notice"]
    reference=[[1,4],[3,0],[2,5]]
    board=[list(col) for col in zip(*reference)]
    scores=[a*3+b*(-2) for a,b in reference]
    wrong=[a*(-2)+b*3 for a,b in reference]
    assert env["board"].tolist()==board and env["scores"].tolist()==scores==[-5,9,-4]
    assert machine.reshape(2,3)[0,1]==4 and env["board"][0,1]==3 and wrong==[10,-6,11]
    changed_outputs = {}
    if "outputs_for" in env:
        project = env["outputs_for"]
        for label,(row,col,new_value) in {"public_F_boundary":(2,1,2),"alternate_E_correct":(1,0,1)}.items():
            source = np.array(reference)
            corrected = source.copy()
            corrected[row,col] = new_value
            expected = [x.copy() for x in reference]
            expected[row][col] = new_value
            expected_board = [list(column) for column in zip(*expected)]
            expected_scores = [3*good - 2*faults for good,faults in expected]
            projected, totals = project(corrected, np.array([3,-2]))
            assert projected.tolist() == expected_board and totals.tolist() == expected_scores
            assert projected.shape==(2,3) and totals.shape==(3,) and source.tolist()==reference
            assert np.argwhere(projected!=np.array(board)).tolist()==[[col,row]]
            assert np.argwhere(totals!=np.array(scores)).ravel().tolist()==[row]
            changed_outputs[label]={"input_coordinate":[row,col],"value":new_value,
                "board":expected_board,"scores":expected_scores,"score_change":expected_scores[row]-scores[row]}
        assert env["new_board"].tolist()==changed_outputs["public_F_boundary"]["board"]
        assert env["new_scores"].tolist()==changed_outputs["public_F_boundary"]["scores"]
    within=[[3,3,9],[12],[]]
    groups=[v for v in within if v]
    assert sum(map(sum,groups))/sum(map(len,groups))==6.75
    assert sum(sum(v)/len(v) for v in groups)/len(groups)==8.5
    assert [sum((i-3)**2 for i in xs)/3 for xs in ([0,3,6],[2,3,4])]==[6,2/3]
    csvpath=LESSON/"data/foundations_returns_transfer.csv"
    lookpath=LESSON/"data/foundations_boxes.csv"
    with csvpath.open(newline="") as f: rows=list(csv.DictReader(f))
    with lookpath.open(newline="") as f: lookup={row["box_id"]:row["zone"] for row in csv.DictReader(f)}
    attach,summary=env["attach_zones"],env["summarize_returns"]
    frame=env["new"]
    right=env["lookup"]
    paired=attach(frame,right)
    pd.testing.assert_frame_equal(paired,attach(frame,right.iloc[::-1]))
    metrics={}
    final=next(p for p in plots if len(p)==4)
    for index,cutoff in enumerate((4,6)):
        ids,observed,ref=grouped(rows,lookup,cutoff)
        act,table=summary(paired,cutoff)
        assert act["slip"].tolist()==ids
        for zone,want in ref.items():
            assert np.allclose(table.loc[zone,["rows","observed","sum_books","mean_books"]],want)
        heights=[sum(lo<=v<lo+3 for _,v in observed) for lo in (0,3,6,9,12)]
        hist,bar=final[2*index:2*index+2]
        assert hist["heights"]==heights and np.allclose(bar["heights"],[ref[z][3] for z in ("East","West")])
        assert all(v.is_integer() for v in hist["ticks"]) and hist["ylabel"] and bar["ylabel"]
        metrics[str(cutoff)]={"selected":ids,"zone_rows_observed_sum_mean":ref,"hist":heights}
    assert all(min(p["bounds"])>=0 and max(p["bounds"])<=1 for p in final)
    assert all(first["bounds"][1] > second["bounds"][3] for first,second in zip(final[:2],final[2:]))
    with tempfile.TemporaryDirectory(dir=HERE,prefix="csv-") as temp:
        path=Path(temp)/"all_missing.csv"
        with path.open("w",newline="") as output:
            wr=csv.DictWriter(output,fieldnames=list(rows[0]));wr.writeheader()
            wr.writerows([{**row,"station":""} for row in rows])
        try: attach(pd.read_csv(path),right)
        except ValueError as error: assert error.args[1]==[row["slip"] for row in rows]
        else: raise AssertionError("Unmatched physical CSV observations disappeared")
    try: attach(frame,pd.concat([right,right.iloc[[0]]]))
    except pd.errors.MergeError: pass
    else: raise AssertionError("Duplicate lookup key was accepted")
    text=renv["text_id"]
    assert renv["unlinked"]==["M07","M12"]
    left,right=renv["fresh_visits"],renv["fresh_places"]
    clean=right.assign(code=text(right["code"]))
    assert clean.loc[clean["code"].duplicated(keep=False),"code"].tolist()==["G2","G2"]
    verified=pd.DataFrame({"code":["G1","G2"],"area":["North","South"]})
    actual=left.assign(place=text(left["place"])).merge(verified,left_on="place",right_on="code",
                                                       how="left",validate="many_to_one",indicator=True)
    assert actual["ticket"].tolist()==["J6","J2","J9"] and actual.loc[actual["_merge"]=="left_only","ticket"].tolist()==["J2"]
    assert actual.loc[actual["ticket"]=="J9","area"].iloc[0]=="South"
    return {"entry_sha256":sha(student),"teacher_sha256":sha(teacher),"supplement_sha256":sha(supplement),
            "entry_code_cells":len(logs),"supplement_code_cells":len(rlogs),"teacher_python_blocks":len(blocks),
            "versions":{"numpy":np.__version__,"pandas":pd.__version__,"matplotlib":matplotlib.__version__,"seaborn":sns.__version__},
            "diagnosis":"Real two-frame exceptions, empty, None, zero, equal cutoff, altered input/return confirmed.",
            "changed_outputs":changed_outputs,"board":board,"robot_scores":scores,"wrong_rule":wrong,"passenger_vs_station":[6.75,8.5],
            "variances":[6,2/3],"public_rows":metrics,"rendered_panels":final,"physical_blank_ids":[row["slip"] for row in rows],
            "conditional":{"worked_unlinked":renv["unlinked"],"fresh_duplicate":"G2","affected":"J9","fresh_unlinked":["J2"],"rows":3},
            "scope":"Public inputs and teacher examples only. First student answers and time were not observed.","status":"passed"}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entry",type=Path,default=LESSON/"week01_foundations.ipynb")
    parser.add_argument("--teacher",type=Path,default=LESSON/"week01_foundations_teacher.md")
    parser.add_argument("--supplement",type=Path,default=LESSON/"week01_foundations_repair.ipynb")
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="matplotlib-",dir=HERE) as cache:
        os.environ["MPLCONFIGDIR"]=cache
        tempfile.tempdir=cache
        report=check_entry(args.entry,args.teacher,args.supplement)
    print(json.dumps(report,ensure_ascii=False,indent=2))
