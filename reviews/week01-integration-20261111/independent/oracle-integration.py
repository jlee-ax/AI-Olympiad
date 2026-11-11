# Independent review code in the live fresh kernel; it is not a student solution.
from fractions import Fraction as F
import itertools,json,math,io,tempfile
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
qa_checks=[]
qa_values=[([0,None,np.nan,6],3),([0],0),([None,np.nan],None),([],None),([1_000_000]*10_000,1_000_000),([-1_000_000]*10_000,-1_000_000),([0,None]*5000,0),([1_000_000,-1_000_000]*5000,0)]
for qa_input,qa_expected in qa_values:
    qa_copy=qa_input.copy();qa_actual=observed_mean(qa_input)
    assert qa_actual is None if qa_expected is None else math.isfinite(qa_actual) and np.isclose(qa_actual,qa_expected)
    assert all((pd.isna(a) and pd.isna(b)) or a==b for a,b in zip(qa_input,qa_copy))
assert water_average==F(120,5)==24
assert float(F(8,3))==three_heights.var(ddof=0)
assert np.array_equal(light_by_day,[[2,2],[3,3],[6,6]])
assert np.allclose(light_by_day.mean(axis=0),[float(F(11,3)),float(F(11,3))])
assert np.array_equal(reshaped,[[2,2,3],[3,6,6]]) and np.array_equal(transposed,[[2,3,6],[2,3,6]])
qa_bank=json.loads(Path('/workspace/scratch/d500e5cb2076/ai-olympiad-course-revision/reviews/week01-integration-20261111/independent/independent-input-bank-v1.json').read_text())
qa_a=np.array(qa_bank['array']['input'])
assert qa_a.mean(axis=0).tolist()==[3,7,11] and qa_a.mean(axis=1).tolist()==[4,10]
assert qa_a.reshape(3,2).tolist()==qa_bank['array']['reshape_3_2']
assert qa_a.T.tolist()==qa_bank['array']['transpose_3_2']
assert (qa_a+[1,10,100]).tolist()==qa_bank['array']['column_result']
assert (qa_a+[[1000],[2000]]).tolist()==qa_bank['array']['row_result']
try:qa_a+np.array([1,2])
except ValueError:pass
else:raise AssertionError('bad broadcasting shape survived')
qa_checks.append('bounded mean None/NaN/zero/extremes; Fraction variance; new axis/reshape/broadcast inputs')
assert training.pot_id.tolist()==['P01','P02','P03','P04']
assert validation.pot_id.tolist()==['P05','P06']
assert list(x_train.columns)==['water_ml'] and x_train.shape==(4,1)
assert y_train.tolist()==[0,0,1,1] and y_validation.tolist()==[1,1]
assert fill.statistics_.tolist()==[20] and model.classes_.tolist()==[0,1]
assert model.centroids_.ravel().tolist()==[10,30]
assert predictions.tolist()==[0,1] and validation_accuracy==F(1,2)
assert fixed_height==9 and p02['height_cm']-fixed_height==1
qa_mean_changed=F(0+20+60,3);qa_positive_changed=(qa_mean_changed+60)/2
assert np.allclose(changed_fill.statistics_,[float(qa_mean_changed)])
assert np.allclose(changed_model.centroids_.ravel(),[10,float(qa_positive_changed)])
assert (original_prediction,changed_prediction)==(1,0)
qa_y_changed=training.copy();qa_y_changed.loc[qa_y_changed.pot_id=='P03','height_cm']=10
qa_fill_y=SimpleImputer(strategy='mean');qa_x_y=qa_fill_y.fit_transform(qa_y_changed[['water_ml']])
qa_model_y=NearestCentroid().fit(qa_x_y,(qa_y_changed.height_cm>=12).astype(int))
assert np.allclose(qa_model_y.centroids_.ravel(),[float(F(40,3)),40])
assert int(qa_model_y.predict(qa_fill_y.transform(pd.DataFrame({'water_ml':[25]})))[0])==0
qa_before=(fill.statistics_.copy(),model.centroids_.copy())
qa_v=validation.copy();qa_v.loc[:,'water_ml']=[-1_000_000,1_000_000];qa_v.loc[:,'height_cm']=0
model.predict(fill.transform(qa_v[['water_ml']]))
assert np.array_equal(fill.statistics_,qa_before[0]) and np.array_equal(model.centroids_,qa_before[1])
qa_scaled_fill=SimpleImputer(strategy='mean');qa_scaled_x=qa_scaled_fill.fit_transform(training[['water_ml']]*0.001)
qa_scaled_model=NearestCentroid().fit(qa_scaled_x,y_train)
assert qa_scaled_model.predict(qa_scaled_fill.transform(probe*0.001)).tolist()==model.predict(fill.transform(probe)).tolist()
qa_checks.append('train X and y change learned state/prediction; validation cannot refit; consistent one-feature units invariant')
qa_expected_ids={'P05':0,'P06':1}
assert dict(zip(result.pot_id,result.prediction))==qa_expected_ids,'ID-to-model prediction mismatch'
assert restored.pot_id.tolist()==['P05','P06'] and restored.prediction.tolist()==[0,1]
assert checked.columns.tolist()==['pot_id','prediction'] and file_check.columns.tolist()==['pot_id','prediction']
assert not result_path.exists() and not result_path.parent.exists()
for qa_perm in itertools.permutations(range(2)):
    qa_frame=validation.iloc[list(qa_perm)]
    qa_map=dict(zip(qa_frame.pot_id,model.predict(fill.transform(qa_frame[['water_ml']]))))
    assert qa_map==qa_expected_ids
