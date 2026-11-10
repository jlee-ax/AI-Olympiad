---
name: koai-reflect
description: Propose tested improvements to KOAI workflows from repeated, evidenced failures. Use after a bounded campaign or recurring correction to decide whether to revise a tool, existing skill, or memory policy.
---

# Convert evidence into a bounded improvement proposal

Read [traceability](../../docs/pstack-traceability.md) and [evaluation protocol](../../docs/evaluation-protocol.md). Work from actual scoped records; label synthetic cases. Do not treat a one-off preference or an unverified agent explanation as a general lesson.

1. Group recurring mistakes by mechanism and cite the distinct occurrences. Separate missing information, stale retrieval, tool failure, incorrect reasoning, weak evaluation, and scope drift.
2. Seek judgment, tooling, and alternative-explanation reviews. Give reviewers the original evidence, not a suggested diagnosis. Synthesize accepted candidates, rejected ideas with reasons, and a backlog.
3. Prefer removing the cause structurally. Compare a tool/check improvement, an edit to an existing procedure, and a new prose rule. Demonstrate that a proposed check catches a real prior failure while allowing a neighboring valid case.
4. For each candidate, name the current baseline, exact proposed change, supported mechanism, research source and counterevidence, local assumptions, expected benefit, cost, and disconfirming result.
5. Compare the candidate against the existing pstack-derived procedure under matched model/tools/source/compute conditions. Include unseen related tasks and regressions. Do not count more calls, more instructions, or a higher self-score as durable learning.
6. Propose the smallest edit. Keep source records and failed attempts available without loading every record into every future prompt. Preserve the original version for rollback.
7. Present the accepted/rejected/backlog disposition and the concrete diff. Changing shared governing skills, evaluation criteria, or execution authority requires the corresponding user decision; prior permission for a lesson does not imply those changes. Do not auto-install, auto-publish, or silently activate a candidate.
8. Record only checks actually run and their limitations. When no candidate demonstrates a useful benefit, keep the current procedure and report no change.

## Result

Return a reviewable improvement proposal, provenance, bounded evaluation results or an explicit “not evaluated,” and the decision needed for activation. Never claim the underlying model learned new weights.

## Origin

Retain pstack [Reflect](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/reflect/SKILL.md) and [Correct](https://github.com/cursor/plugins/blob/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack/skills/correct/SKILL.md), including structural correction before additional instructions and explicit skill-change review. See [attribution](../../THIRD_PARTY_NOTICES.md).
