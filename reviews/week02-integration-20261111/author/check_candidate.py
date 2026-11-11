from pathlib import Path
from fractions import Fraction as F
import argparse, contextlib, hashlib, io, json, os
os.environ['MPLBACKEND']='Agg';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['LOKY_MAX_CPU_COUNT']='1'
import nbformat
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier

parser=argparse.ArgumentParser(description='Run finite candidate checks; write only to an explicitly new output path.')
parser.add_argument('--output',type=Path,help='new JSON result path; omitted means stdout only')
args=parser.parse_args()
base=Path('lessons/week02')
main=nbformat.read(base/'week02_prediction_evaluation.ipynb',as_version=4)
temporal=nbformat.read(base/'week02_temporal_preprocessing.ipynb',as_version=4)
source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [base/'week02_prediction_evaluation.ipynb',base/'week02_temporal_preprocessing.ipynb']}
ns={}
with contextlib.redirect_stdout(io.StringIO()):exec(main.cells[5].source,ns)
full=ns['course_records'];train=ns['known_train_4w'];val=ns['validation']
assert train.row_id.tolist()==['a1','a2','b1','b2','g1','g2','h1','h2']
assert set(train.group)==set('ABGH') and set(val.group)==set('CD')
assert 'b3' not in set(train.row_id) and set(train.label)=={-1,1}
assert not set(train.group)&set(val.group) and not set(full.group)&{'E','F'}
folds=[]
for ti,vi in GroupKFold(2).split(train[['reading']],train.label,train.group):
 t=train.iloc[ti];v=train.iloc[vi]
 assert set(t.group).isdisjoint(v.group) and set(t.label)=={-1,1} and set(v.label)=={-1,1} and len(t)==4
 stats={}
 for name,model in [('logistic',LogisticRegression()),('knn3',KNeighborsClassifier(n_neighbors=3))]:
  pipeline=Pipeline([('imputer',SimpleImputer()),('scaler',StandardScaler()),('model',model)]).fit(t[['reading']],t.label)
  pred=pipeline.predict(v[['reading']]);assert len(pred)==len(v)
  assert int(pipeline['scaler'].n_samples_seen_)==len(t)==4
  stats[name]={'fitted_mean':float(pipeline['imputer'].statistics_[0]),'fit_row_ids':t.row_id.tolist(),'scaler_n_samples_seen':int(pipeline['scaler'].n_samples_seen_),'prediction':pred.tolist()}
  assert np.isclose(pipeline['imputer'].statistics_[0],t.reading.mean())
 folds.append({'train_groups':sorted(set(t.group)),'val_groups':sorted(set(v.group)),'train_rows':len(t),'val_rows':len(v),'models':stats})
assert np.allclose(sorted(x['models']['logistic']['fitted_mean'] for x in folds),[3,16/3])
baseline=Pipeline([('imputer',SimpleImputer()),('scaler',StandardScaler()),('model',DummyClassifier(strategy='constant',constant=-1))]).fit(train[['reading']],train.label)
assert baseline.predict(val[['reading']]).tolist()==[-1,-1,-1,-1]
assert train.row_id.tolist()==['a1','a2','b1','b2','g1','g2','h1','h2']
assert int(baseline['scaler'].n_samples_seen_)==len(train)==8
assert np.isclose(baseline['imputer'].statistics_[0],4) and np.isclose(baseline['scaler'].scale_[0],np.sqrt(2))

# Load only the worked feature constructor; no student answer code is executed.
tns={}; src=next(c.source for c in temporal.cells if c.id=='fe6a294b')
pre=src.split('\ntrain_x = make_features',1)[0]
exec('import numpy as np\nimport pandas as pd\n'+pre,tns);make=tns['make_features']
values={'M':[5,7,9,None], 'N':[None,None,None,1], 'P':[7,9,11,None,17], 'Q':[None,0,None,None,11]}
raw=[]
for unit,vs in values.items():
 times=[1,2,3,4] if unit in ('M','N') else [1,2,3,4,6]
 raw.extend((unit,t,np.nan if v is None else v) for t,v in zip(times,vs))
