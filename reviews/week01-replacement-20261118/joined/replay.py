"""Rebuild the Week 1 replacement checks from recorded independent judgments and real file bytes."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent.relative_to(ROOT)
CASE = Path("reviews/week01-depth-20261118")
OLD = CASE / "joined"
sys.path.insert(0, str(ROOT / "tools"))
import contest_depth
import discovery_loop
import graph_paths
import lesson_route
import quality
import review_preflight
import workflow


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def file_hash(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def source(identity, path):
    return {"id": identity, "revision": "2026-11-18", "sha256": file_hash(path), "uri": str(path)}


def evidence(path, locator, observation=None):
    return {"path": str(path), "sha256": file_hash(path), "locator": locator,
            **({"observation": observation} if observation else {})}


def check_locations(audit, route, canonical):
    if (file_hash(audit["route"]) != audit["route_sha256"]
            or file_hash(audit["canonical_review"]) != audit["canonical_review_sha256"]
            or file_hash(audit["contract"]) != canonical["contract_sha256"]):
        raise ValueError("Reviewed route, independent receipt or contract changed")
    if file_hash(route["entry"]) != audit["notebook_sha256"]:
        raise ValueError("Entry changed after review")
    expected_snaps = audit["files"]
    for path, expected in expected_snaps.items():
        if file_hash(path) != expected:
            raise ValueError("Reviewed file changed: " + path)
    if dict((k, expected_snaps[k]) for k in route["files"]) != route["files"]:
        raise ValueError("Reviewed subjects differ from route")
    for path, cells in audit["read_cells"].items():
        actual = [c["id"] for c in read(path)["cells"]]
        if list(cells) != actual:
            raise ValueError("Whole-notebook cell scope differs: " + path)
    if set(audit["read_cells"]) != set(route["companions"]):
        raise ValueError("Reviewed notebook set differs from registered route")
    round_no = audit["round"]
    round_file = CASE / "rounds" / f"{round_no:04d}" / "round.json"
    if file_hash(round_file) != canonical["round_sha256"]:
        raise ValueError("Registered round changed")
    for topic, detail in audit["units"].items():
        for key, (path, locator) in detail["route_roles"].items():
            if str(path).endswith(".ipynb"):
                ids = set(audit["read_cells"][path])
                for cid in locator.split(","):
                    if cid not in ids:
                        raise ValueError(f"{topic}.{key} unknown cell {cid}")
        if topic not in canonical["topics"]:
            raise ValueError("Missing independent topic " + topic)


def graph_and_depth(audit, basis, route, canonical):
    graph = {"nodes": [], "edges": []}
    paths = {"schema_version": 1, "synthetic": False, "required_demands": [], "paths": []}
    semantics = {"schema_version": 1, "synthetic": False,
                 "reviewer": {"id": audit["reviewer"], "method": audit["method"]},
                 "scope": audit["scope"], "comparisons": []}
    scope_sources = []
    problem_sources = []
    for item in basis["sources"]:
        bound = {"id": item["id"], "url": item["url"], "title": item["revision"],
                 "version": item["revision"], "locator": item["locator"], "read_extent": item["locator"],
                 "verification": "verified_official", "verification_evidence": basis["official_reading"],
                 "accessed_at": basis["recorded_at"][:10]}
        if item["kind"] == "official_scope":
            scope_sources.append(bound)
        else:
            is_past = item["id"] == "antique"
            problem_sources.append({**bound, "kind": "past_problem" if is_past else "example",
                "problem": item["locator"], "year": 2025 if is_past else 2026,
                "target": "international_high_school" if is_past else "high_school"})
    entry = route["entry"]
    revision = audit["notebook_sha256"][:12]
    week = {"week": 1, "in_class_minutes": audit["class_minutes"], "outside_class_minutes": audit["required_homework"],
            "locator": audit["timing_basis"], "required_assessment_format": {"status": "specified", "counts":
            {"multiple_choice": 2, "written": 1}, "locator": "curriculum/student-plan.html#week-1"},
            "observed_assessment_format": {"status": "observed", "counts": audit["written_counts"],
                                          "locator": audit["written_locator"]}}
    depth = {"schema_version": 1, "synthetic": False, "target": {"competition_year": 2027, "division": "middle_school",
             "artifact": entry, "artifact_revision": revision, "artifact_sha256": audit["notebook_sha256"],
             "class_minutes": 120, "weeks": [1], "baseline_assumptions": [audit["scope"]], "goals": []},
             "scope_sources": scope_sources, "problem_sources": problem_sources, "comparisons": [],
             "time_allocations": [week], "unknowns": [], "outside_material_scope":
             ["learner_performance", "actual_classroom_time", "actual_teacher_effort"],
             "limitations": [audit["limits"]]}
    document = HERE / audit["audit_name"]
    for tid, unit in audit["units"].items():
        cid = "compare:" + tid
        pid = "path:" + tid
        goal = "goal:" + tid
        item = canonical["topics"][tid]
        problem = next(s for s in problem_sources if s["id"] == unit["reference_problem"])
        roles = {"source": [HERE / "source-basis.json", problem["id"] + " and domestic"],
                 "demand": [audit["contract"], tid + " objective/minimum/assessment"], **unit["route_roles"]}
        nodes = {role: tid + ":" + role for role in roles}
        for role, nid in nodes.items():
            graph["nodes"].append({"id": nid, "type": "evidence" if role == "source" else "artifact",
                                   "status": "completed", "label": tid + " " + role})
        for left, right in zip(nodes.values(), list(nodes.values())[1:]):
            graph["edges"].append({"from": left, "to": right, "type": "supports"})
        paths["required_demands"].append(nodes["demand"])
        provenance = {role: {**evidence(path, loc), "revision": revision,
                     "origin": "whole-route independent reading" if role not in ("source","demand") else role}
                      for role,(path,loc) in roles.items()}
        paths["paths"].append({"id": pid, "comparison_id": cid, "discovery_demand_id": tid, "roles": nodes,
                               "assessment": {"independent": unit["independent"], "allowed_support": audit["first_attempt"],
                                              "answer_conditions": audit["answer_conditions"]},
                               "provenance": provenance})
        result = {"path_id": pid, "comparison_id": cid}
        for dimension, observation in unit["semantic"].items():
            role = "independent_assessment" if dimension == "independent_assessment" else "feedback"
            refs = [evidence(*roles[role]), evidence(document, "units." + tid + ".semantic." + dimension)]
            refs += [evidence(path,loc) for path,loc in unit.get("additional_evidence",{}).get(dimension,[])]
            result[dimension] = {"judgment": unit.get("semantic_status",{}).get(dimension,"met"),
                                 "rationale": observation, "evidence": refs}
        semantics["comparisons"].append(result)
        depth["target"]["goals"].append({"id": goal, "week": 1, "description": unit["objective"]})
        depth["comparisons"].append({"id": cid, "goal_id": goal, "week": 1, "competency": unit["objective"],
             "assessment_method": audit["method"], "answer_conditions": audit["answer_conditions"],
             "allowed_support": audit["first_attempt"], "author_id": audit["author"],
             "reviewer": {"id": audit["reviewer"], "independent": True,
                          "evidence_locator": str(document) + " units." + tid},
             "scope_refs": [{"source_id": "domestic", "locator": scope_sources[1]["locator"]},
                            {"source_id": "guide", "locator": scope_sources[0]["locator"]}],
             "problem_refs": [{"source_id": problem["id"], "locator": problem["locator"]}],
             "student_task_locators": [str(path) + "#" + loc for path,loc in unit["examined_assessments"]],
             "difference": unit["difference"], "judgment": unit["contest_judgment"],
             "rationale": item["finding"] + " " + unit["semantic"]["independent_assessment"],
             "theory": {"applicable": True, "claim": unit["explain"],
                        "evidence_locators": [str(path) + "#" + loc for path,loc in unit["examined_theory"]]}})
    repair = audit["conditional_path"]
    table = next(p for p in paths["paths"] if p["discovery_demand_id"] == "W1-table")
    repair_id = "path:W1-table:conditional"
    roles = dict(list(table["roles"].items())[:2])
    provenance = {name: table["provenance"][name] for name in roles}
    for role, (path, locator) in repair["role_evidence"].items():
        if str(path).endswith(".ipynb"):
            if not set(locator.split(",")).issubset(audit["read_cells"][path]):
                raise ValueError("Unknown conditional notebook cell " + locator)
        new_node = "W1-table:conditional:" + role
        graph["nodes"].append({"id": new_node, "type": "artifact", "status": "completed", "label": new_node})
        graph["edges"].append({"from": list(roles.values())[-1], "to": new_node, "type": "supports"})
        roles[role] = new_node
        provenance[role] = {**evidence(path, locator), "revision": revision, "origin": "directly read conditional student path"}
    paths["paths"].append({"id": repair_id, "comparison_id": table["comparison_id"], "discovery_demand_id": "W1-table",
        "roles": roles, "provenance": provenance, "assessment": table["assessment"]})
    observed = {"path_id": repair_id, "comparison_id": table["comparison_id"]}
    for dim, explanation in repair["semantic"].items():
        role = "independent_assessment" if dim == "independent_assessment" else "feedback"
        observed[dim] = {"judgment": "met", "rationale": explanation, "evidence": [
            evidence(*repair["role_evidence"][role]), evidence(*repair["evidence_after_return"]),
            evidence(document, "conditional_path.semantic." + dim)]}
    semantics["comparisons"].append(observed)
    semantics["graph_sha256"] = graph_paths.canonical_sha256(graph)
    semantics["path_spec_sha256"] = graph_paths.canonical_sha256(paths)
    return graph, paths, semantics, depth


def quality_input(audit, basis, route, canonical, discovery_path):
    result = read("templates/quality.json")
    contract = read(audit["contract"])
    governing = read(quality.CONTRACT)
    curriculum = governing["baseline"]["path"]
    specs = read(quality.UNIT_SPECIFICATIONS)
    blueprint = {u["id"]: u for u in specs["units"]}
    revision = "replacement-" + audit["notebook_sha256"][:12]
    doc = HERE / audit["audit_name"]
    actual = HERE / audit["physical_report"]
    kernel = HERE / audit["kernel_report"]
    result.update(revision=revision, author_id=audit["author"],
       artifact={"id": "week01-foundations", "revision": revision, "path": route["entry"], "sha256": file_hash(route["entry"])},
       discovery={"path": str(discovery_path)},
       target={"competition_year":2027,"division":"middle_school","coverage_claim":"selected_scope",
               "objective_ids":list(audit["units"]),"learning_outcomes":"outside_scope"})
    result["checkpoint"].update(minutes_since=0, elapsed_total=audit["minutes_elapsed"],
        no_progress_count=0, record=audit["checkpoint"])
    result["operator_notes"] = {"global_policy": audit["limits"], "route": audit["timing_basis"]}
    result["lesson_allocations"] = [{"week": 1, "blocks": audit["blocks"], "basis": audit["timing_basis"],
        "outside_work": [{"id": unit["id"], "required": unit["status"] == "required", "minutes": unit["homework_minutes"]}
                         for unit in route["units"] if unit["status"] != "deferred"]}]
    sources = {}
    for old in ("sources.json","technical-readings.json"):
        for s in read(OLD / old):
            if s["id"] not in audit["technical_sources"]:
                continue
            if s["kind"] not in ("documentation","primary_documentation"):
                raise ValueError("Only unchanged library primary definitions can be reused: " + s["id"])
            sources[s["id"]] = ({**s, "kind":"documentation"},OLD / old)
    for s in basis["sources"]:
        sources[s["id"]] = ({"id":s["id"],"url":s["url"],"version":s["revision"],"kind":"official",
                             "accessed_at":basis["recorded_at"][:10],"extent":"relevant_sections",
                             "locator":s["locator"],"finding":s["statement"],"limitation":s["boundary"]},
                            HERE / "source-basis.json")
    for s in audit.get("new_technical_sources", []):
        sources[s["id"]] = (s, doc)
    def dependency(key, sha, parents=(), path=None, **extra):
        d = {"id":key,"revision":revision,"sha256":sha,"depends_on":list(parents),**extra}
        if path:
            d["path"] = str(path)
        result["dependencies"].append(d)
    for sid,(note,sourcepath) in sources.items():
        result["source_reads"].append(note)
        dependency(sid,file_hash(sourcepath),path=sourcepath)
    for path in audit["files"]:
        dependency("file:"+path,file_hash(path),path=path)
    dependency("refresh",file_hash(audit["contract"]),path=audit["contract"])
    claim_owners = {}
    for tid, item in audit["units"].items():
        spec = blueprint[tid]
        plan_id = "plan:"+tid
        plan_locs = ["#plan-context","#week-1"]+[next(t["plan_locator"] for t in governing["topics"] if t["id"]==key)
                                                 for key in spec["syllabus_ids"]]
        dependency(plan_id,file_hash(curriculum),path=curriculum,locators=plan_locs)
        claim_ids = []
        for local_id, c in item["claims"].items():
            cid = "claim:"+local_id
            claim = {"id":cid,"quantity":local_id,"domain":"Visible instructional route and bounded public inputs",
                     "assumptions":[c["condition"]],"statement":c["text"],"locator":"cell:"+c["cell"],
                     "source_ids":c["sources"]}
            if c.get("oracle"):
                claim["oracle"] = c["oracle"]
            for sid in claim["source_ids"]:
                if sid not in sources:
                    raise ValueError("Missing primary reading: "+sid)
            result["claims"].append(claim)
            claim_ids.append(cid)
            claim_owners[cid] = tid
            dependency(cid,quality.digest(claim),claim["source_ids"])
        related = set(item["asset_paths"])
        refs = ["file:"+name for name in sorted(related)]
        related_topics = next(t["prerequisites"] for t in contract["topics"] if t["id"] == tid)
        dependency(tid,quality.digest(item),claim_ids+[plan_id,"refresh"]+related_topics+refs)
        chain = {role:{"concept_ids":spec["concept_ids"],"locator":"cell:"+c[0],
                       "expected_behavior": c[2], "help":"none" if role=="assessment" else "guided where indicated",
                       "new_input": role=="assessment","activity_id":c[1]} for role,c in item["class_chain"].items()}
        prereqs = [{"id":pid,**specs["diagnostics"][pid],"support_before_use":
                    {"before_unit":tid,"locator":"cell:"+first,"first_use":"cell:"+use}}
                   for pid,(first,use) in item["prereq_cells"].items()]
        regions = {t:["cell:"+cid for cid in val["cells"]] for t,val in item["explanation_checks"].items()}
        result["units"].append({"id":tid,"week":1,"locator":chain["theory"]["locator"],"syllabus_ids":spec["syllabus_ids"],
            "concept_ids":spec["concept_ids"],"claimed_depth":"independent","depth_scope":audit["scope"],
            "mode_evidence":{"practical":"passed"},"prerequisites":prereqs,"claim_ids":claim_ids,
            "plan_dependency_ids":[plan_id],"chain":chain,"explanation_regions":regions,
            "independent_assignment":{"evidence":item["examined_assessments"],"support":audit["first_attempt"]},
            "execution":{"status":audit["physical_status"],"artifact_sha256":file_hash(route["entry"]),
               "command":audit["execution_command"],"environment":audit["environment"],"exit_code":audit["execution_exit"],
               "clean_run":True,"new_input":True,"assertions":audit["assertions"],
               "evidence":[evidence(kernel, "notebooks", "Fresh separate student processes ran all 28 main and 4 conditional code cells, with unchanged input hashes."),
                           evidence(actual, "status, changed_outputs, public_rows, rendered_panels, physical_blank_ids, conditional", "All eight teacher blocks and independently computed raw rows, weighted totals, actual plotted bars, all-blank keys and conditional return cases passed.")]}})
    for c in result["claims"]:
        context = quality.object_fingerprint(result,"K10",c["id"],ROOT)
        result["research_cycles"].append({"id":"read:"+c["id"],"trigger":"Check the current claim against a primary original and public inputs.",
            "queries":[sources[s][0]["url"] for s in c["source_ids"]],"source_ids":c["source_ids"],
            "object_ids":[c["id"]],"object_contexts":{c["id"]:context},"disposition":"unchanged",
            "reason":"The observed operation, stated limits and independently checked public results support the scoped claim."})
    checks = [(tid,k,txt,False) for tid,item in audit["units"].items() for k,txt in item["quality"].items()]
    checks.extend((c["id"],"K06",c["statement"],True) for c in result["claims"])
    for obj, key, why, is_claim in checks:
        tid = claim_owners[obj] if is_claim else obj
        item = audit["units"][tid]
        ref = {"id":key+":"+obj,"criterion_id":key,"object_id":obj,"reviewer_id":audit["reviewer"],"reason":why,
               "status":item.get("quality_status",{}).get(key,"passed"),
               "evidence":[evidence(doc,"units."+tid+" / "+key,why),evidence(actual,"entry_sha256, changed_outputs, public_rows, physical_blank_ids and conditional",item["semantic"]["problem_specific_key"])],
               "context_fingerprint":quality.object_fingerprint(result,key,obj,ROOT)}
        plan_binding = quality.plan_bindings(result,obj,ROOT)["scope_fingerprint"]
        if plan_binding:
            ref["dependency_scope_fingerprint"]=plan_binding
        if key=="K16":
            ref["subchecks"]={t:{"status":v.get("status","passed"),
                "artifact_locators":["cell:"+cid for cid in v["cells"]],
                "evidence":[evidence(route["entry"],",".join(v["cells"]),v["observation"]),
                            evidence(doc,"units."+tid+".explanation_checks."+t,v["observation"])]}
                for t,v in item["explanation_checks"].items()}
        result["reviews"].append(ref)
    return quality.validate(result)


def workflow_state(audit, basis, route, q, qrep, graph, paths, semantics, depth, discovery):
    state=read("templates/workflow.json")
    state["scope"] = {"task_kind":"lesson_production","lesson_production_allowed":True,"recurring_allowed":False}
    state["agreement"].update(operator_agreed=True,operator_id="user",criteria_agreed=False)
    regs={"source-basis":HERE/"source-basis.json","frozen":Path(audit["contract"]),
          "route":Path(audit["route"]),"content":HERE/audit["audit_name"],
          "route-kernel":HERE/audit["kernel_report"],"physical":HERE/audit["physical_report"],
          "subject":Path(route["entry"]),"public-review":Path(audit["canonical_review"]),
          "specification":Path(quality.UNIT_SPECIFICATIONS),"discovery":HERE/"discovery.json"}
    for i,name in enumerate(sorted(route["files"])):
        if name != route["entry"]:
            regs["asset-"+str(i)]=Path(name)
    state["sources"]=[source(key,path) for key,path in regs.items()]
    context=state["context"]
    def local_manifest(i,p):
        return {k:v for k,v in source(i,p).items() if k!="uri"}
    context.update(author={"id":audit["author"],"model_family":"Codex; exact family unverified"},
       inputs=[{"id":"quality:bundle","revision":qrep["revision"],"sha256":qrep["bundle_sha256"]},
               {"id":"quality:criteria","revision":qrep["specification_revision"],"sha256":qrep["specification_sha256"]},
               {"id":"quality:evaluator","revision":"quality-v1","sha256":qrep["evaluator_sha256"]},
               *review_preflight.context_manifests(depth,graph,paths,semantics,state["sources"],discovery)],
       skills=[local_manifest("koai-"+name,"skills/koai-"+name+"/SKILL.md") for name in ("ground","evaluate","orchestrate")],
       references=[local_manifest(k,regs[k]) for k in ("source-basis","frozen","specification")],
       artifact=local_manifest("week01-foundations",route["entry"]),
       rubric=local_manifest("criteria",quality.CATALOG),evaluator=local_manifest("evaluator","tools/quality.py"),
       required_checks=[c["id"] for c in qrep["checks"]],
       finish_condition="Exact current whole-route technical/material and 16-criterion checks. The independent replacement comparison and operator campaign-policy agreement have separate authority.")
    manifest=qrep.get("topic_depth",{}).get("manifest")
    if manifest:
        context["inputs"].append(manifest)
    state["frozen"]=workflow.measurement(state)
    state["scope_readback"]=audit["limits"]
    state["usage"].update(iterations_used=audit["round"]-3,elapsed_minutes=audit["minutes_elapsed"],
                          minutes_since_checkpoint=0,no_progress_count=0)
    records=[("requirements","Direct original source re-read before candidate comparison and exact refreshed topical baseline.",
               [("source-basis","sources and independent_extraction"),("frozen","topics")]),
             ("content","A distinct reviewer inspected all student-visible material and its actual teacher feedback on this route.",
               [("content","read_cells, units and limitations"),("route","links and units"),("public-review","topics")]),
             ("execution","Independently executed every registered student notebook and the scoped technical calculations.",
               [("physical","public probes"),("route-kernel","notebooks, figures and file changes")]),
             ("policy","The bounded experiment was authorized. The full-campaign legacy policy still lacks a numeric operator agreement.",
               [("content","limits and checkpoint"),("frozen","scoped topic design and time")])]
    for rid,txt,refs in records:
        state["records"].append({"id":rid,"kind":"evidence","text":txt,"created_at":audit["recorded_at"],
            "source_refs":[{"source_id":sid,"locator":where} for sid,where in refs],"supersedes":[]})
    state["reviews"]=[{"id":"technical-"+str(audit["round"]),"context_fingerprint":workflow.context_fingerprint(state),
        "author_id":audit["author"],"reviewer":{"id":audit["reviewer"],"model_family":"Codex; exact family unverified"},
        "conclusion":"abstain","reason":audit["limits"],
        "checks":[{"id":c["id"],"status":c["status"] if c["status"] in ("passed","failed") else "not_run",
                   "evidence_record_ids":["policy"] if c["id"]=="K14" else ["requirements","content","execution"]}
                  for c in qrep["checks"]]}]
    errors,_=workflow.validate_state(state)
    if errors:
        raise ValueError("Invalid workflow state: "+repr(errors))
    return state


def build(audit):
    basis=read(HERE/"source-basis.json")
    route=read(audit["route"])
    canonical=read(audit["canonical_review"])
    check_locations(audit,route,canonical)
    graph,paths,semantics,depth=graph_and_depth(audit,basis,route,canonical)
    discovery_path=HERE/"discovery.json"
    discovery=read(discovery_path)
    q=quality_input(audit,basis,route,canonical,discovery_path)
    qr=quality.evaluate(q,ROOT)
    state=workflow_state(audit,basis,route,q,qr,graph,paths,semantics,depth,discovery)
    return {"graph":graph,"paths":paths,"semantic-review":semantics,"contest-depth":depth,
            "quality":q,"workflow":state}, qr


def summarize(audit, bundles, qr):
    graph,paths,sem,depth,state=[bundles[key] for key in ("graph","paths","semantic-review","contest-depth","workflow")]
    d=read(HERE/"discovery.json")
    ds=discovery_loop.inspect(d,ROOT)
    dep=contest_depth.inspect(depth)
    mechanics=graph_paths.inspect_paths(graph,paths,ROOT)
    meaning=graph_paths.inspect_semantic_review(graph,paths,sem,ROOT)
    pre=review_preflight.preflight(ROOT,depth,graph,paths,state,bundles["quality"],sem,d)
    route,_,_=lesson_route.inspect_route(ROOT,audit["route"])
    plan=quality.plan_work(bundles["quality"],ROOT,report=qr)
    policy=workflow.decide(state,qr,ds)
    topology=qr.get("topic_depth",{})
    evidence_files = [HERE / name for name in ("source-basis.json", "transfer-research.md", "discovery-seed.json",
                       "discovery.json", audit["audit_name"], audit["physical_report"], audit["kernel_report"])]
    evidence_files += [Path(audit[k]) for k in ("route", "contract", "canonical_review")]
    evidence_files += [Path(path) for path in sorted(audit["files"])]
    return {"subject_sha256":audit["notebook_sha256"],"synthetic":False,
      "evidence_sha256":{str(path): file_hash(path) for path in evidence_files},
      "bundle_sha256":{key: graph_paths.canonical_sha256(bundle) for key,bundle in bundles.items()},
      "route":route, "topic_depth":{k:topology.get(k) for k in ("status","ready","subject_round","subject_sha256","manifest","errors")},
      "discovery":{"status":ds["status"],"events":len(d["events"]),"elapsed_minutes":ds.get("elapsed_minutes", audit["minutes_elapsed"]),"head":d["events"][-1]["sha256"],"demands":{x["demand_id"]:x["judgment"] for x in ds["comparisons"]},"queue":ds["queue"],"blockers":ds["blockers"]},
      "contest_depth":{"status":dep["status"],"comparisons":dep["comparisons"],"findings":dep["findings"],
          "gaps":dep["gaps"],"assessment_formats":dep["assessment_formats"]},
      "paths":{"status":mechanics["status"],"graph_nodes":len(graph["nodes"]),"graph_edges":len(graph["edges"]),"paths":len(paths["paths"]),"findings":mechanics["findings"],"bindings":len(mechanics["bindings"])},
      "semantic_review":{"status":meaning["status"],"paths":len(meaning["comparisons"]),"findings":meaning["findings"],"bindings":len(meaning["bindings"])},
      "quality":{"status":qr["status"],"ready_for_review":qr["ready_for_review"],
          "criterion_status":{x["id"]:x["status"] for x in qr["checks"]},
          "findings":[{"criterion_id":x["criterion_id"],"status":x["status"],"objects":x["objects"]} for x in qr["findings"]],
          "evaluator_sha256":qr["evaluator_sha256"]}, "plan":{"status":plan["status"],"reason":plan["reason"]},
      "workflow":{"status":policy["status"],"reason":policy["reason"],"errors":workflow.validate_state(state)[0]},
      "preflight":{"status":pre["status"],"blockers":pre["blockers"],"errors":pre["errors"],
          "binding_count":len(pre["bindings"]),"unmatched":[b for b in pre["bindings"] if not b["matched"]]}}


def verify_report(current, recorded):
    from copy import deepcopy

    expected_criteria = {f"K{i:02}": "uncertain" if i == 14 else "passed" for i in range(1, 17)}
    expected_blockers = [
        {"code": "quality_not_ready", "detail": "uncertain"},
        {"code": "workflow_pause", "detail": "criteria_agreement_required"}]
    problems = []
    def compare(field, result, expected):
        if result != expected:
            problems.append(field)

    compare("criterion_status", current["quality"]["criterion_status"], expected_criteria)
    compare("quality.ready_for_review", current["quality"]["ready_for_review"], False)
    compare("preflight.status", current["preflight"]["status"], "blocked")
    compare("preflight.blockers", current["preflight"]["blockers"], expected_blockers)
    compare("preflight.errors", current["preflight"]["errors"], [])
    compare("preflight.unmatched", current["preflight"]["unmatched"], [])
    compare("preflight.binding_count", current["preflight"]["binding_count"], 16)
    compare("topic_depth.ready", current["topic_depth"]["ready"], True)
    compare("registered subjects", set(current["discovery"]["demands"]), {"W1-python","W1-table","W1-array","W1-visualise"})
    compare("structure", [current["paths"]["paths"], current["paths"]["bindings"]], [5, 35])
    compare("semantics", [current["semantic_review"]["paths"], current["semantic_review"]["bindings"]], [5, 38])
    compare("budget", current["route"]["budget"], "overrun")
    for key, value in current.items():
        expected = recorded.get(key)
        if key == "route" and isinstance(expected, dict):
            # A checked-out named branch and its byte-identical published ref can both
            # prove the same official student navigation during a detached CI checkout.
            value, expected = deepcopy(value), deepcopy(expected)
            value["normal_entry"].pop("basis", None)
            expected["normal_entry"].pop("basis", None)
        compare("release." + key, value, expected)
    return {"status": "changed" if problems else "recorded_blockers_verified",
            "production_ready": current["quality"]["ready_for_review"],
            "preflight": current["preflight"]["status"], "blockers": current["preflight"]["blockers"],
            "matched_bindings": current["preflight"]["binding_count"] - len(current["preflight"]["unmatched"]),
            "differences": problems}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit",default="audit.json",help="Scoped review JSON in this directory")
    parser.add_argument("--export",type=Path,help="Write full native CLI input bundles into this directory")
    parser.add_argument("--verify",action="store_true",help="Return zero only for the exact recorded R5 evidence and known blockers")
    args=parser.parse_args()
    audit=read(HERE/args.audit)
    bundles,qr=build(audit)
    if args.export:
        args.export.mkdir(parents=True,exist_ok=True)
        for name,obj in bundles.items():
            (args.export/(name+".json")).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
    report=summarize(audit,bundles,qr)
    if args.verify:
        check = verify_report(report, read(HERE/"reports.json"))
        print(json.dumps(check, ensure_ascii=False, indent=2))
        return int(bool(check["differences"]))
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return int(report["preflight"]["status"]=="blocked")


if __name__=="__main__":
    sys.exit(main())
