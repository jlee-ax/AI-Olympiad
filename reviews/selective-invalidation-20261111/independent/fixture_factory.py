"""Reviewer-written fictional software fixture, never a real educator/student review."""
from pathlib import Path
import copy,json,hashlib,subprocess
BASELINE='76b680d64548af5c87d0455008b25358af06a698'
REPO=Path(__file__).resolve().parents[3]
def make_fixture(q,root,record_context=True):
    root=Path(root);root.mkdir(parents=True,exist_ok=False)
    for name in [q.CATALOG,q.CONTRACT,'curriculum/student-plan.html',q.UNIT_SPECIFICATIONS,q.THEORY_SPECIFICATION]:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(subprocess.check_output(['git','show',BASELINE+':'+name],cwd=REPO))
    contract=q.load(root/q.CONTRACT)
    # Explicitly fresh FICTIONAL baseline; never update the actual contract or old records.
    contract['baseline']['sha256']=q.file_digest(root/'curriculum/student-plan.html')
    (root/q.CONTRACT).write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
    for key in ['a','b','unused']:
        p=root/'sources'/(key+'.txt');p.parent.mkdir(exist_ok=True);p.write_text('Fictional '+key+' source v1; software control only.\n')
    (root/'receipt.json').write_text('{"synthetic":true,"meaning":"Fictional fixture; no learner, author review or user consent."}\n')
    ev=[{'locator':'fictional software control receipt','observation':'Explicit synthetic record, not education or authentic source-reading evidence.','path':'receipt.json','sha256':q.file_digest(root/'receipt.json')}]
    cells=[]
    for branch in ['a','b']:
        for role in ['intro','formula','code','assessment']:
            cells.append({'id':branch+'-'+role,'cell_type':'code' if role=='code' else 'markdown','metadata':{},'source':[branch+' '+role+' fictional region\n'],**({'outputs':[],'execution_count':None} if role=='code' else {})})
    cells.append({'id':'unrelated','cell_type':'markdown','metadata':{},'source':['Unrelated fictional cell.\n']})
    (root/'lesson.ipynb').write_text(json.dumps({'cells':cells,'metadata':{},'nbformat':4,'nbformat_minor':5},ensure_ascii=False,indent=2)+'\n')
    template=json.loads(subprocess.check_output(['git','show',BASELINE+':templates/quality.json'],cwd=REPO))
    template.update(synthetic=True,revision='independent-fictional-control-v1',author_id='fictional-author')
    artifact={'id':'fictional-lesson','revision':'v1','path':'lesson.ipynb','sha256':q.file_digest(root/'lesson.ipynb')};template['artifact']=artifact
    template['target'].update(competition_year=2027,division='middle_school',coverage_claim='selected_scope',objective_ids=['demo:a','demo:b'])
    template['budget']={'max_attempts':8,'max_elapsed_minutes':90,'max_no_progress':3}
    template['policy'].update(calibration_tolerance={'false_rejects':0,'missed_faults':0},maximum_required_homework_minutes=None)
    units=[];claims=[];nodes=[];reads=[];reviews=[];cycles=[];allocations=[]
    for branch,week,scope,concept in [('a',1,'KOAI-02','axis_mean'),('b',2,'KOAI-19','binary_metrics')]:
        uid='demo:'+branch;cid='claim:'+branch;sid='source:'+branch
        oracle=({'kind':'axis_mean','input':[[0,4],[6,10]],'axis':0,'expected':[3,7]} if branch=='a' else {'kind':'binary_metrics','tp':2,'fp':1,'fn':1,'tn':2,'zero_division':0,'expected':{'accuracy':2/3,'precision':2/3,'recall':2/3,'f1':2/3}})
        # expected key is kept on the claim, as the quality oracle protocol requires.
        claim={'id':cid,'statement':'Fictional '+concept+' claim.','domain':'Finite synthetic values','quantity':concept,'assumptions':['Software fixture only'],'source_ids':[sid],'locator':'cell:'+branch+'-formula','oracle':oracle}
        unit={'id':uid,'week':week,'locator':'cell:'+branch+'-intro','syllabus_ids':[scope],'concept_ids':[concept],'claim_ids':[cid],'claimed_depth':'independent','oracle_kinds':[concept],
          'explanation_checks':['T01','T02','T03','T04','T05'],'explanation_regions':{t:['cell:'+branch+'-intro'] for t in ['T01','T02','T03','T04','T05']},
          'mode_evidence':{'theory':'passed','practical':'passed'},
          'prerequisites':[{'id':'fictional-input','task':'Trace synthetic values.','expected':'State values.','observed':'Fictional matching response.','help':'none','status':'passed','evidence':ev}],
          'chain':{role:{'concept_ids':[concept],'locator':'cell:'+branch+'-'+loc,'expected_behavior':'Fictional corresponding behavior.','activity_id':'w'+str(week)+':'+('noncoding' if role=='assessment' else role),'help':'none','new_input':True} for role,loc in [('theory','intro'),('noncoding','formula'),('coding','code'),('assessment','assessment')]},
          'execution':{'status':'passed','artifact_sha256':artifact['sha256'],'command':'FICTIONAL fixture; no lesson worker executed','environment':'synthetic','exit_code':0,'clean_run':True,'new_input':True,'assertions':[{'name':'fictional assertion','status':'passed'}],'evidence':ev},
          'calibration':[{'case_id':'fictional-good-'+branch,'expected':'passed','observed':'passed','evidence':ev},{'case_id':'fictional-fault-'+branch,'expected':'failed','observed':'failed','evidence':ev}]}
        units.append(unit);claims.append(claim)
        reads.append({'id':sid,'kind':'documentation','url':'https://example.invalid/'+branch,'version':'fictional-v1','extent':'relevant_sections','accessed_at':'2026-11-11','locator':'fictional source','finding':'Synthetic declaration only.','limitation':'No actual source read.'})
        nodes.extend([{'id':sid,'revision':'fictional-v1','sha256':q.file_digest(root/'sources'/(branch+'.txt')),'path':'sources/'+branch+'.txt','depends_on':[]},{'id':cid,'revision':'fictional-v1','sha256':q.digest(claim),'depends_on':[sid]},{'id':uid,'revision':'fictional-v1','sha256':q.digest(unit),'depends_on':[cid]}])
        for criterion,oid in [('K02',uid),('K05',uid),('K06',cid),('K09',uid),('K15',uid),('K16',uid)]:
            r={'id':'fictional-review:'+branch+':'+criterion,'criterion_id':criterion,'object_id':oid,'status':'passed','reviewer_id':'fictional-other-reviewer','reason':'Synthetic current-context software control only.','evidence':copy.deepcopy(ev)}
            if criterion=='K16':r['subchecks']={t:{'status':'passed','artifact_locators':['cell:'+branch+'-intro'],'evidence':copy.deepcopy(ev)} for t in ['T01','T02','T03','T04','T05']}
            reviews.append(r)
        cycles.append({'id':'fictional-cycle:'+branch,'trigger':'software control','queries':['fictional '+branch],'source_ids':[sid],'object_ids':[cid],'disposition':'unchanged','reason':'Fictional declaration.'})
        times={1:[20,20,80],2:[30,30,60]}[week]
        allocations.append({'week':week,'outside_work':[{'id':'fictional-required-'+branch,'required':True,'minutes':420 if week==1 else 480}],'blocks':[{'id':'w'+str(week)+':'+kind,'kind':kind,'minutes':minutes,'written_minutes':10 if kind=='noncoding' else 0} for kind,minutes in zip(['theory','noncoding','coding'],times)]})
    template.update(units=units,claims=claims,dependencies=nodes,source_reads=reads,reviews=reviews,research_cycles=cycles,lesson_allocations=allocations,candidates=[],attempts=[])
    if record_context:seed_records(q,template,root)
    return template

def seed_records(q,bundle,root):
    # Caller explicitly creates these FICTIONAL new records. Evaluators never do this to real records.
    for r in bundle['reviews']:r['context_fingerprint']=q.object_fingerprint(bundle,r['criterion_id'],r['object_id'],root)
    for cycle in bundle['research_cycles']:cycle['object_contexts']={oid:q.object_fingerprint(bundle,'K10',oid,root) for oid in cycle['object_ids']}
    bundle['policy'].update(agreed=True,decision_ref='FICTIONAL policy record, not user approval')
    bundle['policy']['agreement_fingerprint']=q.agreement_fingerprint(bundle,root)
