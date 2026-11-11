"""Reviewer-only independent contract oracle. Never imports or reads candidate lessons."""
import argparse, copy, csv, io, json, math, tempfile
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def observed_mean(values):
    observed=[Fraction(str(v)) for v in values if v is not None and not (isinstance(v,float) and math.isnan(v))]
    return None if not observed else sum(observed)/len(observed)

def vector(row,mean,categories):
    grid=row['grid']
    assert len(grid)==2 and all(len(r)==2 for r in grid)
    assert all(v in (0,1) for r in grid for v in r)
    reading=mean if row['reading'] is None else Fraction(str(row['reading']))
    return [reading,sum(grid[r][0] for r in range(2)),*[int(row['zone']==c) for c in categories]]

def squared(a,b):return sum((x-y)**2 for x,y in zip(a,b))

def fit(spec):
    rows=[r for r in spec['train'] if r['target'] in ['ok','check']]
    mean=observed_mean([r['reading'] for r in rows])
    assert mean is not None
    cats=sorted({r['zone'] for r in rows})
    X=[vector(r,mean,cats) for r in rows]
    centers={}
    for label in ['ok','check']:
        class_rows=[x for r,x in zip(rows,X) if r['target']==label]
        centers[label]=[sum(Fraction(x[j]) for x in class_rows)/len(class_rows) for j in range(len(X[0]))]
    return rows,mean,cats,X,centers

def predict(spec):
    rows,mean,cats,X,centers=fit(spec)
    val_X=[vector(r,mean,cats) for r in spec['validation']]
    distances={r['sample_id']:{label:squared(x,c) for label,c in centers.items()} for r,x in zip(spec['validation'],val_X)}
    dc={sid:min(d,key=d.get) for sid,d in distances.items()}
    train_dist={r['sample_id']:[squared(x,t) for t in X] for r,x in zip(spec['validation'],val_X)}
    nn={}
    for sid,d in train_dist.items():
        nearest=sorted(range(len(d)),key=lambda i:(d[i],i))[:3]
        votes=[rows[i]['target'] for i in nearest]
        nn[sid]=max(['ok','check'],key=votes.count)
    return rows,mean,cats,X,centers,val_X,distances,dc,train_dist,nn

def plain(x):
    if isinstance(x,Fraction):return int(x) if x.denominator==1 else float(x)
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x

def eq(actual,expected):
    if isinstance(expected,dict):
        assert actual.keys()==expected.keys(),(actual,expected)
        for k in expected:eq(actual[k],expected[k])
    elif isinstance(expected,list):
        assert len(actual)==len(expected),(actual,expected)
        for a,b in zip(actual,expected):eq(a,b)
    elif isinstance(expected,(int,float)):
        assert math.isclose(float(actual),expected,rel_tol=0,abs_tol=1e-12),(actual,expected)
    else:assert actual==expected,(actual,expected)

def validate_csv(text,spec):
    parsed=list(csv.reader(io.StringIO(text)))
    assert parsed[0]==spec['submission']['header']
    rows=parsed[1:]
    assert len(rows)==len(spec['submission']['required_id_order'])
    assert all(len(r)==2 for r in rows)
    assert [r[0] for r in rows]==spec['submission']['required_id_order']
    assert all(r[1] in spec['submission']['labels'] for r in rows)
    return rows

