"""One frozen case on actual teacher code or a labelled reviewer loop solution."""
import ast,hashlib,importlib.util,json
from pathlib import Path
_D = Path.cwd().parents[1]
_spec=importlib.util.spec_from_file_location('frozen_rectangle_probe',_D/'rectangle_probe.py')
_probe=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_probe)
_fixture=json.loads((_D/'frozen-inputs-v2.json').read_text())
_case=next(c for c in _fixture['cases'] if c['id']==_CASE)
assert not ast.parse(_review_candidate_cell_sources[42]).body
assert T.tolist()==[[1,4,7],[2,5,8]]
_source_file=_D/('active-teacher-rectangle.py' if _IMPLEMENTATION=='teacher' else 'reviewer_rectangle_sample.py')
_source=_source_file.read_text()
_source_sha=hashlib.sha256(_source.encode()).hexdigest()
_changes={
 'inclusive-stop':('top <= row < bottom and left <= col < right','top <= row <= bottom and left <= col < right'),
 'swap-spatial-axes':('top <= row < bottom and left <= col < right','left <= row < right and top <= col < bottom'),
 'reject-valid-stop':('top < bottom <= H','top < bottom < H'),
 'allow-clipping':('if not (0 <= top < bottom <= H and 0 <= left < right <= W):','if False:'),
 'mutate-original':('kept = np.zeros_like(grid)','kept = grid'),
 'count-values-not-area':('area = (bottom - top) * (right - left)','area = int(np.count_nonzero(grid[top:bottom, left:right]))'),
}
if _MUTATION in _changes:
    old,new=_changes[_MUTATION];assert _source.count(old)==1;_source=_source.replace(old,new)
exec(_source,globals())
_solution=rectangle_region if _IMPLEMENTATION=='teacher' else reviewer_rectangle_region
print(json.dumps({'provenance':{'implementation':_IMPLEMENTATION,'source_file':_source_file.name,'original_source_sha256':_source_sha,'executed_source_sha256':hashlib.sha256(_source.encode()).hexdigest(),'mutation':_MUTATION,'student_notebook_has_generic_helper':False,'scope':'actual_teacher_example_function' if _IMPLEMENTATION=='teacher' else 'reviewer_sample_solution_from_student_instructions','student_answer_cell42_blank':True}},ensure_ascii=False))

def _adapter(image, box, budget_policy):
    # The lesson's declared implementation is 2D. Use a spatial plane view only;
    # do not assert that lesson code implements RGB masking or derives budgets.
    H,W,C=image.shape
    if budget_policy['type']=='official_fraction':
        max_cells=H*W*budget_policy['numerator']//budget_policy['denominator']
        if _MUTATION=='ceil-budget':
            max_cells=(H*W*budget_policy['numerator']+budget_policy['denominator']-1)//budget_policy['denominator']
    else:max_cells=budget_policy['maximum']
    if _MUTATION=='channel-budget':max_cells=max_cells*C
    grid=image[:,:,0]
    before=grid.copy()
    crop,mask,kept=_solution(grid,box,max_cells)
    print(json.dumps({'native_2d_return':{'grid_shape':list(grid.shape),'crop_shape':list(np.asarray(crop).shape),'mask_shape':list(np.asarray(mask).shape),'kept_shape':list(np.asarray(kept).shape),'mask_coordinates':np.argwhere(mask).tolist(),'mask_area':int(np.count_nonzero(mask)),'spatial_maximum_passed_by_reviewer_adapter':int(max_cells),'channel_count':int(C),'original_unchanged':bool(np.array_equal(grid,before))}},ensure_ascii=False))
    # Validate native 2D crop/output independently for valid fixtures. For invalid
    # fixtures do not turn a silently accepted wrong result into an apparent reject.
    if _case['expected_valid']:
        (t,l),(b,r)=box
        expected_crop=np.array([[before[row,col] for col in range(l,r)] for row in range(t,b)],dtype=before.dtype)
        assert np.array_equal(crop,expected_crop),'native 2D crop values differ'
        assert np.asarray(kept).shape==before.shape,'native 2D kept shape differs'
        assert np.array_equal(kept,np.where(np.asarray(mask,dtype=bool),before,0)),'native kept/mask values differ'
    return {'mask':mask}

_report=_probe.check_case(_adapter,_CASE,
    execution_scope='actual_candidate_callable' if _IMPLEMENTATION=='teacher' else 'reviewer_sample_solution_from_student_instructions',
    require_masked_image=False)
print(json.dumps({'scope_limit':'actual 2D function and 2D crop/kept checked; adapter computes budget and selects one plane; full RGB implementation is not required/proven','probe_status':_report['status']},ensure_ascii=False))
