import json
# Actual candidate source prefixes: no implementation rewrite; remove only fixed toy-data setup/prints/asserts.
transform_train=_review_candidate_cell_sources[22].split('fill = ',1)[1].split('print(',1)[0]
transform_train='fill = '+transform_train
transform_val=_review_candidate_cell_sources[26].split('print(',1)[0]
fit_source=_review_candidate_cell_sources[24].split('print(',1)[0]
def image_n(n):
    a=np.zeros((2,2,2),dtype=int);a[:,:,1]=1
    for k in range(n):a[k//2,k%2,0]=1
    return a
training=pd.DataFrame({'pot_id':['U9','U3','U5','U1'],'water_ml':[0,20,np.nan,40],'height_cm':[8,9,14,13]})
validation=pd.DataFrame({'pot_id':['Z8','Z2'],'water_ml':[np.nan,0],'height_cm':[13,8]})
# Dictionary insertion order deliberately differs from table row order.
leaf_images={'U1':image_n(2),'U5':image_n(4),'U3':image_n(0),'U9':image_n(1),'Z2':image_n(0),'Z8':image_n(3)}
y_train=(training.height_cm>=12).astype(int)
exec(transform_train);exec(fit_source);exec(transform_val)
assert np.allclose(fill.statistics_,[20])
assert np.array_equal(x_train,[[0,1],[2,0],[2,4],[4,2]])
assert np.allclose(model.centroids_,[[1,.5],[3,3]])
assert np.array_equal(x_validation,[[2,3],[0,0]])
original_center=model.centroids_.copy();original_by_id=dict(zip(training.pot_id,model.predict(x_train)))
# Validate holdout transform leaves fitted state unchanged even under a strong value perturbation.
validation.loc[0,'water_ml']=999
exec(transform_val)
assert np.allclose(fill.statistics_,[20]) and np.array_equal(model.centroids_,original_center)
# Refit actual candidate transform and model on a joint row permutation.
training=training.iloc[[2,0,3,1]].copy();y_train=(training.height_cm>=12).astype(int)
exec(transform_train);exec(fit_source)
assert np.allclose(model.centroids_,original_center)
assert dict(zip(training.pot_id,model.predict(x_train)))==original_by_id
# A training change affects learned state; no assertion every query must change.
training.loc[training.pot_id=='U1','water_ml']=60
exec(transform_train);exec(fit_source)
assert np.allclose(fill.statistics_,[80/3])
assert not np.allclose(model.centroids_,original_center)
print(json.dumps({'scope':'actual_candidate_train/validation_conversion_and_fit_source','source_cells':[22,24,26],'adapter':'exact computation prefixes with fixed toy-data setup/prints/asserts excluded','new_id_and_dictionary_order_control':True,'train_only_fit':True,'joint_permutation':True,'training_change':True},ensure_ascii=False))
