"""Independent contract checks for the blank student's NEW specification (not student work)."""
from pathlib import Path
import io,json,hashlib
import numpy as np,pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.neighbors import NearestCentroid
from sklearn.pipeline import Pipeline
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
book=json.loads((ROOT/'lessons/week01/week01_problem_pipeline.ipynb').read_text())
ns={'pd':pd,'np':np,'io':io,'SimpleImputer':SimpleImputer,'NearestCentroid':NearestCentroid,'Pipeline':Pipeline}
exec(''.join(book['cells'][23]['source']),ns)
train,valid,query=ns['exercise_train'],ns['exercise_validation'],ns['exercise_input']
cols=['vibration','sound','heat'];known=train[train.label.isin([0,1])]
model=Pipeline([('fill',SimpleImputer(strategy='mean')),('classifier',NearestCentroid())]).fit(known[cols],known.label)
pred=model.predict(query[cols]).tolist();expected=dict(zip(query.item,pred))
correct=pd.DataFrame({'item':query.item,'signal':pred}).to_csv(index=False)
def inspect(text):
    table=pd.read_csv(io.StringIO(text))
    assert table.columns.tolist()==['item','signal'],'exact header/2 columns'
    assert table.item.tolist()==query.item.tolist(),'input ID row order/count'
    assert set(table.signal).issubset({0,1}),'only 0/1 permitted'
    assert dict(zip(table.item,table.signal))==expected,'ID prediction provenance'
    return table
inspect(correct)
variants={
 'no_header':'J3,1\nJ1,0\nJ2,0\n',
 'extra_index':pd.DataFrame({'item':query.item,'signal':pred}).to_csv(index=True),
 'old_column_names':'row_id,prediction\nJ3,1\nJ1,0\nJ2,0\n',
 'wrong_sorted_ids':'item,signal\nJ1,0\nJ2,0\nJ3,1\n',
 'unknown_negative_output':'item,signal\nJ3,-1\nJ1,0\nJ2,0\n',
 'predictions_reversed_only':'item,signal\nJ3,0\nJ1,0\nJ2,1\n',
 'missing_row':'item,signal\nJ3,1\nJ1,0\n'}
results=[]
for name,text in variants.items():
 try:inspect(text)
 except AssertionError as error:results.append({'name':name,'status':'detected','reason':str(error),'input_csv':text})
 else:raise AssertionError(name+' survived')
wrong_known=train[train.label.isin([-1,1])]
wrong_mean=SimpleImputer(strategy='mean').fit(wrong_known[cols]).statistics_.tolist()
assert wrong_known.item.tolist()==['R3','R4','R5'] and not np.allclose(wrong_mean,[4,4,2])
results.append({'name':'copied_old_label_mask','status':'detected','wrong_known_ids':wrong_known.item.tolist(),'wrong_means':wrong_mean,'reason':'New unknown=-1 and known 0/1; old mask excludes real normal rows and includes unknown R5'})
# Execute exactly the public teacher's indented example; it is a reference implementation, not student evidence.
teacher=(ROOT/'lessons/week01/week01_problem_pipeline_teacher.md').read_text()
lines=teacher.splitlines();snippet='\n'.join(line[4:] for line in lines if line.startswith('    '))
exec(snippet,ns)
assert ns['valid_pred'].tolist()==[0,1,1]
assert ns['csv_value']==correct
assert np.allclose(ns['independent_model']['fill'].statistics_,[4,4,2])
report={'source_sha256':hashlib.sha256((ROOT/'lessons/week01/week01_problem_pipeline.ipynb').read_bytes()).hexdigest(),'contract_cases':results,'teacher_reference_executed':True,'teacher_reference_matches_fraction_oracle':True,'student_answer_executed':False,'student_learning_observed':False,'scope':'Separate reviewer implementation; model-specific expected vector used only for optional nearest-centroid example, not other classifiers'}
(OUT/'new-contract-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'cases_detected':len(results),'teacher_reference_matches':True}))
