import ast,json
from sklearn.tree import DecisionTreeClassifier
# This is the reviewer's solution of the candidate's unchanged blank assessment.
def _sensor(panel):return sum(1 for r in range(2) for c in range(2) if panel[r,c,0]==1 and panel[r,c,1]==2)
known=exercise_train.loc[exercise_train.label.isin(['정상','점검'])].copy()
review_fill=SimpleImputer(strategy='mean').fit(known[['signal']])
def _features(t):return np.column_stack((review_fill.transform(t[['signal']]).ravel(),[_sensor(p) for p in t.panel]))
rx=_features(known);vx=_features(exercise_validation);nx=_features(exercise_input)
assert not np.array_equal(rx,x_train)
expected_x=[[0,3],[3,1],[4,2],[9,0]]
models={'centroid':NearestCentroid().fit(rx,known.label),'tree_depth2':DecisionTreeClassifier(max_depth=2,random_state=0).fit(rx,known.label)}
answers={}
for name,m in models.items():
 vp=m.predict(vx);pred=m.predict(nx);byid=dict(zip(exercise_input.unit,pred))
 frame=pd.DataFrame({'sample_id':exercise_order,'prediction':[byid[x] for x in exercise_order]})
 text=frame.to_csv(index=False,lineterminator='\n');check=pd.read_csv(StringIO(text))
 assert check.columns.tolist()==['sample_id','prediction'] and check.sample_id.tolist()==['N7','N3','N1']
 assert set(check.prediction).issubset({'정상','점검'})
 answers[name]={'validation':vp.tolist(),'accuracy':float(np.mean(vp==exercise_validation.label.to_numpy())),'submission':check.values.tolist()}
centers={label:center.tolist() for label,center in zip(models['centroid'].classes_,models['centroid'].centroids_)}
report={'scope':'reviewer_reference_solution_not_candidate_student_answer','expected':{'mean':4,'wrong_unknown_included_mean':28,'training_X':expected_x,'centers':{'정상':[1.5,2],'점검':[6.5,1]},'centroid_validation':['정상','점검','정상'],'alternative_validation':['정상','점검','점검'],'submission_order':['N7','N3','N1']},'actual':{'known_ids':known.unit.tolist(),'mean':float(review_fill.statistics_[0]),'all_train_observed_mean':float(exercise_train.signal.mean()),'training_X':rx.tolist(),'centers':centers,'models':answers,'student_answer_blank':not ast.parse(_review_candidate_cell_sources[36]).body}}
print(json.dumps(report,ensure_ascii=False,indent=2))
assert np.array_equal(rx,expected_x) and review_fill.statistics_[0]==4 and exercise_train.signal.mean()==28
assert centers=={'점검':[6.5,1.0],'정상':[1.5,2.0]} or centers=={'정상':[1.5,2.0],'점검':[6.5,1.0]}
assert answers['centroid']['validation']==['정상','점검','정상'] and np.isclose(answers['centroid']['accuracy'],2/3)
assert answers['tree_depth2']['validation']==['정상','점검','점검'] and answers['tree_depth2']['accuracy']==1
assert answers['centroid']['submission']==[['N7','점검'],['N3','점검'],['N1','정상']]
assert report['actual']['student_answer_blank']
# Missing column / duplicate ID diagnostics are reviewer examples, not filled student code.
for invalid in [exercise_input.drop(columns='signal'),pd.concat([exercise_input,exercise_input.iloc[:1]])]:
 assert 'signal' not in invalid.columns or invalid.unit.duplicated().any()
