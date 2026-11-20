# Revise and recheck lesson content

Review the explanations, prerequisites, problems, answers and code in the lesson. Count no points for the number of equations or illustrations. Correct claims about learning gains that the review cannot support. Actual student responses, achievement and classroom time are outside this material review.

## Choose an edit from source evidence

1. Before reading the lesson outline, identify the target ability, prerequisites, required depth and an independent task in official scope, competition problems and relevant technical sources. Record the source location and the limits of the inference.
2. Read the teaching and assessment locations throughout the lesson. Identify missing capabilities, insufficient explanations, genuine duplication and terms used before they are introduced. Record sound foundations as well. A confirmed gap can enter `quality.py plan` even when the capability is absent from the registered units.
3. Add an `edit` to the discovery comparison. If the intent is still open, the planner selects `design_content_revision` with the demand, sources and locations. Resolve uncertain evidence before selecting the change.
4. A revision may combine actions. When adding an explanation, consider which repetition can be merged or removed. Record `kind`, `before`, `after`, `reason`, `alternative` and `postcondition` for every action. The before and after lists contain notebook cell IDs.

| Action | Observable change |
|---|---|
| `add`, `deepen`, `replace` | Add the required content or change the actual conditions or reasoning in an explanation. |
| `merge`, `remove` | Reduce duplicated material while retaining the capability and an independent task. |
| `reorder`, `move` | Change actual cell order. To defer an obligation to a different week, record its destination, owner and plan evidence under `deferred` in the discovery loop. |
| `keep` | Preserve a sound foundation. A fully covered comparison needs no revision candidate. |

For each demand dimension, `edit.routes` records the before and after routes in reading order, including prerequisites, explanations and tasks. A newly discovered gap may have an empty before route. Add routes for other capabilities that need protection. The independent reviewer reads the entire revised lesson and checks the physical changes against the declaration.

## Run the revision

```sh
python3 tools/quality.py plan bundle.json --root .
python3 tools/workflow.py repair workflow.json --quality bundle.json --root .
python3 tools/material_revision.py apply workflow.json bundle.json patch.json candidates/lesson.ipynb --root .
python3 tools/material_revision.py verify workflow.json bundle.json patch.json candidates/lesson.ipynb --review review.json --root .
python3 tools/discovery_loop.py step discovery.json --event advance.json --root .
```

`repair` checks approvals, budgets, baseline, change history and discovery evidence. `decide` reports the resulting state. Bind the input bundle and cases to the manifest for the same review. Recompute the work key after the source, lesson or rule version changes. The plan records skipped candidates and reasons in `skipped`.

A patch supplies the selected `work_key`, the actual `author` and `operations`. An `insert` takes a new ID, type, source and the following cell ID in `before` (null for the end). A `replace` takes an existing ID and new source. A `move` or `remove` addresses an existing ID. Create the parent directory first. The tool checks required paths, unrelated cells and notebook metadata before atomically creating the external candidate. Repeating identical content reuses the candidate.

A review needs `candidate_sha256`, `work_key`, `reviewer` and `checks`. The reviewer is distinct from the editor. For each action such as `action:0`, each route such as `route:learning`, and `new_input`, `boundary` and `regression`, record the judgment, real cells, observation and digest-bound evidence. The new-input and boundary checks use different case IDs. Their evidence JSON binds the candidate digest and each case's `id`, `input`, `expected` and `actual`. The tool compares expected and reported values. Reviewer identity, source meaning and whether the reported execution actually took place require independent evidence.

An `advance_lesson` event includes the common `reason` and `workflow_path`, `quality_path`, `patch_path`, `candidate_path`, `review_path` and `revision`. Only a reverified candidate becomes the next baseline. Keep the original and event history. The new artifact still needs source comparison and final review. Before distribution, use `decide` to confirm that the independent review matches the current material. Save command output to a new history file.

## Findings by review purpose

- For a scoped introductory unit, K02 checks the later week, unit, task and all practical topic IDs. Bind the subsequent week's `continuation.plan_locator` to the unit's plan dependencies. Full-scope completion requires current practical evidence. A lesson containing actual code cells also needs execution checks.
- K04 checks each prerequisite's `id`, `task`, `expected`, `support_before_use` and independent K04 content review. The support fields `before_unit`, `locator` and `first_use` must point to the actual unit and location. A reviewer checks order and validity within a cell. Supplement records containing only historical learner responses with evidence about the design.
- K15 checks whether the material review introduces unsupported claims about student effects. Qualify an evaluator with `python3 tools/quality.py qualify qualification.json --root .`. Supply the domain, distinct author and reviewer, evaluator code digest, file-backed normal and faulty controls, and declared tolerances. Reuse a result for the same evaluator version and domain.
- Unresolved demands from required sources block completion. A question limited to background references needs `purpose: background` and a `scope_reason`. Compare every actual demand found there. If a required source was read and yielded no demands, a separate reviewer can record `exclude_probe` with evidence. For a peripheral question derived from a required source, use `exclude_question` with the original reading and an independent scope judgment. Source changes reopen the question. The extractor cannot approve their own exclusion or convert a required question to background work.

The repository tests exercise the full revision and resume sequence. [Material revision tests](../tests/test_material_revision.py)
