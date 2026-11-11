"""Record a new actual-artifact baseline with preserved and newly traced source demands.

This file performs local byte reads, source-text projection, mechanical payload
preservation checks and discovery transitions. It does not search original web
sources or decide meaning. Comparisons are separately authored reviewer findings.
All writes are confined to this file's own discovery directory.
"""
from __future__ import annotations
import argparse, copy, datetime, hashlib, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'))
import discovery_loop as loop
REVIEWER='/root/discovery_resume'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def save(p,value):
    p.resolve().relative_to(OUT)
    if p.exists():raise ValueError('Refuse to replace existing record: '+rel(p))
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def plain(p,text):
    p.resolve().relative_to(OUT)
    if p.exists():raise ValueError('Refuse to replace existing record: '+rel(p))
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def payloads(state):
    return {d['id']:{k:v for k,v in d.items() if k not in ('trace_id','frontier_id','read_ids')} for d in loop.replay(state)['demands'].values()}
def short(report):
    return {k:report[k] for k in ('authority','status','ready_for_review','session_sha256','seed_sha256','scope','artifact_sha256','open_questions','queue','blockers','usage','exhausted','next_action')}
def project(artifact,folder):
    nb=json.loads(artifact.read_text());chunks=[];spans={};line=1
    for i,c in enumerate(nb['cells']):
        source=c.get('source',[]);text=source if isinstance(source,str) else ''.join(source)
        block=f"## Cell {i}: {c.get('id','<missing>')} ({c['cell_type']})\n\n{text}\n\n"
        chunks.append(block);spans[i]=(line,line+len(block.splitlines())-1);line+=len(block.splitlines())
    p=folder/'lesson-source.md';plain(p,''.join(chunks));return nb,spans,p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--artifact',required=True);ap.add_argument('--expected-sha',required=True);ap.add_argument('--previous',required=True);ap.add_argument('--findings',required=True);ap.add_argument('--run',required=True);ap.add_argument('--author',required=True);ap.add_argument('--boundary',required=True);ap.add_argument('--source-payload');a=ap.parse_args()
    artifact=(ROOT/a.artifact).resolve();artifact.relative_to(ROOT)
    prior=(ROOT/a.previous).resolve();prior.relative_to(ROOT)
    findings_path=(ROOT/a.findings).resolve();findings_path.relative_to(OUT)
    findings=json.loads(findings_path.read_text())
    if sha(artifact)!=a.expected_sha:raise ValueError('Artifact differs from expected final SHA')
    old=json.loads(prior.read_text());before=loop.inspect(old,ROOT)
    old_payloads=payloads(old)
    extra=json.loads((ROOT/a.source_payload).read_text()) if a.source_payload else None
    added={d['id']:d for d in extra['trace']['demands']} if extra else {}
    if set(old_payloads)&set(added):raise ValueError('New source demands cannot replace old demand IDs')
    expected={**old_payloads,**added}
    if set(findings)!=set(expected):raise ValueError('Findings must cover every retained and newly source-traced demand')
    folder=OUT/'runs'/a.run
    if folder.exists():raise ValueError('Choose a new run name; prior records cannot be overwritten')
    folder.mkdir(parents=True)
    nb,spans,projection=project(artifact,folder)
    raw=folder/'artifact-exact.ipynb';raw.write_bytes(artifact.read_bytes())
    cfg=copy.deepcopy(old['seed'])
    if extra:
        if extra['frontier']['id'] in {f['id'] for f in cfg['frontier']}:raise ValueError('Duplicate new frontier ID')
        cfg['frontier'].append(copy.deepcopy(extra['frontier']))
    cfg['scope']={'id':old['seed']['scope']['id']+'-rebound-'+a.run,'lesson_path':rel(projection),'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'lesson_revision':sha(artifact),'readiness':old['seed']['scope']['readiness'],'boundary':a.boundary}
    state=loop.initialize(cfg);save(folder/'config.json',cfg)
    mapping={};transitions=[];seq=0
    def emit(op,data):
        nonlocal state,seq
        seq+=1;event={'id':f'rebind-{a.run}-{seq:03d}-{op}','op':op,'data':data}
        save(folder/'events'/f'{seq:03d}-{op}.json',event)
        state=loop.step(state,event,ROOT)
        report=loop.inspect(state,ROOT)
        transitions.append({'event':event['id'],'status':report['status'],'next_action':report['next_action']})
        return event['id']
    for event in old['events']:
        op=event['op']
        if op=='compare':continue
        if op not in ('discover','read','trace'):raise ValueError('Historical operation needs explicit review before import: '+op)
        data=copy.deepcopy(event['data'])
        if op=='discover':
            data['query']='Historical provenance import for a new actual artifact; no new web search: '+data['query']
        elif op=='read':
            receipt=data.pop('receipt');data['start_line']=receipt['start_line'];data['end_line']=receipt['end_line']
        elif op=='trace':
            data['read_ids']=[mapping[r] for r in data['read_ids']]
            data['rationale']='Historical extracted requirement payloads imported unchanged; not a fresh source extraction. '+data['rationale']
        data['reason']='Separate new actual-artifact baseline; preserve historical external requirements and open questions. Local receipts only; no original-source search or source authentication.'
        mapping[event['id']]=emit(op,data)
    if extra:
        fid=extra['frontier']['id'];actor=extra['extractor']
        emit('discover',{'reason':'Independent extractor directly searched/read official primary material before any new notebook comparison. Local notes retain read extent and limitations.','frontier_id':fid,'query':'Current domestic official practice scope and official Antique input, learned-model, evaluation and submission operations; actual direct web reading on 2026-11-11.','actor':actor,'outcome':'found','candidates':copy.deepcopy(extra['sources'])})
        read_ids=[]
        for source in extra['sources']:
            read_ids.append(emit('read',{'reason':'Read the actual independently authored local primary-source reading note; this receipt is not original-source authentication.','source_id':source['id'],'actor':actor,'start_line':1,'end_line':len((ROOT/source['path']).read_text().splitlines())}))
        trace=copy.deepcopy(extra['trace']);trace['frontier_id']=fid;trace['read_ids']=read_ids;trace['reason']='New source-linked transfer requirements independently extracted before lesson comparison; retain all original requirements and open questions.'
        emit('trace',trace)
    bridge_path=ROOT/'reviews/week01-pipeline-20261111/discovery/runs/bridge-navigation-01/session.json'
    bridge=json.loads(bridge_path.read_text());bridge_report=loop.inspect(bridge,ROOT)
    question_mapping=[]
    for fid,selected in [('problems',[0,1]),('mechanisms',[2])]:
        trace=next(e for e in old['events'] if e['op']=='trace' and e['data']['frontier_id']==fid)
        questions=[bridge_report['open_questions'][i] for i in selected]
        event_id=emit('trace',{'frontier_id':fid,'read_ids':[mapping[r] for r in trace['data']['read_ids']],'actor':REVIEWER,'reason':'Preserve exact additional open-question text from the separate bridge review. No new web search, no demand narrowing, and no assertion that this question is newly source-derived.','rationale':'Manual carryover of prior bridge uncertainty associated with retained source-linked D01/D05/D07. The same demand payloads already exist here and are not duplicated.','counterevidence':'A local bridge exercise or new integrated worked example does not establish later high-dimensional/model transfer, official matching constraints or learner success.','uninvestigated':[q['question'] for q in questions],'demands':[]})
        current_questions=loop.inspect(state,ROOT)['open_questions']
        for q in questions:
            new=next(n for n in current_questions if n['question']==q['question'])
            question_mapping.append({'prior_session_path':rel(bridge_path),'prior_question_id':q['id'],'question':q['question'],'new_question_id':new['id'],'new_frontier_id':fid,'new_trace_event_id':event_id})
    save(folder/'bridge-question-carryover.json',{'prior_session_path':rel(bridge_path),'prior_session_file_sha256':sha(bridge_path),'prior_bridge_demand_payloads_are_exact_subsets':all(old_payloads[k]==v for k,v in payloads(bridge).items()),'mapping':question_mapping,'scope_limit':'Original bridge question IDs remain in its untouched session. This new integrated baseline retains their exact texts under already source-traced frontiers, without adding duplicate educational demands or declaring the questions resolved.'})
    if payloads(state)!=expected:raise ValueError('Original or new demand payload mismatch before comparison')
    cell_ids={c.get('id'):i for i,c in enumerate(nb['cells'])}
    if len(cell_ids)!=len(nb['cells']):raise ValueError('Notebook cell IDs must be unique')
    def span(indices):
        if not indices:return (1,len(projection.read_text().splitlines()))
        indices=[cell_ids[i] if isinstance(i,str) else i for i in indices]
        return (spans[min(indices)][0],spans[max(indices)][1])
    for did,demand in loop.replay(state)['demands'].items():
        finding=findings[did];base=span(finding.get('cells'));dimensions=[]
        for dimension in loop.demand_dimensions(demand):
            custom=finding.get('dimensions',{}).get(dimension['id'],{})
            judgment=custom.get('judgment','met' if finding['judgment']=='covered' else 'uncertain' if finding['judgment']=='uncertain' else 'gap')
            ds=span(custom.get('cells',finding.get('cells')))
            dimensions.append({'id':dimension['id'],'judgment':judgment,'observed_behavior':custom.get('observed_behavior',finding['observed_behavior']),'rationale':'Manual semantic judgment by '+REVIEWER+' after direct lesson reading. Code only binds this declaration to exact file spans; neither semantic entailment nor learner achievement is machine proven.','start_line':ds[0],'end_line':ds[1]})
        emit('compare',{'reason':'Independent manual content review of this standalone artifact against every retained original requirement.','demand_id':did,'reviewer':REVIEWER,'judgment':finding['judgment'],'rationale':finding['observed_behavior'],'start_line':base[0],'end_line':base[1],'dimensions':dimensions})
    report=loop.inspect(state,ROOT)
    if sha(artifact)!=a.expected_sha:raise ValueError('Artifact changed during review; preserve this run and start a new one')
    if payloads(state)!=expected:raise ValueError('Retained/new demand payload mismatch after comparison')
    old_questions={q['question'] for q in before['open_questions']}
    new_questions={q['question'] for q in report['open_questions']}
    if not old_questions.issubset(new_questions):raise ValueError('An original open question was removed or altered')
    save(folder/'session.json',state);save(folder/'report.json',report);save(folder/'current-summary.json',short(report));save(folder/'manifest.json',loop.manifest(state));save(folder/'transitions.json',transitions)
    save(folder/'prior-current-summary.json',short(before))
    save(folder/'projection-provenance.json',{'artifact_path':rel(artifact),'artifact_sha256':sha(artifact),'exact_snapshot_path':rel(raw),'exact_snapshot_sha256':sha(raw),'projection_path':rel(projection),'projection_sha256':sha(projection),'method':'Every cell source in original order with explicit cell index, ID and type; outputs and metadata omitted from projection but preserved in exact notebook snapshot.','cell_count':len(nb['cells']),'cell_spans':spans,'semantic_correspondence_review':'All cell sources directly read by reviewer. Projection correspondence is a manual review declaration; the projector only concatenates the cell source text.','author':a.author,'reviewer':REVIEWER})
    save(folder/'origin.json',{'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_session_path':rel(prior),'prior_session_file_sha256':sha(prior),'prior_session_usage':before['usage'],'prior_artifact_sha256':before['scope'].get('artifact_sha256'),'new_artifact_path':rel(artifact),'new_artifact_sha256':sha(artifact),'new_baseline_reason':'The actual artifact bytes changed, or this is a different standalone lesson artifact. A new explicit seed is required. Prior session history remains unchanged; this is not a continuation that erases counters or gaps.','prior_original_demand_payloads_unchanged':True,'retained_demand_ids':list(old_payloads),'retained_open_question_count':len(old_questions),'historical_external_sources_imported_unchanged':True,'new_source_payload_path':a.source_payload,'new_source_payload_sha256':sha(ROOT/a.source_payload) if a.source_payload else None,'new_extractor':extra['extractor'] if extra else None,'added_demand_ids':list(added),'new_open_question_count':len(new_questions-old_questions),'findings_path':rel(findings_path),'findings_sha256':sha(findings_path),'author':a.author,'reviewer':REVIEWER,'student_answers_fabricated':False,'learner_mastery_observed':False,'classroom_or_selfstudy_duration_measured':False,'original_artifact_modified_by_reviewer':False,'original_prior_session_modified_by_reviewer':False})
    print(json.dumps({'run':rel(folder),'artifact_sha256':sha(artifact),'status':report['status'],'ready_for_review':report['ready_for_review'],'demand_count':len(report['demands']),'queue_count':len(report['queue']),'covered':[c['demand_id'] for c in report['comparisons'] if c['judgment']=='covered'],'events':report['usage']['events'],'next_action':report['next_action'],'prior_artifact_changed':any(b['code']=='artifact_changed' for b in before['blockers'])},ensure_ascii=False))
if __name__=='__main__':main()
