"""Teacher-only finite checks; run trusted notebooks without refreshing their source files.

Default: isolated working directory, in-memory artifacts, JSON on stdout.
Refresh: --output-dir NEW creates the executed notebook, HTML and validation.json.
The temporary directory is not an OS security sandbox: arbitrary Python can still
access absolute paths. Run only trusted notebooks, or use separate OS isolation.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse
import ast
import hashlib
import importlib.metadata
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "week02_prediction_evaluation.ipynb"
ASSESSMENT_MARKER = "# 혼자 작성하는 공간"
ASSESSMENT_TEMPLATE = """# 혼자 작성하는 공간: 새 DataFrame, 훈련/검증 분할, 파이프라인, 예측, 혼동행렬
# 아래에 코드를 직접 작성하세요."""
QA_SOURCE = r'''
assert set(train.group).isdisjoint(validation.group)
assert known_train.row_id.tolist() == ["a1", "a2", "b1", "b2"]
assert np.isclose(preprocess.named_steps["imputer"].statistics_[0], 4)
assert np.isclose(preprocess.named_steps["scaler"].mean_[0], 4)
assert np.isclose(preprocess.named_steps["scaler"].scale_[0], np.sqrt(2))
assert np.allclose(val_z[:,0], np.array([16, 0, 6, 8]) / np.sqrt(2))
assert np.isclose(leaky_imputer.statistics_[0], 9)
assert rule_pred.tolist() == [1,-1,1,1]
assert rule_cm.tolist() == [[0,2],[1,1]]
assert np.isclose(precision, 1/3) and np.isclose(recall, 1/2)
assert np.isclose(baseline.named_steps["imputer"].statistics_[0], 4)
assert np.isclose(baseline.named_steps["scaler"].mean_[0], 4)
assert np.isclose(baseline.named_steps["scaler"].scale_[0], np.sqrt(2))
assert cm_baseline.tolist() == [[2,0],[2,0]] and np.isnan(p_nan) and r_nan == 0
assert confusion_matrix(truth_with_unknown[known], predictions[known], labels=[-1,1]).tolist() == [[0,1],[1,1]]
assert confusion_matrix(wrong_truth, predictions, labels=[-1,1]).tolist() == [[1,1],[1,1]]
assert np.isclose(group_example.correct.mean(), 2/3) and np.isclose(group_accuracy['mean'].mean(), .4)

# Historical M/N finite control; it is not the current two-contract assessment.
new = pd.DataFrame([
    ('m1','M',3,-1), ('m2','M',6,1), ('n1','N',9,1), ('n2','N',np.nan,-1), ('n3','N',12,0),
    ('o1','O',99,1), ('o2','O',np.nan,1), ('p1','P',np.nan,-1), ('p2','P',np.nan,-1),
], columns=['row_id','group','reading','label'])
new_train = new[new.group.isin(['M','N']) & new.label.isin([-1,1])]
new_val = new[new.group.isin(['O','P'])]
new_pipe = Pipeline([('imputer',SimpleImputer()), ('scaler',StandardScaler())])
new_pipe.fit(new_train[['reading']])
assert new_train.row_id.tolist() == ['m1','m2','n1','n2']
assert np.isclose(new_pipe.named_steps['imputer'].statistics_[0], 6)
assert np.isclose(new_pipe.named_steps['scaler'].mean_[0], 6)
assert np.isclose(new_pipe.named_steps['scaler'].scale_[0], np.sqrt(4.5))
assert np.isclose(SimpleImputer().fit(pd.concat([new_train[['reading']],new_val[['reading']]])).statistics_[0],29.25)
new_z = new_pipe.transform(new_val[['reading']])[:,0]
new_pred = np.where(new_z >= 1,1,-1)
assert new_pred.tolist() == [1,-1,-1,-1]
assert confusion_matrix(new_val.label,new_pred,labels=[-1,1]).tolist() == [[2,0],[1,1]]
new_p,new_r,_,_ = precision_recall_fscore_support(new_val.label,new_pred,average='binary',pos_label=1,zero_division=0)
assert new_p == 1 and new_r == .5 and (new_val.label.to_numpy() == new_pred).mean() == .75
assert np.isclose((3+1)/(3+5),.5) and np.isclose((3/3+1/5)/2,.6)
assert roc_matrices[.5] == [[1,1],[1,1]]
assert roc_matrices[.3] == [[1,1],[0,2]]
print('Teacher-only checks passed')
'''


def validate_assessment(nb):
    """Reject answers and stored results before running any notebook code."""
    cells = [c for c in nb.cells if c.cell_type == "code" and ASSESSMENT_MARKER in c.source]
    if len(cells) != 1:
        raise ValueError("배포용 독립 과제 칸은 정확히 하나여야 합니다.")
    cell = cells[0]
    # AST alone accepts arbitrary comment answers. Only the distributed template
    # is permitted; trailing whitespace/line endings do not count as an answer.
    normalized = "\n".join(line.rstrip() for line in cell.source.splitlines()).strip()
    if normalized != ASSESSMENT_TEMPLATE or ast.parse(cell.source).body:
        raise ValueError("배포용 독립 과제 칸에는 원래의 빈 주석 템플릿만 허용됩니다.")
    if cell.outputs:
        raise ValueError("배포용 독립 과제 칸에 저장된 실행 출력이 있습니다.")
    # A comment-only cell may already have execution_count=7 in the distribution.
    return cell


