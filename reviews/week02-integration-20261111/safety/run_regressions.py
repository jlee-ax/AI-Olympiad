"""Reproduce safety checks in temporary copies. Never run the old validator on source files."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
SAFETY = Path(__file__).resolve().parent
NAMES = ("week02_prediction_evaluation.ipynb", "week02_prediction_evaluation.html", "validation.json")
EXPECTED_BASELINE = "9bb1ea5110b74ea1cf32fbc9ee9e9a5aadbceba2f750c2dfc2d6587e18954bdf"
PYTHON = Path("/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source(cell):
    return "".join(cell["source"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append", help="Run only named cases, preserving separate result files.")
    parser.add_argument("--python", type=Path, default=PYTHON)
    parser.add_argument("--candidate-notebook", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--skip-subprocess", action="store_true", help="Do not repeat a socket-kernel attempt after an environment prohibition.")
    parser.add_argument("--results", type=Path, default=SAFETY / "results.json")
    args = parser.parse_args()
    raw = {name: subprocess.check_output(["git", "show", "HEAD:lessons/week02/" + name], cwd=ROOT) for name in NAMES}
    assert sha(raw[NAMES[0]]) == EXPECTED_BASELINE
    baseline_sha = sha(raw[NAMES[0]])
    if args.candidate_notebook:
        raw[NAMES[0]] = args.candidate_notebook.read_bytes()
        assert args.expected_sha and sha(raw[NAMES[0]]) == args.expected_sha
    validator = (ROOT / "lessons/week02/teacher_validate_week02.py").read_bytes()
    book = json.loads(raw[NAMES[0]])
    assert source(next(c for c in book["cells"] if source(c).startswith("# 혼자 작성하는 공간")))
    cases = []
    def add(name, expected=0, detector=None, mutation=None, wrapper=None, output=False, mode="inprocess", path_case=None):
        cases.append(dict(name=name, expected=expected, detector=detector, mutation=mutation, wrapper=wrapper, output=output, mode=mode, path_case=path_case))
    add("normal_comment_template_count7", mutation=lambda b,a: a.update(execution_count=7))
    add("repeat_normal")
    if not args.skip_subprocess:
        add("normal_fresh_subprocess_kernel", mode="subprocess")
    add("normal_new_output", output=True)
    add("repeat_new_output", output=True)
    add("code_answer", 1, "원래의 빈 주석 템플릿만", lambda b,a: a.update(source=source(a)+"\nanswer = 42"))
    add("comment_answer", 1, "원래의 빈 주석 템플릿만", lambda b,a: a.update(source=source(a)+"\n# 정답은 평균 6입니다"))
    def duplicate(b,a):
        cloned=copy.deepcopy(a); cloned["id"]="duplicate-answer"; b["cells"].append(cloned)
    add("duplicate_answer", 1, "정확히 하나", duplicate)
    add("stored_answer_output", 1, "저장된 실행 출력", lambda b,a: a.update(outputs=[dict(output_type="stream", name="stdout", text=["saved answer\n"])]))
    add("missing_answer", 1, "정확히 하나", lambda b,a: b["cells"].remove(a))
    add("missing_cell_id", 1, "IDs must be present", lambda b,a: b["cells"][0].pop("id"))
    add("duplicate_cell_id", 1, "IDs must be unique", lambda b,a: b["cells"][0].update(id=b["cells"][1]["id"]))
    def extra(code):
        def mutation(b,a):
            b["cells"].append(dict(cell_type="code", id="reviewer-extra", metadata={}, source=code, execution_count=None, outputs=[]))
        return mutation
    add("code_runtime_failure", 1, "reviewer code failure", extra("raise RuntimeError('reviewer code failure')"), output=True)
    add("qa_unknown_in_fit_rows", 1, "known_train.row_id.tolist()", extra("known_train = train.copy()"), output=True)
    add("qa_preprocessing_leak", 1, "preprocess.named_steps", extra("preprocess.fit(pd.concat([X_train, X_val]))"), output=True)
    add("qa_group_overlap", 1, "set(train.group).isdisjoint", extra("train = pd.concat([train, validation.iloc[:1]])"), output=True)
    add("qa_metric_orientation", 1, "rule_cm.tolist()", extra("rule_cm = rule_cm.T"), output=True)
    add("relative_writes_are_temporary", mutation=extra("from pathlib import Path\nPath('ordinary-relative-write.txt').write_text('temporary')"))
    plot="get_ipython().run_line_magic('matplotlib', 'inline')\nimport matplotlib.pyplot as plt\nplt.plot([0,1],[1,0])\ndisplay(plt.gcf())\nplt.close('all')"
    add("plot_outputs_preserved", mutation=extra(plot), output=True)
    add("render_failure", 1, "reviewer render failure", wrapper="m.render_html = lambda nb: (_ for _ in ()).throw(RuntimeError('reviewer render failure'))", output=True)
    add("output_failure_rollback", 1, "reviewer output failure", wrapper="original_open=m.Path.open\ndef failing_open(self, mode='r', *a, **k):\n    if mode == 'xb' and self.suffix == '.html':\n        raise OSError('reviewer output failure')\n    return original_open(self, mode, *a, **k)\nm.Path.open=failing_open", output=True)
    add("missing_input", 1, "FileNotFoundError", path_case="missing")
    add("optimized_python_rejected", 1, "Optimized Python disables QA assertions", path_case="optimized")
    add("optimized_env_rejected", 1, "Optimized Python disables QA assertions", path_case="optimized_env")
    for path_case in ("existing_dir", "existing_file", "symlink_dir", "dangling_symlink", "symlink_parent", "overlap_input", "overlap_parent", "missing_parent"):
        add("path_"+path_case, 1, {"symlink_dir":"심링크", "dangling_symlink":"심링크", "symlink_parent":"심링크", "overlap_input":"겹칩니다", "overlap_parent":"겹칩니다", "missing_parent":"부모는 기존"}.get(path_case,"새 경로"), path_case=path_case)
    add("late_output_collision", 1, "새 경로", path_case="late_collision", output=True)
    # A reviewer-only reference on genuinely different data. This does not fill a
    # student answer and does not claim that a student solved a changed problem.
    independent="""review = pd.DataFrame([('u1','U',-4,-1),('u2','U',2,1),('v1','V',8,1),('v2','V',np.nan,-1),('v3','V',31,0),('w1','W',26,1),('w2','W',np.nan,-1)], columns=['row_id','group','reading','label'])
