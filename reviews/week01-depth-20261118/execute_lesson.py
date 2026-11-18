"""Run an unmodified student notebook in a fresh Jupyter kernel with just its CSVs.

Use a Python environment with nbclient, nbformat, nbconvert, ipykernel, NumPy,
pandas, Matplotlib and Seaborn. The report records content execution, not answers
written by students. Generated HTML and PNGs go to --render-dir if requested.
"""
import argparse
import base64
import hashlib
import json
import os
from contextlib import chdir
from pathlib import Path
import shutil
import sys
import tempfile

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from jupyter_client import KernelManager


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute_inprocess(notebook, folder):
    """Use the Jupyter execute protocol when the host cannot bind a kernel socket."""
    from ipykernel.inprocess.manager import InProcessKernelManager

    from traitlets.config import Config
    config = Config()
    config.HistoryManager.hist_file = ":memory:"
    manager = InProcessKernelManager(config=config)
    manager.start_kernel()
    channel = manager.client()
    channel.start_channels()
    try:
        with chdir(folder):
            for cell in [nbformat.v4.new_code_cell("%matplotlib inline"), *notebook.cells]:
                if cell.cell_type != "code":
                    continue
                mid = channel.execute(cell.source, allow_stdin=False)
                reply = channel.shell_channel.get_msg(timeout=90)
                if reply["parent_header"]["msg_id"] != mid or reply["content"]["status"] != "ok":
                    raise RuntimeError(f"{cell.id}: {reply['content']}")
                cell.execution_count = reply["content"]["execution_count"]
                while True:
                    msg = channel.iopub_channel.get_msg(timeout=20)
                    kind, body = msg["msg_type"], msg["content"]
                    parent = msg["parent_header"].get("msg_id")
                    # Some in-process kernel versions emit unparented streams.
                    # Only one request is outstanding until its own idle message.
                    if parent != mid and not (kind == "stream" and parent is None):
                        continue
                    if kind == "status" and body["execution_state"] == "idle":
                        break
                    if kind in {"stream", "display_data", "execute_result", "error"}:
                        cell.outputs.append(nbformat.v4.output_from_msg(msg))
                    if kind == "error":
                        raise RuntimeError(f"{cell.id}: {body}")
    finally:
        channel.stop_channels()
        manager.shutdown_kernel()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path)
    parser.add_argument("--transport", choices=("subprocess","inprocess"), default="subprocess")
    args = parser.parse_args()
    nb = nbformat.read(args.notebook, as_version=4)
    nbformat.validate(nb)
    if any(c.outputs or c.execution_count is not None for c in nb.cells if c.cell_type == "code"):
        raise ValueError("Student copy contains saved results")
    contract = json.loads((Path(__file__).parent / "contract.json").read_text())
    files = [args.data / Path(p).name for p in contract["companion_paths"] if p.endswith(".csv")]
    with tempfile.TemporaryDirectory(prefix="koai-student-") as student:
        folder = Path(student)
        (folder / "data").mkdir()
        for path in files:
            shutil.copyfile(path, folder / "data" / path.name)
        shutil.copyfile(args.notebook, folder / args.notebook.name)
        if args.transport == "inprocess":
            execute_inprocess(nb, folder)
        else:
            manager = KernelManager(kernel_name="python3")
            manager.kernel_spec.argv[0] = sys.executable
            client = NotebookClient(nb, km=manager, timeout=90, allow_errors=False,
                                    resources={"metadata":{"path": str(folder)}})
            try:
                client.execute(cwd=str(folder))
            finally:
                if manager.has_kernel:
                    manager.shutdown_kernel(now=True)
        leftover = sorted(str(p.relative_to(folder)) for p in folder.rglob("*")
                          if p.is_file() and p.name != args.notebook.name
                          and p not in {folder / "data" / data.name for data in files})
    cells = [c for c in nb.cells if c.cell_type == "code"]
    if any(c.execution_count is None for c in cells):
        raise ValueError("Some code cells did not run")
    figures = []
    if args.render_dir:
        args.render_dir.mkdir(parents=True, exist_ok=True)
    for cell in cells:
        for output in cell.outputs:
            png = output.get("data", {}).get("image/png")
            if png:
                data = base64.b64decode(png, validate=False)
                if data[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError("Invalid PNG")
                name = f"{cell.id}-{len(figures)+1}.png"
                if args.render_dir:
                    (args.render_dir / name).write_bytes(data)
                figures.append({"cell": cell.id, "file": name, "width": int.from_bytes(data[16:20], "big"),
                                "height": int.from_bytes(data[20:24], "big")})
    if len({f["cell"] for f in figures}) < 2:
        raise ValueError("Expected independent plotted activities")
    if args.render_dir:
        html, _ = HTMLExporter().from_notebook_node(nb)
        (args.render_dir / "lesson.html").write_text(html, encoding="utf-8")
    from importlib.metadata import version
    report = {"notebook_sha256":digest(args.notebook), "status":"passed",
              "transport":args.transport, "runtime":{p:version(p) for p in ("ipykernel","nbclient","numpy","pandas","matplotlib","seaborn")},
              "csv_sha256":{p.name:digest(p) for p in files}, "code_cells":[c.id for c in cells],
              "figures":figures, "other_files_created":leftover,
              "execution":"fresh kernel; sandbox contains only the notebook and registered CSV files"}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{len(cells)} executed code cells; {len(figures)} rendered figures; {report['notebook_sha256']}")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="koai-kernel-") as runtime_dir:
        for key in ("MPLCONFIGDIR","IPYTHONDIR","JUPYTER_RUNTIME_DIR","XDG_CACHE_HOME"):
            os.environ[key] = str(Path(runtime_dir) / key)
        main()
