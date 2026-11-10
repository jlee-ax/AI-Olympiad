# Concrete quality and work specification

Revision: criteria-v1. The [criterion catalog](criteria.json) defines K01–K15. Every criterion names its object, observable measurement, pass/fail/uncertainty rule, severity and priority, examples, supporting source IDs, expected effect and limit. Operational choices needing agreement remain proposals; they are not published effect sizes.

## Confirmed inputs

The user specified **middle-school learners with basic coding, ten weeks, one 120-minute class per week**. These are confirmed inputs. AI prelearning is not an entry requirement.

The [student HTML](../../curriculum/student-plan.html) is the later full-scope recalibration following the request to place required syllabus topics in class or required self-study. It is retained byte-for-byte, SHA256 96deb5e5e781bf39cc6bb5effe34d6d04a01ac65e13a3811c37f5a825714f7a9. Earlier 240-minute files and the earlier introduction with optional syllabus gaps are not this baseline.

The [curriculum contract](../../curriculum/contract.json) records ten class allocations and all 60 grouped official topics with theory/practical flags, plan anchors and scheduled weeks. The HTML's 100–130 hours of required self-study are separate from 20 class hours. Its estimates and diagnostic targets are recorded source proposals, not observed student performance or scientifically calibrated thresholds.

The [2027 official page](https://kitpa.org/koai/2027) requires sections 1–4 and written plus coding examinations for both divisions. Its linked [syllabus](https://kitpa.org/koai/syllabus) still carries an IOAI 2026 label. Preserve both identifiers. Official practical requirements, planned placement and achieved learner performance are different fields. Current detailed production specifications cover week 1–2; the remaining course stays in the coverage registry.

## Definitions and theoretical-error judgment

A theoretical claim is an atomic statement about a named quantity or mechanism in a stated domain, with assumptions, conventions and an artifact location. A confirmed error requires an independent source/derivation or a reproducible counterexample contradicting that scoped statement. Suspicion or source disagreement stays unresolved.

A permissible simplification omits detail without changing the prediction, explanation or decision required by the objective. Changing a denominator, implication, applicable population, unit or output shape is not harmless simplification.

| Failure | Observable evidence | Action and severity |
|---|---|---|
| False formula, value, shape or answer key | Independent recomputation/source under the same definitions | P0 when reproduced; correct and recheck affected example/code/key |
| Missing domain condition or invalid generalization | A counterexample changes the intended conclusion | P0 when reproduced; otherwise P1 research and uncertainty |
| Quantity, unit, population or convention confusion | Explicit comparison of types/units/denominators | P0 when it changes the taught result |
| Missing prerequisite step | Locate the demanded operation and absent earlier support | P1 if it prevents the required task; change support/sequence |
| Ambiguous assessment | Two plausible readings produce different valid results | P1 when grading or required meaning changes |
| Conflicting, stale or incomplete sources | Original versions and precise contradictory/missing claims | P1 evidence gathering; do not invent a resolution |
| Nonessential presentation | Meaning, behavior and accessibility remain equivalent | P3; no new scientific finding is implied |

Example: TP=5, FP=10, FN=5 gives precision 1/3 and recall 1/2. Reversing the denominators is reproducibly wrong. With no predicted positives, precision requires an explicit undefined-value convention. Validation-based setting selection is legitimate; fitting preprocessing on validation data is different. See [precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_score.html), [leakage](https://scikit-learn.org/stable/common_pitfalls.html) and [NumPy reduction](https://numpy.org/doc/stable/reference/generated/numpy.mean.html).

## Named week 1–2 objects

The [unit specifications](../koai-evaluate/references/unit-specifications.json) define exact behaviors, prerequisite IDs, reference-check kinds and existing time placement.

| Unit | Observable performance and key distinction |
|---|---|
| W1-python | Trace control flow, return/reuse a value, handle stated file/error conditions; distinguish return from print |
| W1-table | Select rows/columns, name feature/target and missingness, inspect dtype/shape; missing is not automatically zero |
| W1-array | Predict dimensions, hand-compute and execute axis reductions; selected axis differs from retained dimensions |
| W1-visualise | Name plotted quantity, aggregation and units, implement and interpret; displaying a graph is not explaining it |
| W2-split | Explain split roles and audit row/group/time conditions; preserve final test independence |
| W2-preprocess | Identify training-fitted statistics and apply a fixed transform; fit differs from transform |
| W2-metrics | Define positive label, confusion counts and each denominator; undefined differs from zero |
| W2-baseline-model | Evaluate the dummy baseline under fixed validation conditions; keep the test embargo through final week 4 selection |

Prerequisite readiness means named observable behavior under recorded help, rather than an age label. Diagnose variables, control flow, functions/return, lists, files/errors; diagnose or teach means before reductions, ratios before metrics and axis behavior before dependent preprocessing. A missing skill needs a specific support activity before first use.

A diagnostic record has ID, task, expected behavior, actual observation, status, help and evidence. A support route identifies its activity, before-unit, artifact locator and time placement. A scheduled support route establishes planning readiness, not demonstrated unaided mastery. The HTML's 4/5 and 3/4 targets remain source proposals until their use is agreed and calibrated.

Guided application means modifying/running an example and interpreting its output with stated assistance. Independent transfer additionally needs new input and no hint or visible completed answer for that assessment. Theory, noncoding prediction/hand-work, coding and assessment must address the same concept and intended performance. Matching IDs is insufficient without substantive review.

## What is implemented

The [reading register](source-readings.json) gives original sources, exact read extents, findings and limitations. Its existence is not a passing lesson review.

| Criteria | Implemented measurement | Remaining judgment or limit |
|---|---|---|
| K01 | Actual file digests, target, ten week IDs, 60 topic IDs/flags/placements | No automatic live-source fetch |
| K02 | Missing objectives, practical-versus-concept contradiction, recorded mode evidence | Actual named components and depth need a current review |
| K03 | Baseline visible times and current material ledger; all activity blocks accounted; 120 total; written 10 inside noncoding | Actual completion time and acceptable outside workload |
| K04 | Required prerequisite IDs for real units, observations/help/evidence and support-route fields | Diagnosis and support adequacy |
| K05 | Four roles, actual artifact locators and matching concept IDs | Semantic alignment review |
| K06 | Current evidence-bearing independent recorded claim review | Arbitrary prose, proof and mechanism correctness |
| K07 | Independent finite 2D axis means, binary metrics, weighted sums and declared split/fit audit | Unsupported math and unrepresented leakage |
| K08 | Current artifact digest, command/environment/exit/assertions, clean/new-input declarations and actual receipt-file digests | Authentic execution and adequate test coverage |
| K09 | Independent-depth claims reject help/visible answer and missing new input; current review | Assessment validity and observed learner performance |
| K10 | Original-source type/version/access/location/extent; methods/results/limits fields for empirical claims | Authentic reading, comprehension and entailment |
| K11 | Focused cycle with known sources and current per-object context | Actual discovery and direct reading |
| K12 | Transitive declared impact and stale per-object review detection | Graph completeness |
| K13 | Exact proposal keys and prior accepted/rejected/no-change reasons | Paraphrase/semantic equivalence |
| K14 | Current policy fingerprint, priority floor, finite budgets and reported 30-minute checkpoint | Authority, measured time, worker/scheduler execution |
| K15 | Good/fault control counts and agreed tolerances, current review | Representative educator calibration and learner outcomes |

A passed semantic check means a current independent evidence-bearing review is recorded; the tool does not authenticate its truth. Synthetic positive cases remain synthetic and cannot validate real workflow state.

Reference functions never evaluate submitted expressions or execute submitted code. Axis means cover finite rectangular 2D arrays, axis 0/1 and keepdims false. Binary metrics use explicit counts and undefined-value handling. Numeric comparison uses relative tolerance 1e-9 and absolute tolerance 1e-12 for those reference cases; these are implementation tolerances, not student grading cutoffs. Split auditing checks declared ID overlap, training-fit inclusion and test-driven selection; it cannot discover hidden group/time leakage.

## Bundle and evidence contract

Start with [the unconfigured bundle](../../templates/quality.json). Schema version is integer 1; synthetic is boolean. Required objects are artifact, target, policy, budget and checkpoint. Object arrays are units, claims, source_reads, research_cycles, dependencies, reviews, candidates, attempts and lesson_allocations.

- Artifact: ID, revision, relative path and actual raw-file SHA256.
- Target: competition year/division, unique nonempty objective IDs, coverage claim selected_scope or full_syllabus, and currently untested learner outcomes.
- Policy: agreed, actual decision reference, agreement fingerprint and stop request. Diagnostic cutoff, outside-work limit and calibration tolerance stay null until agreed.
- Budget: positive attempt, total-minute and no-progress limits, or null before agreement.
- Checkpoint: reported nonnegative minutes-since, cumulative elapsed time and no-progress count, plus an actual checkpoint record.
- Lesson allocations: unique week and block IDs, theory/noncoding/coding kind, integer minutes and written minutes included within the block. Every chain activity points to an accounted block. Setup/support/feedback fit in those blocks or are separately recorded outside work.
- Unit: ID, week, real artifact locator, syllabus/concept/prerequisite/claim IDs, claimed depth, mode evidence, four-role chain, execution and calibration. Each role names concepts, expected behavior, actual locator, activity ID and help; assessment also records new-input status.
- Claim: ID, statement, domain, quantity, assumptions, locator, source IDs and optional reference check. An empirical effect claim declares that type explicitly.
- Dependency: unique ID, content/meaning revision, SHA256 and ancestor IDs. Cited sources are claim ancestors; used claims are unit ancestors.
- Review: ID, criterion/object IDs, status, reviewer, context fingerprint, reason and evidence. Reviewer ID differs from author for a recorded pass; latest matching record applies.
- Evidence: locator and observed support; any local path additionally needs its actual SHA256. Execution needs at least one such bound local receipt, exact artifact digest, command/environment, integer exit, clean/new-input booleans and passed required assertions.
- Calibration: independently labeled good and fault case IDs, expected/observed outcomes and evidence; tolerated missed faults/false rejections are agreed values.

Quality statuses are passed, failed, uncertain and not_run. Contradictory observed output fails; absent or conflicting support is uncertain; a missing run is not a student failure. No missing/uncertain state counts as a pass. The older workflow review enum remains passed/failed/not_run; do not insert an unsupported new enum there.

## Repeated discovery, direct reading and refinement

1. Name the exact trigger: official update, objective/claim change, conflict, failed check or expired relevant review.
2. Log focused queries and original candidates. Secondary summaries are leads. Preserve no-result/access-failure outcomes.
3. Open the original; record URL, version, access date, precise location and actual extent. Empirical effect claims require methods, population/task, comparator, result and limitations. An abstract cannot supply unseen methods.
4. Extract the scoped finding, assumptions, counterevidence and proposed consequence. Distinguish technical facts, empirical observations and local transfer hypotheses.
5. Compare with the prior version, preserve the original and record updated, unchanged or abstain with reasons and affected IDs.
6. Bind the cycle's object_contexts to current K10 per-object fingerprints. A changed claim/source stales the earlier cycle. Access-time-only refresh after an unchanged source does not force unrelated content re-review.

A cycle records ID, trigger, query strings, source/object IDs, current object contexts, disposition and reason. Source reads record original type, version, access date, locator, extent, finding and limitation; empirical support additionally needs method/result fields. Obtain the current context with the review-context command.

The authorized worker performs discovery and direct reading with its available tools. The CLI does not browse, run a model or turn a saved receipt into a new reading. The included register explicitly preserves partial readings instead of claiming unseen methods were read.

## Selective impact and duplicate work

Impact traversal reports affected/unaffected declared IDs without writing records. Per-object fingerprints bind criterion definition, object data, actual HTML row/notebook cell/file region and relevant dependency/source support. Unchanged regions support reuse. Access-time-only updates and new execution receipts do not automatically invalidate unrelated semantic checks.

Changed source meaning/version, object content or criterion stales the affected review. Final aggregate verification still binds the current whole artifact and bundle. Declared dependency coverage is not proof that no hidden dependency exists.

A proposal key binds criterion, object, hypothesis, explicit action, optional new evidence basis and relevant context. Retain accepted/rejected/no-change outcomes and reasons. Unchanged repeated proposals are suppressed; different quantities/actions/evidence remain distinct. Paraphrases require review, not automatic merging or deletion.

## Priority, checkpoint and completion

The proposed order is P0 confirmed wrong content/key or invalid evaluation; P1 scope, prerequisites, execution and unresolved blocking evidence; P2 alignment/support improvement; P3 presentation. A computed reproduced error sets a floor even if a manual label says minor. Unresolved suspicion is not a confirmed P0 error. Within a tier use broader declared dependency impact, then stable ID; cost-based tie-breaks need measured evidence.

Located findings produce scoped candidates. An unlocated higher-priority blocker causes a pause rather than cosmetic work. Ranking never grants execution authority.

Record the actual policy decision/fingerprint and finite budgets before continuing. Changes to agreed criteria, governing scope, target, budget or tolerance require the corresponding refreshed decision. This does not require asking again for an unchanged authorized design task.

At 30 reported minutes, pause and record artifact version, source changes, passed/failed/uncertain/unrun checks, accepted/rejected/no-change work, cumulative usage and remaining budget, in-flight work, next action and unresolved choices. Do not reset cumulative usage or invent an edit. This command is not a timer.

Operator stop has precedence. Exhausted budget stops the campaign. No new eligible candidate can yield a no-op while material remains incomplete. All quality checks establish at most recorded readiness for independent final review. The integrated workflow also requires its current separate review and agreed completion predicate.

## Expected effects, counterevidence and open decisions

Expected effects in the catalog are reductions in identifiable substitution, scope, prerequisite, calculation, stale-review and repeated-work failures. The injected-fault tests demonstrate those finite cases and neighboring normal cases, not educational improvement.

A later effectiveness test needs matched starting tasks, sources, model/tools/resource budgets, calibrated independent review, known-good/error controls, untouched transfer cases, regressions, no-change outcomes, total costs and uncertainty. Learner benefit additionally needs actual independent/delayed/transfer evidence under an agreed study.

Biggs supplies an alignment design framework illustrated in teacher education, not a randomized KOAI effect. Prior-knowledge/complexity findings do not determine local cutoffs. Retrieval experiments on science texts do not validate this programming course. Older-model self-correction counterevidence motivates external checks without proving that later models cannot improve.

Still unset: diagnostic cutoffs/help policy, acceptable outside workload/support allocation, calibration sample/tolerances, minimum useful improvement and total attempt/time/no-progress budgets. The default bundle stays incomplete. This work creates no student responses, new lesson notebooks, learner study or recurring worker run.
