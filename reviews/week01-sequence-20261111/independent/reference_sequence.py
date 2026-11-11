"""Independent reviewer mathematics. Does not read/import any candidate notebook or author validator."""
import argparse,copy,json,math
from pathlib import Path
BASE=Path(__file__).resolve().parent

def validate(table,ids,pad=0):
    if not table or not table[0]:raise ValueError('nonempty table required')
    d=len(table[0])
    if any(len(row)!=d for row in table):raise ValueError('rectangular table required')
    if any(not math.isfinite(float(x)) for row in table for x in row):raise ValueError('finite table required')
    if type(pad) is not int or not 0<=pad<len(table):raise ValueError('invalid PAD ID')
    if not ids or not ids[0] or any(len(row)!=len(ids[0]) for row in ids):raise ValueError('nonempty rectangular ID batch required by reviewer reference')
    if any(type(x) is not int or not 0<=x<len(table) for row in ids for x in row):raise ValueError('token IDs must be integer 0<=ID<V')

def lookup_and_mean(table,ids,pad=0):
    validate(table,ids,pad)
    d=len(table[0]);lookups=[];masks=[];counts=[];sums=[];means=[];valid=[]
    for sentence in ids:
        embeddings=[[float(x) for x in table[i]] for i in sentence]
        mask=[int(i!=pad) for i in sentence]
        count=sum(mask)
        summed=[math.fsum(v[j] for v,m in zip(embeddings,mask) if m) for j in range(d)]
        # Reviewer-only explicit placeholder. It is not an observed average when count=0.
        pooled=[x/count for x in summed] if count else [0.0]*d
        lookups.append(embeddings);masks.append(mask);counts.append(count);sums.append(summed);means.append(pooled);valid.append(bool(count))
    return {'lookup':lookups,'mask':masks,'counts':counts,'sums':sums,'pooled':means,'valid':valid,'zero_count_policy':'zero placeholder with valid=False; mathematical mean undefined'}

def close(actual,expected):
    if isinstance(expected,list):
        assert len(actual)==len(expected),(actual,expected)
        for a,b in zip(actual,expected):close(a,b)
    elif isinstance(expected,(int,float)):
        assert math.isclose(float(actual),float(expected),rel_tol=0,abs_tol=1e-12),(actual,expected)
    else:assert actual==expected,(actual,expected)

def fractions(x):return [[n/d for n,d in row] for row in x]
def norm(v):return math.sqrt(math.fsum(x*x for x in v))
def scores(q,g,cosine=False):
    if cosine and any(norm(v)==0 for v in q+g):raise ValueError('zero direction in retrieval stage')
    return [[math.fsum(a*b for a,b in zip(x,y))/(norm(x)*norm(y) if cosine else 1) for y in g] for x in q]

def run(case):
    f=json.loads((BASE/'independent-inputs-and-expectations.json').read_text());b=f['base'];table=copy.deepcopy(b['table']);ids=copy.deepcopy(b['token_ids'])
    expected_mean=fractions(b['pooled_exact_fractions']);report={'scope':'reviewer_reference_not_candidate_or_student','case':case}
    if case=='base':
        actual=lookup_and_mean(table,ids);close(actual['lookup'],b['lookup']);close(actual['mask'],b['mask']);close(actual['counts'],b['valid_counts']);close(actual['sums'],b['masked_sums']);close(actual['pooled'],expected_mean)
    elif case=='padding-extension':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,c['token_ids']);close(actual['counts'],b['valid_counts']);close(actual['pooled'],expected_mean)
    elif case=='PAD-vector-change':
        table[0]=[100,-50,7];actual=lookup_and_mean(table,ids);close(actual['counts'],b['valid_counts']);close(actual['sums'],b['masked_sums']);close(actual['pooled'],expected_mean);assert actual['lookup']!=b['lookup']
    elif case=='real-zero-token':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,c['token_ids']);close(actual['counts'],[1]);close(actual['pooled'],[[0,0,0]]);assert actual['valid']==[True]
        try:scores(actual['pooled'],[[1,0,0]],True)
        except ValueError:actual['separate_retrieval_zero_rejection']=True
        else:raise AssertionError('zero mean is not a direction')
    elif case=='all-PAD':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,c['token_ids']);close(actual['counts'],[0]);close(actual['sums'],[[0,0,0]]);assert actual['valid']==[False]
    elif case=='repeated-token':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,c['token_ids']);close(actual['counts'],[3]);close(actual['pooled'],[expected_mean[0]]);assert actual['pooled'][0]!=c['wrong_deduplicate_mean']
    elif case=='position-permutation':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,c['token_ids']);close(actual['pooled'],expected_mean);assert actual['lookup']!=b['lookup']
    elif case in ['invalid-negative-ID','invalid-high-ID']:
        c=next(c for c in f['cases'] if c['id']==case)
        try:lookup_and_mean(table,c['token_ids'])
        except ValueError as e:actual={'rejected':True,'message':str(e)}
        else:raise AssertionError('invalid token ID was accepted')
    elif case=='wrong-denominator-only':
        correct=lookup_and_mean(table,ids);wrong=[[x/b['T'] for x in row] for row in correct['sums']];c=next(c for c in f['cases'] if c['id']==case);close(wrong,c['wrong_divide_masked_sum_by_T']);assert wrong!=correct['pooled'];actual={'correct':correct['pooled'],'wrong':wrong,'control_detects_fault':True}
    elif case=='valid-zero-dropped':
        c=next(c for c in f['cases'] if c['id']==case);counts=[];pooled=[]
        for row in ids:
            vectors=[table[i] for i in row if i!=0 and any(table[i])];counts.append(len(vectors));pooled.append([math.fsum(v[j] for v in vectors)/len(vectors) for j in range(3)])
        close(counts,c['wrong_nonzero-vector-filter_counts']);close(pooled[1],c['wrong_second_sentence_mean']);actual={'wrong_counts':counts,'wrong_means':pooled,'control_detects_fault':pooled!=expected_mean};assert actual['control_detects_fault']
    elif case=='downstream-cosine':
        c=next(c for c in f['cases'] if c['id']==case);actual=lookup_and_mean(table,ids);q=actual['pooled'];g=c['gallery'];raw=scores(q,g);cosine=scores(q,g,True)
        close(raw,fractions(c['raw_dot_matrix_exact_fractions']))
        expected_cos=[[28/math.sqrt(792),30/math.sqrt(1452),-4/math.sqrt(132)],[6/math.sqrt(66),1,-1/math.sqrt(11)]]
        close(cosine,expected_cos)
        raw_ids=[c['gallery_ids'][max(range(len(g)),key=row.__getitem__)] for row in raw];cos_ids=[c['gallery_ids'][max(range(len(g)),key=row.__getitem__)] for row in cosine]
        close(raw_ids,c['raw_best_ids']);close(cos_ids,c['cosine_best_ids']);actual.update(raw_scores=raw,cosine_scores=cosine,raw_ids=raw_ids,cosine_ids=cos_ids)
    else:raise ValueError(case)
    report.update(actual=actual,status='reference_matches_frozen_expectations');return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))
