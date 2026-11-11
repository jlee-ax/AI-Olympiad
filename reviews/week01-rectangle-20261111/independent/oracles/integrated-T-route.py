import ast,json
assert 'plants' not in globals(), 'full notebook namespace leaked into fresh return route'
assert T.tolist()==[[1,4,7],[2,5,8]] and T.shape==(2,3)
assert not ast.parse(_review_candidate_cell_sources[42]).body
# Actual teacher example function, not the student's empty answer.
from pathlib import Path
exec((Path.cwd().parents[1]/'active-teacher-rectangle.py').read_text())
original=T.copy()
a=rectangle_region(T,((0,1),(2,3)),4);b=rectangle_region(T,((0,0),(2,2)),4)
assert a[0].tolist()==[[4,7],[5,8]] and a[1].astype(int).tolist()==[[0,1,1],[0,1,1]]
assert a[2].tolist()==[[0,4,7],[0,5,8]]
assert b[0].tolist()==[[1,4],[2,5]] and b[2].tolist()==[[1,4,0],[2,5,0]]
assert np.array_equal(original,T)
for box in [((0,0),(2,3)),((1,1),(3,3)),((1,1),(1,2))]:
 try:rectangle_region(T,box,4)
 except ValueError:pass
 else:raise AssertionError('teacher example accepted invalid educational T box')
print(json.dumps({'scope':'actual final input41 creates T in new integrated kernel; teacher function solves public T examples; student42 blank','prepared_without_original_kernel':True,'actual_T':T.tolist(),'first_crop':a[0].tolist(),'second_crop':b[0].tolist(),'same_area_different_positions':not np.array_equal(a[1],b[1]),'original_unchanged':True,'student_answer_blank':True},ensure_ascii=False))
