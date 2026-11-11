import ast,json,traceback,warnings
from pathlib import Path
D=Path.cwd().parents[1];f=json.loads((D/'frozen-inputs-v1.json').read_text());m=f['majority']
def native_label(v):
    if isinstance(v,(bool,np.bool_)):return v
    if isinstance(v,(int,float)) and v in [-1,0,1]:return {-1:'B',0:0,1:'T'}[v]
    return v
raw=[native_label(r['y']) for r in m['training_rows']]
model,chosen,mask=fit_known_mode(raw)
assert chosen=='B' and mask.tolist()==[r['y']!=0 for r in m['training_rows']]
prior=dict(zip(model.classes_.tolist(),model.class_prior_.tolist()));assert np.isclose(prior['B'],2/3) and np.isclose(prior['T'],1/3)
qx=np.array([np.nan if r['x'] is None else r['x'] for r in m['query_rows']]).reshape(-1,1)
pred=model.predict(qx);assert pred.tolist()==['B']*len(qx)
assert np.array_equal(pred,model.predict(np.array([9e4,-9e4,0,7]).reshape(-1,1)))
before=(model.classes_.copy(),model.class_prior_.copy())
val_reports=[]
for vy in m['validation_label_variants']:
    changed_truth=np.array([native_label(y) for y in vy]);after=model.predict(qx)
    assert np.array_equal(after,pred) and np.array_equal(before[0],model.classes_) and np.array_equal(before[1],model.class_prior_)
    val_reports.append({'changed_validation_truth':changed_truth.tolist(),'predictions_unchanged':True,'fit_state_unchanged':True})
reversed_raw=list(raw)
for change in m['training_frequency_reversal_changes']:
    i=next(i for i,r in enumerate(m['training_rows']) if r['id']==change['id']);reversed_raw[i]=native_label(change['y'])
reverse_model,reverse_chosen,_=fit_known_mode(reversed_raw);assert reverse_chosen=='T' and reverse_model.predict(qx).tolist()==['T']*len(qx)
permuted,permuted_chosen,_=fit_known_mode([raw[i] for i in m['permutation']]);assert permuted_chosen==chosen and np.array_equal(permuted.predict(qx),pred)
zero_model,zero_label,zero_mask=fit_known_mode(['B','B','T',0.0]);assert zero_label=='B' and zero_mask.tolist()==[True,True,True,False]
# Unknown-majority augmentation follows the frozen unknown-exclusion criterion; candidate input values were not used.
unknown_heavy=raw+m['no_known_cases'][0]*len(raw);um,ul,uk=fit_known_mode(unknown_heavy);assert ul==chosen and int(uk.sum())==int(mask.sum())
rejections=[]
def reject(name,arg,fragment=None):
    try:fit_known_mode(arg)
    except ValueError as ex:
        if fragment is not None:assert fragment in str(ex),(name,str(ex))
        rejections.append({'case':name,'expected':'ValueError for documented contract','actual':'ValueError','message':str(ex),'traceback':traceback.format_exc(),'detector':'actual candidate fit_known_mode guard'})
    else:raise AssertionError('candidate accepted forbidden input: '+name)
for val in [True,False,np.bool_(True),np.bool_(False)]:reject('boolean_'+str(type(val).__name__)+'_'+str(val),['B','B','T',val],'B/T/0')
for i,arg in enumerate(m['invalid_label_cases']):reject('invalid_label_'+str(i),[native_label(v) for v in arg],'B/T/0')
reject('raw_numeric_pm1_not_native_contract',[1,-1,0],'B/T/0')
for i,arg in enumerate(m['no_known_cases']):reject('no_known_'+str(i),arg,'알려진')
reject('tie_declared_stop_policy',[native_label(v) for v in m['tie_case']['labels']],'동률')
one=[]
for c in m['single_class_cases']:
    mm,cl,km=fit_known_mode([native_label(y) for y in c['labels']]);assert cl==native_label(c['expected_class'])
    assert mm.classes_.tolist()==[cl] and mm.predict_proba(qx).shape==(len(qx),1)
    one.append({'known_class':cl,'classes':mm.classes_.tolist(),'proba_columns':1})
