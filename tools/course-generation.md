# Generate and review course materials

The controller reads the ten-week plan, the domestic competition scope, primary competition and technical sources, accepted prerequisite notebooks, and the decisions that depend on the current week. The curriculum contract supplies the official topics, theory/practical flags and time allocations. The course design supplies the source locators, prerequisite graph, minimum explanation, upper depth limit and a public transfer interface for each week. International problems provide evidence for a particular capability; the source determines its division and status. Generate student lessons in Korean. Write operating guidance and review records in English.

## Run a course

Use Node 24 and Python 3.12. Create a private directory outside the checkout for the runtime configuration, source records, assessments, state database and candidate exports. Substitute that directory for `/private/course` below. The PDF reader requires `pdftotext`. If retrieval fails, check the original URL, publication year, division and selected pages or lines.

```sh
node tools/course.mjs plan
python tools/course_sources.py --out /private/course/primary.json
node tools/course.mjs run --state /private/course/state.sqlite --suite /private/course/assessments.json --primary /private/course/primary.json --runtime /private/course/runtime.json --calls 60 --attempts 3
node tools/course.mjs status --state /private/course/state.sqlite --suite /private/course/assessments.json --primary /private/course/primary.json --runtime /private/course/runtime.json
node tools/course.mjs history --state /private/course/state.sqlite
```

`resume` accepts the same options as `run` and starts at the recorded phase. `--week 7` includes the prerequisites for week 7. `export` accepts the same input arguments and `--output /private/course/new-export`. It writes current, accepted student and teacher notebooks into a new external directory.

Omit `--baseline` for blank generation. To revise an existing lesson, supply a private JSON manifest such as `{"1":{"notebooks":{"main":"lessons/week01/week01_integrated.ipynb"},"teacher":"lessons/week01/week01_integrated_teacher.md"}}`. The importer normalizes legacy cell IDs and clears saved outputs in its notebook copies. The optional `teacher` path accepts a notebook (`.ipynb`) or a UTF-8 guide (`.md`, `.markdown`, `.txt`). The importer preserves the entire guide in one Markdown cell and records the SHA-256 of its original bytes. To restore a previous candidate, pass a private JSON mapping from week numbers to accepted candidate SHA-256 values with `--restore`. The restored material must pass the current assessment.

## Configure workers and the kernel

Point the controller at a loopback Ollama or Chat Completions endpoint. Supply the actual served model versions and a digest-pinned Docker image containing Jupyter, a Python kernel and the course libraries. Use a registry manifest digest (`registry/image@sha256:…`) or the immutable local image ID returned by `docker image inspect --format '{{.Id}}' IMAGE`. The example uses placeholders for locally provisioned resources. Author, examiner and reviewer requests use separate identities and stateless conversations. Each request carries the same language instructions for Korean student materials and English documentation, including teacher-only notes and decision records. Record shared model families when interpreting independent judgments.

```json
{
  "profile": "private",
  "author": "lesson-writer",
  "reviewer": "independent-reader",
  "examiner": "assessment-designer",
  "author_model": "<served-writer-version>",
  "reviewer_model": "<served-reader-version>",
  "examiner_model": "<served-examiner-version>",
  "model_protocol": "ollama",
  "endpoint": "http://127.0.0.1:11434/api/chat",
  "kernel_image": "<registry/image>@sha256:<64-hex-digest>",
  "auto_assess": true
}
```

With `auto_assess`, the examiner supplies public signatures and private cases for each practical obligation and the main transfer problem. A second reader solves fresh inputs without receiving the answer key. The candidate author receives only public specifications. A manually supplied private suite also needs a current digest and an independent verification record. Identify any changes from the original competition's input, output, constraints or scoring unit. Use `development` for trusted test fixtures and a local Python kernel. Use the isolated private runtime for untrusted notebooks. The private kernel receives public inputs and probe arguments, with no mount of the repository, ledger or expected answers.

## Review and revision

1. Before reading any manuscript, the reviewer records a source-backed decision, minimum explanation, ceiling, counterexample and subsequent use. A source may reveal a missing demand. Adding an entirely new source family requires registering and reading it.
2. The author binds every compulsory requirement to teaching and assessment cells. A conditional supplement has an entry condition, estimated time and return to a required student cell. Required explanations and independent work remain on the mandatory route.
3. Each student notebook starts in its own fresh kernel. The teacher reference receives unseen inputs. The controller compares results outside the kernel, including equivalent answers, invariants and variations that require a different answer.
4. The reviewer reads the source, candidate and prerequisite material. For a table-to-matrix conversion, trace each row, axis and identifier and identify the choice a new input forces. Check whether the prompt gives away the operation, whether a simpler explanation is sufficient and which later week needs further theory. Terms, equations and figures earn no credit by count. The software checks the planned upper time limit. The reviewer assesses plausibility.
5. Record the action, evidence, alternative, rejected version and result. The controller can keep, revise, move, merge, remove, restore or add conditional material. Versioned sources, configuration, evidence and prerequisites determine which prior decisions are current. A consumed budget saves the current phase. Uncertainty and repeated rejection require changed evidence before further work.

