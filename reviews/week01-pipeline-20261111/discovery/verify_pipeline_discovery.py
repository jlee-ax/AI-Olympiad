"""Read-only verification of this source-linked discovery review.
Checks bytes, retained declarations and replay; never searches or judges meaning.
"""
from __future__ import annotations
import ast,hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(OUT));from rebind_pipeline_review import loop,payloads
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    initial=json.loads((OUT/'initial-state/manifest.json').read_text())
    bridge='lessons/week01/week01_axes_linear_bridge.ipynb'
    protected=[]
    for name,expected in initial['protected_files'].items():
        actual=sha(ROOT/name);protected.append({'path':name,'expected_initial_sha256':expected,'current_sha256':actual,'unchanged':actual==expected,'authorized_navigation_change':name==bridge})
    selection_path=OUT/'current-run-selection.json';selection=json.loads(selection_path.read_text());current=set(selection['current_runs']);historical=selection.get('historical_runs',{})
    paths=sorted((OUT/'runs').glob('*/session.json'))
    if {p.parent.name for p in paths} != current|set(historical):raise ValueError('Every run must have an explicit current or historical disposition')
    runs=[];past=[]
    for p in paths:
        folder=p.parent;s=json.loads(p.read_text());r=loop.inspect(s,ROOT);origin=json.loads((folder/'origin.json').read_text());prior=ROOT/origin['prior_session_path'];old=json.loads(prior.read_text());old_r=loop.inspect(old,ROOT)
        extra=json.loads((ROOT/origin['new_source_payload_path']).read_text()) if origin['new_source_payload_path'] else None
        expected=payloads(old)
        if extra:expected={**expected,**{d['id']:d for d in extra['trace']['demands']}}
        prov=json.loads((folder/'projection-provenance.json').read_text());artifact=ROOT/prov['artifact_path'];snapshot=ROOT/prov['exact_snapshot_path'];projection=ROOT/prov['projection_path'];nb=json.loads(snapshot.read_text());chunks=[]
        for i,c in enumerate(nb['cells']):
            source=c.get('source',[]);text=source if isinstance(source,str) else ''.join(source)
            chunks.append(f"## Cell {i}: {c.get('id','<missing>')} ({c['cell_type']})\n\n{text}\n\n")
        old_questions={q['question'] for q in old_r['open_questions']};wanted_questions=old_questions|set(extra['trace']['uninvestigated'] if extra else [])
        static={'prior_session_unchanged':sha(prior)==origin['prior_session_file_sha256'],'all_retained_and_new_demand_payloads_match':payloads(s)==expected,'all_original_open_questions_retained':old_questions.issubset({q['question'] for q in r['open_questions']}),'expected_open_questions_match':wanted_questions=={q['question'] for q in r['open_questions']},'snapshot_matches_bound_sha':sha(snapshot)==prov['artifact_sha256']==r['scope']['artifact_sha256'],'projection_matches_every_snapshot_cell_source':projection.read_text()==''.join(chunks),'projection_matches_recorded_sha':sha(projection)==prov['projection_sha256'],'findings_match_recorded_sha':sha(ROOT/origin['findings_path'])==origin['findings_sha256'],'new_source_payload_matches_recorded_sha':not extra or sha(ROOT/origin['new_source_payload_path'])==origin['new_source_payload_sha256']}
        fresh={'artifact_matches_binding':sha(artifact)==prov['artifact_sha256'],'snapshot_is_exact_current_bytes':artifact.read_bytes()==snapshot.read_bytes(),'saved_report_matches_current_inspection':json.loads((folder/'report.json').read_text())==r,'freshness_blockers_absent':not any(b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read') for b in r['blockers'])}
        blanks=[]
        for i,c in enumerate(nb['cells']):
            if c.get('id')=='06ceb97e':blanks.append({'cell_index':i,'cell_id':c['id'],'ast_statement_count':len(ast.parse(''.join(c['source'])).body)})
        item={'run':folder.name,'session_path':str(p.relative_to(ROOT)),'session_file_sha256':sha(p),'bound_artifact_sha256':prov['artifact_sha256'],'current_artifact_sha256':sha(artifact),'projection_sha256':sha(projection),'static_checks':static,'current_checks':fresh,'status':r['status'],'ready_for_review':r['ready_for_review'],'demand_count':len(r['demands']),'retained_demand_count':len(payloads(old)),'added_demand_ids':origin['added_demand_ids'],'queue_count':len(r['queue']),'covered':[c['demand_id'] for c in r['comparisons'] if c['judgment']=='covered'],'events':r['usage']['events'],'open_question_count':len(r['open_questions']),'next_action':r['next_action'],'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')],'blank_answer_cells':blanks}
        if folder.name in current:runs.append(item)
        else:
            item['historical_disposition']=historical[folder.name]
            item['historical_session_sha_matches_selection']=sha(p)==historical[folder.name]['session_file_sha256']
            item['historical_report_sha_matches_selection']=sha(folder/'report.json')==historical[folder.name]['report_file_sha256']
            past.append(item)
    old_current=[]
    oldbase=ROOT/'reviews/week02-expansion-20261111/discovery';old_selection=json.loads((oldbase/'current-run-selection.json').read_text())
    for name in old_selection['current_runs']:
        p=oldbase/'runs'/name/'session.json';r=loop.inspect(json.loads(p.read_text()),ROOT);old_current.append({'run':name,'session_path':str(p.relative_to(ROOT)),'status':r['status'],'ready_for_review':r['ready_for_review'],'bound_artifact_sha256':r['scope']['artifact_sha256'],'current_artifact_sha256':r['artifact_sha256'],'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')]})
    index=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=ROOT,text=True).strip());index=index if index.is_absolute() else ROOT/index
    history_ok=all(x['unchanged'] for x in protected if not x['authorized_navigation_change']) and all(all(x['static_checks'].values()) and x['historical_session_sha_matches_selection'] and x['historical_report_sha_matches_selection'] for x in past)
    current_ok=all(all(x['static_checks'].values()) and all(x['current_checks'].values()) and all(c['ast_statement_count']==0 for c in x['blank_answer_cells']) for x in runs)
    result={'authority':'advisory_only','current_selection':str(selection_path.relative_to(ROOT)),'protected_initial_files':protected,'all_protected_history_and_original_unchanged':history_ok,'new_current_sessions':runs,'historical_rebound_sessions':past,'previous_current_session_inspections':old_current,'all_current_mechanical_checks_passed':current_ok,'git_index_sha256':sha(index),'git_index_matches_initial':sha(index)==initial['git_index_sha256'],'limits':['Comparison meaning was directly judged by the independent reviewer. This script checks bytes and recorded declarations only.','The source extractor performed new official-web reads independently of lesson content; local source receipts authenticate neither upstream source truth nor independence.','Prior quality/workflow agreement and readiness records remain unchanged; new production authorization is not a fabricated old acceptance.','No student answers or learning results were observed.']}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if history_ok and current_ok else 2
if __name__=='__main__':raise SystemExit(main())