def check_output_dir(path, notebook):
    """Check lexically as well as after resolution, including dangling symlinks."""
    path = Path(os.path.abspath(path))
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError("출력 경로에는 심링크를 사용할 수 없습니다: " + str(component))
    resolved = path.resolve()
    source = notebook.resolve()
    if resolved == source or resolved in source.parents:
        raise ValueError("출력 디렉터리가 입력 경로와 겹칩니다: " + str(path))
    if os.path.lexists(path):
        raise FileExistsError("출력 디렉터리는 존재하지 않는 새 경로여야 합니다: " + str(path))
    if not path.parent.is_dir():
        raise ValueError("출력 디렉터리의 부모는 기존 디렉터리여야 합니다: " + str(path.parent))
    return path


@contextmanager
def isolated_runtime():
    """Keep ordinary IPython/Jupyter/plot caches and relative writes temporary."""
    with tempfile.TemporaryDirectory(prefix="week02-validator-") as temp:
        workspace = Path(temp)
        variables = {
            "IPYTHONDIR": str(workspace / "ipython"),
            "JUPYTER_CONFIG_DIR": str(workspace / "jupyter-config"),
            "JUPYTER_DATA_DIR": str(workspace / "jupyter-data"),
            "JUPYTER_RUNTIME_DIR": str(workspace / "jupyter-runtime"),
            "MPLCONFIGDIR": str(workspace / "matplotlib"),
            "XDG_CACHE_HOME": str(workspace / "cache"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        previous = {key: os.environ.get(key) for key in variables}
        old_cwd, old_bytecode = Path.cwd(), sys.dont_write_bytecode
        try:
            os.environ.update(variables)
            sys.dont_write_bytecode = True
            os.chdir(workspace)
            yield workspace
        finally:
            os.chdir(old_cwd)
            sys.dont_write_bytecode = old_bytecode
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def execute_notebook(nb, inprocess, workspace):
    if not inprocess:
        from nbclient import NotebookClient
        NotebookClient(nb, timeout=180, kernel_name="python3",
                       resources={"metadata": {"path": str(workspace)}}).execute()
        return
    from ipykernel.inprocess.manager import InProcessKernelManager
    import nbformat
    manager = InProcessKernelManager()
    client = None
    try:
        manager.start_kernel()
        client = manager.client()
        client.start_channels()
        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=180)
            cell.execution_count = reply["content"].get("execution_count")
            cell.outputs = []
            while True:
                message = client.get_iopub_msg(timeout=180)
                kind = message["msg_type"]
                if kind == "status" and message["content"].get("execution_state") == "idle":
                    break
                if kind in ("stream", "display_data", "execute_result", "error"):
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
            if reply["content"]["status"] != "ok":
                raise RuntimeError("Notebook cell " + cell.id + " failed: " + repr(reply["content"]))
            if any(output.output_type == "error" for output in cell.outputs):
                raise RuntimeError("Notebook cell failed: " + cell.id)
    finally:
        if client is not None:
            client.stop_channels()
        if manager.has_kernel:
            manager.shutdown_kernel()


def coalesce_stream_outputs(nb):
    """IPython may chunk one print stream differently between identical runs."""
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        merged = []
        for output in cell.outputs:
            if (output.output_type == "stream" and merged
                    and merged[-1].output_type == "stream"
                    and merged[-1].name == output.name
                    and {k: v for k, v in merged[-1].items() if k != "text"}
                        == {k: v for k, v in output.items() if k != "text"}):
                merged[-1].text += output.text
            else:
                merged.append(output)
        cell.outputs = merged


def render_html(nb):
    from nbconvert import HTMLExporter
    return HTMLExporter().from_notebook_node(nb)[0]


def write_new_outputs(output_dir, notebook, payloads):
    """Never replace an existing target, including a target created during execution."""
    output_dir = check_output_dir(output_dir, notebook)
    # mkdir is the exclusive claim. Rendering and serialization finish before it.
    output_dir.mkdir()
    created = []
    try:
        for name, data in payloads.items():
            destination = output_dir / name
            with destination.open("xb") as stream:
                created.append((destination, os.fstat(stream.fileno())))
                stream.write(data)
    except BaseException:
        # Only remove files this call opened, and only if their inode is unchanged.
        # Never recursively delete a directory that another actor could have edited.
        for destination, before in reversed(created):
            try:
                after = destination.lstat()
                if (after.st_dev, after.st_ino) == (before.st_dev, before.st_ino):
                    destination.unlink()
            except FileNotFoundError:
                pass
        try:
            output_dir.rmdir()
        except OSError:
            pass
        raise


def main(argv=None):
    if not __debug__:
        raise RuntimeError("Optimized Python disables QA assertions; run without -O/PYTHONOPTIMIZE.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inprocess", action="store_true", help="Use a fresh in-process IPython kernel.")
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Trusted, self-contained input notebook.")
    parser.add_argument("--output-dir", type=Path, help="Create three artifacts in a NEW directory; existing paths are refused.")
    args = parser.parse_args(argv)
    notebook = args.notebook.absolute()
    # Fail before kernel startup. Keep a byte snapshot to detect concurrent edits.
    input_bytes = notebook.read_bytes()
    input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    raw_notebook = json.loads(input_bytes.decode("utf-8"))
    raw_ids = [cell.get("id") for cell in raw_notebook.get("cells", [])]
    if any(not isinstance(cell_id, str) or not cell_id for cell_id in raw_ids):
        raise ValueError("Input cell IDs must be present; automatic ID repair is not allowed.")
    if len(set(raw_ids)) != len(raw_ids):
        raise ValueError("Input cell IDs must be unique; automatic ID repair is not allowed.")
    output_dir = check_output_dir(args.output_dir, notebook) if args.output_dir is not None else None
    with isolated_runtime() as workspace:
        import nbformat
        nb = nbformat.reads(input_bytes.decode("utf-8"), as_version=4)
        nbformat.validate(nb)
        assessment = validate_assessment(nb)
        source_before = [(c.id, c.cell_type, c.source) for c in nb.cells]
        qa = nbformat.v4.new_code_cell(QA_SOURCE)
        nb.cells.append(qa)
        try:
            execute_notebook(nb, args.inprocess, workspace)
            coalesce_stream_outputs(nb)
            assert any("Teacher-only checks passed" in out.get("text", "") for out in qa.outputs)
        finally:
            # Never include the teacher answer/check cell in any published artifact.
            nb.cells.remove(qa)
        assert [(c.id, c.cell_type, c.source) for c in nb.cells] == source_before
        code_cells = [c for c in nb.cells if c.cell_type == "code"]
        assert all(c.execution_count is not None for c in code_cells)
        assert not any(o.output_type == "error" for c in code_cells for o in c.outputs)
        assert not assessment.outputs
        nbformat.validate(nb)
        html = render_html(nb)
        notebook_bytes = nbformat.writes(nb).encode("utf-8")
        html_bytes = html.encode("utf-8")
        artifact_bytes = {notebook.name: notebook_bytes, notebook.with_suffix(".html").name: html_bytes}
        if len(artifact_bytes) != 2 or "validation.json" in artifact_bytes:
            raise ValueError("Input notebook filename collides with an output artifact.")
        report = {
            "nbformat_validation": "passed",
            "top_to_bottom_execution": "passed",
            "execution_method": "fresh in-process IPython kernel" if args.inprocess else "fresh Jupyter kernel via nbclient",
            "input_sha256": input_sha256,
            "artifacts": {name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                          for name, data in artifact_bytes.items()},
            "artifact_mode": "new output directory" if output_dir else "memory only; stdout report",
            "output_directory": str(output_dir) if output_dir else None,
            "total_cells": len(nb.cells), "code_cells": len(code_cells), "executed_code_cells": len(code_cells),
            "error_outputs": 0, "assessment_answer_cell_filled": False,
            "assessment_template_and_saved_outputs": "checked before execution",
            "teacher_only_independent_checks": "passed; A/B worked-example and historical M/N finite controls; current two-contract answers are not checked, and student performance is not observed",
            "week04_group_cv_checks": "not performed here; known_train_4w and group-CV feasibility require separate review",
            "test_labels_and_scores_in_student_notebook": None,
            "test_labels_and_scores_inspection": "not performed; arbitrary input is not scanned for held-out test content",
            "teacher_qa_removed_from_artifacts": True,
            "actual_student_performance_observed": False,
            "class_timing_measured": False,
            "html_visual_inspection": "not performed by validator",
            "html_math_rendering": "nbconvert uses a remote MathJax CDN; availability not verified",
            "versions": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scikit-learn", "nbformat", "nbclient", "nbconvert", "ipykernel")},
            "limitations": ["finite synthetic examples only", "execution does not measure learning", "class timing is proposed",
                            "temporary cwd/cache directories are not OS isolation; arbitrary Python may access absolute paths",
                            "week04 extension known_train_4w and group-CV feasibility are not checked by this validator",
                            "self-contained trusted notebooks only; relative files are resolved in a temporary directory"],
        }
        report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        payloads = {**artifact_bytes, "validation.json": report_text.encode("utf-8")}
        if notebook.read_bytes() != input_bytes:
            raise RuntimeError("입력 파일이 실행 중 변경되었습니다. 오래된 결과는 쓰지 않습니다.")
        if output_dir is not None:
            write_new_outputs(output_dir, notebook, payloads)
    print(report_text, end="")
    return report


if __name__ == "__main__":
    main()