### Check what learners have to use

The course design's `tool_prerequisites` connects Python modules or individual callables to practical curriculum topics. Their teaching weeks come from the curriculum contract. A placement is available in the current week or through a prerequisite path. Two independent weeks do not become prerequisites merely because their numbers are ordered. A specific method can have a later placement than its parent package. The `plan` command prints the effective placements. Removing the registration disables that particular code detector and changes the weekly decision identity.

Before a candidate reaches the student kernel, the controller parses the actual learner cells with the Python standard library. It checks the physical notebook order, the planned order and the compulsory route with optional units skipped. It traces common import aliases, assigned constructors, Python helper calls, results consumed later, and registered data-only loaders. Each observation records the source cell, line, route tier, tool and topic. Teacher solutions use a separate kernel. A required premature operation returns the author for revision and is retained in the journal; its numerical result never licenses the assignment. A conditional example can still make a required activity depend on a later tool through its output.

For a supplied demonstration inside a required unit, an author may declare `route.provided_examples: [{cell, alternative, reason}]` using actual student cell references. The alternative is compulsory work that a learner can perform independently. A declared demonstration cannot itself serve as the required assessment or transfer. A later compulsory cell consuming its modeled output is still a dependency. The reader checks the demonstration and the alternative on the actual student page.

The independent `tool_prerequisites` review traces the teaching and assessment for students. It judges ambiguous text, attribution, dynamic calls and explicit demonstrations; it cites specific required cells and records a disposition wherever the scanner returns `review_cells`. General technique requirements expressed only in prose, dynamic Python, third-party implementation details and unregistered APIs require the reader's examination. Code analysis cannot establish that a student understands a method or that all concepts in an unfamiliar library are represented in the registry.

## Recover interrupted external calls

Inspect `pending-calls --state ...` for a reserved request whose response was lost. If the service log contains the original response, provide an external record with `id`, `hash`, `outcome: recovered`, `reason` and the actual `response`. Pass it to `resolve-call --state ... --evidence /private/course/recovery.json`. When the service records establish that the request was never executed, use `outcome: absent` with the evidence. The ledger records the recovery and enables a fresh attempt. A request with an unknown outcome stays pending.

## Evidence for adoption

| Question | Evidence |
|---|---|
| Is the planned depth sufficient? | Check each domestic theory/practical obligation against a real explanation and assessment, fresh practical inputs and independent review. State which extension belongs later and why. |
| Does the change improve the material? | Compare a healthy foundation with a shallow copy exercise. Detect leading prompts and harmful deletion. A new theory needs a decision it changes. A supplement needs a reason to leave the main route. |
| Is the decision independently assessable? | Change a constraint, candidate order or scoring unit. Check both the teacher implementation and whether the student has a meaningful choice. Use unseen cases and keep answers separate. |
| Does the controller work? | Exercise a blank run, restart, stale sources, conflicting updates, private assessment, history, restoration and preservation of existing files. Report the runtime and which components used controlled responses. |
| Do the skills help? | Run the paired experiment below on independently reviewed cases. Student outcomes and observed classroom time are outside these material checks. |

## NVIDIA SkillEvaluator

The [native procedure](skill-evaluation.md) pins the NVIDIA revision and verifies that the two Harbor arms receive the same common files and prompts. Pass `--course-context` to both `check` and `prepare` to add public specifications from five official competition tasks. Private cases and the treatment skill stay outside the common context.

For the later effect study, freeze held-out cases and compare the previous and revised skills, each with its own with-skill and without-skill arms. Match models, judge, budget, repetitions and fixture bytes. Keep Tier 1 validation, Tier 2 overlaps, task preparation and actual Tier 3 trials as separate observations. Pass the reviewed `--suite` and `--review` receipt to the repository adapter. Run the upstream `tier3` command on the prepared skill. Use the upstream `compare-versions` command for compatible retained reports.

The primary outcome is the fraction of held-out faulty cases correctly detected, repaired and independently verified on a changed input. Report paired differences, denominator, case families and uncertainty. Also report false removals or additions on healthy material, missed critical defects, duplicate adoption, incomplete runs and cost. Predeclare error margins before examining comparative results. Public development cases and preparation runs provide integration evidence.
