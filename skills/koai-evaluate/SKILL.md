---
name: koai-evaluate
description: Evaluate an exact KOAI artifact revision with frozen criteria and independently grounded checks. Use to review a proposed lesson change, calibrate an evaluator, or determine what a claimed improvement actually establishes.
---

# Evaluate the artifact and the measurement

Read [the evaluation protocol](references/evaluation.md) and [workflow contract](../../tools/README.md). Use agreed criteria; when criteria are unresolved, report the evidence needed instead of inventing a pass score.

1. Bind the review to the actual artifact digest and the complete input/skill/rubric/evaluator/reference context. Establish baseline and candidate before inspecting comparative outcomes.
2. Keep four claims distinct: structural/provenance validity; technical/content correctness; pedagogical suitability; observed learner outcomes. A stronger claim needs its own evidence. Leave learning effectiveness untested without an appropriate learner study.
3. Review the real artifact independently of its author. Run relevant executable examples/checks in an authorized isolated environment; verify factual claims and answer keys against independent evidence. Mark each required check as passed, failed, or not run and attach its actual receipt.
4. For comparative judging, anonymize author/model/variant labels, use the same task and source access, and hold compute allowance fixed. Keep evaluation-only tasks and scoring details outside the candidate's work context; keep student learning objectives explicit.
5. Challenge the evaluator with known-correct controls and substantive seeded faults. Reverse candidate order and inspect verbosity effects. Calibrate a sample against educator judgments and record disagreements. A second model family alone does not establish independent or reliable judgment.
6. Accept improvement only under the agreed criteria and regression constraints. Do not alter the rubric, test, source baseline, or threshold to make a candidate pass. If the measurement is wrong, open a separate revision and rerun the comparison.
7. Reject stale reviews after artifact/context changes. Never mark a failed, unrun, missing, or unrelated receipt as a current pass. Inspect semantic support yourself: the workflow validator cannot establish that a linked source or receipt says what the record claims.
8. Run `python3 tools/workflow.py validate PATH` and `python3 tools/workflow.py decide PATH` on the updated recorded state. Report their mechanical findings alongside the substantive review.

## Result

Return the exact revision, check-by-check outcomes, evidence pointers, reviewer identity/model, baseline/candidate differences, uncertainty, and the strongest warranted claim. Keep pedagogical approval and student-facing publication separate.

Consult the [research evidence](../references/evidence.md) when proposing evaluator changes or generalizing a result.
