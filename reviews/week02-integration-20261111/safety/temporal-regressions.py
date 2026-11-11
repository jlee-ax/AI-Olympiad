"""Supplement validator safety tests; all execution uses preserved temporary copies."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import traceback

ROOT=Path(__file__).resolve().parents[3]
SAFETY=Path(__file__).resolve().parent
BASELINE=SAFETY/'temporal-baseline'
PYTHON=Path('/workspace/scratch/d500e5cb2076/olympiad-week1-cloud/.venv/bin/python')
SCRIPT='validate_week02_temporal_preprocessing.py'
BOOK='week02_temporal_preprocessing.ipynb'
HTML='week02_temporal_preprocessing.html'
GUIDE='week02_temporal_preprocessing_teacher.md'
OLD='week02_temporal_preprocessing_validation.json'
NAMES=[BOOK,HTML,GUIDE,OLD]
EXPECTED='b5f555d8d089b5856f952f74f683fc44bd8404c6449c355f1e48b4a25f98477c'
sha=lambda data:hashlib.sha256(data).hexdigest()
parser=argparse.ArgumentParser()
parser.add_argument('--fixture',type=Path,default=BASELINE)
parser.add_argument('--validator',type=Path,default=ROOT/'lessons/week02'/SCRIPT)
parser.add_argument('--expected-validator-sha')
parser.add_argument('--results',type=Path,default=SAFETY/'temporal-results.json')
args=parser.parse_args()
raw={name:(args.fixture/name).read_bytes() for name in NAMES}
assert sha(raw[BOOK])==EXPECTED
validator=args.validator.read_bytes()
if args.expected_validator_sha:assert sha(validator)==args.expected_validator_sha
book=json.loads(raw[BOOK])
cases=[]
def add(name,expected=0,detector=None,mutation=None,path_case=None,wrapper=None,write=False):
    cases.append(dict(name=name,expected=expected,detector=detector,mutation=mutation,path_case=path_case,wrapper=wrapper,write=write))
add('normal_default_stdout')
add('new_report',write=True)
for path_case in ('existing_file','existing_directory','symlink_file','dangling_symlink','symlink_parent','missing_parent','overlap_input'):
    detector='symlink' if 'symlink' in path_case else ('existing directory' if path_case=='missing_parent' else 'NEW file')
    add('path_'+path_case,1,detector,path_case=path_case,write=True)
add('comment_answer',1,'original blank exercise comment template',lambda b,a:a.update(source=''.join(a['source'])+'\n# 정답은 중앙값9입니다'))
add('code_answer',1,'original blank exercise comment template',lambda b,a:a.update(source=''.join(a['source'])+'\nanswer=9'))
def duplicate(b,a):
    c=copy.deepcopy(a);c['id']='duplicate-exercise';b['cells'].append(c)
add('duplicate_exercise',1,'Exactly one independent-exercise',duplicate)
def tagged_markdown(b,a):
    b['cells'].append(dict(cell_type='markdown',id='duplicate-tagged-markdown',metadata={'tags':['independent-exercise']},source='reviewer duplicate'))
add('duplicate_tagged_markdown',1,'Exactly one independent-exercise',tagged_markdown)
add('stored_exercise_output',1,'unexecuted and have no saved outputs',lambda b,a:a.update(outputs=[dict(output_type='stream',name='stdout',text='saved answer')]))
add('executed_exercise_count7',1,'unexecuted and have no saved outputs',lambda b,a:a.update(execution_count=7))
add('missing_exercise',1,'Exactly one independent-exercise',lambda b,a:b['cells'].remove(a))
add('optimized_flag',1,'Optimized Python disables QA assertions',path_case='optimized')
add('optimized_env',1,'Optimized Python disables QA assertions',path_case='optimized_env')
def extra(code):
    def mutate(b,a):
        b['cells'].append(dict(cell_type='code',id='reviewer-extra',metadata={},source=code,execution_count=1,outputs=[]))
    return mutate
add('code_runtime_failure',1,'reviewer runtime failure',extra("raise RuntimeError('reviewer runtime failure')"),write=True)
add('actual_temporal_qa_failure',1,'expected_recent',extra("val_x.loc[val_x.index[0], 'recent'] = 999"),write=True)
add('report_construction_failure',1,'reviewer report failure',wrapper="m.platform.platform=lambda: (_ for _ in ()).throw(RuntimeError('reviewer report failure'))",write=True)
add('partial_write_rollback',1,'reviewer partial write failure',path_case='partial_write',write=True)
add('late_report_collision',1,'NEW file',path_case='late_collision',write=True)
for input_name in (BOOK,HTML,GUIDE):add('input_changed_'+input_name,1,'Input changed during validation',path_case='input_changed:'+input_name,write=True)

def run(case):
    with tempfile.TemporaryDirectory(prefix='temporal-safety-case-') as temporary:
        folder=Path(temporary);input_dir=folder/'input';input_dir.mkdir()
        for name,data in raw.items():(input_dir/name).write_bytes(data)
        script=input_dir/SCRIPT;script.write_bytes(validator)
        b=copy.deepcopy(book);a=next(c for c in b['cells'] if 'independent-exercise' in c['metadata'].get('tags',[]))
        if case['mutation']:
            case['mutation'](b,a);(input_dir/BOOK).write_text(json.dumps(b,ensure_ascii=False))
        output=folder/'NEW.json';kind=case['path_case'];wrapper=case['wrapper'] or ''
        if kind=='existing_file':output=input_dir/OLD
        elif kind=='existing_directory':output=input_dir
        elif kind=='symlink_file':output=folder/'link.json';output.symlink_to(input_dir/OLD)
        elif kind=='dangling_symlink':output=folder/'link.json';output.symlink_to(folder/'absent')
        elif kind=='symlink_parent':(folder/'link').symlink_to(input_dir,target_is_directory=True);output=folder/'link'/'NEW.json'
        elif kind=='missing_parent':output=folder/'absent'/'NEW.json'
        elif kind=='overlap_input':output=input_dir/BOOK
        elif kind=='partial_write':
            wrapper="""original_open=m.Path.open
