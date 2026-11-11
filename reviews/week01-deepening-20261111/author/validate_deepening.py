#!/usr/bin/env python3
"""Execute the candidate anew and check its stated examples and teacher key."""
import argparse
import ast
import hashlib
import itertools
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"
os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
import nbformat
import numpy as np
import pandas as pd
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / "lessons/week01"
NB = LESSON / "week01_integrated.ipynb"
HTML = LESSON / "week01_integrated.html"
TEACHER = LESSON / "week01_integrated_teacher.md"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def payloads(cell):
    outputs=[]
    for out in cell.outputs:
        if out.output_type == "stream":
            outputs.append(("stream",out.name,out.text))
        elif out.output_type in ("display_data","execute_result"):
            outputs.append((out.output_type,dict(out.data)))
        else:
            outputs.append((out.output_type,dict(out)))
    return outputs

def manual_leaves(image):
    return sum(int(image[r,c,0] == 1 and image[r,c,1] == 1)
               for r in range(2) for c in range(2))

def manual_device(panel):
    return sum(int(panel[r,c,0] == 1 and panel[r,c,1] == 2)
               for r in range(2) for c in range(2))

def reference_xy(frame, imputer=None):
    """One possible teacher solution, not a student answer or a universal model."""
    for name in ("unit","signal","panel"):
        if name not in frame.columns:
            raise ValueError("missing " + name)
    if frame["unit"].isna().any() or frame["unit"].duplicated().any():
        raise ValueError("missing or repeated unit")
    if imputer is None:
        imputer=SimpleImputer(strategy="mean").fit(frame[["signal"]])
    values=imputer.transform(frame[["signal"]]).ravel()
    counts=[manual_device(p) for p in frame["panel"]]
    return np.column_stack((values, counts)), imputer

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write")
    parser.add_argument("--protected-worktree", type=Path, help="Optional separate worktree root to compare before/after")
    args=parser.parse_args()
    paths=[NB,HTML,TEACHER,
           LESSON/"week01_python_tables.ipynb",
           LESSON/"week01_axes_linear_bridge.ipynb",
           LESSON/"week01_problem_pipeline.ipynb"]
    protected_paths=[]
    if args.protected_worktree is not None:
        protected=args.protected_worktree.resolve()/"lessons/week01"
        protected_paths=[protected/"week01_python_tables.ipynb",
                         protected/"week01_python_tables.html",
                         protected/"lesson-manifest.json",
                         protected/"teacher-notes.txt",
                         protected/"validation.json",
                         protected/"data/week1_plants.csv",
                         protected/"data/week1_plants_new.csv"]
        absent=[str(p) for p in protected_paths if not p.is_file()]
        if absent:
            parser.error("specified protected worktree lacks: "+", ".join(absent))
        paths.extend(protected_paths)
    before={str(p):sha(p) for p in paths}
    saved=nbformat.read(NB,as_version=4)
    book=nbformat.read(NB,as_version=4)
    nbformat.validate(book)
    fresh_html,_=HTMLExporter().from_notebook_node(book)
    assert fresh_html==HTML.read_text(encoding="utf-8"),"HTML export differs"
    assert len(book.cells)==38 and sum(c.cell_type=="code" for c in book.cells)==18
    checks=["notebook_schema_and_exact_html_export"]
    with tempfile.TemporaryDirectory(prefix="week01-deep-qa-") as temp:
        os.environ["IPYTHONDIR"]=temp
        os.environ["MPLCONFIGDIR"]=temp
        manager=InProcessKernelManager(); manager.start_kernel()
        shell=manager.kernel.shell
        client=manager.client(); client.start_channels()
        try:
            indices=[]
            for index,cell in enumerate(book.cells):
                if cell.cell_type!="code":
                    continue
                client.execute(cell.source,store_history=True)
                reply=client.get_shell_msg(timeout=120)
                if reply["content"]["status"]!="ok":
                    raise AssertionError(f"cell {index}: {reply['content']}")
                cell.execution_count=reply["content"]["execution_count"]
                cell.outputs=[]
                while True:
                    msg=client.get_iopub_msg(timeout=120)
                    if msg["msg_type"]=="status" and msg["content"].get("execution_state")=="idle":
                        break
                    if msg["msg_type"] in ("stream","display_data","execute_result","error"):
                        cell.outputs.append(nbformat.v4.output_from_msg(msg))
                assert not any(o.output_type=="error" for o in cell.outputs)
                assert payloads(cell)==payloads(saved.cells[index]),f"saved output differs at {index}"
                indices.append(index)
            checks.append("fresh_inprocess_all_18_code_cells_saved_text_html_and_png_match")
            ns=shell.user_ns

            answers=[c for c in saved.cells if c.cell_type=="code" and c.source.startswith("# 새 명세의 특성과 모델")]
            assert len(answers)==1 and not ast.parse(answers[0].source).body and answers[0].outputs==[]
            assert "N7,점검" not in HTML.read_text(encoding="utf-8")
            assert "N7,점검" not in NB.read_text(encoding="utf-8")
            checks.append("student_independent_code_blank_and_teacher_csv_absent")

            mean=ns["observed_mean"]; frame=ns["plants"]
            assert mean(frame["water_ml"].tolist())==24
            assert mean([0,None,np.nan,6])==3 and mean([0])==0
            assert mean([]) is None and mean([None,np.nan]) is None
            assert mean([1_000_000]*10_000)==1_000_000
            assert mean([-1_000_000,1_000_000,None])==0
            assert frame.loc[frame["water_ml"].isna(),"pot_id"].tolist()==["P03"]
            assert frame.loc[frame["water_ml"]==0,"pot_id"].tolist()==["P01"]
            checks.append("bounded_real_csv_mean_none_nan_zero_empty")

            days=ns["light_by_day"]
            assert days.shape==(3,2)
            assert np.allclose(days.mean(axis=0),[11/3,11/3])
            assert np.array_equal(days.mean(axis=1),[2,3,6])
            assert ns["reshaped"].shape==ns["transposed"].shape==(2,3)
            assert ns["reshaped"][0,1]!=ns["transposed"][0,1]
            assert np.array_equal(days+np.array([1,2]),[[3,4],[4,5],[7,8]])
            try:
                days+np.array([1,2,3])
            except ValueError:
                pass
            else:
                raise AssertionError("broadcast mismatch not rejected")
            assert np.isclose(np.var([8,10,12]),8/3)
            assert np.var([0,4])==4 and np.var([1,3])==1
            checks.append("axis_reshape_broadcast_and_variance")

            counter=ns["count_yellow_leaf"]
            for object_bits in range(16):
                for color_bits in range(16):
                    objects=np.array([(object_bits>>i)&1 for i in range(4)]).reshape(2,2)
                    colors=np.array([(color_bits>>i)&1 for i in range(4)]).reshape(2,2)
                    image=np.stack((objects,colors),axis=2)
                    assert counter(image)==manual_leaves(image)
                    changed=image.copy()
                    changed[:,:,1][objects==0]=1-changed[:,:,1][objects==0]
                    assert counter(changed)==counter(image)
            image=ns["leaf_images"]["P02"]
            assert image[0,1].tolist()==[1,1] and image[1,0].tolist()==[1,0]
            assert image.transpose(1,0,2).shape==image.shape
            assert image.transpose(1,0,2)[0,1].tolist()==[1,0]
            assert counter(image)==1 and int((image[:,:,1]==1).sum())==3
            assert [counter(ns["leaf_images"][i]) for i in frame["pot_id"]]==[0,1,2,3,2,3]
            checks.append("256_valid_observations_background_invariance_and_same_shape_transpose")

            by_id=ns["leaf_images"]; train=ns["training"]; target=ns["y_train"]
            expected_counts=dict(zip(["P01","P02","P03","P04","P05","P06"],[0,1,2,3,2,3]))
            reordered=frame.iloc[[3,1,5,0,4,2]]
            assert [counter(by_id[x]) for x in reordered["pot_id"]]==[expected_counts[x] for x in reordered["pot_id"]]
            wrong=list(by_id.values())[::-1]
            assert [counter(x) for x in wrong] != [expected_counts[x] for x in frame["pot_id"]]
            assert all(x.shape==(2,2,2) for x in wrong)
            assert ns["fixed_height"]==9 and ns["p02"]["height_cm"]-ns["fixed_height"]==1
            assert np.array_equal(ns["x_train"],[[0,0],[2,1],[2,2],[4,3]])
            assert np.allclose(ns["fill"].statistics_,[20])
            assert target.tolist()==[0,0,1,1]
            assert np.allclose(ns["model"].centroids_,[[1,.5],[3,2.5]])
            assert np.array_equal(ns["x_validation"],[[1,2],[5,3]])
            assert np.allclose(((ns["model"].centroids_-ns["x_validation"][0])**2).sum(axis=1),[2.25,4.25])
            assert ns["predictions"].tolist()==[0,1]
            assert ns["y_validation"].tolist()==[1,1] and ns["validation_accuracy"]==.5
            assert np.allclose(ns["changed_fill"].statistics_,[80/3])
            assert np.allclose(ns["changed_model"].centroids_,[[1,.5],[13/3,2.5]])
            assert (ns["original_prediction"],ns["changed_prediction"])==(1,0)
            for order in itertools.permutations(range(4)):
                t=train.iloc[list(order)]; y=target.iloc[list(order)]
                fill=SimpleImputer().fit(t[["water_ml"]])
                x=np.column_stack((fill.transform(t[["water_ml"]]).ravel()/10,
                                   [manual_leaves(by_id[i]) for i in t["pot_id"]]))
                model=NearestCentroid().fit(x,y)
                assert np.allclose(model.centroids_,[[1,.5],[3,2.5]])
            mismatched=NearestCentroid().fit(ns["x_train"],[1,0,0,1])
            assert not np.allclose(mismatched.centroids_,ns["model"].centroids_)
            oldstats=ns["fill"].statistics_.copy()
            oldcenters=ns["model"].centroids_.copy()
            altered=ns["validation"][["water_ml"]].copy(); altered.iloc[0,0]=9999
            ns["fill"].transform(altered)
            assert np.array_equal(oldstats,ns["fill"].statistics_)
            assert np.array_equal(oldcenters,ns["model"].centroids_)
            checks.append("id_pairing_real_fit_24_joint_permutations_mismatch_and_train_only")

            ax=ns["ax"]
            got=sorted(tuple(map(float,row)) for col in ax.collections for row in col.get_offsets())
            expected=sorted((float(a),float(b)) for a,b in zip(frame["light_h"],frame["height_cm"]))
            assert got==expected and {t.get_text() for t in ax.texts}==set(frame["pot_id"])
            assert ax.get_xlabel()=="하루 빛 시간 (h)" and ax.get_ylabel()=="일주일 뒤 높이 (cm)"
            assert ns["checked"]["pot_id"].tolist()==["P05","P06"]
            assert ns["file_check"]["prediction"].tolist()==[0,1]
            assert not ns["result_path"].exists()
            checks.append("scatter_identity_units_and_memory_and_physical_csv_roundtrip")

            p=ns["panel_examples"]["B"]
            assert p[0,1].tolist()==[1,2] and p[1,0].tolist()==[0,2]
            assert manual_device(p)==1 and counter(p)==0
            assert p.transpose(1,0,2).shape==p.shape
            assert p.transpose(1,0,2)[0,1].tolist()==[0,2]
            t=ns["exercise_train"]; v=ns["exercise_validation"]; q=ns["exercise_input"]
            known=t[t["label"]!="?"].copy()
            assert known["unit"].tolist()==["T1","T2","T3","T4"]
            X,imputer=reference_xy(known)
            assert np.allclose(imputer.statistics_,[2])
            assert np.array_equal(X,[[0,0],[2,1],[2,2],[4,3]])
            Xv,_=reference_xy(v,imputer); Xq,_=reference_xy(q,imputer)
            nearest=NearestCentroid().fit(X,known["label"])
            tree=DecisionTreeClassifier(max_depth=2,random_state=0).fit(X,known["label"])
            assert nearest.predict(Xv).tolist()==["정상","점검","정상"]
            assert tree.predict(Xv).tolist()==["정상","점검","점검"]
            assert nearest.predict(Xq).tolist()==["점검","정상","점검"]
            assert (nearest.predict(Xv)==v["label"]).mean()==2/3
            assert (tree.predict(Xv)==v["label"]).mean()==1
            pairs=dict(zip(q["unit"],nearest.predict(Xq)))
            order=ns["exercise_order"]
            result=pd.DataFrame({"sample_id":order,"prediction":[pairs[i] for i in order]})
            assert result["prediction"].tolist()==["점검","점검","정상"]
            csv_path=Path(temp)/"exercise-result.csv"
            result.to_csv(csv_path,index=False)
            reread=pd.read_csv(csv_path)
            assert reread.equals(result)
            assert list(reread.columns)==["sample_id","prediction"]
            assert reread["sample_id"].tolist()==order
            assert set(reread["prediction"]).issubset({"정상","점검"})
            reversed_result=result.copy()
            reversed_result["prediction"]=reversed_result["prediction"].iloc[::-1].to_numpy()
            assert not reversed_result.equals(result)
            for bad in (q.drop(columns="signal"),pd.concat([q,q.iloc[[0]]],ignore_index=True)):
                try:
                    reference_xy(bad,imputer)
                except ValueError:
                    pass
                else:
                    raise AssertionError("reference checker accepted missing column or duplicate ID")
            checks.append("teacher_key_independent_schema_two_models_file_and_error_cases")
        finally:
            client.stop_channels()
            manager.shutdown_kernel()
            shell._atexit_once()
    assert before=={str(p):sha(p) for p in paths},"a protected or input file changed"
    receipt={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
             "method":"fresh in-process kernel; independent scalar loops and two independently fit models",
             "cell_count":len(book.cells),"code_cell_count":len(indices),
             "executed_code_cells_zero_based":indices,"checks":checks,
             "source_sha256_before_and_after":before,
             "protected_worktree":{"status":"checked" if protected_paths else "not_checked",
                                   "reason":"explicit path" if protected_paths else "no path supplied",
                                   "files_compared":len(protected_paths)},
             "validator_sha256":sha(Path(__file__)),
             "limitations":["blank student answer was not solved by a learner",
                            "reference error checks exercise a teacher solution, not student code",
                            "student achievement and workload are unobserved",
                            "ordinary socket Jupyter/Colab and browser visual rendering were not tested",
                            "synthetic exercises do not solve the international competition tasks"]}
    if args.write:
        Path(args.write).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
