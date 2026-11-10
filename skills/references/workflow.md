# Workflow and pending decisions

This reference defines the production process and its unresolved choices. Current work covers repository design, skills, and read-only inspection tools. Actual lesson production, learner experiments, and recurring execution have not begun. A document, saved approval field, or planner result does not create authority.

## Working principles

Assign one writer to each bounded artifact and a separate reviewer who inspects the artifact and evidence directly. Pilot a complete unit before expanding parallel work. Freeze the measurement conditions, test one hypothesis at a time, and retain or revert changes based on the agreed evidence. Preserve failed attempts, corrections, and handoff records.

Prevent repeatable errors through tools or checks before adding more instructions. Test a proposed check against a known failure and a neighboring valid case. Review recurring lessons as candidates; do not turn every observation into an active skill. Concise code and adequate beginner explanation are different goals: do not delete necessary teaching steps to shorten an artifact.

These procedures and their adaptations have not demonstrated local educational benefit. The [evidence register](evidence.md) separates published results, counterevidence, proposed transfers, and local tests. Source provenance is retained in [third-party notices](../../THIRD_PARTY_NOTICES.md).

## Competition scope and confirmed course inputs

Checked on 2026-11-10: the [KOAI 2027 announcement](https://kitpa.org/notice/89) and [official rules](https://kitpa.org/storage/6df0e67a-48d7-4255-ba4f-7d86b2bd2824.pdf) specify syllabus sections 1–4 for both middle- and high-school divisions (p. 7, §11). Both have a three-hour written examination with 80 multiple-choice and 10 written-response questions, and a three-hour coding examination with two tasks (p. 8, §12). The [2027 details](https://kitpa.org/koai/2027) agree; read the detailed rules even if a schedule heading omits coding.

The linked [syllabus](https://kitpa.org/koai/syllabus) still carries an IOAI 2026 label. Record both the governing competition year and the referenced syllabus version. The middle-school sections 1–2 restriction in the [2026 sample notice](https://kitpa.org/files/36) does not define 2027 scope. That sample release has no published official answers; agent solutions must not be labeled official. Recheck current sources before production.

| Item | Confirmed input or current specification | Remaining evidence/decision |
|---|---|---|
| Learners and meetings | Middle-school students with basic coding; ten weeks, one 120-minute class per week, as explicitly specified by the user | Actual diagnostic responses, support allocation and cutoff policy |
| Week 1 | Current student HTML plus named Python/table/array/visualization production specifications | Actual materials, diagnosis, execution and current reviews |
| Week 2 | Current student HTML plus split/preprocessing/metrics/baseline-model production specifications | Actual materials and evidence under the stated help/depth conditions |
| Workload | Confirmed 120-minute classes; earlier 240-minute version superseded; required and optional outside work separate | Actual feasibility, acceptable outside workload and support limits |
| Deliverables | Student explanations/practice, teacher guidance/solutions, code/data, assessments/review records | Required formats, environment, access, and intended audience |

Syllabus coverage does not establish that the full scope can be mastered in 20 hours. The meeting count/duration and target are confirmed; production specifications do not constitute completed teaching materials.

The [concrete specification](quality-specification.md), [15-criterion catalog](criteria.json), [unit behaviors](../koai-evaluate/references/unit-specifications.json), and [pinned student plan](../../curriculum/student-plan.html) make these requirements inspectable. No new lesson or learner observation is implied.

## Contract for one production unit

A future authorized unit is a week-specific package. Link:

1. **Request to objective:** actual authorization, official source location, observable learner behavior, and prerequisites. Separate official requirements from instructional choices.
2. **Objective to material and assessment:** identify the artifact section and the observation that would demonstrate the objective. Mentioning a topic does not demonstrate mastery.
3. **Change to hypothesis:** problem, baseline, one proposed mechanism, expected observation, disconfirming result, and affected scope.
4. **Review to exact version:** artifact revision/content digest plus input, skill, rubric, evaluator, and reference versions.
5. **Disposition to evidence:** keep, revert, further review, or no change; actual checks, unrun checks, disagreements, and remaining uncertainty.

Use the [state contract](../../tools/README.md) for machine-readable fields rather than inventing a second schema. Proposed, reviewed, and active knowledge are useful distinctions, but the tool does not implement an automatic promotion lifecycle.

## Responsibilities and cycle

The coordinator resolves scope, dependencies, versions, and conflicting results. The writer makes one bounded change and supplies its evidence. A separate reviewer checks the actual artifact, independent references, and criteria; a different model family alone does not guarantee independent correctness. An educator reviews objectives, workload, misconceptions, explanations, and assessment interpretation. This does not require human approval for every minor edit; sampling and intervention points remain to be agreed.

For authorized work: ground and recall current sources → select a justified unit → write and independently evaluate → retain or revert against the frozen baseline → correct affected work and record the handoff. Record rejected proposals and no-change outcomes. Reuse a conclusion only while its evidence and complete context remain applicable.

At the requested 30-minute checkpoint, preserve the artifact, in-flight work, evidence, spent budget, and next action at a consistent stopping point. It is not a requirement to generate a change, commit, or PR every 30 minutes, nor permission to schedule another run. Do not force an unsafe interruption or report incomplete work as successful.

The tool exposes `validate`, `decide`, `fingerprint`, and `recall` as read-only operations. It does not launch workers or maintain a durable scheduler. Host requirements and limitations are documented with the [tool](../../tools/README.md#host-runtime-notes).

## Evidence and completion

Artifact review and learner mastery are separate. Without an appropriate learner study, learning outcomes remain `untested`. Automated structure/execution checks and educator judgments each have their own limits.

After artifact, input, source, skill, rubric, or evaluator changes, revisit affected reviews. Preserve old receipts as history; do not relabel them as current. An incomplete dependency graph cannot identify every consequence. Missing evidence, known failures, and unresolved required disagreements cannot be offset by a favorable average score.

Only the current required checks under agreed criteria can support a completion claim. Follow the [evaluation protocol](../koai-evaluate/references/evaluation.md). Superseding records preserve corrections without silently erasing their predecessors; lexical recall and exact deduplication do not establish semantic equivalence.

## Decisions still needed

| Decision | Record before the dependent work |
|---|---|
| Required checks and reviewer roles | Mandatory/optional checks, severity, ownership, recheck conditions; changing the required set needs renewed criteria agreement and a new baseline revision |
| Numeric criteria | Denominators, measurement method, sample size, uncertainty, tolerable error, minimum improvement; no invented scores or thresholds |
| Human participation | Initial criteria setting, educator calibration, sample review, and exception resolution; identify who participates and when |
| Comparative evaluation | Single-pass baseline, bounded iteration, and iteration with educational criteria; matched inputs/models/tools/resource budgets, blinding, and final holdouts |
| Recurrence and stopping | Separate execution authorization, host, total time/cost/attempt limits, stagnation conditions, checkpoint and restart procedure |
| Storage and updates | Actual storage location, retention, excluded personal data, source corrections, review scope, writer coordination and recovery |

Lesson production and recurrence remain disabled pending concrete criteria and authorization. Current branch maintenance is authorized; PR creation, merging, deployment, and student-facing release are separate actions requiring their applicable authorization. Do not repeatedly ask for already authorized work.

For a real decision, record its date, decision-maker, user-request reference, exact scope and chosen values, reasons, alternatives, sources, and review conditions. Distinguish proposals, agent inferences, and user decisions. Resolve conflicts by authority and scope rather than choosing the latest date. A saved `approved` label is not authentication.
