"""Execute every student notebook on a declared route in a separate process and fresh Jupyter kernel."""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path
from comparison_material import material


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(root, route, path, inputs, directory, transport, output_cache):
    import nbformat
    from nbclient import NotebookClient
    from jupyter_client import KernelManager

    src = root / path
    source = material(root, route, path)
    nb = nbformat.reads(source.decode("utf-8"), as_version=4)
    nbformat.validate(nb)
    code = [c for c in nb.cells if c.cell_type == "code"]
    saved = sum(len(c.outputs) for c in code)
    for c in code:
        c.outputs = []
        c.execution_count = None
    folder = directory / "student"
    (folder / "data").mkdir(parents=True)
    (folder / src.name).write_bytes(source)
    for name in inputs:
        (folder / "data" / Path(name).name).write_bytes(material(root, route, name))
    before = {str(p.relative_to(folder)): sha(p) for p in folder.rglob("*") if p.is_file()}
    if transport == "inprocess":
        saved_runner = root / "reviews/week01-depth-20261118/execute_lesson.py"
        spec = importlib.util.spec_from_file_location("saved_kernel_execution", saved_runner)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        runner.execute_inprocess(nb, folder)
    else:
        manager = KernelManager(kernel_name="python3")
        manager.kernel_spec.argv[0] = sys.executable
        client = NotebookClient(nb, km=manager, timeout=120, allow_errors=False,
                                resources={"metadata": {"path": str(folder)}})
        try:
            client.execute(cwd=str(folder))
        finally:
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
    after = {str(p.relative_to(folder)): sha(p) for p in folder.rglob("*") if p.is_file()}
    if any(c.execution_count is None for c in code):
        raise RuntimeError("Incomplete student code execution")
    figures = []
    for c in code:
        for out in c.outputs:
            if out.output_type == "error":
                raise RuntimeError(f"Unexpected error at {c.id}")
            png = out.get("data", {}).get("image/png")
            if png:
                image = base64.b64decode(png)
                figures.append({"cell": c.id, "width": int.from_bytes(image[16:20], "big"),
                                "height": int.from_bytes(image[20:24], "big"),
                                "sha256": hashlib.sha256(image).hexdigest()})
    if output_cache:
        output_cache.mkdir(parents=True, exist_ok=True)
        by_cell = {c.id: c.outputs for c in code}
        (output_cache / (route["files"][path] + ".json")).write_text(
            json.dumps(by_cell, ensure_ascii=False), encoding="utf-8")
    return {"notebook": path, "sha256": route["files"][path], "saved_outputs_cleared_in_memory": saved,
            "code_cells": len(code), "figures": figures, "status": "executed",
            "changed_student_files": sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k)),
            "data": {name: route["files"][name] for name in inputs}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("route", type=Path)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--transport", choices=("inprocess", "subprocess"), default="subprocess")
    p.add_argument("--outputs", type=Path,
                   help="Save authentic cell displays keyed by the source notebook digest for a blind packet.")
    p.add_argument("--only", metavar="NOTEBOOK")
    args = p.parse_args()
    root = args.root.resolve()
    route = json.loads(args.route.read_text())
    for path in route["files"]:
        material(root, route, path)
    if args.only:
        if args.only not in route["companions"]:
            raise ValueError("Unregistered notebook")
        with tempfile.TemporaryDirectory(prefix="koai-route-run-") as scratch:
            tmp = Path(scratch)
            for key in ("IPYTHONDIR", "JUPYTER_RUNTIME_DIR", "MPLCONFIGDIR", "XDG_CACHE_HOME"):
                os.environ[key] = str(tmp / "runtime" / key.lower())
            os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
            print(json.dumps(one(root, route, args.only, route["companions"][args.only]["data"], tmp, args.transport, args.outputs),
                             ensure_ascii=False))
        return
    results = []
    for path in route["companions"]:
        cmd = [sys.executable, "-B", str(Path(__file__).resolve()), str(args.route.resolve()),
               "--root", str(root), "--transport", args.transport, "--only", path]
        if args.outputs:
            cmd.extend(["--outputs", str(args.outputs.resolve())])
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode:
            results.append({"notebook": path, "status": "error", "detail": res.stderr[-2800:]})
        else:
            results.append(json.loads(res.stdout))
    print(json.dumps({"route_sha256": sha(args.route), "transport": args.transport,
        "versions": {lib: version(lib) for lib in ("numpy","pandas","matplotlib","seaborn","scikit-learn","ipykernel")},
        "notebooks": results}, ensure_ascii=False, indent=2))
    return int(any(row["status"] != "executed" for row in results))


if __name__ == "__main__":
    raise SystemExit(main())
