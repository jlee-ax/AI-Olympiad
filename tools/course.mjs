import { createHash, randomUUID } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync, chmodSync, renameSync, openSync, fsyncSync, closeSync } from "node:fs";
import { tmpdir } from "node:os";
import { mkdtemp, rm } from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import { parseArgs } from "node:util";
import { courseCore as core } from "./course_core.mjs";
import { runCourse } from "./course_run.mjs";
import { prepareWeek } from "./course_assess.mjs";
import { openLedger } from "./course_ledger.mjs";

const read=p=>readFileSync(p,"utf8");
const json=p=>JSON.parse(read(p));
const hash=x=>createHash("sha256").update(core.stable(x)).digest("hex");
function inside(parent,p){const rel=relative(parent,p);return !rel || !(rel.startsWith(".."+sep)||rel===".."||rel.startsWith(sep));}
function fail(msg){throw new Error(msg);}
function parseWeekRows(html) {
  const rows={};
  for(const tr of html.matchAll(/<tr\b[^>]*\bid=["']week-(\d+)["'][^>]*>([\s\S]*?)<\/tr>/gi)){
    const week=Number(tr[1]);
    if(Object.hasOwn(rows,week))throw new Error("Duplicate student plan row "+week);
    rows[week]=tr[0];
  }
  return rows;
}

export function loadCourse(root,designPath,contractPath,primaryPath=null) {
  const scoped=p=>{
    const path=realpathSync(resolve(root,p));
    if(!inside(root,path))fail("Course input outside repository: "+p);
    return read(path);
  };
  const contract=JSON.parse(scoped(contractPath)), design=JSON.parse(scoped(designPath));
  const plan=scoped(contract.baseline.path), studentPlan=parseWeekRows(plan);
  const primary=primaryPath?json(realpathSync(primaryPath)):null;
  const sources={};
  for(const [id,info] of Object.entries(design.sources)){
    const file=scoped(info.file);
    let text;
    if(info.key){
      const item=JSON.parse(file)[info.key];
      if(item?.locator!==info.locator)fail("Source locator changed: "+id);
      text=item.text;
    }else{
      const lines=file.split(/\r?\n/).filter(s=>s.startsWith(info.starts));
      if(lines.length!==1||!lines[0].includes(info.locator))fail("Missing or ambiguous source excerpt: "+id);
      text=lines[0];
    }
    const original=primary?.[id];
    if(primary && (!original || original.locator!==info.locator || !/^[0-9a-f]{64}$/.test(original.original_sha256) || !original.text?.trim()))fail("Missing or mismatched primary source "+id);
    sources[id]={locator:info.locator,provenance:info.provenance,text,...(original?{primary:original}:{})};
  }
  const refs=["skills/references/workflow.md","skills/references/quality-specification.md",
    "skills/references/criteria.json","skills/koai-evaluate/references/theory-explanation.json",
    "skills/koai-evaluate/references/evaluation.md","tools/material-revision.md"];
  const shared=Object.fromEntries(refs.map(p=>[p,scoped(p)]));
  function roleFiles(roles){return {...shared,...Object.fromEntries(roles.map(name=>[name,scoped("skills/koai-"+name+"/SKILL.md")]))};}
  const skills={author:roleFiles(["ground","recall","orchestrate"]),reviewer:roleFiles(["ground","evaluate","reflect"])};
  const scope={year:contract.competition_year,division:contract.division,syllabus:contract.syllabus_label,
    common_plan:plan.replace(/<tr\b[^>]*\bid=["']week-\d+["'][^>]*>[\s\S]*?<\/tr>/gi,"")};
  return {course:core.compile(contract,design,sources,studentPlan),sources,skills,scope};
}

function loadBaselines(manifest,root){
  if(!manifest)return {};
  const definitions=json(manifest), result={};
  for(const [number,def] of Object.entries(definitions)){
    const blobs={};
    function notebook(name,path){
      const real=realpathSync(resolve(root,path));
      if(!inside(root,real))fail("Baseline path outside repository");
      const bytes=read(real);
      blobs[name]={path,sha256:createHash("sha256").update(bytes).digest("hex")};
      const raw=JSON.parse(bytes);
      if(raw.nbformat!==4||!Array.isArray(raw.cells)||!raw.cells.length)fail("Unsupported historical notebook");
      const seen=new Set();
      const cells=raw.cells.map((original,i)=>{
        const cell={...original};
        cell.id=cell.id??("legacy-"+hash([name,i,cell.source]).slice(0,16));
        if(seen.has(cell.id))fail("Duplicate historical cell ID");seen.add(cell.id);
        if(cell.cell_type==="code"){cell.outputs=[];cell.execution_count=null;}
        return cell;
      });
      return {...raw,nbformat_minor:Math.max(raw.nbformat_minor??0,5),cells};
    }
    const notebooks=Object.fromEntries(Object.entries(def.notebooks).map(([name,path])=>[name,notebook(name,path)]));
    if(!notebooks.main||Object.hasOwn(notebooks,"teacher"))fail("Name the student baseline 'main'");
    const teacher=def.teacher?notebook("teacher",def.teacher):
      {nbformat:4,nbformat_minor:5,metadata:{},cells:[{id:"missing-key",cell_type:"markdown",metadata:{},source:"No teacher answer was supplied with this baseline."}]};
    result[number]={digest:hash(blobs),candidate:{week:Number(number),notebooks,teacher,
      provenance:blobs,reason:"Imported a read-only, unverified baseline"}};
  }
  return result;
}

async function invoke(command,request,extraEnv={},timeout=900000) {
  if(!Array.isArray(command)||!command.length||!command.every(x=>typeof x==="string"&&x.length))fail("Expected a command argument array");
  const cwd=await mkdtemp(join(tmpdir(),"course-call-"));
  try {
    return await new Promise((resolveResult,reject)=>{
      const env={PATH:process.env.PATH,HOME:cwd,TMPDIR:cwd,LANG:"C.UTF-8",...extraEnv};
      const child=spawn(command[0],command.slice(1),{cwd,env,stdio:["pipe","pipe","pipe"],shell:false});
      const data=[];let bytes=0,stderrBytes=0,done=false;
      const finish=(error,result)=>{if(done)return;done=true;clearTimeout(timer);error?reject(error):resolveResult(result);};
      const timer=setTimeout(()=>{child.kill("SIGKILL");finish(new Error("Worker timed out"));},timeout);
      child.stdout.on("data",buffer=>{bytes+=buffer.length;if(bytes>24*1024*1024){child.kill("SIGKILL");finish(new Error("Worker output limit"));}else data.push(buffer);});
      child.stderr.on("data",b=>{stderrBytes+=b.length;});
      child.on("error",error=>finish(error));
      child.on("close",code=>{if(code!==0){finish(new Error("Worker exit "+code+"; "+stderrBytes+" diagnostic bytes"));return;}
        try{finish(null,JSON.parse(Buffer.concat(data).toString("utf8")));}catch(e){finish(e);}});
      child.stdin.on("error",error=>finish(error));
      child.stdin.end(JSON.stringify(request));
    });
  }finally{await rm(cwd,{recursive:true,force:true});}
}

export async function main(argv) {
  const {values:v,positionals}=parseArgs({args:argv,allowPositionals:true,options:{
    root:{type:"string",default:resolve(dirname(fileURLToPath(import.meta.url)),"..")},
    design:{type:"string",default:"curriculum/course-harness.json"},contract:{type:"string",default:"curriculum/contract.json"},
    state:{type:"string"},baseline:{type:"string"},suite:{type:"string"},primary:{type:"string"},runtime:{type:"string"},week:{type:"string"},calls:{type:"string",default:"60"},
    attempts:{type:"string",default:"3"},output:{type:"string"},restore:{type:"string"},evidence:{type:"string"}}});
  const command=positionals[0],root=realpathSync(v.root);
  if(!["plan","run","resume","status","history","pending-calls","resolve-call","export"].includes(command)||positionals.length!==1)fail("Use plan, run, resume, status, history, pending-calls, resolve-call or export");
  const load=()=>loadCourse(root,v.design,v.contract,v.primary),base=load();
  if(command==="plan")return {scope:base.scope.year,weeks:base.course.order.map(w=>({week:w,prerequisites:base.course.weeks[w].prerequisites,decision:base.course.weeks[w].decision,assess:core.obligations(base.course.weeks[w])}))};
  if(!v.state)fail("Specify an external state database");
  const state=resolve(v.state), dir=realpathSync(dirname(state));
  if(inside(root,dir)||existsSync(state)&&inside(root,realpathSync(state)))fail("State must be outside the repository");
  const db=openLedger(state);chmodSync(state,0o600);
  let timer,locked=false;
  try{
    if(command==="pending-calls")return db.pending();
    if(command==="resolve-call"){
      if(!v.evidence)fail("Provide the external recovery evidence record");
      const file=realpathSync(v.evidence);if(inside(root,file))fail("Use private external recovery evidence");
      db.acquire();locked=true;db.resolveCall(json(file));return {remaining:db.pending()};
    }
    if(command==="history")return db.events().map(({id,week,key,entry})=>({id,week,key,kind:entry.kind,attempt:entry.attempt,hash:entry.hash}));
    if(!v.suite||!v.runtime)fail("Specify the external assessment suite and runtime configuration");
    const runtimeFile=realpathSync(v.runtime), config=json(runtimeFile);
    const suiteFile=existsSync(v.suite)?realpathSync(v.suite):join(realpathSync(dirname(resolve(v.suite))),resolve(v.suite).split(sep).at(-1));
    if(!existsSync(suiteFile)&&!config.auto_assess)fail("Missing frozen suite; set auto_assess to prepare it with independent workers");
    const suites=existsSync(suiteFile)?json(suiteFile):{};
    const live=config.profile==="private";
    if(!["private","development"].includes(config.profile))fail("Unknown runtime profile");
    if(live && !v.primary)fail("Refresh or supply independently captured primary source records");
    if(live && (inside(root,suiteFile)||inside(root,runtimeFile)))fail("Keep private assessment and runtime outside the checkout");
    const pinnedImage = /^(?:[a-z0-9][a-z0-9._:/-]*@)?sha256:[0-9a-f]{64}$/;
    if(live && (!pinnedImage.test(config.kernel_image)||Object.values(suites).some(p=>p.visibility!=="private")))fail("Private evaluation requires pinned isolated kernel and private probes");
    if(!config.author_model||!config.reviewer_model)fail("Pin both model names or versions");
    const changing=command==="run"||command==="resume";
    if(changing){
      db.acquire();locked=true;
      timer=setInterval(()=>{try{db.renew();}catch{clearInterval(timer);}},30000);
    }
    const readVersions=()=>["course_core.mjs","course_assess.mjs","course_run.mjs","course_ledger.mjs","course.mjs","course_kernel.py","course_local_worker.py","course_diff.py","material_revision.py"].map(p=>hash(read(join(root,"tools",p))));
    const versions=readVersions();
    const python=config.python??"python3", local=[python,"-I",join(root,"tools/course_local_worker.py")];
    const kernel=live?["docker","run","--rm","-i","--network=none","--read-only","--cap-drop=ALL","--security-opt=no-new-privileges",
        "--pids-limit=256","--memory="+(config.kernel_memory??"4g"),"--tmpfs","/tmp:rw,exec,nosuid,size=1g","--user","65534:65534",
        "-e","HOME=/tmp","-e","JUPYTER_RUNTIME_DIR=/tmp/jupyter-runtime",
        "--mount","type=bind,src="+join(root,"tools/course_kernel.py")+",dst=/opt/course_kernel.py,readonly",
        config.kernel_image,"python","-I","/opt/course_kernel.py"]:
      [python,"-I",join(root,"tools/course_kernel.py")];
    async function call(command,request,key,env) {
      const fingerprint=hash(request), reservation=db.reserve(key,fingerprint);
      if(reservation.recorded)return reservation.response;
      const result=await invoke(command,request,env);
      db.remember(key,fingerprint,result);
      return result;
    }
    const selected=v.week?v.week.split(",").map(Number):base.course.order;
    const restore=v.restore?json(realpathSync(v.restore)):{};
    const baselines=loadBaselines(v.baseline,root);
    const modelEnv={COURSE_MODEL_PROTOCOL:config.model_protocol??"ollama",COURSE_MODEL_EFFORT:config.reasoning_effort??"",COURSE_AUTHOR_MODEL:config.author_model,COURSE_REVIEWER_MODEL:config.reviewer_model,COURSE_GROUND_MODEL:config.reviewer_model,COURSE_EXAMINER_MODEL:config.examiner_model??config.reviewer_model,COURSE_ASSESSOR_MODEL:config.reviewer_model,COURSE_LOCAL_MODEL_URL:config.endpoint??"http://127.0.0.1:11434/api/chat"};
    const frozenBasis=w=>hash({week:w,sources:Object.fromEntries(w.sources.map(k=>[k,base.sources[k]])),skills:base.skills.reviewer,config,versions});
    async function makeSuite(w){
      if(inside(root,suiteFile))fail("Assessment output must be private and external to the checkout");
      const binding=frozenBasis(w);
      const assess=(_who,request,id)=>call(local,request,binding+"/"+id,modelEnv);
      const packet=await prepareWeek(w,base.sources,base.skills.reviewer,config,assess,hash,live?"private":"development");
      const old=existsSync(suiteFile)?json(suiteFile):{};
      if(hash(old)!==hash(suites))fail("Assessment file changed concurrently");
      packet.course_binding=binding;
      const file=suiteFile+"."+randomUUID()+".tmp";const fd=openSync(file,"wx",0o600);
      try{writeFileSync(fd,JSON.stringify({...old,[w.week]:packet},null,2));fsyncSync(fd);}finally{closeSync(fd);}
      renameSync(file,suiteFile);
      return packet;
    }
    const io={...base,baselines,version:versions,digest:hash,ledger:db,suites,config,restore,
      actualWorkers:live,
      needsSuite:config.auto_assess?(w,packet)=>!packet||packet.course_binding!==frozenBasis(w):null,prepareSuite:makeSuite,
      worker:(_who,request,id)=>call(local,request,id,modelEnv),
      checkEdit:(previous,candidate,id)=>call([python,"-I",join(root,"tools/course_diff.py")],{previous,candidate},id,{}),
      kernel:(candidate,probes,id)=>call(kernel,{notebooks:candidate.notebooks,teacher:candidate.teacher,probes},id,{}),
      isCurrent:(w,key,deps,context)=>{
        const fresh=load(),packet=fresh.course.weeks[w];
        const liveRefs=Object.fromEntries(packet.sources.map(id=>[id,fresh.sources[id]]));
        return Object.entries(deps).every(([n,b])=>{const head=db.head(Number(n));return head?.hash===b.hash&&head?.input===b.input;}) &&
          hash({...context,version:readVersions(),scope:fresh.scope,week:packet,references:liveRefs,skills:fresh.skills,config:json(runtimeFile),suite:json(suiteFile)[w],imported:loadBaselines(v.baseline,root)[w]?.digest??null})===key;
      }};
    const result=await runCourse(io,selected,{calls:changing?Number(v.calls):0,attempts:Number(v.attempts),inspect:!changing});
    if(command==="export"){
      if(!v.output||existsSync(resolve(v.output))||!selected.every(w=>result.completed.includes(w)))fail("Export requires a new directory and current reviewed weeks");
      const output=resolve(v.output);
      if(inside(root,realpathSync(dirname(output))))fail("Use an external candidate directory");
      mkdirSync(output,{mode:0o700});
      for(const week of selected){
        const head=db.head(week),wdir=join(output,"week-"+week);
        mkdirSync(wdir);for(const [name,note] of Object.entries(head.candidate.notebooks))writeFileSync(join(wdir,name+".ipynb"),JSON.stringify(note,null,2));
        writeFileSync(join(wdir,"teacher.ipynb"),JSON.stringify(head.candidate.teacher,null,2),{mode:0o600});
        writeFileSync(join(wdir,"review.json"),JSON.stringify({hash:head.hash,input:head.input,scope:head.visibility,coverage:head.candidate.coverage,route:head.candidate.route},null,2));
      }
    }
    return result;
  }finally{if(timer)clearInterval(timer);if(locked)db.release();db.close();}
}

if(process.argv[1] && realpathSync(process.argv[1])===fileURLToPath(import.meta.url)){
  try{const out=await main(process.argv.slice(2));console.log(JSON.stringify(out,null,2));
    if(["run","resume","status"].includes(process.argv[2]) && out.scope?.some(w=>!out.completed.includes(w)))process.exitCode=1;
  }catch(e){console.error(e.message);process.exitCode=2;}
}
