"""Reproduce the closed declared-goal universe using the pinned pre-change inspector."""
import copy, hashlib, json, runpy, subprocess, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=subprocess.check_output(['git','show','c3579c47c7c64ac7d0919410e665a917db4cdeab:tools/contest_depth.py'],cwd=ROOT,text=True)
baseline=types.ModuleType('pinned_contest_depth');exec(compile(SOURCE,'c3579c47c7c64ac7d0919410e665a917db4cdeab:tools/contest_depth.py','exec'),baseline.__dict__)
make=runpy.run_path(str(ROOT/'tests/test_contest_depth.py'))['synthetic_bundle']
bundle=make();original=baseline.inspect(bundle)
external=copy.deepcopy(bundle)
# Fictional external requirements intentionally absent from the selected goals.
external['external_discovery']={'requirements':['derive matrix contraction dimensions','map arbitrary class labels','fit statistics on train partition only']}
unchanged=baseline.inspect(external)
registered=copy.deepcopy(bundle)
registered['target']['goals'].append({'id':'goal:unseen','week':1,'description':'An externally derived new operation'})
visible=baseline.inspect(registered)
actual_path=Path(__file__).resolve().parent/'inputs/baseline-candidate-depth.json'
actual=json.loads(actual_path.read_text())
actual_result=baseline.inspect(actual)
result={'baseline_commit':'c3579c47c7c64ac7d0919410e665a917db4cdeab','baseline_code_sha256':hashlib.sha256(SOURCE.encode()).hexdigest(),
 'cases':[{'id':'declared_scoped_control','expected':'recorded_met','actual':original['status']},
 {'id':'unregistered_external_demands_invisible','expected':'identical_report','actual':'identical_report' if unchanged==original else 'changed_report'},
 {'id':'manually_registered_uncompared_goal_visible','expected':'uncertain','actual':visible['status']}],
 'actual_record':{'path':str(actual_path),'goals':[x['id'] for x in actual['target']['goals']], 'comparisons':[x['id'] for x in actual['comparisons']], 'status':actual_result['status']},
 'interpretation':'This does not demonstrate false validity within the selected scope. It reproduces the absence of external demand discovery: undeclared obligations are invisible until an operator registers them.',
 'limits':['The controls are explicitly synthetic. No source discovery or lesson revision is performed by the old inspector.','Recorded actual status preserves existing uncertainty; it is not upgraded to a pass.']}
assert all(x['expected']==x['actual'] for x in result['cases'])
print(json.dumps(result,ensure_ascii=False,indent=2))
