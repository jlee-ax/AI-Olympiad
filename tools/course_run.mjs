import {courseCore} from './course_core.mjs';

function makeCourseRunner(core) {
  "use strict";
  const insist=(ok,why)=>{if(!ok)throw new Error(why);};
  const requiredKeys=week=>["transfer",...core.obligations(week).filter(id=>id.endsWith(".practical"))];
  function publicOracles(week, packet) {
    const labels=requiredKeys(week), functions=[];
    insist(packet && ["private","development"].includes(packet.visibility) && typeof packet.owner==="string" && packet.owner.trim(), "Missing independent assessment for week " + week.week);
    insist(core.stable(Object.keys(packet.probes).sort())===core.stable(labels.sort()),"Incomplete private assessor coverage for week " + week.week);
    return Object.fromEntries(labels.map(id=>{
      const probe=packet.probes[id];
      insist(probe && typeof probe.spec==="string" && probe.spec.trim() && /^[A-Za-z_][A-Za-z0-9_]*$/.test(probe.entrypoint) && !functions.includes(probe.entrypoint),"Invalid public assessment specification " + id);
      functions.push(probe.entrypoint);
      // Validate every oracle before any worker gets a request.
      core.evaluateCases(probe.cases,probe.cases.map(c=>Object.hasOwn(c,"expected")?c.expected:c.any_of?.[0]));
      return [id,{spec:probe.spec,entrypoint:probe.entrypoint}];
    }));
  }
  const candidateSchema={
    week:"active week number",action:"create|revise|supplement|remove|merge|move|keep|restore",reason:"evidence and alternative",
    notebooks:{main:"nbformat 4.5+ student notebook; further names are optional supplements"},
    teacher:"separate nbformat 4.5+ teacher notebook implementing named Python functions; student notebooks never import it",
    route:{units:[{cells:["main/markdown-cell-id"],tier:"class|homework|conditional",minutes:"integer",trigger:"required for conditional",returns:"student cell required for conditional"}]},
    provided_example_guidance:"Optional route.provided_examples entries {cell,alternative,reason} justify a supplied demonstration inside a required unit. The independent mandatory alternative must work without the later tool. A required exercise or a downstream compulsory use cannot be exempted.",
    transfer:{principle:"main/explanation",prompt:"main/independent-prompt",solution:"teacher/reference",rationale:"decision a reader has to make"},
    edits:"On revisions, map changed notebook names to {actions:[{kind,before:[cell IDs],after:[cell IDs],reason,alternative,postcondition}],routes:{capability:{before:[IDs],after:[IDs]}}}; explicitly bind retired notebooks to successor student cells in retired.",
    coverage:[{obligation:"exact topic.mode from required list",teaching:["main/explanation"],assessment:["main/work"],solution:"teacher/reference for practical",sources:["source-id"]}]
  };
  function nextFailure(state, evidence) {
    return {...state,phase:"author",attempt:state.attempt+1,feedback:evidence};
  }
  async function runCourse(io, selection, options) {
    const {course, digest, ledger, skills, sources, config, suites}=io;
    insist(Number.isSafeInteger(options.calls) && (options.calls>0 || (options.inspect && options.calls===0)) && Number.isSafeInteger(options.attempts) && options.attempts>0,"Positive finite worker budgets required");
    insist(config.author && config.reviewer && config.author!==config.reviewer,"Distinct author and reviewer roles are required");
    insist(selection.length && selection.every(w=>course.order.includes(w)), "Unknown selected week");
    const requested=new Set();
    function add(w){if(requested.has(w))return;for(const p of course.weeks[w].prerequisites)add(p);requested.add(w);}
    selection.forEach(add);
    let calls=0;
    const bound={},active={},reasons={};
    for(const weekNum of course.order.filter(w=>requested.has(w))) {
      const week=course.weeks[weekNum], unavailable=week.prerequisites.filter(w=>!active[w]);
      if(unavailable.length){reasons[weekNum]="prerequisites "+unavailable.join(",");continue;}
      let suite=suites[weekNum];
      if(io.needsSuite && await io.needsSuite(week,suite)){
        if(options.inspect||calls+2>options.calls){reasons[weekNum]="independent assessment pending";continue;}
        calls+=2;
        try{suite=await io.prepareSuite(week);suites[weekNum]=suite;}
        catch(e){reasons[weekNum]="assessment: "+String(e.message);continue;}
      }
      let probes;
      try {
        probes=publicOracles(week,suite);
        insist(suite.owner!==config.author,"Author owns private assessment");
        if(suite.visibility==="private"){
          const v=suite.verification;
          insist(v && typeof v.reviewer==="string" && v.reviewer.trim() && v.reviewer!==suite.owner && v.reviewer!==config.author &&
            typeof v.finding==="string" && v.finding.trim() && /^[0-9a-f]{64}$/.test(v.answer_hash) && v.case_hash===await digest(suite.probes), "Private suite lacks a current independent verification");
        }
      }
      catch(error){reasons[weekNum]=String(error.message);continue;}
      const references=Object.fromEntries(week.sources.map(id=>[id,sources[id]]));
      const deps=Object.fromEntries(week.prerequisites.map(w=>[w,{hash:active[w].hash,input:active[w].input}]));
      const preset=io.restore?.[weekNum]??null;
      const imported=io.baselines?.[weekNum]??null;
      const context={version:io.version,scope:io.scope,week,references,deps,skills,config,suite,restore:preset,imported:imported?.digest??null};
      const key=await digest(context);
      const priorMaterial=Object.fromEntries(week.prerequisites.map(n=>[n,{hash:active[n].hash,notebooks:active[n].candidate.notebooks,transfer:active[n].candidate.transfer}]));
      bound[weekNum]=key;
      const head=await ledger.head(weekNum);
      if(head && head.input===key){
        insist(await digest(head.candidate)===head.hash,"Corrupt accepted candidate");
        active[weekNum]=head;continue;
      }
      if(options.inspect){reasons[weekNum]=(await ledger.read(key))?.phase??"not_started";continue;}
      const previous=head?.candidate??imported?.candidate??null;
      const pinned=head?.hash??null;
      let state=await ledger.read(key)??{week:weekNum,phase:"ground",attempt:1,pinned,revision:0};
      if(state.pinned!==pinned){reasons[weekNum]="baseline changed; replan before resuming";continue;}
      const save=async(next,kind,metadata={},accepted=null)=>{
        const updated={...next,revision:state.revision+1};
        await ledger.save(key,state.revision,updated,{week:weekNum,kind,attempt:state.attempt,...metadata},accepted);
        state=updated;
      };
      while(!["accepted","uncertain","stopped"].includes(state.phase)){
        if(state.attempt>options.attempts){await save({...state,phase:"stopped"},"attempt_limit");break;}
        if(calls>=options.calls)break;
        const id=key+"/"+state.attempt+"/"+state.phase;
        if(state.phase==="ground"){
          const request={role:"ground",worker_id:config.reviewer,week,sources:references,skills:skills.reviewer,
            instructions:"Before seeing any manuscript, inspect the cited external source evidence and weekly curriculum. Return {verdict:ready|uncertain,demands:[{id,sources:[...],decision,minimum,ceiling,counterexample,later_use}]}. Explain which later registered decision uses the principle. Infer prerequisites or missing external decisions even if absent from the planned lesson. Prefer original task input, output and scoring units; require no direct domestic question when only a precursor is supported. Scope domestic obligations and international examples separately. Use uncertain for insufficient evidence."};
          calls++;
          const basis=await io.worker(config.reviewer,request,id);
          insist(basis && ["ready","uncertain"].includes(basis.verdict) && Array.isArray(basis.demands),"Invalid source-grounding response");
          if(basis.verdict==="uncertain"){await save({...state,phase:"uncertain",basis},"uncertain_sources");break;}
          const ids=new Set();
          for(const d of basis.demands){insist(/^[A-Za-z0-9_-]{1,60}$/.test(d.id) && !ids.has(d.id) && Array.isArray(d.sources) && d.sources.length && d.sources.every(s=>week.sources.includes(s)) && [d.decision,d.minimum,d.ceiling,d.counterexample,d.later_use].every(t=>typeof t==="string"&&t.trim()),"Ungrounded or ambiguous demand");ids.add(d.id);}
          insist(ids.size>0,"No source-grounded demand");
          await save({...state,phase:"author",basis},"grounded",{demands:basis.demands.map(d=>d.id)});
        }else if(state.phase==="author"){
          const actionInstruction=previous
            ? "Use keep for unchanged notebooks or a revision action for changes. Compare edits to accepted_baseline."
            : "Use create for this blank baseline, including retries after feedback.";
          const request={role:"author",worker_id:config.author,week, sources:references,prerequisites:deps,
            skills:skills.author,prerequisite_material:priorMaterial,previous:state.candidate??previous,accepted_baseline:previous,
            feedback:state.feedback??null,required:core.obligations(week),public_probes:probes,frozen_demands:state.basis.demands,schema:candidateSchema,
            instructions:"Write Korean student materials for the entire registered week and separate teacher answers. Use the preceding notebooks and next_uses to teach the actual decision and reasoning. Explain what the representation preserves or loses, work through a small calculation or algorithm where relevant, and ask for a reasoned choice on fresh conditions. Preserve official obligations and learner time, mark adaptations. Keep hidden answers out of student work. The student's independent prompt must leave the decision to the student even when the teacher probe interface specifies an algorithm. Use direct explanations; an analogy cannot substitute for the operation and its conditions. Return one JSON candidate. "+actionInstruction+" Check each required activity against the scheduled tools in week.tool_prerequisites; provide an independent earlier-method solution when demonstrating an advanced tool. The public transfer interface is one calibration probe, not the entire lesson."};
          calls++;
          let candidate;
          if(preset){const old=await ledger.history(weekNum,preset);insist(old && old.hash===preset && previous,"Invalid restore target");candidate={...old.candidate,action:"restore",reason:"Restore previously accepted "+preset+" and independently verify again"};}
          else candidate=await io.worker(config.author,request,id);
          let validation;
          try{validation=core.validateCandidate(week,candidate,previous);}
          catch(error){
            const evidence=error.tool_prerequisites ? {tool_prerequisites:error.tool_prerequisites} : {};
            await save(nextFailure({...state,candidate},String(error.message)),"invalid_candidate",{reason:String(error.message),...evidence});continue;
          }
          if(io.checkEdit && previous && !["keep","restore"].includes(candidate.action)){
            const diff=await io.checkEdit(previous,candidate,id+"/diff");
            if(!diff.ok){await save(nextFailure({...state,candidate},diff.reason),"invalid_edit",{reason:diff.reason});continue;}
          }
          const hash=await digest(candidate);
          const contentHash=await digest([candidate.notebooks,candidate.teacher,candidate.route,candidate.coverage,candidate.transfer]);
          if(state.lastRejected===contentHash){await save({...state,phase:"stopped"},"repeated_rejection");break;}
          await save({...state,phase:"kernel",candidate,hash,contentHash,validation},"authored",{hash});
        }else if(state.phase==="kernel"){
          const input=Object.fromEntries(Object.entries(suite.probes).map(([id,p])=>[id,{entrypoint:p.entrypoint,inputs:p.cases.map(c=>c.input)}]));
          calls++;
          const execution=await io.kernel(state.candidate,input,id);
          let checks={};
          if(execution?.ok){
            insist(core.stable(Object.keys(execution.output).sort())===core.stable(Object.keys(input).sort()),"Incomplete kernel result");
            checks=Object.fromEntries(Object.entries(suite.probes).map(([id,p])=>[id,core.evaluateCases(p.cases,execution.output[id])]));
          }
          const failures=Object.entries(checks).filter(([,v])=>!v.passed).map(([id])=>id);
          if(!execution?.ok||failures.length){
            const feedback=execution?.ok?"A fresh case failed for "+failures.join(", "):"Notebook execution failed";
            await save(nextFailure({...state,lastRejected:state.contentHash},feedback),"execution_failed",{hash:state.hash,checks,diagnostic:execution?.diagnostic??null});continue;
          }
          await save({...state,phase:"review",checks},"executed",{hash:state.hash,checks});
        }else if(state.phase==="review"){
          const request={role:"reviewer",worker_id:config.reviewer,week,sources:references,skills:skills.reviewer,
            candidate:state.candidate,candidate_hash:state.hash,frozen_demands:state.basis.demands,prerequisite_material:priorMaterial,previous,
            tool_prerequisites:state.validation.tool_prerequisites??null,required_checks:[...core.reviewKeys(week),...core.obligations(week),...state.basis.demands.map(d=>"demand."+d.id)],
            instructions:"Independently review only the cited sources, prerequisite material and candidate. For every check cite existing cell references and a concrete finding. When tool_prerequisites is present, independently follow the compulsory work from explanation to the assessment on new input. Cite the transfer principle, prompt and all review_cells. For each review cell provide checks.tool_prerequisites.decisions[ref] = {disposition:uses_prior_only|example_only|requires_later|unresolved,reason:string}. Check learner instructions, links, provided demonstrations and executable alternatives against the week and its prerequisites. A general scope pass, a working teacher reference or the availability of a library on the machine cannot justify expecting a later tool. For each official obligation cite both its teaching and assessment. For representation, independent_task and depth_floor cite the transfer principle and independent prompt. State which change of viewpoint is necessary, with a direct example or counterexample; reject solutions cued by a gratuitous analogy. Judge the minimum explanation and the point at which more theory belongs in a later week. Test whether the task gives away the decision, accepts equivalent valid approaches, and still works on a different problem. Compare retention, revision and conditional supplementation, and name which later objective depends on the choice. Use {candidate_hash,reviewer,verdict,checks:{name:{verdict,cells:[...],finding}}}. Verdicts: pass, revise, uncertain. Do not infer student results."};
          calls++;
          const review=await io.worker(config.reviewer,request,id);
          const verdict=core.checkReview(week,state.candidate,review,state.hash,config,state.basis.demands.map(d=>"demand."+d.id),state.validation.tool_prerequisites);
          if(verdict==="uncertain"){await save({...state,phase:"uncertain",review},"unresolved_review",{hash:state.hash,review});break;}
          if(verdict==="revise"){const findings=Object.entries(review.checks).filter(([,v])=>v.verdict!=="pass").map(([k,v])=>[k,v.cells,v.finding]);
            await save(nextFailure({...state,lastRejected:state.contentHash},findings),"rejected",{hash:state.hash,review});continue;}
          const accepted={week:weekNum,input:key,hash:state.hash,candidate:state.candidate,dependencies:deps,
            status:"accepted",visibility:suite.visibility,previous:pinned};
          if(io.isCurrent && !(await io.isCurrent(weekNum,key,deps,context))){reasons[weekNum]="live source or prerequisite changed";break;}
          await save({...state,phase:"accepted"},"accepted",{hash:state.hash,review},accepted);
          active[weekNum]=accepted;
        }else throw new Error("Unknown journal phase " + state.phase);
      }
      if(!active[weekNum])reasons[weekNum]??=state.phase;
    }
    const result=core.reportCourse(course,active,bound);
    const allPrivate=Object.values(active).every(a=>a.visibility==="private");
    return {...result,scope:[...requested],calls,reasons,eligibility:result.status==="complete" && allPrivate && io.actualWorkers===true?"independent_reviews_recorded":"development_or_partial"};
  }
  return {runCourse,publicOracles,candidateSchema};
}

export const {runCourse, publicOracles} = makeCourseRunner(courseCore);
