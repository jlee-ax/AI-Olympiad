# Course harness verification

The integration baseline is `607c56eb71fded982805987d74a6609aeee4c3fc`. This change adds the reusable controller, the ten-week design, role guidance, tests and the course-context option for NVIDIA SkillEvaluator. Existing student lessons are outside the change. Week 1 lesson comparison and any claim of educational improvement are deferred.

## Scope

The current contract has 60 topics, with 25 theory and 59 practical obligations. Their first formal assessment counts by week are 3, 4, 5, 11, 7, 23, 7, 11, 13 and 0. The last week still has its own cross-topic transfer assessment. The software binds each obligation to the required student route and an independent review. Feasibility of the 23 obligations assigned to Week 6 still calls for a review of actual materials.

## Controls

| Test | Expected observation |
|---|---|
| Cold start and re-entry | All selected weeks follow dependencies. A second run on the same inputs issues no further worker calls. A budget stop resumes the saved phase. |
| Source and plan changes | Changing the source used only in Week 8 reopens Weeks 8, 9 and 10. An unchanged foundation remains accepted. A second registration with different week numbers uses the same runner. |
| Edition history | An undeclared deletion, stale acceptance, competing writer or missing successor fails. A restored version is independently checked and both historical versions remain available. |
| Depth and review | A source-grounded requirement can reject an otherwise executable manuscript. Check the actual explanation, independent student choice, sufficient mathematical depth and what belongs later. |
| Independent assessment | The assessor sees inputs without the key. Reordered equivalent alternatives pass. A mislabeled counterexample, key change or reference disagreement fails. |
| Native workflow | The CLI, model HTTP request/response boundary, real SQLite state and Jupyter processes participate. Controlled worker replies are used for repeatable technical tests. |
| Worker revision | Changing the model worker in a private copy reopens assessment. Resume issues one examiner request and one blind-solver request. The next resume reuses that new assessment. |
| NVIDIA inputs | Both Harbor arms receive identical public inputs. The evaluated role stays treatment-specific. Both default and course-context preparations retain private grading boundaries. |

## Earlier isolated exercises

Three independent student-task drafts were tested before this integration. Their teacher JavaScript reference implementations passed 3 frozen input sets for Week 4, 3 for Week 7 and 4 for Week 8. In the density-map exercise a correct reference calculation coexisted with a leading prompt. Content review rejected the stated operation and a subsequent rainwater analogy; students were then asked to distinguish regional mass from maximum individual response in the original domain. These are limited task-level observations.

The frozen manifest digest was `677440cb49c8d1bd09c05edf528403170c0c5d1c7c32b1035b3ce9862a8b52c3`. Consult the original [Restroom](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Restroom/Restroom.ipynb), [Chicken Counting](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Chicken_Counting/Chicken_Counting.ipynb) and [Concepts](https://github.com/IOAI-official/IOAI-2025/blob/39558e9a639d170bd92de91958fcdc915f670463/Individual-Contest/Concepts/Concepts.ipynb) tasks for the official inputs and outputs.

## Integration measurements

Node 24.22.3 executed the 25 instrumented controller scenarios and the disk SQLite suite. SQLite checks include reopening the database, rejecting a stale prerequisite and recovering an externally completed request from its original response. The source refresher captured the 15 registered primary records. All five skills passed native Tier 1 with the configured scanners. All five native Tier 2 commands and the embedding catalog completed using local Nomic and Qwen inference. Native Harbor prepared 15 public role-case pairs and five public editing pairs, checked the identical shared-file manifests and preserved the verifier boundary. These 20 pairs are preparation and integration evidence. The package Python fingerprint matched the repository pin.

All five Tier 1 reports recorded 12 validators, zero errors and zero skipped checks. They recorded 50 warning occurrences across the five reports, including metadata recommendations and client compatibility notices. Tier 2 recorded four similarity warnings per role. Publication status remained incomplete. The first native preparation also exposed a scanner message on standard output before the JSON document. Moving console diagnostics to standard error restored parseable CLI output for all five preparations.

Locally, 294 Python tests passed. The local environment restricted the ZeroMQ sockets needed for two fresh-kernel tests. The hosted runner executed all 296 Python tests without skips. It also ran the complete CLI on all ten weeks and 84 obligations with controlled HTTP responses, real SQLite and fresh Jupyter kernels. A repeat issued zero worker calls, and changing the Week 8 answer key reopened Weeks 8, 9 and 10. A separate Week 1 run passed inside a digest-pinned Docker image with external networking disabled. The test inspected the language instructions actually delivered to every worker role. See the [hosted job log](https://github.com/jlee-ax/AI-Olympiad/actions/runs/44715785416/job/136218703255).

A subsequent test edited the worker in a scratch checkout and resumed the same SQLite journal. Before the fix the CLI reported an out-of-date assessment but made zero requests to refresh it. After binding the call receipts to the assessment's source, configuration and implementation revision, the same input produced exactly one examiner request and one blind-solver request. The next resume used their recorded result. The [integration checks](https://github.com/jlee-ax/AI-Olympiad/pull/7/checks) run this case alongside the complete regression suite.

Native evaluation uses the repository's [pinned NVIDIA source](https://github.com/NVIDIA/SkillEvaluator/tree/e3ede733f4d57578a1630b0579ea236b8cf8a727). Public development exercises and controlled workers measure functionality. A future Week 1 effect study needs held-out cases, a shared budget, independent content review and paired results. Student achievement and measured classroom time are outside this release gate.
