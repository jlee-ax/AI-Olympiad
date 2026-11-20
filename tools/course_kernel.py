"""Execute the generated student notebooks and the independent numeric probes.

Run in an isolated worker containing Jupyter, a Python kernel and the public
course dependencies. The controller sends inputs only; expected answers remain
outside this process. Stdout is reserved for one JSON response.
"""
import copy
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def execute_notebook(notebook, directory):
    nb = nbformat.from_dict(copy.deepcopy(notebook))
    nbformat.validate(nb)
    client = NotebookClient(
        nb, kernel_name="python3", timeout=int(os.environ.get("COURSE_CELL_TIMEOUT", "90")),
        allow_errors=False, resources={"metadata": {"path": str(directory)}},
    )
    client.execute(cwd=str(directory))
    return nb


def main(request):
    outputs = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for index, nb in enumerate(request["notebooks"].values()):
            directory = root / ("student-" + str(index))
            directory.mkdir()
            execute_notebook(nb, directory)
        for index, (name, probe) in enumerate(request["probes"].items()):
            function = probe["entrypoint"]
            if not function.isascii() or not function.isidentifier():
                raise ValueError("Invalid assessment function")
            directory = root / ("probe-" + str(index))
            directory.mkdir()
            nb = nbformat.from_dict(copy.deepcopy(request["teacher"]))
            marker = "COURSE_RESULT_" + uuid.uuid4().hex
            data = json.dumps(probe["inputs"], allow_nan=False, ensure_ascii=True)
            code = (
                "import json as _course_json\n"
                f"_course_in = _course_json.loads({data!r})\n"
                f"_course_out = [{function}(v) for v in _course_in]\n"
                f"print({marker!r} + _course_json.dumps(_course_out, allow_nan=False))"
            )
            nb.cells.append(nbformat.v4.new_code_cell(code))
            result = execute_notebook(nb, directory)
            text = "".join(o.get("text", "") for o in result.cells[-1].outputs if o.output_type == "stream")
            lines = [line[len(marker):] for line in text.splitlines() if line.startswith(marker)]
            if len(lines) != 1:
                raise ValueError("No unique probe output")
            outputs[name] = json.loads(lines[0])
    return {"ok": True, "output": outputs}


if __name__ == "__main__":
    try:
        result = main(json.load(sys.stdin))
    except Exception as exc:
        result = {"ok": False, "diagnostic": type(exc).__name__}
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
