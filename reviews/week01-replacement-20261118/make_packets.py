"""Export complete student routes to neutrally named text packets kept separate from keys."""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path

from comparison_material import material


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def pack_displays(outputs, target, alias, cell_id):
    """Keep executed displays separate so an attempted exercise can precede its output."""
    lines = []
    for index, output in enumerate(outputs, 1):
        data = output.get("data", {})
        value = output.get("text", data.get("text/plain"))
        if isinstance(value, list):
            value = "".join(value)
        if value:
            lines.extend(["\n```text\n", value.rstrip(), "\n```\n"])
        if "image/png" in data:
            png = base64.b64decode(data["image/png"], validate=True)
            relative = Path("outputs") / Path(alias).stem / f"{cell_id}-{index}.png"
            dest = target / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(png)
            lines.append(f"\n![실행한 그림]({relative.as_posix()})\n")
    if lines:
        return ["\n<details><summary>실행 후 출력</summary>\n", *lines, "\n</details>\n"]
    return []


def export_route(root, route, target, output_cache):
    target.mkdir(parents=True, exist_ok=False)
    student_paths = [route["entry"]]
    for unit in route["units"]:
        if unit["path"] not in student_paths:
            student_paths.append(unit["path"])
    notebook_names = {p: f"document-{i:02}.md" for i, p in enumerate(student_paths, 1)}
    replacements = {Path(p).name: name for p, name in notebook_names.items()}
    delayed = set()
    for companion in route["companions"].values():
        delayed.update(companion.get("after_attempt", []))
    for path in delayed:
        replacements[Path(path).name] = "after-attempt/" + Path(path).name
    raw_digests = {}
    all_ids = {}
    for path, alias in notebook_names.items():
        source = root / path
        raw = material(root, route, path)
        notebook = json.loads(raw)
        displays = load(output_cache / (route["files"][path] + ".json"))
        code_ids = {c["id"] for c in notebook["cells"] if c["cell_type"] == "code"}
        if set(displays) != code_ids:
            raise ValueError(f"Executed displays do not match {alias}")
        lines = []
        seen = set()
        for cell in notebook["cells"]:
            cid = cell["id"]
            if cid in seen:
                raise ValueError(f"Repeated cell id: {source} {cid}")
            seen.add(cid)
            body = cell["source"]
            body = body if isinstance(body, str) else "".join(body)
            for basename, neutral in replacements.items():
                # Local unversioned paths are relative to the original notebook directory.
                body = body.replace(basename, neutral)
            body = re.sub(r"https://github\.com/jlee-ax/AI-Olympiad/(?:blob|tree)/[^)\s\"<>]+",
                          "[course repository reference]", body)
            lines.append(f"\n\n<!-- cell {cid} | {cell['cell_type']} -->\n")
            if cell["cell_type"] == "code":
                lines.extend(["\n" + chr(96)*3 + "python\n", body, "\n" + chr(96)*3 + "\n"])
                lines.extend(pack_displays(displays[cid], target, alias, cid))
            else:
                lines.append(body)
        (target / alias).write_text("".join(lines).lstrip() + "\n", encoding="utf-8")
        all_ids[alias] = seen
        raw_digests[alias] = hashlib.sha256(raw).hexdigest()
    schedule = []
    for u in route["units"]:
        doc = notebook_names[u["path"]]
        if not set(u["cells"]) <= all_ids[doc]:
            raise ValueError(f"Unknown cell in {u['id']}")
        row = {"unit": u["id"], "document": doc, "cells": u["cells"], "status": u["status"], "when": u["reason"]}
        for k in ("class_minutes", "homework_minutes", "class_range", "homework_range"):
            if k in u:
                row[k] = u[k]
        schedule.append(row)
    # Include only registered student input files, never companion answer keys or teacher notes.
    public_data = set()
    for row in route["companions"].values():
        public_data.update(row["data"])
    for path in sorted(public_data):
        source = root / path
        raw = material(root, route, path)
        dest = target / "data" / source.name
        dest.parent.mkdir(exist_ok=True)
        if dest.exists() and dest.read_bytes() != raw:
            raise ValueError(f"Colliding data filename: {source.name}")
        dest.write_bytes(raw)
    for path in sorted(delayed):
        source = root / path
        raw = material(root, route, path)
        destination = target / "after-attempt" / source.name
        destination.parent.mkdir(exist_ok=True)
        destination.write_bytes(raw)
    (target / "route.json").write_text(json.dumps({"entry": notebook_names[route["entry"]],
        "units": schedule, "timing": route.get("timing", "See the registered planned estimates.")},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"source_sha256": raw_digests,
            "packet_sha256": {str(p.relative_to(target)): digest(p) for p in sorted(target.rglob("*")) if p.is_file()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("candidate", type=Path)
    p.add_argument("incumbent", type=Path)
    p.add_argument("assignment", type=Path)
    p.add_argument("destination", type=Path)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--outputs", type=Path, required=True, help="Cell displays from run_route.py --outputs")
    args = p.parse_args()
    assignment = load(args.assignment)
    routes = {"candidate": load(args.candidate), "incumbent": load(args.incumbent)}
    if set(assignment[k] for k in ("P", "Q")) != set(routes):
        raise ValueError("Both routes must occur once")
    args.destination.mkdir(parents=True, exist_ok=False)
    result = {k: export_route(args.root, routes[assignment[k]], args.destination / k, args.outputs) for k in ("P", "Q")}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
