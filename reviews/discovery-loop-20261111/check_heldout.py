"""Independent technical controls for two externally found, non-lesson requirements.
These are new small contract probes, not official task solutions or learner results.
"""
from fractions import Fraction
from pathlib import Path
import hashlib,json
OUT=Path(__file__).resolve().parent
root=OUT.parents[1]

def weighted(y,p):
    weights=[1 if label==-1 else 50 for label in y]
    return Fraction(sum(w for w,a,b in zip(weights,y,p) if a==b),sum(weights))
y=[-1,-1,-1,2];a=[-1,-1,-1,-1];b=[0,0,-1,2]
plain=lambda p:Fraction(sum(i==j for i,j in zip(y,p)),len(y))
assert plain(a)==Fraction(3,4)>plain(b)==Fraction(1,2)
assert weighted(y,a)==Fraction(3,53)<weighted(y,b)==Fraction(51,53)
bad_denominator=Fraction(3,sum(1 if p==-1 else 50 for p in a))
assert bad_denominator!=weighted(y,a)
# New imbalance/label case: the weights depend on true labels, not guesses.
assert weighted([2,-1],[2,2])==Fraction(50,51)

calls=[]
def unavailable_api(*args):
    calls.append(args)
    raise RuntimeError('This inference fixture has no development scorer service')
def bad_submission(label,options,local):
    return unavailable_api(label,options)
def local_submission(label,options,local):
    return [list(local[label])] # illustrative local marker lookup, not a trained solution
try:
    bad_submission('sample',['sample'],{'sample':[1,3]})
    raise AssertionError('Known faulty inference path must fail without the development API')
except RuntimeError: pass
assert len(calls)==1
assert local_submission('sample',['sample'],{'sample':[1,3]})==[[1,3]] and len(calls)==1
assert local_submission('new',['new'],{'new':[2]})==[[2]] and len(calls)==1
session=json.loads((OUT/'runs/session.json').read_text())
final=json.loads((OUT/'runs/final-report.json').read_text())
queue={x['demand_id']:x for x in final['queue']}
assert {'H01','H02'} <= queue.keys()
assert not final['ready_for_review']
result={'status':'passed','implementation_sha256':hashlib.sha256((root/'tools/discovery_loop.py').read_bytes()).hexdigest(),
 'heldout_scope':{'H01':'requirement-level holdout; shares Radar source with development requirements','H02':'additional official generation-task family, Concepts'},
 'H01':{'plain_A':str(plain(a)),'plain_B':str(plain(b)),'weighted_A':str(weighted(y,a)),'weighted_B':str(weighted(y,b)), 'wrong_predicted_label_denominator_rejected':True},
 'H02':{'known_external_dependency_failed':True,'local_dependency_control_passed':True,'network_calls':0},
 'state_replay':{'H01':queue['H01']['reasons'],'H02':queue['H02']['reasons'],'aggregate':final['status']},
 'limits':['The reducer preserves the recorded gap judgments; it does not discover scoring errors from prose by itself.','No official large dataset, hosted API, model training or learner assessment was run.']}
print(json.dumps(result,ensure_ascii=False,indent=2))
