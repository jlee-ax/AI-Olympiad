"""Check the advertised Week 1 navigation with three isolated kernels.

Only supplied setup/example/input cells and explicit reviewer fixtures run.
Student answer cells remain blank; the fixture is not student performance.
"""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import os
import subprocess
import sys
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path.cwd())
parser.add_argument('--candidate-sha')
parser.add_argument('--scratch',type=Path)
parser.add_argument('--worker',type=Path)
args=parser.parse_args()

if args.worker:
    from ipykernel.inprocess.manager import InProcessKernelManager
    from IPython.utils.capture import capture_output
    notebook=json.loads(args.worker.read_text(encoding='utf-8'))
    cells={c['id']:c for c in notebook['cells']}
    manager=InProcessKernelManager()
    with capture_output():
        manager.start_kernel()
    shell=manager.kernel.shell
    try:
        for raw in sys.stdin:
            try:
                req=json.loads(raw)
                if req.get('stop'):
                    print(json.dumps({'status':'stopped'}),flush=True)
                    break
                for cell_id in req.get('cells',[]):
                    cell=cells[cell_id]
                    assert cell['cell_type']=='code'
                    src=cell['source']
                    src=src if isinstance(src,str) else ''.join(src)
                    assert any(line.strip() and not line.lstrip().startswith('#') for line in src.splitlines()), 'do not execute student answer cells'
                    with capture_output():
                        res=shell.run_cell(src,store_history=False)
                    if not res.success:
                        raise RuntimeError(f'{cell_id}: {res.error_before_exec or res.error_in_exec}')
                code=req.get('reviewer_fixture')
                if code:
                    with capture_output():
                        res=shell.run_cell(code,store_history=False)
                    if not res.success:
                        raise RuntimeError('reviewer fixture: '+str(res.error_before_exec or res.error_in_exec))
                val={}
                for key,expr in req.get('inspect',{}).items():
                    value=eval(expr,shell.user_ns)
                    if hasattr(value,'tolist'):value=value.tolist()
                    val[key]=value
                print(json.dumps({'status':'ok','observed':val},ensure_ascii=False),flush=True)
            except BaseException as e:
                print(json.dumps({'status':'error','error':str(e)},ensure_ascii=False),flush=True)
    finally:
        with capture_output():
            manager.shutdown_kernel()
    raise SystemExit(0)

if not args.candidate_sha or not args.scratch:
    parser.error('--candidate-sha and --scratch are required')
ROOT=args.root.resolve()
lesson=ROOT/'lessons/week01'
paths={'integrated':lesson/'week01_integrated.ipynb',
       'tables':lesson/'week01_python_tables.ipynb',
       'bridge':lesson/'week01_axes_linear_bridge.ipynb'}
hashes={k:sha256(v.read_bytes()).hexdigest() for k,v in paths.items()}
assert hashes['integrated']==args.candidate_sha
baseline_table='b239479f4572a01f0e2848043078b45f3cda6f60e02369da091a4f4a63651880'
assert hashes['tables']==baseline_table
tables=json.loads(paths['tables'].read_text())
assert [(i,tables['cells'][i]['id']) for i in (3,27,54)]==[(3,'d2be9ce3'),(27,'eb304b96'),(54,'5c37fc90')]
processes=[]

def send(p,request):
    p.stdin.write(json.dumps(request,ensure_ascii=False)+'\n');p.stdin.flush()
    line=p.stdout.readline()
    if not line:raise RuntimeError('worker exited: '+p.stderr.read())
    result=json.loads(line)
    if result['status']!='ok':raise RuntimeError(result)
    return result['observed']

