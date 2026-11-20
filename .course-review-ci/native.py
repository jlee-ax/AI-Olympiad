"""Exercise the repository's native controller against the approved, exact materials."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path.cwd()
CI = ROOT / ".course-review-ci"
OLD = "e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352"
REVIEWS = "reviews/week01-whole-20261120"
sys.path.insert(0,str(CI))
sys.path.insert(0,str(ROOT / "lessons/week01"))
import validate_bundle as bundle
from examiner import design
from blind_solver import solve

def load(p):
    return json.loads(Path(p).read_bytes())

def sha(value):
    if isinstance(value, Path):
        value = value.read_bytes()
    return hashlib.sha256(value).hexdigest()

def packed(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)).encode()

def write(path, value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")

def export(label, raw):
    # The caller permits exactly these public documents. Never export a suite, notebook, role request, ledger or answer.
    if label not in {"candidate-packet.json","native-textbook-review.json","lesson-manifest.json","bundle-checkpoint.json"}:
        raise ValueError("Unregistered public evidence")
    stream = base64.b64encode(raw).decode()
    print("COURSE_PUBLIC_BEGIN",label,len(raw),sha(raw),flush=True)
    for position in range(0,len(stream),3000):
        print("COURSE_PUBLIC_DATA",label,position//3000,stream[position:position+3000],flush=True)
    print("COURSE_PUBLIC_END",label,flush=True)

def main():
    phase = sys.argv[1]
    if phase == "seal":
        from seal import seal
        for label,raw in seal():export(label,raw)
        return
    with tempfile.TemporaryDirectory(prefix="course-independent-") as folder:
        ext=Path(folder)
        subprocess.run(["node",str(CI/"assemble.mjs"),str(ext)],check=True)
        packet=load(ext/"packet.json")
        # This inspection packet contains the public teaching material IDs, scope evidence and hashes only.
        if phase == "prepare":
            export("candidate-packet.json",(ext/"packet.json").read_bytes())
            return
        if phase!="run":raise ValueError("Unknown evidence phase")
        actual = load(ext/"candidate.json")
        original = load(ext/"original.json")
        approvals = load(CI/"author-approval.json")
        review = load(CI/"reviewer.json")
        for name in ("original_candidate_sha256","candidate_sha256","historical_route_sha256"):
            assert approvals[name]==packet[name],name
        assert review["candidate_hash"]==packet["candidate_sha256"]
        assert review["reviewer"]=="week1-independent-curriculum-reader"
        assert set(review["checks"])==set(packet["review_keys"])
        initial = load(CI/"ground.json")
        calls = []
        failures = []
        revisions = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                try:
                    if self.path!="/api/chat":raise ValueError("Unexpected transport path")
                    size=int(self.headers["Content-Length"])
                    assert 0<size<24*1024*1024
                    wire=json.loads(self.rfile.read(size))
                    req=json.loads(wire["messages"][-1]["content"])
                    role=req["role"]
                    if role=="examiner":
                        assert not calls
                        answer=design()
                        assert set(answer["probes"])==set(req["required"])
                    elif role=="assessor":
                        assert [x["role"] for x in calls]==["examiner"]
                        assert all(set(q)=={"entrypoint","spec","inputs"} for q in req["questions"].values())
                        answer={"verdict":"pass","finding":"Independent solver evaluated only the four given public functions and fresh inputs. Its origin is hash-bound in this receipt; the native controller compares answers against separately constructed keys.","answers":solve(req["questions"])}
                    elif role=="ground":
                        assert "candidate" not in req and "previous" not in req
                        answer=initial
                    elif role=="author":
                        assert all(set(p)=={"spec","entrypoint"} for p in req["public_probes"].values())
                        if not revisions:
                            assert req["feedback"] is None
                            answer=original
                        else:
                            assert len(revisions)==1 and req["feedback"], "Corrected submission must follow a real refusal"
                            answer=actual
                        revisions.append(req["feedback"])
                    elif role=="reviewer":
                        assert len(revisions)==2 and req["candidate_hash"]==review["candidate_hash"]
                        assert set(req["required_checks"])==set(review["checks"])
                        answer=review
                    else:raise ValueError("Unexpected curriculum role")
                    calls.append({"role":role,"worker_id":req["worker_id"],"request_sha256":sha(packed(req)),"response_sha256":sha(packed(answer))})
                    output=json.dumps({"model":wire["model"],"done":True,"message":{"content":json.dumps(answer,ensure_ascii=False)}}).encode()
                    self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(output)));self.end_headers();self.wfile.write(output)
                except Exception as error:
                    failures.append((type(error).__name__,role if "role" in locals() else "unknown"))
                    self.send_error(400,"Invalid bound request")
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        config={"profile":"development","auto_assess":True,"author":"week1-curriculum-author","reviewer":review["reviewer"],"examiner":"week1-independent-prerequisite-examiner","python":sys.executable,"author_model":"external-author-response","reviewer_model":"external-independent-reader-response","examiner_model":"independent-parameterized-examiner","endpoint":f"http://127.0.0.1:{server.server_port}/api/chat"}
        write(ext/"runtime.json",config)
        background=threading.Thread(target=server.serve_forever,daemon=True);background.start()
        def command(cmd):
            args=["node","tools/course.mjs",cmd,"--week","1","--baseline",str(ext/"old-manifest.json"),"--suite",str(ext/"suite.json"),"--runtime",str(ext/"runtime.json"),"--state",str(ext/"state.sqlite"),"--calls","12","--attempts","2"]
            proc=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            if proc.returncode:
                try:
                    summary=json.loads(proc.stdout)
                    safe={"completed":summary.get("completed"),"phase":summary.get("reasons")}
                    print("Controller result",json.dumps(safe),flush=True)
                except ValueError:pass
                if failures:print("Worker failure types",failures,flush=True)
                print("Controller diagnostics",proc.stderr.strip()[:1200])
                raise RuntimeError("Native controller did not complete "+cmd)
            return json.loads(proc.stdout)
        try:
            run=command("run");resume=command("resume");status=command("status")
        finally:
            server.shutdown();server.server_close();background.join(timeout=5)
        assert run["completed"]==resume["completed"]==status["completed"]==[1] and resume["calls"]==status["calls"]==0
        assert [x["role"] for x in calls]==["examiner","assessor","ground","author","author","reviewer"], [x["role"] for x in calls]
        assert not failures
        suite=load(ext/"suite.json")["1"];db=sqlite3.connect(ext/"state.sqlite")
        events=[(i,key,json.loads(raw)) for i,key,raw in db.execute("select id,key,entry from events order by id")]
        assert [r["kind"] for _,_,r in events]==["grounded","invalid_candidate","authored","executed","accepted"],[r["kind"] for _,_,r in events]
        phases=[];totals={}
        for i,ctx,row in events:
            kind=row["kind"]
            record={"id":i,"native_context_sha256":ctx,"attempt":row["attempt"],"kind":kind}
            if "hash" in row:record["candidate_sha256"]=row["hash"]
            if kind=="invalid_candidate":
                record["candidate_sha256"]=packet["original_candidate_sha256"]
                record["reason"]=row["reason"]
                assert record["reason"] == packet["historical_refusal"]
                findings = row["tool_prerequisites"]["blocked"]
                assert findings and all(item["tier"] in {"class","homework"} for item in findings)
                record["blocked_tool_findings"] = findings
            if kind=="grounded":record["demands"]=row["demands"]
            if kind=="executed":
                totals={k:{"passed":sum(r["passed"] for r in v["rows"]),"total":len(v["rows"])} for k,v in row["checks"].items()}
                assert all(n["total"]==n["passed"] and n["total"]>=3 for n in totals.values())
                record["probes"]=totals
            if kind=="accepted":
                record.update(verdict=row["review"]["verdict"],review_checks={k:v["verdict"] for k,v in row["review"]["checks"].items()})
                assert record["review_checks"]["tool_prerequisites"]=="pass"
            phases.append(record)
        assert phases[-1]["candidate_sha256"]==packet["candidate_sha256"]
        diffrows=[json.loads(response) for call_id,response in db.execute("select id,response from calls") if call_id.endswith("/diff")]
        assert len(diffrows)==1 and diffrows[0]["ok"]
        db.close()
        manifest=load(ROOT/bundle.MANIFEST)["current_release"]
        for role,member in manifest["members"].items():
            p=ROOT/member["student"];g=ROOT/member["teacher"];b=packet["installed"][role]
            assert b["published_notebook_sha256"]==sha(p) and b["guide_sha256"]==sha(g)
            b["authored_cells_sha256"]=bundle.authored_cells_sha256(p)
        current_scope=bundle.course_scope(ROOT)
        version_paths=["tools/course.mjs","tools/course_core.mjs","tools/course_assess.mjs","tools/course_run.mjs","tools/course_ledger.mjs","tools/course_kernel.py","tools/course_diff.py","tools/material_revision.py","tools/course_tool_prerequisites.py","tools/course_tool_prerequisites.mjs","skills/koai-evaluate/SKILL.md"]
        evidence={"schema":"week01_native_prerequisite_review_v2","week":1,"date":os.environ.get("GITHUB_RUN_ID") and __import__("datetime").datetime.now(__import__("datetime").timezone.utc).date().isoformat(),"decision":"accepted","profile":"development","eligibility":run["eligibility"],"native_program":"tools/course.mjs","previous_teaching_edition":OLD,"action":"revise","method":"Run and resume in the normal CLI using four actual learner notebooks, all four teacher guides and four copied, executable teacher solutions. The original submitted notebooks used the exact previously published route. The corrected author response was admitted after its recorded rejection and was then executed and independently reviewed.","source_scope":"Repository-registered primary-source readings and externally reviewed active official sources as recorded in the dated ground and educational review. The controller did not fetch a new all-course original-document packet.","physical_execution":"The unmodified repository course kernel used four distinct conventional Jupyter student sessions and one new teacher session for each probe. No external model was hosted in CI. The loopback transport verified external curriculum decisions bound to this candidate, with separately authored executable exam generation and blind scoring.","randomized_inputs":"Fresh numeric cases generated using operating-system entropy remained in temporary runner storage. Only totals and digests are retained. Repeating the procedure draws new inputs. The public specifications and methods were known; realized inputs and expected answers were withheld from lesson authors.","assessment_file_sha256":sha(ext/"suite.json"),"blind_verification":{k:suite["verification"][k] for k in ("reviewer","answer_hash","case_hash")},"role_source_sha256":{p:sha(CI/p) for p in ("ground.json","examiner.py","blind_solver.py","reviewer.json","author-approval.json","assemble.mjs","native.py")},"named_external_responses":calls,"program_sha256":{p:sha(ROOT/p) for p in version_paths},"route_file_sha256":packet["historical_route_sha256"],"route_class_minutes":sum(u["minutes"] for u in packet["route_units"] if u["tier"]=="class"),"route_homework_minutes":sum(u["minutes"] for u in packet["route_units"] if u["tier"]=="homework"),"previous_candidate_sha256":packet["original_candidate_sha256"],"native_import_sha256":packet["native_import_sha256"],"candidate_sha256":packet["candidate_sha256"],"governing_week_one_sha256":current_scope["curriculum/course-harness.json#week-1"],"course_scope":current_scope,"tool_prerequisites":{"rules":packet["compiled_tool_rules"],"assessment":packet["validation"],"historical_refusal":packet["historical_refusal"],"judgment":review["checks"]["tool_prerequisites"]},"material_bindings":packet["installed"],"typed_edit":diffrows[0],"native_phases":phases,"final_probe_totals":totals,"final_review_check_count":len(phases[-1]["review_checks"]),"resume":{k:resume[k] for k in ("scope","completed","calls","eligibility")},"status":{k:status[k] for k in ("scope","completed","calls","eligibility")},"workflow":{"repository":os.environ.get("GITHUB_REPOSITORY"),"run":os.environ.get("GITHUB_RUN_ID"),"commit":os.environ.get("GITHUB_SHA")}}
        result=ext/"native-textbook-review.json";write(result,evidence);export(result.name,result.read_bytes())

if __name__=="__main__":
    main()
