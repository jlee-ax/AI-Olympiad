---
name: koai-orchestrate
description: Coordinate a bounded KOAI week 1–2 lesson-production unit using pstack ownership, verification, and checkpoints. Use to plan or resume authorized material work, allocate independent tasks, or decide the next work unit.
---

# Coordinate one verifiable unit

Read [the design](../../docs/design.md), [evaluation protocol](../../docs/evaluation-protocol.md), and [workflow contract](../../docs/workflow-contract.md). Invoke koai-ground for source/scope uncertainty and koai-recall before resuming.

## Establish the contract

- Record the user's actual authorization, a finite work budget, intended output, writable scope, a falsifiable completion condition, required checks, and a frozen evaluation baseline.
- Read the current state with `python3 tools/workflow.py validate PATH`, then `python3 tools/workflow.py decide PATH` from the repository root. These commands inspect recorded state; they neither grant authority nor execute the next action.
- Respect the returned reason. A continue decision permits only the next already-authorized unit within the recorded scope. Check live user instructions and permissions separately. A synthetic example never grants execution authority.
- Keep lesson production and recurring execution disabled until their concrete criteria and authorization are supplied. Design work may continue within the user's design request.

## Delegate and verify

1. Pilot one complete unit before parallelizing. Give each independent artifact/PR one writer. Give a reviewer the actual artifact and checks, not just the author's summary. Use a different model family where available; disclose a same-family fallback.
2. Supply each worker with its goal, current source/criteria versions, allowed paths/actions, dependencies, and evidence of completion. Keep workers from editing the same artifact concurrently. Reconcile prerequisite and terminology consistency across units.
3. Keep changes bounded to one hypothesis. Preserve baseline output and measure with the frozen criteria. Accept a candidate only after the relevant independent, current-revision checks pass; otherwise retain the baseline and record why.
4. Record accepted, rejected, blocked, and no-change outcomes. Reuse a prior result only when its full input/skill/rubric/evaluator/reference fingerprint still matches and the underlying evidence remains valid.
5. At a 30-minute checkpoint, preserve the current artifact, in-flight work, spent budget, evidence, and next action. The interval is a requested review boundary, not a scientifically optimal cadence or permission to schedule another run. Do not interrupt an unsafe-to-interrupt operation merely to hit a clock boundary.
6. On a stall, inspect the cause and remaining authorized budget. Re-scope or propose a different hypothesis; do not invent work to keep the loop busy. Stop on the agreed predicate/budget, honor a user stop immediately, and surface genuinely unresolved decisions.
7. Package any accepted change with exact artifact revision, evidence pointers, regressions checked, reviewer findings, and remaining uncertainty. Separate draft PR preparation, publication, merge, and student-facing release. This repository supplies no forge writer or deployment executor.

## Handoff

Return current state, accepted/reverted changes, unverified checks, budget used, next permitted action, and blocking decisions. Report “no useful change” when supported. Do not describe artifact quality as learner effectiveness without learner evidence.

## Origin

Retain pstack [Orchestrate](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/orchestrate.md), [Hillclimb](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/hillclimb.md), and [Autonomous run](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/poteto-mode/playbooks/autonomous-run.md) responsibilities. Adapt their host and task assumptions to the local read-only planner. See [traceability](../../docs/pstack-traceability.md) and [attribution](../../THIRD_PARTY_NOTICES.md).
