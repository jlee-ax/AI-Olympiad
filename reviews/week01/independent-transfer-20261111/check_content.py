"""Check actual new Week 1 exercises and teacher guidance; no learner answers are filled."""
import ast
from contextlib import redirect_stdout
from io import StringIO
from html.parser import HTMLParser
from fractions import Fraction
import json
import math
from pathlib import Path
import traceback
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
lesson=ROOT/'lessons/week01'
notebook=json.loads((lesson/'week01_python_tables.ipynb').read_text(encoding='utf-8'))
cells={c['id']:''.join(c.get('source',[])) for c in notebook['cells']}
notes=(lesson/'teacher-notes.txt').read_text(encoding='utf-8')

# Execute the actual unfilled diagnostic example and verify the reported source.
text=cells['7208718e']; marker='**진단 5의 새 오류'
part=text[text.index(marker):]
example=part.split('~~~python\n',1)[1].split('\n~~~',1)[0]
try:
    exec(compile(example,'lesson.py','exec'),{})
    raise AssertionError('The shown uncorrected example must fail')
except IndexError as exc:
    frames=traceback.extract_tb(exc.__traceback__)
    assert [(f.filename,f.lineno) for f in frames[-2:]]==[('lesson.py',4),('lesson.py',2)]
    assert 'IndexError: list index out of range' in part
for body in ('return values[-1]', 'return values[len(values)-1]'):
    assert body in notes
    scope={};exec('def last_value(values):\n    '+body,scope)
    assert scope['last_value']([2,4,6])==6 and scope['last_value']([9])==9
assert '비어 있지 않은' in part and '받은 도움' in part

# The actual mean function honors the stated bounded domain; the old wider claim
# is challenged by a documented finite-float counterexample outside that domain.
ns={}
with redirect_stdout(StringIO()):
    exec(compile(cells['81129230'],'<lesson-mean>','exec'),ns)
mean=ns['mean_of_numbers']
assert mean([1000000]*10000)==1000000 and mean([-1000000,1000000])==0
assert math.isclose(mean([0.1,0.2]),0.15,rel_tol=1e-9,abs_tol=1e-12)
assert math.isinf(mean([1e308,1e308]))  # deliberately outside the new contract
assert '10,000' in cells['b17df2fe'] and '1,000,000' in cells['b17df2fe']
assert '반올림' in cells['b17df2fe'] and '범위 밖' in cells['d96a754b']
assert 'Python 정수 또는 유한한 float' in cells['c6d01f13']

# Fractions give an independent oracle for the exact new numbers.
def variance(xs):
    mu=sum(map(Fraction,xs))/len(xs)
    return sum((Fraction(x)-mu)**2 for x in xs)/len(xs)
x=[1,3,8]
assert sum(x)==12 and variance(x)==Fraction(26,3)
assert variance([n+2 for n in x])==Fraction(26,3)
assert variance([2*n for n in x])==Fraction(104,3)
assert '[1, 3, 8]' in cells['9ce91662'] and '편차' in cells['9ce91662']
assert '26/3cm²' in notes and '104/3cm²' in notes
assert 'student-response' in next(c for c in notebook['cells'] if c['id']=='variance-independent-response')['metadata']['tags']
assert '받은 도움' in cells['variance-independent-response']

# Same output shape, different axis semantics; an incompatible neighbor must fail.
t=np.array([[1,4,7],[2,5,8]])
columns=np.array([10,20,30]);rows=np.array([[100],[200]])
assert (t+columns).shape==(2,3) and (t+columns)[1,2]==38
assert np.array_equal(t+columns,t+columns.reshape(1,3))
assert np.array_equal(t+columns,t+np.tile(columns,(2,1)))
assert (t+rows).shape==(2,3) and (t+rows)[1,2]==208
assert np.array_equal(t+rows,t+np.tile(rows,(1,3)))
try:
    t+np.array([1,2]);raise AssertionError('Incompatible axis sizes must fail')
except ValueError: pass
assert '[[1, 4, 7], [2, 5, 8]]' in cells['df2802a3'] and '받은 도움' in cells['df2802a3']
assert '8+30=38' in notes and '8+200=208' in notes and 'shape(1,3)' in notes

# Use the actual new CSV and independent DataFrame cases for the merge contract.
original=pd.read_csv(lesson/'data/week1_plants_new.csv')
changed=original.copy(deep=True);changed.loc[changed['sample_id']=='Q02','site']='옥상'
lookup=pd.DataFrame({'site':['실내','창가'],'note':['실내 관찰 구역','창가 관찰 구역']})
merged=changed.merge(lookup,on='site',how='left',validate='many_to_one')
assert len(merged)==4 and merged.loc[merged['note'].isna(),'sample_id'].tolist()==['Q02']
duplicate=pd.concat([lookup,lookup.iloc[[0]]],ignore_index=True)
try:
    changed.merge(duplicate,on='site',how='left',validate='many_to_one')
    raise AssertionError('Duplicate right keys must fail the validation')
except pd.errors.MergeError: pass
without_check=changed.merge(duplicate,on='site',how='left')
assert len(without_check)==5 and len(without_check[without_check['sample_id']=='Q01'])==2
# A fresh, unmodified left table would duplicate both indoor rows, not one.
assert len(original.merge(duplicate,on='site',how='left'))==6
assert 'Q02가 옥상인 화분 복사본을 그대로 유지' in cells['0fd965eb']
assert original.loc[original['sample_id']=='Q02','site'].item()=='실내'
assert '옥상' in cells['0fd965eb'] and 'MergeError' in notes and '총 5행' in notes

