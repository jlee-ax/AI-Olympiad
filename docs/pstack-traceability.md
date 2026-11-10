# pstack traceability

## Attribution, revision and scope

This project is a deliberate homage to Lauren Tan's **pstack**, using its workflow vocabulary and evidence-led habits as the starting point.
Upstream: [cursor/plugins/pstack](https://github.com/cursor/plugins/tree/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack).
Reviewed revision: **c742dd61706fbacc1b95f1a20b7b988cf096ce6c** (2026-10-27).
This is a local specialization for a proposed KOAI preparation workflow, not an upstream pstack release or an endorsement.
Pinning records what was inspected; it does not imply that newer upstream changes have been incorporated.

The local design adds explicit records and a non-executing planner around selected pstack practices.
It does not install Cursor's runtime, launch subagents, produce lessons, schedule runs, execute proposed changes, or operate GitHub.
The English local skill contracts are [ground](../skills/koai-ground/SKILL.md), [orchestrate](../skills/koai-orchestrate/SKILL.md), [recall](../skills/koai-recall/SKILL.md), [evaluate](../skills/koai-evaluate/SKILL.md) and [reflect](../skills/koai-reflect/SKILL.md).
The [workflow contract](workflow-contract.md) describes the [planner](../tools/workflow.py) and [disabled template](../templates/workflow.json); [example state](../examples/workflow.json) is synthetic.
Research results and proposed local evaluations are in [evidence](evidence.md).
Statements below describe provenance and intended behavior, not measured educational or operational effectiveness.

## Classification

- **Retained:** Keep the upstream principle and identify its source.
- **Adapted:** Change its environment, scope or authority boundary explicitly.
- **Supplemented:** Add a local record or test that upstream does not establish.
- **Unverified:** A benefit, capability or implementation parity still needs direct evidence.

A retained principle is not a claim that every upstream instruction has been implemented.
A supplementary schema is not proof of the truth of the values entered into it.

## Source-to-local mapping

| Upstream source and observed behavior | Classification | Local treatment | Evidence and unresolved test |
| --- | --- | --- | --- |
| [hillclimb](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/hillclimb.md): prove measurement sensitivity, freeze the harness, record a baseline and regression gate, test one mechanism-specific hypothesis at a time, repeat measurements beyond noise, then keep or revert against an agreed stop predicate. | Retained core experimental discipline; execution unverified. | Plan bounded comparisons with fixed measurement conditions, explicit hypotheses and evidence-backed dispositions. Keep quality thresholds unset until locally justified; the planner does not run experiments or promote changes. | E01/E03/E07: demonstrate harness sensitivity, repeatability and held-out benefit. Upstream also permits stopping when remaining ideas are marginal relative to cost; its example numbers are not local defaults. |
| [autonomous-run](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/autonomous-run.md): define a checkable completion predicate; verify small changes; commit advances and discard changes that do not help. | Retained principle; adapted runtime. | Record the intended result, bounded change, evidence and disposition. The local planner proposes decisions; it cannot change files or commit them. | E03/E08: test improvement against a pinned baseline; structural validity alone is insufficient. |
| Same playbook: Cursor's built-in /loop, event wakeups and time-based heartbeats provide persistence. | Adapted; runtime unverified. | Keep a requested cadence as planning metadata. Recurrence is off; no scheduler or watcher is provided here. | No cited result validates 30 minutes. Test cycle duration and useful opportunities before choosing a wake mechanism. |
| Same playbook: continue past plateaus, pivot, and surface a genuine dead end without relaxing the predicate. | Adapted. | A finite repair predicate and open-ended teaching improvement are different problems. Permit explicit no-change, pause, blocked and stop reasoning within a bounded campaign. | E03/E09: validate progress, noise and total cost. No universal stagnation count is supplied. |
| [show-me-your-work](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/show-me-your-work/SKILL.md): canonical append-only TSV, evidence pointers, run ownership, transcript audit and cross-model review. | Retained principle; supplemented records. | Preserve decision history and superseding corrections. Local structured records complement the upstream trail rather than silently replacing its contract. | Verify pointers and actual actions; a schema cannot prove that a logged claim happened or that a review was independent. |
| [recall](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/recall/SKILL.md): scoped history, shared-record search, live-state verification and a compact current-state brief. | Retained principle; adapted data access. | Recall local records with scope and provenance. Reading a saved record is not a live check of a PR, source, learner fact or external service. | E06: test corrections, abstention and original-evidence retrieval. Do not infer an autonomous memory store from a recall command. |
| [correct](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/correct/SKILL.md): group repeated mistakes; architecture, types, lint and tests before prose rules; prove checks fail on past mistakes. | Retained. | Prefer enforceable prevention for repeatable production errors. Keep judgment-dependent educational criteria explicit and separately reviewed. | E02/E04: compare prevention with reminders and include valid counterexamples. Upstream's recurrence heuristic is not a measured local threshold. |
| [reflect](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/reflect/SKILL.md): judgment, tooling and divergent review; Accepted/Rejected/Backlog; structural-enforcement routing. | Retained principle. | Distinguish observations, candidate lessons and validated procedures. Preserve rejected items with reasons rather than creating a skill for every observation. | E01/E05: test applicability to unseen tasks, duplicate handling, negative transfer and maintenance cost. |
| Same skill: explicit operator approval before accepted skill edits; no push/PR; substantive edits use a draft/test/iterate process. | Adapted authority boundary must remain explicit. | Implementing this design does not activate future autonomous skill changes or PR handling. Any later extension must name its approved scope and how candidates become active. | Do not describe unmodified pstack reflect as an autonomous self-publishing loop. This repository does not implement that loop. |
| [eval](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/eval.md): organic same-prompt variants, hidden rubric, blinded cross-family judge, transcript inspection and parent synthesis. | Retained; supplemented evaluation plan. | Keep candidate and evaluator roles distinct. Add repeatability, evaluator-version records, order reversal and held-out transfer as proposed investigations. | E07: cross-family review is not proof of independent errors; educator calibration and untouched assessments remain unrun. |
| [orchestrate](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/orchestrate.md): native Task workers, Project notes/store, available PR/CI subscriptions, one PR owner and a separate current-head verifier. | Retained coordination principle; runtime unverified. | Record responsibility and head-specific evidence when applicable. The local planner is not a replacement execution harness or PR bot. | Test one authorized unit end to end before expanding. No workers, subscriptions, merges or GitHub mutations are enabled by these documents. |

## Deliberate local supplements

These are proposed aids to pstack, with separate validation obligations:

1. **Claim-level evidence records:** distinguish an observed result, an inference and a proposed teaching transfer.
   Preserve source version, location and limitations; a URL by itself does not support every nearby claim.
2. **Versioned dependency records:** make affected work discoverable after a source, input or skill changes.
   The dependency graph can be incomplete; a selected recheck set is not proof that all consequences were found.
3. **Proposed candidate lifecycle:** distinguish proposed, reviewed and active knowledge from rejected or superseded items.
   This is a proposed record convention, not an implemented runtime promotion state machine; record validity would not prove that promotion was appropriate.
4. **No-change and stopping rationale:** allow a useful review to conclude that evidence does not justify another edit.
   A no-change disposition does not claim the broader goal is complete; a stop reason must identify completion or the limiting condition.
5. **Whole-lifecycle accounting:** consider authoring, execution, retries, evaluation, memory maintenance and human review.
   Cheap answer generation can coexist with expensive learning and review.
6. **Teaching-specific evaluation:** examine correctness, prerequisite fit, misconception handling and learner outcomes separately.
   Passing software checks or winning a model preference comparison does not demonstrate learning.

## What remains unverified

| Question | Required evidence |
| --- | --- |
| Does the specialized workflow outperform pstack? | Matched local tasks, repeated runs and uncertainty reporting. |
| Does an accepted skill generalize? | Unseen tasks and negative-transfer checks beyond its originating example. |
| Does local recall maintain correct current state? | Correction, stale-reference, conflict and missing-evidence cases. |
| Does deduplication preserve distinct meanings? | Paraphrase and near-match cases; false merges and duplicate misses. |
| Do model reviewers agree with educators? | Blinded calibration with known errors and order reversal. |
| Does the proposed cadence help? | Measured opportunity frequency, completion times, costs and useful accepted changes. |
| Can it run with little human intervention? | Authorized end-to-end trials measuring review and recovery effort; none are claimed here. |

## Authority and evidence boundaries

Current work covers design documents, local skill contracts and non-executing planning/validation utilities.
Real lesson production and recurring runs remain disabled; criteria are intentionally unset.
A continue recommendation, valid JSON file or positive review does not grant a new action permission.
Source examples, sample records and proposed tests must not be reported as completed lessons or successful improvement campaigns.
Any future change to these boundaries should cite the governing user instruction and the affected local contract.

## Updating this mapping

When an upstream or local contract changes, record its revision and revisit affected rows.
Keep the distinction between native harness capabilities, pstack instructions and local implementations.
Add observed test evidence before changing an unverified benefit into a demonstrated local result.