class Broken:
    def __init__(self,f):self.f=f
    def __enter__(self):return self
    def __exit__(self,*a):return self.f.__exit__(*a)
    def fileno(self):return self.f.fileno()
    def write(self,text):
        self.f.write(text[:23]);self.f.flush();raise OSError('reviewer partial write failure')
def patched_open(self,mode='r',*a,**k):
    opened=original_open(self,mode,*a,**k)
    return Broken(opened) if mode=='x' else opened
m.Path.open=patched_open
"""
        elif kind=='late_collision':
            wrapper="""original_write=m.write_new_report
def late(path,rendered):
    path.write_text('concurrent user result');return original_write(path,rendered)
m.write_new_report=late
"""
        elif kind and kind.startswith('input_changed:'):
            target=input_dir/kind.split(':',1)[1]
            wrapper="target=m.Path("+repr(str(target))+")\noriginal_platform=m.platform.platform\nalready=False\ndef changed_input():\n    global already\n    if not already:\n        target.write_bytes(target.read_bytes()+b'\\n');already=True\n    return original_platform()\nm.platform.platform=changed_input\n"
        protected=[input_dir/name for name in NAMES]
        before={p.name:sha(p.read_bytes()) for p in protected};expected_after=dict(before)
        if kind and kind.startswith('input_changed:'):
            name=kind.split(':',1)[1];expected_after[name]=sha((input_dir/name).read_bytes()+b'\n')
        cli=['--write',str(output)] if case['write'] else []
        if wrapper:
            runner=folder/'runner.py';runner.write_text("import importlib.util\ns=importlib.util.spec_from_file_location('temporal_validator',"+repr(str(script))+")\nm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"+wrapper+"\nm.main("+repr(cli)+")\n")
            command=[str(PYTHON),'-B',str(runner)]
        else:command=[str(PYTHON),'-B',*(['-O'] if kind=='optimized' else []),str(script),*cli]
        cache=folder/'cache';cache.mkdir();env=os.environ.copy();env['TMPDIR']=str(cache);env['PYTHONDONTWRITEBYTECODE']='1';env['MPLBACKEND']='Agg'
        for key in ('IPYTHONDIR','MPLCONFIGDIR','JUPYTER_RUNTIME_DIR','JUPYTER_CONFIG_DIR','JUPYTER_DATA_DIR','XDG_CACHE_HOME'):env[key]=str(cache/key.lower())
        if kind=='optimized_env':env['PYTHONOPTIMIZE']='1'
        result=subprocess.run(command,cwd=input_dir,env=env,capture_output=True,text=True,timeout=120)
        after={p.name:sha(p.read_bytes()) for p in protected}
        checks=dict(expected_exit_and_detector=result.returncode==case['expected'] and (not case['detector'] or case['detector'] in result.stderr),input_and_existing_report_match_expected=after==expected_after,no_adjacent_new_files=set(p.name for p in input_dir.iterdir())==set(NAMES)|{SCRIPT})
        report=None
        if case['expected']==0 and result.returncode==0:
            report=json.loads(result.stdout)
            checks['report_records_checked_input_snapshot']=all(report['sha256'][name]==before[name] for name in (BOOK,HTML,GUIDE))
            checks['report_does_not_claim_old_capture_or_warning']='saved_output_capture' not in report and 'saved_output_capture_warning' not in report and 'previous_attempt' not in report
            if case['write']:checks['new_report_json_equals_stdout']=json.loads(output.read_text())==json.loads(result.stdout)
            else:checks['default_created_no_report']=not output.exists()
        elif case['write'] and kind in (None,'partial_write'):
            checks['no_partial_new_report']=not output.exists()
        if kind=='late_collision':checks['late_user_result_preserved']=output.read_text()=='concurrent user result'
        if kind and kind.startswith('input_changed:'):
            checks['user_input_change_preserved']=after==expected_after and after!=before
            checks['no_stale_report']=not output.exists()
        cache_entries=[str(p.relative_to(cache)) for p in cache.rglob('*')]
        shutil.rmtree(cache);checks['test_cache_removed_by_harness']=not cache.exists()
        return dict(name=case['name'],passed=all(checks.values()),returncode=result.returncode,detector=case['detector'],checks=checks,before_sha256=before,expected_after_sha256=expected_after,after_sha256=after,stdout=result.stdout,stderr=result.stderr,cache_entries_before_harness_cleanup=cache_entries)

def run_safe(case):
    try:return run(case)
    except Exception:return dict(name=case['name'],passed=False,returncode=None,checks={'harness_completed':False},stderr=traceback.format_exc())
with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(run_safe,cases))
report=dict(created_utc=datetime.now(timezone.utc).isoformat(),validator_sha256=sha(validator),notebook_sha256=EXPECTED,all_passed=all(c['passed'] for c in results),cases=results,execution='existing venv Python -B in temporary copies; no socket kernel or package installation',limitations=['arbitrary notebook Python is not OS isolated','temporary cache paths are supplied and removed by this test harness','finite teacher reference cases and blank-state guard are not student achievement verification'])
args.results.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(all_passed=report['all_passed'],validator_sha256=report['validator_sha256'],cases=[{k:c[k] for k in ('name','passed','returncode')} for c in results]),ensure_ascii=False,indent=2))
if not report['all_passed']:raise SystemExit(1)
