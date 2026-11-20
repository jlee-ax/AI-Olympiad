import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const pythonName = /^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$/;
const dataRule = /^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\*?$/;

export function compileToolPrerequisites(contract, design, entries, order) {
  const registrations = design.tool_prerequisites ?? [];
  if (!Array.isArray(registrations)) throw Error("Invalid tool prerequisite registrations");
  if (!registrations.length) return;
  const topicById = new Map(contract.topics.map(topic => [topic.id, topic]));
  const seenTopics = new Set(), seenModules = new Set();
  const ancestors = new Map();
  for (const number of order) {
    const preceding = new Set();
    for (const direct of entries.get(number).prerequisites) {
      preceding.add(direct);
      for (const previous of ancestors.get(direct)) preceding.add(previous);
    }
    ancestors.set(number, preceding);
  }
  const rules = registrations.map(registration => {
    const {topic, modules, data_only = [], mentions = []} = registration || {};
    const definition = topicById.get(topic);
    const uniqueStrings = (list, predicate) => Array.isArray(list) && list.every(v => typeof v === "string" && predicate(v)) && new Set(list).size === list.length;
    if (!definition || !definition.practical || seenTopics.has(topic) ||
        !uniqueStrings(modules, s => pythonName.test(s)) || !modules.length ||
        modules.some(m => seenModules.has(m)) ||
        !uniqueStrings(data_only, s => dataRule.test(s) && modules.some(m => s.startsWith(m + "."))) ||
        !uniqueStrings(mentions, s => pythonName.test(s))) {
      throw Error("Invalid or ambiguous tool prerequisite registration: " + topic);
    }
    seenTopics.add(topic);
    modules.forEach(m => seenModules.add(m));
    const placements = definition.scheduled_weeks;
    const first = placements.filter(week => !placements.some(other => ancestors.get(week).has(other))).sort((a,b) => a-b);
    return {topic, modules:[...modules].sort(), data_only:[...data_only].sort(), mentions:[...mentions].sort(),
      introduced_in:first, placements};
  }).sort((a,b) => a.topic.localeCompare(b.topic));
  for (const [week, row] of entries) {
    row.tool_prerequisites = rules.map(({placements, ...rule}) => ({
      ...rule, available:placements.some(w => w === week || ancestors.get(week).has(w))
    }));
  }
}

export function inspectToolPrerequisites(week, candidate, blocks, mandatory) {
  const demonstrations = candidate.route.provided_examples ?? [];
  if (!Array.isArray(demonstrations)) throw Error("Invalid provided examples");
  const assessment = new Set([candidate.transfer.principle, candidate.transfer.prompt,
    ...candidate.coverage.flatMap(item => item.assessment)]);
  const cited = new Set();
  for (const {cell, alternative, reason} of demonstrations) {
    if (!mandatory.has(cell) || !mandatory.has(alternative) || cell === alternative ||
        blocks.get(cell)?.cell_type !== "code" || assessment.has(cell) || cited.has(cell) ||
        typeof reason !== "string" || !reason.trim()) throw Error("Invalid provided example or independent alternative: " + cell);
    cited.add(cell);
  }
  if (demonstrations.some(entry => cited.has(entry.alternative))) throw Error("The required alternative cannot depend on another provided example");
  // Send only authored learner source. Saved images, teacher answers and private cases never reach the parser.
  const notebooks = Object.fromEntries(Object.entries(candidate.notebooks).map(([name, notebook]) => [name, {
    cells: notebook.cells.map(({id, cell_type, source}) => ({id, cell_type, source}))
  }]));
  const packet = {week:week.week, rules:week.tool_prerequisites, notebooks, route:candidate.route};
  const program = fileURLToPath(new URL("./course_tool_prerequisites.py", import.meta.url));
  const response = spawnSync("python3", ["-I", program], {
    input:JSON.stringify(packet), encoding:"utf8", timeout:30000, maxBuffer:16 * 1024 * 1024
  });
  if (response.error || response.status !== 0) throw Error("Cannot verify student tool prerequisites: " +
    (response.error?.message || response.stderr?.trim() || "Python parser failed"));
  const report = JSON.parse(response.stdout);
  if (!Array.isArray(report.findings) || !Array.isArray(report.blocked) || !Array.isArray(report.review_cells)) {
    throw Error("Invalid student tool prerequisite evidence");
  }
  if (report.blocked.length) {
    const first = report.blocked[0];
    const source = first.origin !== first.cell ? " (from " + first.origin + ")" : "";
    const error = Error("Premature required tool dependency " + first.topic + ": " + first.api +
      " at " + first.cell + " line " + first.line + source + ". Use an introduced method or move the dependent work.");
    error.tool_prerequisites = report;
    throw error;
  }
  return report;
}

export function checkToolReview(candidate, criterion, evidence) {
  const needed = [candidate.transfer.principle, candidate.transfer.prompt, ...evidence.review_cells];
  if (!needed.every(ref => criterion.cells.includes(ref))) throw Error("Tool review missed a required activity or flagged cell");
  const decisions = criterion.decisions ?? {};
  const cells = evidence.review_cells;
  if (typeof decisions !== "object" || decisions === null || Array.isArray(decisions) ||
      Object.keys(decisions).length !== cells.length || cells.some(ref => !Object.hasOwn(decisions, ref))) {
    throw Error("Resolve each flagged tool prerequisite cell in the independent review");
  }
  for (const ref of cells) {
    const decision = decisions[ref];
    if (!decision || !["uses_prior_only","example_only","requires_later","unresolved"].includes(decision.disposition) ||
        typeof decision.reason !== "string" || !decision.reason.trim() ||
        (decision.disposition === "requires_later" && criterion.verdict !== "revise") ||
        (decision.disposition === "unresolved" && criterion.verdict === "pass")) {
      throw Error("Unresolved or inconsistent tool prerequisite decision at " + ref);
    }
  }
}
