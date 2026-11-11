import ast,json,math
# Provided B inputs plus actual helper; reviewer solves the blank problem to check the teacher key.
raw=query_new @ gallery_new.T
c=cosine_scores(query_new,gallery_new);pos=np.argmax(c,axis=1);ids=g_ids_new[pos]
order=np.array([2,0,3,1]);c2=cosine_scores(query_new,gallery_new[order]);p2=np.argmax(c2,axis=1)
expected=[[4/5,2/math.sqrt(5),3/math.sqrt(10),1/math.sqrt(5)],[1,1/math.sqrt(5),3/math.sqrt(10),2/math.sqrt(5)]]
actual={'raw':raw.tolist(),'cosine':c.tolist(),'raw_positions':np.argmax(raw,axis=1).tolist(),'raw_ids':g_ids_new[np.argmax(raw,axis=1)].tolist(),'positions':pos.tolist(),'ids':ids.tolist(),'permuted_positions':p2.tolist(),'permuted_ids':g_ids_new[order][p2].tolist(),'wrong_ids':g_ids_new[p2].tolist(),'answer_blank':not ast.parse(_review_candidate_cell_sources[31]).body}
print(json.dumps({'scope':'actual_preparation_route_and_helper_plus_reviewer_solution_of_blank_B','expected':{'raw':[[4,6,3,2],[5,3,3,4]],'cosine':expected,'raw_ids':[8,90],'ids':[53,90],'permuted_positions':[0,1],'permuted_ids':[53,90],'wrong_ids':[90,8]},'actual':actual},ensure_ascii=False,indent=2))
assert np.array_equal(raw,[[4,6,3,2],[5,3,3,4]]) and np.allclose(c,expected,atol=1e-12,rtol=0)
assert actual['raw_ids']==[8,90] and actual['positions']==[2,0] and actual['ids']==[53,90]
assert actual['permuted_positions']==[0,1] and actual['permuted_ids']==[53,90] and actual['wrong_ids']==[90,8]
assert actual['answer_blank']
