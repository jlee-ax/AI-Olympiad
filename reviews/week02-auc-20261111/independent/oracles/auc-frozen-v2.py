import ast,json,math,traceback,warnings
from fractions import Fraction
from pathlib import Path
import sklearn
D=Path.cwd().parents[1]
fixed=json.loads((D/'frozen-inputs-v1.json').read_text())
f=fixed['binary_mixed_tie']; yy=list(f['labels']);ss=list(f['scores'])

def pair_reference(labels,values,tie=Fraction(1,2)):
    if len(labels)!=len(values) or not set(labels)<=set([-1,1]):raise ValueError('reference contract: aligned known binary rows only')
    pos=[v for y,v in zip(labels,values) if y==1];neg=[v for y,v in zip(labels,values) if y==-1]
    if not pos or not neg:return None
    return sum((Fraction(1) if p>n else tie if p==n else Fraction(0)) for p in pos for n in neg)/(len(pos)*len(neg))
def roc_reference(labels,values):
    P=labels.count(1);N=labels.count(-1)
    if not P or not N:return None
    points=[(Fraction(0),Fraction(0))]
    for t in sorted(set(values),reverse=True):
        points.append((Fraction(sum(y==-1 and s>=t for y,s in zip(labels,values)),N),Fraction(sum(y==1 and s>=t for y,s in zip(labels,values)),P)))
    area=sum((x2-x1)*(y1+y2)/2 for (x1,y1),(x2,y2) in zip(points,points[1:]))
    return points,area
frac=lambda a:Fraction(*a)
expected=frac(f['expected_auc_fraction']);pair=pair_reference(yy,ss);points,area=roc_reference(yy,ss)
assert pair==area==expected
assert [x for x,y in points]==[frac(z) for z in f['expected_roc_fpr_fractions']]
assert [y for x,y in points]==[frac(z) for z in f['expected_roc_tpr_fractions']]
labels01=np.array(yy)==1
actual_curve=roc_curve(np.array(yy),np.array(ss),pos_label=1,drop_intermediate=False)
actual_area=auc(actual_curve[0],actual_curve[1]);actual_rank=roc_auc_score(labels01.astype(int),np.array(ss))
assert np.isclose(actual_area,float(expected)) and np.isclose(actual_rank,float(expected))
assert np.allclose(actual_curve[0],[float(x) for x,y in points]) and np.allclose(actual_curve[1],[float(y) for x,y in points])
reverse=roc_auc_score(labels01.astype(int),-np.array(ss));swap=roc_auc_score((~labels01).astype(int),ss);both=roc_auc_score((~labels01).astype(int),-np.array(ss))
assert np.isclose(reverse,float(frac(f['expected_reverse_score_auc_fraction'])))
assert np.isclose(swap,float(frac(f['expected_label_swap_auc_fraction']))) and np.isclose(both,float(expected))
shifted=np.array(ss)+f['strictly_increasing_transform']['offset']
assert np.isclose(roc_auc_score(labels01.astype(int),shifted),float(expected))
t=f['base_threshold'];shifted_t=f['transformed_threshold']
base_c=counts_at(np.array(yy),np.array(ss),t);shift_c=counts_at(np.array(yy),shifted,t)
assert base_c==f['expected_base_counts'] and shift_c==f['expected_same_fixed_numeric_threshold_counts']
assert np.isclose(rates(base_c)['F1'],float(frac(f['expected_base_F1_fraction'])))
assert np.isclose(rates(shift_c)['F1'],float(frac(f['expected_same_fixed_numeric_threshold_F1_fraction'])))
assert np.array_equal(np.array(ss)>=t,shifted>=shifted_t)
a=fixed['deterministic_all_tie_imbalanced'];alltie=roc_auc_score((np.array(a['labels'])==1).astype(int),a['scores']);constant_pred=np.where(np.array(a['scores'])>=a['threshold'],1,-1)
assert np.isclose(alltie,float(frac(a['expected_auc_fraction'])))
accuracy=float((constant_pred==a['labels']).mean());assert np.isclose(accuracy,float(frac(a['expected_accuracy_fraction'])))
alltie_c=counts_at(np.array(a['labels']),np.array(a['scores']),a['threshold']);assert rates(alltie_c)['F1']==0
u=f['unknown_row'];uy=np.array(yy+[u['label']]);us=np.array(ss+[u['score']]);known=np.isin(uy,[-1,1])
filtered=roc_auc_score((uy[known]==1).astype(int),us[known]);unknown_wrong=roc_auc_score((uy==1).astype(int),us)
assert np.isclose(filtered,float(expected)) and np.isclose(unknown_wrong,float(frac(f['wrong_unknown_to_negative_auc_fraction'])))
missing=[]
for c in fixed['missing_class_cases']:
    y=np.array(c['labels']);s=np.array(c['scores']);known=np.isin(y,[-1,1]);y=y[known];s=s[known]
    assert pair_reference(y.tolist(),s.tolist()) is None and roc_reference(y.tolist(),s.tolist()) is None
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        try:
            value=roc_auc_score((y==1).astype(int),s)
            assert np.isnan(value),'library unexpectedly reports numeric AUC without both classes'
            observed={'value':'NaN','warnings':[str(x.message) for x in w]}
        except ValueError as exc:observed={'exception':'ValueError','message':str(exc),'traceback':traceback.format_exc(),'warnings':[str(x.message) for x in w]}
    missing.append({'name':c['name'],'mathematical_status':'undefined P*N=0','library':observed})
