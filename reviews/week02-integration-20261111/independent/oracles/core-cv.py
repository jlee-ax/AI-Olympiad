import json,math,traceback
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
D=Path.cwd().parents[1]
f=json.loads((D/'frozen-inputs-v2.json').read_text())['CV']
assert len(known_train)==4 and len(known_train_4w)==8
assert preprocess.named_steps['scaler'].n_samples_seen_==4
assert np.isclose(preprocess.named_steps['imputer'].statistics_[0],4)
assert np.isclose(leaky_imputer.statistics_[0],9)
def factory(model=None):
 return Pipeline([('imputer',SimpleImputer()),('scaler',StandardScaler()),('model',model if model is not None else LogisticRegression(random_state=0,max_iter=200))])
def state(pipe):
 return {'mean':float(pipe.named_steps['imputer'].statistics_[0]),'variance':float(pipe.named_steps['scaler'].var_[0]),'n':int(pipe.named_steps['scaler'].n_samples_seen_)}
def partition(tr,va,entity='group',unseen=True):
 if not len(tr) or not len(va) or not tr.row_id.is_unique or not va.row_id.is_unique:raise ValueError('empty/duplicate partition')
 if set(tr.row_id)&set(va.row_id):raise ValueError('row overlap')
 if unseen and set(tr[entity])&set(va[entity]):raise ValueError('entity overlap')
 if set(tr.label)!={-1,1}:raise ValueError('two known training classes required')
def calc(tr):
 xs=[float(v) for v in tr.reading if not pd.isna(v)];mean=sum(xs)/len(xs);filled=[mean if pd.isna(v) else float(v) for v in tr.reading];variance=sum((v-mean)**2 for v in filled)/len(filled)
 return mean,variance
report={'scope':'actual candidate cohorts plus reviewer CV procedure using real sklearn fits; not student implementation','actual_cohort':[],'frozen_families':[],'negative_controls':[]}
full=factory().fit(known_train_4w[['reading']],known_train_4w.label)
assert state(full)['n']==8 and np.isclose(state(full)['mean'],4)
report['full_extension_state']=state(full)
models={'logistic':lambda:LogisticRegression(random_state=0,max_iter=200),'knn3':lambda:KNeighborsClassifier(n_neighbors=3),'tree':lambda:DecisionTreeClassifier(max_depth=2,random_state=0),'svm':lambda:SVC(),'dummy':lambda:DummyClassifier(strategy='constant',constant=-1)}
for ti,vi in GroupKFold(n_splits=2).split(known_train_4w[['reading']],known_train_4w.label,known_train_4w.group):
 tr=known_train_4w.iloc[ti];va=known_train_4w.iloc[vi];partition(tr,va);mu,var=calc(tr)
 for name,maker in models.items():
  p=factory(maker()).fit(tr[['reading']],tr.label);pred=p.predict(va[['reading']]);s=state(p)
  assert s['n']==len(tr) and np.isclose(s['mean'],mu) and np.isclose(s['variance'],var) and len(pred)==len(va) and set(pred).issubset({-1,1})
  report['actual_cohort'].append({'model':name,'fit_rows':tr.row_id.tolist(),'validation_rows':va.row_id.tolist(),'train_groups':sorted(tr.group.unique()),'classes':sorted(tr.label.unique().tolist()),'state':s,'predictions':pred.tolist()})
new=pd.DataFrame(f['training_records']).rename(columns={'id':'row_id','entity':'group'});known=new[new.label.isin([-1,1])].copy()
assert len(known)==f['expected_known_rows']
for family in f['accepted_examples_not_exhaustive']:
 for fold in family['folds']:
  tr=known[known.group.isin(fold['train_entities'])];va=known[known.group.isin(fold['validation_entities'])];partition(tr,va)
  p=factory().fit(tr[['reading']],tr.label);s=state(p);pred=p.predict(va[['reading']])
  assert np.isclose(s['mean'],fold['expected_fit_mean']) and np.isclose(s['variance'],fold['expected_population_variance_after_mean_fill']) and s['n']==len(tr)
  old=state(p);changed=va.copy();changed['reading']=99999.;p.predict(changed[['reading']]);assert state(p)==old
  report['frozen_families'].append({'family':family['id'],'fit_ids':tr.row_id.tolist(),'validation_ids':va.row_id.tolist(),'state':s,'predictions':pred.tolist(),'heldout_change_fit_state_unchanged':True})
def expect_rejection(name,fn,kind):
 try:fn()
 except kind as err:report['negative_controls'].append({'name':name,'detected':True,'type':type(err).__name__,'message':str(err),'traceback':traceback.format_exc()})
 else:raise AssertionError('negative control escaped: '+name)
bad=f['bad_row_split'];expect_rejection('row-group-overlap',lambda:partition(known[known.row_id.isin(bad['train_ids'])],known[known.row_id.isin(bad['validation_ids'])]),ValueError)
old=pd.DataFrame(f['infeasible_control']['training']).rename(columns={'id':'row_id','entity':'group'})
for group in old.group.unique():expect_rejection('single-class-training-fold',lambda group=group:partition(old[old.group==group],old[old.group!=group]),ValueError)
fold=f['accepted_examples_not_exhaustive'][0]['folds'][0];tr=known[known.group.isin(fold['train_entities'])];va=known[known.group.isin(fold['validation_entities'])]
leak=Pipeline([('imputer',SimpleImputer()),('scaler',StandardScaler())]).fit(known[['reading']])
leaky_model=LogisticRegression(random_state=0).fit(leak.transform(tr[['reading']]),tr.label)
try:assert np.isclose(leak.named_steps['imputer'].statistics_[0],fold['expected_fit_mean'])
except AssertionError:report['negative_controls'].append({'name':'full-cohort-preprocess-in-CV-fold','detected':True,'actual_mean':float(leak.named_steps['imputer'].statistics_[0]),'expected_mean':fold['expected_fit_mean'],'traceback':traceback.format_exc(),'classifier_training_rows':len(tr)})
else:raise AssertionError('leaky fit state escaped')
assert np.isclose(SimpleImputer().fit(new[['reading']]).statistics_[0],f['wrong_unknown_included_mean'])
assert np.isclose(SimpleImputer().fit(known.loc[known.reading!=0,['reading']]).statistics_[0],f['wrong_zero_dropped_mean'])
# Known entities at later times is a different permitted deployment contract.
tr=known[known.time==1];va=known[known.time==2];partition(tr,va,unseen=False);assert set(tr.group)==set(va.group) and tr.time.max()<va.time.min() and 1.5<2
report['same_entity_future_split_accepted']=True
print(json.dumps(report,ensure_ascii=False,indent=2))
