// Compile actual four-book candidates for an externally reviewed native CLI rehearsal.
import {createHash} from "node:crypto";
import {execFileSync} from "node:child_process";
import {existsSync,mkdirSync,readFileSync,writeFileSync} from "node:fs";
import {dirname,resolve} from "node:path";
import {courseCore as core} from "../tools/course_core.mjs";
import {loadBaselines,loadCourse} from "../tools/course.mjs";

const base="e3e00a4aae2c4e9169ae4f66f9f9ec5cb0db2352";
const root=process.cwd(), out=process.argv[2];
if(!out)throw Error("Expected external output directory");
const work=".course-review-inputs";
const read=p=>readFileSync(p,"utf8");
const sha=b=>createHash("sha256").update(b).digest("hex");
const json=p=>JSON.parse(read(p));
const write=(p,o)=>{mkdirSync(dirname(p),{recursive:true});writeFileSync(p,JSON.stringify(o,null,2)+"\n");};
const manifestPath="lessons/week01/lesson-manifest.json";
const mapping={integrated:"main",tables:"tables",axes:"axes",pipeline:"pipeline"};
const routePath="reviews/week01-whole-20261120/e3e00a4-author-route.json";
const oldRoute=json(routePath);
if(sha(read(routePath))!=="27963df19c04077883a4b50d211902b312d08d73929359d43f590ae6dedd34fc")throw Error("The historical route is not the recorded source");
const loaded=loadCourse(root,"curriculum/course-harness.json","curriculum/contract.json");
const week=loaded.course.weeks[1];
const referenceIds=["ref-projection","ref-digit-lookup","ref-named-means","ref-pixel-plot"];
function projection(raw){
 const x=JSON.parse(raw);const cells=x.cells.map(cell=>{
    const c={...cell,metadata:{...cell.metadata},source:Array.isArray(cell.source)?cell.source.join(""):cell.source};
    delete c.metadata.execution;
    if(c.cell_type==="code"){c.outputs=[];c.execution_count=null;}
    if(c.attachments)for(const m of Object.values(c.attachments))for(const [mime,v] of Object.entries(m))
      if(Array.isArray(v)&&mime!=="application/json"&&!mime.endsWith("+json"))m[mime]=v.join("");
    return c;
 });
 return {nbformat:4,nbformat_minor:5,metadata:{},cells};
}
function load(kind){
 const readVersion=p=>kind==="old"?execFileSync("git",["show",base+":"+p],{encoding:"utf8",maxBuffer:24*1024*1024}):read(p);
 const release=JSON.parse(readVersion(manifestPath)).current_release;
 const spec={notebooks:{},teacher:work+"/"+kind+"/teacher.ipynb"};
 const bindings={};
 const t={nbformat:4,nbformat_minor:5,metadata:{},cells:[]};
 let integrated;
 for(const [role,notename] of Object.entries(mapping)){
   const m=release.members[role]; const book=readVersion(m.student),guide=readVersion(m.teacher);
   const p=work+"/"+kind+"/"+notename+".ipynb";write(p,projection(book));spec.notebooks[notename]=p;
   const canonical=projection(book);
   t.cells.push({cell_type:"markdown",id:"guide-"+role,source:guide,metadata:{path:m.teacher,sha256:sha(guide)}});
   if(role==="integrated")integrated=guide;
   bindings[role]={published_notebook_sha256:sha(book),guide_sha256:sha(guide),normalized_native_cells_sha256:sha(core.stable(canonical.cells)),cells:canonical.cells.length,code_cells:canonical.cells.filter(c=>c.cell_type==="code").length};
 }
 const matches=[...integrated.matchAll(/<!--\s*teacher-cell:\s*([a-z0-9-]+)\s*-->\s*\x60\x60\x60python\s*\n([\s\S]*?)^\x60\x60\x60/gm)];
 for(const id of referenceIds){const match=matches.filter(x=>x[1]===id);if(match.length!==1)throw Error("Teacher solution: "+id);
   t.cells.push({cell_type:"code",id,source:match[0][2],metadata:{},outputs:[],execution_count:null});}
 write(spec.teacher,t);
 const sourceManifest=out+"/"+kind+"-manifest.json";write(sourceManifest,{"1":spec});
 return {baseline:loadBaselines(sourceManifest,root)[1],bindings};
}
const old=load("old"),now=load("new"), first={...old.baseline.candidate,...oldRoute};
const current={...now.baseline.candidate,week:1,action:"revise",reason:"Restore the registered sequence for learning Python, arrays and statistics while retaining the actual classification question, numerical explanation and independent transfer. Replace the later model API with the class means and squared distances the student is asked to calculate.",route:oldRoute.route,transfer:oldRoute.transfer,coverage:oldRoute.coverage,edits:{}};
const routes={main:"manual-training-and-distance",pipeline:"known-class-numerical-rule",teacher:"align-numerical-guide-and-classroom-answers"};
const intents={
 main:["Replace the optional estimator calls with training-derived numeric calculations and keep a fresh validation example.","Defer the entire classification calculation to Week 2.","The original image features, learned values and prediction error can be traced without model-library calls."],
 pipeline:["Replace the compulsory classifier interface with arithmetic on labeled training rows and fresh feature vectors.","Treat the entire required classification practice as an optional software tutorial.","The learner can verify imputation, both centers, squared distances, held-out predictions and observed error with the Week 1 tools."],
 teacher:["Align the two instructor guides with the arithmetic actually assigned and retain the independent teacher solutions.","Keep a second model-library implementation as the answer key.","The worked explanations use exactly the learner-visible quantities and the private probe references keep their published contracts."]
};
for(const [name,a] of Object.entries({...first.notebooks,teacher:first.teacher})){
 const b=name==="teacher"?current.teacher:current.notebooks[name];const changed=[];
 if(a.cells.length!==b.cells.length)throw Error("This review bound the cell inventory of "+name);
 a.cells.forEach((x,i)=>{if(x.id!==b.cells[i].id)throw Error("Changed order in "+name);if(core.stable(x)!==core.stable(b.cells[i]))changed.push(x.id);});
 if(!changed.length)continue;
 if(!intents[name])throw Error("Unexpected change: "+name);
 const [reason,alternative,postcondition]=intents[name];
 current.edits[name]={actions:[{kind:"replace",before:changed,after:changed,reason,alternative,postcondition}],routes:{[routes[name]]:{before:changed,after:changed}}};
}
if(Object.keys(current.edits).sort().join()!=="main,pipeline,teacher")throw Error("Expected both revised books and their instructor guides");
const proposed=core.validateCandidate(week,current,old.baseline.candidate);
let rejection;try{core.validateCandidate(week,first,old.baseline.candidate);}catch(error){rejection=error.message;}
if(!rejection)throw Error("Historical material still passes candidate admission under its authentic required route");
const response=Object.fromEntries([["original",first],["candidate",current]]);
for(const [name,body] of Object.entries(response))write(out+"/"+name+".json",body);
const packet={baseline_commit:base,original_candidate_sha256:sha(core.stable(first)),candidate_sha256:sha(core.stable(current)),historical_route_sha256:sha(read(routePath)),native_import_sha256:old.baseline.digest,installed:now.bindings,original:old.bindings,edits:current.edits,
 transfer:current.transfer,coverage:current.coverage,route_units:current.route.units.map(u=>({tier:u.tier,minutes:u.minutes,cells:u.cells.length})),historical_refusal:rejection,validation:proposed.tool_prerequisites,
 frozen_demands:json(".course-review-ci/ground.json").demands.map(d=>d.id),
 review_keys:[...(core.reviewKeys?core.reviewKeys(week):core.requiredReview),...core.obligations(week),...json(".course-review-ci/ground.json").demands.map(d=>"demand."+d.id)],
 compiled_tool_rules:week.tool_prerequisites};
write(out+"/packet.json",packet);
