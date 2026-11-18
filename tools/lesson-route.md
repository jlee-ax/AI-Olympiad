# Check a student route and a matched material comparison

Start where a student starts. Open the learning-material link in the Week 1 row of the course plan. Read the required entry, follow its instructions to the named sections, and take a conditional branch only when its stated trigger applies. The historical comparison starts at the corresponding link in the committed older plan.

The CLI needs a full Git checkout, Python 3.10+ and Mistune 3 to parse rendered notebook links. The notebook execution environment already includes Mistune via nbconvert. In a separate environment install `python -m pip install 'mistune>=3,<4'`. The existing topic-depth and quality CLIs retain their own dependencies.

```sh
case_dir=reviews/week01-replacement-20261118
python -B tools/lesson_route.py inspect --root . --route "$case_dir/route.json" \
  --incumbent "$case_dir/incumbent.json"
python -B tools/lesson_route.py check --root . --route "$case_dir/route.json" \
  --incumbent "$case_dir/incumbent.json" --protocol "$case_dir/protocol.json" \
  --results "$case_dir/results.json"
python -B -m unittest discover -s tests -p test_lesson_route.py -v
python -B -m unittest discover -s tests -q
```

The final command for the full suite also needs the dependencies used by the other repository tests. `inspect` verifies current files and returns the raw route hash, registered depth evidence hash and planned minutes. `check` returns zero for a complete, bound comparison and its permitted recorded recommendation. Read `decision`, `case_states`, `matched_rule_result`, `reviewer_checks` and `unit_coverage` to see the outcome. A documented retain or hold can accompany adverse, uncertain or conflicting evidence. Missing evaluation cases, stale bytes and unsupported promotion return a nonzero exit. Actual learner outcomes and time in class require observations.

## Route manifest

Use `schema_version: 1`, a distinct `id`, `entry` and optionally `week` (defaults to 1). Paths are canonical, repository-relative and symlink-free. `files` maps every relevant student notebook, teacher key and data file to its raw SHA-256. Extra bound evidence such as a workload ledger can be included. `companions` maps each notebook path to `teacher` and `data` arrays. Use an optional `after_attempt` array for delayed student-facing feedback that students can actually open through a text link. Keep teacher-only files out of student packets.

Each unit defines `id`, notebook `path`, ordered `cells`, `status` and `reason`. Give conditional units an observable trigger. The candidate includes nonnegative `class_minutes` and `homework_minutes` for every unit. Give each candidate unit its `class_range` and `homework_range` as inclusive minute pairs for a workload-bounded replacement. A point estimate alone is displayed as such. Put future material in `deferred` units with zero time. Name further curriculum deferrals in the surrounding scope notes when there are no current student cells to cite.

```json
{
  "id": "join-practice",
  "path": "lessons/week01/core.ipynb",
  "cells": ["choose-key", "check-rows"],
  "status": "required",
  "reason": "Choose a key before the first changed-table exercise.",
  "class_minutes": 0,
  "class_range": [0, 0],
  "homework_minutes": 20,
  "homework_range": [15, 25]
}
```

A unit owns each listed cell exactly once. Multiple routes into the same unit incur one charge. The candidate entry maps every reviewed student cell. Put `{"case":"reviews/week01-depth-20261118","round":4}` under `depth`, substituting the actual final ordinal. The normal topic-depth gate replays its append-only archive and checks the current companions. Required cells and the entry's class/homework totals must match the selected round. The actual reviewed cells constrain each unit's class and homework assignment, including when multiple units split a topic. Conditional and required linked work add to the weekly upper bounds. Give an `overrun` explanation when those bounds exceed the plan. A shorter homework plan uses `shorter_homework_reason` to explain maintained coverage.

Each item in `links` gives `from`, source `cell`, `to` and `href`. The cited Markdown cell must render a visible text link to the destination unit's first cell. A bare notebook URL opens its first physical cell. To enter a later section, use a unique anchor, the heading fragment, or a JupyterLab cell fragment such as `core.ipynb#cell-id=choose-key`. Later declared units in the same notebook are accessible in reading order. A required unit must be reachable without a conditional detour. Quoted code, HTML comments, images, wrong fragments and extra files in a packet confer no teaching credit. Reviewers check whether the text actually directs the learner to the work. [JupyterLab notebook section links](https://jupyterlab.readthedocs.io/en/stable/user/urls.html#linking-notebook-sections)

Use the same inventory, links and unit statuses for the incumbent, with its full historical `basis_commit` and a truthful `timing` description. Read its plan, notebooks, data and teacher keys from Git at that ancestor, including when a live path has since changed or disappeared. The report shows the archived URL and whether its named Git reference is locally available. A retired branch can be reconstructed from the actual historical material-column link and the pinned file blob. The historical timing description can record an unknown combined burden.

