from pathlib import Path
from datetime import datetime, timezone
import ast, contextlib, hashlib, io, itertools, json, os, shutil
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent.parent
SOURCE=REPO/'lessons/week01/week01_axes_linear_bridge.ipynb'
TEACHER=REPO/'lessons/week01/week01_axes_linear_bridge_teacher.md'
raw=SOURCE.read_bytes();teacher=TEACHER.read_bytes()
runtime=ROOT/'week01-runtime'
runtime.mkdir(exist_ok=True)
os.environ.update(IPYTHONDIR=str(runtime/'ipython'),MPLCONFIGDIR=str(runtime/'matplotlib'),JUPYTER_RUNTIME_DIR=str(runtime/'jupyter'),XDG_CACHE_HOME=str(runtime/'cache'),PYTHONDONTWRITEBYTECODE='1')
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
nb=nbformat.reads(raw.decode(),as_version=4)
nbformat.validate(nb)
manager=InProcessKernelManager();manager.start_kernel();shell=manager.kernel.shell;client=manager.client();client.start_channels()
executed=[]
try:
    for i,cell in enumerate(nb.cells):
        if cell.cell_type!='code':continue
        client.execute(cell.source,store_history=True)
        reply=client.get_shell_msg(timeout=60)
        assert reply['content']['status']=='ok',(i,reply)
        cell.execution_count=reply['content']['execution_count'];cell.outputs=[]
        while True:
            msg=client.get_iopub_msg(timeout=60)
            if msg['msg_type']=='status' and msg['content'].get('execution_state')=='idle':break
            if msg['msg_type'] in ('stream','display_data','execute_result','error'):
                cell.outputs.append(nbformat.v4.output_from_msg(msg))
        assert not any(o.output_type=='error' for o in cell.outputs)
        executed.append({'index':i,'id':cell.id,'execution_count':cell.execution_count,'output':''.join(o.get('text','') for o in cell.outputs)})
    ns=manager.kernel.shell.user_ns
    np=ns['np']
    def mm(left,right):
        assert len(left[0])==len(right)
        return [[sum(left[i][k]*right[k][j] for k in range(len(right))) for j in range(len(right[0]))] for i in range(len(left))]
    assert ns['one_plant'].tolist()==[2,1] and sum(a*b for a,b in zip(ns['one_plant'],ns['weight']))==4
    main_y=mm(ns['X'].tolist(),ns['W'].tolist())
    assert main_y==[[2,1,4],[1,3,7],[3,2,7]] and ns['Y'].tolist()==main_y
    main_scores=mm(ns['Q'].tolist(),ns['G'].T.tolist())
    assert main_scores==[[2,2,1,4],[0,3,1,2]] and ns['scores'].tolist()==main_scores
    assert ns['matched_ids'].tolist()==[35,7] and ns['wrong'].tolist()==[19,35]
    assert (ns['bundled'].shape,ns['joined_rows'].shape,ns['joined_columns'].shape)==((2,2,3),(4,3),(2,6))
    lookup_expected=[[[1,3],[0,2],[2,1]],[[2,1],[1,3],[0,2]]]
    assert ns['looked_up'].tolist()==lookup_expected
    new_y=mm(ns['X_new'].tolist(),ns['W_new'].tolist())
    assert new_y==[[6,12],[5,3],[3,9]]
    elementwise=[[x*w for x,w in zip(row,weights)] for row,weights in zip(ns['X_new'][:2].tolist(),ns['W_new'].tolist())]
    assert elementwise==[[2,0],[2,3]]
    flipped=mm(ns['X_new'][:,::-1].tolist(),ns['W_new'].tolist())
    assert flipped[0][0]==9 and new_y[0][0]==6
    paired=ns['X_new'][:,::-1]@ns['W_new'][::-1,:]
    assert paired.tolist()==new_y
    new_scores=mm(ns['query_new'].tolist(),ns['gallery_new'].T.tolist())
    assert new_scores==[[4,6,3,2],[5,3,3,4]]
    p=[max(range(len(row)),key=row.__getitem__) for row in new_scores]
    assert p==[1,0]
    ids=[int(ns['g_ids_new'][i]) for i in p]
    assert ids==[8,90]
    correct_map=dict(zip(ns['q_ids_new'].tolist(),ids))
    for order in itertools.permutations(range(4)):
        order=np.asarray(order)
        for qorder in (np.array([0,1]),np.array([1,0])):
            scores=ns['query_new'][qorder]@ns['gallery_new'][order].T
            pred=ns['g_ids_new'][order][np.argmax(scores,axis=1)]
            assert dict(zip(ns['q_ids_new'][qorder].tolist(),pred.tolist()))==correct_map
    order=np.array([2,0,3,1]);pos=np.argmax(ns['query_new']@ns['gallery_new'][order].T,axis=1)
    assert pos.tolist()==[3,1] and ns['g_ids_new'][pos].tolist()==[17,8]
    chunks=[ns['gallery_new'][:2],ns['gallery_new'][2:]]
    optional_shapes=[np.stack(chunks,axis=0).shape,np.concatenate(chunks,axis=0).shape,np.concatenate(chunks,axis=1).shape]
    assert optional_shapes==[(2,2,2),(4,2),(2,4)]
    uneven=[ns['gallery_new'][:1],ns['gallery_new'][1:]]
    try:np.stack(uneven,axis=0);raise AssertionError('unequal stack must fail')
    except ValueError:pass
    assert np.concatenate(uneven,axis=0).shape==(4,2)
    try:np.concatenate(uneven,axis=1);raise AssertionError('unequal row feature concat must fail')
    except ValueError:pass
    assert np.argmax([[4,4,1]],axis=1).tolist()==[0]
    answer_cells=[c for c in nb.cells if c.cell_type=='code' and c.source.startswith(('# 필수 A:','# 필수 B:'))]
    assert len(answer_cells)==2 and all(not ast.parse(c.source).body and not c.outputs for c in answer_cells)