# Actual returned model is a most_frequent classifier; X placeholders inside the helper do not take frozen feature values.
# Separately fit the same estimator type to two changed X arrays with the same known y to check feature independence.
known_labels=np.asarray(raw,dtype=object)[mask].astype(str);x1=np.array([r['x'] for r in m['training_rows']])[mask].reshape(-1,1);x2=-x1+333
mx1=type(model)(strategy='most_frequent').fit(x1,known_labels);mx2=type(model)(strategy='most_frequent').fit(x2,known_labels)
assert np.array_equal(mx1.predict(qx),mx2.predict(qx))
neg=[]
def differs(name,wrong,expected,scope):
    try:assert wrong==expected,name
    except AssertionError:neg.append({'case':name,'expected':'reviewer oracle detects mismatch','actual':'detected','wrong':wrong,'correct':expected,'scope':scope,'traceback':traceback.format_exc()})
    else:raise AssertionError('negative control did not discriminate: '+name)
leaky,leak_chosen,_=fit_known_mode(raw+[native_label(y) for y in m['validation_label_variants'][1]])
differs('validation_labels_appended_to_training',leak_chosen,chosen,'actual helper accepts supplied labels but cannot infer their data origin; reviewer detects wrong caller boundary')
y=np.array([r['y'] for r in f['rare_evaluation']['rows']]);bpred=model.predict(np.arange(len(y)).reshape(-1,1));zpred=np.array([r['candidate_z'] for r in f['rare_evaluation']['rows']]);stats={}
for name,pp,key in [('baseline',np.where(bpred=='T',1,-1),'baseline_expected'),('candidate_z',zpred,'candidate_z_expected')]:
    c=counts_at(y,pp,0);r=rates(c);e=f['rare_evaluation'][key]
    assert c=={k:e[k] for k in ['TP','FP','TN','FN']}
    for metric in ['accuracy','recall','F1']:
        a,b=e[metric+'_fraction'];assert np.isclose(r[metric],a/b)
    if e.get('precision','defined') is None:assert r['precision'] is None
    else:a,b=e['precision_fraction'];assert np.isclose(r['precision'],a/b)
    native_actual=np.where(y==1,'T','B');native_pred=np.where(pp==1,'T','B')
    w=weighted_accuracy(native_actual,native_pred,target_weight=f['rare_evaluation']['target_truth_weight']);a,b=e['truth_weighted_fraction'];assert np.isclose(w,a/b)
    with warnings.catch_warnings(record=True) as warnings_seen:
        warnings.simplefilter('always');p0,r0,f0,_=precision_recall_fscore_support(native_actual,native_pred,average='binary',pos_label='T',zero_division=np.nan)
    if name=='baseline':assert np.isnan(p0) and r0==0 and f0==0
    stats[name]={'counts':c,'metrics':r,'truth_weighted':float(w),'native_precision_policy_nan':'NaN' if np.isnan(p0) else float(p0),'warnings':[str(v.message) for v in warnings_seen]}
choices={metric:max(stats,key=lambda n:stats[n]['truth_weighted'] if metric=='truth_weighted' else stats[n]['metrics'][metric]) for metric in ['accuracy','recall','F1','truth_weighted']}
assert choices==f['rare_evaluation']['metric_choices']
# Unknown row is filtered in both truth and predictions; the helper's native B/T metric contract does not auto-filter it.
extra=f['rare_evaluation']['unknown_extra'];yextra=np.append(y,extra['y']);pextra=np.append(zpred,extra['candidate_z']);kk=np.isin(yextra,[-1,1]);assert counts_at(yextra[kk],pextra[kk],0)==stats['candidate_z']['counts']
zero=[]
for q in f['zero_denominator_cases']:
    cc=counts_at(np.array(q['truth']),np.array(q['prediction']),0);rr=rates(cc)
    for k in ['accuracy','precision','recall','F1']:
        if k in q:assert rr[k]==q[k],(q['name'],k,rr[k])
    zero.append({'name':q['name'],'actual_counts':cc,'mathematical_rates':rr})
