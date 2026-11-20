import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { loadCourse } from "../tools/course.mjs";

const exec = promisify(execFile);
const repo = fileURLToPath(new URL("../", import.meta.url));
const controller = join(repo, "tools/course.mjs");

function cell(id, source, code = false) {
  const value = {id, source, metadata: {}, cell_type: code ? "code" : "markdown"};
  return code ? {...value, outputs: [], execution_count: null} : value;
}

function notebook(cells) {
  return {nbformat: 4, nbformat_minor: 5, metadata: {}, cells};
}

// These public, deterministic answers exercise the transport. They carry no course-quality evidence.
function fixtureReply(request) {
  const {role, week} = request;
  if (role === "examiner") {
    const probes = {};
    for (const [i, key] of request.required.entries()) {
      probes[key] = {
        entrypoint: "choose_" + i, spec: "Return the ID in the highest-scoring column.",
        cases: [
          {id: "ordinary", kind: "normal", input: {ids: [11, 90], scores: [2, 5]}, expected: 90},
          {id: "reordered", kind: "invariant", base: "ordinary", input: {ids: [90, 11], scores: [5, 2]}, expected: 90},
          {id: "changed", kind: "sensitive", base: "ordinary", input: {ids: [11, 90], scores: [6, 5]}, expected: 11},
        ],
      };
    }
    return {probes};
  }
  if (role === "assessor") {
    const answers = {};
    for (const [key, q] of Object.entries(request.questions)) {
      assert.deepEqual(Object.keys(q).sort(), ["entrypoint", "inputs", "spec"]);
      answers[key] = q.inputs.map(({ids, scores}) => ids[scores.indexOf(Math.max(...scores))]);
    }
    return {verdict: "pass", finding: "Independently computed fixture IDs.", answers};
  }
  if (role === "ground") {
    return {verdict: "ready", demands: [{id: "input-contract", sources: [week.sources[0]],
      decision: week.decision, minimum: week.minimum, ceiling: week.ceiling,
      counterexample: week.transfer, later_use: "See the supplied dependency graph."}]};
  }
  if (role === "author") {
    const definitions = [];
    for (const p of Object.values(request.public_probes)) {
      assert.deepEqual(Object.keys(p).sort(), ["entrypoint", "spec"]);
      definitions.push("def " + p.entrypoint + "(row):\n    return max(zip(row['scores'], row['ids']))[1]");
    }
    const student = notebook([cell("principle", "열 번호는 위치를 나타냅니다. 각 열에 대응하는 ID를 확인하세요."),
      cell("question", "열과 ID의 순서를 함께 바꿨을 때 어떤 결과가 유지될까요?"),
      cell("work", "assert len([11, 90]) == 2", true)]);
    return {week: week.week, action: "create", reason: "Exercise the blank-generation entry point.",
      notebooks: {main: student}, teacher: notebook([cell("reference", definitions.join("\n\n"), true)]),
      route: {units: [{tier: "class", minutes: 20, cells: ["main/principle", "main/question", "main/work"]}]},
      transfer: {principle: "main/principle", prompt: "main/question", solution: "teacher/reference", rationale: week.decision},
      coverage: request.required.map(obligation => ({obligation, teaching: ["main/principle"],
        assessment: ["main/work"], solution: "teacher/reference", sources: [week.sources[0]]}))};
  }
  if (role === "reviewer") {
    const checks = Object.fromEntries(request.required_checks.map(key => [key, {verdict: "pass",
      cells: ["main/principle", "main/question", "main/work"], finding: "Transport fixture."}]));
    return {reviewer: request.worker_id, candidate_hash: request.candidate_hash, verdict: "pass", checks};
  }
  throw Error("Unexpected role " + role);
}