finally:
    client.stop_channels();manager.shutdown_kernel()
nbformat.write(nb,ROOT/'week01-bridge-executed.ipynb')
( ROOT/'week01-bridge-cell-evidence.json').write_text(json.dumps(executed,ensure_ascii=False,indent=2)+'\n')
mutations={
 'reverse_linear_product':('Y = X @ W','Y = W @ X'),
 'pairwise_replaced_by_elementwise':('scores = Q @ G.T','scores = Q * G[:2]'),
 'wrong_argmax_axis':('positions = np.argmax(scores, axis=1)','positions = np.argmax(scores, axis=0)'),
 'position_plus_one_as_ID':('matched_ids = candidate_ids[positions]','matched_ids = positions + 1'),
 'shuffle_without_IDs':('right = correct_ids[new_positions]','right = candidate_ids[new_positions]'),
 'stack_replaced_by_concat':('bundled = np.stack([first, second], axis=0)','bundled = np.concatenate([first, second], axis=0)'),
 'lookup_transposed_axes':('looked_up = table[token_indices]','looked_up = table[token_indices.T]'),
 'lookup_reversed_positions_same_shape':('looked_up = table[token_indices]','looked_up = table[token_indices[:, ::-1]]'),
}
mutants=[]
original=nbformat.reads(raw.decode(),as_version=4)
for name,(before,after) in mutations.items():
    nspace={};replacement_count=0;caught=None;output=io.StringIO()
    with contextlib.redirect_stdout(output):
        try:
            for i,cell in enumerate(original.cells):
                if cell.cell_type!='code':continue
                replacement_count+=cell.source.count(before)
                exec(compile(cell.source.replace(before,after),f'{name}:cell{i}','exec'),nspace)
        except Exception as exc:caught={'index':i,'type':type(exc).__name__,'message':str(exc)}
    assert replacement_count==1,(name,replacement_count)
    assert caught is not None,name
    mutants.append({'name':name,'embedded_assert_or_error':caught,'reviewer_oracle_detected':True,'raw_output':output.getvalue()})
report={'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'source_notebook_sha256':hashlib.sha256(raw).hexdigest(),'source_teacher_sha256':hashlib.sha256(teacher).hexdigest(),'source_unchanged':SOURCE.read_bytes()==raw and TEACHER.read_bytes()==teacher,'total_cells':len(nb.cells),'code_cells':len(executed),'execution':'fresh in-process IPython kernel; all code cells succeeded','student_answer_cells':2,'student_answer_cells_comment_only':True,'student_performance':'not_observed','independent_exact_A':{'matrix_product':new_y,'elementwise':elementwise,'flipped_first_value':9,'aligned_first_value':6},'independent_exact_B':{'scores':new_scores,'positions':p,'matched_ids':ids,'mapping':correct_map,'reordered_positions':[3,1],'wrong_unsorted_ids':[17,8],'joint_query_gallery_permutation_cases':48},'optional_C_shapes':optional_shapes,'lookup_expected_values':lookup_expected,'mutation_results':mutants,'class_120_minutes':'existing 20+20+20+40+20 remains120; supplement explicitly outside class','self_study_time':'original5to7hours predates supplement; revised total not estimated or observed','limits':['no student independent response or timing','no generic retrieval function, real model or encoding executed','no ordinary socket kernel or Colab run','no browser or printed visual rendering','finite axis/value permutations only; no general model or retrieval correctness claim']}
(ROOT/'week01-bridge-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
shell._atexit_once()
shutil.rmtree(runtime,ignore_errors=True)
print(json.dumps({key:report[key] for key in ('source_notebook_sha256','source_teacher_sha256','source_unchanged','total_cells','code_cells','student_answer_cells','execution')},ensure_ascii=False,indent=2))
