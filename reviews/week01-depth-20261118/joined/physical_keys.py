"""Replay public teacher-key joins on physically serialized identifiers from one archived round."""
import argparse
import ast
import csv
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
CASE = HERE.parent
ROOT = HERE.parents[2]


def archive_inputs(round_id):
    manifest = json.loads((CASE / "rounds" / round_id / "round.json").read_text())
    result = {}
    for entry in manifest["companions"]:
        path = ROOT / entry["snapshot"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Snapshot is stale: {path.name}")
        result[path.name] = path
    return manifest, result


def key_function(path):
    namespace = {"pd": pd}
    for block in re.findall(r"^```python\s*\n(.*?)^```\s*$", path.read_text(), re.M | re.S):
        definitions = [node for node in ast.parse(block).body if isinstance(node, ast.FunctionDef)]
        if definitions:
            module = ast.Module(body=definitions, type_ignores=[])
            exec(compile(module, str(path), "exec"), namespace)
    return namespace["attach_zones"]


def read_original(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def physical(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return pd.read_csv(path)


def main(round_id):
    manifest, files = archive_inputs(round_id)
    attach = key_function(files["week01_foundations_teacher.md"])
    original = read_original(files["foundations_returns_transfer.csv"])
    lookup = read_original(files["foundations_boxes.csv"])
    result = []
    with tempfile.TemporaryDirectory(prefix="join-test-", dir=HERE) as temp:
        directory = Path(temp)
        for name in ("all left CSV keys missing", "all right CSV keys missing",
                     "both CSV key columns missing", "paired empty textual key plus unknown", "both tables normal"):
            left = [dict(r) for r in original]
            right = [dict(r) for r in lookup]
            if name in ("all left CSV keys missing", "both CSV key columns missing"):
                for item in left:
                    item["station"] = ""
            if name in ("all right CSV keys missing", "both CSV key columns missing"):
                for item in right:
                    item["box_id"] = ""
            body = physical(directory / "observations.csv", left)
            locations = physical(directory / "lookup.csv", right)
            expected = [] if name == "both tables normal" else body["slip"].tolist()
            if name == "paired empty textual key plus unknown":
                body.loc[body["slip"] == "T1", "station"] = ""
                body.loc[body["slip"] == "T2", "station"] = "UNKNOWN"
                locations = pd.concat([locations, pd.DataFrame({"box_id": [""], "zone": ["invented"]})])
                expected = ["T1", "T2"]
            ids = None
            failure = None
            try:
                attached = attach(body, locations)
            except ValueError as exc:
                if len(exc.args) > 1 and isinstance(exc.args[1], list):
                    ids = exc.args[1]
                failure = str(exc)
            else:
                if len(attached) == len(body) and attached["slip"].tolist() == body["slip"].tolist():
                    ids = []
            row = {"case": name, "left_dtype": str(body["station"].dtype),
                   "right_dtype": str(locations["box_id"].dtype), "expected_unmatched": expected,
                   "reported_unmatched": ids, "error": failure, "passed": ids == expected}
            result.append(row)
    return {"round": round_id, "notebook_sha256": manifest["candidate_sha256"], "pandas": pd.__version__,
            "records": result, "passed": all(r["passed"] for r in result)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round")
    report = main(parser.parse_args().round)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["passed"] else 1)
