import itertools,json
from pathlib import Path
checked_cases=0
for flat in itertools.product([0,1], repeat=8):
    sample=np.array(flat).reshape(2,2,2)
    hand=sum(1 for r in range(2) for c in range(2) if sample[r,c,0]==1 and sample[r,c,1]==1)
    assert count_yellow_leaf(sample)==hand
    changed=sample.copy()
    for r in range(2):
        for c in range(2):
            if changed[r,c,0]==0:changed[r,c,1]=1-changed[r,c,1]
    assert count_yellow_leaf(changed)==hand
    assert count_yellow_leaf(sample.transpose(1,0,2))==hand
    checked_cases+=1
# Explicit independent grids, encoded into the leaf helper's published domain.
grids=[[[1,0],[1,0]],[[0,1],[1,0]],[[0,1],[0,1]],[[1,1],[1,1]]]
actual=[]
for grid in grids:
    image=np.zeros((2,2,2),dtype=int)
    image[:,:,0]=grid
    image[:,0,1]=1
    got=count_yellow_leaf(image)
    hand=sum(grid[r][0] for r in range(2))
    assert got==hand
    actual.append(got)
assert actual==[2,1,0,2]
assert observed_mean([0,None,np.nan,2])==1
assert observed_mean([None,np.nan]) is None and observed_mean([]) is None
assert observed_mean([1000000]*10000)==1000000
print(json.dumps({'scope':'actual_candidate_count_yellow_leaf_and_observed_mean','valid_binary_grids':checked_cases,'background_invariant':True,'spatial_transpose_count_invariant':True,'independent_encoded_grid_results':actual,'adapter_limit':'first-column meaning supplied by reviewer encoding, not a claimed candidate generic schema parser'},ensure_ascii=False))
