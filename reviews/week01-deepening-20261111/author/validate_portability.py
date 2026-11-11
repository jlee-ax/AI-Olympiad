#!/usr/bin/env python3
"""Exercise the validator and safe builder in an isolated local clone."""
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
AUTHOR=Path("reviews/week01-deepening-20261111/author")
LESSON=Path("lessons/week01")
COPY=[LESSON/"week01_integrated.ipynb",LESSON/"week01_integrated.html",
      LESSON/"week01_integrated_teacher.md",AUTHOR/"validate_deepening.py",
      AUTHOR/"build_deepening.py"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd,cwd):
    return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=180,check=True,
                          env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})

def main():
    before={str(p):sha(ROOT/p) for p in COPY}
    with tempfile.TemporaryDirectory(prefix="week01-portable-") as temp:
        tmp=Path(temp); clone=tmp/"clone"; generated=tmp/"generated"
        run(["git","clone","--quiet","--no-local",str(ROOT),str(clone)],ROOT)
        for rel in COPY:
            dest=clone/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/rel,dest)
        command=[sys.executable,"-B",str(AUTHOR/"build_deepening.py"),"--output-dir",str(generated)]
        built=run(command,clone)
        outfiles=[generated/"week01_integrated.ipynb",generated/"week01_integrated.html"]
        assert [sha(f) for f in outfiles]==[sha(clone/LESSON/"week01_integrated.ipynb"),
                                           sha(clone/LESSON/"week01_integrated.html")]
        generated_before=[sha(f) for f in outfiles]
        again=subprocess.run(command,cwd=clone,text=True,capture_output=True,timeout=30,
                             env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})
        assert again.returncode!=0 and "output directory already exists" in again.stderr
        assert generated_before==[sha(f) for f in outfiles]
        validation=json.loads(run([sys.executable,"-B",str(AUTHOR/"validate_deepening.py")],clone).stdout)
        assert validation["protected_worktree"]["status"]=="not_checked"
        assert validation["protected_worktree"]["files_compared"]==0
        assert len(validation["checks"])==9
        assert all(str(clone) in p for p in validation["source_sha256_before_and_after"])
        follow=json.loads(run([sys.executable,"-B","reviews/week01-integration-20261111/author/validate_followup_route.py"],clone).stdout)
        assert all(item["status"]=="passed" for item in follow["results"])
        outcome={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
                 "method":"fresh local git clone; copy current uncommitted candidate and author tools; execute with current Python",
                 "builder_stdout":built.stdout.strip(),
                 "generated_sha256":[sha(f) for f in outfiles],
                 "builder_existing_directory_refused":True,
                 "builder_refusal_exit_code":again.returncode,
                 "builder_output_unchanged_after_refusal":True,
                 "candidate_validation_checks":validation["checks"],
                 "protected_worktree":validation["protected_worktree"],
                 "followup_results":follow["results"],
                 "limitations":["same installed Python, libraries, and fonts as source workspace",
                                "clone used no protected-worktree argument",
                                "temporary clone and generated files are removed",
                                "no learner observation or full browser rendering"]}
    assert before=={str(p):sha(ROOT/p) for p in COPY}
    (ROOT/AUTHOR/"portability.json").write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(outcome,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
