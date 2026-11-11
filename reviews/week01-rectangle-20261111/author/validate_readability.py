#!/usr/bin/env python3
"""Validate the rectangle lesson and its teacher reference in fresh processes."""
import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / 'lessons/week01'
MAIN = LESSON / 'week01_integrated.ipynb'
ORIGINAL = LESSON / 'week01_python_tables.ipynb'
BRIDGE = LESSON / 'week01_axes_linear_bridge.ipynb'
TEACHER = LESSON / 'week01_integrated_teacher.md'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run_worker(kind):
    import nbformat
    import numpy as np
    from ipykernel.inprocess.manager import InProcessKernelManager
    from nbconvert import HTMLExporter
    path = MAIN if kind in ('main', 'main-route') else (ORIGINAL if kind == 'original-A' else BRIDGE)
    book = nbformat.read(path, as_version=4)
    nbformat.validate(book)
    saved = nbformat.read(path, as_version=4)
    if kind == 'main':
        rendered_html = MAIN.with_suffix('.html').read_text(encoding='utf-8')
        assert HTMLExporter().from_notebook_node(book)[0] == rendered_html
        assert '<strong>잘라낸 부분(crop)</strong>' in rendered_html
        assert '**잘라낸 부분(crop)**' not in rendered_html
        indices = [i for i, c in enumerate(book.cells) if c.cell_type == 'code']
    elif kind == 'main-route':
        indices = [41, 42]
    elif kind == 'original-A':
        indices = [3, 27, 54, 59, 61, 64, 66]
    else:
        indices = [2, 14, 16, 22, 24, 27, 29, 31, 33]
    def payloads(cell):
        items = []
        for output in cell.outputs:
            if output.output_type == 'stream':
                items.append(('stream', output.name, output.text))
            elif output.output_type in ('display_data', 'execute_result'):
                items.append((output.output_type, dict(output.data), dict(output.metadata)))
            else:
                items.append((output.output_type, dict(output)))
        return items
    manager = InProcessKernelManager(); manager.start_kernel()
    shell = manager.kernel.shell; client = manager.client(); client.start_channels()
    try:
        for index in indices:
            cell = book.cells[index]
            assert cell.cell_type == 'code', (kind, index)
            client.execute(cell.source, store_history=True)
            reply = client.get_shell_msg(timeout=120)
            if reply['content']['status'] != 'ok':
                raise AssertionError(f'{kind} cell {index}: {reply["content"]}')
            cell.execution_count = reply['content']['execution_count']
            cell.outputs = []
            while True:
                msg = client.get_iopub_msg(timeout=120)
                if msg['msg_type'] == 'status' and msg['content'].get('execution_state') == 'idle': break
                if msg['msg_type'] in ('stream', 'display_data', 'execute_result', 'error'):
                    cell.outputs.append(nbformat.v4.output_from_msg(msg))
            assert not any(x.output_type == 'error' for x in cell.outputs)
            if kind == 'main':
                assert payloads(cell) == payloads(saved.cells[index]), ('saved output differs', index)
        ns = shell.user_ns
        checks = []
        if kind == 'main':
            assert len(book.cells) == 44 and len(indices) == 21
            assert book.cells[17].id == 'rectangle-worked-text'
            assert book.cells[18].id == 'rectangle-worked-code'
            assert book.cells[40].id == 'rectangle-independent-text'
            assert book.cells[41].id == 'rectangle-independent-input'
            assert book.cells[42].id == 'rectangle-independent-answer'
            assert not ast.parse(saved.cells[42].source).body and saved.cells[42].outputs == []
            assert not ast.parse(saved.cells[38].source).body and saved.cells[38].outputs == []
            assert ns['rectangle_grid'].shape == (8,12)
            assert ns['crop'].tolist() == [[0,29,30],[40,41,42]]
            assert ns['region_mask'].shape == ns['kept_grid'].shape == (8,12)
            mask = np.zeros((8,12), dtype=bool); mask[2:4,4:7] = True
            assert np.array_equal(ns['region_mask'], mask) and int(mask.sum()) == 6
            assert np.array_equal(ns['kept_grid'], np.where(mask, ns['rectangle_grid'], 0))
            assert np.count_nonzero(ns['crop']) == 5 and mask[2,4]
            assert np.array_equal(ns['rectangle_grid'], ns['rectangle_before'])
            assert ns['area'] == ns['max_cells'] == 6
            assert np.array_equal(ns['x_train'], [[0,0],[2,1],[2,2],[4,3]])
            assert ns['predictions'].tolist() == [0,1] and ns['validation_accuracy'] == .5
            assert not ns['result_path'].exists()
            checks += ['top_to_bottom_saved_outputs_and_html',
                       'actual_worked_area_location_original_zero_and_no_mutation',
                       'previous_actual_model_and_physical_csv',
                       'two_student_answer_cells_empty']
            text = '\n'.join(c.source for c in book.cells if c.cell_type == 'markdown')
            for marker in ('별도 커널', '최대 6.25%', 'JSONL', '4칸', 'Python 정수',
                           '다른 자료형 입력에 대한 처리는 요구하지 않습니다',
                           '슬라이스하기 전에', 'ValueError', 'reshape·전치·열별·행별 브로드캐스팅',
                           '과제 B:', '과제 C:', '과제 D·E:', '필수 A와 B'):
                assert marker in text, marker
            assert '120분' not in text and '5~7시간' not in text
            assert '[[0,7],[10,11]]' not in text
            checks.append('contract_and_existing_exercise_routing_in_student_source')

            teacher = TEACHER.read_text(encoding='utf-8')
            blocks = re.findall(r'```python\n(.*?)\n```', teacher, flags=re.S)
            matched = [x for x in blocks if 'def rectangle_region' in x]
            assert len(matched) == 1
            tree = ast.parse(matched[0]); defs = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'rectangle_region']
            assert len(defs) == 1
            isolated = {'np': np}; exec(compile(ast.Module(body=defs, type_ignores=[]), '<teacher-reference>', 'exec'), isolated)
            f = isolated['rectangle_region']
            T = np.array([[1,4,7],[2,5,8]]); before = T.copy()
            crop1, mask1, kept1 = f(T, ((0,1),(2,3)), 4)
            crop2, mask2, kept2 = f(T, ((0,0),(2,2)), 4)
            assert crop1.tolist() == [[4,7],[5,8]] and crop2.tolist() == [[1,4],[2,5]]
            assert mask1.tolist() == [[False,True,True],[False,True,True]]
            assert mask2.tolist() == [[True,True,False],[True,True,False]]
            assert kept1.tolist() == [[0,4,7],[0,5,8]] and kept2.tolist() == [[1,4,0],[2,5,0]]
            assert mask1.sum() == mask2.sum() == 4 and mask1.shape == mask2.shape == (2,3)
            assert np.array_equal(T,before) and not np.array_equal(mask1,mask2)
            assert f(T, ((1,2),(2,3)), 4)[0].tolist() == [[8]]
            changed = crop1.copy(); changed[0,0] = -500
            assert np.array_equal(T,before)
            assert T[1:3,1:3].tolist() == [[5,8]]
            R = np.array([[1,2,3,4],[5,0,7,8],[9,10,11,12]])
            before_R = R.copy(); rc, rm, ro = f(R, ((1,1),(3,3)), 4)
            assert rc.tolist() == [[0,7],[10,11]] and rm.shape == ro.shape == (3,4)
            assert rm.tolist() == [[False,False,False,False],[False,True,True,False],[False,True,True,False]]
            assert ro.tolist() == [[0,0,0,0],[0,0,7,0],[0,10,11,0]]
            assert int(rm.sum()) == 4 and np.count_nonzero(rc) == 3
            assert np.array_equal(R,before_R)
            class Spy(np.ndarray):
                def __new__(cls, value):
                    result = np.asarray(value).view(cls); result.touched = False; return result
                def __array_finalize__(self, original):
                    if original is not None: self.touched = getattr(original, 'touched', False)
                def __getitem__(self, key):
                    self.touched = True
                    return super().__getitem__(key)
            for bounds in [((0,0),(2,3)), ((1,1),(3,3)), ((1,1),(1,2)),
                           ((-1,0),(1,1)), ((1,1),(0,2))]:
                probe = Spy(T)
                try:
                    f(probe, bounds, 4)
                except ValueError: pass
                else: raise AssertionError(('bad box accepted',bounds))
                assert not probe.touched, ('sliced before validation',bounds)
            assert '44셀·코드 21셀' in teacher and '셀 41' in teacher and '셀 42' in teacher and '셀 38' in teacher
            checks += ['actual_teacher_reference_two_T_regions_edge_and_invalids',
                       'teacher_reference_new_3x4_zero_retention_and_no_mutation',
                       'teacher_reference_bad_inputs_rejected_before_slice']
        elif kind == 'main-route':
            assert saved.cells[41].id == 'rectangle-independent-input'
            assert saved.cells[42].id == 'rectangle-independent-answer'
            assert np.array_equal(ns['T'], [[1,4,7],[2,5,8]])
            assert not ast.parse(saved.cells[42].source).body and not saved.cells[42].outputs
            checks.append('fresh_integrated_kernel_recreates_T_and_keeps_student_answer_blank')
        elif kind == 'original-A':
            assert len(saved.cells) == 89
            assert np.array_equal(ns['B'], [[1,5,9],[3,7,11]])
            assert np.array_equal(ns['two_by_three'], [[2,4,6],[8,10,12]])
            assert np.array_equal(ns['grid'], [[2,4],[6,8],[10,12]])
            assert not ast.parse(saved.cells[61].source).body and not ast.parse(saved.cells[66].source).body
            assert 'T' not in ns
            text = '\n'.join(c.source for c in saved.cells if c.cell_type == 'markdown')
            for marker in ('reshape', 'transpose', '보정', '오른쪽 축', '과제 B', '과제 C', '과제 D', '과제 E'):
                assert marker in text, marker
            checks.append('separate_original_A_preparation_and_provided_cells_student_blanks')
        else:
            assert len(saved.cells) == 35
            assert not ast.parse(saved.cells[29].source).body and not ast.parse(saved.cells[33].source).body
            assert 'query_new' not in ns
            pool = ns['lookup_and_masked_mean']; scores = ns['cosine_scores']
            _,_,sums,counts,q = pool(ns['token_table_new'],ns['query_tokens_new'])
            assert sums.tolist() == [[6,9],[6,4]] and counts.tolist() == [[3],[2]]
            assert np.allclose(q,[[2,3],[3,2]])
            assert ns['g_ids_new'][np.argmax(scores(q,ns['gallery_new']),axis=1)].tolist() == [53,90]
            checks.append('separate_bridge_A_B_preparation_and_actual_helper')
        result = {'kind':kind,'status':'passed','cells':len(book.cells),
                  'executed_code_cells_zero_based':indices,'checks':checks}
    finally:
        client.stop_channels(); manager.shutdown_kernel(); shell._atexit_once()
    print(json.dumps(result,ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',choices=['main','main-route','original-A','bridge-route'])
    parser.add_argument('--protected-worktree',type=Path)
    parser.add_argument('--write',type=Path,help='new JSON path; existing files refused')
    args=parser.parse_args()
    if args.worker:
        run_worker(args.worker); return
    paths=[MAIN,MAIN.with_suffix('.html'),TEACHER,ORIGINAL,ORIGINAL.with_suffix('.html'),
           BRIDGE,BRIDGE.with_suffix('.html'),LESSON/'week01_axes_linear_bridge_teacher.md',
           LESSON/'week01_problem_pipeline.ipynb',LESSON/'data/week1_plants.csv',LESSON/'data/week1_plants_new.csv']
    protected=[]; protected_readme=None
    if args.protected_worktree is not None:
        base=args.protected_worktree.resolve()/'lessons/week01'
        protected=[base/'week01_python_tables.ipynb',base/'week01_python_tables.html',
                   base/'lesson-manifest.json',base/'teacher-notes.txt',base/'validation.json',
                   base/'data/week1_plants.csv',base/'data/week1_plants_new.csv']
        if any(not p.is_file() for p in protected):parser.error('protected worktree comparison file missing')
        paths.extend(protected); protected_readme=base/'README.md'
    before={str(path):sha(path) for path in paths}
    readme_before=protected_readme.exists() if protected_readme else None
    results=[]
    for kind in ['main','main-route','original-A','bridge-route']:
        with tempfile.TemporaryDirectory(prefix='week01-rectangle-qa-') as tmp:
            env={**os.environ,'IPYTHONDIR':tmp,'MPLCONFIGDIR':tmp,'PYTHONDONTWRITEBYTECODE':'1',
                 'LOKY_MAX_CPU_COUNT':'1','PYDEVD_DISABLE_FILE_VALIDATION':'1'}
            proc=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',kind],
                                cwd=ROOT,text=True,capture_output=True,env=env,timeout=180)
            if proc.returncode:raise RuntimeError(f'{kind} failed: {proc.stdout}\n{proc.stderr}')
            results.append(json.loads(proc.stdout))
    assert before=={str(path):sha(path) for path in paths}
    if protected_readme is not None:assert readme_before==protected_readme.exists()
    report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),
            'method':'four separate processes, each a fresh in-process kernel',
            'results':results,'source_sha256_before_and_after':before,
            'protected_worktree':{'status':'checked' if protected else 'not_checked',
                                  'files_compared':len(protected),'readme_exists':readme_before},
            'validator_sha256':sha(Path(__file__)),
            'limitations':['teacher reference and provided blank-cell execution are not student performance',
                           'finite synthetic inputs do not prove all numerical or type behavior',
                           'ordinary Jupyter/Colab socket kernels and full browser rendering not tested',
                           'actual learner time, help, attainment, later weeks and international evaluation unobserved']}
    if args.write:
        with args.write.open('x',encoding='utf-8') as stream:
            stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
