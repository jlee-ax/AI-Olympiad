#!/usr/bin/env python3
"""Test safe builders and candidate checks in an isolated local clone."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
AUTHOR=Path("reviews/week01-sequence-20261111/author")
LESSON=Path("lessons/week01")
STEMS=("week01_axes_linear_bridge","week01_integrated")
COPY=[LESSON/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html","_teacher.md")]
COPY += [AUTHOR/"build_candidate.py",AUTHOR/"validate_candidate.py"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def run(cmd,cwd):
    return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=240,check=True,
                          env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})
def main():
    before={str(p):sha(ROOT/p) for p in COPY}
    with tempfile.TemporaryDirectory(prefix="week01-sequence-portable-") as tmp:
        tmp=Path(tmp);clone=tmp/"clone";prior=tmp/"prior";out=tmp/"candidate"
        run(["git","clone","--quiet","--no-local",str(ROOT),str(clone)],ROOT)
        for rel in COPY:
            dst=clone/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/rel,dst)
        previous=Path("reviews/week01-retrieval-20261111/author/build_candidate.py")
        run([sys.executable,"-B",str(previous),"--output-dir",str(prior)],clone)
        build=[sys.executable,"-B",str(AUTHOR/"build_candidate.py"),
               "--bridge-baseline",str(prior/"week01_axes_linear_bridge.ipynb"),
               "--integrated-baseline",str(prior/"week01_integrated.ipynb"),
               "--output-dir",str(out)]
        built=run(build,clone)
        generated=[out/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html")]
        current=[clone/LESSON/(stem+suffix) for stem in STEMS for suffix in (".ipynb",".html")]
        assert [sha(p) for p in generated]==[sha(p) for p in current]
        output_sha=[sha(p) for p in generated]
        refused=subprocess.run(build,cwd=clone,text=True,capture_output=True,timeout=30,
                               env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})
        assert refused.returncode!=0 and "output directory already exists" in refused.stderr
        assert output_sha==[sha(p) for p in generated]
        validator=[sys.executable,"-B",str(AUTHOR/"validate_candidate.py")]
        validation=json.loads(run(validator,clone).stdout)
        assert validation["protected_worktree"]=={"status":"not_checked","files_compared":0}
        assert all(x["status"]=="passed" for x in validation["results"])
        assert all(str(clone) in p for p in validation["source_sha256_before_and_after"])
        sentinel=tmp/"already-exists.json";sentinel.write_text("do not overwrite",encoding="utf-8")
        refused_json=subprocess.run(validator+["--write",str(sentinel)],cwd=clone,
                                    text=True,capture_output=True,timeout=240,
                                    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","LOKY_MAX_CPU_COUNT":"1"})
        assert refused_json.returncode!=0 and "FileExistsError" in refused_json.stderr
        assert sentinel.read_text(encoding="utf-8")=="do not overwrite"
        result={"checked_at_utc":datetime.now(timezone.utc).isoformat(),
                "method":"fresh local clone, copied uncommitted candidate and tools, same installed environment",
                "generated_sha256":dict(zip([p.name for p in generated],output_sha)),
                "builder_stdout":built.stdout.strip(),
                "existing_output_directory_refused":True,
                "existing_output_directory_exit_code":refused.returncode,
                "generated_files_unchanged_after_refusal":True,
                "validator_existing_json_refused":True,
                "validator_existing_json_exit_code":refused_json.returncode,
                "sentinel_unchanged":True,
                "candidate_results":validation["results"],
                "protected_worktree":validation["protected_worktree"],
                "limitations":["same Python, packages, and fonts as source environment",
                               "previous committed builder and baseline artifacts must be present",
                               "protected worktree absent from validator arguments",
                               "temporary clone and output are removed",
                               "no learner observation or full browser rendering"]}
    assert before=={str(p):sha(ROOT/p) for p in COPY}
    with (ROOT/AUTHOR/"portability.json").open("x",encoding="utf-8") as stream:
        stream.write(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
