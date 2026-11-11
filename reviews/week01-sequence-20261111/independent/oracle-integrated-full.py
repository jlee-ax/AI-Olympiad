import ast,json
assert not ast.parse(_review_candidate_cell_sources[36]).body
assert np.array_equal(x_train, [[0,0],[2,1],[2,2],[4,3]])
assert np.allclose(model.centroids_, [[1,.5],[3,2.5]])
assert np.allclose(fill.statistics_, [20])
assert np.allclose(changed_fill.statistics_, [80/3])
assert np.allclose(changed_model.centroids_, [[1,.5],[13/3,2.5]])
assert (original_prediction,changed_prediction)==(1,0)
expected_pairs=dict(zip(result['pot_id'],result['prediction']))
assert dict(zip(restored['pot_id'],restored['prediction']))==expected_pairs
assert checked.columns.tolist()==['pot_id','prediction']
assert checked['pot_id'].tolist()==['P05','P06']
assert checked['prediction'].tolist()==[0,1]
assert validation_accuracy==.5
print(json.dumps({'scope':'actual_candidate_demo','x_train':x_train.tolist(),'centers':model.centroids_.tolist(),'validation':predictions.tolist(),'accuracy':float(validation_accuracy),'blank_student_response':True,'trained_change':[original_prediction,changed_prediction]},ensure_ascii=False))
