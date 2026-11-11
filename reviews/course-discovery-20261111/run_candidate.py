"""Review a completed actual Week2 notebook without editing it or its teacher files."""
import argparse, contextlib, copy, io, json, sys
from pathlib import Path
from run_review import ROOT,OUT,Run,loop,sha,rel,save,write_once,nlines,prepare,REVIEWER

def project(artifact,path):
 nb=json.loads(artifact.read_text()); chunks=[]; spans={}; line=1
 for i,c in enumerate(nb['cells']):
    text=''.join(c.get('source',[])); block=f"## Cell {i}: {c.get('id','<missing>')} ({c['cell_type']})\n\n{text}\n\n"
    chunks.append(block); spans[i]=(line,line+len(block.splitlines())-1);line+=len(block.splitlines())
 write_once(path,''.join(chunks));return nb,spans

def actual_execution(nb,artifact,path):
 # In-process IPython executes notebook cells in order without kernel sockets.
 # Student answer cells remain untouched; results live only in this new review.
 from IPython.core.interactiveshell import InteractiveShell
 import importlib.metadata
 shell=InteractiveShell(user_ns={}); results=[]
 for i,c in enumerate(nb['cells']):
    if c['cell_type']!='code': continue
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
      result=shell.run_cell(''.join(c.get('source',[])),store_history=True)
    error=result.error_before_exec or result.error_in_exec
    results.append({'cell_index':i,'cell_id':c.get('id'),'stdout':stream.getvalue(),'error':None if error is None else repr(error)})
    if error:break
 ns=shell.user_ns
 checks=[]
 if not any(r['error'] for r in results):
    import numpy as np
    def check(name,condition):checks.append({'name':name,'passed':bool(condition)})
    check('known training rows exclude unknown',ns['known_train']['row_id'].tolist()==['a1','a2','b1','b2'])
    check('split group sets disjoint',set(ns['train']['group']).isdisjoint(set(ns['validation']['group'])))
    check('valid and deliberately leaky imputation differ 4 versus 9',np.isclose(ns['preprocess'].named_steps['imputer'].statistics_[0],4) and np.isclose(ns['leaky_imputer'].statistics_[0],9))
    before=ns['preprocess'].named_steps['imputer'].statistics_.copy();ns['preprocess'].transform(ns['X_val']*100);check('transform changed validation values leaves learned imputation unchanged',np.array_equal(before,ns['preprocess'].named_steps['imputer'].statistics_))
    check('rule confusion matrix correct',ns['rule_cm'].tolist()==[[0,2],[1,1]])
    check('zero denominator policy remains NaN with zero recall',np.isnan(ns['p_nan']) and ns['r_nan']==0)
    check('row and group metric differ on stated unequal counts',np.isclose(ns['group_example']['correct'].mean(),2/3) and np.isclose(ns['group_accuracy']['mean'].mean(),.4))
    check('ROC matrices at both thresholds',ns['roc_matrices']=={.5:[[1,1],[1,1]],.3:[[1,1],[0,2]]})
 result={'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'method':'fresh in-process IPython InteractiveShell; top-to-bottom execution; no source notebook writes','code_cell_count':sum(c['cell_type']=='code' for c in nb['cells']),'executed_code_cells':len(results),'error_count':sum(bool(r['error']) for r in results),'cells':results,'independent_runtime_checks':checks,'versions':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scikit-learn','ipython']},'student_answers_evaluated':False,'learner_performance_observed':False,'time_to_learn_measured':False,'limits':['Finite code/examples only. No student answers were fabricated or completed.','Checks of numeric outputs and saved statistics do not authenticate explanations, transfer, class timing or course sufficiency.','No CLIP, contest dataset, online API, hidden test or deployment execution was attempted.']}
 save(path,result)
 if result['error_count'] or not all(c['passed'] for c in checks):raise RuntimeError('Candidate execution or runtime check failed')
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--expected-sha',required=True);a=ap.parse_args();prepare()
 artifact=ROOT/'lessons/week02/week02_prediction_evaluation.ipynb'
 if sha(artifact)!=a.expected_sha:raise ValueError('Candidate bytes changed before review')
 folder=OUT/'candidate-inputs'/a.run;folder.mkdir(parents=True,exist_ok=True)
 projection=folder/'lesson-source.md';nb,sp=project(artifact,projection)
 save(folder/'projection-provenance.json',{'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'projection_path':rel(projection),'projection_sha256':sha(projection),'method':'ordered source text of every notebook cell, including cell IDs and type, with explicit cell headings; outputs omitted','semantic_correspondence_review':'Reviewer directly read all 25 cells, source and teacher notes; headings are added, no teaching content is added.','cell_spans':sp,'author':'/root/week02_lesson (gpt-6.1-terra, max), identity confirmed by parent','reviewer':REVIEWER})
 prior=ROOT/'reviews/discovery-loop-20261111/runs/session.json';old=json.loads(prior.read_text());v=loop.replay(old)
 config={'schema_version':1,'synthetic':False,'scope':{'id':'actual-week02-against-retained-course-frontier','lesson_path':rel(projection),'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'lesson_revision':sha(artifact),'readiness':'course','boundary':'Separate actual Week2-only artifact review against the unchanged fourteen prior demands and three new demands. No earlier lesson judgment is erased. This unit is not an assembled ten-week course; its open demands remain course work.'},'frontier':copy.deepcopy(old['seed']['frontier'])+[{'id':'heldout','question':'Revisit original scoring and runtime-contract requirements on actual Week2 without narrowing them.','required_kinds':['official_problem']},{'id':'next-wave','question':'Compare new national modality and Pixel/Antique/CS229 requirements with actual Week2.','required_kinds':['official_scope','official_problem','research']}],'policy':{'max_events':100,'max_rounds':20,'max_no_progress':8,'max_elapsed_minutes':180}}
 save(folder/'config.json',config);r=Run(a.run,loop.initialize(config))
 # Import original demands and provenance exactly; actor identifies the historical
 # extractor, not a new extraction/search performed by this reviewer.
 for fid in ['scope','problems','mechanisms','heldout']:
    original=[d for d in v['demands'].values() if d['frontier_id']==fid]
    sids=sorted({v['reads'][rid]['source_id'] for d in original for rid in d['read_ids']})
    sources=[v['sources'][sid] for sid in sids]
    r.event('discover',frontier_id=fid,query='Replay prior declared source notes for retained demand semantics; not a new web search: '+rel(prior),actor='source-research-sol',outcome='found',candidates=sources)
    reads=[r.event('read',source_id=s['id'],actor='source-research-sol',start_line=1,end_line=nlines(ROOT/s['path'])) for s in sources]
    demands=[{k:val for k,val in d.items() if k not in ['trace_id','frontier_id','read_ids']} for d in original]
    r.event('trace',frontier_id=fid,read_ids=reads,actor='source-research-sol',rationale='Unchanged historical demand payloads copied from original source extractor; not a claim of a fresh extraction or current web-source verification.',counterevidence='Original source notes are agent-authored paraphrases. Original broad course demand does not imply all of it belongs in Week2.',uninvestigated=[],demands=demands)
 r.external('next-wave')
 def span(*indices):return (sp[min(indices)][0],sp[max(indices)][1])
 whole=(1,nlines(projection))
 findings={
 'D11':('uncertain','National page remains IOAI2026-labelled while linking from KOAI2027. Candidate states national 2026 scope. International2027 full differences and domestic applicability remain unverified.',span(24),None),
 'D01':('gap','Tabular row/column and one-feature transforms are implemented; no independent high-dimensional axis/layout transfer required by Radar/retrieval is present. This is later-course residual work.',whole,{'prerequisites':'met'}),
 'D02':('gap','No distance-neighbor voting implementation or unseen k/tie/duplicate-point assessment is present. Week2 is a prerequisite, not the Week4 kNN lesson.',whole,None),
 'D03':('uncertain','Cells2–5 distinguish feature/target/time and use reading only; Cell19 asks about post-prediction repair data. Original requirement also asks independent shape-correct versus semantically unavailable input diagnosis; that exact contrast is not explicitly assessed here. Earlier Week1 covered judgment is preserved in its own baseline.',span(2,5),{'prerequisites':'met','learning':'met','principle':'met','practice':'met','assessment':'uncertain'}),
 'D04':('gap','Permitted -1/+1 outputs and unknown handling exist; no internal index encode/decode or noncontiguous multi-class label restoration exercise is implemented.',span(2,5),{'prerequisites':'met'}),
 'D05':('gap','Row IDs and output ordering are explained; no retrieval similarity-matrix position-to-original-ID reconstruction or new-ID assessment is implemented.',span(2,5),{'prerequisites':'met'}),
 'D12':('gap','No mutable-default/alias diagnostic is implemented. This remains a separate Python follow-up rather than an asserted Week2 requirement.',whole,None),
 'D06':('uncertain','Cells6–8 derive train-only mean/scale and execute correct transform plus a separately marked leakage counterexample. Cell19 supplies new-input independent fit/transform and reasons. The retained assessment also requires leakage versus overfitting distinction; Cell3 mentions validation adaptation, but no independent contrast item is provided. Formula and operation improve; full original demand is not marked covered.',span(6,8),{'prerequisites':'met','learning':'met','principle':'met','practice':'met','assessment':'uncertain'}),
 'D07':('gap','No token embedding lookup or new vocabulary-axis shape assessment exists.',whole,None),
 'D08':('gap','No attention mask participation semantics or all-masked/variable-length assessment exists.',whole,None),
 'D09':('gap','Classification metrics are not softmax/cross-entropy derivation or stable-logit computation. No probability/loss/stabilization assessment exists.',span(9,15),None),
 'D10':('gap','Independent new inputs, hand/code checks and finite-example limitations are present. The original demand retains numerical gradient checks/relative-error foundations, which are not taught or assessed in this unit.',span(19,24),{'learning':'met','assessment':'uncertain','practice':'met','prerequisites':'gap','principle':'gap'}),
 'H01':('gap','Cells16–19 teach row accuracy versus mean per-group accuracy on unequal group counts. The retained Radar demand instead uses truth-dependent weights w(-1)=1, others=50 and requires metric ranking reversal. Those operations and their independent assessment are absent; a related denominator lesson is partial prerequisite progress.',span(16,19),{'prerequisites':'met'}),
 'H02':('gap','Candidate distinguishes public development labels from hidden inference labels and says to check the contract. It does not implement unavailable inference API detection/removal or offline submission reconstruction required by Concepts.',span(3),{'prerequisites':'uncertain'}),
 'N01':('covered','For this Week2 unit only, explicit reasoning/calculation (Cells2–4,6,9,16) is connected to actual code (5,7,11,13,15,17) and a distinct new-input written+coding task (19–21), with help recording. This is a manual material-design judgment, not a course/exam/student success finding.',span(19,21),None),
 'N02':('gap','No half-open image rectangle, area budget, boundary case or JSONL output-contract task exists in Week2. Appropriate later placement is a proposal; no actual Week7/9 delivery or responsible committed placement is claimed.',whole,{'prerequisites':'uncertain'}),
 'N03':('uncertain','Cells2/4/14–15 correctly distinguish unknown from negative and explicitly limit known-label training; Cell19 asks new n3 reason and implementation. The CS229-derived observation-model/constant-alpha counterexample is not taught or independently tested. Introductory label semantics are supported, but the entire declared assumptions dimension remains uncertain.',span(2,4),{'prerequisites':'met','learning':'met','assessment':'met','assumptions':'uncertain'})}
 for did,(judgment,observed,basis,dimj) in findings.items():
    ds={}
    if did in ['D03','D06','N01','N03']:ds['assessment']=span(19,21)
    if did=='N03':ds['assumptions']=span(4,8)
    if did=='D06':ds['principle']=span(6,8);ds['practice']=span(7,8)
    r.compare(did,judgment,observed,basis,ds,dimj)
 report=r.finish()
 before_sha=sha(artifact);execution=actual_execution(nb,artifact,r.path/'execution-output.json')
 if sha(artifact)!=before_sha:raise ValueError('Original notebook bytes changed during execution/review; retain this session as stale and create a new run')
 save(r.path/'origin.json',{'parent_baseline_session':rel(prior),'parent_baseline_file_sha256':sha(prior),'expanded_baseline_session':rel(OUT/'runs/baseline-wave-01/session.json'),'expanded_baseline_file_sha256':sha(OUT/'runs/baseline-wave-01/session.json'),'previous_candidate_observed_but_not_review_bound':'ca7ba8c40797859bd74a051a28c850e15131bcc9aff552e0f046edef0d5104bd','candidate_original_path':rel(artifact),'candidate_original_sha256':before_sha,'new_baseline_reason':'Different actual lesson artifact requires a new explicit seed; all original demand payloads retained without retirement or narrowing.','author_role':'/root/week02_lesson (gpt-6.1-terra, max), distinct teaching author; identity confirmed by parent','reviewer_role':REVIEWER,'new_extractor_role':'/root/course_discovery/verify_new_scope','historical_extractor_role':'source-research-sol, imported unchanged','original_notebook_modified':False,'original_teacher_files_modified':False,'student_mastery':'not_observed'})
 print(json.dumps({'run':rel(r.path),'artifact_sha256':before_sha,'status':report['status'],'ready_for_review':report['ready_for_review'],'demands':len(report['demands']),'queue_count':len(report['queue']),'covered':[c['demand_id'] for c in report['comparisons'] if c.get('judgment')=='covered'],'events':report['usage']['events'],'code_cells_executed':execution['executed_code_cells'],'runtime_checks':len(execution['independent_runtime_checks']),'next_action':report['next_action']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
