---
name: koai-orchestrate
description: Use when choosing the next bounded KOAI production step, assigning a verifier, or resuming at a budget checkpoint.
metadata:
  tags: workflow-coordination
---

# Coordinate one verifiable unit

## Purpose

Choose one executable unit within the recorded scope and return its owner, checks, checkpoint and stop condition.

## Prerequisites

Use the actual state, current artifact and agreed completion condition. Production decisions also need the bound quality assessment and discovery evidence.

## Instructions

Read [the workflow and pending decisions](../references/workflow.md), [evaluation protocol](../koai-evaluate/references/evaluation.md), and [state contract](../../tools/README.md). Invoke koai-ground for source/scope uncertainty and koai-recall before resuming.

## Establish the contract

- Record the user's actual authorization, a finite work budget, intended output, writable scope, a falsifiable completion condition, required checks, and a frozen evaluation baseline.
- Read the current state with `python3 tools/workflow.py validate PATH`, then `python3 tools/workflow.py decide PATH` from the repository root. These commands inspect recorded state; they neither grant authority nor execute the next action.
- Respect the returned reason. A continue decision permits only the next already-authorized unit within the recorded scope. Check live user instructions and permissions separately. A synthetic example never grants execution authority.
- Keep lesson production and recurring execution disabled until their concrete criteria and authorization are supplied. Design work may continue within the user's design request.

## Delegate and verify

1. Pilot one complete unit before parallelizing. Give each independent artifact/PR one writer. Give a reviewer the actual artifact and checks, not just the author's summary. Use a different model family where available; disclose a same-family fallback.
2. Supply each worker with its goal, current source/criteria versions, allowed paths/actions, dependencies, and evidence of completion. Keep workers from editing the same artifact concurrently. Reconcile prerequisite and terminology consistency across units.
3. Bound the revision to an instructional objective. Combine additions, deepening, removal and reordering when they solve the same evidenced gap. Preserve baseline output and measure with the frozen criteria. Accept a candidate only after the relevant independent, current-revision checks pass; otherwise retain the baseline and record why.
4. Record accepted, rejected, blocked, and no-change outcomes. Reuse a prior result only when its full input/skill/rubric/evaluator/reference fingerprint still matches and the underlying evidence remains valid.
5. At a 30-minute checkpoint, preserve the current artifact, in-flight work, spent budget, evidence, and next action. The interval is a requested review boundary, not a scientifically optimal cadence or permission to schedule another run. Do not interrupt an unsafe-to-interrupt operation merely to hit a clock boundary.
6. On a stall, inspect the cause and remaining authorized budget. Re-scope or propose a different hypothesis; do not invent work to keep the loop busy. Stop on the agreed predicate/budget, honor a user stop immediately, and surface genuinely unresolved decisions.
7. Package any accepted change with exact artifact revision, evidence pointers, regressions checked, reviewer findings, and remaining uncertainty. Separate draft PR preparation, publication, merge, and student-facing release. This repository supplies no forge writer or deployment executor.

## Handoff

Return current state, accepted/reverted changes, unverified checks, budget used, next permitted action, and blocking decisions. Report “no useful change” when supported. Do not describe artifact quality as learner effectiveness without learner evidence.

## Concrete decision contract

Use [the priority/checkpoint contract](../references/quality-specification.md#priority-checkpoint-and-completion). Evaluate the quality bundle, then run its plan command. A reproduced wrong claim/key precedes presentation work; unresolved evidence stays a research task. Preserve the confirmed 120-minute class accounting and separate outside work. Record the actual policy decision, current agreement fingerprint and finite budgets. Bind the quality bundle, criteria and evaluator manifests in workflow inputs before lesson/recurring decisions. A pause/no-op can leave material incomplete.

The current quality gate includes K16 [theoretical explanation](../koai-evaluate/references/theory-explanation.json), alongside execution and numerical checks. Account for the configured required-homework cap in each selected week's ledger and pinned range. When resuming, use the last appended current-object review/cycle, retaining earlier records as history; a newer failure or abstention is blocking evidence. Do not schedule a recurring run merely because a checkpoint is recorded.

For an authorized lesson unit, include the [competition-depth comparison](../koai-evaluate/references/contest-depth.md) in the bounded review. Queue a specific, source-grounded demand or an explicit unresolved evidence gap; do not mistake internal lesson alignment, a scheduled topic, a structurally valid graph, or more content for demonstrated contest readiness. Preserve the 120-minute class and list outside work separately.

On lesson handoff or resume, run [joined review preflight](../../tools/review-preflight.md), including active-record recall and current artifact/path/bundle bindings, after the separate substantive review. Use [the manual cycle](../../tools/MANUAL-CYCLE.md) to preserve bounded work, dispositions and checkpoints. Its advisory result is not an executor; a complete declared path is not proof of correct teaching or observed independence. Queue remaining whole-artifact gaps explicitly rather than repeating already verified unaffected work.

For real readiness, seed and maintain the [external requirement discovery loop](../../tools/discovery-loop.md) before comparing lesson content. Search/read original external material, trace newly observed prerequisites and learning/assessment depth into fresh demands, and expand unresolved questions rather than restricting work to existing claims/comparisons. The tool executes local reads and state transitions; the human/model supplies search execution, source truth and semantic judgments. Keep foundational deferral accountable, bind the current discovery manifest in the aggregate review, and respect cumulative stop/resume limits. A completed sampled record cannot establish exhaustive contest coverage or learner mastery.

For an unresolved content gap, use the [material revision procedure](../../tools/material-revision.md). Request the repair-phase decision, apply the selected typed edit to a new candidate, and verify it before advancing the discovery record. Final readiness uses the current release-phase decision.

## Examples

Inspect the unconfigured template from the repository root:

```sh
python3 -B tools/workflow.py validate templates/workflow.json
python3 -B tools/workflow.py decide templates/workflow.json
```

The record is structurally valid. Its decision is `pause / operator_agreement_required`; use the reason in the handoff.

## Troubleshooting and limitations

A valid JSON state can still yield a pause or stop. Keep spent budget and the last completed evidence with the checkpoint. The CLI does not launch a worker.
