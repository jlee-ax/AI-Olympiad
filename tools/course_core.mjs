function makeCourseCore() {
  "use strict";
  const modes = ["theory", "practical"];
  const operationKinds = ["create", "revise", "supplement", "remove", "merge", "move", "keep", "restore"];
  function requireValue(ok, why) { if (!ok) throw new Error(why); }
  function record(value) { return Boolean(value) && typeof value === "object" && !Array.isArray(value); }
  function nonempty(value) { return typeof value === "string" && value.trim().length > 0; }
  function unique(values, label) {
    requireValue(Array.isArray(values) && new Set(values).size === values.length, "Duplicate or invalid " + label);
  }
  function stable(value) {
    if (Array.isArray(value)) return "[" + value.map(stable).join(",") + "]";
    if (record(value)) return "{" + Object.keys(value).sort().map(key => JSON.stringify(key) + ":" + stable(value[key])).join(",") + "}";
    if (value === undefined || (typeof value === "number" && !Number.isFinite(value))) throw new Error("Non-JSON value");
    return JSON.stringify(value);
  }
  function same(left, right) { return stable(left) === stable(right); }
  function compile(contract, design, sources, studentPlan) {
    requireValue(Array.isArray(contract.weeks) && contract.weeks.length && Array.isArray(contract.topics), "Empty contract");
    requireValue(Array.isArray(design.weeks) && design.weeks.length === contract.weeks.length, "Incomplete week registration");
    const allocations = new Map(contract.weeks.map(w => [w.week, w]));
    unique(contract.weeks.map(w => w.week), "weeks");
    unique(contract.topics.map(t => t.id), "topics");
    const entries = new Map();
    for (const w of design.weeks) {
      requireValue(Number.isInteger(w.week) && allocations.has(w.week) && !entries.has(w.week), "Unknown or repeated week");
      const budget = allocations.get(w.week);
      requireValue(budget.theory_minutes + budget.noncoding_minutes + budget.coding_minutes === contract.class_minutes &&
        Array.isArray(budget.required_self_study_hours) && budget.required_self_study_hours.length === 2 &&
        budget.required_self_study_hours.every(x => Number.isFinite(x) && x >= 0) &&
        budget.required_self_study_hours[0] <= budget.required_self_study_hours[1], "Invalid curriculum time");
      for (const name of ["decision", "minimum", "ceiling", "transfer", "interface"]) {
        requireValue(nonempty(w[name]), "Missing " + name + " for week " + w.week);
      }
      unique(w.prerequisites, "prerequisites");
      unique(w.sources, "sources");
      requireValue(w.sources.length && w.sources.every(id => sources[id] && nonempty(sources[id].locator) && nonempty(sources[id].text)), "Missing source for week " + w.week);
      requireValue(nonempty(studentPlan[w.week]), "Missing student plan row for week " + w.week);
      entries.set(w.week, {...w, budget, plan:studentPlan[w.week], topics:[]});
    }
    const done = new Set(), visiting = new Set(), order=[];
    function visit(week) {
      requireValue(entries.has(week) && !visiting.has(week), "Missing or cyclic prerequisite " + week);
      if (done.has(week)) return;
      visiting.add(week);
      for (const before of entries.get(week).prerequisites) visit(before);
      visiting.delete(week); done.add(week); order.push(week);
    }
    for (const w of entries.keys()) visit(w);
    for(const row of entries.values()){
      row.next_uses=order.filter(n=>entries.get(n).prerequisites.includes(row.week)).map(n=>{
        const next=entries.get(n);return {week:n,decision:next.decision,minimum:next.minimum,transfer:next.transfer};
      });
    }
    for (const topic of contract.topics) {
      requireValue(nonempty(topic.id) && nonempty(topic.name) && modes.every(m => typeof topic[m] === "boolean") &&
        modes.some(m => topic[m]) && Array.isArray(topic.scheduled_weeks) && topic.scheduled_weeks.length, "Invalid topic " + topic.id);
      unique(topic.scheduled_weeks, "topic placements");
      const placements = topic.scheduled_weeks;
      const assessedAt = design.assess_at?.[topic.id] ?? Math.max(...placements);
      requireValue(placements.includes(assessedAt), "Assessment outside scheduled weeks " + topic.id);
      for (const week of placements) {
        requireValue(entries.has(week), "Unknown week for " + topic.id);
        entries.get(week).topics.push({id:topic.id,name:topic.name,modes:modes.filter(m => topic[m]),assess:week === assessedAt});
      }
    }
    for(const id of Object.keys(design.assess_at || {})) requireValue(contract.topics.some(t=>t.id===id), "Unknown assessment override " + id);
    return {order, weeks:Object.fromEntries(entries)};
  }

  function blockIndex(candidate) {
    const blocks = new Map();
    requireValue(record(candidate.notebooks) && Object.hasOwn(candidate.notebooks,"main"), "Missing main notebook");
    requireValue(!Object.hasOwn(candidate.notebooks,"teacher") && record(candidate.teacher), "Missing separate teacher notebook");
    for (const [name, nb] of Object.entries({...candidate.notebooks,teacher:candidate.teacher})) {
      requireValue(/^[a-z][a-z0-9_-]{0,60}$/.test(name) && nb?.nbformat === 4 && nb.nbformat_minor >= 5 && Array.isArray(nb.cells) && nb.cells.length, "Invalid notebook " + name);
      for (const cell of nb.cells) {
        const ref = name + "/" + cell.id;
        requireValue(/^[A-Za-z0-9_-]{1,64}$/.test(cell.id || "") && !blocks.has(ref) &&
          ["markdown","code"].includes(cell.cell_type) && record(cell.metadata), "Invalid cell " + ref);
        const body = Array.isArray(cell.source) ? cell.source.join("") : cell.source;
        requireValue(nonempty(body), "Empty cell " + ref);
        if (cell.cell_type === "code") requireValue(Array.isArray(cell.outputs) && cell.outputs.length === 0 && cell.execution_count === null, "Saved answer/output " + ref);
        blocks.set(ref,{...cell,body});
      }
    }
    return blocks;
  }
  function obligations(week) {
    return week.topics.filter(t => t.assess).flatMap(t => t.modes.map(m => t.id + "." + m));
  }
  function validateCandidate(week, candidate, previous) {
    requireValue(record(candidate) && candidate.week === week.week && operationKinds.includes(candidate.action) && nonempty(candidate.reason), "Invalid candidate action");
    requireValue(previous ? candidate.action !== "create" : candidate.action === "create", "Action incompatible with baseline");
    const blocks = blockIndex(candidate);
    const hit = (ref, type) => blocks.has(ref) && (!type || blocks.get(ref).cell_type === type);
    requireValue(record(candidate.route) && Array.isArray(candidate.route.units) && candidate.route.units.length, "Missing student route");
    const routed=new Set(), mandatory=new Set(); let classMinutes=0, homework=0;
    for (const u of candidate.route.units) {
      requireValue(Array.isArray(u.cells) && u.cells.length && u.cells.every(ref=>hit(ref) && !ref.startsWith("teacher/")) &&
        ["class","homework","conditional"].includes(u.tier) && Number.isInteger(u.minutes) && u.minutes>0, "Invalid route unit");
      if (u.tier==="conditional") requireValue(nonempty(u.trigger) && hit(u.returns), "Supplement needs an entry condition and return cell");
      for(const ref of u.cells){requireValue(!routed.has(ref),"Duplicate route cell " + ref);routed.add(ref);if(u.tier!=="conditional")mandatory.add(ref);}
      if(u.tier==="class")classMinutes+=u.minutes;
      if(u.tier==="homework")homework+=u.minutes;
    }
    for(const u of candidate.route.units)if(u.tier==="conditional")requireValue(mandatory.has(u.returns), "Conditional work must return to the mandatory student route");
    const sequence=[...mandatory];
    requireValue(routed.size===[...blocks.keys()].filter(r=>!r.startsWith("teacher/")).length && classMinutes<=week.budget.theory_minutes+week.budget.noncoding_minutes+week.budget.coding_minutes &&
      homework<=60*week.budget.required_self_study_hours[1], "Unregistered content or excess planned workload");
    requireValue(record(candidate.transfer) && hit(candidate.transfer.prompt,"markdown") && hit(candidate.transfer.principle,"markdown") &&
      hit(candidate.transfer.solution,"code") && candidate.transfer.prompt!==candidate.transfer.principle && nonempty(candidate.transfer.rationale), "Missing independent task or explanation");
    requireValue(candidate.transfer.solution.startsWith("teacher/") && mandatory.has(candidate.transfer.prompt) && mandatory.has(candidate.transfer.principle) && sequence.indexOf(candidate.transfer.principle)<sequence.indexOf(candidate.transfer.prompt), "Keep the private solution separate from student material");
    const references = r=>Array.isArray(r)&&r.length&&r.every(ref=>mandatory.has(ref));
    requireValue(Array.isArray(candidate.coverage), "Missing coverage");
    unique(candidate.coverage.map(c=>c.obligation), "coverage claims");
    const wanted=obligations(week);
    requireValue(same([...wanted].sort(),candidate.coverage.map(c=>c.obligation).sort()), "Missing or out-of-scope assessed obligation");
    for(const c of candidate.coverage) {
      requireValue(references(c.teaching) && references(c.assessment) && c.teaching.some(ref=>!c.assessment.includes(ref)) &&
        c.assessment.every(ref=>c.teaching.some(before=>sequence.indexOf(before)<sequence.indexOf(ref))) &&
        Array.isArray(c.sources) && c.sources.length && c.sources.every(id=>week.sources.includes(id)), "Unbound obligation " + c.obligation);
      if(c.obligation.endsWith(".practical"))requireValue(c.assessment.some(ref=>hit(ref,"code")) && hit(c.solution,"code") && c.solution.startsWith("teacher/"), "Missing practical evidence " + c.obligation);
    }
    if(previous) {
      const old=blockIndex(previous);
      const different=!same([previous.notebooks,previous.teacher],[candidate.notebooks,candidate.teacher]);
      requireValue(candidate.action==="keep" ? !different : different, "Action has no matching notebook change");
      if(candidate.action==="merge")requireValue([...blocks.keys()].some(k=>old.has(k)&&old.get(k).body!==blocks.get(k).body),"No retained cell incorporates merged content");
      if(candidate.action==="move"){
        const oldOrder=[...old.keys()].filter(k=>blocks.has(k)&&!k.startsWith("teacher/"));
        const newOrder=[...blocks.keys()].filter(k=>old.has(k)&&!k.startsWith("teacher/"));
        requireValue(!same(oldOrder,newOrder),"No retained student cell moved");
      }
      if(candidate.action==="remove"||candidate.action==="merge")requireValue([...old.keys()].some(ref=>!blocks.has(ref)), "No cell removed");
      if(candidate.action==="supplement")requireValue(Object.keys(candidate.notebooks).some(n=>!Object.hasOwn(previous.notebooks,n)&&
        candidate.route.units.some(u=>u.tier==="conditional"&&u.cells.some(ref=>ref.startsWith(n+"/")))), "No new conditional notebook");
    }
    return {cells:[...blocks.keys()],obligations:wanted,class_minutes:classMinutes,homework_minutes:homework};
  }

  const requiredReview=["scope","prerequisites","explanation","independent_task","alternative_solution","workload","answer_visibility","representation","depth_floor","depth_ceiling","downstream_use","revision_alternative"];
  function checkReview(week,candidate,report,hash,readers,demands=[]) {
    requireValue(report?.candidate_hash===hash && nonempty(report.reviewer) && report.reviewer!==readers.author &&
      report.reviewer===readers.reviewer && ["pass","revise","uncertain"].includes(report.verdict), "Stale or non-independent review");
    const blocks=blockIndex(candidate);
    const keys=[...requiredReview,...obligations(week),...demands];
    requireValue(record(report.checks) && same(Object.keys(report.checks).sort(),keys.sort()),"Incomplete review criteria");
    for(const [k,c] of Object.entries(report.checks)) {
      requireValue(["pass","revise","uncertain"].includes(c.verdict) && nonempty(c.finding) &&
        Array.isArray(c.cells) && c.cells.length && c.cells.every(ref=>blocks.has(ref)), "Unlocated judgment " + k);
      if(k.startsWith("demand.") && c.verdict==="pass")requireValue(new Set(c.cells.filter(ref=>!ref.startsWith("teacher/"))).size>=2,"Demand needs both a student explanation and distinct assessment");
      if(["representation","independent_task","depth_floor"].includes(k) && c.verdict==="pass")requireValue(c.cells.includes(candidate.transfer.principle) && c.cells.includes(candidate.transfer.prompt),"Review missed the principle or independent task for " + k);
      const claim=candidate.coverage.find(row=>row.obligation===k);
      if(claim)requireValue(c.cells.some(ref=>claim.teaching.includes(ref)) && c.cells.some(ref=>claim.assessment.includes(ref)),"Review missed obligation evidence " + k);
    }
    const values=Object.values(report.checks);
    const verdict=values.some(c=>c.verdict==="revise")?"revise":values.some(c=>c.verdict==="uncertain")?"uncertain":"pass";
    requireValue(report.verdict===verdict,"Review summary contradicts findings");
    return verdict;
  }

  function evaluateCases(suite,output) {
    requireValue(Array.isArray(suite) && suite.length>=3 && Array.isArray(output) && output.length===suite.length, "Incomplete independent execution");
    unique(suite.map(c=>c.id),"case IDs");
    const kinds=new Set(suite.map(c=>c.kind));
    requireValue(["normal","invariant","sensitive"].every(k=>kinds.has(k)),"Missing control family");
    requireValue(new Set(suite.map(c=>stable(c.input))).size===suite.length,"Duplicate independent input");
    function matches(expected, actual, tolerance) {
      if (typeof expected === "number" && typeof actual === "number") return Number.isFinite(actual) && Math.abs(expected-actual) <= tolerance;
      if (Array.isArray(expected)) return Array.isArray(actual) && actual.length===expected.length && expected.every((x,i)=>matches(x,actual[i],tolerance));
      if (record(expected)) return record(actual) && same(Object.keys(expected).sort(),Object.keys(actual).sort()) && Object.keys(expected).every(k=>matches(expected[k],actual[k],tolerance));
      return expected===actual;
    }
    const answers=c=>Object.hasOwn(c,"expected")?[c.expected]:c.any_of;
    for(const c of suite) {
      requireValue(nonempty(c.id) && c.input!==undefined && Object.hasOwn(c,"expected")!==Object.hasOwn(c,"any_of") &&
        Array.isArray(answers(c)) && answers(c).length && Number.isFinite(c.atol??0) && (c.atol??0)>=0, "Invalid independent case");
      requireValue(["normal","invariant","sensitive","boundary"].includes(c.kind), "Unknown independent case family");
      const choices=answers(c);
      requireValue(new Set(choices.map(stable)).size===choices.length,"Duplicate alternative in private assessment");
      if(["invariant","sensitive"].includes(c.kind)) {
        const base=suite.find(x=>x.id===c.base&&x.kind==="normal");
        requireValue(base, "Control disagrees with its baseline " + c.id);
        const original=answers(base);
        const equalSet=same(original.map(stable).sort(),choices.map(stable).sort()) && (base.atol??0)===(c.atol??0);
        const overlap=original.some(x=>choices.some(y=>matches(x,y,(base.atol??0)+(c.atol??0))));
        requireValue(c.kind==="invariant" ? equalSet : !overlap, "Control disagrees with its baseline " + c.id);
      }
    }
    const rows=suite.map((c,i)=>({id:c.id,kind:c.kind,passed:answers(c).some(y=>matches(y,output[i],c.atol??0))}));
    return {passed:rows.every(c=>c.passed),rows};
  }

  function reportCourse(course,active,bound) {
    const completed=[],pending=[],coverage=new Set();
    for(const week of course.order) {
      const a=active[week];
      if(a?.status==="accepted" && a.input===bound[week]){completed.push(week);for(const k of obligations(course.weeks[week]))coverage.add(k);}
      else pending.push(week);
    }
    return {completed,pending,verified_obligations:[...coverage].sort(),status:pending.length?"incomplete":"complete"};
  }
  return {compile,stable,obligations,validateCandidate,checkReview,evaluateCases,reportCourse,requiredReview};
}

export const courseCore = makeCourseCore();
