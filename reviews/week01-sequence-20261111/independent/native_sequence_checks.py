"""Reviewer oracle calling the actual candidate helper; never fills learner responses."""
import ast,json,math
from pathlib import Path
_D=Path.cwd().parents[1]
_f=json.loads((_D/'independent-inputs-and-expectations.json').read_text())
_t=np.array(_f['base']['table'],float);_i=np.array(_f['base']['token_ids'])
_expected_mean=np.array([[4/3,4/3,10/3],[.5,-.5,1.5]])
def _reference(table,ids):
    vec=[];mask=[];sums=[];counts=[];means=[]
    for row in ids:
        vv=[list(table[int(k)]) for k in row]; mm=[int(k)!=0 for k in row]
        n=sum(mm);ss=[sum(v[j] for v,ok in zip(vv,mm) if ok) for j in range(len(table[0]))]
        if not n:raise ValueError('reference undefined mean')
        vec.append(vv);mask.append(mm);sums.append(ss);counts.append([n]);means.append([x/n for x in ss])
    return vec,mask,sums,counts,means

def _check(table,ids):
    original_t=np.array(table,copy=True);original_i=np.array(ids,copy=True)
    expected=_reference(table,ids);actual=lookup_and_masked_mean(table,ids)
    print(json.dumps({'scope':'actual_candidate_helper_on_frozen_new_input','case':_CASE,'expected':[np.asarray(a).tolist() for a in expected],'actual':[np.asarray(a).tolist() for a in actual]},ensure_ascii=False))
    assert len(actual)==5
    for k,(a,b) in enumerate(zip(actual,expected)):
        assert np.asarray(a).shape==np.asarray(b).shape,('shape',k,np.asarray(a).shape,np.asarray(b).shape)
        assert np.allclose(a,b,rtol=0,atol=1e-12),('values',k)
    assert np.array_equal(table,original_t) and np.array_equal(ids,original_i),'inputs mutated'
    return actual

def _reject(table,ids,reason):
    try:lookup_and_masked_mean(table,ids)
    except ValueError as err:
        print(json.dumps({'case':_CASE,'expected':'ValueError','actual':'ValueError','message':str(err),'reason':reason},ensure_ascii=False));return
    except Exception as err:raise AssertionError('wrong exception for '+reason+': '+repr(err))
    raise AssertionError('accepted invalid '+reason)

if _CASE=='base':
    a=_check(_t,_i);assert a[0].shape==(2,4,3) and a[3].shape==(2,1) and a[4].shape==(2,3)
elif _CASE=='padding-extension':_check(_t,np.pad(_i,((0,0),(0,2))))
elif _CASE=='PAD-vector-change':
    _t[0]=[100,-50,7];_check(_t,_i)
elif _CASE=='real-zero-token':
    a=_check(_t,np.array([[1,0,0,0]]));assert a[3].item()==1 and not a[4].any()
    try:cosine_scores(a[4],[[1,1,1]])
    except ValueError as err:print(json.dumps({'mean_valid':True,'cosine_rejected_separately':True,'message':str(err)},ensure_ascii=False))
    else:raise AssertionError('cosine of valid zero mean unexpectedly accepted')
elif _CASE=='all-PAD':_reject(_t,[[0,0,0,0]],'all-PAD')
elif _CASE=='repeated-token':_check(_t,np.array([[2,3,2,0]]))
elif _CASE=='position-permutation':
    a=_check(_t,np.array([[0,2,3,2],[0,5,0,1]]));assert np.allclose(a[4],_expected_mean) and not np.array_equal(a[0],_f['base']['lookup'])