negative=[]
def detect(name,wrong,right,scope):
    try:
        assert np.isclose(float(wrong),float(right)),name
    except AssertionError:
        negative.append({'name':name,'expected':'reviewer oracle rejects incorrect result','actual':'rejected by numerical mismatch','wrong_result':float(wrong),'correct_result':float(right),'scope':scope,'detector':'reviewer comparison, not a student answer checker','traceback':traceback.format_exc()})
    else:raise RuntimeError('negative control was not discriminated: '+name)
detect('tie_zero_credit',pair_reference(yy,ss,Fraction(0)),expected,'reviewer pair-formula mutation; no pair helper exists in candidate')
detect('tie_full_credit',pair_reference(yy,ss,Fraction(1)),expected,'reviewer pair-formula mutation')
detect('wrong_positive_score_direction',reverse,expected,'actual candidate-imported sklearn roc_auc_score called with wrong-directed input')
detect('ROC_axes_swapped',auc(actual_curve[1],actual_curve[0]),expected,'actual candidate-imported sklearn auc called with swapped axes')
detect('hard_predictions_instead_of_score_ranking',roc_auc_score(labels01.astype(int),(np.array(ss)>=t).astype(int)),expected,'actual candidate-imported sklearn roc_auc_score on disclosed hard decisions; valid different quantity, wrong full-score target')
detect('unknown_treated_as_negative',unknown_wrong,expected,'actual sklearn call with unfiltered y==1; lesson final text must require prior filtering')
try:
    forced_numeric_auc=0.5
    assert forced_numeric_auc is None,'numeric fallback cannot represent undefined AUC'
except AssertionError:
    negative.append({'name':'class_absence_forced_half','expected':'reject numeric fallback when reference status is undefined','actual':'rejected','wrong_result':forced_numeric_auc,'correct_result':None,'scope':'reviewer explicit semantic guard, not candidate/library guard','detector':'reviewer assertion','traceback':traceback.format_exc()})
else:raise RuntimeError('undefined-AUC guard was not discriminated')
detect('AUC_half_asserted_to_mean_accuracy_half',0.5,accuracy,'deterministic constant-score counterexample to interpretation; not executable candidate prose')
# Existing provided-cell assertions already ran. Check native helper state and blank student cell explicitly.
assert np.isclose(transformer.named_transformers_['num'].named_steps['median'].statistics_[0],4)
assert np.isclose(val_encoded.loc['c6','num__recent'],1.5)
assert counts_at(truth,scores,1.5)=={'TP':2,'FP':1,'TN':1,'FN':0}
assert not ast.parse(_review_candidate_cell_sources[22]).body
report={'scope':'actual candidate imported sklearn metrics + native counts/rates, compared with separately written Python/Fraction reference; no custom student AUC helper is supplied','sklearn_version':sklearn.__version__,'frozen_expected_fraction':str(expected),'reference_pair':str(pair),'reference_ROC_area':str(area),'actual_ROC_area':float(actual_area),'actual_ranking_AUC':float(actual_rank),'reverse_AUC':float(reverse),'label_swap_AUC':float(swap),'swap_and_reverse_AUC':float(both),'F1_original':rates(base_c)['F1'],'F1_same_numeric_threshold_after_shift':rates(shift_c)['F1'],'AUC_preserved_after_shift':True,'predictions_preserved_after_threshold_shift':True,'all_tie_AUC':float(alltie),'all_tie_deterministic_accuracy':accuracy,'unknown_filter_preserves_expected':True,'missing_class':missing,'negative_controls':negative,'blank_student_answer':True,'student_performance_time':'not_observed'}
print(json.dumps(report,ensure_ascii=False,indent=2))