async function runFixture(profile, image) {
  const scratch = await mkdtemp(join(tmpdir(), "course-cli-"));
  const roles = [];
  const server = createServer(async (req, res) => {
    try {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      const instructions = body.messages.find(message => message.role === "system").content;
      assert.match(instructions, /student-facing lessons and exercises in Korean/);
      assert.match(instructions, /all other documentation in English/);
      const task = JSON.parse(body.messages.at(-1).content);
      roles.push(task.role);
      const ret = fixtureReply(task);
      res.writeHead(200, {"Content-Type": "application/json"});
      res.end(JSON.stringify({model: body.model, done: true, message: {content: JSON.stringify(ret)}}));
    } catch (e) {
      res.writeHead(400); res.end(e.message);
    }
  });
  const filename = name => join(scratch, name);
  try {
    await new Promise((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolve);
    });
    const runtime = {profile, author: "writer", reviewer: "reader", examiner: "examiner", auto_assess: true,
      author_model: "fixture-writer", reviewer_model: "fixture-reader", examiner_model: "fixture-examiner",
      endpoint: "http://127.0.0.1:" + server.address().port + "/api/chat", python: process.env.COURSE_TEST_PYTHON || "python3"};
    if (image) runtime.kernel_image = image;
    await writeFile(filename("runtime.json"), JSON.stringify(runtime));
    const {sources, course} = loadCourse(repo, "curriculum/course-harness.json", "curriculum/contract.json");
    const primary = Object.fromEntries(Object.entries(sources).map(([key, src]) => [key, {locator: src.locator,
      original_sha256: createHash("sha256").update(src.text).digest("hex"), text: src.text, fixture: true}]));
    await writeFile(filename("primary.json"), JSON.stringify(primary));
    const common = ["--state", filename("journal.sqlite"), "--suite", filename("probes.json"),
      "--runtime", filename("runtime.json"), "--primary", filename("primary.json")];
    const selected = profile === "private" ? ["--week", "1"] : [];
    async function call(command, args = [], expectedCode = 0) {
      let code = 0, stdout, stderr;
      try {
        ({stdout, stderr} = await exec(process.execPath, [controller, command, ...common, ...args],
          {cwd: repo, maxBuffer: 8 * 1024 * 1024, timeout: 600000}));
      } catch (e) {
        ({code, stdout, stderr} = e);
      }
      assert.equal(code, expectedCode, command + ": " + stderr + "\n" + stdout);
      return JSON.parse(stdout);
    }

    const paused = await call("run", ["--week", "1", "--calls", "3"], 1);
    assert.equal(paused.reasons["1"], "author");
    const result = await call("resume", [...selected, "--calls", "80"]);
    const weeks = profile === "private" ? [1] : course.order;
    assert.deepEqual(result.completed, weeks);
    assert.equal(roles.filter(x => x === "author").length, weeks.length);
    if (profile === "development") {
      assert.equal(result.verified_obligations.length, 84);
      assert.equal(result.eligibility, "development_or_partial");
    }
    const before = roles.length;
    assert.equal((await call("run", selected)).calls, 0);
    assert.equal(roles.length, before);
    assert.deepEqual((await call("status", selected)).completed, weeks);
    const output = filename("export");
    await call("export", [...selected, "--output", output]);
    const saved = JSON.parse(await readFile(join(output, "week-1/main.ipynb"), "utf8"));
    assert.equal(saved.cells.at(-1).execution_count, null);
    assert.deepEqual(saved.cells.at(-1).outputs, []);
    const teacher = JSON.parse(await readFile(join(output, "week-1/teacher.ipynb"), "utf8"));
    assert.match(teacher.cells[0].source, /def choose_/);
    const journal = await call("history");
    assert.equal(journal.filter(e => e.kind === "accepted").length, weeks.length);
    assert.deepEqual(await call("pending-calls"), []);

    const suite = JSON.parse(await readFile(filename("probes.json"), "utf8"));
    const changedWeek = profile === "private" ? 1 : 8;
    suite[changedWeek].probes.transfer.cases[0].expected = -1000;
    await writeFile(filename("probes.json"), JSON.stringify(suite));
    const stale = await call("status", selected, 1);
    assert.deepEqual(stale.pending, profile === "private" ? course.order : [8, 9, 10]);
    assert.equal(roles.length, before);
  } finally {
    if (server.listening) await new Promise(resolve => server.close(resolve));
    await rm(scratch, {recursive: true, force: true});
  }
}

test("all ten weeks through CLI, real SQLite, HTTP workers and fresh Jupyter kernels", () => runFixture("development"));
if (process.env.COURSE_CI_KERNEL_IMAGE) {
  test("digest-pinned private Docker kernel, hidden probes and resume", () =>
    runFixture("private", process.env.COURSE_CI_KERNEL_IMAGE));
}
