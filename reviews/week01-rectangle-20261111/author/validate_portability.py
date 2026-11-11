#!/usr/bin/env python3
"""Rebuild and check the candidate in an isolated local clone without overwriting results."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
LESSON=Path('lessons/week01')
AUTHOR=Path('reviews/week01-rectangle-20261111/author')
COPY=[LESSON/'week01_integrated.ipynb',LESSON/'week01_integrated.html',LESSON/'week01_integrated_teacher.md',
      AUTHOR/'build_candidate.py',AUTHOR/'validate_candidate.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd,cwd,timeout=240):
 p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=timeout,
                  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','LOKY_MAX_CPU_COUNT':'1'})
 if p.returncode:raise RuntimeError(f'command failed: {cmd}\n{p.stdout}\n{p.stderr}')
 return p
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--write',type=Path,help='new result path; existing files are refused')
 args=parser.parse_args()
 if args.write and args.write.exists():parser.error('result path already exists')
 before={str(p):sha(ROOT/p) for p in COPY}
 with tempfile.TemporaryDirectory(prefix='week01-rectangle-portability-') as tmp:
  tmp=Path(tmp);clone=tmp/'clone';retrieval=tmp/'retrieval';sequence=tmp/'sequence';out=tmp/'rectangle'
  run(['git','clone','--quiet','--no-local',str(ROOT),str(clone)],ROOT)
  for rel in COPY:
   target=clone/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
  p1=run([sys.executable,'-B','reviews/week01-retrieval-20261111/author/build_candidate.py',
          '--output-dir',str(retrieval)],clone)
  p2=run([sys.executable,'-B','reviews/week01-sequence-20261111/author/build_candidate.py',
          '--bridge-baseline',str(retrieval/'week01_axes_linear_bridge.ipynb'),
          '--integrated-baseline',str(retrieval/'week01_integrated.ipynb'),
          '--output-dir',str(sequence)],clone)
  build=[sys.executable,'-B',str(AUTHOR/'build_candidate.py'),
         '--baseline',str(sequence/'week01_integrated.ipynb'),'--output-dir',str(out)]
  p3=run(build,clone)
  outputs=[out/'week01_integrated.ipynb',out/'week01_integrated.html']
  current=[clone/LESSON/'week01_integrated.ipynb',clone/LESSON/'week01_integrated.html']
  assert [sha(p) for p in outputs]==[sha(p) for p in current]
  generated=[sha(p) for p in outputs]
  refused=subprocess.run(build,cwd=clone,text=True,capture_output=True,timeout=60)
  assert refused.returncode!=0 and 'output directory already exists' in refused.stderr
  assert generated==[sha(p) for p in outputs]
  validator=[sys.executable,'-B',str(AUTHOR/'validate_candidate.py')]
  result=json.loads(run(validator,clone).stdout)
  assert all(x['status']=='passed' for x in result['results'])
  assert result['protected_worktree']['status']=='not_checked'
  sentinel=tmp/'existing.json';sentinel.write_text('do not overwrite',encoding='utf-8')
  blocked=subprocess.run(validator+['--write',str(sentinel)],cwd=clone,text=True,capture_output=True,
                         timeout=240,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','LOKY_MAX_CPU_COUNT':'1'})
  assert blocked.returncode!=0 and 'FileExistsError' in blocked.stderr
  assert sentinel.read_text(encoding='utf-8')=='do not overwrite'
  report={'checked_at_utc':datetime.now(timezone.utc).isoformat(),
          'method':'fresh local clone, copied uncommitted candidate and tools, same installed environment',
          'generated_sha256':dict(zip([p.name for p in outputs],generated)),
          'previous_builders_stdout':[p1.stdout.strip(),p2.stdout.strip()],
          'candidate_builder_stdout':p3.stdout.strip(),
          'existing_output_directory_refused':True,'generated_files_unchanged':True,
          'existing_json_refused':True,'json_sentinel_unchanged':True,
          'candidate_results':result['results'],'protected_worktree':result['protected_worktree'],
          'limitations':['same Python packages and fonts as source environment',
                         'previous committed builders and baseline artifacts are required',
                         'protected worktree not supplied','no learner or browser rendering observation']}
 assert before=={str(p):sha(ROOT/p) for p in COPY}
 if args.write:
  with args.write.open('x',encoding='utf-8') as stream:
   stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
