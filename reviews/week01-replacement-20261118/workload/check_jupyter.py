"""Run each archived public notebook in a separate process with a fresh in-process IPython kernel."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve().parent
CHILD = """
import json
import sys
from pathlib import Path
from IPython.utils.capture import capture_output
from ipykernel.inprocess.manager import InProcessKernelManager

notebook = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
manager = InProcessKernelManager()
manager.start_kernel()
shell = manager.kernel.shell
with capture_output():
    shell.run_line_magic("matplotlib", "inline")
executed, images, worked_ids = [], [], []
for cell in notebook["cells"]:
    if cell["cell_type"] != "code":
        continue
    with capture_output() as captured:
        result = shell.run_cell("".join(cell["source"]), store_history=True)
    if result.error_before_exec or result.error_in_exec:
        raise ValueError(f"Cell {cell['id']} failed: {result.error_before_exec or result.error_in_exec}")
    executed.append(cell["id"])
    if any("image/png" in item.data for item in captured.outputs):
        images.append(cell["id"])
    if cell["id"] == "repair-match":
        assert "['M07', 'M12']" in captured.stdout
        worked_ids = ["M07", "M12"]
manager.shutdown_kernel()
print(json.dumps({"executed_code_cells": executed, "image_cells": images, "worked_ids_from_stdout": worked_ids}))
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(number):
    case = ROOT / "reviews/week01-depth-20261118/rounds" / f"{number:04d}"
    record = json.loads((case / "round.json").read_text(encoding="utf-8"))
    paths = {"main": case / "candidate.ipynb", "repair": OWN / "inputs/week01_foundations_repair.ipynb"}
    if sha(paths["main"]) != record["candidate_sha256"]:
        raise ValueError("Archived main differs from round")
    reports, sources = {}, {}
    with tempfile.TemporaryDirectory(prefix="week01-kernel-audit-") as tmp:
        course = Path(tmp)
        data = course / "data"
        data.mkdir()
        env = os.environ.copy()
        for name in ("IPYTHONDIR", "MPLCONFIGDIR", "JUPYTER_CONFIG_DIR", "JUPYTER_RUNTIME_DIR"):
            folder = course / name.lower()
            folder.mkdir()
            env[name] = str(folder)
        for companion in record["companions"]:
            name = Path(companion["path"]).name
            if name.endswith(".csv"):
                source = ROOT / companion["snapshot"]
                if sha(source) != companion["sha256"]:
                    raise ValueError("Archived CSV differs: " + name)
                sources[name] = sha(source)
                shutil.copyfile(source, data / name)
        for role, path in paths.items():
            ran = subprocess.run([sys.executable, "-B", "-c", CHILD, str(path)], cwd=course, env=env,
                                 text=True, capture_output=True, check=True)
            result = json.loads(ran.stdout.splitlines()[-1])
            if role == "main" and len(result["image_cells"]) < 3:
                raise ValueError("Expected all three worked example figures")
            reports[role] = {"sha256": sha(path), **result}
    return {"round": number, "round_sha256": sha(case / "round.json"), "data_sha256": sources,
            "notebooks": reports, "scope": "Separate processes with fresh in-process IPython kernels, unmodified public student notebooks, and the three pinned CSVs in a temporary course directory. Delivered student response cells are left as supplied. The independent fresh and return answers are in the corresponding recovery-route receipt.",
            "status": "passed"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--round", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.round), ensure_ascii=False, indent=2))
