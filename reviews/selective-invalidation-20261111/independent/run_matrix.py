from pathlib import Path
import subprocess,sys,json,hashlib,concurrent.futures,argparse
from candidate_support import OUT,write_json
p=argparse.ArgumentParser();p.add_argument('--code',required=True);p.add_argument('--prefix',required=True);a=p.parse_args();code=Path(a.code).resolve();sha=hashlib.sha256(code.read_bytes()).hexdigest()
names=['control','plan_week1','plan_week9','scope02','scope60','outside_global_p','style_only','bound_code','bound_output','unrelated_cell','execution_counter','source_a_changed','source_a_missing','source_read_version','source_unused_changed','source_path_changed','evidence_changed','evidence_missing','undeclared_plan','disconnected_plan','missing_source_node','missing_claim_source_edge','unrelated_repin','shared_source','append_current','append_failed','append_uncertain','append_not_run','append_stale','retired_history','source_symlink_escape']
def run(name):
    proc=subprocess.run([sys.executable,'-B',str(OUT/'case_worker.py'),'--code',str(code),'--sha',sha,'--case',name,'--prefix',a.prefix],capture_output=True,text=True,timeout=90)
    parent=OUT/'cases'/(a.prefix+'-'+name);parent.mkdir(parents=True,exist_ok=True);(parent/'worker-stdout.txt').write_text(proc.stdout);(parent/'worker-stderr.txt').write_text(proc.stderr)
    result_path=parent/'result.json'
    if result_path.exists():r=json.loads(result_path.read_text());return {'case':name,'status':r['status'],'process_exit':proc.returncode,'result':str(result_path.relative_to(OUT)),'error':r.get('error') or r.get('evaluate_error')}
    return {'case':name,'status':'harness_or_setup_error','process_exit':proc.returncode,'stderr':proc.stderr}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,names))
summary={'code_sha256':sha,'prefix':a.prefix,'cases':results,'all_cases_expected':all(r['status'].startswith('passed') for r in results),'new_subprocess_per_case':True,'fictional_controls_not_real_review_or_learner_evidence':True}
write_json(OUT/(a.prefix+'-matrix-results.json'),summary);print(json.dumps(summary,ensure_ascii=False,indent=2))
sys.exit(0 if summary['all_cases_expected'] else 1)