lookup={r['id']:r['candidate_z'] for r in f['rare_evaluation']['rows']};ordered=[lookup[i] for i in f['rare_evaluation']['required_output_order']];assert ordered==f['rare_evaluation']['candidate_z_predictions_in_required_order']
differs('wrong_prediction_ID_order',list(reversed(ordered)),ordered,'reviewer nonconstant peer prediction ledger; constant predictions alone cannot detect row reordering')
differs('accuracy_used_for_predeclared_F1_objective',choices['accuracy'],choices['F1'],'reviewer objective comparison using actual native metric results')
# Separate synthetic split reference, not a candidate helper and not an official Robot dataset split.
sf=f['split_reference'];byid={r['id']:r for r in sf['rows']}
def split_check(part,goal='same_ids_unseen_combinations',requested=()):
    tr=part['train_ids'];va=part['validation_ids']
    if not tr or not va or len(set(tr))!=len(tr) or len(set(va))!=len(va) or set(tr)&set(va) or set(tr)|set(va)!=set(byid):raise ValueError('invalid row partition')
    if any(k not in sf['available_input_fields'] for k in requested):raise ValueError('requested history/input is unavailable')
    T=[byid[k] for k in tr];V=[byid[k] for k in va]
    if goal=='same_ids_unseen_combinations':
        if {r['entity'] for r in T}!={r['entity'] for r in V}:raise ValueError('different entity set changes deployment target')
        keys=lambda a:{(r['colour'],r['object']) for r in a}
        if keys(T)&keys(V):raise ValueError('heldout combination leakage')
        for col in ['colour','object']:
            if not {r[col] for r in V}<={r[col] for r in T}:raise ValueError('unseen primitive is a different target')
    elif goal=='new_entity':
        if {r['entity'] for r in T}&{r['entity'] for r in V}:raise ValueError('entity overlap for unseen entity goal')
    else:raise ValueError('unknown goal')
    return True
splits={'scope':'reviewer synthetic reference only; no candidate split validator is supplied','valid_family_a':split_check(sf['valid_family_a']),'valid_family_b':split_check(sf['valid_family_b']),'different_goal_new_entity':split_check(sf['different_goal_new_entity_partition'],'new_entity'),'expected_rejections':[]}
for name,fn in [('combination_leak',lambda:split_check(sf['invalid_combination_leak'])),('missing_history',lambda:split_check(sf['valid_family_a'],requested=sf['invalid_feature_request'])),('new_entity_split_for_wrong_goal',lambda:split_check(sf['different_goal_new_entity_partition']))]:
    try:fn()
    except ValueError as ex:splits['expected_rejections'].append({'case':name,'actual':'ValueError','message':str(ex),'traceback':traceback.format_exc(),'detector':'reviewer reference only'})
    else:raise AssertionError('split reference accepted: '+name)
assert not ast.parse(_review_candidate_cell_sources[23]).body
assert np.isclose(worked_auc,0.5) and np.isclose(transformer.named_transformers_['num'].named_steps['median'].statistics_[0],4)
print(json.dumps({'scope':'actual fit_known_mode returned models/native metrics plus separately labelled reviewer reference; frozen ±1 labels are explicitly mapped to B/T before native helper calls','actual_chosen':chosen,'actual_prior':prior,'zero_float_accepted':True,'unknown_heavy_excluded':True,'validation_label_changes':val_reports,'training_frequency_reversal':reverse_chosen,'training_permutation_unchanged':True,'query_X_change_predictions_unchanged':True,'separate_model_X_fit_change_unchanged':True,'candidate_rejections':rejections,'one_class':one,'rare_metrics':stats,'objective_choices':choices,'zero_denominators':zero,'negative_controls':neg,'split_reference':splits,'blank_student_answer':True,'student_performance_time':'not_observed'},ensure_ascii=False,indent=2))
