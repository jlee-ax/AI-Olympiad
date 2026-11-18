"""Exercise the two controlled notebook revisions in fresh in-process Jupyter kernels in separate Python processes.

Requires nbclient, ipykernel, nbformat and the course scientific Python packages.
The revisions and review-state fixtures are controlled tests, not lesson releases.
"""
from importlib.metadata import version
from multiprocessing import get_context
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
import test_material_revision as cases


def execute(directory, candidate, independent):
    with get_context('spawn').Pool(1) as worker:
        return worker.apply(execute_inprocess, (directory, candidate, independent))


def execute_inprocess(directory, candidate, independent):
    os.chdir(directory)
    notebook = nbformat.reads(json.dumps(candidate), as_version=4)
    nbformat.validate(notebook)
    code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code' and cell.source.strip()]
    for cell in code_cells:
        cell.outputs = []
        cell.execution_count = None
    notebook.cells.append(nbformat.v4.new_code_cell(independent))
    manager = InProcessKernelManager()
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    try:
        for cell in [*code_cells, notebook.cells[-1]]:
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=90)['content']
            if reply['status'] != 'ok':
                raise RuntimeError((cell.id, reply.get('ename'), reply.get('evalue')))
            cell.execution_count = reply['execution_count']
            while True:
                message = client.get_iopub_msg(timeout=90)
                kind = message['msg_type']
                if kind == 'status' and message['content'].get('execution_state') == 'idle':
                    break
                if kind in ('stream', 'display_data', 'execute_result', 'error'):
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
    finally:
        client.stop_channels()
        manager.shutdown_kernel()
    assert all(cell.execution_count is not None for cell in code_cells)
    outputs = notebook.cells[-1].outputs
    result = json.loads(''.join(out.text for out in outputs if out.output_type == 'stream').strip())
    return {'lesson_code_cells_executed': len(code_cells), 'new_input_cells_executed': 1,
            'kernel': 'InProcessKernelManager in a fresh process', 'kernel_errors': 0, 'new_input_results': result}


def main():
    with TemporaryDirectory() as temp:
        work = Path(temp)
        os.environ['MPLBACKEND'] = 'Agg'
        os.environ['MPLCONFIGDIR'] = str(work / 'mpl')
        case = cases.NotebookRoute()
        case.setUp()
        try:
            created = case.execute('apply')
            candidate = cases.quality.load(case.root / 'candidate.ipynb')
            assert candidate['cells'] == case.original['cells']
            one = execute(work, candidate, """import json
new = [observed_mean(x) for x in ([0, None, -5, 14], [None, np.nan], [], [0])]
assert new == [3.0, None, None, 0.0]
print(json.dumps(new))""")
            one.update(source='lessons/week01/week01_integrated.ipynb', candidate_sha256=created['candidate_sha256'],
                       diff=created['diff'], restored_cells_equal_original=True)
        finally:
            case.doCleanups()
        start, item, ops, _ = cases.week_two_fixture()
        two_book, diff = cases.edits.build(start, item, {'work_key': 'k', 'author': 'fixture-editor', 'operations': ops},
                                          {'9d29f53a', 'e7e69eb4', '31911a77'})
        two = execute(work, two_book, """import json
model = MinMaxScaler().fit([[3.0],[7.0]])
later = model.transform([[-1.0],[3.0],[11.0]]).ravel().tolist()
clipped = MinMaxScaler(clip=True).fit([[3.0],[7.0]]).transform([[11.0],[15.0]]).ravel().tolist()
assert later == [-1.0, 0.0, 2.0] and clipped == [1.0,1.0]
assert model.data_min_.tolist() == [3.0] and model.data_max_.tolist() == [7.0]
print(json.dumps({"later":later, "clipped":clipped}))""")
        two.update(source='lessons/week02/week02_temporal_preprocessing.ipynb', diff=diff, earlier_training_invariance_check_preserved=True)
        assert ''.join(cases.edits.notebook_index(two_book)['new-check']['source']).startswith(
            ''.join(cases.edits.notebook_index(start)['31911a77']['source']))
        reports = {}
        for label, name in [('course', 'runs/session.json'), ('bridge', 'bridge-cycle/candidate-state.json')]:
            state = cases.loop.load(ROOT / 'reviews/discovery-loop-20261111' / name)
            result = cases.loop.inspect(state, ROOT)
            reports[label] = {'status': result['status'], 'demands': len(result['demands']),
                              'open': len(result['queue']), 'revision_candidates': [
                                  row['demand_id'] for row in result['queue'] if row.get('revision')]}
        print(json.dumps({'packages': {k: version(k) for k in ('nbclient','ipykernel','numpy','pandas','scikit-learn')},
                          'week1': one, 'week2': two, 'historical_sessions_replayed': reports},
                         ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
