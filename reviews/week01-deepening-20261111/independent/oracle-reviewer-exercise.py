import ast
import json,tempfile
from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
# Reviewer implementation of the student exercise; the student answer remains blank.
def sensor_count(panel):
    return sum(1 for r in range(2) for c in range(2) if panel[r,c,0]==1 and panel[r,c,1]==2)
def review_features(table,imputer):
    return np.column_stack((imputer.transform(table[['signal']]).ravel(),[sensor_count(x) for x in table.panel]))
known=exercise_train.loc[exercise_train.label.isin(['정상','점검'])].copy()
review_fill=SimpleImputer(strategy='mean').fit(known[['signal']])
assert review_fill.statistics_[0]==2
rx=review_features(known,review_fill);vy=exercise_validation.label.to_numpy()
vx=review_features(exercise_validation,review_fill);nx=review_features(exercise_input,review_fill)
assert np.array_equal(rx,[[0,0],[2,1],[2,2],[4,3]])
assert sensor_count(panel_examples['B'])==1
assert count_yellow_leaf(panel_examples['B'])==0  # Blind reuse of leaf codes would be wrong; outside that helper's domain.
models={'centroid':NearestCentroid().fit(rx,known.label),'tree_depth2':DecisionTreeClassifier(max_depth=2,random_state=0).fit(rx,known.label)}
answers={}
for name,m in models.items():
    vp=m.predict(vx);npred=m.predict(nx)
    byid=dict(zip(exercise_input.unit,npred))
    frame=pd.DataFrame({'sample_id':exercise_order,'prediction':[byid[k] for k in exercise_order]})
    text=frame.to_csv(index=False,lineterminator='\n')
    reread=pd.read_csv(StringIO(text))
    assert reread.columns.tolist()==['sample_id','prediction'] and reread.sample_id.tolist()==exercise_order
    assert len(reread)==3 and set(reread.prediction).issubset({'정상','점검'})
    answers[name]={'validation':vp.tolist(),'accuracy':float(np.mean(vp==vy)),'submission':reread.values.tolist()}
assert answers['centroid']['validation']==['정상','점검','정상']
assert answers['centroid']['submission']==[['N7','점검'],['N3','점검'],['N1','정상']]
assert answers['tree_depth2']['validation']==['정상','점검','점검']
assert answers['centroid']['validation']!=answers['tree_depth2']['validation']
# Reviewer requirements check; not candidate/student-provided guard code.
def guard(table):
    if not {'unit','signal','panel'}.issubset(table.columns):raise ValueError('missing column')
    if table.unit.isna().any() or table.unit.duplicated().any():raise ValueError('invalid ID')
for bad in [exercise_input.drop(columns='signal'),pd.concat([exercise_input,exercise_input.iloc[:1]])]:
    try:guard(bad)
    except ValueError:pass
    else:raise AssertionError('review guard not triggered')
assert not ast.parse(_review_candidate_cell_sources[36]).body
print(json.dumps({'scope':'reviewer_solution_of_candidate_student_exercise_not_candidate_answer_or_student_work','answers':answers,'known_training_ids':known.unit.tolist(),'unknown_excluded':True,'mean':float(review_fill.statistics_[0]),'blank_student_answer':True,'teacher_examples_verified':True},ensure_ascii=False))
