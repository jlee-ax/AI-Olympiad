"""One independent selective-invalidation case in its own process; fictional roots only."""
from pathlib import Path
import argparse,copy,hashlib,json,sys,subprocess
from candidate_support import OUT,REPO,load_candidate,bound_fixture,review,captures,write_json
p=argparse.ArgumentParser();p.add_argument('--code',required=True);p.add_argument('--sha',required=True);p.add_argument('--case',required=True);p.add_argument('--prefix',required=True);a=p.parse_args()
code=Path(a.code).resolve();assert hashlib.sha256(code.read_bytes()).hexdigest()==a.sha
q=load_candidate(code);case_dir=OUT/'cases'/(a.prefix+'-'+a.case);root=case_dir/'root';b=bound_fixture(q,root)
def refresh_fictional():
    for r in b['reviews']:
        r['context_fingerprint']=q.object_fingerprint(b,r['criterion_id'],r['object_id'],root)
        r['dependency_scope_fingerprint']=q.plan_bindings(b,r['object_id'],root)['scope_fingerprint']
        r['context_bindings']=q.context_bindings(b,r['object_id'],root)
    for cyc in b['research_cycles']:cyc['object_contexts']={oid:q.object_fingerprint(b,'K10',oid,root) for oid in cyc['object_ids']}
def replace_row(row_id):
    path=root/'curriculum/student-plan.html';text=path.read_text();needle='id="'+row_id+'"';start=text.index(needle);end=text.index('</tr>',start)
    path.write_text(text[:end]+'<td>Independent structural change.</td>'+text[end:])
def touch_cell(cid,key='source'):
    path=root/'lesson.ipynb';n=q.load(path);c=next(c for c in n['cells'] if c['id']==cid)
    if key=='source':c['source'].append('Independently changed source.\n')
    elif key=='outputs':c['outputs']=[{'output_type':'stream','name':'stdout','text':'Changed displayed output.\n'}]
    else:c['execution_count']=99
    write_json(path,n)
expected=('current','current');expect_eval_error=False;special={}
if a.case=='control':pass
elif a.case=='plan_week1':replace_row('week-1');expected=('review_required','current')
elif a.case=='plan_week9':replace_row('week-9')
elif a.case=='scope02':replace_row('scope-02');expected=('review_required','current')
elif a.case=='scope60':replace_row('scope-60')
elif a.case=='outside_global_p':
    path=root/'curriculum/student-plan.html';path.write_text(path.read_text().replace('</main>','<p>New global declared requirement.</p></main>'));expected=('review_required','review_required')
elif a.case=='style_only':
    path=root/'curriculum/student-plan.html';path.write_text(path.read_text().replace('</style>','/* independent cosmetic stylesheet */\n</style>'))
elif a.case=='bound_code':touch_cell('a-code');expected=('review_required','current')
elif a.case=='bound_output':touch_cell('a-code','outputs');expected=('review_required','current')
elif a.case=='unrelated_cell':touch_cell('unrelated')
elif a.case=='execution_counter':touch_cell('a-code','execution_count')
elif a.case=='source_a_changed':(root/'sources/a.txt').write_text('Changed declared source bytes.');expected=('review_required','current')
elif a.case=='source_a_missing':(root/'sources/a.txt').unlink();expected=('review_required','current')
elif a.case=='source_read_version':b['source_reads'][0]['version']='fictional-v2';expected=('review_required','current')
elif a.case=='source_unused_changed':(root/'sources/unused.txt').write_text('Unregistered file changed; meaning unknown to inspector.')
elif a.case=='source_path_changed':
    (root/'sources/a-v2.txt').write_bytes((root/'sources/a.txt').read_bytes());next(n for n in b['dependencies'] if n['id']=='source:a')['path']='sources/a-v2.txt';expected=('review_required','current')
elif a.case=='evidence_changed' or a.case=='evidence_missing':
    path=root/'review-a.txt';path.write_text('A-only fictional review evidence.');r=review(b);r['evidence']=[{'path':'review-a.txt','sha256':q.file_digest(path),'locator':'fictional A evidence','observation':'software control only'}]
    assert q.review_freshness(b,r,root)['status']=='current'
    if a.case=='evidence_changed':path.write_text('Changed fictional review evidence.')
    else:path.unlink()
    expected=('review_required','current')
elif a.case=='undeclared_plan':
    next(u for u in b['units'] if u['id']=='demo:a').pop('plan_dependency_ids');expected=('binding_required','current')
elif a.case=='disconnected_plan':
    next(n for n in b['dependencies'] if n['id']=='demo:a')['depends_on'].remove('plan:a');expected=('binding_required','current')
elif a.case=='missing_source_node':
    b['dependencies']=[n for n in b['dependencies'] if n['id']!='source:a'];expect_eval_error=True
elif a.case=='missing_claim_source_edge':
    next(n for n in b['dependencies'] if n['id']=='claim:a')['depends_on']=[];expect_eval_error=True
elif a.case=='unrelated_repin':
    replace_row('week-9')
    for n in b['dependencies']:
        if n['id'].startswith('plan:'):n.update(revision='whole-file-provenance-v2',sha256=q.file_digest(root/n['path']))
