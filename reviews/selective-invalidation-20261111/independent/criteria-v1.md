# Selective review invalidation — independent criteria frozen before candidate

Scope: read-only inspection of recorded review currency after changes to plan, lesson, or declared evidence. No lesson edits, no automatic work/review/approval, no full re-review triggered merely by a changed whole-file hash. Hashes detect a changed declared context; they do not decide whether a lesson is correct, adequate, equivalent, or improved. Human semantic judgment remains necessary.

The reviewer read the existing closure/object_fingerprint/_review/K12/evaluate/plan/CLI and workflow/preflight integration at baseline commit `76b680d64548af5c87d0455008b25358af06a698`, existing normal/fault/history tests and real old quality records. The implementation candidate has not been read. Later criteria changes require a separate addendum; do not overwrite v1 to favor the result.

## Expected behavior

1. **Explicit affected review records.** A changed declared/relevant dependency yields an auditable per-object/criterion indication that review is required/current context is unreviewed or stale. List affected latest review IDs, object/criterion, and a structural reason/dependency where feasible. Merely failing global baseline K01 or changing an overall bundle hash is insufficient to mark what must be revisited.
2. **Plan relevance.** A lesson unit's stated week and syllabus IDs can establish relevant plan week/scope regions. Changing week1 or one of that unit's scope requirements invalidates that unit's applicable reviews and dependent claims/reviews, without invalidating unrelated week2/other-scope units unless they share the changed dependency. Applicable contract/blueprint fields follow the same selective rule. Unknown/absent week/scope/locator is a gap/invalid/uncertain context, not a silent current pass.
3. **Artifact relevance.** A changed reviewed primary/role/explanation/upstream-claim cell or displayed attachment/output invalidates its dependent review. An unrelated undeclared cell does not invalidate this content review solely because artifact SHA changed. Whole artifact binding/execution readiness may separately fail; retain that distinction. Execution counters alone remain non-semantic bookkeeping where the existing contract excludes them.
4. **Evidence relevance.** Change or remove an actual local source/evidence file used by the reviewed object's declared dependency closure and mark the affected review; preserve unrelated objects. Test source declarations, dependency-node path, and current review evidence paths according to the supported schema. Missing files/locators are explicit gaps or safe invalid-input failures, never unchanged/current approval. Retain confinement/root-escape checks.
5. **Shared/transitive paths.** A shared source/claim/plan scope can affect multiple consumers; a transitive upstream change reaches all declared consumers, not just the nearest edge. An isolated source affects only its consumers. A node declaration revision/digest change and an actual local-file change with unchanged declaration must both be detected within declared coverage.
6. **Declaration gaps.** Missing referenced dependency nodes/edges, missing required bindings inferred from available unit metadata, unknown source IDs and missing local files are exercised. No invented dependency makes everything pass. If a semantically relevant source was omitted from every available declaration, software cannot infer it: report the coverage limit/manual obligation rather than claim comprehensive dependency discovery. Do not use global invalidation as a substitute for explicit selective coverage.
7. **Append-only history.** Old records remain byte-for-byte/in-memory unchanged. Appending a genuinely new review record for current context makes it active for its object/criterion and leaves prior records historical. A stale old record does not veto a current new record. Software does not create a review, refresh its fingerprint, rewrite evidence, or assert reviewer independence on the caller's behalf.
8. **No fallback to old pass.** Appending current failed/uncertain/not_run, or a stale latest review, cannot be replaced with an older passing record. Last appended record per current object/criterion retains the existing selection contract. Adding a record for an unrelated/retired object does not supersede the current object. Research-cycle behavior, if touched, retains the corresponding last-record rule.
9. **Read-only and preservation.** API/CLI inspections do not mutate bundle dictionaries, source/artifact files, review history, index, or remote. Tests mutate only copied fixtures below this independent directory. Original lessons and real old evidence stay unchanged. No append is made to real records; any new passing reviewer statements are explicitly fictional software controls.
10. **CLI and connected gates.** Expose explicit re-review information through the documented API/CLI and normal quality evaluate/plan path; joined preflight/workflow must not treat stale/invalid quality as continuing/readiness. Preserve documented distinctions between parse success/exit0 and passing readiness; malformed input errors must remain structured/safe. A new standalone report is insufficient if ordinary readiness still reuses old passes.
11. **Real and normal controls.** Run at least one actual old quality bundle (prefer `reviews/week01/final-followup/quality.json` and `reviews/system-followup-20261111/current/quality.json`) against actual current inputs without manufacturing reviews to make it green. Record preexisting stale/blocked conditions separately from new behavior. A separate fresh explicit synthetic normal control must start with current review records and prove neighboring unrelated edits stay current.
12. **Honest reporting.** Preserve failed intermediate tests, unexpected results, and the exact code/input SHA. Distinguish implementation bugs from harness bugs, expected fault rejection from successful execution, and structural dependency currency from semantic adequacy/student learning. New final code SHA is required before final review; recheck fixes at that SHA.

## Fixed fault/normal matrix

| ID | Scenario | Expected structural outcome |
|---|---|---|
| C00 | Fresh current control with at least 2 independent units/claims and current reviews | Current per-review states; no automatic semantic/learner claim |
| P01 | Relevant week1 text/link/markup changes | Week1 consumers require explicit re-review; independent week2 remains current |
| P02 | Unrelated week9 change | Current week1/week2 content reviews retained, global pinned baseline may separately fail |
| P03 | Relevant scope row / topic requirement changes | Only mapped scope consumers plus transitive consumers require re-review |
| P04 | Unrelated scope / unrelated contract topic changes | Unmapped consumers unchanged; no blanket clearing |
| A01 | Bound lesson role/code/assessment/upstream claim cell changed | Dependent latest reviews stale/re-review |
| A02 | Unbound other cell changed | Content reviews retained; full-artifact validity handled separately |
| S01 | Bound local source bytes change with old manifest digest | Affected consumer re-review, unrelated review current |
| S02 | Bound local source absent | Explicit affected gap/re-review or structured invalid; never current pass |
| S03 | Unused source file change | Unrelated object currency retained within declared coverage |
| D01 | Missing referenced node/edge / required binding / known unit metadata | Invalid or explicit dependency gap; no false current pass |
| D02 | Undeclared-to-all external dependency | Limit/manual coverage gap acknowledged; no claim hash detected its meaning |
| H01 | Append current new pass after old stale | New active, old retained historical, no source/history mutations |
| H02 | Append failed/uncertain/not_run after pass | Latest status retained, no old-pass fallback |
| H03 | Append stale latest / unrelated historical object | Latest current-object stale blocks; unrelated historical append does not |
| R01 | Actual old quality bundle and ordinary evaluate/plan | Explicit affected old reviews visible, preexisting non-ready conditions retained |
| I01 | CLI/API and workflow/preflight integration | Consistent affected state, no stale readiness; read-only hashes preserved |

This matrix fixes expected categories before implementation. Exact supported API names/output fields may be adapted to the candidate's documented contract; semantic expectations may not be weakened. No new lesson, syllabus, learner, or automatic review-generation feature is authorized by this review.
