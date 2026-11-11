"""Teacher-only execution and finite-case checks; contains independent exercise answers."""
from pathlib import Path
import ast
import argparse
import importlib.metadata
import json
import os
import shutil
import warnings

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager

ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "week02_prediction_evaluation.ipynb"
parser = argparse.ArgumentParser()
parser.add_argument("--inprocess", action="store_true")
args = parser.parse_args()
nb = nbformat.read(NOTEBOOK, as_version=4)
nbformat.validate(nb)
source_before = [(c.id, c.cell_type, c.source) for c in nb.cells]
code_cells = [c for c in nb.cells if c.cell_type == 'code']
assessment = next(c for c in code_cells if c.source.startswith('# 혼자 작성하는 공간'))
# Validate the distribution template before executing any student-supplied content.
assessment_answer_cell_filled = bool(ast.parse(assessment.source).body)
assert not assessment_answer_cell_filled, '배포용 독립 과제 칸에 학생 답안 코드가 들어 있습니다.'

# This appended check runs in the same fresh kernel after all student cells and is removed
# before saving; the independent exercise cell remains untouched and empty of answers.
qa = nbformat.v4.new_code_cell(r'''
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

# New, independent assessment data; answers are intentionally absent from student artifact.
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
''')
nb.cells.append(qa)
if not args.inprocess:
    NotebookClient(nb, timeout=180, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
else:
    manager = InProcessKernelManager()
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    old = Path.cwd()
    os.chdir(ROOT)
    try:
        for cell in nb.cells:
            if cell.cell_type != 'code':
                continue
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=180)
            if reply['content']['status'] != 'ok':
                raise RuntimeError(reply['content'])
            cell.execution_count = reply['content']['execution_count']
            cell.outputs = []
            while True:
                message = client.get_iopub_msg(timeout=180)
                kind = message['msg_type']
                if kind == 'status' and message['content'].get('execution_state') == 'idle':
                    break
                if kind in ('stream', 'display_data', 'execute_result', 'error'):
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
            if any(output.output_type == 'error' for output in cell.outputs):
                raise RuntimeError('Cell failed: ' + cell.id)
    finally:
        client.stop_channels()
        manager.shutdown_kernel()
        os.chdir(old)
assert any('Teacher-only checks passed' in out.get('text', '') for out in nb.cells[-1].outputs)
nb.cells.pop()
assert [(c.id,c.cell_type,c.source) for c in nb.cells] == source_before
code_cells = [c for c in nb.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs)
assert not assessment.outputs
nbformat.validate(nb)
nbformat.write(nb, NOTEBOOK)
html, _ = HTMLExporter().from_notebook_node(nb)
(ROOT / 'week02_prediction_evaluation.html').write_text(html, encoding='utf-8')
report = {
    'nbformat_validation': 'passed',
    'top_to_bottom_execution': 'passed',
    'execution_method': 'fresh in-process IPython kernel' if args.inprocess else 'fresh Jupyter kernel via nbclient',
    'total_cells': len(nb.cells), 'code_cells': len(code_cells), 'executed_code_cells': len(code_cells),
    'error_outputs': 0, 'assessment_answer_cell_filled': assessment_answer_cell_filled,
    'teacher_only_independent_checks': 'passed; exact cases documented in teacher notes',
    'test_labels_and_scores_in_student_notebook': False,
    'actual_student_performance_observed': False,
    'class_timing_measured': False,
    'html_visual_inspection': 'not performed: organization browser policy blocks local file URLs',
    'html_math_rendering': 'nbconvert uses a remote MathJax CDN; availability not verified',
    'versions': {p: importlib.metadata.version(p) for p in ('numpy','pandas','scikit-learn','nbformat','nbclient','nbconvert','ipykernel')},
    'limitations': ['finite synthetic examples only', 'execution does not measure learning', 'class timing is proposed'],
}
(ROOT / 'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
