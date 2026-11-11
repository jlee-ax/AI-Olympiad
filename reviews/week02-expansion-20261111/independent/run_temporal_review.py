from pathlib import Path
from fractions import Fraction as F
from math import sqrt,isnan
from datetime import datetime,timezone
import ast,base64,contextlib,hashlib,io,json,os,re,shutil
ROOT=Path(__file__).resolve().parent
REPO=Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision')
SOURCE=REPO/'lessons/week02'
NAMES=['week02_temporal_preprocessing.ipynb','week02_temporal_preprocessing.html','week02_temporal_preprocessing_teacher.md','validate_week02_temporal_preprocessing.py']
raw={name:(SOURCE/name).read_bytes() for name in NAMES}
sha={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
runtime=ROOT/'temporal-runtime';runtime.mkdir(exist_ok=True)
os.environ.update(IPYTHONDIR=str(runtime/'ipython'),MPLCONFIGDIR=str(runtime/'matplotlib'),JUPYTER_RUNTIME_DIR=str(runtime/'jupyter'),XDG_CACHE_HOME=str(runtime/'cache'),PYTHONDONTWRITEBYTECODE='1',MPLBACKEND='Agg')
import nbformat
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_curve,roc_auc_score
from sklearn.preprocessing import OneHotEncoder,MinMaxScaler
from ipykernel.inprocess.manager import InProcessKernelManager
from nbconvert import HTMLExporter
from bs4 import BeautifulSoup
book=nbformat.reads(raw[NAMES[0]].decode(),as_version=4);nbformat.validate(book)
original=nbformat.reads(raw[NAMES[0]].decode(),as_version=4)
source_copy=ROOT/'temporal-source';source_copy.mkdir(exist_ok=True)
for name,data in raw.items():(source_copy/name).write_bytes(data)
manager=InProcessKernelManager();manager.start_kernel();shell=manager.kernel.shell
client=manager.client();client.start_channels()
def execute_cell(cell):
 client.execute(cell.source,store_history=True);reply=client.get_shell_msg(timeout=90)
 assert reply['content']['status']=='ok',reply
 cell.execution_count=reply['content']['execution_count'];cell.outputs=[]
 while True:
  msg=client.get_iopub_msg(timeout=90)
  if msg['msg_type']=='status' and msg['content'].get('execution_state')=='idle':break
  if msg['msg_type'] in ('stream','display_data','execute_result','error'):cell.outputs.append(nbformat.v4.output_from_msg(msg))
 assert not any(o.output_type=='error' for o in cell.outputs)
execute_cell(nbformat.v4.new_code_cell('%matplotlib inline'))
executed=[]
for i,cell in enumerate(book.cells):
 if cell.cell_type=='code':
  execute_cell(cell)
  executed.append({'index':i,'id':cell.id,'count':cell.execution_count,'text':''.join(o.get('text','') for o in cell.outputs)})
ns=shell.user_ns
make=ns['make_features'];counts=ns['counts_at'];rates=ns['rates']
checks=[]
def passed(name):checks.append(name)
def equal_number(a,b):return (pd.isna(a) and pd.isna(b)) or np.isclose(float(a),float(b),rtol=1e-11,atol=1e-11)
def oracle_features(records,targets):
 rows=[];provenance=[]
 for target in targets.to_dict('records'):
  available=sorted([r for r in records.to_dict('records') if r['unit']==target['unit'] and r['time']<target['time']],key=lambda r:r['time'])
  observed=[r for r in available if not pd.isna(r['reading'])]
  recent=observed[-1]['reading'] if observed else np.nan
  last=observed[-3:]
  if len(last)==3:
   vals=[F(str(r['reading'])) for r in last];mean=sum(vals)/3;var=sum((v-mean)**2 for v in vals)/3
   m,s=float(mean),sqrt(float(var))
  else:m=s=np.nan
  rows.append({'id':target['id'],'recent':recent,'mean3':m,'std3':s,'kind':target['kind']})
  provenance.append({'id':target['id'],'unit':target['unit'],'target_time':target['time'],'allowed_times':[r['time'] for r in available],'window_times':[r['time'] for r in last] if len(last)==3 else []})
 return pd.DataFrame(rows).set_index('id'),provenance
provenance={}
for name,targets in [('train',ns['train_targets']),('validation',ns['val_targets'])]:
 expected,trace=oracle_features(ns['records'],targets);actual=make(ns['records'],targets)
 assert actual.index.tolist()==expected.index.tolist()
 for col in ['recent','mean3','std3']:assert all(equal_number(a,b) for a,b in zip(actual[col],expected[col])),(name,col)
 assert actual.kind.tolist()==expected.kind.tolist();provenance[name]=trace
passed('all worked feature values and source times match independent list/Fraction implementation')
# Every target is invariant to current/future values and to other units.
for target in pd.concat([ns['train_targets'],ns['val_targets']]).to_dict('records'):
 row=pd.DataFrame([target]);before=make(ns['records'],row)
 changed=ns['records'].copy();mask=(changed.unit!=target['unit']) | (changed.time>=target['time'])
 changed.loc[mask,'reading']=np.arange(mask.sum())+1e8
 pd.testing.assert_frame_equal(before,make(changed,row))
 current=ns['records'].loc[(ns['records'].unit==target['unit']) & (ns['records'].time<target['time'])]
 pd.testing.assert_frame_equal(before,make(current,row))
for seed in range(20):pd.testing.assert_frame_equal(ns['val_x'],make(ns['records'].sample(frac=1,random_state=seed),ns['val_targets']))
passed('strict current/future and cross-unit exclusion, full/prefix equality, 20 shuffled inputs')
# Online and batch contracts intentionally differ for t7.
batch=make(ns['records'].loc[ns['records'].time<6],ns['val_targets'])
assert batch.recent.tolist()==[8,8,1,1] and ns['val_x'].recent.tolist()==[8,12,1,7]
passed('online t6 becomes t7 past; batch cutoff before6 excludes it')
edge_raw=pd.DataFrame([('X',1,99.),('Z',3,9.),('Z',2,8.),('Z',1,3.),('W',2,np.nan)],columns=['unit','time','reading'])
edge_targets=pd.DataFrame([('z3','Z',3,'red',1),('w3','W',3,'blue',-1),('early','Z',0,'red',1)],columns=ns['train_targets'].columns)
e=make(edge_raw,edge_targets)
assert e.loc['z3','recent']==8 and pd.isna(e.loc['z3','mean3']) and pd.isna(e.loc['w3','recent']) and pd.isna(e.loc['early','recent'])
try:make(pd.concat([edge_raw,edge_raw.iloc[[0]]]),edge_targets);raise AssertionError('duplicate must fail')
except ValueError:pass
passed('missing initial/all history, insufficient window, duplicate unit/time rejection')
# Training fitted state and category schema must survive validation stress.
imputer=ns['transformer'].named_transformers_['num'].named_steps['median']
scale=ns['transformer'].named_transformers_['num'].named_steps['range']
cat=ns['transformer'].named_transformers_['cat']
assert np.allclose(imputer.statistics_,[4,13/3,(sqrt(8/3)+sqrt(8/9))/2])
assert np.allclose(scale.data_min_,[2,4,sqrt(8/9)]) and np.allclose(scale.data_max_,[6,14/3,sqrt(8/3)])
assert cat.categories_[0].tolist()==['blue','red']
state=[a.copy() for a in (imputer.statistics_,scale.data_min_,scale.data_max_,cat.categories_[0])]
stress=ns['val_x'].copy();stress[['recent','mean3','std3']]=1e10;stress['kind']='new-kind'
encoded=ns['transformer'].transform(stress)
assert np.all(encoded[:,-2:]==0)
assert all(np.array_equal(a,b) for a,b in zip(state,(imputer.statistics_,scale.data_min_,scale.data_max_,cat.categories_[0])))
passed('all three trained numeric statistics, unknown schema and validation-stress invariance')
# Same-width separate fitting is a semantic schema failure, not a shape failure.
a=OneHotEncoder(handle_unknown='ignore',sparse_output=False).fit(pd.DataFrame({'kind':['red','blue','red']}))
b=OneHotEncoder(handle_unknown='ignore',sparse_output=False).fit(pd.DataFrame({'kind':['green','blue']}))
assert a.transform(pd.DataFrame({'kind':['green','blue']})).tolist()==[[0,0],[1,0]]
assert b.transform(pd.DataFrame({'kind':['green','blue']})).tolist()==[[0,1],[1,0]]
assert a.get_feature_names_out().tolist()!=b.get_feature_names_out().tolist()
passed('same-width validation encoder changes column meaning; default unknown rejects')
# New exercise is rebuilt from the student table, independent of the teacher code.
new_raw=pd.DataFrame([('M',1,5.),('M',2,7.),('M',3,9.),('M',4,np.nan),('N',1,np.nan),('N',2,np.nan),('N',3,np.nan),('N',4,1.),('P',1,7.),('P',2,9.),('P',3,11.),('P',4,np.nan),('P',6,17.),('Q',1,np.nan),('Q',2,0.),('Q',3,np.nan),('Q',4,np.nan),('Q',6,11.)],columns=['unit','time','reading'])
tr=pd.DataFrame([('m4','M',4,'gold',-1),('m5','M',5,'gold',1),('n4','N',4,'silver',-1),('n5','N',5,'silver',1)],columns=ns['train_targets'].columns)
va=pd.DataFrame([('p6','P',6,'bronze',1),('p7','P',7,'bronze',-1),('q6','Q',6,'gold',1),('q7','Q',7,'gold',-1)],columns=tr.columns)
tx,vx=make(new_raw,tr),make(new_raw,va)
assert np.allclose(tx.recent,[9,9,np.nan,1],equal_nan=True) and vx.recent.tolist()==[11,17,0,11]
assert np.allclose([tx.loc['m4','mean3'],tx.loc['m4','std3'],vx.loc['p6','mean3'],vx.loc['p6','std3']],[7,sqrt(8/3),9,sqrt(8/3)])
new_pipe=clone(ns['transformer']).fit(tx)
assert new_pipe.named_transformers_['num'].named_steps['median'].statistics_[0]==9
assert np.array_equal(new_pipe.transform(tx)[:,0],[1,1,1,0])
new_encoded=pd.DataFrame(new_pipe.transform(vx),index=vx.index,columns=new_pipe.get_feature_names_out())
new_scores=new_encoded['num__recent'].to_numpy();new_truth=va.label.to_numpy()
assert new_scores.tolist()==[5/4,2.,-1/8,5/4] # exact comparisons are deliberate
assert new_encoded.loc['p6',['cat__kind_gold','cat__kind_silver']].tolist()==[0,0]
assert new_encoded.loc['q6',['cat__kind_gold','cat__kind_silver']].tolist()==[1,0]
passed('new independent table: all recent/window values, median9/range8, categories and exact threshold scores')
def manual_counts(y,score,threshold):
 pred=[1 if s>=threshold else -1 for s in score]
 return {name:sum((int(t),p)==pair for t,p in zip(y,pred)) for name,pair in {'TP':(1,1),'FP':(-1,1),'TN':(-1,-1),'FN':(1,-1)}.items()}
def fraction_rates(c):
 tp,fp,tn,fn=[c[k] for k in ('TP','FP','TN','FN')]
 pairs={'accuracy':(tp+tn,tp+fp+tn+fn),'precision':(tp,tp+fp),'recall':(tp,tp+fn),'F1':(2*tp,2*tp+fp+fn),'FPR':(fp,fp+tn),'TPR':(tp,tp+fn)}
 return {k:(F(n,d) if d else None) for k,(n,d) in pairs.items()}
metric_evidence=[]
for y,scoreset,thresholdset,label in [(ns['truth'],ns['scores'],[float('inf'),2.5,1.5,0],'worked'),(new_truth,new_scores,[float('inf'),2,5/4,-1/8],'independent')]:
 for threshold in thresholdset:
  c=manual_counts(y,scoreset,threshold);assert counts(y,scoreset,threshold)==c
  exact=fraction_rates(c);actual=rates(c)
  for key,value in exact.items():assert actual[key] is None if value is None else np.isclose(actual[key],float(value))
  metric_evidence.append({'table':label,'threshold':str(threshold),'counts':c,'exact_rates':{k:str(v) for k,v in exact.items()}})
 f,t,th=roc_curve(y,scoreset,pos_label=1,drop_intermediate=False)
 for threshold,x,z in zip(th,f,t):
  manual=fraction_rates(manual_counts(y,scoreset,threshold));assert np.isclose(x,float(manual['FPR'])) and np.isclose(z,float(manual['TPR']))
assert roc_auc_score(new_truth,new_scores)==1/8
assert roc_auc_score(ns['truth'],ns['scores'])==1/2
for y,score in [(np.array([-1,-1]),np.array([.1,.2])),(np.array([1,1]),np.array([.1,.2]))]:
 for threshold in [0,1]:
  c=manual_counts(y,score,threshold)
  for key,value in fraction_rates(c).items():assert rates(c)[key] is None if value is None else np.isclose(rates(c)[key],float(value))
passed('independent Fraction confusion/rates/zero denominators, ROC ties and AUC')
assert np.allclose(ns['ax'].lines[0].get_xdata(),ns['fpr']) and np.allclose(ns['ax'].lines[0].get_ydata(),ns['tpr'])
assert ns['ax'].get_xlabel()=='FPR' and ns['ax'].get_ylabel()=='TPR'
ns['fig'].savefig(ROOT/'temporal-roc.png',dpi=130)
passed('actual plotted line and FPR/TPR axis labels match computed ROC')
# Actual truth/prediction arrays are checked with a separate Fraction implementation.
weighted_functions={name for name,value in ns.items() if callable(value) and 'weight' in name}
weight=ns['weighted_accuracy']
def weighted_oracle(y,p,w):
 weights=[F(w) if item=='T' else F(1) for item in y]
 return sum(item for item,t,guess in zip(weights,y,p) if t==guess)/sum(weights)
weighted_evidence=[];weighted_rounding=[]
for y,p,w,label in [
 (ns['actual'].tolist(),ns['guess_a'].tolist(),5,'worked_A'),
 (ns['actual'].tolist(),ns['guess_b'].tolist(),5,'worked_B'),
 (['B']*6+['T']*2,['B']*8,4,'independent_U'),
 (['B']*6+['T']*2,['B']*3+['T']*5,4,'independent_V'),
 (['B','T'],['T','B'],4,'zero_correct'),
 (['B','T'],['B','T'],4,'all_correct')]:
 exact=weighted_oracle(y,p,w);assert np.isclose(weight(y,p,w),float(exact),rtol=1e-12,atol=1e-15)
 for order in [list(range(len(y))),list(range(len(y)-1,-1,-1))]:
  observed=weight([y[i] for i in order],[p[i] for i in order],w)
  assert np.isclose(observed,float(exact),rtol=1e-12,atol=1e-15)
  if observed!=float(exact):weighted_rounding.append({'case':label,'actual':observed,'exact_float':float(exact),'difference':observed-float(exact)})
 weighted_evidence.append({'case':label,'truth':y,'predicted':p,'target_weight':w,'exact':str(exact)})
for y,p,w in [([],[],4),(['B'],['B','T'],4),([['B']],[['B']],4),(['X'],['B'],4),(['B'],['X'],4),(['B'],['B'],0),(['B'],['B'],-1),(['B'],['B'],float('nan')),(['B'],['B'],float('inf'))]:
 try:weight(y,p,w);raise AssertionError('invalid weighted input must fail')
 except ValueError:pass
for extreme_weight in [1e308,1e-308]:
 assert np.isfinite(weight(['B','T'],['B','T'],extreme_weight)) and weight(['B','T'],['B','T'],extreme_weight)==1
 assert np.isfinite(weight(['B','T'],['T','B'],extreme_weight)) and weight(['B','T'],['T','B'],extreme_weight)==0
passed('truth-based weights and all-truth denominator from arrays; independent U/V; finite-positive invalid guards and extreme finite weights')
# Pure in-memory source mutations; these never modify the source notebook.
mutations={
 'include_current_time':('raw.time < row.time','raw.time <= row.time'),
 'remove_unit_boundary':('(raw.unit == row.unit) & (raw.time < row.time)','(raw.time < row.time)'),
 'reverse_time_sort':('past.sort_values("time")','past.sort_values("time", ascending=False)'),
 'remove_time_sort':('past = past.sort_values("time")','past = past'),
 'ffill_copies_in_window':('past.reading.dropna().tail(3)','past.reading.ffill().dropna().tail(3)'),
 'sample_instead_population_std':('last3.std(ddof=0)','last3.std(ddof=1)'),
 'mean_instead_of_median':('SimpleImputer(strategy="median")','SimpleImputer(strategy="mean")'),
 'backfill_instead_forwardfill':('filled = past.reading.ffill()','filled = past.reading.bfill()'),
 'fit_on_training_plus_validation':('transformer.fit_transform(train_x)','transformer.fit(pd.concat([train_x, val_x])).transform(train_x)'),
 'refit_validation_transform':('val_array = transformer.transform(val_x)','val_array = transformer.fit_transform(val_x)'),
 'clip_out_of_training_range':('("range", MinMaxScaler())','("range", MinMaxScaler(clip=True))'),
 'strict_threshold_loses_ties':('score >= threshold','score > threshold'),
 'weight_by_prediction':('weights = np.where(actual == "T", target_weight, 1.0)','weights = np.where(predicted == "T", target_weight, 1.0)'),
 'denominator_correct_rows_only':('np.sum(weights * (actual == predicted)) / np.sum(weights)','np.sum(weights * (actual == predicted)) / np.sum(weights * (actual == predicted))'),
}
mutant_results=[]
import matplotlib.pyplot as plt
for name,(before,after) in mutations.items():
 namespace={};caught=None;replacement_count=0;output=io.StringIO()
 with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
  try:
   for i,cell in enumerate(original.cells):
    if cell.cell_type!='code':continue
    replacement_count+=cell.source.count(before)
    if 'plt.subplots(' in cell.source:continue
    exec(compile(cell.source.replace(before,after),f'{name}:cell{i}','exec'),namespace)
  except Exception as exc:caught={'cell':i,'type':type(exc).__name__,'message':str(exc)}
 assert replacement_count==1,(name,replacement_count)
 oracle_error=None
 if caught is None:
  try:
   actual=namespace['make_features'](ns['records'],ns['val_targets']);expect,_=oracle_features(ns['records'],ns['val_targets'])
   for col in ('recent','mean3','std3'):assert all(equal_number(a,b) for a,b in zip(actual[col],expect[col])),col
   pd.testing.assert_frame_equal(make(edge_raw,edge_targets),namespace['make_features'](edge_raw,edge_targets))
   assert namespace['counts_at'](ns['truth'],ns['scores'],1.5)==manual_counts(ns['truth'],ns['scores'],1.5)
   candidate_pipe=clone(namespace['transformer']).fit(tx)
   assert candidate_pipe.named_transformers_['num'].named_steps['median'].statistics_[0]==9, 'median differs from mean on new table'
   assert np.array_equal(candidate_pipe.transform(tx)[:,0],[1,1,1,0]), 'new missing training row must be median-filled'
  except Exception as exc:oracle_error={'type':type(exc).__name__,'message':str(exc)}
 assert caught or oracle_error,name
 mutant_results.append({'name':name,'before':before,'after':after,'notebook_detected':caught,'reviewer_oracle_detected':oracle_error,'stdout':output.getvalue()})
 plt.close('all')
# Stored student outputs, answer blankness and HTML pairing are checked independently.
answers=[c for c in original.cells if 'independent-exercise' in c.metadata.get('tags',[])]
assert len(answers)==1 and not ast.parse(answers[0].source).body and not answers[0].outputs
stored_png=[(i,o['data']['image/png']) for i,c in enumerate(original.cells) for o in c.get('outputs',[]) if 'image/png' in o.get('data',{})]
assert len(stored_png)>=1,'student notebook must retain an actual ROC PNG'
for i,png in stored_png:(ROOT/f'temporal-stored-cell-{i}.png').write_bytes(base64.b64decode(png))
def projection(html):
 soup=BeautifulSoup(html,'html.parser')
 for node in soup.select('script,style,.jp-InputPrompt,.jp-OutputPrompt'):node.decompose()
 return [re.sub(r'\s+',' ',node.get_text(' ',strip=True)).strip() for node in soup.select('.jp-Cell')]
expected_html,_=HTMLExporter().from_notebook_node(original)
assert projection(raw[NAMES[1]].decode())==projection(expected_html)
text='\n'.join(c.source for c in original.cells)
assert not re.search(r'\d+\s*(?:[~∼–-]\s*\d+)?\s*(?:분|시간)(?![가-힣])|편성|실측|소요\s*시간|수업\s*밖|필수\s*자습',text)
source_after={name:hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in NAMES}
assert source_after==sha,'source changed during independent review'
nbformat.write(book,ROOT/'temporal-executed.ipynb')
report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':sha,'source_unchanged':True,'execution':'fresh InProcessKernelManager, inline plotting configured, sequential cells','total_cells':len(book.cells),'executed_code_cells':len(executed),'code_cell_evidence':executed,'student_answer_ast_empty':True,'student_performance':'not_observed','checks':checks,'provenance':provenance,'metrics':metric_evidence,'weighted_function_names':sorted(weighted_functions),'weighted_exact_cases':weighted_evidence,'weighted_rounding_observations':weighted_rounding,'source_mutations':mutant_results,'ROC_png_visual_inspection':'independent reviewer viewed stored PNG; points, labels and axes readable','stored_roc_png_cells':[i for i,png in stored_png],'HTML_cell_text_matches_fresh_export':True,'limits':['finite synthetic cases only','real learner work and revised study load unobserved','ordinary socket kernel/Colab/browser HTML visual rendering not attempted','real hidden final test not created or verified']}
(ROOT/'temporal-review-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str)+'\n')
client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
shutil.rmtree(runtime,ignore_errors=True)
(source_copy/'week02_temporal_preprocessing.html').unlink(missing_ok=True)
print(json.dumps({'sha256':sha,'total_cells':len(book.cells),'code_cells':len(executed),'checks':len(checks),'mutations':len(mutant_results),'weighted_functions':sorted(weighted_functions),'stored_plot_cells':report['stored_roc_png_cells']},ensure_ascii=False,indent=2))
