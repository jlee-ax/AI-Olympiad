# Evaluation protocol

This is a proposed check contract and comparison plan for future week 1–2 material production. It contains no lesson content, exercises, solutions, actual review scores, or learner results. Pass thresholds, experimental budgets, sample sizes, and stagnation counts remain unagreed. The [tool contract](../../../tools/README.md) defines the serialized state; [workflow decisions](../../references/workflow.md) define the pending scope.

## Four levels of evidence

| Level | Claim examined | What passing does not establish |
|---|---|---|
| Records and traceability | References exist and artifact revisions, hashes, and evaluation context match. | Sources are substantively correct or goals are appropriate. |
| Technical and content correctness | Code executes in the stated environment and agrees with independently checked facts and solutions. | Students understand or can apply it elsewhere. |
| Pedagogical suitability | Evidence supports the fit of goals, prerequisites, explanations, practice, assessment, and workload for the intended learners. | Actual learning, long-term retention, or transfer. |
| Learning outcomes | Real learners demonstrate performance under stated assessment conditions. | Automatic generalization to other learners, topics, or periods. |

Learning outcomes are currently **`untested`**. Automated checks and agent simulations of students are not learner data.

## Proposed checks

For each executed check, record the checker, artifact hash, versions of inputs/skills/criteria/evaluator/references, execution time, observation, and evidence location. Required checks and numerical thresholds must be agreed before use.

| Check | Observation required | Failure or unresolved condition |
|---|---|---|
| Authorization and scope | Connect the authorized request to materials, goals, and weeks. | No production authority; treating an unagreed target as settled. |
| Goals and sources | Link core goals and claims to source locations; distinguish official rules from instructional choices. | Applying the 2026 middle-school restriction to 2027, citing nonexistent official answers, or unsupported claims. |
| Current revision | Match the artifact revision/hash and full evaluation context to the review. | Reusing a pass after content, references, evaluator, or other relevant inputs change. |
| Reproducible execution | Run code/notebooks in order in a fresh environment with declared dependencies and data; inspect exit status and outputs. | Hidden cell state, missing files/dependencies, or no actual execution. |
| Content and answers | Check solutions through suitable independent references, manual calculation, or a separate implementation. | A generated answer is its own sole authority; multiple answers or ambiguous conditions remain unresolved. |
| Data and evaluation procedure | Check splitting, preprocessing, and metric calculation against the stated purpose. | Evaluation data leakage or mismatched denominators, labels, or metric interpretations. |
| Goal–assessment alignment | Explain which behavior each assessment evidences; distinguish recall/execution from explanation/transfer. | An application goal assessed only by term recognition, or success through copying a supplied answer. |
| Prerequisites and explanations | Supply or explicitly assume required concepts; connect example steps, explanations, and practice. | Claiming fit without knowing learner level, or omitting essential reasoning. |
| Workload and usability | Account separately for class, practice, homework, and review; inspect actual readability of materials and outputs. | Conflicting schedules, invisible formulas/outputs, or presenting estimated time as observed time. |
| Regression and completeness | Recheck affected solutions, assessments, references, and other dependent materials. | Changed explanations with stale code/solutions, or unexamined impact. |

The only serialized `check.status` values are `passed`, `failed`, and `not_run`. “Not applicable” is a human rationale or a proposed exclusion, not another status or a waiver for a required check. Unexecuted required checks remain `not_run`. Changing `required_checks` requires renewed criteria agreement, a new frozen baseline revision, and review evidence matching the changed context. Missing checks or stale evidence cannot support completion. Do not fill missing evidence with zero scores or passes.

## Pedagogical review

Initially record **observations, evidence, disagreements, and reasons for uncertainty**, rather than a weighted total. Before introducing a numerical scale, agree on each level's meaning and examples and calibrate reviewers.

| Dimension | Review question | Evidence required |
|---|---|---|
| Correctness and alignment | Are explanations, code, and solutions correct and do they address the agreed goals? | Independent checks and goal–material–assessment links. |
| Prerequisites and explanation depth | Are prerequisites confirmed, and is the amount of explanation justified? | Learner diagnosis or explicit assumptions; step-by-step review. |
| Learner activity | What must students retrieve, explain, implement, or compare? | Activity and feedback design, including when answers become available. |
| Assessment interpretation | What ability does success demonstrate, and what does it not demonstrate? | Scoring rationale, independent solutions, and review of misconceptions and ambiguity. |
| Feasibility and workload | Can the material be used within agreed time, tool, and access constraints? | Execution records, teacher review, and schedules separating estimates from observations. |

