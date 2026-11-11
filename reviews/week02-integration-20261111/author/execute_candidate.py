from pathlib import Path
import argparse, ast, os, sys
p=argparse.ArgumentParser()
p.add_argument('source',type=Path);p.add_argument('out',type=Path);p.add_argument('html',type=Path);p.add_argument('runtime',type=Path)
a=p.parse_args()
a.runtime.mkdir(parents=True,exist_ok=True)
for key,name in [('IPYTHONDIR','ipython'),('MPLCONFIGDIR','matplotlib'),('JUPYTER_RUNTIME_DIR','jupyter'),('XDG_CACHE_HOME','cache')]:
 d=a.runtime/name;d.mkdir(exist_ok=True);os.environ[key]=str(d.resolve())
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['OPENBLAS_NUM_THREADS']='1'
import nbformat
from nbconvert import HTMLExporter
from ipykernel.inprocess.manager import InProcessKernelManager
nb=nbformat.read(a.source,as_version=4);nbformat.validate(nb)
before=[(c.id,c.cell_type,c.source) for c in nb.cells]
km=InProcessKernelManager();km.start_kernel();kc=km.client();kc.start_channels()

def execute(source):
 kc.execute(source,store_history=True)
 reply=kc.get_shell_msg(timeout=180)
 if reply['content']['status']!='ok': raise RuntimeError(str(reply['content']))
 outputs=[]
 while True:
  msg=kc.get_iopub_msg(timeout=180);kind=msg['msg_type']
  if kind=='status' and msg['content'].get('execution_state')=='idle': break
  if kind in ('stream','display_data','execute_result','error'):outputs.append(nbformat.v4.output_from_msg(msg))
 if any(o.output_type=='error' for o in outputs): raise RuntimeError(str(outputs))
 return reply['content']['execution_count'],outputs
try:
 execute('%matplotlib inline')
 for i,c in enumerate(nb.cells):
  if c.cell_type!='code':continue
  if 'independent-exercise' in c.metadata.get('tags',[]):
   assert not ast.parse(c.source).body
   c.execution_count=None;c.outputs=[];continue
  c.execution_count,c.outputs=execute(c.source)
  if c.id=='4cfbd70e': assert not ast.parse(c.source).body and not c.outputs
finally:
 kc.stop_channels();km.shutdown_kernel()
assert before==[(c.id,c.cell_type,c.source) for c in nb.cells]
nbformat.validate(nb)
with a.out.open('x',encoding='utf-8') as f:nbformat.write(nb,f)
html,_=HTMLExporter().from_notebook_node(nb)
with a.html.open('x',encoding='utf-8') as f:f.write(html)
print('executed',a.source,'to',a.out,'and',a.html,'cells',len(nb.cells),'code',sum(c.cell_type=='code' for c in nb.cells))
