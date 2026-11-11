"""Read-only byte, replay and preserved-obligation verification.
Current sessions and superseded historical sessions are selected explicitly.
No source search, semantic judgment, artifact or index writes occur here.
"""
from __future__ import annotations
import hashlib,json,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(OUT));from rebind_review import loop,payloads
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    pre=json.loads((OUT/'prechange-current-state.json').read_text());historical=[]
    for item in pre['sessions']:
        p=ROOT/item['path'];r=loop.inspect(json.loads(p.read_text()),ROOT)
        historical.append({'session_path':item['path'],'session_file_sha256':sha(p),'unchanged_from_prechange':sha(p)==item['file_sha256'],'bound_artifact_sha256':r['scope'].get('artifact_sha256'),'current_artifact_sha256':r['artifact_sha256'],'status':r['status'],'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')]})
    legacy_path=ROOT/'reviews/discovery-loop-20261111/runs/session.json'
    legacy_expected=json.loads((ROOT/'reviews/course-discovery-20261111/checks/final-03/integrity-and-execution-evidence.json').read_text())['prior_session_sha256']
    legacy={'session_path':str(legacy_path.relative_to(ROOT)),'expected_prior_sha256':legacy_expected,'current_sha256':sha(legacy_path),'unchanged_from_prior_final_review':sha(legacy_path)==legacy_expected}
    paths=sorted((OUT/'runs').glob('*/session.json'))
    selection_path=OUT/'current-run-selection.json'
    selection=json.loads(selection_path.read_text()) if selection_path.exists() else {'current_runs':[p.parent.name for p in paths],'historical_runs':{}}
    selected=set(selection['current_runs']);declared=set(selected)|set(selection['historical_runs']);actual={p.parent.name for p in paths}
    if declared!=actual:raise ValueError('Every run must be explicitly current or historical')
    runs=[];prior_runs=[]
    for p in paths:
        folder=p.parent;s=json.loads(p.read_text());r=loop.inspect(s,ROOT)
        origin=json.loads((folder/'origin.json').read_text());prior=ROOT/origin['prior_session_path'];old=json.loads(prior.read_text());old_r=loop.inspect(old,ROOT)
        prov=json.loads((folder/'projection-provenance.json').read_text());artifact=ROOT/prov['artifact_path'];snapshot=ROOT/prov['exact_snapshot_path'];projection=ROOT/prov['projection_path']
        nb=json.loads(snapshot.read_text());chunks=[]
        for i,c in enumerate(nb['cells']):
            source=c.get('source',[]);text=source if isinstance(source,str) else ''.join(source)
            chunks.append(f"## Cell {i}: {c.get('id','<missing>')} ({c['cell_type']})\n\n{text}\n\n")
        static={'prior_session_unchanged':sha(prior)==origin['prior_session_file_sha256'],'all_original_demand_payloads_retained':payloads(s)==payloads(old),'all_original_open_questions_retained':{q['question'] for q in r['open_questions']}=={q['question'] for q in old_r['open_questions']},'snapshot_matches_bound_artifact_sha':sha(snapshot)==prov['artifact_sha256']==r['scope']['artifact_sha256'],'projection_matches_every_snapshot_cell_source':projection.read_text()==''.join(chunks),'projection_matches_recorded_sha':sha(projection)==prov['projection_sha256'],'findings_match_recorded_sha':sha(ROOT/origin['findings_path'])==origin['findings_sha256']}
        freshness={'artifact_matches_final_binding':sha(artifact)==prov['artifact_sha256'],'snapshot_is_exact_current_bytes':artifact.read_bytes()==snapshot.read_bytes(),'saved_report_matches_current_inspection':json.loads((folder/'report.json').read_text())==r,'freshness_blockers_absent':not any(b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read') for b in r['blockers'])}
        item={'run':folder.name,'session_path':str(p.relative_to(ROOT)),'session_file_sha256':sha(p),'bound_artifact_sha256':prov['artifact_sha256'],'current_artifact_sha256':sha(artifact),'projection_sha256':sha(projection),'static_checks':static,'current_checks':freshness,'status':r['status'],'ready_for_review':r['ready_for_review'],'demand_count':len(r['demands']),'queue_count':len(r['queue']),'covered':[c['demand_id'] for c in r['comparisons'] if c['judgment']=='covered'],'events':r['usage']['events'],'open_question_count':len(r['open_questions']),'next_action':r['next_action'],'freshness_blockers':[b for b in r['blockers'] if b['code'] in ('artifact_changed','artifact_unreadable','stale_source_read')]}
        if folder.name in selected:runs.append(item)
        else:
            item['historical_disposition']=selection['historical_runs'][folder.name]
            item['historical_session_sha_matches_selection']=sha(p)==item['historical_disposition']['session_file_sha256'];prior_runs.append(item)
    index=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=ROOT,text=True).strip())
    if not index.is_absolute():index=ROOT/index
    history_ok=legacy['unchanged_from_prior_final_review'] and all(h['unchanged_from_prechange'] for h in historical) and all(h['historical_session_sha_matches_selection'] and all(h['static_checks'].values()) for h in prior_runs)
    current_ok=all(all(r['static_checks'].values()) and all(r['current_checks'].values()) for r in runs)
    result={'authority':'advisory_only','selection_path':str(selection_path.relative_to(ROOT)) if selection_path.exists() else None,'legacy_original_session':legacy,'historical_sessions':historical,'new_separate_baselines':runs,'superseded_rebound_sessions':prior_runs,'all_history_unchanged':history_ok,'all_new_mechanical_checks_passed':current_ok,'git_index_sha256':sha(index),'git_index_matches_prechange':sha(index)==pre['git_index_sha256'],'limits':['Every old session remains unchanged. A stale historical rebound is explicitly superseded for current reporting rather than erased or silently accepted.','Meaning judgments were authored by the reviewer after reading source text; this verification checks bytes, replay and declared obligation preservation only.','The original external searches were not rerun. A separate official ROC version-consistency read is recorded in its own auxiliary note.','No learner answers, independent performance or learning effects were observed.']}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if history_ok and current_ok else 2
if __name__=='__main__':raise SystemExit(main())
