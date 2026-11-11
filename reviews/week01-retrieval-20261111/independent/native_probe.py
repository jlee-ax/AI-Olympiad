import json,math
from pathlib import Path
_review_root=Path.cwd().parents[1]
_fixture=json.loads((_review_root/'independent-inputs-and-expectations.json').read_text())
_base=_fixture['base']
_report={'case':_review_case,'scope':'actual_candidate_normalize_rows/cosine_scores/selection_source','expected':{},'actual':{}}
def _review_publish():print(json.dumps(_report,ensure_ascii=False,indent=2))
def _review_select(queries,candidates,ids):
    # Reuse actual executed candidate selection statements, including any controlled mutation.
    global Q,G,candidate_ids,Q_unit,G_unit,scores,positions,matched_ids
    Q=np.asarray(queries,dtype=float);G=np.asarray(candidates,dtype=float);candidate_ids=np.asarray(ids)
    text='Q_unit = '+_review_candidate_cell_sources[16].split('Q_unit = ',1)[1].split('print(',1)[0]
    exec(text,globals())
    return {'scores':scores.tolist(),'positions':positions.tolist(),'ids':matched_ids.tolist(),'query_unit':Q_unit.tolist(),'gallery_unit':G_unit.tolist(),'query_unit_norms':np.linalg.norm(Q_unit,axis=1).tolist(),'gallery_unit_norms':np.linalg.norm(G_unit,axis=1).tolist()}
def _review_equal(actual,expected):
    if isinstance(expected,list):
        assert len(actual)==len(expected),(actual,expected)
        for a,b in zip(actual,expected):_review_equal(a,b)
    elif isinstance(expected,(int,float)):assert math.isclose(float(actual),expected,rel_tol=0,abs_tol=1e-12),(actual,expected)
    else:assert actual==expected,(actual,expected)
q=_base['query_vectors'];g=_base['gallery_vectors'];ids=_base['gallery_ids']
if _review_case=='base2d':
    got=_review_select(q,g,ids);_report['actual']=got
    _report['expected']={k:_base[k] for k in ['cosine_matrix','normalized_queries','normalized_gallery','cosine_best_ids']};_review_publish()
    _review_equal(got['scores'],_base['cosine_matrix']);_review_equal(got['query_unit'],_base['normalized_queries']);_review_equal(got['gallery_unit'],_base['normalized_gallery']);_review_equal(got['ids'],_base['cosine_best_ids'])
elif _review_case=='independent3d':
    f=json.loads((_review_root/'independent-3d-addendum.json').read_text());q=f['queries'];g=f['gallery'];ids=f['gallery_ids']
    fractional=lambda x:[[n/d for n,d in row] for row in x]
    got=_review_select(q,g,ids);_report['actual']=got;_report['expected']={'scores':fractional(f['cosine_exact_fractions']),'ids':f['expected_best_ids'],'query_unit':fractional(f['normalized_query_exact_fractions']),'gallery_unit':fractional(f['normalized_gallery_exact_fractions'])};_review_publish()
    for k,v in _report['expected'].items():_review_equal(got[k],v)
    _review_equal(got['gallery_unit_norms'],[1]*4)
    gotq=_review_select([[-x for x in q[0]],q[1]],g,ids);_review_equal(gotq['ids'],f['negative_query_scale']['expected_best_ids'])
    changed=[r[:] for r in g];changed[1]=[-x for x in changed[1]]
    gotg=_review_select(q,changed,ids);_review_equal(gotg['ids'],f['negative_gallery_scale']['expected_best_ids'])
    print(json.dumps({'additional_3d_negative_query_ids':gotq['ids'],'additional_3d_negative_gallery_ids':gotg['ids']}))
elif _review_case in ['positive-query-scale','positive-gallery-scale','negative-query-scale','negative-gallery-scale']:
    f=next(x for x in _fixture['cases'] if x['id']==_review_case)
    q=[r[:] for r in q];g=[r[:] for r in g]
    if 'query' in _review_case:q[0]=[x*(7 if _review_case.startswith('positive') else -1) for x in q[0]]
    else:g[1]=[x*(10 if _review_case.startswith('positive') else -1) for x in g[1]]
    got=_review_select(q,g,ids);_report.update(expected={'scores':f['expected_cosine_matrix']},actual=got);_review_publish();_review_equal(got['scores'],f['expected_cosine_matrix'])
    if 'expected_cosine_best_ids' in f:_review_equal(got['ids'],f['expected_cosine_best_ids'])
