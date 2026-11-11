#!/usr/bin/env python3
"""Run only the student-directed preparation and supporting example cells.

The original and bridge notebooks run in separate fresh Python processes with
in-process kernels. Their student answer cells are not filled.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LESSON = ROOT / "lessons/week01"
ORIGINAL = LESSON / "week01_python_tables.ipynb"
BRIDGE = LESSON / "week01_axes_linear_bridge.ipynb"
WORKER = r'''
import json,sys
from pathlib import Path
import nbformat
from ipykernel.inprocess.manager import InProcessKernelManager

path=Path(sys.argv[1]); kind=sys.argv[2]
book=nbformat.read(path,as_version=4)
# Three preparation cells first; other listed cells are only examples that the
# cited exercises actually depend upon. Answer cells are never completed.
indices=([3,27,54,19,20,22,43,46,48,59,64,69,71,73,74,78,84]
         if kind=="original" else [2,21,23,25,27])
manager=InProcessKernelManager();manager.start_kernel()
shell=manager.kernel.shell;client=manager.client();client.start_channels()
try:
 for i in indices:
  cell=book.cells[i]
  assert cell.cell_type=="code",i
  client.execute(cell.source,store_history=True)
  reply=client.get_shell_msg(timeout=120)
  if reply["content"]["status"]!="ok":raise RuntimeError(f"cell {i}: {reply['content']}")
  errors=[]
  while True:
   msg=client.get_iopub_msg(timeout=120)
   if msg["msg_type"]=="status" and msg["content"].get("execution_state")=="idle":break
   if msg["msg_type"]=="error":errors.append(msg["content"])
  assert not errors,(i,errors)
 ns=shell.user_ns
 if kind=="original":
  assert "sunlight_hours" in ns["plants"].columns
  assert "light_h" not in ns["plants"].columns
  assert ns["plants"].shape==(6,5)
  assert ns["plants"].loc[ns["plants"]["pot_id"]=="P05","water_ml"].item()==20
  assert set(["sample_id","site","light_hours","water_amount_ml","final_height_cm"]).issubset(ns["new_plants"].columns)
  assert ns["new_plants"].shape==(4,5) and ns["B"].shape==(2,3)
  assert ns["dirty_plants"].loc[ns["dirty_plants"]["pot_id"]=="P02","water_ml"].item()=="20ml"
  assert ns["site_notes"].shape==(2,2)
  assert "sns" in ns
 else:
  assert ns["X_new"].shape==(3,2) and ns["W_new"].shape==(2,2)
  assert ns["query_new"].shape==(2,2) and ns["gallery_new"].shape==(4,2)
  assert ns["q_ids_new"].tolist()==[61,22]
 print(json.dumps({"notebook":kind,"executed_cell_indices_zero_based":indices,"status":"passed"},ensure_ascii=False))
finally:
 client.stop_channels();manager.shutdown_kernel();shell._atexit_once()
'''


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", help="Optional JSON receipt")
    args = parser.parse_args()
    paths = [ORIGINAL, BRIDGE, LESSON / "data/week1_plants.csv",
             LESSON / "data/week1_plants_new.csv"]
    before = {str(path): digest(path) for path in paths}
    results = []
    for kind, notebook in (("original", ORIGINAL), ("bridge", BRIDGE)):
        with tempfile.TemporaryDirectory(prefix=f"week1-route-{kind}-") as temp:
            env = os.environ.copy()
            env.update({"IPYTHONDIR": temp, "MPLCONFIGDIR": temp,
                        "PYDEVD_DISABLE_FILE_VALIDATION": "1",
                        "PYTHONDONTWRITEBYTECODE": "1", "LOKY_MAX_CPU_COUNT": "1"})
            process = subprocess.run(
                [sys.executable, "-B", "-c", WORKER, str(notebook), kind],
                cwd=LESSON, env=env, text=True, capture_output=True, timeout=120)
            if process.returncode:
                raise RuntimeError(f"{kind} failed ({process.returncode})\n{process.stdout}\n{process.stderr}")
            results.append(json.loads(process.stdout))
    assert before == {str(path): digest(path) for path in paths}
    receipt = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validator_sha256": digest(Path(__file__)),
        "source_sha256_before_and_after": before,
        "method": "two separate fresh Python processes, each with an in-process IPython kernel",
        "results": results,
        "limits": [
            "Student answer cells are empty and no learner completed the exercises",
            "Only the stated preparation and supporting examples were executed",
            "No ordinary socket kernel or full HTML browser rendering was tested"
        ]
    }
    if args.write:
        Path(args.write).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