args.scratch.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory(prefix='week01-route-',dir=args.scratch) as tmp:
    try:
        for name,path in paths.items():
            env=os.environ.copy()
            for key in ('JUPYTER_RUNTIME_DIR','JUPYTER_CONFIG_DIR','JUPYTER_DATA_DIR','IPYTHONDIR','MPLCONFIGDIR','XDG_CACHE_HOME','TMPDIR'):
                folder=Path(tmp)/name/key;folder.mkdir(parents=True,exist_ok=True);env[key]=str(folder)
            env['PYTHONDONTWRITEBYTECODE']='1'
            p=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(path)],cwd=lesson,
                               env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
            processes.append(p)
        integrated,main,bridge=processes
        initial=send(integrated,{'cells':['484f22ba','9462ed76'],
                                'inspect':{'has_T':"'T' in globals()",'columns':"exercise_validation.columns.tolist()",
                                           'plants':"plants.columns.tolist()"}})
        assert initial['has_T'] is False and initial['columns']==['unit','signal','panel'] and 'light_h' in initial['plants']
        prepared=send(main,{'cells':['d2be9ce3','eb304b96','5c37fc90'],
                            'inspect':{'plants':"plants.columns.tolist()",'new_shape':"list(new_plants.shape)",'B_shape':"list(B.shape)"}})
        assert 'sunlight_hours' in prepared['plants'] and 'light_h' not in prepared['plants']
        assert prepared['new_shape']==[4,5] and prepared['B_shape']==[2,3]
        # T is a reviewer fixture because the corresponding main answer is a blank student cell.
        main_t=send(main,{'reviewer_fixture':'T = np.array([[1,4,7],[2,5,8]])\nreviewer_sentinel = "main kernel"',
                          'inspect':{'T':'T.tolist()'}})
        assert main_t['T']==[[1,4,7],[2,5,8]]
        isolation=send(integrated,{'inspect':{'has_T':"'T' in globals()",'has_sentinel':"'reviewer_sentinel' in globals()"}})
        assert isolation=={'has_T':False,'has_sentinel':False}
        returned=send(integrated,{'cells':['rectangle-independent-input'],
                                  'inspect':{'T':'T.tolist()','has_sentinel':"'reviewer_sentinel' in globals()"}})
        assert returned=={'T':[[1,4,7],[2,5,8]],'has_sentinel':False}
        bridge_state=send(bridge,{'cells':['ba428b91','3950021e','retrieval-norm-code','d81386f3','sequence-mean-code','ec433d3b','07c93362'],
                                  'inspect':{'has_T':"'T' in globals()",'has_train':"'exercise_train' in globals()",
                                             'X_new':"list(X_new.shape)",'W_new':"list(W_new.shape)",
                                             'token_shape':"list(query_tokens_new.shape)"}})
        assert bridge_state=={'has_T':False,'has_train':False,'X_new':[3,2],'W_new':[2,2],'token_shape':[2,4]}
        edge_code='''
real = lookup_and_masked_mean(token_table_new, np.array([[4, 0]]))
assert real[3].tolist() == [[1]] and real[4].tolist() == [[0.0, 0.0]]
for ids in [np.array([[0,0]]),np.array([[-1]]),np.array([[5]]),np.array([[True]],dtype=object)]:
    try: lookup_and_masked_mean(token_table_new, ids)
    except ValueError: pass
    else: raise AssertionError("invalid token IDs accepted")
for bad in [np.array([[0.0,0.0]]),np.array([[float("nan"),1.0]])]:
    try: normalize_rows(bad)
    except ValueError: pass
    else: raise AssertionError("invalid vector accepted")
'''
        send(bridge,{'reviewer_fixture':edge_code})
        after=send(integrated,{'inspect':{'T':'T.tolist()','has_sentinel':"'reviewer_sentinel' in globals()",
                                          'training_IDs':"exercise_train.unit.tolist()"}})
        assert after['T']==[[1,4,7],[2,5,8]] and not after['has_sentinel']
        assert after['training_IDs']==['T1','T2','T3','T4','T5']
    finally:
        for p in processes:
            if p.poll() is None:
                try:
                    p.stdin.write(json.dumps({'stop':True})+'\n');p.stdin.flush();p.wait(timeout=10)
                except Exception:
                    p.terminate();p.wait(timeout=10)
assert hashes=={k:sha256(v.read_bytes()).hexdigest() for k,v in paths.items()}
print(json.dumps({'status':'passed','kernels':'three separate processes with InProcessKernelManager',
                  'source_sha256':hashes,'main_preparation_ids':['d2be9ce3','eb304b96','5c37fc90'],
                  'integrated_initial':initial,'main_prepared':prepared,'integrated_before_return':isolation,
                  'integrated_after_recreate_T':returned,'bridge_inputs':bridge_state,'integrated_return':after,
                  'edge_cases':'valid zero token, all PAD, negative/out-of-range/bool IDs, zero/NaN vectors passed',
                  'reviewer_fixture':'T and sentinel added only to main test kernel; no student answer was executed',
                  'limits':'Not a standard socket Jupyter server, HTML browser test, or observation of a learner.'},ensure_ascii=False,indent=2))
