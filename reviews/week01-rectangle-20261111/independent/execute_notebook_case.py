"""One configured case per new process and fresh in-process kernel. All writes scoped here."""
import argparse,ast,base64,hashlib,json,os,sys,tempfile,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('config');args=p.parse_args()
config_path=Path(args.config).resolve();config=json.loads(config_path.read_text())
assert config_path.is_relative_to(ROOT)
case=ROOT/'runs'/config['id'];case.mkdir(parents=True,exist_ok=False)
runtime=case/'runtime';runtime.mkdir()
for key in ['IPYTHONDIR','MPLCONFIGDIR','XDG_CACHE_HOME','JUPYTER_RUNTIME_DIR','TMPDIR','TMP','TEMP']:
    d=runtime/key.lower();d.mkdir();os.environ[key]=str(d)
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','LOKY_MAX_CPU_COUNT']:os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1';tempfile.tempdir=os.environ['TMPDIR']
os.chdir(case)
phase='initialization';events=[]
def permitted(path):
    return isinstance(path,(int,type(None))) or Path(os.fsdecode(path)).resolve().is_relative_to(ROOT)
def audit(event,values):
    if event=='open':
        path,mode,flags=values
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and not permitted(path):raise PermissionError('write outside independent scope: '+str(path))
        if not isinstance(path,(int,type(None))):
            q=Path(os.fsdecode(path)).resolve()
            if q.is_relative_to(ROOT) and q.suffix in ['.csv','.zip']:events.append({'phase':phase,'path':str(q.relative_to(ROOT)),'operation':'write' if writing else 'read'})
    if event in ['os.mkdir','os.remove','os.rmdir'] and not permitted(values[0]):raise PermissionError('mutation outside independent scope')
    if event in ['os.rename','os.replace'] and not all(permitted(x) for x in values[:2]):raise PermissionError('rename outside independent scope')
sys.addaudithook(audit)
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
source=Path(config['notebook']);raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha==config['sha256'],(sha,config['sha256'])
book=nbformat.reads(raw.decode(),as_version=4);nbformat.validate(book)
result={'id':config['id'],'candidate_sha':sha,'notebook':str(source),'config_sha':hashlib.sha256(config_path.read_bytes()).hexdigest(),'status':'running','scope':config['scope'],'execution':'new subprocess / fresh in-process kernel','cells':[],'student_achievement':'not_observed','learning_time':'not_observed'}
manager=InProcessKernelManager();manager.start_kernel();client=manager.client();client.start_channels();shell=manager.kernel.shell
started=time.monotonic()
def execute(text):
    client.execute(text,store_history=True);reply=client.get_shell_msg(timeout=120);outputs=[]
    while True:
        msg=client.get_iopub_msg(timeout=120)
        if msg['msg_type']=='status' and msg['content'].get('execution_state')=='idle':break
        if msg['msg_type'] in ['stream','display_data','execute_result','error']:outputs.append(dict(nbformat.v4.output_from_msg(msg)))
    return reply['content'],outputs

def projection(outputs):
    projected=[]
    for o in outputs:
        if o['output_type']=='stream':projected.append(['stream',o['name'],o['text']])
        elif o['output_type'] in ['display_data','execute_result']:projected.append(['display',o['data'].get('text/plain',''),sorted(o['data'])])
        else:projected.append(['error',o.get('ename'),o.get('evalue')])
    return projected
try:
    indices=config.get('cells',[i for i,c in enumerate(book.cells) if c.cell_type=='code'])
    for i in indices:
        cell=book.cells[i];assert cell.cell_type=='code'
        text=cell.source
        for change in config.get('replacements',[]):
            if change['cell']==i:
                assert text.count(change['old'])==1,(i,change['old'])
                text=text.replace(change['old'],change['new'])
        # Optional function-only extraction preserves actual FunctionDef text; worked demo is explicitly excluded.
        original_text=text
        if i in config.get('definitions_only_cells',[]):
            tree=ast.parse(text)
            definitions=[ast.get_source_segment(text,n) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
            assert definitions, 'no actual candidate definitions'
            text='\n\n'.join(definitions)
        phase='notebook_cell_'+str(i)
        shell.user_ns.setdefault('_review_candidate_cell_sources', {})[i] = text
        reply,outputs=execute(text)
        row={'index':i,'definitions_only':i in config.get('definitions_only_cells',[]),'full_source_sha':hashlib.sha256(original_text.encode()).hexdigest(),'source_sha':hashlib.sha256(text.encode()).hexdigest(),'blank_ast':not ast.parse(shell.input_transformer_manager.transform_cell(text)).body,'status':reply['status'],'outputs':outputs}
        if config.get('compare_stored'):
            row['stored_projection_match']=projection(outputs)==projection([dict(o) for o in cell.outputs])
            row['stored_png_present']=any('image/png' in o.get('data',{}) for o in cell.outputs)
            row['actual_png_present']=any('image/png' in o.get('data',{}) for o in outputs)
        result['cells'].append(row)
        if reply['status']!='ok':
            result.update(status='notebook_error',failed_cell=i,error={k:reply.get(k) for k in ['ename','evalue','traceback']});break
    else:
        result['status']='passed'
        if config.get('oracle'):
            phase='reviewer_oracle';oracle=Path(config['oracle']).resolve();assert oracle.is_relative_to(ROOT)
            reply,outputs=execute(oracle.read_text())
            result['oracle']={'sha256':hashlib.sha256(oracle.read_bytes()).hexdigest(),'status':reply['status'],'outputs':outputs}
            if reply['status']!='ok':result.update(status='oracle_error',error={k:reply.get(k) for k in ['ename','evalue','traceback']})
        if result['status']=='passed' and config.get('require_candidate_file'):
            name=config['require_candidate_file']
            actual_events=[e for e in events if e['phase'].startswith('notebook_cell_') and Path(e['path']).name==name]
            result['required_candidate_file_events']=actual_events
            assert {'read','write'}.issubset({e['operation'] for e in actual_events}), 'actual notebook physical file write/read missing: '+name
        if result['status']=='passed' and config.get('compare_stored'):
            assert all(c['stored_projection_match'] for c in result['cells']),'saved textual output/type differs'
        if config.get('save_png'):
            for cell in result['cells']:
                for j,o in enumerate(cell['outputs']):
                    if 'image/png' in o.get('data',{}):(case/f'cell-{cell["index"]}-{j}.png').write_bytes(base64.b64decode(o['data']['image/png']))
except Exception as e:
    result.update(status='harness_or_assertion_error',error={'type':type(e).__name__,'message':str(e)})
finally:
    client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
    result.update(elapsed_seconds=round(time.monotonic()-started,4),source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==sha,file_io_events=events)
    shutil.rmtree(runtime);result['runtime_removed']=not runtime.exists()
    (case/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['id','status','scope','source_unchanged','runtime_removed']},ensure_ascii=False))
sys.exit(0 if result['status']=='passed' else 1)
