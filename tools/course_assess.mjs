import {courseCore} from "./course_core.mjs";
import {publicOracles} from "./course_run.mjs";

function makeAssessmentBuilder(core,runner) {
  async function prepareWeek(week,sources,skills,config,call,digest,visibility) {
    if(!config.examiner || config.examiner===config.author || config.examiner===config.reviewer)throw new Error("Use distinct exam writer, author and independent reader identities");
    const required=["transfer",...core.obligations(week).filter(k=>k.endsWith(".practical"))];
    const context={week, sources:Object.fromEntries(week.sources.map(k=>[k,sources[k]])), skills, required};
    const key=await digest({context,config,version:1});
    const format={probes:{key:{spec:"public input/output details; never include private answers",entrypoint:"unique python function name",
      cases:[{id:"n",kind:"normal",input:{},expected:"JSON answer"},
        {id:"i",base:"n",kind:"invariant",input:{},expected:"same semantic result"},
        {id:"s",base:"n",kind:"sensitive",input:{},expected:"different semantic result"}]}}};
    const draft=await call(config.examiner,{role:"examiner",worker_id:config.examiner,...context,format,
      instructions:"Prepare independent, previously unused authentic public interfaces and private grading cases for exactly the listed obligations. Preserve the public transfer interface. Use explicit hand-solvable fresh inputs, including boundary, invariant and sensitive controls. Support alternative correct answers with any_of instead of expected and finite small atol only when justified. Keep expected answers out of public specs. Reject unsuitable or unavailable primary evidence. Return the JSON object."},key+"/design");
    const packet={visibility,owner:config.examiner,probes:draft.probes};
    const specs=runner.publicOracles(week,packet);
    const questions=Object.fromEntries(Object.entries(packet.probes).map(([k,p])=>[k,{...specs[k],inputs:p.cases.map(c=>c.input)}]));
    const blind=await call(config.reviewer,{role:"assessor",worker_id:config.reviewer,...context,questions,
      instructions:"Solve each input independently. Check validity, dataset/official status, lower/upper depth, workload and non-leakage of each public interface. Include equivalent correct alternatives in the question design review. Return {verdict:'pass'|'uncertain'|'revise',finding:string,answers:{obligation:[one answer per input]}}."},key+"/blind");
    if(blind.verdict!=="pass"||typeof blind.finding!=="string"||!blind.finding.trim() || !blind.answers)throw new Error("Independent assessment review unresolved");
    if(core.stable(Object.keys(blind.answers).sort())!==core.stable(Object.keys(packet.probes).sort()))throw new Error("Incomplete oracle review");
    for(const [id,p] of Object.entries(packet.probes))if(!core.evaluateCases(p.cases,blind.answers[id]).passed)throw new Error("Independent solution disagreed for " + id);
    return {...packet,basis:key,verification:{reviewer:config.reviewer,finding:blind.finding,answer_hash:await digest(blind.answers),case_hash:await digest(packet.probes)}};
  }
  return {prepareWeek};
}

export const {prepareWeek} = makeAssessmentBuilder(courseCore,{publicOracles});
