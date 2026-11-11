#!/usr/bin/env python3
"""Exercise the candidate and non-overwriting builder in a fresh local clone."""
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
AUTHOR=Path("reviews/week01-retrieval-20261111/author")
LESSON=Path("lessons/week01")
STEMS=("week01_axes_linear_bridge","week01_integrated")
COPY=[LESSON/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html","_teacher.md")]
COPY += [AUTHOR/"build_candidate.py",AUTHOR/"validate_candidate.py"]

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run(cmd,cwd):
    return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=240,check=True,
                          env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})

def main():
    before={str(p):sha(ROOT/p) for p in COPY}
    with tempfile.TemporaryDirectory(prefix="week01-retrieval-portable-") as tmp:
        tmp=Path(tmp);clone=tmp/"clone";out=tmp/"new-output"
        run(["git","clone","--quiet","--no-local",str(ROOT),str(clone)],ROOT)
        for rel in COPY:
            dst=clone/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/rel,dst)
        build=[sys.executable,"-B",str(AUTHOR/"build_candidate.py"),"--output-dir",str(out)]
        build_result=run(build,clone)
        generated=[out/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html")]
        current=[clone/LESSON/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html")]
        assert [sha(p) for p in generated]==[sha(p) for p in current]
        old=[sha(p) for p in generated]
        refused=subprocess.run(build,cwd=clone,text=True,capture_output=True,timeout=30,
                               env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})
        assert refused.returncode!=0 and "output directory already exists" in refused.stderr
        assert old==[sha(p) for p in generated]
        check=json.loads(run([sys.executable,"-B",str(AUTHOR/"validate_candidate.py")],clone).stdout)
        assert check["protected_worktree"]=={"status":"not_checked","files_compared":0}
        assert all(x["status"]=="passed" for x in check["results"])
        assert all(str(clone) in p for p in check["source_sha256_before_and_after"])
        result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
                "method":"fresh local clone, copied uncommitted candidates and tools, same installed environment",
                "generated_sha256":dict(zip([p.name for p in generated],[sha(p) for p in generated])),
                "builder_stdout":build_result.stdout.strip(),
                "existing_directory_refused_exit_code":refused.returncode,
                "generated_files_unchanged_after_refusal":True,
                "candidate_results":check["results"],
                "protected_worktree":check["protected_worktree"],
                "limitations":["same Python, libraries, and fonts as source environment",
                               "protected worktree absent from validator arguments",
                               "temporary clone and output are removed",
                               "no actual learner or full browser rendering"]}
    assert before=={str(p):sha(ROOT/p) for p in COPY}
    (ROOT/AUTHOR/"portability.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
