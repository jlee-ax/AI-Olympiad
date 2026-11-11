"""Reviewer-owned reference mathematics; never imports/reads the candidate lesson."""
import argparse,copy,json,math
from pathlib import Path
BASE=Path(__file__).resolve().parent

def row_norm(v):return math.sqrt(math.fsum(float(x)*float(x) for x in v))
def normalize_rows(rows,zero='raise'):
    result=[]
    for v in rows:
        norm=row_norm(v)
        if norm==0:
            if zero=='raise':raise ValueError('zero vector has no unit direction')
            if zero=='invalid':result.append(None);continue
            raise ValueError(zero)
        result.append([float(x)/norm for x in v])
    return result

def dot_matrix(q,g):
    if not q or not g:raise ValueError('nonempty rows required')
    d=len(q[0]);assert all(len(v)==d for v in q+g)
    return [[math.fsum(float(a)*float(b) for a,b in zip(x,y)) for y in g] for x in q]

def cosine_matrix(q,g,zero='raise'):
    nq=normalize_rows(q,zero);ng=normalize_rows(g,zero)
    return [[None if x is None or y is None else math.fsum(a*b for a,b in zip(x,y)) for y in ng] for x in nq]

def choose_ids(scores,ids,policy='smallest_id'):
    result=[];ties=[]
    for row in scores:
        valid=[i for i,v in enumerate(row) if v is not None]
        if not valid:result.append(None);ties.append([]);continue
        top=max(row[i] for i in valid)
        chosen=[i for i in valid if row[i]==top]
        ties.append([ids[i] for i in chosen])
        result.append(min(ids[i] for i in chosen) if policy=='smallest_id' else ids[chosen[0]])
    return result,ties

def compare(a,b):
    if isinstance(b,list):
        assert len(a)==len(b),(a,b)
        for x,y in zip(a,b):compare(x,y)
    elif isinstance(b,(float,int)):
        assert math.isclose(a,b,rel_tol=0,abs_tol=1e-12),(a,b)
    else:assert a==b,(a,b)