elif a.case=='shared_source':
    next(u for u in b['units'] if u['id']=='demo:b')['claim_ids'].append('claim:a');next(n for n in b['dependencies'] if n['id']=='demo:b')['depends_on'].append('claim:a');refresh_fictional()
    (root/'sources/a.txt').write_text('Shared source changed.');expected=('review_required','review_required')
elif a.case=='append_current':
    (root/'sources/a.txt').write_text('Source changed before a fictional independent new review.')
    old=review(b);r=copy.deepcopy(old);r['id']+=':new';r['context_fingerprint']=q.object_fingerprint(b,r['criterion_id'],r['object_id'],root);r['context_bindings']=q.context_bindings(b,r['object_id'],root);r['dependency_scope_fingerprint']=q.plan_bindings(b,r['object_id'],root)['scope_fingerprint'];b['reviews'].append(r);special={'old_id':old['id'],'new_id':r['id']}
elif a.case in ['append_failed','append_uncertain','append_not_run','append_stale']:
    r=copy.deepcopy(review(b));r['id']+=':'+a.case
    if a.case=='append_stale':r['context_fingerprint']='0'*64;expected=('review_required','current')
    else:r['status']=a.case.removeprefix('append_')
    b['reviews'].append(r);special={'latest_id':r['id'],'recorded_status':r['status']}
elif a.case=='retired_history':
    r=copy.deepcopy(review(b));r.update(id='fictional-review:retired',object_id='retired:unit',context_fingerprint='0'*64);b['reviews'].append(r)
elif a.case=='source_symlink_escape':
    outside=case_dir/'outside.txt';outside.parent.mkdir(parents=True,exist_ok=True);outside.write_text('Fictional outside-root canary.');(root/'sources/escape.txt').symlink_to(outside.resolve());next(n for n in b['dependencies'] if n['id']=='source:a')['path']='sources/escape.txt';expected=('review_required','current')
else:raise ValueError('unknown case '+a.case)
write_json(case_dir/'bundle.json',b);before=copy.deepcopy(b)
files_before={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file() and not f.is_symlink()}
output={'case':a.case,'code_sha256':a.sha,'expected_statuses':list(expected),'fictional_control':True,'status':'running'}
try:
    try:
        fs=captures(q,b,root);output['freshness']=fs
        if not expect_eval_error:assert tuple(fs[k]['status'] for k in ['demo:a','demo:b'])==expected,{k:v['status'] for k,v in fs.items()}
    except ValueError as e:
        if not expect_eval_error:raise
        output['freshness_input_error']=str(e)
    try:
        report=q.evaluate(b,root);output['report_status']=report['status'];output['ready_for_review']=report['ready_for_review'];output['checks']={c['id']:c['status'] for c in report['checks']};output['selective_review']=report.get('selective_review');write_json(case_dir/'evaluate.json',report)
        assert not expect_eval_error,'invalid dependency graph was accepted'
        assert isinstance(report.get('selective_review'),dict),'ordinary evaluate lacks selective review result'
        if a.case=='control':assert report['ready_for_review']
        if a.case in ['plan_week9','scope60','unrelated_cell','execution_counter','style_only','unrelated_repin']:assert output['checks']['K01']=='failed' and not report['ready_for_review'],'global binding guard weakened'
        if a.case=='append_current':
            assert q._review(b,'K05','demo:a',root)=='passed';assert special['old_id'] in report['selective_review']['historical_review_ids'];assert special['new_id'] in report['selective_review']['active_review_ids']
        if a.case in ['append_failed','append_uncertain','append_not_run']:assert q._review(b,'K05','demo:a',root)==special['recorded_status']
        if a.case=='append_stale':assert q._review(b,'K05','demo:a',root)=='uncertain'
        planned=q.plan_work(b,root);assert planned.get('selective_review')==report['selective_review'];write_json(case_dir/'plan.json',planned)
        output['status']='passed'
    except (ValueError,OSError) as error:
        output['evaluate_error']={'type':type(error).__name__,'message':str(error)}
        if expect_eval_error:output['status']='passed_expected_invalid'
        else:output['status']='failed_missing_regular_path_diagnostics'
    command=[sys.executable,'-B',str(code),'evaluate',str(case_dir/'bundle.json'),'--root',str(root)]
    proc=subprocess.run(command,capture_output=True,text=True);output['cli_exit']=proc.returncode
    (case_dir/'cli-stdout.json').write_text(proc.stdout);(case_dir/'cli-stderr.txt').write_text(proc.stderr);cli=json.loads(proc.stdout)
    if output['status']=='passed':assert cli.get('selective_review')==output['selective_review'],'CLI/API selective results differ'
    elif expect_eval_error:assert proc.returncode==2 and cli['status']=='blocked'
except Exception as error:
    output.update(status='failed',error={'type':type(error).__name__,'message':str(error)})
finally:
    output['bundle_unchanged_by_inspection']=b==before
    output['files_unchanged_by_inspection']=files_before=={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file() and not f.is_symlink()}
    if not output['bundle_unchanged_by_inspection'] or not output['files_unchanged_by_inspection']:output['status']='failed_read_only'
    write_json(case_dir/'result.json',output)
print(json.dumps({'case':a.case,'status':output['status'],'freshness':{k:v['status'] for k,v in output.get('freshness',{}).items()},'error':output.get('error') or output.get('evaluate_error')},ensure_ascii=False))
sys.exit(0 if output['status'].startswith('passed') else 1)
