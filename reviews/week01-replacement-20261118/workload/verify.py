"""Check the cited local bytes, activity rates, and non-overlapping workload scenarios.

Run from any directory with a path to workload/incumbent.json or workload/replacement.json.
This recomputes editorial estimates. It does not measure time spent by learners.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def plus(values):
    items = list(values)
    return [sum(v[0] for v in items), sum(v[1] for v in items)]


def verify(root, ledger):
    categories = ledger["categories"]
    blocks = ledger["home_blocks"] + ledger["conditional_blocks"]
    archival = {}
    if ledger["id"] == "incumbent":
        manifest = json.loads((root / ledger["manifest"]).read_text(encoding="utf-8"))
        if manifest["basis_commit"] != ledger["basis_commit"]:
            raise ValueError("Incumbent basis differs from the frozen manifest")
        archival = manifest["files"]
    for path, digest in ledger["inputs_sha256"].items():
        if path in archival:
            if archival[path] != digest:
                raise ValueError("Historical input differs from the frozen manifest: " + path)
            blob = subprocess.run(
                ["git", "-C", str(root), "cat-file", "blob", ledger["basis_commit"] + ":" + path],
                capture_output=True, check=True,
            ).stdout
        else:
            blob = (root / path).read_bytes()
        if hashlib.sha256(blob).hexdigest() != digest:
            raise ValueError("Source bytes changed: " + path)
    for block in blocks:
        amounts = {}
        for cat in categories:
            amounts[cat] = plus(
                [v * block["atoms"][unit] for v in ledger["unit_rates"][unit].get(cat, [0, 0])]
                for unit in block["atoms"]
            )
        if block["category_minutes"] != amounts or block["minutes"] != plus(amounts.values()):
            raise ValueError("Incorrect block calculation: " + block["id"])
    lookup = {b["id"]: b for b in blocks}
    if len(lookup) != len(blocks):
        raise ValueError("Block identifiers must be unique")
    for block in ledger["class_blocks"]:
        if plus(block["category_minutes_estimate"].values()) != block["minutes"]:
            raise ValueError("Class categorization differs from the block: " + block["id"])
    if plus(b["minutes"] for b in ledger["class_blocks"]) != ledger["totals"]["class_minutes"]:
        raise ValueError("Class schedule differs from its total")
    if plus(b["minutes"] for b in ledger["home_blocks"]) != ledger["totals"]["required_home"]["minutes"]:
        raise ValueError("Required homework differs from its total")
    for scenario in ledger.get("scenarios", []):
        ids = scenario["block_ids"]
        if len(ids) != len(set(ids)) or not set(ids) <= lookup.keys():
            raise ValueError("Overlapping or unknown block in " + scenario["id"])
        if plus(lookup[i]["minutes"] for i in ids) != scenario["minutes"]:
            raise ValueError("Scenario total differs: " + scenario["id"])
    return {"route": ledger["id"], "class_minutes": ledger["totals"]["class_minutes"],
            "core_home_minutes": ledger["totals"]["required_home"]["minutes"],
            "scenarios": {s["id"]: s["minutes"] for s in ledger.get("scenarios", [])},
            "blocks": len(blocks), "source_files": len(ledger["inputs_sha256"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    print(json.dumps(verify(root, json.loads(args.ledger.read_text(encoding="utf-8"))), ensure_ascii=False))