raw=pd.DataFrame(raw,columns=['unit','time','reading']).sample(frac=1,random_state=73)
rows=[('m4','M',4,'gold',-1),('m5','M',5,'gold',1),('n4','N',4,'silver',-1),('n5','N',5,'silver',1),('p6','P',6,'bronze',1),('p7','P',7,'bronze',-1),('q6','Q',6,'gold',1),('q7','Q',7,'gold',-1)]
target=pd.DataFrame(rows,columns=['id','unit','time','kind','label'])
tr=target[target.time<6];va=target[target.time>=6]
assert tr.id.tolist()==['m4','m5','n4','n5'] and va.id.tolist()==['p6','p7','q6','q7']
assert set(tr.unit).isdisjoint(va.unit) and tr.time.max()<va.time.min()
train_x=make(raw,tr.drop(columns='label'));val_x=make(raw,va.drop(columns='label'))
assert np.allclose(train_x.recent,[9,9,np.nan,1],equal_nan=True) and np.allclose(val_x.recent,[11,17,0,11])
num=Pipeline([('median',SimpleImputer(strategy='median')),('scale',MinMaxScaler())])
transform=ColumnTransformer([('num',num,['recent','mean3','std3']),('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),['kind'])])
transform.fit(train_x)
fitted=transform.named_transformers_['num'];enc=transform.named_transformers_['cat']
assert fitted['median'].statistics_[0]==9 and fitted['scale'].data_min_[0]==1 and fitted['scale'].data_max_[0]==9
names=transform.get_feature_names_out();val_encoded=pd.DataFrame(transform.transform(val_x),index=val_x.index,columns=names)
scores=val_encoded['num__recent'].tolist();assert scores==[1.25,2,-0.125,1.25]
assert val_encoded.loc['p6',['cat__kind_gold','cat__kind_silver']].tolist()==[0,0]
before=(fitted['median'].statistics_.copy(),fitted['scale'].data_min_.copy(),fitted['scale'].data_max_.copy(),enc.categories_[0].copy())
truth=va.label.to_numpy(); thresholds=[2,1.25,-0.125,-1]
metrics=[]
for t in thresholds:
 pred=np.where(np.array(scores)>=t,1,-1);tp=int(((truth==1)&(pred==1)).sum());fp=int(((truth==-1)&(pred==1)).sum());tn=int(((truth==-1)&(pred==-1)).sum());fn=int(((truth==1)&(pred==-1)).sum());f1=F(2*tp,2*tp+fp+fn)
 metrics.append({'threshold':t,'counts':[tp,fp,tn,fn],'f1':str(f1)})
assert [x['f1'] for x in metrics]==['0','2/5','2/3','2/3']
chosen=max(thresholds,key=lambda t:(F(2*int(((truth==1)&(np.array(scores)>=t)).sum()),2*int(((truth==1)&(np.array(scores)>=t)).sum())+int(((truth==-1)&(np.array(scores)>=t)).sum())+int(((truth==1)&(np.array(scores)<t)).sum())),t))
assert chosen==-0.125

infer_raw=pd.DataFrame([('R',1,3),('R',2,5),('R',7,9),('S',1,2),('S',2,1),('S',7,0),('U',1,3),('U',2,1),('U',7,-1)],columns=['unit','time','reading'])
infer_target=pd.DataFrame([('r8','R',8,'bronze'),('s8','S',8,'gold'),('u8','U',8,'silver')],columns=['id','unit','time','kind'])
assert 'label' not in infer_target.columns
ix=make(infer_raw,infer_target);encoded=pd.DataFrame(transform.transform(ix),index=ix.index,columns=names)
iscores=encoded['num__recent'].tolist();ipred=np.where(np.array(iscores)>=chosen,1,-1).tolist()
assert iscores==[1,-0.125,-0.25] and ipred==[1,1,-1]
assert np.where(np.array(iscores)>=-1,1,-1).tolist()==[1,1,1]
assert encoded.loc['r8',['cat__kind_gold','cat__kind_silver']].tolist()==[0,0]
# Additional unseen examples with a different order, values, histories, and no labels.
other_raw=pd.DataFrame([('W',1,-4),('W',3,-1),('W',7,-3),('Z',1,1),('Z',3,0),('Z',7,1),('V',1,0),('V',3,2),('V',7,0)],columns=['unit','time','reading'])
other_target=pd.DataFrame([('w8','W',8,'bronze'),('z8','Z',8,'gold'),('v8','V',8,'silver')],columns=['id','unit','time','kind'])
other=make(other_raw.sample(frac=1,random_state=9),other_target)
other_scores=pd.DataFrame(transform.transform(other),index=other.index,columns=names)['num__recent'].to_numpy()
assert other_scores.tolist()==[-.5,0,-.125]
assert np.where(other_scores>=chosen,1,-1).tolist()==[-1,1,1]
reordered=other_target.iloc[::-1];rx=make(other_raw,reordered);rs=pd.DataFrame(transform.transform(rx),index=rx.index,columns=names)['num__recent']
assert dict(zip(other.index,other_scores))==rs.to_dict()
after=(fitted['median'].statistics_,fitted['scale'].data_min_,fitted['scale'].data_max_,enc.categories_[0])
assert all(np.array_equal(a,b) for a,b in zip(before,after))
assert all(hashlib.sha256((base/name).read_bytes()).hexdigest()==sha for name,sha in source_hashes.items())
result={'source_sha256':source_hashes,'cv_folds':folds,'expanded_dummy_refit':{'fit_row_ids':train.row_id.tolist(),'scaler_n_samples_seen':int(baseline['scaler'].n_samples_seen_),'imputer':4,'scale_mean':4,'scale_std':'sqrt(2)','prediction':[-1,-1,-1,-1]},'independent_split':{'training':tr.id.tolist(),'validation':va.id.tolist(),'max_train_time':5,'min_val_time':6},'validation_scores':scores,'threshold_metrics':metrics,'chosen_threshold':chosen,'unlabeled_exercise':{'ids':infer_target.id.tolist(),'scores':iscores,'prediction':ipred,'alternate_minus_one_prediction':[1,1,1]},'new_unlabeled_case':{'ids':other_target.id.tolist(),'scores':other_scores.tolist(),'prediction':[-1,1,1],'row_id_reorder_invariance':True},'fit_state_invariant':True,'scope':'synthetic finite cases; not student performance or fourth-week lesson completion'}
if args.output is not None:
 with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
