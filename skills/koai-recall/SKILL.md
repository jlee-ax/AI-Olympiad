---
name: koai-recall
description: Recover the current KOAI task state from source-linked records and live artifacts. Use when resuming work, checking earlier decisions, avoiding redundant work, or resolving stale and superseded memories.
---

# Reconstruct current state

Read [the workflow contract](../../tools/README.md). Scope retrieval to the requested project, topic, and period. Use the user's supplied state capsule when it is sufficient; do not mine unrelated conversations.

1. Validate the state and run `python3 tools/workflow.py recall PATH --query "TOPIC"`. This is lexical retrieval of active records, not semantic deduplication, truth verification, or a complete search of external history.
2. Read each consequential source pointer and the current artifact. Distinguish a past decision, an observed result, a proposed rule, and a learner observation. Do not turn a past agent assertion into a verified fact.
3. Check supersession, source versions, current requirements, and the complete context fingerprint. Exclude superseded records from current recommendations while preserving them as history. Report competing unsuperseded records as a conflict; do not silently choose the most recent wording.
4. Before repeating work, inspect prior accepted and rejected attempts under the same inputs, skills, rubric, evaluator, and references. Reuse unchanged verified work. A changed source or a newly discovered defect can justify another attempt; record the difference.
5. Treat paraphrased duplicates as candidates for review. The current tool does not establish semantic equivalence. Do not merge distinct concepts or erase negative results to simplify retrieval.
6. When recording a correction, append a source-linked replacement and explicit supersession relationship. Recheck any review whose inputs changed. Do not edit the evaluation baseline merely to preserve a passing result.
7. Return a short capsule: current goal/scope; artifact and review revisions; applicable decisions; relevant failed attempts; stale/conflicting evidence; next justified action.

## Completion

Every reused conclusion traces to its source and current scope. Missing or unavailable evidence is marked as such. A retrieved memory does not authorize lesson generation, recurring execution, or publication.

Compare supersession and fingerprint-based reuse with simpler records before expanding storage; their local benefit remains unverified.

## Concrete decision contract

Use [selective impact and duplicate-work rules](../references/quality-specification.md#selective-impact-and-duplicate-work). Run the quality impact query for changed source/claim IDs. Reuse current per-object content reviews when their actual region and relevant source meaning/version are unchanged; an access-time-only refresh is not a reason for global rewriting. Preserve rejected/no-change attempt keys. New action, hypothesis or evidence is an explicit change, not a paraphrase-based automatic merge.