qa_checks.append('baseline CSV exact header and ID/model provenance; physical CSV cleaned')
# New specification: reviewer reference with chosen models, no code inserted into blank student cell.
qa_known=exercise_train[exercise_train.label.isin(['정상','점검'])].copy()
assert qa_known.unit.tolist()==['T1','T2','T3','T4']
qa_manual_mean=sum(F(v) for v in qa_known.signal if not pd.isna(v))/3
assert qa_manual_mean==2
qa_models=[]
def qa_predict_pairs(qa_imputer,qa_classifier,qa_frame):
    if not {'unit','signal'}.issubset(qa_frame.columns):raise ValueError('missing input column')
    if qa_frame.unit.isna().any() or qa_frame.unit.duplicated().any():raise ValueError('missing or duplicate ID')
    return dict(zip(qa_frame.unit,qa_classifier.predict(qa_imputer.transform(qa_frame[['signal']]))))
def qa_format_check(qa_text,qa_expected=None):
    qa_table=pd.read_csv(io.StringIO(qa_text))
    assert qa_table.columns.tolist()==['sample_id','prediction'],'wrong header/index/columns'
    assert qa_table.sample_id.tolist()==exercise_order,'wrong ID order/count'
    assert set(qa_table.prediction)<=set(['정상','점검']),'wrong label meanings'
    if qa_expected is not None:assert dict(zip(qa_table.sample_id,qa_table.prediction))==qa_expected,'wrong ID-prediction provenance'
    return qa_table
for qa_name,qa_classifier in [('nearest_centroid',NearestCentroid()),('decision_tree',DecisionTreeClassifier(max_depth=1,random_state=0))]:
    qa_imputer=SimpleImputer(strategy='mean');qa_filled=qa_imputer.fit_transform(qa_known[['signal']]);qa_classifier.fit(qa_filled,qa_known.label)
    assert qa_imputer.statistics_.tolist()==[2]
    qa_val=qa_classifier.predict(qa_imputer.transform(exercise_validation[['signal']])).tolist()
    qa_pairs=qa_predict_pairs(qa_imputer,qa_classifier,exercise_input)
    qa_out=pd.DataFrame({'sample_id':exercise_order,'prediction':[qa_pairs[x] for x in exercise_order]})
    qa_text=qa_out.to_csv(index=False,lineterminator='\n');qa_format_check(qa_text,qa_pairs)
    with tempfile.TemporaryDirectory(prefix='reviewer-independent-csv-') as qa_dir:
        qa_path=Path(qa_dir)/'reviewer-answer.csv';qa_out.to_csv(qa_path,index=False);qa_format_check(qa_path.read_text(),qa_pairs)
    qa_probe_label=qa_classifier.predict(qa_imputer.transform(pd.DataFrame({'signal':[1.5]}))).tolist()[0]
    if qa_name=='nearest_centroid':
        assert dict(zip(qa_classifier.classes_,qa_classifier.centroids_.ravel()))=={'정상':1,'점검':3}
        assert qa_val==['정상','점검','정상'] and qa_pairs=={'N3':'점검','N1':'정상','N7':'정상'}
    else:assert qa_classifier.tree_.node_count>1
    for qa_wrong in [exercise_input.drop(columns='signal'),pd.concat([exercise_input,exercise_input.iloc[:1]])]:
        try:qa_predict_pairs(qa_imputer,qa_classifier,qa_wrong)
        except ValueError:pass
        else:raise AssertionError('new-spec reviewer guard accepted missing-column/duplicate-ID')
    qa_models.append({'model':qa_name,'validation_predictions':qa_val,'accuracy':sum(a==b for a,b in zip(qa_val,exercise_validation.label))/3,'probe_1_5_prediction':qa_probe_label,'ordered_csv':qa_text,'physical_csv_reopened':True})
assert qa_models[0]['probe_1_5_prediction']!=qa_models[1]['probe_1_5_prediction'],'different valid trained models should be accepted on a new probe'
qa_constant='sample_id,prediction\nN7,정상\nN3,정상\nN1,정상\n';qa_format_check(qa_constant)
try:qa_format_check(qa_constant,{'N7':'정상','N3':'점검','N1':'정상'})
except AssertionError:pass
else:raise AssertionError('format alone falsely certified model provenance')
qa_csv_mutants={'header':'unit,prediction\nN7,정상\nN3,점검\nN1,정상\n','extra_index':',sample_id,prediction\n0,N7,정상\n1,N3,점검\n2,N1,정상\n','wrong_order':'sample_id,prediction\nN3,점검\nN1,정상\nN7,정상\n','wrong_label':'sample_id,prediction\nN7,?\nN3,점검\nN1,정상\n','same_length_predictions_only_reversed':'sample_id,prediction\nN7,정상\nN3,정상\nN1,점검\n'}
for qa_name,qa_text in qa_csv_mutants.items():
    try:qa_format_check(qa_text,{'N7':'정상','N3':'점검','N1':'정상'})
    except AssertionError:pass
    else:raise AssertionError(qa_name+' not detected')
qa_unknown=exercise_train.copy();qa_unknown.loc[qa_unknown.label=='?','signal']=1_000_000
qa_unknown_known=qa_unknown[qa_unknown.label.isin(['정상','점검'])]
assert SimpleImputer(strategy='mean').fit(qa_unknown_known[['signal']]).statistics_.tolist()==[2]
qa_checks.append('new string-label/unknown contract; real reviewer CSV; 2 valid classifiers; 5 malformed outputs; format vs model provenance')
print(json.dumps({'independent_checks':qa_checks,'models':qa_models,'student_answer_completed':False,'student_learning_or_time_observed':False},ensure_ascii=False))
