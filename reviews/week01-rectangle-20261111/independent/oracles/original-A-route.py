import ast,json
assert not ast.parse(_review_candidate_cell_sources[61]).body
assert not ast.parse(_review_candidate_cell_sources[66]).body
assert two_by_three.tolist()==[[2,4,6],[8,10,12]]
assert grid.tolist()==[[2,4],[6,8],[10,12]]
assert 'T' not in globals(), 'T unexpectedly preexisting across fresh kernel'
# This part is reviewer work following the open original-A prompts, not learner work.
task_array=np.array([[2,5,8],[11,14,17]])
r=task_array.reshape(3,2,order='C');t=task_array.T
assert r.tolist()==[[2,5],[8,11],[14,17]] and t.tolist()==[[2,11],[5,14],[8,17]]
T=np.array([[1,4,7],[2,5,8]])
assert (T+np.array([10,20,30])).tolist()==[[11,24,37],[12,25,38]]
assert (T+np.array([[100],[200]])).tolist()==[[101,104,107],[202,205,208]]
try:T+np.array([100,200])
except ValueError:bad_broadcast_rejected=True
else:raise AssertionError('bad broadcast accepted')
print(json.dumps({'scope':'provided original preparation/examples plus reviewer reference for blank A','original_notebook_cells':89,'T_creation':'reviewer explicitly created T in this fresh original kernel; not supplied by blank cell66','reshape_and_transpose_same_shape_different_values':True,'row_and_column_broadcast_checked':True,'bad_broadcast_rejected':bad_broadcast_rejected,'blank_student_cells':[61,66],'student_achievement':'not_observed'},ensure_ascii=False))
