"""Read-only byte, payload, question and CLI verification; no semantic judgment."""
from __future__ import annotations
import ast,hashlib,json,pathlib,subprocess,sys,tarfile
ROOT=pathlib.Path(__file__).resolve().parents[3];OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(OUT));from rebind_integrated_review import loop,payloads
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    initial=read(OUT/'initial-read-only-state.json');context=read(OUT/'context-binding.json');selection=read(OUT/'current-run-selection.json')
    protected=[{'path':p,'initial_sha256':v,'current_sha256':sha(ROOT/p),'unchanged':sha(ROOT/p)==v} for p,v in initial['protected_history_files'].items()]
    contexts=[{**x,'current_sha256':sha(ROOT/x['path']),'unchanged':sha(ROOT/x['path'])==x['sha256']} for x in context['files']]
    current=set(selection['current_runs']);past=selection.get('historical_runs',{})
    paths=sorted((OUT/'runs').glob('*/session.json'));assert {p.parent.name for p in paths}==current|set(past)
    runs=[]
    for p in paths:
        f=p.parent;s=read(p);r=loop.inspect(s,ROOT);origin=read(f/'origin.json');prior=ROOT/origin['prior_session_path'];old=read(prior);old_r=loop.inspect(old,ROOT);carry=read(f/'bridge-question-carryover.json');bridge_p=ROOT/carry['prior_session_path'];bridge=read(bridge_p);bridge_r=loop.inspect(bridge,ROOT)
        prov=read(f/'projection-provenance.json');artifact=ROOT/prov['artifact_path'];snapshot=ROOT/prov['exact_snapshot_path'];projection=ROOT/prov['projection_path'];nb=read(snapshot);parts=[]
        for i,c in enumerate(nb['cells']):
            source=c.get('source',[]);text=source if isinstance(source,str) else ''.join(source)
            parts.append(f"## Cell {i}: {c.get('id','<missing>')} ({c['cell_type']})\n\n{text}\n\n")
        expected_questions={q['question'] for q in old_r['open_questions']}|{q['question'] for q in bridge_r['open_questions']}
        rebuilt=loop.initialize(read(f/'config.json'))
        for event_path in sorted((f/'events').glob('*.json')):rebuilt=loop.step(rebuilt,read(event_path),ROOT)
        static={'prior_session_file_unchanged':sha(prior)==origin['prior_session_file_sha256'],'all_nineteen_demand_payloads_exactly_preserved':payloads(s)==payloads(old) and len(payloads(s))==19,'bridge_demands_exact_subsets_no_duplicates':all(payloads(old)[k]==v for k,v in payloads(bridge).items()),'all_eight_original_question_texts_preserved':{q['question'] for q in r['open_questions']}==expected_questions and len(r['open_questions'])==8,'bridge_question_source_session_unchanged':sha(bridge_p)==carry['prior_session_file_sha256'],'bridge_question_mapping_exact':all(next(q for q in bridge_r['open_questions'] if q['id']==m['prior_question_id'])['question']==m['question']==next(q for q in r['open_questions'] if q['id']==m['new_question_id'])['question'] for m in carry['mapping']),'snapshot_matches_bound_sha':sha(snapshot)==prov['artifact_sha256']==r['scope']['artifact_sha256'],'projection_matches_every_snapshot_cell':projection.read_text()==''.join(parts),'projection_sha_matches_record':sha(projection)==prov['projection_sha256'],'findings_sha_matches_record':sha(ROOT/origin['findings_path'])==origin['findings_sha256'],'saved_event_inputs_reproduce_full_receipts_and_hash_chain':rebuilt==s,'saved_manifest_matches_replay':read(f/'manifest.json')==loop.manifest(s)}
        fresh={'actual_artifact_matches_binding':sha(artifact)==prov['artifact_sha256'],'snapshot_matches_current_raw_bytes':artifact.read_bytes()==snapshot.read_bytes(),'saved_report_matches_current_inspection':read(f/'report.json')==r,'no_artifact_source_or_projection_freshness_failure':not any(b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read') for b in r['blockers'])}
        cli=[]
        for command in ['report','next','manifest']:
            a=[sys.executable,'-B','tools/discovery_loop.py',command,str(p.relative_to(ROOT)),'--root','.'];proc=subprocess.run(a,cwd=ROOT,capture_output=True,text=True);actual=json.loads(proc.stdout)
            expected=r if command=='report' else loop.manifest(s) if command=='manifest' else {k:r[k] for k in ('authority','status','next_action','queue','usage','exhausted','limits')}
            cli.append({'command':a,'exit_code':proc.returncode,'stdout_sha256':hashlib.sha256(proc.stdout.encode()).hexdigest(),'equals_API_result':actual==expected});assert proc.returncode==0
        blanks=[{'cell_index':i,'cell_id':c['id'],'ast_statement_count':len(ast.parse(''.join(c['source'])).body)} for i,c in enumerate(nb['cells']) if c.get('id')=='e49ac1c2']
        runs.append({'run':f.name,'current':f.name in current,'session_path':str(p.relative_to(ROOT)),'session_file_sha256':sha(p),'artifact_sha256':r['artifact_sha256'],'bound_artifact_sha256':r['scope']['artifact_sha256'],'projection_sha256':sha(projection),'status':r['status'],'ready_for_review':r['ready_for_review'],'demand_count':len(r['demands']),'question_count':len(r['open_questions']),'queue_count':len(r['queue']),'covered':[c['demand_id'] for c in r['comparisons'] if c['judgment']=='covered'],'usage':r['usage'],'next_action':r['next_action'],'static_checks':static,'freshness_checks':fresh,'cli_checks':cli,'blank_answer_cells':blanks,'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')]})
    prior_current=[]
    for name in ['pipeline-final-01','bridge-navigation-01']:
        p=ROOT/'reviews/week01-pipeline-20261111/discovery/runs'/name/'session.json';r=loop.inspect(read(p),ROOT);prior_current.append({'run':name,'status':r['status'],'ready_for_review':r['ready_for_review'],'bound_sha256':r['scope']['artifact_sha256'],'actual_sha256':r['artifact_sha256'],'queue_count':len(r['queue']),'covered':[c['demand_id'] for c in r['comparisons'] if c['judgment']=='covered'],'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')]})
    context_calls=[]
    for c in read(OUT/'checks/context/calls.json'):
        proc=subprocess.run(c['argv'],cwd=ROOT,capture_output=True,text=True);value=json.loads(proc.stdout);saved=read(OUT/'checks/context'/str(c['name']+'.json'));context_calls.append({'name':c['name'],'exit_code':proc.returncode,'result_matches_recorded':value==saved,'status':value.get('status'),'reason':value.get('reason')})
    chains=read(OUT/'source-demand-evidence-next.json');final=read(OUT/'final-review-status.json')
    selected=OUT/'runs'/selection['current_runs'][0];selected_state=read(selected/'session.json');selected_view=loop.replay(selected_state);selected_report=loop.inspect(selected_state,ROOT)
    chain_checks={'session_file_binding':sha(selected/'session.json')==chains['session_file_sha256'],'every_demand_has_one_chain':{x['demand_id'] for x in chains['chains']}==set(selected_view['demands']) and len(chains['chains'])==len(selected_view['demands']),'exact_comparison_and_queue_copied':all(x['compare_event_id']==selected_view['comparisons'][x['demand_id']]['event_id'] and x['dimension_receipts_and_manual_judgments']==selected_view['comparisons'][x['demand_id']]['dimensions'] and x['queue_entry']==next((q for q in selected_report['queue'] if q['demand_id']==x['demand_id']),None) for x in chains['chains']),'independent_summary_bytes_match':sha(ROOT/final['independent_final_summary_path'])==final['independent_final_summary_sha256'],'independent_report_bytes_match':sha(ROOT/final['independent_report_path'])==final['independent_report_sha256'],'independent_final_sha_matches_current_artifact':read(ROOT/final['independent_final_summary_path'])['source_notebook_sha256']==selected_report['artifact_sha256']==final['bound_final_notebook_sha256']}
    ip=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=ROOT,text=True).strip());ip=ip if ip.is_absolute() else ROOT/ip
    archives=[]
    for p in sorted((OUT/'build-attempts').glob('*.manifest.json')):
        m=read(p);archive=OUT/m['archive'];items=[]
        with tarfile.open(archive,'r:gz') as t:
            for x in m['members']:
                raw=t.extractfile(x['path']).read();items.append(len(raw)==x['bytes'] and hashlib.sha256(raw).hexdigest()==x['sha256'])
        archives.append({'manifest':str(p.relative_to(ROOT)),'archive_sha_matches':sha(archive)==m['archive_sha256'],'every_member_bytes_and_sha_match':all(items)})
    history_ok=all(x['unchanged'] for x in protected);context_ok=all(x['unchanged'] for x in contexts) and all(x['result_matches_recorded'] and x['exit_code']==0 for x in context_calls)
    current_ok=all(all(x['static_checks'].values()) and all(x['freshness_checks'].values()) and all(c['exit_code']==0 and c['equals_API_result'] for c in x['cli_checks']) and len(x['blank_answer_cells'])==1 and all(c['ast_statement_count']==0 for c in x['blank_answer_cells']) for x in runs if x['current'])
    result={'authority':'advisory_only','all_protected_history_unchanged':history_ok,'protected_history_files':protected,'context_binding_current':context_ok,'context_files':contexts,'source_demand_evidence_next_checks':chain_checks,'context_cli_rechecks':context_calls,'runs':runs,'previous_artifact_scopes_still_separate':prior_current,'compressed_build_attempt_integrity':archives,'git_index_matches_initial':sha(ip)==initial['git_index_sha256'],'git_index_sha256':sha(ip),'all_current_mechanical_checks_passed':current_ok,'limits':['This script checks bytes, event replay, receipts, declared payloads/question text and deterministic CLI/API agreement. It neither browses primary sources nor decides semantic sufficiency.','The independent reviewer manually read all cell sources and authored nineteen findings. Distinct actor strings are structural declarations, not authenticated independence.','The extra context manifest is checked by this verifier, not automatically by the core discovery state.','No aggregate graph/path/semantic-preflight acceptance or quality/workflow agreement is created. Student learning and completion duration remain unobserved.']}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if history_ok and context_ok and current_ok and all(chain_checks.values()) and all(x['archive_sha_matches'] and x['every_member_bytes_and_sha_match'] for x in archives) else 2
if __name__=='__main__':raise SystemExit(main())
