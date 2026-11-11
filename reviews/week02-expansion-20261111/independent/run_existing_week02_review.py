from pathlib import Path
from fractions import Fraction as F
from math import sqrt
from datetime import datetime, timezone
import contextlib, hashlib, importlib.metadata, io, json, os, shutil, subprocess, sys
import nbformat

REPO = Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision')
SOURCE = REPO/'lessons/week02'
OUT = Path(__file__).resolve().parent
PYTHON = Path('/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python')
NAMES = ['week02_prediction_evaluation.ipynb','teacher_validate_week02.py','teacher-notes.md']
raw = {name:(SOURCE/name).read_bytes() for name in NAMES}
hashes = {name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
original = nbformat.reads(raw[NAMES[0]].decode(), as_version=4)
nbformat.validate(original)
(OUT/'source-original.ipynb').write_bytes(raw[NAMES[0]])

def run_case(name, replacement=None, fill_answer=False):
    folder=OUT/'cases'/name
    folder.mkdir(parents=True,exist_ok=True)
    for filename,value in raw.items(): (folder/filename).write_bytes(value)
    for generated in ('week02_prediction_evaluation.html','validation.json'):
        (folder/generated).unlink(missing_ok=True)
    replacements=0
    if replacement or fill_answer:
        book=nbformat.reads(raw[NAMES[0]].decode(),as_version=4)
        if replacement:
            before,after=replacement
            for cell in book.cells:
                if cell.cell_type!='code': continue
                replacements+=cell.source.count(before)
                cell.source=cell.source.replace(before,after)
            assert replacements==1,(name,replacements)
        if fill_answer:
            answer=next(c for c in book.cells if c.cell_type=='code' and c.source.startswith('# 혼자 작성하는 공간'))
            answer.source += '\nx_student = 1\n'
        nbformat.write(book,folder/NAMES[0])
    runtime=OUT/'runtime'/name
    runtime.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1',IPYTHONDIR=str(runtime/'ipython'),MPLCONFIGDIR=str(runtime/'matplotlib'),JUPYTER_RUNTIME_DIR=str(runtime/'jupyter'),XDG_CACHE_HOME=str(runtime/'cache'))
    cmd=[str(PYTHON),'-B',str(folder/'teacher_validate_week02.py'),'--inprocess']
    result=subprocess.run(cmd,cwd=folder,env=env,capture_output=True,text=True,timeout=60)
    (folder/'stdout.txt').write_text(result.stdout)
    (folder/'stderr.txt').write_text(result.stderr)
    return {'name':name,'command':cmd,'returncode':result.returncode,'replacements':replacements,'detected':result.returncode!=0,'stdout_tail':result.stdout[-800:],'stderr_tail':result.stderr[-1200:]}

execution=run_case('original')
assert execution['returncode']==0,execution
executed=nbformat.read(OUT/'cases/original'/NAMES[0],as_version=4)
outputs=[{'index':i,'id':c.id,'source':c.source,'outputs':c.get('outputs',[])} for i,c in enumerate(executed.cells) if c.cell_type=='code']
(OUT/'executed-cell-evidence.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+'\n')
ns={}
with contextlib.redirect_stdout(io.StringIO()):
    for i,cell in enumerate(original.cells):
        if cell.cell_type=='code': exec(compile(cell.source,f'original:cell{i}','exec'),ns)
assert ns['known_train'].row_id.tolist()==['a1','a2','b1','b2']
assert set(ns['train'].group).isdisjoint(ns['validation'].group)
assert ns['records'].row_id.is_unique
assert set(ns['records'].group)==set('ABCD')
mean=F(2+4+6,3)
filled=[F(2),F(4),F(6),mean]
variance=sum((x-mean)**2 for x in filled)/4
assert mean==4 and variance==2
manual_z=[float((x-mean)/sqrt(variance)) for x in [F(20),mean,F(10),F(12)]]
assert ns['np'].allclose(ns['val_z'][:,0],manual_z)
manual_pred=[1 if z>=1 else -1 for z in manual_z]
assert manual_pred==[1,-1,1,1] and ns['rule_pred'].tolist()==manual_pred
actual=ns['y_val'].tolist()
counts={key:sum((a,p)==pair for a,p in zip(actual,manual_pred)) for key,pair in {'TN':(-1,-1),'FP':(-1,1),'FN':(1,-1),'TP':(1,1)}.items()}
assert counts=={'TN':0,'FP':2,'FN':1,'TP':1}
assert F(counts['TP'],counts['TP']+counts['FP'])==F(1,3)
assert F(counts['TP'],counts['TP']+counts['FN'])==F(1,2)
assert ns['np'].isnan(ns['p_nan']) and ns['r_nan']==0
state_before={name:[step.statistics_.copy() if hasattr(step,'statistics_') else step.mean_.copy() for key,step in ns[name].steps if key in ('imputer','scaler')] for name in ('preprocess','baseline')}
extreme=ns['pd'].DataFrame({'reading':[1e12,float('nan'),-1e12]})
ns['preprocess'].transform(extreme);ns['baseline'].predict(extreme)
for name in state_before:
    after=[step.statistics_.copy() if hasattr(step,'statistics_') else step.mean_.copy() for key,step in ns[name].steps if key in ('imputer','scaler')]
    assert all(ns['np'].array_equal(a,b) for a,b in zip(state_before[name],after))
reverse=ns['validation'].iloc[::-1]
reverse_pred=ns['np'].where(ns['preprocess'].transform(reverse[['reading']])[:,0]>=1,1,-1)
assert dict(zip(reverse.row_id,reverse_pred))==dict(zip(ns['validation'].row_id,ns['rule_pred']))
# Extra zero-denominator cases, using fixed label order even when a class is absent.
zeros=[]
for y,p in [([-1,-1],[-1,-1]),([-1,-1],[-1,1]),([-1,1],[-1,-1])]:
    precision,recall,f1,_=ns['precision_recall_fscore_support'](y,p,labels=[-1,1],pos_label=1,average='binary',zero_division=ns['np'].nan)
    zeros.append({'truth':y,'pred':p,'precision':str(precision),'recall':str(recall),'f1':str(f1)})
assert zeros[0]['precision']=='nan' and zeros[0]['recall']=='nan' and zeros[0]['f1']=='nan'
assert zeros[1]['precision']=='0.0' and zeros[1]['recall']=='nan'
# Exact independent new-table calculation predates reading the teacher key.
new_mean=F(3+6+9,3);new_filled=[F(3),F(6),F(9),new_mean]
new_variance=sum((x-new_mean)**2 for x in new_filled)/4
new_pred=[1 if (v-new_mean)/sqrt(new_variance)>=1 else -1 for v in [F(99),new_mean,new_mean,new_mean]]
assert new_mean==6 and new_variance==F(9,2) and new_pred==[1,-1,-1,-1]
new_exact={'fit_row_ids':['m1','m2','n1','n2'],'mean':str(new_mean),'population_variance':str(new_variance),'sigma':sqrt(new_variance),'leaky_mean':str(F(3+6+9+99,4)),'predictions':new_pred,'confusion_matrix':[[2,0],[1,1]],'accuracy':'3/4','precision':'1','recall':'1/2','F1':'2/3','group_XY_row_mean':str(F(4,8)),'group_XY_equal_mean':str((F(3,3)+F(1,5))/2)}
answer=next(c for c in original.cells if c.cell_type=='code' and c.source.startswith('# 혼자 작성하는 공간'))
assert all(not line.strip() or line.lstrip().startswith('#') for line in answer.source.splitlines())
assert not answer.outputs
mutations={
 'leaky_preprocess':('train_z = preprocess.fit_transform(X_train)','train_z = preprocess.fit_transform(pd.concat([X_train, X_val]))'),
 'include_unknown_train':('known_train = train[train["label"].isin([-1, 1])].copy()','known_train = train.copy()'),
 'reverse_confusion_labels':('rule_cm = confusion_matrix(y_val, rule_pred, labels=[-1, 1])','rule_cm = confusion_matrix(y_val, rule_pred, labels=[1, -1])'),
 'swap_precision_recall':('precision, recall, f1, _ =','recall, precision, f1, _ ='),
 'leaky_baseline_fit':('baseline.fit(X_train, known_train["label"])','baseline.fit(X_val, validation["label"])'),
 'invert_roc_threshold':('pred = np.where(roc_scores >= threshold, 1, -1)','pred = np.where(roc_scores < threshold, 1, -1)'),
}
mutation_results=[run_case(name,pair) for name,pair in mutations.items()]
assert all(case['detected'] for case in mutation_results),mutation_results
answer_guard=run_case('filled_assignment_answer',fill_answer=True)
assert answer_guard['detected'], answer_guard
source_after={name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in NAMES}
report={'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256_before':hashes,'source_sha256_after':source_after,'source_unchanged_during_review':hashes==source_after,'python':str(PYTHON),'versions':{name:importlib.metadata.version(name) for name in ('numpy','pandas','scikit-learn','ipykernel','nbformat','nbclient')},'execution':execution,'original_code_cells':len(outputs),'student_answer_code_is_comment_only':True,'student_answer_output_empty':True,'student_performance':'not_observed','class_120_minutes':'sum_checked_not_measured','self_study_360_to_480_minutes':'sum_checked_not_measured','independent_exact_main':{'mean':str(mean),'variance':str(variance),'validation_z':manual_z,'prediction':manual_pred,'counts':counts},'independent_exact_new':new_exact,'extra_zero_division_cases':zeros,'fit_state_extreme_validation_invariance':'passed','row_id_reverse_order_consistency':'passed','six_mutations':mutation_results,'extra_answer_guard_mutation':answer_guard,'unverified':['real learner independent performance and time','ordinary socket Jupyter kernel and Colab','timestamp-based splitting, forward-fill and sliding-window execution','median, one-hot and min-max homework implementation','week04 final test procedure','visual browser or printed rendering'],'scope':'finite synthetic foundation; not whole week02 practical mastery'}
(OUT/'week02-review-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'source_sha256':hashes,'source_unchanged':report['source_unchanged_during_review'],'kernel_execution':'passed','code_cells':len(outputs),'six_mutations_detected':[case['name'] for case in mutation_results if case['detected']],'filled_assignment_guard_detected':answer_guard['detected'],'review_json':str(OUT/'week02-review-results.json')},ensure_ascii=False,indent=2))

# These paths are generated only inside this independent review directory.
shutil.rmtree(OUT/'runtime', ignore_errors=True)
for case_folder in (OUT/'cases').iterdir():
    (case_folder/'week02_prediction_evaluation.html').unlink(missing_ok=True)
    (case_folder/'teacher-notes.md').unlink(missing_ok=True)