elif _review_case in ['zero-query','zero-gallery']:
    if _review_case=='zero-query':q=[[0,0]]
    else:g=g+[[0,0]];ids=ids+[100]
    _report['expected']={'policy':'candidate explicitly rejects zero rows with ValueError'}
    try:got=_review_select(q,g,ids)
    except ValueError as e:_report['actual']={'exception':'ValueError','message':str(e)};_review_publish()
    else:_report['actual']=got;_review_publish();raise AssertionError('candidate stated zero rejection did not occur')
elif _review_case=='tie-first-position':
    f=next(x for x in _fixture['cases'] if x['id']=='exact-tie');q=[f['query_vector']];g=f['gallery_vectors'];ids=f['gallery_ids']
    got=_review_select(q,g,ids);_report.update(expected={'scores':[[1,1,0]],'positions':[0],'ids':[42],'note':'native lesson declares first current position; reviewer separate min-ID contract would choose7'},actual=got);_review_publish()
    _review_equal(got['scores'],[[1,1,0]]);_review_equal(got['positions'],[0]);_review_equal(got['ids'],[42])
    got2=_review_select(q,[g[1],g[0],g[2]],[ids[1],ids[0],ids[2]]);_review_equal(got2['ids'],[7]);print(json.dumps({'native_first_tie_after_joint_permutation':got2['ids']}))
elif _review_case=='joint-row-id':
    f=next(x for x in _fixture['cases'] if x['id']=='row-id-joint-permutation');order=f['gallery_row_order'];gp=[g[i] for i in order];ip=[ids[i] for i in order]
    got=_review_select(q,gp,ip);_report.update(expected={'scores':f['expected_cosine_matrix'],'positions':f['expected_cosine_best_positions'],'ids':f['expected_cosine_best_ids']},actual=got);_review_publish()
    for k,v in _report['expected'].items():_review_equal(got[k],v)
    wrong=_review_select(q,gp,ids);_review_equal(wrong['ids'],f['id_only_not_permuted_wrong_output']);print(json.dumps({'id_only_wrong_output':wrong['ids']}))
elif _review_case=='axis-square':
    f=next(x for x in _fixture['cases'] if x['id']=='square-broadcast-trap');got=normalize_rows(f['gallery_vectors'])
    _report.update(expected={'gallery_unit':f['correct_row_normalized'],'norms':[1,1]},actual={'gallery_unit':got.tolist(),'norms':np.linalg.norm(got,axis=1).tolist()});_review_publish();_review_equal(got.tolist(),f['correct_row_normalized']);_review_equal(np.linalg.norm(got,axis=1).tolist(),[1,1])
elif _review_case=='invalid-inputs':
    invalid=[[],[[]],[1,2],[[np.nan,1]],[[np.inf,1]],[[1e308,1e308]],[[1e-300,0]]]
    got=[]
    for vectors in invalid:
        try:normalize_rows(vectors)
        except ValueError as e:got.append({'rejected':True,'message':str(e)})
        else:got.append({'rejected':False})
    try:cosine_scores([[1,0]],[[1,0,1]])
    except ValueError as e:got.append({'dimension_mismatch_rejected':True,'message':str(e)})
    else:got.append({'dimension_mismatch_rejected':False})
    _report.update(expected={'all_rejected':True,'domain_note':'nonempty finite real 2D with computable positive length; extreme examples test stated rejection, not universal normalization'},actual=got);_review_publish();assert all(x.get('rejected',x.get('dimension_mismatch_rejected')) for x in got)
elif _review_case=='raw-dot-contract':
    # Reuse only actual raw-score assignment; this contract intentionally uses unnormalized dot.
    Q=np.asarray(q,dtype=float);G=np.asarray(g,dtype=float);candidate_ids=np.asarray(ids)
    rawtext='raw_scores = '+_review_candidate_cell_sources[14].split('raw_scores = ',1)[1].split('print(',1)[0]
    exec(rawtext,globals());got={'matrix':raw_scores.tolist(),'ids':candidate_ids[np.argmax(raw_scores,axis=1)].tolist()}
    _report.update(expected={'matrix':_base['raw_dot_matrix'],'ids':_base['raw_dot_best_ids']},actual=got);_review_publish();_review_equal(got['matrix'],_base['raw_dot_matrix']);_review_equal(got['ids'],_base['raw_dot_best_ids'])
else:raise ValueError(_review_case)