review_train=review[review.group.isin(['U','V']) & review.label.isin([-1,1])]
review_val=review[review.group.eq('W')]
review_pipe=Pipeline([('imputer',SimpleImputer()),('scaler',StandardScaler())]).fit(review_train[['reading']])
assert review_train.row_id.tolist()==['u1','u2','v1','v2']
assert np.isclose(review_pipe.named_steps['imputer'].statistics_[0],2)
assert np.isclose(review_pipe.named_steps['scaler'].scale_[0],np.sqrt(18))
assert np.allclose(review_pipe.transform(review_val[['reading']])[:,0],[24/np.sqrt(18),0])
"""
    add("independent_new_input_reference", mutation=extra(independent))
    def run(case):
        with tempfile.TemporaryDirectory(prefix="week02-safety-case-") as temporary:
            folder=Path(temporary)
            input_dir=folder/"input"; input_dir.mkdir()
            for name,data in raw.items(): (input_dir/name).write_bytes(data)
            script=input_dir/"teacher_validate_week02.py"; script.write_bytes(validator)
            b=copy.deepcopy(book)
            a=next(c for c in b['cells'] if source(c).startswith('# 혼자 작성하는 공간'))
            if case['mutation']:
                case['mutation'](b,a)
                (input_dir/NAMES[0]).write_text(json.dumps(b,ensure_ascii=False))
            existing=folder/'existing-user-output'; existing.mkdir(); (existing/'keep.txt').write_text('user edits preserved')
            output=folder/'NEW'; extra_args=[]
            path_case=case['path_case']
            if path_case=='existing_dir': output=existing
            elif path_case=='existing_file': output=existing/'keep.txt'
            elif path_case=='symlink_dir': output=folder/'link'; output.symlink_to(existing, target_is_directory=True)
            elif path_case=='dangling_symlink': output=folder/'link'; output.symlink_to(folder/'absent')
            elif path_case=='symlink_parent': (folder/'link').symlink_to(existing,target_is_directory=True); output=folder/'link'/'NEW'
            elif path_case=='overlap_input': output=input_dir/NAMES[0]
            elif path_case=='overlap_parent': output=input_dir
            elif path_case=='missing_parent': output=folder/'absent'/'NEW'
            elif path_case=='missing': extra_args += ['--notebook',str(input_dir/'missing.ipynb')]
            elif path_case=='late_collision':
                b['cells'].append(dict(cell_type='code',id='reviewer-late-collision',metadata={},execution_count=None,outputs=[],source=f"from pathlib import Path\np=Path({str(output)!r})\np.mkdir()\n(p/'keep.txt').write_text('created during execution')"))
                (input_dir/NAMES[0]).write_text(json.dumps(b,ensure_ascii=False))
            if case['output'] or path_case not in (None,'missing','optimized','optimized_env'): extra_args += ['--output-dir',str(output)]
            protected=[input_dir/name for name in NAMES]+[existing/'keep.txt']
            before={str(p.relative_to(folder)):sha(p.read_bytes()) for p in protected}
            runtime=folder/'outer-cache'; runtime.mkdir()
            env=os.environ.copy(); env['TMPDIR']=str(runtime); env['PYTHONDONTWRITEBYTECODE']='1'
            for key in ('IPYTHONDIR','MPLCONFIGDIR','JUPYTER_RUNTIME_DIR','JUPYTER_CONFIG_DIR','JUPYTER_DATA_DIR','XDG_CACHE_HOME'):
                env[key]=str(runtime/key.lower())
            if path_case=='optimized_env': env['PYTHONOPTIMIZE']='1'
            cli=['--inprocess'] if case['mode']=='inprocess' else []
            if case['wrapper']:
                wrapper=folder/'wrapper.py'
                wrapper.write_text("import importlib.util\ns=importlib.util.spec_from_file_location('review_validator',"+repr(str(script))+")\nm=importlib.util.module_from_spec(s)\ns.loader.exec_module(m)\n"+case['wrapper']+"\nm.main("+repr(cli+extra_args)+")\n")
                command=[str(args.python),'-B',str(wrapper)]
            else: command=[str(args.python),'-B',*(['-O'] if path_case=='optimized' else []),str(script),*cli,*extra_args]
            result=subprocess.run(command,cwd=input_dir,env=env,capture_output=True,text=True,timeout=120)
            after={str(p.relative_to(folder)):sha(p.read_bytes()) for p in protected}
            expected_detected=(result.returncode==case['expected'] and (not case['detector'] or case['detector'] in result.stderr))
            checks=dict(expected_exit_and_detector=expected_detected,protected_sha_unchanged=before==after,runtime_cache_removed=not any(runtime.iterdir()),no_adjacent_new_files=set(p.name for p in input_dir.iterdir())==set(NAMES)|{'teacher_validate_week02.py'})
            artifacts={}
            if case['output'] and case['expected']==0 and result.returncode==0 and all((output/name).is_file() for name in NAMES):
                outbook=json.loads((output/NAMES[0]).read_text())
                identity=lambda x:[(c['id'],c['cell_type'],source(c)) for c in x['cells']]
                checks['three_artifacts_only']=set(p.name for p in output.iterdir())==set(NAMES)
                checks['sources_ids_unchanged']=identity(outbook)==identity(b)
                checks['qa_removed']=not any('Teacher-only checks passed' in source(c) for c in outbook['cells'])
                answer=next(c for c in outbook['cells'] if source(c).startswith('# 혼자 작성하는 공간'))
                checks['answer_still_blank_no_output']=source(answer)==source(a) and not answer['outputs']
                checks['report_stdout_matches_file']=json.loads(result.stdout)==json.loads((output/'validation.json').read_text())
                output_report=json.loads(result.stdout)
                checks['report_artifact_sha_matches_files']=all(output_report['artifacts'][name]['sha256']==sha((output/name).read_bytes()) and output_report['artifacts'][name]['bytes']==len((output/name).read_bytes()) for name in NAMES[:2])
                checks['html_contains_sources_and_outputs']='훈련 개체' in (output/NAMES[1]).read_text() and 'Teacher-only checks passed' not in (output/NAMES[1]).read_text()
                if case['name']=='plot_outputs_preserved': checks['plot_retained_in_nb_and_html']=any('image/png' in o.get('data',{}) for c in outbook['cells'] for o in c.get('outputs',[])) and 'image/png;base64' in (output/NAMES[1]).read_text()
                artifacts={name:sha((output/name).read_bytes()) for name in NAMES}
            elif case['output'] and case['expected']==0: checks['expected_artifacts_present']=False
            elif case['output'] and path_case!='late_collision': checks['no_partial_output_directory']=not output.exists()
            if path_case=='late_collision': checks['late_existing_output_preserved']=(output/'keep.txt').read_text()=='created during execution' and len(list(output.iterdir()))==1
            return dict(name=case['name'],passed=all(checks.values()),checks=checks,returncode=result.returncode,detector=case['detector'],before_sha256=before,after_sha256=after,artifact_sha256=artifacts,stdout=result.stdout,stderr=result.stderr)
    def run_safe(case):
        try:
            return run(case)
        except Exception:
            return dict(name=case["name"],passed=False,checks={"harness_completed":False},returncode=None,detector=case["detector"],stdout="",stderr=traceback.format_exc())
    if args.case:
        cases=[case for case in cases if case["name"] in args.case]
        if len(cases)!=len(set(args.case)):
            raise ValueError("Unknown case selection")
    with ThreadPoolExecutor(max_workers=2) as executor:
        results=list(executor.map(run_safe,cases))
    reproduced={c["name"]:c for c in results if c["name"] in ("normal_new_output","repeat_new_output")}
    reproduction = ({"notebook_bytes_equal": reproduced["normal_new_output"]["artifact_sha256"][NAMES[0]] == reproduced["repeat_new_output"]["artifact_sha256"][NAMES[0]], "html_bytes_equal": reproduced["normal_new_output"]["artifact_sha256"][NAMES[1]] == reproduced["repeat_new_output"]["artifact_sha256"][NAMES[1]]} if len(reproduced)==2 and all(c["passed"] for c in reproduced.values()) else {"status":"not run in this selection"})
    report=dict(created_utc=datetime.now(timezone.utc).isoformat(),validator_sha256=sha(validator),baseline_notebook_sha256=baseline_sha,input_notebook_sha256=sha(raw[NAMES[0]]),python=str(args.python),all_passed=all(c['passed'] for c in results),cases=results,reproduction=reproduction,skipped=['ordinary socket kernel: prior attempt denied by environment; see baseline-first-results.json'] if args.skip_subprocess else [],limitations=['arbitrary Python absolute-path access is not blocked; no OS sandbox','finite examples do not observe student mastery or timing','system Python smoke missing nbformat; not counted as semantic execution','remote MathJax availability and browser visual inspection not tested here'])
    args.results.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(all_passed=report['all_passed'],validator_sha256=report['validator_sha256'],cases=[{k:c[k] for k in ('name','passed','returncode')} for c in results]),ensure_ascii=False,indent=2))
    return 0 if report['all_passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