elif _CASE=='invalid-negative-ID':_reject(_t,[[-1,2,0,0]],'negative ID before indexing')
elif _CASE=='invalid-high-ID':_reject(_t,[[7,2,0,0]],'ID==V before indexing')
elif _CASE=='invalid-bool-ID':_reject(_t,[[True,2,0,0]],'bool ID')
elif _CASE=='invalid-float-ID':_reject(_t,[[2.0,3,0,0]],'float ID')
elif _CASE=='wrong-axis-input':_reject(_t,[2,3,2,0],'one-dimensional IDs')
elif _CASE=='downstream-cosine':
    a=_check(_t,_i);g=np.array([[1,1,2],[1,-1,3],[-1,0,0]]);gid=np.array([80,17,65]);raw=a[4]@g.T;co=cosine_scores(a[4],g)
    expected_cos=np.array([[28/math.sqrt(792),30/math.sqrt(1452),-4/math.sqrt(132)],[6/math.sqrt(66),1,-1/math.sqrt(11)]])
    print(json.dumps({'raw':raw.tolist(),'cosine':co.tolist(),'raw_ids':gid[raw.argmax(1)].tolist(),'cosine_ids':gid[co.argmax(1)].tolist()}))
    assert np.allclose(raw,[[28/3,10,-4/3],[3,11/2,-.5]],rtol=0,atol=1e-12)
    assert np.allclose(co,expected_cos,rtol=0,atol=1e-12)
    assert gid[raw.argmax(1)].tolist()==[17,17] and gid[co.argmax(1)].tolist()==[80,17]
elif _CASE=='B-route':
    a=_check(token_table_new,query_tokens_new);q=a[4];raw=q@gallery_new.T;co=cosine_scores(q,gallery_new);pos=co.argmax(1);order=np.array([2,0,3,1]);pos2=cosine_scores(q,gallery_new[order]).argmax(1)
    print(json.dumps({'scope':'reviewer_solution_using_actual_helpers_not_student_response','counts':a[3].ravel().tolist(),'q':q.tolist(),'raw':raw.tolist(),'cosine':co.tolist(),'raw_ids':g_ids_new[raw.argmax(1)].tolist(),'cosine_ids':g_ids_new[pos].tolist(),'reordered_positions':pos2.tolist(),'correct_reordered_ids':g_ids_new[order][pos2].tolist(),'wrong_unmoved_ids':g_ids_new[pos2].tolist()}))
    assert np.allclose(q,[[2,3],[3,2]]) and a[3].ravel().tolist()==[3,2]
    assert np.array_equal(raw,[[7,9,5,4],[8,6,5,6]]) and g_ids_new[raw.argmax(1)].tolist()==[8,90]
    assert pos.tolist()==[2,0] and g_ids_new[pos].tolist()==[53,90] and pos2.tolist()==[0,1]
    assert g_ids_new[order][pos2].tolist()==[53,90] and g_ids_new[pos2].tolist()==[90,8]
    # Different lawful implementations: token-count matrix multiplication versus loops above/native indexed masked sums.
    hist=np.array([[sum(int(k)==v for k in row) if v!=0 else 0 for v in range(len(token_table_new))] for row in query_tokens_new])
    alternative=(hist@token_table_new)/hist.sum(1,keepdims=True)
    assert np.allclose(alternative,q);assert not ast.parse(_review_candidate_cell_sources[33]).body
    print(json.dumps({'alternative':'token frequency weighted sum','same_mean':True,'student_blank':True}))
elif _CASE=='wrong-denominator-cosine-control':
    _t[0]=0
    # Native actual function has the single denominator mutation; reference remains correct.
    actual=lookup_and_masked_mean(_t,_i);correct=np.array(_reference(_t,_i)[4]);wrong=actual[4]
    g=np.array([[1,1,2],[1,-1,3],[-1,0,0]])
    c1=cosine_scores(correct,g);c2=cosine_scores(wrong,g)
    print(json.dumps({'scope':'actual_candidate_function_single_fault_injection','correct_mean':correct.tolist(),'mutant_mean':wrong.tolist(),'coordinate_oracle_detects_wrong_mean':not np.allclose(correct,wrong),'cosine_scores_equal':bool(np.allclose(c1,c2,rtol=0,atol=1e-12)),'cosine_scores_correct':c1.tolist(),'cosine_scores_wrong':c2.tolist(),'cosine_argmax_equal':np.array_equal(c1.argmax(1),c2.argmax(1))}))
    assert not np.allclose(correct,wrong) and np.allclose(wrong,[[1,1,2.5],[.25,-.25,.75]])
    assert np.allclose(c1,c2,rtol=0,atol=1e-12) and np.array_equal(c1.argmax(1),c2.argmax(1))
else:raise AssertionError('unknown case '+_CASE)
