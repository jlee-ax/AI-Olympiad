import json,traceback,ast
from pathlib import Path
D=Path.cwd().parents[1];f=json.loads((D/'frozen-inputs-v2.json').read_text());d=f['decision'];rows=d['validation_ledger'];known=[r for r in rows if r['truth']!=d['unknown_label']]
y=np.array([r['truth'] for r in known]);s=np.array([r['score'] for r in known]);stats={}
for t in d['candidate_thresholds']:
 c=counts_at(y,s,t);r=rates(c);pred=np.where(s>=t,1,-1)
 group={g:np.mean([int(p==row['truth']) for row,p in zip(known,pred) if row['entity']==g]) for g in {row['entity'] for row in known}}
 r['mean_entity_accuracy']=float(np.mean(list(group.values())))
 r['truth_weighted_accuracy']=weighted_accuracy(np.where(y==1,'T','B'),np.where(pred==1,'T','B'),target_weight=d['target_truth_weight'])
 r['overall_accuracy']=r['accuracy'];stats[t]={'counts':c,'metrics':r,'prediction':pred.tolist()}
 exp=next(e for e in d['expected_metrics'] if e['threshold']==t)
 for k in ['TP','FP','TN','FN']:assert c[k]==exp[k]
 for metric,key in [('overall_accuracy','accuracy_fraction'),('mean_entity_accuracy','entity_accuracy_fraction'),('truth_weighted_accuracy','truth_weighted_accuracy_fraction')]:assert np.isclose(r[metric],exp[key][0]/exp[key][1])
selected={metric:max(d['candidate_thresholds'],key=lambda t:(stats[t]['metrics'][metric],t)) for metric in d['expected_selected_threshold']}
assert selected==d['expected_selected_threshold']
locked=("truth_weighted_accuracy",selected['truth_weighted_accuracy'],">=","highest threshold on tie")
by_id={r['id']:(1 if r['score']>=locked[1] else -1) for r in d['unlabeled_application_rows']};applied=[by_id[k] for k in d['required_output_id_order']]
assert applied==d['expected_predictions_in_required_order_for_weighted_objective']
neg=[]
for name,wrong,correct in [('wrong-metric-for-weighted-task',selected['overall_accuracy'],selected['truth_weighted_accuracy']),('minimize-instead-of-maximize',min(d['candidate_thresholds'],key=lambda t:stats[t]['metrics']['truth_weighted_accuracy']),selected['truth_weighted_accuracy'])]:
 try:assert wrong==correct
 except AssertionError:neg.append({'name':name,'detected':True,'traceback':traceback.format_exc()})
 else:raise AssertionError('wrong decision escaped')
# Candidate's actual boundary helper must move tied score rows together.
c=counts_at(y,s,0.5);strict=counts_at(y,np.nextafter(s,-np.inf),0.5);assert c!=strict
wrong_rows=[dict(r,truth=-1 if r['truth']==0 else r['truth']) for r in rows]
def macro(t):
 groups={r['entity'] for r in wrong_rows};return np.mean([np.mean([(1 if r['score']>=t else -1)==r['truth'] for r in wrong_rows if r['entity']==g]) for g in groups])
wrong_unknown_choice=max(d['candidate_thresholds'],key=lambda t:(macro(t),t));assert wrong_unknown_choice!=selected['mean_entity_accuracy']
tie=json.loads((D/'threshold-tie-input-addendum.json').read_text());tv=tie['validation'];ty=np.array(tv['truth']);ts=np.array(tv['scores']);scores_by_t={t:rates(counts_at(ty,ts,t))['accuracy'] for t in tv['candidate_thresholds']}
assert len(set(scores_by_t.values()))==1
chosen=max(tv['candidate_thresholds'],key=lambda t:(scores_by_t[t],t));assert chosen==tie['expected_selected_threshold']
newscore=tie['new_unlabeled_rows'][0]['score'];tiepred=[1 if newscore>=t else -1 for t in tv['candidate_thresholds']];assert tiepred[0]!=tiepred[1] and [1 if newscore>=chosen else -1]==tie['expected_selected_prediction']
# Reviewer solution of actual candidate's open exercise; not a student answer.
raw=pd.DataFrame([('M',1,5.),('M',2,7.),('M',3,9.),('M',4,np.nan),('N',1,np.nan),('N',2,np.nan),('N',3,np.nan),('N',4,1.),('P',1,7.),('P',2,9.),('P',3,11.),('P',4,np.nan),('P',6,17.),('Q',1,np.nan),('Q',2,0.),('Q',3,np.nan),('Q',4,np.nan),('Q',6,11.)],columns=['unit','time','reading'])
tr=pd.DataFrame([('M4','M',4,'gold',-1),('M5','M',5,'gold',1),('N4','N',4,'silver',-1),('N5','N',5,'silver',1)],columns=['id','unit','time','kind','label']);va=pd.DataFrame([('P6','P',6,'bronze',1),('P7','P',7,'bronze',-1),('Q6','Q',6,'gold',1),('Q7','Q',7,'gold',-1)],columns=tr.columns)
assert set(tr.unit).isdisjoint(va.unit) and tr.time.max()<va.time.min()
tx=make_features(raw,tr);vx=make_features(raw,va)
num=Pipeline([('median',SimpleImputer(strategy='median')),('range',MinMaxScaler())]);num.fit(tx[['recent']]);vscore=num.transform(vx[['recent']]).ravel();assert np.allclose(vscore,[1.25,2,-.125,1.25])
choices=[2,1.25,-.125,-1];f1s={t:rates(counts_at(va.label.to_numpy(),vscore,t))['F1'] for t in choices};fixed=max(choices,key=lambda t:(f1s[t],t));assert fixed==-.125
unlab=pd.DataFrame([('R',1,3.),('R',2,5.),('R',7,9.),('S',1,2.),('S',2,1.),('S',7,0.),('U',1,3.),('U',2,1.),('U',7,-1.)],columns=raw.columns);targets=pd.DataFrame([('R8','R',8,'bronze'),('S8','S',8,'gold'),('U8','U',8,'silver')],columns=['id','unit','time','kind'])
before=(num.named_steps['median'].statistics_.copy(),num.named_steps['range'].data_min_.copy(),num.named_steps['range'].data_max_.copy());newx=make_features(unlab,targets);new_scores=num.transform(newx[['recent']]).ravel();pred=np.where(new_scores>=fixed,1,-1);assert pred.tolist()==[1,1,-1]
assert all(np.array_equal(a,b) for a,b in zip(before,(num.named_steps['median'].statistics_,num.named_steps['range'].data_min_,num.named_steps['range'].data_max_)))
assert np.where(new_scores>=-1,1,-1).tolist()!=pred.tolist()
assert not ast.parse(_review_candidate_cell_sources[22]).body
print(json.dumps({'scope':'actual candidate counts/rates/weighted_accuracy/make_features helpers plus labelled reviewer decision/CV-independent exercise procedure; student22 blank','frozen_metrics':stats,'selected':selected,'locked_policy':locked,'unlabeled_predictions_in_required_order':applied,'negative_controls':neg,'wrong_unknown_policy_choice_differs':True,'native_strict_threshold_counterexample_detected':True,'independent_validation_tie_same_score':scores_by_t,'independent_tie_selected':chosen,'independent_tie_new_predictions_differ':True,'candidate_open_exercise_reference':{'selected_threshold':fixed,'candidate_F1':f1s,'new_row_ids':targets.id.tolist(),'new_scores':new_scores.tolist(),'predictions':pred.tolist(),'fit_stats_unchanged':True},'student_achievement':'not_observed'},ensure_ascii=False,indent=2))