# Execute the actual prepared dirty-input cell, preserving the underlying dataset.
plants=pd.read_csv(lesson/'data/week1_plants.csv')
plant_baseline=plants.copy(deep=True)
scope={'plants':plants,'pd':pd}
exec(compile(cells['d7c7b7c4'],'<lesson-dirty-input>','exec'),scope)
dirty=scope['dirty_plants']
assert dirty.loc[dirty['pot_id']=='P02','water_ml'].item()=='20ml'
try:
    pd.to_numeric(dirty['water_ml'],errors='raise')
    raise AssertionError('Raw unit string must fail numeric conversion')
except ValueError: pass
cleaned=dirty.copy(deep=True)
cleaned['water_ml']=pd.to_numeric(cleaned['water_ml'].replace({'20ml':'20'}),errors='raise')
assert cleaned['water_ml'].count()==5 and cleaned['water_ml'].sum()==140 and cleaned['water_ml'].mean()==28
assert pd.isna(cleaned.loc[cleaned['pot_id']=='P03','water_ml'].item())
coerced=pd.to_numeric(dirty['water_ml'],errors='coerce')
assert coerced.count()==4 and coerced.mean()==30  # silently lost P02
pd.testing.assert_frame_equal(plants,plant_baseline)
assert dirty.loc[dirty['pot_id']=='P02','water_ml'].item()=='20ml'
try:
    pd.to_numeric(pd.Series(['20ml','mystery']).replace({'20ml':'20'}),errors='raise')
    raise AssertionError('Unknown strings must not be silently removed')
except ValueError: pass
assert 'dirty_plants' in cells['b38de2c6'] and '평균28ml' in notes

# Missing heights: row count and observed count have different denominators.
missing_height=original.copy(deep=True)
missing_height.loc[missing_height['sample_id']=='Q02','final_height_cm']=np.nan
indoor=missing_height[missing_height['site']=='실내']['final_height_cm']
assert indoor.size==2 and indoor.count()==1 and indoor.mean()==7
empty=indoor.copy();empty[:]=np.nan
assert empty.size==2 and empty.count()==0 and pd.isna(empty.mean())
assert original.loc[original['sample_id']=='Q02','final_height_cm'].item()==9
assert '이 복사본은 아래 병합 실험과 별개' in cells['0fd965eb']
assert '높이 관측수1' in notes and '평균7cm' in notes

# Match vector entries by names, not just length.
quantities=np.array([1,4,2]); aligned=np.array([800,500,1200]); supplier=np.array([500,1200,800])
assert len(quantities)==len(aligned)==len(supplier)==3
assert quantities@aligned==5200 and quantities@supplier==6900
assert np.array([2,1])@np.array([6,4])==16
assert 'B, C, A 순서' in cells['1e511556'] and '6900원' in notes and '5200원' in notes

# Actual source-table coordinates and a noncausal interpretation, not learner results.
for name,expected in [('Q02',(2,9)),('Q04',(5,14))]:
    row=original.loc[original['sample_id']==name].iloc[0]
    assert (row['light_hours'],row['final_height_cm'])==expected
assert '(4h,9cm), (7h,14cm)' in notes and '인과관계' in notes
assert 'Q02와 Q04' in cells['d60c3acd'] and '합성 표' in cells['d60c3acd']

# Student code slots remain unfilled and answer key remains in the teacher file.
for cell in notebook['cells']:
    if 'student-code' in cell.get('metadata',{}).get('tags',[]):
        assert all(not line.strip() or line.lstrip().startswith('#') for line in cell['source'])
assert 'def recorded_mean(values):' not in '\n'.join(cells.values())
assert not (lesson/'README.md').exists()
# Static content only: this is not a browser/layout or accessibility test.
class Text(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,data): self.parts.append(data)
parser=Text();parser.feed((lesson/'week01_python_tables.html').read_text(encoding='utf-8'))
body=' '.join(parser.parts)
for phrase in ('진단 5의 새 오류','새 배열을 혼자 예측하고 확인하기','새 분산 문제에 내 말로 답하기','새 병합 조건을 먼저 예측하기','결측 높이와 집계를 먼저 예측하기'):
    assert phrase in body
assert 'def recorded_mean(values):' not in body
print(json.dumps({'status':'passed','traceback':'actual error location, fixes and boundary verified',
 'variance':'exact fractions, translation and scaling checked',
 'broadcast':'valid row/column operations and incompatible shape checked',
 'merge':'actual new CSV, unmatched/duplicate keys and source immutability checked',
 'graph':'actual new CSV coordinates and translated positions checked',
 'dirty_input':'actual prepared string fails raw numeric conversion; targeted repair preserves unknowns and original',
 'missing_height':'size/count/mean and all-missing boundary checked on copies of real CSV',
 'vector_order':'same-length misaligned and aligned totals plus retry checked',
 'html_static_content':'five prompts present and teacher solution absent; layout unverified',
 'learner_answers':'blank_not_observed'},ensure_ascii=False,indent=2))
