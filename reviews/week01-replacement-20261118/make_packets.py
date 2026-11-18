"""Export complete student routes to neutrally named text packets kept separate from keys."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def export_route(root, route, target):
    target.mkdir(parents=True, exist_ok=False)
    files = route["files"]
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
        if digest(source) != files[path]:
            raise ValueError(f"Stale student copy: {path}")
        notebook = load(source)
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
            else:
                lines.append(body)
        (target / alias).write_text("".join(lines).lstrip() + "\n", encoding="utf-8")
        all_ids[alias] = seen
        raw_digests[alias] = digest(source)
    schedule = []
    for u in route["units"]:
        doc = notebook_names[u["path"]]
        if not set(u["cells"]) <= all_ids[doc]:
            raise ValueError(f"Unknown cell in {u['id']}")
        row = {"unit": u["id"], "document": doc, "cells": u["cells"], "status": u["status"], "when": u["reason"]}
        for k in ("class_minutes", "homework_minutes"):
            if k in u:
                row[k] = u[k]
        schedule.append(row)
    # Include only registered student input files, never companion answer keys or teacher notes.
    public_data = set()
    for row in route["companions"].values():
        public_data.update(row["data"])
    for path in sorted(public_data):
        source = root / path
        if digest(source) != files[path]:
            raise ValueError(f"Stale data: {path}")
        dest = target / "data" / source.name
        dest.parent.mkdir(exist_ok=True)
        if dest.exists() and dest.read_bytes() != source.read_bytes():
            raise ValueError(f"Colliding data filename: {source.name}")
        shutil.copyfile(source, dest)
    for path in sorted(delayed):
        source = root / path
        if digest(source) != files[path]:
            raise ValueError(f"Stale self-check: {path}")
        destination = target / "after-attempt" / source.name
        destination.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, destination)
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
    args = p.parse_args()
    assignment = load(args.assignment)
    routes = {"candidate": load(args.candidate), "incumbent": load(args.incumbent)}
    if set(assignment[k] for k in ("P", "Q")) != set(routes):
        raise ValueError("Both routes must occur once")
    args.destination.mkdir(parents=True, exist_ok=False)
    result = {k: export_route(args.root, routes[assignment[k]], args.destination / k) for k in ("P", "Q")}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
