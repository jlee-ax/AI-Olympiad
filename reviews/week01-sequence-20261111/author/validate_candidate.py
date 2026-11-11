#!/usr/bin/env python3
"""Run candidate notebooks in separate processes and validate their actual functions."""
import argparse
import ast
import hashlib
import itertools
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LESSON=ROOT/"lessons/week01"
BRIDGE=LESSON/"week01_axes_linear_bridge.ipynb"
MAIN=LESSON/"week01_integrated.ipynb"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_worker(kind):
    import nbformat
    import numpy as np
    import pandas as pd
    from ipykernel.inprocess.manager import InProcessKernelManager
    from nbconvert import HTMLExporter
    from sklearn.impute import SimpleImputer
    from sklearn.neighbors import NearestCentroid
    from sklearn.tree import DecisionTreeClassifier

    path=BRIDGE if kind in ("bridge","bridge-route") else MAIN
    if kind=="original-route":
        path=LESSON/"week01_python_tables.ipynb"
    book=nbformat.read(path,as_version=4)
    nbformat.validate(book)
    saved=nbformat.read(path,as_version=4)
    if kind in ("bridge","main"):
        html=(LESSON/(path.stem+".html")).read_text(encoding="utf-8")
        assert HTMLExporter().from_notebook_node(book)[0]==html,"HTML differs"
    if kind=="bridge-route":
        indices=[2,14,16,22,24,27,29,31,33]
    elif kind=="original-route":
        indices=[3,27,54,19,20,22,43,46,48,59,64,69,71,73,74,78,84]
    else:
        indices=[i for i,c in enumerate(book.cells) if c.cell_type=="code"]
    def payloads(cell):
        out=[]
        for item in cell.outputs:
            if item.output_type=="stream": out.append(("stream",item.name,item.text))
            elif item.output_type in ("display_data","execute_result"):
                out.append((item.output_type,dict(item.data)))
            else: out.append((item.output_type,dict(item)))
        return out

    manager=InProcessKernelManager();manager.start_kernel()
    shell=manager.kernel.shell;client=manager.client();client.start_channels()
    try:
        for index in indices:
            cell=book.cells[index]
            assert cell.cell_type=="code",(kind,index)
            client.execute(cell.source,store_history=True)
            reply=client.get_shell_msg(timeout=120)
            if reply["content"]["status"]!="ok":
                raise AssertionError(f"{kind} cell {index}: {reply['content']}")
            cell.execution_count=reply["content"]["execution_count"]
            cell.outputs=[]
            while True:
                msg=client.get_iopub_msg(timeout=120)
                if msg["msg_type"]=="status" and msg["content"].get("execution_state")=="idle":
                    break
                if msg["msg_type"] in ("stream","display_data","execute_result","error"):
                    cell.outputs.append(nbformat.v4.output_from_msg(msg))
            assert not any(item.output_type=="error" for item in cell.outputs)
            if kind in ("bridge","main"):
                assert payloads(cell)==payloads(saved.cells[index]),f"stored output differs {kind}:{index}"
        ns=shell.user_ns; checks=[]
        if kind=="bridge":
            unit=ns["normalize_rows"]; cosine=ns["cosine_scores"]
            Q=ns["Q"];G=ns["G"];ids=ns["candidate_ids"]
            assert Q.shape==(2,2) and G.shape==(4,2)
            assert np.array_equal(ns["raw_scores"],[[3,0,2,1],[4,2,0,.5]])
            assert ids[np.argmax(ns["raw_scores"],axis=1)].tolist()==[42,42]
            assert np.allclose(np.linalg.norm(unit(G),axis=1),1)
            assert np.linalg.norm(G,axis=1,keepdims=True).shape==(4,1)
            score=cosine(Q,G)
            assert score.shape==(2,4)
            assert np.allclose(score[0],[.6,0,1,2/np.sqrt(5)])
            assert ids[np.argmax(score,axis=1)].tolist()==[19,7]
            dist=((G-Q[0])**2).sum(axis=1)
            assert np.allclose(dist,[20,5,1,.25]) and ids[dist.argmin()]==35
            checks.append("candidate_native_dot_cosine_distance_and_ids")

            q=np.array([[0.,2.,-2.],[1.,2.,2.]])
            g=np.array([[2.,0.,0.],[0.,0.,-3.],[1.,2.,2.]])
            g_ids=np.array([71,48,83])
            expected=np.array([[0,1/np.sqrt(2),0],[1/3,-2/3,1]])
            assert np.allclose(cosine(q,g),expected,atol=1e-12)
            assert g_ids[np.argmax(cosine(q,g),axis=1)].tolist()==[48,83]
            assert np.allclose(np.linalg.norm(unit(q),axis=1),1)
            assert np.allclose(cosine(q*7,g),expected)
            scaled=g.copy();scaled[1]*=10
            assert np.allclose(cosine(q,scaled),expected)
            assert np.allclose(cosine(-q[:1],g),-expected[:1])
            flipped=g.copy();flipped[1]*=-1
            flipped_expected=expected.copy();flipped_expected[:,1]*=-1
            assert np.allclose(cosine(q,flipped),flipped_expected)
            checks.append("native_functions_unseen_three_features_and_positive_negative_scaling")

            square=np.array([[2.,0.],[3.,4.]])
            correct=unit(square); wrong=square/np.linalg.norm(square,axis=1)
            assert correct.shape==wrong.shape==(2,2)
            assert np.allclose(correct,[[1,0],[.6,.8]])
            assert np.allclose(wrong,[[1,0],[1.5,.8]])
            assert np.allclose(np.linalg.norm(wrong,axis=1),[1,1.7])
            bad_axis=G/np.linalg.norm(G,axis=0,keepdims=True)
            assert bad_axis.shape==unit(G).shape
            assert not np.allclose(np.linalg.norm(bad_axis,axis=1),1)
            assert ids[np.argmax(cosine(Q[:,::-1],G),axis=1)].tolist()!=[19,7]
            for bad in ([[0,0]],[[np.nan,1]],[[np.inf,1]],[[1e308,1e308]],[]):
                try: unit(bad)
                except ValueError: pass
                else: raise AssertionError("invalid vector accepted")
            try: cosine([[1,0]],[[1,2,3]])
            except ValueError: pass
            else: raise AssertionError("different feature counts accepted")
            checks.append("same_shape_wrong_axis_broadcast_feature_order_and_rejected_invalids")

            tie=cosine([[1,0]],[[2,0],[4,0]])[0]
            tie_ids=np.array([19,8])
            assert np.allclose(tie,[1,1]) and tie_ids[np.argmax(tie)]==19
            assert tie_ids[::-1][np.argmax(tie[::-1])]==8
            for order in itertools.permutations(range(4)):
                order=np.array(order)
                pos=np.argmax(cosine(Q,G[order]),axis=1)
                assert ids[order][pos].tolist()==[19,7]
            assert ns["right"].tolist()==[19,7] and ns["wrong"].tolist()==[42,35]
            checks.append("tie_first_position_and_24_unique_winner_id_permutations")

            pool=ns["lookup_and_masked_mean"]
            E=np.array([[99,98,97,96],[0,0,0,0],[1,2,0,4],
                        [3,-2,4,0],[5,0,1,2],[-1,3,2,1]],float)
            I=np.array([[2,3,2],[1,4,0]])
            vec,mask,sums,counts,means=pool(E,I)
            assert E.shape==(6,4) and I.shape==(2,3) and vec.shape==(2,3,4)
            assert mask.tolist()==[[True,True,True],[True,True,False]]
            assert counts.tolist()==[[3],[2]]
            assert np.allclose(sums,[[5,2,4,8],[5,0,1,2]])
            assert np.allclose(means,[[5/3,2/3,4/3,8/3],[2.5,0,.5,1]])
            assert np.array_equal(vec[0,0],vec[0,2])
            changed=E.copy();changed[0]=[-8,7,5,4]
            assert np.allclose(pool(changed,I)[-1],means)
            extended=np.pad(I,((0,0),(0,3)),constant_values=0)
            assert np.allclose(pool(E,extended)[-1],means)
            rev=I[:,::-1];rev_vec,_,_,_,rev_mean=pool(E,rev)
            assert not np.array_equal(vec,rev_vec) and np.allclose(means,rev_mean)
            zero_vec,zero_mask,zero_sum,zero_count,zero_mean=pool(E,[[1,0,0]])
            assert zero_mask.tolist()==[[True,False,False]] and zero_count.tolist()==[[1]]
            assert np.array_equal(zero_sum,[[0,0,0,0]]) and np.array_equal(zero_mean,[[0,0,0,0]])
            try: cosine(zero_mean,[[1,1,1,1]])
            except ValueError: pass
            else: raise AssertionError("zero mean was incorrectly accepted for cosine")
            for bad in ([[-1,2,0]], [[6,2,0]], [[2.,1.,0.]],
                        [[True,2,0]], [[0,0,0]]):
                try: pool(E,bad)
                except ValueError: pass
                else: raise AssertionError(f"invalid token IDs accepted: {bad}")
            try: pool([[np.nan,0],[1,1]],[[1,0]])
            except ValueError: pass
            else: raise AssertionError("non-finite table accepted")
            checks.append("actual_lookup_helper_unseen_V6_B2_T3_d4_and_boundaries")

            qvec,qmask,qsums,qcounts,q=pool(ns["token_table_new"],ns["query_tokens_new"])
            assert qvec.shape==(2,4,2) and qmask.tolist()==[[True,True,True,False],[True,True,False,False]]
            assert qcounts.tolist()==[[3],[2]] and qsums.tolist()==[[6,9],[6,4]]
            assert np.allclose(q,[[2,3],[3,2]])
            assert qmask[1,1] and np.array_equal(qvec[1,1],[0,0])
            g=ns["gallery_new"];ids=ns["g_ids_new"]
            raw=q@g.T;scores=cosine(q,g)
            assert raw.tolist()==[[7,9,5,4],[8,6,5,6]]
            assert ids[np.argmax(raw,axis=1)].tolist()==[8,90]
            assert ids[np.argmax(scores,axis=1)].tolist()==[53,90]
            order=np.array([2,0,3,1]);pos=np.argmax(cosine(q,g[order]),axis=1)
            assert pos.tolist()==[0,1]
            assert ids[order][pos].tolist()==[53,90] and ids[pos].tolist()==[90,8]
            naive=qvec.mean(axis=1)
            assert np.allclose(naive,[[3.25,5],[5,6.5]])
            assert ids[np.argmax(cosine(naive,g),axis=1)].tolist()==[53,53]
            zero_pad=ns["token_table_new"].copy();zero_pad[0]=0
            full_T=zero_pad[ns["query_tokens_new"]].mean(axis=1)
            assert np.allclose(full_T,[[1.5,2.25],[1.5,1]])
            assert not np.allclose(full_T,q) and np.allclose(cosine(full_T,g),scores)
            for prefix in ("# 필수 A:", "# 필수 B:"):
                answers=[c for c in saved.cells if c.cell_type=="code" and c.source.startswith(prefix)]
                assert len(answers)==1 and not ast.parse(answers[0].source).body and answers[0].outputs==[]
            teacher=(LESSON/"week01_axes_linear_bridge_teacher.md").read_text(encoding="utf-8")
            assert "Q=[[2,3],[3,2]]" in teacher and "[[7,9,5,4],[8,6,5,6]]" in teacher
            checks.append("reference_B_actual_helper_counts_sums_mean_cosine_ID_and_teacher")
            assert len(book.cells)==35
        elif kind=="bridge-route":
            assert ns["X_new"].shape==(3,2) and ns["W_new"].shape==(2,2)
            assert ns["q_ids_new"].tolist()==[61,22]
            assert "query_new" not in ns
            q=ns["lookup_and_masked_mean"](ns["token_table_new"],ns["query_tokens_new"])[-1]
            assert ns["g_ids_new"][np.argmax(ns["cosine_scores"](q,ns["gallery_new"]),axis=1)].tolist()==[53,90]
            assert not ast.parse(saved.cells[29].source).body and not ast.parse(saved.cells[33].source).body
            checks.append("fresh_kernel_2_14_16_22_24_27_29_31_33_prepares_reuse")
        elif kind=="original-route":
            assert "sunlight_hours" in ns["plants"] and "light_h" not in ns["plants"]
            assert ns["plants"].shape==(6,5) and ns["new_plants"].shape==(4,5)
            assert ns["dirty_plants"].loc[ns["dirty_plants"]["pot_id"]=="P02","water_ml"].item()=="20ml"
            assert ns["site_notes"].shape==(2,2) and "sns" in ns
            checks.append("fresh_original_preparation_and_provided_examples")
        else:
            df=ns["plants"]
            assert ns["observed_mean"](df["water_ml"].tolist())==24
            assert ns["observed_mean"]([0,None,np.nan,6])==3
            assert ns["observed_mean"]([None,np.nan]) is None
            assert np.array_equal(ns["x_train"][0],[0,0])
            assert ns["model"].predict([[0,0]]).tolist()==[0]
            assert ns["predictions"].tolist()==[0,1] and ns["validation_accuracy"]==.5
            assert ns["checked"]["pot_id"].tolist()==["P05","P06"]
            assert ns["file_check"]["prediction"].tolist()==[0,1]
            assert not ns["result_path"].exists()
            checks.append("main_fit_zero_valid_and_physical_csv_roundtrip")

            answer=[c for c in saved.cells if c.cell_type=="code" and c.source.startswith("# 새 명세의 특성과 모델")]
            assert len(answer)==1 and not ast.parse(answer[0].source).body and answer[0].outputs==[]
            text="".join(c.source for c in saved.cells if c.cell_type=="markdown")
            for fragment in ("query_ids =", "def normalize_rows(vectors):", "embedding_table =", "def lookup_and_masked_mean(table, token_ids):", "완성 예제를 가립니다"):
                assert fragment in text
            assert "N7,점검" not in html and "N7,점검" not in MAIN.read_text()
            checks.append("student_blank_and_precise_function_reuse_instructions")

            def count(panel):
                return sum(int(panel[r,c,0]==1 and panel[r,c,1]==2)
                           for r in range(2) for c in range(2))
            train=ns["exercise_train"];valid=ns["exercise_validation"];new=ns["exercise_input"]
            known=train[train["label"]!="?"].copy()
            assert known["unit"].tolist()==["T1","T2","T3","T4"]
            imputer=SimpleImputer().fit(known[["signal"]])
            assert imputer.statistics_.tolist()==[4] and train["signal"].mean()==28
            def features(frame):
                return np.column_stack((imputer.transform(frame[["signal"]]).ravel(),
                                        [count(p) for p in frame["panel"]]))
            X=features(known);V=features(valid);N=features(new)
            assert X.tolist()==[[0,3],[3,1],[4,2],[9,0]]
            assert X.tolist()!=ns["x_train"].tolist()
            centroid=NearestCentroid().fit(X,known["label"])
            tree=DecisionTreeClassifier(max_depth=2,random_state=0).fit(X,known["label"])
            assert centroid.predict(V).tolist()==["정상","점검","정상"]
            assert tree.predict(V).tolist()==["정상","점검","점검"]
            assert (centroid.predict(V)==valid["label"]).mean()==2/3
            assert (tree.predict(V)==valid["label"]).mean()==1
            pairs=dict(zip(new["unit"],centroid.predict(N)))
            output=pd.DataFrame({"sample_id":ns["exercise_order"],
                                 "prediction":[pairs[i] for i in ns["exercise_order"]]})
            assert output["prediction"].tolist()==["점검","점검","정상"]
            with tempfile.TemporaryDirectory(prefix="device-csv-check-") as tmp:
                out=Path(tmp)/"device.csv";output.to_csv(out,index=False)
                assert pd.read_csv(out).equals(output)
            wrong_output=output.copy()
            wrong_output["prediction"]=wrong_output["prediction"].iloc[::-1].to_numpy()
            assert wrong_output["sample_id"].tolist()==output["sample_id"].tolist()
            assert set(wrong_output["prediction"])==set(output["prediction"])
            assert not wrong_output.equals(output)
            def check_device_input(frame):
                if "unit" not in frame or "signal" not in frame or "panel" not in frame:
                    raise ValueError("missing required column")
                if frame["unit"].isna().any() or frame["unit"].duplicated().any():
                    raise ValueError("missing or duplicate ID")
            check_device_input(new)
            for bad in (new.drop(columns="signal"),
                        pd.concat([new,new.iloc[[0]]],ignore_index=True)):
                try: check_device_input(bad)
                except ValueError: pass
                else: raise AssertionError("teacher reference accepted bad device input")
            teacher=(LESSON/"week01_integrated_teacher.md").read_text(encoding="utf-8")
            assert "N7,점검" in teacher and "N3,점검" in teacher and "N1,정상" in teacher
            checks.append("teacher_reference_new_X_mean_models_csv_ID_and_error_cases")
            assert len(book.cells)==38
        result={"kind":kind,"status":"passed","cells":len(book.cells),
                "executed_code_cells_zero_based":indices,"checks":checks}
    finally:
        client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
    print(json.dumps(result,ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker",choices=["bridge","main","bridge-route","original-route"])
    parser.add_argument("--write",type=Path)
    parser.add_argument("--protected-worktree",type=Path,
                        help="optional root of the separate protected worktree")
    args=parser.parse_args()
    if args.worker:
        run_worker(args.worker);return
    paths=[BRIDGE,BRIDGE.with_suffix(".html"),LESSON/"week01_axes_linear_bridge_teacher.md",
           MAIN,MAIN.with_suffix(".html"),LESSON/"week01_integrated_teacher.md",
           LESSON/"week01_python_tables.ipynb",LESSON/"week01_problem_pipeline.ipynb",
           LESSON/"data/week1_plants.csv",LESSON/"data/week1_plants_new.csv"]
    protected=[]
    if args.protected_worktree is not None:
        base=args.protected_worktree.resolve()/"lessons/week01"
        protected=[base/"week01_python_tables.ipynb",base/"week01_python_tables.html",
                   base/"lesson-manifest.json",base/"teacher-notes.txt",base/"validation.json",
                   base/"data/week1_plants.csv",base/"data/week1_plants_new.csv"]
        if any(not p.is_file() for p in protected):
            parser.error("specified protected worktree is missing a tracked comparison file")
        paths.extend(protected)
    before={str(p):sha(p) for p in paths}
    results=[]
    for kind in ("bridge","main","bridge-route","original-route"):
        with tempfile.TemporaryDirectory(prefix="week01-retrieval-qa-") as tmp:
            env={**os.environ,"IPYTHONDIR":tmp,"MPLCONFIGDIR":tmp,
                 "PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1",
                 "PYDEVD_DISABLE_FILE_VALIDATION":"1"}
            cmd=[sys.executable,"-B",str(Path(__file__).resolve()),"--worker",kind]
            proc=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
            if proc.returncode:
                raise RuntimeError(f"{kind} failed: {proc.stdout}\n{proc.stderr}")
            results.append(json.loads(proc.stdout))
    assert before=={str(p):sha(p) for p in paths}
    receipt={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
             "method":"four separate processes, each with a fresh in-process kernel",
             "results":results,"source_sha256_before_and_after":before,
             "validator_sha256":sha(Path(__file__)),
             "protected_worktree":{"status":"checked" if protected else "not_checked",
                                   "files_compared":len(protected)},
             "limitations":["student answers were not completed by a learner",
                            "device exercise model/CSV checks are a teacher reference, not student execution",
                            "normalizer tests use small finite vectors; not a universal floating-point proof",
                            "ordinary socket Jupyter/Colab and full browser rendering not tested",
                            "student workload, learning, and international contest success unobserved"]}
    if args.write:
        with args.write.open("x",encoding="utf-8") as stream:
            stream.write(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(receipt,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