def main(case):
    spec=json.loads((ROOT/'independent-transfer-spec.json').read_text())
    expected=json.loads((ROOT/'reference-expectations.json').read_text())
    result={'case':case,'scope':'reviewer_reference_only_not_candidate_or_student','candidate_read':False}
    values=predict(spec)
    rows,mean,cats,X,centers,val_X,distances,dc,train_dist,nn=values
    if case=='arithmetic':
        actual={'training_known_ids':[r['sample_id'] for r in rows],'imputation_mean':mean,'training_X':X,'centroids':centers,'validation_X':val_X,'squared_distances_to_centroids':distances,'centroid_predictions_by_id':dc,'squared_distances_to_train':train_dist,'three_nn_predictions_by_id':nn}
        for k,v in actual.items():eq(v,expected[k])
        truth={r['sample_id']:r['target'] for r in spec['validation']}
        acc=Fraction(sum(dc[sid]==truth[sid] for sid in truth),len(truth))
        acc_nn=Fraction(sum(nn[sid]==truth[sid] for sid in truth),len(truth))
        assert acc==Fraction(*expected['centroid_accuracy_fraction'])
        assert acc_nn==Fraction(*expected['three_nn_accuracy_fraction'])
        result.update(actual=plain(actual),centroid_accuracy=str(acc),three_nn_accuracy=str(acc_nn),assertions='match_manual_frozen_expectations')
    elif case=='controls':
        controls={}
        for label,vals,expected_mean in [('zero',[None,0,2],1),('empty',[],None),('all_missing',[None,None],None),('nan',[float('nan'),0,2],1)]:
            got=observed_mean(vals);eq(got,expected_mean);controls[label]=plain(got)
        leaked=observed_mean([r['reading'] for r in spec['train']])
        eq(leaked,expected['unknown_included_wrong_mean']);assert leaked!=mean
        controls['wrong_fit_unknown_mean']=plain(leaked)
        wrong_zero=observed_mean([r['reading'] for r in rows if r['reading']])
        assert wrong_zero!=mean;controls['wrong_zero_omission_mean']=plain(wrong_zero)
        grid=spec['train'][0]['grid'];assert sum(grid[0])!=sum(r[0] for r in grid)
        controls['same_shape_axis_wrong']={'correct':sum(r[0] for r in grid),'wrong':sum(grid[0])}
        changed=copy.deepcopy(spec);changed['validation'][1]['reading']=999
        v2=predict(changed);assert v2[1]==mean and v2[4]==centers
        controls['validation_999_does_not_change_fit']=True
        flipped=copy.deepcopy(spec);flipped['train'].reverse();v3=predict(flipped)
        assert v3[4]==centers and v3[7]==dc
        controls['centroid_joint_row_permutation']=True
        assert dc['V9']!=nn['V9']
        for text in [expected['centroid_csv'],expected['three_nn_csv']]:validate_csv(text,spec)
        controls['two_different_model_outputs_accepted']=True
        mutants={'header':expected['centroid_csv'].replace('case_id,status','sample_id,prediction'),
          'order':'case_id,status\nV9,ok\nV7,check\nV4,ok\n',
          'duplicate':'case_id,status\nV7,check\nV7,ok\nV4,ok\n',
          'missing':'case_id,status\nV7,check\nV9,ok\n',
          'invalid_label':expected['centroid_csv'].replace('V9,ok','V9,?')}
        rejected=[]
        for name,text in mutants.items():
            try:validate_csv(text,spec)
            except AssertionError:rejected.append(name)
            else:raise AssertionError('format oracle failed to reject '+name)
        controls['format_mutants_rejected']=rejected
        # CSV format alone cannot detect a semantically wrong but allowed prediction.
        assert validate_csv(expected['centroid_csv'].replace('V7,check','V7,ok'),spec)
        controls['valid_shape_wrong_prediction_requires_semantic_review']=True
        result['actual']=controls
    elif case=='physical_csv':
        events=[]
        with tempfile.TemporaryDirectory(prefix='reference-csv-',dir=ROOT) as td:
            path=Path(td)/spec['submission']['filename']
            payload=expected['centroid_csv'].encode('utf-8')
            path.write_bytes(payload);events.append({'stage':'reviewer_reference','operation':'write_bytes','filename':path.name})
            reread=path.read_bytes();events.append({'stage':'reviewer_reference','operation':'read_bytes','filename':path.name})
            assert reread==payload
            parsed=validate_csv(reread.decode(),spec)
            eq(parsed,expected['centroid_submission_rows'])
        assert not path.exists()
        result.update(actual={'rows':parsed,'file_io_events':events,'temporary_file_removed':True,'candidate_physical_io_proven':False})
    else:raise ValueError(case)
    result['status']='passed'
    print(json.dumps(plain(result),ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['arithmetic','controls','physical_csv'],required=True)
    main(p.parse_args().case)
