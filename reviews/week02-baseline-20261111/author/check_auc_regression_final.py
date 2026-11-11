from pathlib import Path
from fractions import Fraction as F
import hashlib,json,warnings
import numpy as np
import sklearn
from sklearn.metrics import roc_curve,roc_auc_score,auc


def pair_auc(labels,scores):
 pos=[F(str(s)) for y,s in zip(labels,scores) if y==1]; neg=[F(str(s)) for y,s in zip(labels,scores) if y==-1]
 if not pos or not neg:return None
 return sum((F(1) if p>n else F(1,2) if p==n else F(0)) for p in pos for n in neg)/(len(pos)*len(neg))

def exact_roc(labels,scores):
 if 1 not in labels or -1 not in labels:return None
 s=[F(str(x)) for x in scores]; thresholds=sorted(set(s),reverse=True);points=[(F(0),F(0))]
 for threshold in thresholds:
  tp=sum(y==1 and v>=threshold for y,v in zip(labels,s));fp=sum(y==-1 and v>=threshold for y,v in zip(labels,s))
  points.append((F(fp,labels.count(-1)),F(tp,labels.count(1))))
 return points

def trapezoid(points):
 return sum((x2-x1)*(y1+y2)/2 for (x1,y1),(x2,y2) in zip(points,points[1:]))

def test_case(name,labels,scores,expected):
 pairs=pair_auc(labels,scores);points=exact_roc(labels,scores);area=trapezoid(points)
 assert pairs==area==expected,(name,pairs,area,expected)
 binary=np.array(labels)==1; fpr,tpr,_=roc_curve(binary,np.array(scores),drop_intermediate=False)
 lib_auc=roc_auc_score(binary,np.array(scores));lib_area=auc(fpr,tpr)
 assert np.isclose(lib_auc,float(expected)) and np.isclose(lib_area,float(expected))
 assert all(np.allclose(pair,[float(v) for v in exact]) for pair,exact in zip(zip(fpr,tpr),points))
 return {'name':name,'label':labels,'scores':scores,'exact_pair_auc':str(pairs),'exact_trapezoid':str(area),'roc_points':[[str(x),str(y)] for x,y in points],'sklearn_auc':float(lib_auc),'sklearn_trapezoid':float(lib_area)}

cases=[
 test_case('main_worked',[1,-1,1,-1],[.9,.6,.4,.1],F(3,4)),
 test_case('supplement_worked',[1,-1,-1,1],[1.5,2.5,0,1.5],F(1,2)),
 test_case('independent_exercise',[1,-1,1,-1],[1.25,2,-.125,1.25],F(1,8)),
 test_case('reverse_ranking',[1,1,-1,-1],[0,1,2,3],F(0)),
 test_case('correct_ranking',[1,1,-1,-1],[3,2,1,0],F(1)),
 test_case('all_tied',[1,1,-1,-1],[.5,.5,.5,.5],F(1,2)),
 test_case('fresh_mixed_ties',[1,-1,1,-1,1,-1],[3,3,2,1,0,2],F(4,9)),
]
assert any(x!=y for x,y in exact_roc([1,-1,-1,1],[1.5,2.5,0,1.5]))
# Independent score transform and threshold contract on the existing main table.
y=np.array([1,-1,1,-1]);s=np.array([.9,.6,.4,.1]);p0=np.where(s>=.5,1,-1);p1=np.where(s>=.3,1,-1);translated=s+1
pred_same=np.where(translated>=1.5,1,-1);pred_unmoved=np.where(translated>=.5,1,-1)
def f1(p):
 tp=int(((y==1)&(p==1)).sum());fp=int(((y==-1)&(p==1)).sum());fn=int(((y==1)&(p==-1)).sum());return F(2*tp,2*tp+fp+fn)
assert f1(p0)==F(1,2) and f1(p1)==F(4,5) and f1(pred_unmoved)==F(2,3)
assert np.array_equal(p0,pred_same) and not np.array_equal(p0,pred_unmoved)
assert roc_auc_score(y==1,translated)==roc_auc_score(y==1,s)==.75
# If 0 means unknown, filter truth and scores together before binary conversion.
unknown_y=np.array([1,0,-1]);unknown_s=np.array([.6,.9,.2]);known=np.isin(unknown_y,[-1,1])
correct=roc_auc_score(unknown_y[known]==1,unknown_s[known]);naive=roc_auc_score(unknown_y==1,unknown_s)
assert correct==1 and naive==.5
one_class=[]
for label in [1,-1]:
 labels=[label,label];assert pair_auc(labels,[.2,.8]) is None
 with warnings.catch_warnings(record=True) as observed:
  warnings.simplefilter('always')
  try:
   got=roc_auc_score(np.array(labels)==1,[.2,.8]); state={'return':str(got),'warnings':[type(w.message).__name__ for w in observed]};assert np.isnan(got)
  except ValueError as error:state={'error':type(error).__name__,'warnings':[type(w.message).__name__ for w in observed]}
 one_class.append({'labels':labels,'mathematical_auc':'undefined',**state})

base=Path('lessons/week02');paths=[base/'week02_prediction_evaluation.ipynb',base/'week02_prediction_evaluation.html',base/'week02_temporal_preprocessing.ipynb',base/'week02_temporal_preprocessing.html',base/'teacher-notes.md',base/'week02_temporal_preprocessing_teacher.md',base/'build_week02.py']
result={'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'sklearn':sklearn.__version__,'cases':cases,'thresholds':{'fixed_score_f1_at_0.5':str(f1(p0)),'fixed_score_f1_at_0.3':str(f1(p1)),'scores_and_threshold_shift_together_same_prediction':True,'scores_only_shift_f1':str(f1(pred_unmoved)),'auc_unchanged':.75},'unknown_label':{'known_only_auc':correct,'wrong_unknown_to_negative_auc':naive},'one_class':one_class,'scope':'finite synthetic numeric controls; not student achievement or probability calibration'}
out=Path('reviews/week02-baseline-20261111/author/auc-validation-final.json')
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'cases':[(c['name'],c['exact_pair_auc']) for c in cases],'thresholds':result['thresholds'],'unknown_label':result['unknown_label'],'one_class':one_class},ensure_ascii=False))
