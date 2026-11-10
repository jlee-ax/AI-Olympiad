from pathlib import Path
from datetime import datetime,timezone
import json,time,hashlib,math,base64,sys,importlib.metadata
import nbformat
from nbclient import NotebookClient
import argparse
from ipykernel.inprocess.manager import InProcessKernelManager
from queue import Empty
from nbconvert import HTMLExporter
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
OUT=ROOT
FIGDIR=ROOT/".validation"
FIGDIR.mkdir(exist_ok=True)
parser=argparse.ArgumentParser()
parser.add_argument("--inprocess",action="store_true",help="Use a fresh socket-free IPython kernel in restricted cloud environments")
args=parser.parse_args()
path=OUT/"week01_python_tables.ipynb"
nb=nbformat.read(path,as_version=4)
nbformat.validate(nb)
started=time.monotonic()
def execute_inprocess(notebook, directory):
    import os
    old_directory=Path.cwd()
    os.chdir(directory)
    manager=InProcessKernelManager()
    manager.start_kernel()
    kernel_client=manager.client()
    kernel_client.start_channels()
    try:
        for cell in notebook.cells:
            if cell.cell_type!="code":
                continue
            message_id=kernel_client.execute(cell.source,store_history=True)
            reply=kernel_client.get_shell_msg(timeout=180)
            if reply["content"]["status"]!="ok":
                raise RuntimeError(reply["content"])
            cell.outputs=[]
            cell.execution_count=reply["content"]["execution_count"]
            while True:
                message=kernel_client.get_iopub_msg(timeout=180)
                kind=message["msg_type"]
                if kind=="status" and message["content"].get("execution_state")=="idle":
                    break
                if kind in ["stream","display_data","execute_result","error"]:
                    cell.outputs.append(nbformat.v4.output_from_msg(message))
            if any(o.output_type=="error" for o in cell.outputs):
                raise RuntimeError("Cell failed")
    finally:
        kernel_client.stop_channels()
        manager.shutdown_kernel()
        os.chdir(old_directory)
def execute_notebook(notebook,directory):
    if args.inprocess:
        execute_inprocess(notebook,directory)
    else:
        NotebookClient(notebook,timeout=180,kernel_name="python3",resources={"metadata":{"path":str(directory)}}).execute()
execute_notebook(nb,OUT)
elapsed=time.monotonic()-started
nbformat.validate(nb)
nbformat.write(nb,path)

# Independent arithmetic checks use Python sums rather than only repeating NumPy reductions.
A=[[2.,4.],[6.,8.],[10.,12.]]
manual_column=[sum(row[j] for row in A)/len(A) for j in range(len(A[0]))]
manual_row=[sum(row)/len(row) for row in A]
assert manual_column==[6,8] and manual_row==[3,7,11]
assert np.allclose(np.array(A).mean(axis=0),manual_column)
assert np.allclose(np.array(A).mean(axis=1),manual_row)
seq=[2,4,6];avg=sum(seq)/len(seq)
variance=sum((x-avg)**2 for x in seq)/len(seq)
assert math.isclose(variance,8/3)
assert math.isclose(np.var(seq,ddof=0),variance)
assert math.isclose(pd.Series(seq).var(ddof=0),variance)
assert math.isclose(sum((x+10-(avg+10))**2 for x in seq)/len(seq),variance)
B=[[1,5,9],[3,7,11]]
assert [sum(row[j] for row in B)/len(B) for j in range(3)]==[2,6,10]
assert [sum(row)/len(row) for row in B]==[5,7]
data=pd.read_csv(OUT/"data/week1_plants.csv")
assert data.shape==(6,5) and data["water_ml"].isna().sum()==1
observed=[0,20,40,20,60]
assert sum(observed)/len(observed)==28
assert data.loc[data["water_ml"].isna(),"pot_id"].tolist()==["P03"]
assert data.loc[data["water_ml"].eq(0),"pot_id"].tolist()==["P01"]
assert data.loc[data.sunlight_hours.ge(5),"pot_id"].tolist()==["P03","P04","P06"]
new=pd.read_csv(OUT/"data/week1_plants_new.csv")
assert new.shape==(4,5)
assert new.loc[new.light_hours.ge(4),"sample_id"].tolist()==["Q03","Q04"]
assert new.water_amount_ml.notna().sum()==3 and new.water_amount_ml.mean()==20
assert sum(a*b for a,b in zip([1,4,2],[800,500,1200]))==5200
histcounts=np.histogram(data.height_cm,bins=[6,10,14,18,22])[0].tolist()
assert histcounts==[1,3,1,1]

