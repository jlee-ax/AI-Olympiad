#!/usr/bin/env python3
"""Execute a supplied notebook in a fresh in-process kernel; preserve the source."""
import base64, hashlib, json, os, sys
from pathlib import Path
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager
from nbconvert import HTMLExporter

source=Path(sys.argv[1]).resolve()
outdir=Path(sys.argv[2]).resolve()
name=sys.argv[3]
outdir.mkdir(parents=True,exist_ok=True)
raw=source.read_bytes(); source_sha=hashlib.sha256(raw).hexdigest()
book=nbformat.reads(raw.decode('utf-8'),as_version=4);nbformat.validate(book)
projection=lambda b:[{k:c.get(k) for k in ('id','cell_type','source','attachments')} for c in b.cells]
original=projection(book)
manager=InProcessKernelManager();manager.start_kernel();client=manager.client();client.start_channels()
dispatch=client._dispatch_to_kernel

def dispatch_with_stream_parent(msg):
    # InProcessKernel redirects streams after the kernel's set_parent call.
    # Associate both streams with the exact request before it is dispatched.
    manager.kernel.stdout.set_parent(msg)
    manager.kernel.stderr.set_parent(msg)
    return dispatch(msg)
client._dispatch_to_kernel=dispatch_with_stream_parent

def run(code, store_history=True):
    msgid=client.execute(code,store_history=store_history,allow_stdin=False)
    reply=client.get_shell_msg(timeout=120)
    if reply['parent_header']['msg_id']!=msgid:raise RuntimeError('unexpected shell reply')
    outputs=[]
    while True:
        msg=client.get_iopub_msg(timeout=120);kind=msg['msg_type'];parent=msg.get('parent_header',{}).get('msg_id')
        if kind in ('stream','display_data','execute_result','error') and parent!=msgid:
            raise RuntimeError('output parent does not match current cell: '+str((kind,parent,msgid)))
        if parent!=msgid:continue
        if kind in ('stream','display_data','execute_result','error'):outputs.append(nbformat.v4.output_from_msg(msg))
        if kind=='status' and msg['content'].get('execution_state')=='idle':break
    if reply['content']['status']!='ok':raise RuntimeError(str(reply['content']))
    if any(o.output_type=='error' for o in outputs):raise RuntimeError('error output')
    return reply['content']['execution_count'],outputs

previous=Path.cwd();os.chdir(source.parent)
try:
    _,smoke=run('print("capture-check-2d44c")',False)
    assert any(o.output_type=='stream' and 'capture-check-2d44c' in o.text for o in smoke),'stdout capture failed'
    executed=[]
    for index,cell in enumerate(book.cells):
        if cell.cell_type!='code':continue
        count,outputs=run(cell.source)
        cell.execution_count=count;cell.outputs=outputs
        executed.append({'index':index,'id':cell.id})
    assert projection(book)==original
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_sha
    assert not [o for c in book.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
    nbformat.validate(book)
    saved=outdir/(name+'-executed.ipynb');nbformat.write(book,saved)
    images=[]
    for i,c in enumerate(book.cells):
        for j,o in enumerate(c.get('outputs',[])):
            encoded=o.get('data',{}).get('image/png')
            if encoded:
                p=outdir/(name+f'-cell-{i}-{j}.png');p.write_bytes(base64.b64decode(encoded));images.append(str(p))
    all_text=''.join(o.get('text','') for c in book.cells for o in c.get('outputs',[]) if o.output_type=='stream')
    markers={'integrated':'훈련 / 검증 / 새 기기 행 수:', 'tables':'준비 완료.', 'bridge':'첫 행:'}
    assert markers[name] in all_text,(name,markers[name])
    html_path=None
    if name=='integrated':
        html,_=HTMLExporter().from_notebook_node(book)
        html_path=outdir/(name+'-executed.html');html_path.write_text(html,encoding='utf-8')
    result={'status':'passed','notebook':str(source),'source_sha256':source_sha,'code_cells_executed':len(executed),'cells':executed,'kernel':'InProcessKernelManager in a fresh process','stdout_parent_smoke':'passed','source_projection_unchanged':True,'source_file_unchanged':True,'saved_executed':str(saved),'saved_sha256':hashlib.sha256(saved.read_bytes()).hexdigest(),'html':str(html_path) if html_path else None,'images':images,'stdout_cells':sum(any(o.output_type=='stream' for o in c.get('outputs',[])) for c in book.cells),'errors':[]}
    (outdir/(name+'-execution.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='cells'},ensure_ascii=False))
finally:
    client.stop_channels();manager.shutdown_kernel();os.chdir(previous)
