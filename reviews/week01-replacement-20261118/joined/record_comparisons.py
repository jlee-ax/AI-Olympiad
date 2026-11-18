"""Add reviewed raw source lines from one released notebook to its real discovery session."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import discovery_loop


def cell_ranges(raw):
    decoder = json.JSONDecoder()
    offset = re.search(r'"cells"\s*:\s*\[',raw).end()
    ranges = {}
    while True:
        while raw[offset] in " \t\r\n,":
            offset += 1
        if raw[offset] == "]":
            return ranges
        cell,end = decoder.raw_decode(raw,offset)
        first = raw.count("\n",0,offset)
        last = raw.count("\n",0,end)
        ranges[cell["id"]] = (first,last)
        offset = end


def record(audit):
    path = ROOT / audit["entry"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != audit["notebook_sha256"]:
        raise ValueError("Release notebook has changed")
    raw = path.read_text()
    lines = raw.splitlines()
    ranges = cell_ranges(raw)
    def span(cid,needle):
        first,last = ranges[cid]
        token = json.dumps(needle,ensure_ascii=False)[1:-1]
        chosen = [i+1 for i in range(first,last+1) if token in lines[i]]
        if len(chosen)!=1:
            raise ValueError("Need one precise current source line: "+cid+" / "+needle)
        return dict(start_line=chosen[0],end_line=chosen[0])
    output=HERE/"discovery.json"
    state=discovery_loop.load(output if output.exists() else HERE/"discovery-seed.json")
    existing={e["id"]:e for e in state["events"]}
    for tid,unit in audit["units"].items():
        eid=f"r{audit['round']}-{tid}"
        if eid in existing:
            old=existing[eid]["data"]
            if old["lesson_receipt"]["sha256"]!=audit["notebook_sha256"] or old["rationale"]!=unit["discovery_summary"]:
                raise ValueError("Existing review differs for "+eid)
            continue
        dims=[]
        for dimension,details in unit["discovery_dimensions"].items():
            cid,needle,judgment,observation=details
            dims.append({"id":dimension,"judgment":judgment,"observed_behavior":observation,
                         "rationale":unit["discovery_summary"],**span(cid,needle)})
        grade="gap" if any(d["judgment"]=="gap" for d in dims) else "uncertain" if any(d["judgment"]=="uncertain" for d in dims) else "covered"
        first=unit["discovery_dimensions"]["assessment"]
        data={"reason":"Direct reading of all student-route material and exact teacher response; the entry span anchors the discovery requirement and the joined graph binds the actual additional panes.",
              "demand_id":tid,"reviewer":audit["reviewer"],"rationale":unit["discovery_summary"],
              "judgment":grade,**span(first[0],first[1]),"dimensions":dims}
        if audit.get("minutes_elapsed") is not None and tid == next(iter(audit["units"])):
            elapsed = sum(e["data"].get("minutes", 0) for e in state["events"])
            data["minutes"] = max(0, audit["minutes_elapsed"] - elapsed)
        state=discovery_loop.step(state,{"id":eid,"op":"compare","data":data},ROOT)
    output.write_text(json.dumps(state,ensure_ascii=False,indent=1)+"\n")
    report=discovery_loop.inspect(state,ROOT)
    print(report["status"],{c["demand_id"]:c["judgment"] for c in report["comparisons"]})


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit",type=Path)
    record(json.loads(parser.parse_args().audit.read_text()))
