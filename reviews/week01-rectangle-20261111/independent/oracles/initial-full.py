import ast,json
assert not ast.parse(_review_candidate_cell_sources[38]).body
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

assert not ast.parse(_review_candidate_cell_sources[42]).body
assert area == int(region_mask.sum()) == 6
assert rectangle_grid.shape == region_mask.shape == kept_grid.shape == (8,12)
assert np.array_equal(crop, [[0,29,30],[40,41,42]])
assert np.argwhere(region_mask).tolist()==[[2,4],[2,5],[2,6],[3,4],[3,5],[3,6]]
assert np.array_equal(rectangle_grid,rectangle_before)
print(json.dumps({"scope":"actual_fixed_example_only_not_generic_helper_or_student_solution","selected_coordinates":np.argwhere(region_mask).tolist(),"crop":crop.tolist(),"source_unchanged":True,"blank_student_cells":[38,42]},ensure_ascii=False))