[Biggs (1996)](https://doi.org/10.1007/BF00138871) supplies an alignment framework, not experimental proof of this agent architecture. [Karpicke and Blunt (2011)](https://learninglab.psych.purdue.edu/downloads/2011/2011_Karpicke_Blunt_Science.pdf) studied retrieval from science texts and motivates delayed assessment. [Chen et al. (2015)](https://repository.lboro.ac.uk/articles/journal_contribution/The_worked_example_effect_the_generation_effect_and_element_interactivity/12053721) supports examining how prerequisites and complexity affect explanation versus independent problem solving. None establishes the same effect in KOAI lessons or the benefit of a 30-minute agent cycle.

## Calibrate the evaluator

First test whether the evaluator detects actual errors without needlessly changing correct material. Tool-test records created at this stage are **synthetic metadata**, not completed lesson reviews or student performance.

For a future authorized content-evaluation trial:

1. Prepare independently verified correct cases and errors with known locations and causes. Separate wrong answers, calculation/execution errors, leakage, year/scope confusion, ambiguous questions, and unsupported prerequisite assumptions. No lesson cases are produced in the current stage.
2. Keep error locations, reference answers, and severity in evaluation records hidden from the author. Put disputed cases in a separate set rather than treating suspicion as ground truth.
3. Require evidence identifying the error's cause and location, not just a right/wrong label. Measure missed errors and false rejection of correct cases separately.
4. Reverse presentation order and remove author cues to test judgment stability. Resolve disagreements using independent evidence or retain them as unresolved.
5. Separate cases used to revise the evaluator/prompt from final assessment cases. Scores on familiar cases alone do not establish general performance.

Blocking a synthetic record marked failed tests decision logic. Detecting an actually incorrect solution tests content evaluation. Success at the first is not evidence of success at the second.

Oak's [Aila evaluation case study (2025)](https://arxiv.org/pdf/2502.10410) reports improved agreement after expert feedback, but covers one question-quality criterion and limited human evaluation. It supports calibration and separate validation, not a claim that automatic approval is reliable.

## Compare bounded workflows

These are proposed experiments after agreement. Experiments that generate real teaching materials also require production authorization and are not running now.

| Candidate | Shared procedure | Change | Question |
|---|---|---|---|
| A: Strong single-pass baseline | Same goals, source investigation, separate author/reviewer, and outcome records. | Stop after initial authoring and one independent review. | What quality and total cost are achieved without iteration? |
| B: Bounded iteration | Same as A. | Add explicit hypotheses, measurements, and keep/revert decisions within an agreed budget. | Does iteration reduce confirmed errors or teacher correction time? |
| C: Iteration with pedagogical criteria | Same as B. | Add goal–assessment alignment, prerequisite/workload checks, and calibrated pedagogical review. | Does the benefit justify the extra review cost? |

Provide the same initial materials, source bundle, request, goals, model version, and tool access to each candidate. Record total tokens, cost, elapsed time, tool calls, and teacher effort. Match total resource budgets even if call counts differ; otherwise report the quality–cost relationship. Budget values and iteration counts remain unset. Give the single-pass baseline the complete task description. Do not reserve useful task information for iterative candidates.

Blind candidate/model identities, use the same review criteria, and reverse output order. Separate criteria-development cases from final assessment cases. Report failures, rejected changes, regressions, and no-change outcomes, not only the best run. A changed goal or criterion starts a new baseline and comparison.

Apply the requested 30-minute checkpoint equally. Checkpoint counts and edit volume are not quality scores. No change is a valid outcome when there is no new evidence.

## Measures and unresolved values

| Measure | Recording method | Current status |
|---|---|---|
| Total teacher time | Separate authoring support, review, correction, and pre-class repair; label measured, self-reported, or estimated time. | Measurement plan only; values and targets unset. |
| Confirmed errors | Independently verified errors in baseline/candidate, severity, number inspected, and denominator. | No observations; tolerances unagreed. |
| Evaluator false passes/rejections | Missed known errors / error cases; rejected correct cases / correct cases. | Cases, sample sizes, and acceptable rates unagreed. |
| Review agreement/disagreement | Item-level judgments, evidence, reviewer differences, and uncertain ground truth. | No observations. |
| Net benefit of iteration | Defects removed and introduced, teacher time, and total cost. | Minimum improvement and stagnation criteria unagreed. |
| Learning outcomes | Independent performance, delayed retention, and transfer in a separately authorized study. | `untested`; no collection or experiment underway. |

The [EEF/NFER ChatGPT lesson-preparation trial](https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects/choices-in-edtech-using-generative-ai-chatgpt-for-ks3-science-lesson-preparation-2024-teacher-choices-trial) and [Aila evaluation](https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects/aila-teacher-choices-trial) distinguish preparation time from material quality. Report teacher time savings, fewer material defects, and learning gains separately here too. Do not copy published effects into this project's targets or results. See the broader [evidence register](../../references/evidence.md) for additional mechanisms and counterevidence.

## Decisions and stopping

Without agreed criteria, this proposal cannot establish improvement or authorize production or recurrence. Once criteria are agreed, completion still requires every required check for the current artifact and evaluation context. A favorable average cannot offset known failure, stale review, missing evidence, or unresolved required disagreement.

A 30-minute checkpoint pauses for review; it does not schedule another run. Distinguish exhausted budgets, missing authority, failed dependencies, and agreed stagnation conditions. Do not invent stagnation counts or minimum gains. Report confirmed results, failed/unexecuted/unverified checks, and pending decisions.
