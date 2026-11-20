import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { appendFile, copyFile, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { courseCore } from "../tools/course_core.mjs";
import { runCourse, publicOracles } from "../tools/course_run.mjs";
import { prepareWeek } from "../tools/course_assess.mjs";
import { openLedger } from "../tools/course_ledger.mjs";
import { loadBaselines, loadCourse } from "../tools/course.mjs";

function portableCourseTestkit(core,runner,base,hash) {
  const clone=v=>JSON.parse(JSON.stringify(v));
  function exact(a,b,name){if(core.stable(a)!==core.stable(b))throw new Error(name+" expected "+JSON.stringify(b)+" observed "+JSON.stringify(a));}
  function fail(fn,pattern,name){try{fn();}catch(e){if(pattern.test(e.message))return;throw e;}throw new Error("Expected failure: "+name);}
  function note(cells){return {nbformat:4,nbformat_minor:5,metadata:{},cells};}
  function cell(id,source,code=false){return code?{id,cell_type:"code",source,metadata:{},outputs:[],execution_count:null}:{id,cell_type:"markdown",source,metadata:{}};}
  function sample(week,obligations,sources,previous=null) {
    const result={
      week:week.week,action:previous?"keep":"create",reason:"Instrumented fixture under independent replay.",
      notebooks:{main:note([cell("principle","A source-linked development explanation."),cell("prompt","Make an independent choice on unseen input."),cell("work","# student workspace")])},
      teacher:note([cell("answer","def solve(value):\n    return value['x']\n",true)]),
      transfer:{principle:"main/principle",prompt:"main/prompt",solution:"teacher/answer",rationale:week.decision},
      coverage:obligations.map(k=>({obligation:k,teaching:["main/principle"],assessment:["main/work"],solution:"teacher/answer",sources:[sources[0]]})),
      route:{units:[{cells:["main/principle","main/prompt","main/work"],tier:"class",minutes:90}]}
    };
    result.notebooks.main.cells[2]=cell("work","# student workspace",true);
    return result;
  }
  function makeReview(req,override={}) {
    const checks=Object.fromEntries(req.required_checks.map(k=>[k,{verdict:"pass",finding:"Development-only simulated judgment.",cells:["main/principle","main/prompt","main/work"]}]));
    Object.assign(checks,override);
    const vs=Object.values(checks);
    return {candidate_hash:req.candidate_hash,reviewer:req.worker_id,checks,verdict:vs.some(v=>v.verdict==="revise")?"revise":vs.some(v=>v.verdict==="uncertain")?"uncertain":"pass"};
  }
  function memoryLedger() {
    const jobs=new Map(),headMap=new Map(),versions=new Map(),events=[];
    return {events,head:w=>headMap.get(w),read:k=>jobs.get(k),history:(w,h)=>versions.get(w+":"+h),
      save(k,from,state,event,accepted){
        if((jobs.get(k)?.revision??0)!==from)throw new Error("Concurrent modification");
        if(accepted){if((headMap.get(state.week)?.hash??null)!==accepted.previous)throw new Error("Baseline changed");
          headMap.set(state.week,clone(accepted));versions.set(state.week+":"+accepted.hash,clone(accepted));}
        jobs.set(k,clone(state));events.push({...event,key:k});
      }};
  }
  function makeIO() {
    const io={course:clone(base.course),sources:clone(base.sources),skills:{author:"test-writer-v1",reviewer:"test-reviewer-v1"},scope:{year:2027},digest:hash,version:"instrumented-test",actualWorkers:false,
      config:{author:"writer",reviewer:"reader"},ledger:memoryLedger(),suites:{},calls:[],isCurrent:()=>true};
    for(const w of io.course.order){
      const keys=["transfer",...core.obligations(io.course.weeks[w]).filter(k=>k.endsWith(".practical"))];
      io.suites[w]={owner:"independent test fixture",visibility:"development",probes:Object.fromEntries(keys.map((name,i)=>[name,{entrypoint:"solve_"+i,spec:"Return the JSON field x unchanged for the wiring test",
        cases:[{id:"normal",kind:"normal",input:{x:2},expected:2},{id:"same",base:"normal",kind:"invariant",input:{x:2,tag:"changed"},expected:2},{id:"different",base:"normal",kind:"sensitive",input:{x:4},expected:4}]}]))};
    }
    io.worker=async (who,req,key)=>{
      io.calls.push([who,req.week.week,key]);
      if(JSON.stringify(req).includes('"expected":'))throw new Error("Private answer leaked into worker context");
      if(req.role==="ground")return {verdict:"ready",demands:[{id:"public-decision",sources:[req.week.sources[0]],decision:req.week.decision,minimum:req.week.minimum,ceiling:req.week.ceiling,counterexample:req.week.transfer,later_use:"See registered dependencies"}]};
      return who===io.config.author?sample(req.week,req.required,req.week.sources,req.accepted_baseline):makeReview(req);
    };
    io.kernel=async(candidate,probes,key)=>{
      io.calls.push(["kernel",candidate.week,key]);return {ok:true,output:Object.fromEntries(Object.entries(probes).map(([k,p])=>[k,p.inputs.map(x=>x.x)]))};
    };
    return io;
  }
  async function runTests(assessment) {
    const report=[];
    async function check(name,fn){await fn();report.push(name);}
    const opts={calls:100,attempts:3};const all=base.course.order,first=all[0];
    await check("cold start and repeat with real ten-week contract",async()=>{
      const io=makeIO();const r=await runner.runCourse(io,all,opts);
      exact(r.completed,all,"completed weeks");exact(r.verified_obligations.length,84,"obligations");
      exact([r.calls,r.eligibility],[40,"development_or_partial"],"real work separation");
      const repeat=await runner.runCourse(io,all,opts);exact(repeat.calls,0,"duplicate executions");
      exact(io.ledger.events.filter(e=>e.kind==="accepted").length,10,"acceptance count");
    });
    await check("crash after persisted candidate, restart and no duplicate acceptance",async()=>{
      const io=makeIO(),kernel=io.kernel;io.kernel=()=>{throw new Error("injected interruption");};
      let crashed=false;try{await runner.runCourse(io,[first],opts);}catch(e){crashed=e.message==="injected interruption";}
      exact(crashed,true,"fault reached");io.kernel=kernel;const recovered=await runner.runCourse(io,[first],opts);
      exact([recovered.completed,io.calls.filter(c=>c[0]==="writer").length],[[first],1],"resume phase");
    });
    await check("budget pauses at exact stage and resumes",async()=>{
      const io=makeIO();const start=await runner.runCourse(io,[first],{calls:2,attempts:3});
      exact([start.completed,start.reasons[first]],[[],"kernel"],"budget");
      const resumed=await runner.runCourse(io,[first],opts);exact(resumed.calls,2,"remaining stages");
    });
    await check("missing oracle halts without worker activity",async()=>{
      const io=makeIO();delete io.suites[first];const r=await runner.runCourse(io,all,opts);
      exact([r.completed.length,r.calls],[0,0],"missing input");
    });
    await check("correctly bound source change reopens only dependent weeks",async()=>{
      const io=makeIO();await runner.runCourse(io,all,opts);
      const id=io.course.weeks[8].sources.find(x=>x==="concepts");io.sources[id].text+=" actual correction";
      const status=await runner.runCourse(io,all,{...opts,inspect:true,calls:0});
      exact(status.pending,[8,9,10],"source impact");
      const again=await runner.runCourse(io,all,opts);exact([again.calls,again.completed.length],[12,10],"selective replay");
      const distinct=io.ledger.events.filter(e=>e.kind==="accepted"&&e.week===8);exact(distinct.length,2,"review history");
    });
    await check("mid-run source change prevents adoption",async()=>{
      const io=makeIO();io.isCurrent=()=>false;const r=await runner.runCourse(io,[first],opts);
      exact([r.completed.length,io.ledger.events.some(e=>e.kind==="accepted")],[0,false],"stale");
    });
    await check("uncertainty stays open and blocks dependents",async()=>{
      const io=makeIO(),w=io.worker;
      io.worker=(who,q,id)=>q.role==="reviewer"?makeReview(q,{scope:{verdict:"uncertain",cells:["main/principle"],finding:"Scope unresolved"}}):w(who,q,id);
      const r=await runner.runCourse(io,all,opts);exact([r.completed,r.reasons[first]],[[],"uncertain"],"unknown not approved");
    });
    await check("repeated cosmetic response to failed independent probe stops",async()=>{
      const io=makeIO();
      io.kernel=async(_c,probes)=>({ok:true,output:Object.fromEntries(Object.entries(probes).map(([k,p])=>[k,p.inputs.map(()=>2)]))});
      const r=await runner.runCourse(io,[first],opts);exact(r.completed.length,0,"mutant accepted");
      exact(io.ledger.events.map(e=>e.kind),["grounded","authored","execution_failed","repeated_rejection"],"no-op stop");
    });
    await check("new grading rejects malformed controls and preserves other valid answers",()=>{
      const suite=[{id:"a",kind:"normal",input:{x:1},any_of:[[1],[2]]},{id:"b",base:"a",kind:"invariant",input:{x:1,order:2},any_of:[[1],[2]]},{id:"c",base:"a",kind:"sensitive",input:{x:2},expected:[3]}];
      exact(core.evaluateCases(suite,[[2],[1],[3]]).passed,true,"alternative valid");
      exact(core.evaluateCases(suite,[[2],[2],[2]]).passed,false,"sensitivity");
      fail(()=>core.evaluateCases(suite.map((c,i)=>i===1?{...c,any_of:[[3]]}:c),[[1],[1],[1]]),/Control disagrees/,"mislabelled control");
    });
    await check("teacher key separation, scope, workload and deletion proof",()=>{
      const w=base.course.weeks[first],ok=sample(w,core.obligations(w),w.sources);
      core.validateCandidate(w,ok,null);
      const missing=clone(ok);missing.coverage.pop();fail(()=>core.validateCandidate(w,missing,null),/obligation/,"missing scope");
      const leak=clone(ok);leak.route.units[0].cells.push("teacher/answer");fail(()=>core.validateCandidate(w,leak,null),/route unit/,"teacher leak");
      const overload=clone(ok);overload.route.units[0].minutes=121;fail(()=>core.validateCandidate(w,overload,null),/workload/,"overload");
      const fake=clone(ok);fake.action="remove";fake.notebooks.main.cells[0].source+=" new adjective";fail(()=>core.validateCandidate(w,fake,ok),/No cell removed/,"cosmetic removal");
      const localized=clone(ok);localized.action="supplement";localized.notebooks.repair=note([cell("why","conditional prerequisite")]);
      localized.route.units.push({tier:"conditional",minutes:10,cells:["repair/why"],returns:"main/work",trigger:"cannot align source IDs in the entry task"});
      core.validateCandidate(w,localized,ok);
      const back=clone(ok);back.action="remove";core.validateCandidate(w,back,localized);
      delete localized.route.units[1].returns;fail(()=>core.validateCandidate(w,localized,ok),/return cell/,"unconnected supplement");
    });
    await check("review requires an independent actor, exact version and located evidence",()=>{
      const w=base.course.weeks[first],cand=sample(w,core.obligations(w),w.sources),h=hash(cand);
      const ref={candidate_hash:h,worker_id:"reader",required_checks:[...core.reviewKeys(w),...core.obligations(w)]};
      const r=makeReview(ref),roles={author:"writer",reviewer:"reader"};
      core.checkReview(w,cand,r,h,roles);
      fail(()=>core.checkReview(w,cand,r,h+"!",roles),/Stale/,"stale review");
      fail(()=>core.checkReview(w,cand,r,h,{author:"reader",reviewer:"reader"}),/independent/,"self approval");
      r.checks[core.obligations(w)[0]].cells=["main/work"];fail(()=>core.checkReview(w,cand,r,h,roles),/missed/,"nominal path");
    });
    await check("stop after grounding refusal and before exposing any manuscript",async()=>{
      const io=makeIO();io.worker=async(w,r)=>{if(r.role!=="ground"||r.candidate||r.previous)throw new Error("author context leaked");return {verdict:"uncertain",demands:[]};};
      const result=await runner.runCourse(io,[first],opts);exact([result.calls,result.reasons[first]],[1,"uncertain"],"blind freeze");
    });
    await check("crash before adoption and optimistic duplicate prevention",async()=>{
      const io=makeIO(),original=io.ledger.save;let crash=true;
      io.ledger.save=(...args)=>{if(crash && args[3].kind==="accepted"){crash=false;throw Error("before adoption");}return original(...args);};
      let caught=false;try{await runner.runCourse(io,[first],opts);}catch(e){caught=e.message==="before adoption";}
      exact(caught,true,"crash occurred");exact(io.ledger.head(first)??null,null,"no partial head");
      await runner.runCourse(io,[first],opts);exact(io.ledger.events.filter(x=>x.kind==="accepted").length,1,"adopt once");
      const key=io.ledger.head(first).input;
      fail(()=>io.ledger.save(key,0,{week:first,revision:1},{kind:"old write"},null),/Concurrent/,"stale writer");
    });
    await check("restore previously accepted content and recheck it, keep both histories",async()=>{
      const io=makeIO();await runner.runCourse(io,[first],opts);const a=io.ledger.head(first);
      const worker=io.worker;
      io.worker=async(w,q,id)=>{const out=await worker(w,q,id);if(q.role==="author"&&q.accepted_baseline){out.action="revise";out.notebooks.main.cells[0].source+=" actual evidence";}return out;};
      io.suites[first].study_revision=2;await runner.runCourse(io,[first],opts);const b=io.ledger.head(first);
      exact(a.hash===b.hash,false,"revision did not advance");io.restore={[first]:a.hash};
      const again=await runner.runCourse(io,[first],opts);const c=io.ledger.head(first);
      exact([again.completed,c.candidate.action],[[first],"restore"],"verified restoration");
      exact(c.candidate.notebooks,a.candidate.notebooks,"restored bytes");
      exact([io.ledger.history(first,a.hash).hash,io.ledger.history(first,b.hash).hash],[a.hash,b.hash],"retained versions");
    });
    await check("optional branch cannot discharge a compulsory official goal",()=>{
      const w=base.course.weeks[first],cand=sample(w,core.obligations(w),w.sources);
      cand.notebooks.repair=note([cell("optional","optional prerequisite")]);
      cand.route.units.push({tier:"conditional",minutes:7,cells:["repair/optional"],returns:"main/work",trigger:"remediation only"});
      cand.coverage[0].teaching=["repair/optional"];
      fail(()=>core.validateCandidate(w,cand,null),/Unbound obligation/,"compulsory scope in optional work");
    });
    await check("unchanged healthy baseline requires no new manuscript and legacy baseline is read-only",async()=>{
      const io=makeIO(),w=io.course.weeks[first],baseline=sample(w,core.obligations(w),w.sources);
      io.baselines={[first]:{digest:hash(baseline),candidate:baseline}};
      const before=core.stable(baseline);
      const result=await runner.runCourse(io,[first],opts);exact(result.completed,[first],"baseline completion");
      exact(io.ledger.head(first).candidate.action,"keep","unchanged decision");
      exact(core.stable(baseline),before,"baseline mutated");
    });
    await check("auto-preparation leaves a blocked assessment ungraded",async()=>{
      const io=makeIO();delete io.suites[first];io.needsSuite=(_w,s)=>!s;io.prepareSuite=async()=>{throw new Error("blind solution mismatch");};
      const res=await runner.runCourse(io,[first],opts);exact([res.completed,res.calls],[[],2],"assessment failure");
      exact(io.calls.length,0,"unaudited manuscript created");
    });
    await check("student route rejects a supplement that leads to a teacher key or to itself",()=>{
      const w=base.course.weeks[first],candidate=sample(w,core.obligations(w),w.sources);
      candidate.notebooks.remedy=note([cell("why","Reread the coordinate labels.")]);
      const branch={tier:"conditional",minutes:5,trigger:"if the returned ID is a row index",cells:["remedy/why"],returns:"main/work"};
      candidate.route.units.push(branch);
      core.validateCandidate(w,candidate,null);
      for(const dest of ["teacher/answer","remedy/why"]){
        branch.returns=dest;
        fail(()=>core.validateCandidate(w,candidate,null),/return to the mandatory/,"broken optional route");
      }
    });
    await check("explanation precedes required transfer and official assessment",()=>{
      const w=base.course.weeks[first],candidate=sample(w,core.obligations(w),w.sources);
      candidate.route.units[0].cells=["main/prompt","main/principle","main/work"];
      fail(()=>core.validateCandidate(w,candidate,null),/private solution/,"early transfer");
      candidate.route.units[0].cells=["main/work","main/principle","main/prompt"];
      fail(()=>core.validateCandidate(w,candidate,null),/Unbound obligation/,"assessment before teaching");
    });
    await check("equivalent answers form an unordered set and sensitivity distinguishes all accepted outputs",()=>{
      const cases=[{id:"base",kind:"normal",input:1,any_of:[3,2]},{id:"swap",base:"base",kind:"invariant",input:2,any_of:[2,3]},
        {id:"changed",base:"base",kind:"sensitive",input:3,expected:4}];
      exact(core.evaluateCases(cases,[2,3,4]).passed,true,"alternative order");
      const overlap=clone(cases);overlap[2].any_of=[3,4];delete overlap[2].expected;
      fail(()=>core.evaluateCases(overlap,[2,2,3]),/Control disagrees/,"constant predictor");
      const missing=clone(cases);missing.push({id:"unregistered",kind:"madeup",input:4,expected:2});
      fail(()=>core.evaluateCases(missing,[2,2,4,2]),/Unknown independent/,"unregistered case kind");
    });
    async function blind(callMode) {
      const io=makeIO(), w=io.course.weeks[first], original=io.suites[first];io.config.examiner="exam-writer";
      const seen=[];
      const call=async(who,request)=>{
        seen.push([who,request.role]);
        if(request.role==="examiner")return {probes:clone(original.probes)};
        exact(Object.values(request.questions).every(q=>Object.keys(q).sort().join()==="entrypoint,inputs,spec"),true,"blind grading view");
        const answers=Object.fromEntries(Object.entries(request.questions).map(([id,q])=>[id,q.inputs.map(v=>v.x)]));
        if(callMode==="wrong")Object.values(answers)[0][0]=-200;
        return {verdict:"pass",finding:"Examiner-independent hand calculation on changed inputs.",answers};
      };
      const suite=await assessment.prepareWeek(w,io.sources,io.skills.reviewer,io.config,call,hash,"private");
      exact(seen,[["exam-writer","examiner"],["reader","assessor"]],"separate frozen and blind calls");
      return {suite,io};
    }
    await check("private assessment is frozen by an examiner and solved blind before authoring",async()=>{
      const {suite,io}=await blind("correct");
      io.suites[first]=suite;const result=await runner.runCourse(io,[first],opts);
      exact(result.completed,[first],"verified private suite");exact(result.eligibility,"development_or_partial","test service");
    });
    await check("independent disagreement and late hidden-key tampering block authoring",async()=>{
      let rejected=false;try{await blind("wrong");}catch(e){rejected=/disagreed/.test(e.message);}
      exact(rejected,true,"independent disagreement");
      const {suite,io}=await blind("correct");io.suites[first]=suite;
      suite.probes.transfer.spec+=" late alteration";
      const result=await runner.runCourse(io,[first],opts);
      exact([result.completed,result.calls],[[],0],"tampered private suite");
      exact(/current independent verification/.test(result.reasons[first]),true,"tampering reason");
    });
    await check("grounded work receives the later curricular decisions that depend on it",async()=>{
      const io=makeIO(),own=io.worker,expected=io.course.order.filter(n=>io.course.weeks[n].prerequisites.includes(first));
      if(!expected.length)throw new Error("Real prerequisite has no successor");
      io.worker=(who,req,id)=>{
        exact(req.week.next_uses.map(row=>row.week),expected,"downstream placements");
        exact(req.week.next_uses.every(row=>Boolean(row.minimum&&row.transfer&&row.decision)),true,"missing later decision");
        return own(who,req,id);
      };
      exact((await runner.runCourse(io,[first],opts)).completed,[first],"connected curricular run");
    });
    await check("new course registration with different week numbers and roles uses the same runner",async()=>{
      const design={weeks:[
        {week:41,prerequisites:[],sources:["original"],decision:"제출 단위를 확인한다.",minimum:"입력 한 행과 출력 한 행을 연결한다.",ceiling:"후속 학습은 다음 단원에 둔다.",transfer:"새 순서에서도 대응한다.",interface:"f(x) → output"},
        {week:73,prerequisites:[41],sources:["original"],decision:"조건부 비용을 계산한다.",minimum:"같은 결정 규칙을 새 입력에 적용한다.",ceiling:"전체 모형 유도는 범위 밖이다.",transfer:"비용 변화에 따른 결정을 비교한다.",interface:"f(x) → output"}]};
      const budget={theory_minutes:20,noncoding_minutes:20,coding_minutes:80,required_self_study_hours:[1,2]};
      const contract={class_minutes:120,weeks:design.weeks.map(w=>({week:w.week,...budget})),
        topics:[{id:"unseen-unit",name:"제출 단위",theory:true,practical:false,scheduled_weeks:[41]},
          {id:"unseen-cost",name:"의사결정 비용",theory:false,practical:true,scheduled_weeks:[73]}]};
      const sources={original:{locator:"fixture:new-curriculum",text:"Registered transfer-only test curriculum."}};
      const course=core.compile(contract,design,sources,{41:"Plan A",73:"Plan B"});
      const standalone=portableCourseTestkit(core,runner,{course,sources},hash).makeIO();
      const result=await runner.runCourse(standalone,[73],opts);
      exact(result.completed,[41,73],"generic routing without week 1");exact(result.verified_obligations,["unseen-cost.practical","unseen-unit.theory"],"new obligations");
    });
    await check("an unplanned source demand is frozen before authoring and can reject a numerically working reference",async()=>{
      const io=makeIO(),original=io.worker;
      const source=io.course.weeks[first].sources.find(id=>id==="antique");
      if(!source)throw new Error("Expected original public problem association");
      const key="demand.unknown-label",decision="원문의 미상 라벨 0과 제출 가능한 두 클래스를 구분한다.";
      let authored=0,reviews=0;
      io.worker=async(who,req,id)=>{
        if(req.role==="ground")return {verdict:"ready",demands:[{id:"unknown-label",sources:[source],decision,minimum:"미상 행과 관찰 라벨 -1을 구별한다.",ceiling:"준지도 알고리즘 선택은 후속 단원에 둔다.",counterexample:"미상 행 하나가 늘어날 때 알려진 라벨의 표본 수는 그대로다.",later_use:"라벨로 계산할 손실의 분모를 고른다."}]};
        if(req.role==="author"){
          authored++;exact(req.frozen_demands[0].decision,decision,"new external requirement lost");
          const candidate=sample(req.week,req.required,req.week.sources,req.accepted_baseline);
          candidate.notebooks.main.cells[0].source=authored===1?"첫 열을 특징으로 옮긴다.":"미상 라벨 0을 가진 행도 특징을 가진다. 알려진 라벨로 손실을 계산할 때에는 -1과 +1인 행만 분모에 넣는다.";
          candidate.notebooks.main.cells[1].source=authored===1?"같은 표를 다시 옮기세요.":"훈련 라벨이 [0,-1,+1,0]이다. 미상 그림 한 장을 더 받으면 표의 행 수, 알려진 라벨로 계산할 손실의 분모, 제출 가능한 값 중 무엇이 달라지는지 근거를 쓰세요.";
          return candidate;
        }
        if(req.role==="reviewer"){
          reviews++;
          if(!req.required_checks.includes(key))throw new Error("Missing frozen criterion");
          if(reviews===1)return makeReview(req,{[key]:{verdict:"revise",cells:["main/principle","main/prompt"],finding:"입출력 구별과 미상 라벨에 대한 판단이 없다."}});
        }
        return original(who,req,id);
      };
      const result=await runner.runCourse(io,[first],opts);
      exact([result.completed,authored,reviews],[[first],2,2],"substantive revision");
      const events=io.ledger.events.map(e=>e.kind);
      exact(events.filter(k=>k==="executed").length,2,"both numerical trials had passed");
      exact(events.filter(k=>k==="rejected").length,1,"independent judgment rejected the first manuscript");
      exact(events.indexOf("grounded")<events.indexOf("authored"),true,"grounding before writing");
    });
    return report;
  }
  return {runTests,makeIO,makeReview,sample,note,cell};
}

const root=fileURLToPath(new URL("../",import.meta.url));
const contract=loadCourse(root,"curriculum/course-harness.json","curriculum/contract.json");
const digest=value=>createHash("sha256").update(courseCore.stable(value)).digest("hex");

test("registered course runs from a blank state and fails independent controls", async t => {
  const kit=portableCourseTestkit(courseCore,{runCourse,publicOracles},contract,digest);
  const results=await kit.runTests({prepareWeek});
  for(const name of results)t.diagnostic(name);
  assert.equal(results.length,25);
});

test("the Week 1 teacher guide reaches the author intact and a byte change reopens the week", async t => {
  const dir=await mkdtemp(join(tmpdir(),"course-week-guide-"));
  t.after(()=>rm(dir,{recursive:true,force:true}));
  const manifest=join(dir,"baseline.json"), main="activity.ipynb", guide="instructor.md";
  await copyFile(join(root,"lessons/week01/week01_integrated.ipynb"),join(dir,main));
  const original=await readFile(join(root,"lessons/week01/week01_integrated_teacher.md"));
  await writeFile(join(dir,guide),original);
  await writeFile(manifest,JSON.stringify({1:{notebooks:{main},teacher:guide}}));
  const kit=portableCourseTestkit(courseCore,{runCourse,publicOracles},contract,digest);
  const io=kit.makeIO(), worker=io.worker;
  io.baselines=loadBaselines(manifest,dir);
  let request;
  io.worker=async(who,req,id)=>{
    const reply=await worker(who,req,id);
    if(req.role==="author"){request=req;reply.action="revise";}
    return reply;
  };
  assert.deepEqual((await runCourse(io,[1],{calls:4,attempts:1})).completed,[1]);
  assert.match(request.instructions,/revision action/);
  assert.doesNotMatch(request.instructions,/use create/i);
  assert.deepEqual(request.previous,request.accepted_baseline);
  const baseline=request.accepted_baseline;
  assert.deepEqual(Object.keys(baseline.notebooks),["main"]);
  assert.deepEqual(baseline.teacher,{nbformat:4,nbformat_minor:5,metadata:{},cells:[
    {id:"teacher-guide",cell_type:"markdown",metadata:{},source:original.toString("utf8")}]});
  assert.deepEqual(baseline.provenance.teacher,{path:guide,sha256:createHash("sha256").update(original).digest("hex")});
  const inspect={inspect:true,calls:0,attempts:1}, originalDigest=io.baselines[1].digest;
  await appendFile(join(dir,guide),"\n");
  io.baselines=loadBaselines(manifest,dir);
  assert.notEqual(io.baselines[1].digest,originalDigest);
  assert.equal(io.baselines[1].candidate.teacher.cells[0].id,baseline.teacher.cells[0].id);
  assert.equal((await runCourse(io,[1],inspect)).reasons[1],"not_started");
  await writeFile(join(dir,guide),original);
  io.baselines=loadBaselines(manifest,dir);
  assert.equal(io.baselines[1].digest,originalDigest);
  assert.deepEqual((await runCourse(io,[1],inspect)).completed,[1]);
});

test("teacher imports distinguish UTF-8 text guides from historical notebooks", async t => {
  const dir=await mkdtemp(join(tmpdir(),"course-baseline-format-"));
  t.after(()=>rm(dir,{recursive:true,force:true}));
  const manifest=join(dir,"manifest.json"), main="worked.ipynb";
  const legacy={nbformat:4,nbformat_minor:2,metadata:{},cells:[
    {cell_type:"code",metadata:{},source:["print(3)\n"],execution_count:7,outputs:[{output_type:"stream",name:"stdout",text:"3\n"}]}]};
  await writeFile(join(dir,main),JSON.stringify(legacy));
  async function imported(teacher){
    await writeFile(manifest,JSON.stringify({37:{notebooks:{main},teacher}}));
    return loadBaselines(manifest,dir)[37].candidate;
  }
  const fromNotebook=await imported(main);
  for(const notebook of [fromNotebook.notebooks.main,fromNotebook.teacher]){
    assert.equal(notebook.nbformat_minor,5);
    assert.match(notebook.cells[0].id,/^legacy-/);
    assert.deepEqual(notebook.cells[0],{...legacy.cells[0],id:notebook.cells[0].id,outputs:[],execution_count:null});
  }
  assert.deepEqual(await imported(main),fromNotebook);
  assert.deepEqual(JSON.parse(await readFile(join(dir,main),"utf8")),legacy);
  const source="\uFEFFInstructor’s notes\r\n\r\n~~~python\r\nraise RuntimeError('literal text')\r\n~~~\r\n";
  for(const guide of ["field-notes.TXT","field-notes.markdown"]){
    await writeFile(join(dir,guide),source);
    const candidate=await imported(guide);
    assert.deepEqual(candidate.teacher.cells,[{id:"teacher-guide",cell_type:"markdown",metadata:{},source}]);
    assert.equal(candidate.provenance.teacher.sha256,createHash("sha256").update(Buffer.from(source)).digest("hex"));
  }
  for(const [name,content,error] of [
    ["notes.py","print(3)",/Unsupported teacher baseline format/],
    ["binary.txt","Notes\u0000end",/readable text/],
    ["invalid.md",Buffer.from([0xc3,0x28]),/valid UTF-8/],
    ["empty.md","\r\n\t",/readable text/],
    ["broken.ipynb","plain text",SyntaxError],
  ]){
    await writeFile(join(dir,name),content);
    await assert.rejects(imported(name),error);
  }
  assert.equal((await imported(undefined)).teacher.cells[0].id,"missing-key");
});

test("author instructions use create on a blank retry and revision actions after acceptance", async () => {
  const kit=portableCourseTestkit(courseCore,{runCourse,publicOracles},contract,digest);
  const io=kit.makeIO(), worker=io.worker, requests=[];
  io.worker=async(who,req,id)=>{
    const reply=await worker(who,req,id);
    if(req.role==="author"){
      requests.push(req);
      if(requests.length===1)reply.action="revise";
    }
    return reply;
  };
  const options={calls:6,attempts:2};
  assert.deepEqual((await runCourse(io,[1],options)).completed,[1]);
  assert.equal(requests.length,2);
  assert.equal(requests[0].previous,null);
  assert.equal(requests[1].previous.action,"revise");
  for(const req of requests){
    assert.equal(req.accepted_baseline,null);
    assert.match(req.instructions,/use create/i);
  }
  io.suites[1].revision=2;
  assert.deepEqual((await runCourse(io,[1],options)).completed,[1]);
  assert.equal(requests.length,3);
  assert.equal(requests[2].accepted_baseline.action,"create");
  assert.match(requests[2].instructions,/revision action/);
  assert.doesNotMatch(requests[2].instructions,/use create/i);
});

test("SQLite commits are durable, exclusive and reject stale updates",async()=>{
  const dir=await mkdtemp(join(tmpdir(),"koai-ledger-test-"));
  const dbPath=join(dir,"state.sqlite");
  let one,two,again;
  try{
    one=openLedger(dbPath);two=openLedger(dbPath);one.acquire();
    assert.throws(()=>two.acquire(),/owns this run/);
    assert.throws(()=>two.save("rogue",0,{week:1,revision:1},{kind:"rogue"}),/Lost/);
    assert.deepEqual(one.reserve("request","frozen"),{recorded:false});
    one.remember("request","frozen",{value:7});
    assert.deepEqual(one.reserve("request","frozen"),{recorded:true,response:{value:7}});
    assert.deepEqual(two.receipt("request","frozen"),{value:7});
    assert.throws(()=>two.receipt("request","changed"),/Frozen/);
    const a={week:1,hash:"h1",input:"first",status:"accepted",previous:null,dependencies:{}};
    one.save("first",0,{week:1,revision:1},{kind:"accepted"},a);
    assert.throws(()=>one.save("first",0,{week:1,revision:1},{kind:"racing"}),/concurrently/);
    const child={week:2,hash:"h2",input:"second",status:"accepted",previous:null,dependencies:{1:{hash:"h1",input:"old"}}};
    assert.throws(()=>one.save("child",0,{week:2,revision:1},{kind:"accepted"},child),/Prerequisite/);
    assert.equal(one.read("child"),null);
    assert.equal(one.events().length,1);
    one.reserve("interrupted","fingerprint");
    one.release();one.close();one=null;
    again=openLedger(dbPath);again.acquire();
    assert.deepEqual(again.head(1),a);assert.deepEqual(again.history(1,"h1"),a);
    child.dependencies[1].input="first";
    again.save("child",0,{week:2,revision:1},{kind:"accepted"},child);
    assert.equal(again.events().length,2);
    assert.throws(()=>again.reserve("interrupted","fingerprint"),/Uncertain external call/);
    assert.throws(()=>again.resolveCall({id:"interrupted",hash:"wrong",outcome:"absent",reason:"checked"}),/matching/);
    again.resolveCall({id:"interrupted",hash:"fingerprint",outcome:"recovered",response:{value:8},reason:"Recovered original service log"});
    assert.deepEqual(again.reserve("interrupted","fingerprint"),{recorded:true,response:{value:8}});
    assert.equal(again.pending().length,0);
  }finally{for(const db of [one,two,again])if(db)db.close();await rm(dir,{recursive:true,force:true});}
});


test("the normal author gate reopens a pre-policy week and preserves the premature-use rejection", async () => {
  const kit = portableCourseTestkit(courseCore, {runCourse, publicOracles}, contract, digest);
  const io = kit.makeIO();
  const worker = io.worker, current = io.course.weeks[1];
  io.course.weeks[1] = structuredClone(current);
  delete io.course.weeks[1].tool_prerequisites;
  let correct = false;
  io.worker = async (identity, request, id) => {
    const reply = await worker(identity, request, id);
    if (request.role === "author") {
      reply.notebooks.main.cells[2].source = correct
        ? "from sklearn.datasets import load_digits as examples\nvalues = examples().data"
        : "from sklearn.neighbors import NearestCentroid as Classifier\nmodel = Classifier()";
      if (correct && request.accepted_baseline) reply.action = "revise";
    }
    return reply;
  };
  const options = {calls:4, attempts:3};
  assert.deepEqual((await runCourse(io,[1],options)).completed,[1]);
  const former = io.ledger.head(1), kernelCalls = io.calls.filter(c => c[0] === "kernel").length;
  io.course.weeks[1] = current;
  assert.equal((await runCourse(io,[1],{calls:0,attempts:3,inspect:true})).reasons[1],"not_started");
  await runCourse(io,[1],{calls:2,attempts:3});
  assert.equal(io.calls.filter(c => c[0] === "kernel").length, kernelCalls);
  const rejection = io.ledger.events.findLast(e => e.kind === "invalid_candidate");
  assert.ok(rejection.tool_prerequisites.blocked.some(r => r.topic === "KOAI-04" && r.cell === "main/work"));
  assert.equal(io.ledger.head(1).hash, former.hash);
  correct = true;
  assert.deepEqual((await runCourse(io,[1],options)).completed,[1]);
  const accepted = io.ledger.head(1);
  assert.notEqual(accepted.hash, former.hash);
  assert.ok(io.ledger.history(1,former.hash));
  assert.equal((await runCourse(io,[1],options)).calls,0);

  io.course.weeks[8].budget.coding_minutes += 1;
  assert.deepEqual((await runCourse(io,[1],{calls:0,attempts:3,inspect:true})).completed,[1]);
  io.course.weeks[1] = {...current,tool_prerequisites:current.tool_prerequisites.map(
    r => r.topic === "KOAI-04" ? {...r,introduced_in:[3]} : r)};
  assert.equal((await runCourse(io,[1],{calls:0,attempts:3,inspect:true})).reasons[1],"not_started");
  io.course.weeks[1] = current;
  io.version = "new static analyzer version";
  assert.equal((await runCourse(io,[1],{calls:0,attempts:3,inspect:true})).reasons[1],"not_started");
});

test("registrations follow prerequisite reachability and individual methods within an available library", () => {
  const kit = portableCourseTestkit(courseCore, {runCourse, publicOracles}, contract, digest);
  const source = {original:{locator:"local unit",text:"A course registration for testing."}};
  const rules = [{topic:"curves",modules:["matrix_lab.curves"],data_only:["matrix_lab.curves.read_*"],mentions:["Curve"]}];
  const weeks = [[50,[]],[20,[50]],[35,[20]],[81,[50]]].map(([week,prerequisites]) => ({
    week,prerequisites,sources:["original"],decision:"Select a representation.",minimum:"Compare two original inputs.",
    ceiling:"Use methods already introduced.",transfer:"Compare changed inputs.",interface:"matrix → decision"
  }));
  const course = {weeks,tool_prerequisites:rules};
  const budget = {theory_minutes:20,noncoding_minutes:20,coding_minutes:80,required_self_study_hours:[1,2]};
  const syllabus = {class_minutes:120,weeks:weeks.map(({week})=>({week,...budget})),topics:[
    {id:"curves",name:"Curve methods",theory:false,practical:true,scheduled_weeks:[20,35]}]};
  const plan = Object.fromEntries(weeks.map(({week})=>[week,"Published student plan."]));
  const compile = config => courseCore.compile(syllabus,config,source,plan);
  const compiled = compile(course);
  for (const week of [50,20,35,81]) {
    const packet = compiled.weeks[week], rule = packet.tool_prerequisites[0];
    assert.deepEqual(rule.introduced_in,[20]);
    assert.equal(rule.available,[20,35].includes(week));
    const sample = kit.sample(packet,courseCore.obligations(packet),["original"]);
    sample.notebooks.main.cells[2].source = "from matrix_lab.curves import Curve as C\nmake_curve = C\ncurve = make_curve()";
    if (rule.available) courseCore.validateCandidate(packet,sample,null);
    else assert.throws(()=>courseCore.validateCandidate(packet,sample,null),/Premature required tool dependency curves/);
  }
  for (const bad of [
    [{topic:"absent", modules:["matrix_lab"]}],
    [...rules,...rules],
    [{...rules[0],modules:["matrix_lab.*"]}],
    [{...rules[0],data_only:["other.read"]}],
    [{...rules[0],modules:["matrix_lab","matrix_lab"]}]
  ]) assert.throws(()=>compile({...course,tool_prerequisites:bad}),/Invalid or ambiguous/);
  for (const [topic, module, name, teachingWeek] of [
    ["KOAI-08","sklearn.linear_model","LinearRegression",3],
    ["KOAI-11","sklearn.neighbors","KNeighborsClassifier",4],
    ["KOAI-11","sklearn.neighbors","KNeighborsRegressor",4],
    ["KOAI-15","sklearn.cluster","KMeans",5],
    ["KOAI-16","sklearn.decomposition","PCA",5]
  ]) {
    const second = contract.course.weeks[2], scheduled = contract.course.weeks[teachingWeek];
    for (const packet of [second, scheduled]) {
      const sample = kit.sample(packet,courseCore.obligations(packet),packet.sources);
      sample.notebooks.main.cells[2].source = "from "+module+" import "+name+" as Operation\nOperation()";
      if (packet === scheduled) courseCore.validateCandidate(packet,sample,null);
      else assert.throws(()=>courseCore.validateCandidate(packet,sample,null),new RegExp(topic));
    }
  }
});

test("provided examples require a separate compulsory alternative and an independent cell decision", () => {
  const kit=portableCourseTestkit(courseCore,{runCourse,publicOracles},contract,digest);
  const week=contract.course.weeks[1], roles={author:"writer",reviewer:"reader"};
  const sample=kit.sample(week,courseCore.obligations(week),week.sources);
  sample.notebooks.main.cells.unshift(kit.cell("example","from sklearn.neighbors import NearestCentroid\nexample = NearestCentroid()",true));
  sample.route.units[0].cells.unshift("main/example");
  sample.route.provided_examples=[{cell:"main/example",alternative:"main/work",reason:"The independent table exercise can be solved using the given numbers."}];
  let evidence=courseCore.validateCandidate(week,sample,null).tool_prerequisites;
  assert.deepEqual(evidence.review_cells,["main/example","main/work"]);
  const h=digest(sample);
  const review=kit.makeReview({candidate_hash:h,worker_id:"reader",required_checks:[...courseCore.reviewKeys(week),...courseCore.obligations(week)]});
  assert.throws(()=>courseCore.checkReview(week,sample,review,h,roles),/missed/);
  review.checks.tool_prerequisites.cells.push("main/example");
  assert.throws(()=>courseCore.checkReview(week,sample,review,h,roles),/Resolve/);
  review.checks.tool_prerequisites.decisions = {
    "main/example":{disposition:"example_only",reason:"The supplied construction has no output consumed in the student work."},
    "main/work":{disposition:"uses_prior_only",reason:"The independent route uses its own input and does not use the example variable."}
  };
  assert.equal(courseCore.checkReview(week,sample,review,h,roles),"pass");
  review.checks.tool_prerequisites.decisions["main/work"].disposition="unresolved";
  assert.throws(()=>courseCore.checkReview(week,sample,review,h,roles),/inconsistent/);
  sample.notebooks.main.cells.at(-1).source="predictions = example.predict([[2,3]])";
  assert.throws(()=>courseCore.validateCandidate(week,sample,null),/Premature.*main\/work/);
  sample.route.provided_examples[0].cell="main/work";
  assert.throws(()=>courseCore.validateCandidate(week,sample,null),/Invalid provided/);
});
