"""Apply the repository's existing typed cell-diff checks to whole-course revisions."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from material_revision import check_diff, ids, validate_actions
from quality import _pairs


def check(request):
    previous, candidate = request["previous"], request["candidate"]
    old = {**previous["notebooks"], "teacher": previous["teacher"]}
    new = {**candidate["notebooks"], "teacher": candidate["teacher"]}
    known = {name + "/" + c["id"] for name, nb in candidate["notebooks"].items() for c in nb["cells"]}
    retired = candidate.get("retired", {})
    if set(old) - set(new) != set(retired):
        raise ValueError("Explain every retired notebook with its successor in the student path")
    for name, successors in retired.items():
        if not successors or not set(successors) <= known:
            raise ValueError("Missing successor for " + name)
    changed = {name for name in old.keys() & new.keys() if old[name] != new[name]}
    edits = candidate.get("edits", {})
    if changed != set(edits):
        raise ValueError("The edit declaration must match the changed notebooks")
    results = {}
    for name in sorted(changed):
        intent = edits[name]
        if not intent.get("actions") or not intent.get("routes"):
            raise ValueError("Missing actions or successor routes for " + name)
        validate_actions(intent["actions"])
        for reference, route in intent["routes"].items():
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError("Empty route name")
            ids(route.get("before"), "route.before")
            ids(route.get("after"), "route.after", True)
        # All pre-existing student/teacher cells must have a successor if removed.
        protected = {c["id"] for c in old[name]["cells"]}
        if any(not route["after"] for route in intent["routes"].values()):
            raise ValueError("Missing post-edit route")
        results[name] = check_diff(old[name], new[name], intent, protected)
    return {"ok": True, "changes": results}


if __name__ == "__main__":
    try:
        result = check(json.load(sys.stdin, object_pairs_hook=_pairs))
    except (ValueError, TypeError, KeyError, IndexError) as error:
        result = {"ok": False, "reason": str(error)}
    print(json.dumps(result, ensure_ascii=False))