## Freeze and blind review

Commit `protocol.json` before the finalist revision. Include `schema_version`, `id`, `maker`, unique `case_ids` and an `inputs` mapping of paths to raw hashes of the prompts, data, scoring rules and verification materials. Publish sealed bytes at those paths after judging. The public freeze carries their hashes. Supply `candidate_before_revision` with an ancestor `commit` and the entry's raw `sha256` (null for an absent entry) to verify the baseline and that student materials stayed unchanged through the freeze. Optional `required_cases` defaults to all cases. Optional `groups` may specify `safety`, `burden`, `regression` or `replication` case lists. A `conditional_cases` list identifies prompts whose support legitimately depends on a remedial branch.

The Week 1 protocol selects `replacement_rule: "matched-giwt-v1"` and four required cases. Each independent reader records the material they used, judgments and evidence against opaque side labels. A blind original is JSON with these fields, directly or under `route_evidence`.

| Field | Contents |
| --- | --- |
| `reviewer` | Reader identity used in the wrapper |
| `subjects` | Map of two opaque labels to exact raw route-manifest hashes |
| `protocol_sha256`, `depth_sha256` | Raw protocol hash and the candidate's current `inspect` depth evidence hash |
| `cases` | Case ID to both opaque labels' observations. Optional `outputs` on the case maps raw output paths to hashes. |
| `checks` | Each blind label maps `preservation`, `prerequisites`, `execution`, `workload`, `serious_faults_absent` to JSON true, false or `"?"` for this rule. |

An observation carries `verdict` (`pass`, `revise` or `uncertain`), a specific `finding` and `cells` mapping unit IDs to actual student cell IDs. Cite required or appropriately triggered material. A wholly unsupported adverse judgment may cite an empty map and identify the gap. A positive bit requires student evidence. For Week 1, include a `bits` map of G, I, W and T to 0, 1 or `"?"` and the Boolean `fatal`. Retain each reader's per-bit reasoning and task output in the original.

For shared workload, preservation, rendered packet or execution evidence, commit a map `{"schema_version":1,"files":{"repo/path":"raw SHA-256"}}` before rating. Give readers its opaque raw digest and record it in each original's `evidence_sha256`. Bind the map in the result under `evidence: {path, sha256}`. Files already public must match at this commit. Withheld packet files can first appear later. All listed bytes are checked after disclosure.

After both originals are fixed, store a wrapper per reader in `assessments/*.json` beside the result. A protocol with a precommitted `allocation_sha256` verifies the revealed `comparison/assignment.json` next to the results manifest, both role labels and the counterbalanced assigned reader orders. An optional `assignment` path/hash on the result can point to an alternate location. The native reader's optional `order` must match its assignment.

```json
{
  "schema_version": 1,
  "reviewer": "reader-name",
  "original": {"path": "reviews/case/originals/reader.json", "sha256": "<raw hash>"},
  "labels": {"candidate": "B", "incumbent": "A"}
}
```

A direct receipt can instead carry the observations under `candidate` and `incumbent`, with `candidate_sha256` and `incumbent_sha256`. Use blind originals for the registered final comparison. Readers, their independence and their findings remain accountable human declarations.

In `results.json`, set `schema_version`, the complete `freeze_commit`, `depth_sha256`, a `finding`, and the manual branch `decision` of `retain`, `hold`, `pilot` or `replace`. Bind each `candidate`, `incumbent` and `protocol` as a `{path, sha256}` object. The `assessments` path-to-hash map includes every independent wrapper. A pilot names the supported subset in `pilot_cases`. For a partial task, `pilot_bits` can map its case ID to the specific agreed bits proposed for the pilot. Committed independent receipts, originals and named outputs remain append-only. A new comparison after a material or scoring change needs fresh, bound independent work and a new freeze if the evaluation changes.

## Reading the four-case decision

G, I, W and T cover choosing a method, implementation and checking, reasoning and conditions, and transfer to a changed input. Each reader's affirmative bits count once. An unknown contributes zero. Four bits make a case sufficient, two or three partial, and one or zero insufficient. A fatal judgment makes a case insufficient. The report preserves disagreements and each original finding.

Full replacement requires at least three supported bits on each task, three fully supported tasks, preservation of previously supported bits and agreed new bits on at least two tasks. One gain must involve G, W or T. A supported gain needs evidence from both routes. Independent candidate checks for preservation, prerequisites, execution, workload and serious errors must all be affirmative. The candidate's charged time upper bounds must fit the weekly budget. A partial pilot identifies which claims earned agreement. A valid evaluation can end with retaining the incumbent.
