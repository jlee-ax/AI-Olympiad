#!/usr/bin/env python3
"""One case = one subprocess = one fresh in-process kernel. No ordinary socket kernel.

Call from the independent review directory. All generated files stay in its cases/ tree.
Optional --oracle is reviewer Python executed in the same live kernel AFTER notebook cells.
This worker never launches another kernel or invokes the author's validator.
"""
import argparse,ast,hashlib,json,os,sys,shutil,time
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--notebook',required=True)
parser.add_argument('--expected-sha',required=True)
parser.add_argument('--case',required=True)
parser.add_argument('--oracle')
parser.add_argument('--compare-stored',action='store_true')
args=parser.parse_args()
assert args.case and all(c.isalnum() or c in '_-' for c in args.case)
case=OUT/'cases'/args.case;case.mkdir(parents=True,exist_ok=False)
runtime=case/'runtime';runtime.mkdir()
for name in ['IPYTHONDIR','MPLCONFIGDIR','XDG_CACHE_HOME','JUPYTER_RUNTIME_DIR','TMPDIR','TMP','TEMP']:
    p=runtime/name.lower();p.mkdir();os.environ[name]=str(p)
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['LOKY_MAX_CPU_COUNT']='1';os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1'
import tempfile
tempfile.tempdir=os.environ['TMPDIR']
source=Path(args.notebook).resolve();raw=source.read_bytes();source_sha=hashlib.sha256(raw).hexdigest()
assert source_sha==args.expected_sha,'source SHA differs from author/variant binding'
(case/'source.ipynb').write_bytes(raw)
# Real CSV inputs can be read with the original relative layout; no original data is modified.
resource_dir=OUT.parents[2]/'lessons/week01/data'
if resource_dir.exists():
    (case/'data').mkdir()
    for p in resource_dir.glob('*.csv'):shutil.copyfile(p,case/'data'/p.name)
os.chdir(case)
# Enforce delegated write scope even if a lesson accidentally uses an absolute output path.
def permitted(path):
    if isinstance(path,(int,type(None))):return True
    return Path(os.fsdecode(path)).resolve().is_relative_to(OUT)
file_io_events=[]
def audit(event,values):
    if event=='open':
        path,mode,flags=values
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing and not permitted(path):raise PermissionError('review scope forbids write: '+str(path))
        if not isinstance(path,(int,type(None))):
            file_path=Path(os.fsdecode(path)).resolve()
            if file_path.suffix.lower() in ('.csv','.zip') and file_path.is_relative_to(case):
                file_io_events.append({'path':str(file_path.relative_to(case)),'operation':'write' if writing else 'read','physical_file_api':True})
    if event in ['os.mkdir','os.remove','os.rmdir'] and not permitted(values[0]):raise PermissionError('review scope forbids mutation: '+str(values[0]))
    if event in ['os.rename','os.replace'] and (not permitted(values[0]) or not permitted(values[1])):raise PermissionError('review scope forbids rename')
sys.addaudithook(audit)
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
book=nbformat.reads(raw.decode('utf-8'),as_version=4);nbformat.validate(book)
saved=nbformat.reads(raw.decode('utf-8'),as_version=4)
result={'case':args.case,'source':str(source),'source_sha256':source_sha,'worker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checked_at_utc':datetime.now(timezone.utc).isoformat(),'status':'running','execution':'single fresh InProcessKernelManager in a new subprocess','cells':len(book.cells),'executed_code_cells':[],'oracle':None,'student_performance':'not_observed','elapsed_seconds':None}
def output_projection(cell):
    return [('stream',o.name,o.text) if o.output_type=='stream' else ('display',o.data.get('text/plain',''),sorted(o.data)) if o.output_type in ('display_data','execute_result') else ('error',str(o)) for o in cell.outputs]
manager=InProcessKernelManager();manager.start_kernel();shell=manager.kernel.shell;client=manager.client();client.start_channels()
started=time.monotonic()
def execute(text):
    client.execute(text,store_history=True);reply=client.get_shell_msg(timeout=120);outputs=[]
    while True:
        m=client.get_iopub_msg(timeout=120)
        if m['msg_type']=='status' and m['content'].get('execution_state')=='idle':break
        if m['msg_type'] in ['stream','display_data','execute_result','error']:outputs.append(nbformat.v4.output_from_msg(m))
    return reply,outputs
try:
    for i,cell in enumerate(book.cells):
        if cell.cell_type!='code':continue
        reply,cell.outputs=execute(cell.source);cell.execution_count=reply['content']['execution_count']
        result['executed_code_cells'].append(i)
        if reply['content']['status']!='ok':
            result.update(status='notebook_error',failed_cell=i,error={key:reply['content'].get(key) for key in ['ename','evalue','traceback']});break
        if args.compare_stored and output_projection(cell)!=output_projection(saved.cells[i]):
            result.update(status='stored_output_mismatch',failed_cell=i,stored=output_projection(saved.cells[i]),actual=output_projection(cell));break
    else:
        result['status']='passed'
        if args.oracle:
            oracle=Path(args.oracle).resolve();oracle_source=oracle.read_text()
            reply,outputs=execute(oracle_source)
            result['oracle']={'source':str(oracle),'sha256':hashlib.sha256(oracle_source.encode()).hexdigest(),'status':reply['content']['status'],'outputs':[dict(o) for o in outputs]}
            if reply['content']['status']!='ok':result.update(status='oracle_error',error={key:reply['content'].get(key) for key in ['ename','evalue','traceback']})
except Exception as error:
    result.update(status='harness_error',error={'type':type(error).__name__,'message':str(error)})
finally:
    client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
    result['elapsed_seconds']=round(time.monotonic()-started,4)
    nbformat.write(book,case/'executed.ipynb')
    result['source_unchanged']=hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
    result['file_io_events']=file_io_events
    shutil.rmtree(runtime)
    result['runtime_removed']=not runtime.exists()
    (case/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['case','status','source_sha256','executed_code_cells','source_unchanged','runtime_removed']},ensure_ascii=False))
sys.exit(0 if result['status']=='passed' else 1)
