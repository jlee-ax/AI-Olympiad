"""Re-run the repository's read-only CLIs on the saved Week 1 production records."""
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent.relative_to(ROOT)


def local(name):
    return str(HERE / name)


def command(tool, *args):
    return [sys.executable, "-B", "tools/" + tool + ".py", *args]


def run(label, argv):
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True)
    try:
        data = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        data = {"output": completed.stdout.decode(errors="replace").strip()}
    item = {
        "command": shlex.join(["python3", *argv[1:]]),
        "exit": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
    }
    for key in ("status", "reason", "ready_for_review", "synthetic", "errors", "warnings", "output"):
        if key in data:
            item[key] = data[key]
    if completed.stderr:
        item["stderr"] = completed.stderr.decode(errors="replace").strip()
    if label == "topic_depth":
        for key in ("ready", "subject_round", "subject_sha256", "freeze_commit", "manifest"):
            if key in data:
                item[key] = data[key]
    elif label == "discovery":
        item.update(demands=[d["id"] for d in data["demands"]],
                    comparisons={c["demand_id"]: c["judgment"] for c in data["comparisons"]},
                    queue=data["queue"], blockers=data["blockers"], usage=data["usage"])
    elif label == "depth":
        item.update(comparisons=data["comparisons"], assessment_formats=data["assessment_formats"],
                    findings=data["findings"], gaps=data["gaps"], outside_material_scope=data["outside_material_scope"])
    elif label == "paths":
        item["bindings"] = len(data.get("bindings", []))
        item["findings"] = data.get("findings", [])
    elif label == "semantic":
        item["mechanical_status"] = data.get("mechanical_status")
        item["bindings"] = len(data.get("bindings", []))
        item["comparisons"] = len(data.get("comparisons", []))
        item["findings"] = data.get("findings", [])
    elif label == "quality" and "checks" in data:
        item["checks"] = {c["id"]: c["status"] for c in data["checks"]}
        item["findings"] = [{k:v for k,v in f.items() if k in ("criterion_id","status","affected_objects","priority")} for f in data["findings"]]
        item["topic_depth"] = {k:v for k,v in data.get("topic_depth", {}).items() if k in ("status", "ready", "errors", "freeze_commit", "subject_round", "subject_sha256", "manifest")}
    elif label == "plan":
        for key in ("next_candidate", "next_action", "next_discovery_action"):
            if key in data:
                item[key] = data[key]
    elif label == "recall":
        item["active_record_ids"] = [rec["id"] for rec in data.get("records", [])]
    elif label == "preflight":
        item["blockers"] = data.get("blockers", [])
        item["local_bindings"] = len(data.get("bindings", []))
        item["unmatched_bindings"] = [b for b in data.get("bindings", []) if not b["matched"]]
        item["unverified_sources"] = data.get("unverified_sources", [])
        item["scope"] = data.get("review_scope")
        item["workflow"] = {k:data.get("workflow", {}).get(k) for k in ("status", "reason")}
    return item


def historical_comparisons():
    session = json.loads((ROOT / HERE / "discovery.json").read_text())
    rounds = ROOT / HERE.parent / "rounds"
    report = []
    for event in session["events"]:
        if event["op"] != "compare":
            continue
        number = int(event["id"].split("-", 1)[0][1:])
        archive = (rounds / f"{number:04}" / "candidate.ipynb").read_bytes()
        lines = archive.decode("utf-8").splitlines(keepends=True)
        digest = hashlib.sha256(archive).hexdigest()
        data = event["data"]
        spans = [data["lesson_receipt"], *(d["receipt"] for d in data["dimensions"])]
        matched = True
        for span in spans:
            excerpt = "".join(lines[span["start_line"] - 1:span["end_line"]])
            matched &= (span["sha256"] == digest and span["excerpt"] == excerpt
                        and span["excerpt_sha256"] == hashlib.sha256(excerpt.encode()).hexdigest())
        report.append({"event": event["id"], "judgment": data["judgment"],
                       "spans": len(spans), "archived_bytes_match": matched})
    return {"exit": int(not all(r["archived_bytes_match"] for r in report)),
            "status": "matched" if all(r["archived_bytes_match"] for r in report) else "stale",
            "comparisons": len(report), "spans": sum(r["spans"] for r in report), "events": report}


def main():
    root = ["--root", "."]
    graph = local("graph.json")
    paths = ["--spec", local("paths.json")]
    sem = ["--semantic-review", local("semantic-review.json")]
    qual = local("quality.json")
    state = local("workflow.json")
    discovery = local("discovery.json")
    depth = local("contest-depth.json")
    inputs = ["--quality", qual, "--discovery", discovery, *root]
    checks = {
        "topic_depth": command("topic_depth", "check", "--case", str(HERE.parent), *root),
        "discovery": command("discovery_loop", "report", discovery, *root),
        "depth": command("contest_depth", depth),
        "structure": command("validate", graph),
        "paths": command("graph_paths", graph, *paths, *root),
        "semantic": command("graph_paths", graph, *paths, *sem, *root),
        "quality": command("quality", "evaluate", qual, *root),
        "plan": command("quality", "plan", qual, *root),
        "workflow_validation": command("workflow", "validate", state),
        "recall": command("workflow", "recall", state),
        "decision": command("workflow", "decide", state, *inputs),
        "preflight": command("review_preflight", "--depth", depth, "--graph", graph,
                             "--paths", local("paths.json"), *sem, "--state", state, *inputs),
    }
    rows = {label: run(label, argv) for label, argv in checks.items()}
    rows["archived_comparisons"] = historical_comparisons()
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return max(row["exit"] for row in rows.values())


if __name__ == "__main__":
    sys.exit(main())
