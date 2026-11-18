"""Run the archived Week 1 input through the repository's public verification commands."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import replay


def run():
    audit = replay.read(replay.HERE / "audit.json")
    bundles, quality = replay.build(audit)
    summary = replay.summarize(audit, bundles, quality)
    tool_names = ("quality", "workflow", "contest_depth", "discovery_loop", "graph_paths",
                  "validate", "topic_depth", "lesson_route", "review_preflight")
    source_hashes = {name: replay.file_hash("tools/" + name + ".py") for name in tool_names}
    checks = {}
    with tempfile.TemporaryDirectory(prefix=".joined-native-", dir=replay.ROOT / replay.HERE) as tmp:
        out = Path(tmp).relative_to(replay.ROOT)
        for name, data in bundles.items():
            (replay.ROOT / out / (name + ".json")).write_text(json.dumps(data, ensure_ascii=False))
        def native(filename):
            return str(out / (filename + ".json"))
        def check(name, tool, arguments, *, plain=False):
            cmd = [sys.executable, "-B", "tools/" + tool + ".py", *arguments]
            proc = subprocess.run(cmd, cwd=replay.ROOT, capture_output=True, text=True, check=False)
            if proc.stderr.strip():
                raise RuntimeError(name + ": " + proc.stderr.strip())
            if plain:
                report = {"status": proc.stdout.strip()}
            else:
                report = json.loads(proc.stdout)
            if report.get("errors") or proc.returncode > 1:
                raise RuntimeError(name + ": " + str(report.get("errors", proc.returncode)))
            record = {"command": ["python", "-B", *[a.replace(str(out) + "/", "<native>/") for a in cmd[2:]]],
                      "exit": proc.returncode, "status": report["status"]}
            for key in ("reason", "ready_for_review", "ready", "budget"):
                if key in report:
                    record[key] = report[key]
            checks[name] = record
            return report
        graph, paths, semantics = native("graph"), native("paths"), native("semantic-review")
        depth, quality_file, state = native("contest-depth"), native("quality"), native("workflow")
        discovery = str(replay.HERE / "discovery.json")
        check("route", "lesson_route", ["inspect", "--root", ".", "--route", audit["route"]])
        check("registered_depth", "topic_depth", ["check", "--root", ".", "--case", str(replay.CASE)])
        check("discovery", "discovery_loop", ["report", discovery, "--root", "."])
        check("contest", "contest_depth", [depth])
        check("structure", "validate", [graph], plain=True)
        graph_args = [graph, "--spec", paths, "--root", "."]
        check("declared_paths", "graph_paths", graph_args)
        check("semantic_paths", "graph_paths", [*graph_args, "--semantic-review", semantics])
        actual_quality = check("quality", "quality", ["evaluate", quality_file, "--root", "."])
        actual_checks = {row["id"]: row["status"] for row in actual_quality["checks"]}
        if actual_checks != summary["quality"]["criterion_status"]:
            raise RuntimeError("Native quality results differ from the recorded criteria")
        check("plan", "quality", ["plan", quality_file, "--root", "."])
        check("workflow_state", "workflow", ["validate", state])
        check("workflow", "workflow", ["decide", state, "--root", ".", "--quality", quality_file,
                                       "--discovery", discovery])
        preflight = check("preflight", "review_preflight", ["--root", ".", "--depth", depth, "--graph", graph,
            "--paths", paths, "--semantic-review", semantics, "--state", state, "--quality", quality_file,
            "--discovery", discovery])
        if preflight["blockers"] != summary["preflight"]["blockers"]:
            raise RuntimeError("Native preflight returned a different set of blockers")
    summary["native_commands"] = checks
    summary["source_sha256"] = source_hashes
    return summary


if __name__ == "__main__":
    report = run()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(report["native_commands"]["preflight"]["exit"])
