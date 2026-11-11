"""One case per fresh subprocess and fresh in-process kernel; writes scoped here."""
import argparse,ast,base64,hashlib,json,os,shutil,sys,tempfile,time
from pathlib import Path
D=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('config');a=p.parse_args();cp=Path(a.config).resolve();assert cp.is_relative_to(D);cfg=json.loads(cp.read_text())
case=D/'runs'/cfg['id'];case.mkdir(parents=True,exist_ok=False);runtime=case/'runtime';runtime.mkdir()
for key in ['IPYTHONDIR','JUPYTER_CONFIG_DIR','JUPYTER_DATA_DIR','JUPYTER_RUNTIME_DIR','MPLCONFIGDIR','XDG_CACHE_HOME','TMPDIR','TMP','TEMP']:
 q=runtime/key.lower();q.mkdir();os.environ[key]=str(q)
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','LOKY_MAX_CPU_COUNT']:os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1';sys.dont_write_bytecode=True;tempfile.tempdir=os.environ['TMPDIR'];os.chdir(case)
def permitted(path):return isinstance(path,(int,type(None))) or Path(os.fsdecode(path)).resolve().is_relative_to(D)
def audit(event,values):
 if event=='open':
  path,mode,flags=values;writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
  if writing and not permitted(path):raise PermissionError('write outside independent scope: '+str(path))
 if event in ['os.mkdir','os.remove','os.rmdir'] and not permitted(values[0]):raise PermissionError('filesystem mutation outside review scope')
 if event in ['os.rename','os.replace'] and not all(permitted(v) for v in values[:2]):raise PermissionError('rename outside review scope')
sys.addaudithook(audit)
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
source=Path(cfg['notebook']);raw=source.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha==cfg['sha256'];nb=nbformat.reads(raw.decode(),as_version=4);nbformat.validate(nb)
result={'id':cfg['id'],'scope':cfg['scope'],'input_sha256':sha,'notebook':str(source),'config_sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'status':'running','execution':'new subprocess/fresh in-process kernel','cells':[],'student_performance_and_time':'not_observed'}
m=InProcessKernelManager();m.start_kernel();client=m.client();client.start_channels();shell=m.kernel.shell;started=time.monotonic()
def execute(code,history=True):
 client.execute(code,store_history=history);reply=client.get_shell_msg(timeout=180)['content'];outputs=[]
 while True:
  msg=client.get_iopub_msg(timeout=180)
  if msg['msg_type']=='status' and msg['content'].get('execution_state')=='idle':break
  if msg['msg_type'] in ['stream','display_data','execute_result','error']:outputs.append(dict(nbformat.v4.output_from_msg(msg)))
 return reply,outputs
def project(outputs):
 out=[]
 for o in outputs:
  if o['output_type']=='stream':
   if out and out[-1][0]=='stream' and out[-1][1]==o['name']:out[-1][2]+=o['text']
   else:out.append(['stream',o['name'],o['text']])
  elif o['output_type'] in ['display_data','execute_result']:out.append(['display',o['data'].get('text/plain',''),sorted(o['data'])])
  else:out.append(['error',o.get('ename'),o.get('evalue')])
 return out
try:
 setup,setupout=execute('%matplotlib inline',False);assert setup['status']=='ok';result['setup']='matplotlib inline; not student code'
 for i in cfg.get('cells',[i for i,c in enumerate(nb.cells) if c.cell_type=='code']):
  cell=nb.cells[i];assert cell.cell_type=='code';code=cell.source
  for change in cfg.get('replacements',[]):
   if change['cell']==i:assert code.count(change['old'])==1;code=code.replace(change['old'],change['new'])
  shell.user_ns.setdefault('_review_candidate_cell_sources',{})[i]=code
  reply,outputs=execute(code);row={'index':i,'source_sha256':hashlib.sha256(code.encode()).hexdigest(),'blank_ast':not ast.parse(shell.input_transformer_manager.transform_cell(code)).body,'status':reply['status'],'outputs':outputs}
  if cfg.get('compare_stored'):row.update(stored_projection_match=project(outputs)==project([dict(o) for o in cell.outputs]),stored_png_present=any('image/png' in o.get('data',{}) for o in cell.outputs),actual_png_present=any('image/png' in o.get('data',{}) for o in outputs))
  result['cells'].append(row)
  if reply['status']!='ok':result.update(status='notebook_error',failed_cell=i,error={k:reply.get(k) for k in ['ename','evalue','traceback']});break
 else:
  result['status']='passed'
  if cfg.get('oracle'):
   oracle=Path(cfg['oracle']).resolve();assert oracle.is_relative_to(D);reply,outputs=execute(oracle.read_text());result['oracle']={'sha256':hashlib.sha256(oracle.read_bytes()).hexdigest(),'status':reply['status'],'outputs':outputs}
   if reply['status']!='ok':result.update(status='oracle_error',error={k:reply.get(k) for k in ['ename','evalue','traceback']})
  if result['status']=='passed' and cfg.get('compare_stored'):assert all(x['stored_projection_match'] for x in result['cells']),'stored text/type mismatch'
  if cfg.get('save_png'):
   for row in result['cells']:
    for j,o in enumerate(row['outputs']):
     if 'image/png' in o.get('data',{}):(case/f'cell-{row["index"]}-{j}.png').write_bytes(base64.b64decode(o['data']['image/png']))
except Exception as e:result.update(status='harness_or_assertion_error',error={'type':type(e).__name__,'message':str(e)})
finally:
 client.stop_channels();m.shutdown_kernel();shell._atexit_once();result.update(elapsed_seconds=round(time.monotonic()-started,4),source_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==sha);shutil.rmtree(runtime);result['runtime_removed']=not runtime.exists();(case/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['id','status','source_unchanged','runtime_removed']},ensure_ascii=False));sys.exit(0 if result['status']=='passed' else 1)