manifest=json.loads((OUT/"lesson-manifest.json").read_text())
blocks=manifest["class_blocks"]
assert blocks[0]["start"]==0 and blocks[-1]["end"]==120
assert all(a["end"]==b["start"] for a,b in zip(blocks,blocks[1:]))
totals={k:sum(b["end"]-b["start"] for b in blocks if b["type"]==k) for k in ["theory","noncoding","coding"]}
assert totals=={"theory":20,"noncoding":20,"coding":80}
ranges=manifest["homework_ranges_minutes"]
assert [sum(r[i] for r in ranges) for i in [0,1]]==[300,420]
assert manifest["schedules_created"] is False
errors=[(i,o) for i,c in enumerate(nb.cells) if c.cell_type=="code" for o in c.outputs if o.output_type=="error"]
assert not errors
codes=[c for c in nb.cells if c.cell_type=="code"]
assert all(isinstance(c.execution_count,int) for c in codes)
png=[]
for i,c in enumerate(nb.cells):
    if c.cell_type=="code":
        for output in c.outputs:
            payload=output.get("data",{}).get("image/png")
            if payload:
                png.append(i)
                (FIGDIR/f"figure_cell_{i:02}.png").write_bytes(base64.b64decode(payload))
exporter=HTMLExporter()
exporter.exclude_input_prompt=True
exporter.exclude_output_prompt=True
html,_=exporter.from_notebook_node(nb)
# A readable Korean body font; code remains monospace.
html=html.replace("</head>","<style>body{font-family:'Noto Sans CJK KR','Noto Sans CJK JP',sans-serif} .jp-RenderedHTMLCommon{font-size:16px;line-height:1.75} .jp-Notebook{max-width:1100px;margin:auto} .jp-RenderedHTMLCommon img{max-width:100%;height:auto}</style></head>")
(OUT/"week01_python_tables.html").write_text(html,encoding="utf-8")

standalone=FIGDIR/"standalone-check"
standalone.mkdir(exist_ok=True)
fallback_nb=nbformat.read(path,as_version=4)
for cell in fallback_nb.cells:
    if cell.cell_type=="code":
        cell.outputs=[];cell.execution_count=None
execute_notebook(fallback_nb,standalone)
fallback_outputs=" ".join("".join(o.get("text","")) for c in fallback_nb.cells if c.cell_type=="code" for o in c.outputs)
assert "노트북에 포함된 동일한 CSV" in fallback_outputs

text="\n".join(c.source for c in nb.cells if c.cell_type=="markdown")
assert "—" not in text and "–" not in text
assert r"\sum" in text and r"\bar{x}" in text and "keepdims=False" in text
assert sum("student-response" in c.get("metadata",{}).get("tags",[]) for c in nb.cells)>=10
report={
 "checked_at_utc":datetime.now(timezone.utc).isoformat(),
 "notebook":path.name,"base_commit":manifest["base_commit"],
 "nbformat_validation":"passed","top_to_bottom_execution":"passed",
 "execution_method":("fresh IPython InProcessKernelManager per complete run" if args.inprocess else "nbclient separate fresh kernel"),
 "separate_nbclient_kernel":("blocked in authoring cloud: environment prohibits ZMQ TCP and IPC sockets; kernel died before cell execution" if args.inprocess else "passed"),
 "code_cells":len(codes),"executed_code_cells":len(codes),"error_outputs":len(errors),
 "execution_seconds":round(elapsed,3),
 "plot_output_cells":png,"plot_output_count":len(png),
 "embedded_diagrams":sum(len(c.get("attachments",{})) for c in nb.cells),
 "independent_arithmetic_checks":"passed",
 "csv_checks":"passed","histogram_counts":histcounts,
 "time_minutes":totals,"class_total":120,"required_homework_minutes":[300,420],
 "standalone_without_csv_files":"passed",
 "student_answers":"blank_not_assessed","student_mastery":"not_observed",
 "classroom_timing":"estimated_not_observed",
 "visual_inspection":"pending_after_execution","browser_jupyterlab":"not_checked_by_script",
 "packages":{p:importlib.metadata.version(p) for p in ["numpy","pandas","matplotlib","seaborn","jupyterlab","nbclient","nbformat","ipykernel"]},
 "notebook_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
 "source_baseline_sha256":manifest["baseline_sha256"],
 "schedules_created":False
}
(OUT/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