def run(case):
    f=json.loads((BASE/'independent-inputs-and-expectations.json').read_text());b=f['base']
    q=copy.deepcopy(b['query_vectors']);g=copy.deepcopy(b['gallery_vectors']);ids=b['gallery_ids'][:]
    actual={'scope':'reviewer_reference_only_not_candidate_or_student','case':case}
    if case=='base':
        actual.update(query_norms=[row_norm(v) for v in q],gallery_norms=[row_norm(v) for v in g],normalized_queries=normalize_rows(q),normalized_gallery=normalize_rows(g),raw_dot_matrix=dot_matrix(q,g),cosine_matrix=cosine_matrix(q,g))
        for key in ['query_norms','gallery_norms','normalized_queries','normalized_gallery','raw_dot_matrix','cosine_matrix']:compare(actual[key],b[key])
        actual['cosine_best_ids']=choose_ids(actual['cosine_matrix'],ids)[0]
        actual['raw_dot_best_ids']=choose_ids(actual['raw_dot_matrix'],ids)[0]
        compare(actual['cosine_best_ids'],b['cosine_best_ids']);compare(actual['raw_dot_best_ids'],b['raw_dot_best_ids'])
    elif case in ['positive-query-scale','positive-gallery-scale','negative-query-scale','negative-gallery-scale']:
        spec=next(x for x in f['cases'] if x['id']==case)
        if 'query' in case:q[0]=[x*(7 if case.startswith('positive') else -1) for x in q[0]]
        else:g[1]=[x*(10 if case.startswith('positive') else -1) for x in g[1]]
        matrix=cosine_matrix(q,g);compare(matrix,spec['expected_cosine_matrix'])
        actual.update(cosine_matrix=matrix,best_ids=choose_ids(matrix,ids)[0])
        if 'expected_cosine_best_ids' in spec:compare(actual['best_ids'],spec['expected_cosine_best_ids'])
    elif case in ['zero-query','zero-gallery']:
        if case=='zero-query':q[0]=[0,0]
        else:g.append([0,0]);ids.append(100)
        try:cosine_matrix(q,g)
        except ValueError:actual['explicit_zero_rejection']=True
        else:raise AssertionError('zero must be explicit in this reviewer reference')
        invalid=cosine_matrix(q,g,zero='invalid');actual['invalid_policy_matrix']=invalid;actual['invalid_policy_ids']=choose_ids(invalid,ids)[0]
        if case=='zero-query':assert actual['invalid_policy_ids'][0] is None
        else:compare(actual['invalid_policy_ids'],b['cosine_best_ids'])
    elif case=='exact-tie':
        spec=next(x for x in f['cases'] if x['id']==case);matrix=cosine_matrix([spec['query_vector']],spec['gallery_vectors'])
        compare(matrix[0],spec['expected_cosines'])
        selected,ties=choose_ids(matrix,spec['gallery_ids']);assert selected==[7] and set(ties[0])=={42,7}
        actual.update(matrix=matrix,minimum_id_policy=selected,first_position_policy=choose_ids(matrix,spec['gallery_ids'],'first')[0],tied_ids=ties)
    elif case=='row-id-joint-permutation':
        spec=next(x for x in f['cases'] if x['id']==case);order=spec['gallery_row_order'];g=[g[i] for i in order];correct=[ids[i] for i in order]
        matrix=cosine_matrix(q,g);compare(matrix,spec['expected_cosine_matrix']);compare(choose_ids(matrix,correct)[0],spec['expected_cosine_best_ids']);compare(choose_ids(matrix,ids)[0],spec['id_only_not_permuted_wrong_output'])
        actual.update(matrix=matrix,correct_ids=choose_ids(matrix,correct)[0],id_only_wrong=choose_ids(matrix,ids)[0])
    elif case=='square-broadcast-trap':
        spec=next(x for x in f['cases'] if x['id']==case);norms=spec['row_norms'];wrong=[[v/norms[j] for j,v in enumerate(row)] for row in spec['gallery_vectors']]
        compare(wrong,spec['wrong_divide_by_1d_row_norms']);compare([row_norm(v) for v in wrong],spec['wrong_row_norms']);compare(normalize_rows(spec['gallery_vectors']),spec['correct_row_normalized'])
        actual.update(wrong_shape_valid_values=wrong,wrong_row_norms=[row_norm(v) for v in wrong])
    elif case=='independent-3d':
        spec=json.loads((BASE/'independent-3d-addendum.json').read_text());q=spec['queries'];g=spec['gallery'];ids=spec['gallery_ids'];matrix=cosine_matrix(q,g)
        fraction_values=lambda a:[[v[0]/v[1] for v in row] for row in a]
        compare(matrix,fraction_values(spec['cosine_exact_fractions']));compare(choose_ids(matrix,ids)[0],spec['expected_best_ids'])
        compare(normalize_rows(q),fraction_values(spec['normalized_query_exact_fractions']));compare(normalize_rows(g),fraction_values(spec['normalized_gallery_exact_fractions']))
        actual.update(matrix=matrix,chosen_ids=choose_ids(matrix,ids)[0],all_gallery_row_norms=[row_norm(v) for v in normalize_rows(g)])
        negq=[[-x for x in q[0]],q[1]];compare(choose_ids(cosine_matrix(negq,g),ids)[0],spec['negative_query_scale']['expected_best_ids'])
        negg=copy.deepcopy(g);negg[1]=[-x for x in negg[1]];compare(choose_ids(cosine_matrix(q,negg),ids)[0],spec['negative_gallery_scale']['expected_best_ids'])
    else:raise ValueError(case)
    actual['status']='reference_matches_frozen_expectations'
    return actual

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);args=p.parse_args();print(json.dumps(run(args.case),ensure_ascii=False,indent=2))
