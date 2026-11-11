"""Separate actual Week1 supplement comparison; no merged-course claim."""
import argparse,contextlib,io,json
from pathlib import Path
from run_review import ROOT,OUT,Run,loop,sha,rel,save,nlines,REVIEWER
from run_candidate import project
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--expected-sha',required=True);a=ap.parse_args()
artifact=ROOT/'lessons/week01/week01_axes_linear_bridge.ipynb'
if sha(artifact)!=a.expected_sha:raise ValueError('Bridge artifact changed before review')
folder=OUT/'candidate-inputs'/a.run;folder.mkdir(parents=True,exist_ok=True)
projection=folder/'lesson-source.md';nb,sp=project(artifact,projection)
original=ROOT/'reviews/discovery-loop-20261111/runs/session.json';old=json.loads(original.read_text());v=loop.replay(old);selected=[v['demands'][d] for d in ['D01','D05','D07']]
sids=sorted({v['reads'][rid]['source_id'] for d in selected for rid in d['read_ids']});sources=[v['sources'][sid] for sid in sids]
config={'schema_version':1,'synthetic':False,'scope':{'id':'week01-supplement-retained-demands','lesson_path':rel(projection),'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'lesson_revision':sha(artifact),'readiness':'course','boundary':'Independent Week1 supplementary artifact only, assessed against three unchanged original broad demands. Neither original Week1 nor Week2 is merged into this projection. No course completion or mandatory Week1 placement is inferred.'},'frontier':[{'id':'retained-three','question':'Which parts of original D01/D05/D07 are actually implemented in the new bridge, and which original operations still remain?','required_kinds':['official_scope','official_problem','research']}],'policy':{'max_events':80,'max_rounds':12,'max_no_progress':8,'max_elapsed_minutes':180}}
save(folder/'config.json',config);save(folder/'projection-provenance.json',{'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'projection_path':rel(projection),'projection_sha256':sha(projection),'method':'all 29 cell source texts in order, explicit cell IDs/types, outputs omitted','author':'/root/week01_bridge (gpt-6.1-terra, max), confirmed by parent','reviewer':REVIEWER,'cell_spans':sp})
r=Run(a.run,loop.initialize(config))
r.event('discover',frontier_id='retained-three',query='Retained original source notes supporting D01/D05/D07; original source extraction is imported, not a new web search.',actor='source-research-sol',outcome='found',candidates=sources)
reads=[r.event('read',source_id=s['id'],actor='source-research-sol',start_line=1,end_line=nlines(ROOT/s['path'])) for s in sources]
r.event('trace',frontier_id='retained-three',read_ids=reads,actor='source-research-sol',rationale='Retain exact original demand payloads and source-note provenance for this separate actual supplement comparison.',counterevidence='The supplement explicitly limits itself to foundations and optional bridges. Missing later-course operations do not make the foundational unit inappropriate.',uninvestigated=['High-dimensional/model-context axis tracking and reshape-versus-transpose still require actual later material.','Normalization, identity/gender matching constraints and real encoder/submission performance remain separate from synthetic maximum-dot-product lookup.','Vocabulary-versus-sequence axes and independent new lookup B/L/H assessment remain future teaching; student transfer and time are unobserved.'],demands=[{k:val for k,val in d.items() if k not in ['trace_id','frontier_id','read_ids']} for d in selected])
def span(lo,hi):return (sp[lo][0],sp[hi][1])
r.compare('D01','gap','Cells1–12 and20–23 explicitly explain row/feature/output axes, contraction and shape-correct feature-order errors. The unchanged original demand additionally requires reshape-versus-transpose coordinate prediction and an incorrect-reshape counterexample, plus model-input/target-axis transfer. Those are not implemented in this standalone supplement. This is local progress, not broad D01 completion.',span(1,12),{'assessment':span(20,23)},{'prerequisites':'met','learning':'uncertain','assessment':'gap','principle':'gap','practice':'gap'})
r.compare('D05','gap','Cells13–17 build Q@G.T, convert maximum positions to arbitrary IDs, and show a shape-preserving shuffled-ID failure; Cells24–27 supply a new independent ID/order task. Norm/normalized cosine and same-identity/different-gender official matching constraints are absent; text correctly labels synthetic max-dot scoring as a teaching contract. The original broad demand remains open.',span(13,17),{'assessment':span(24,27),'practice':span(24,27)},{'prerequisites':'gap','learning':'gap','assessment':'uncertain','principle':'gap','practice':'met'})
r.compare('D07','gap','Cells17–19 now prompt and print all lookup vectors, show (2,3)->(2,3,2), preserve repeated-index values and contrast a shape-preserving reversed-position error. Learning and guided practice progress are met. No separate independent lookup task varies B/L/H or contrasts vocabulary size V with token length L; independent Cell28 remains stack/concatenate with candidate-ID alignment, not lookup. The original broad demand remains gap.',span(17,19),{'assessment':span(28,28)},{'prerequisites':'met','learning':'met','assessment':'gap','principle':'uncertain','practice':'met'})
report=r.finish()
from IPython.core.interactiveshell import InteractiveShell
shell=InteractiveShell(user_ns={});outputs=[]
for i,c in enumerate(nb['cells']):
 if c['cell_type']!='code':continue
 stream=io.StringIO()
 with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):res=shell.run_cell(''.join(c['source']),store_history=True)
 err=res.error_before_exec or res.error_in_exec;outputs.append({'cell_index':i,'cell_id':c.get('id'),'stdout':stream.getvalue(),'error':None if err is None else repr(err)})
 if err:break
ns=shell.user_ns
import numpy as np
checks={'linear_transformation_output':np.array_equal(ns['Y'],[[2,1,4],[1,3,7],[3,2,7]]),'ID_restoration_after_shuffle':np.array_equal(ns['right'],[35,7]) and np.array_equal(ns['wrong'],[19,35]),'lookup_shape_and_repeated_index_row':ns['looked_up'].shape==(*ns['token_indices'].shape,ns['table'].shape[1]) and np.array_equal(ns['looked_up'][0,0],ns['looked_up'][1,1])}
save(r.path/'execution-output.json',{'artifact_sha256':sha(artifact),'method':'fresh in-process IPython; ordered code cells; no source-file write','code_cells':len(outputs),'errors':sum(bool(x['error']) for x in outputs),'outputs':outputs,'finite_runtime_checks':checks,'student_answers_fabricated':False,'student_learning_observed':False,'scope_limit':'Numeric toy examples only, no encoder/contest data/hidden submission execution or student evaluation.'})
if sha(artifact)!=a.expected_sha:raise ValueError('Bridge artifact changed during review')
if any(x['error'] for x in outputs) or not all(checks.values()):raise ValueError('Bridge runtime check failed')
save(r.path/'origin.json',{'original_session_path':rel(original),'original_session_sha256':sha(original),'candidate_path':rel(artifact),'candidate_sha256':sha(artifact),'author':'/root/week01_bridge','reviewer':REVIEWER,'original_demand_payloads_unchanged':True,'original_lesson_unmodified':True,'comparison_scope':'Separate supplement only; no change to prior baseline or Week2 session.'})
print(json.dumps({'run':rel(r.path),'artifact_sha256':sha(artifact),'status':report['status'],'ready_for_review':report['ready_for_review'],'queue_count':len(report['queue']),'events':report['usage']['events'],'code_cells_executed':len(outputs),'finite_runtime_checks':len(checks)},ensure_ascii=False,indent=2))
