"""Reproduce deferred review cases; this is not a student solution or grader."""
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import argparse,json,math
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestCentroid
from sklearn.tree import DecisionTreeClassifier

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path.cwd());a=p.parse_args()
r=a.root.resolve();n=json.loads((r/'lessons/week01/week01_integrated.ipynb').read_text(encoding='utf-8'))
c=next(c for c in n['cells'] if c.get('id')=='9462ed76');source=c['source'] if isinstance(c['source'],str) else ''.join(c['source'])
ns={'np':np,'pd':pd}
with redirect_stdout(StringIO()):exec(source,ns)
train=ns['exercise_train'];known=train[train.label.isin(['정상','점검'])]
mean=float(known.signal.mean());assert mean==4
validation=ns['exercise_validation'].copy(deep=True);validation.loc[validation.unit=='V7','signal']=np.nan
wrong_mean=float(validation.signal.mean());assert wrong_mean==5.5

def features(df,fill):
 return np.column_stack((df.signal.fillna(fill),[int(((x[:,:,0]==1)&(x[:,:,1]==2)).sum()) for x in df.panel]))
models={}
for name,model in [('centroid',NearestCentroid()),('tree',DecisionTreeClassifier(max_depth=2,random_state=0))]:
 model.fit(features(known,mean),known.label)
 models[name]={'training_fitted_fill':model.predict(features(validation,mean)).tolist(),
               'validation_refitted_fill':model.predict(features(validation,wrong_mean)).tolist()}
assert models['centroid']['training_fitted_fill'][-1]=='정상'
assert models['centroid']['validation_refitted_fill'][-1]=='점검'
assert models['tree']['training_fitted_fill']==models['tree']['validation_refitted_fill']
reordered=train.set_index('unit').loc[['T5','T1','T2','T3','T4']].reset_index()
first_four=reordered.iloc[:4];naive=float(first_four.signal.mean())
assert math.isclose(naive,103/3) and '?' in first_four.label.tolist()
left=pd.DataFrame({'sample_id':['Q1','Q2'],'site':[None,'실내']})
right=pd.DataFrame({'site':[None,'실내'],'note':['unknown-key','indoor']})
joined=left.merge(right,on='site',how='left',validate='many_to_one',indicator=True)
assert len(joined)==len(left) and joined.loc[joined.sample_id.eq('Q1'),'_merge'].item()=='both'
print(json.dumps({'status':'passed','scope':'Reviewer-generated counterexamples, not learner work or automatic grading.',
 'missing_validation_signal':{'training_mean':mean,'validation_refit_mean':wrong_mean,'model_predictions':models},
 'reordered_training_rows':{'first_four_ids':first_four.unit.tolist(),'naive_mean':naive,'known_label_mean':mean},
 'missing_merge_key':{'left_rows':len(left),'joined_rows':len(joined),'Q1_merge':str(joined.loc[joined.sample_id.eq('Q1'),'_merge'].item()),'qualification':'When missing denotes unknown identity, this match must be examined under the task contract; matching missing values is not universally invalid.'}},ensure_ascii=False,indent=2))
