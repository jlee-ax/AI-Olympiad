# AI Olympiad

A **pstack-derived design and validation prototype** for preparing KOAI week 1–2 materials. It includes repository-local skills, source-linked state records, and a deterministic decision planner. It does not generate lessons, run agents, schedule work, create PRs, or deploy anything.

The current user instruction authorizes improving this design and testing its tools. Real lesson production and recurring execution remain disabled until their concrete criteria are agreed. A saved approval field is a record to verify against actual user instructions, not an authority mechanism.

## Start here

1. Read [design and boundaries](docs/design.md) and [open decisions](docs/decisions.md).
2. Use the [five English skill entry points](skills/README.md).
3. Inspect the [workflow contract](docs/workflow-contract.md) and [disabled state template](templates/workflow.json).
4. Review [the evaluation protocol](docs/evaluation-protocol.md), [primary evidence](docs/evidence.md), and [pstack traceability](docs/pstack-traceability.md).

## Inspect state without executing work

Python 3.10+; the workflow tool and tests use the standard library.

```sh
python3 tools/workflow.py validate templates/workflow.json
python3 tools/workflow.py decide templates/workflow.json
python3 tools/workflow.py fingerprint templates/workflow.json
python3 tools/workflow.py recall examples/workflow.json --query example
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The template is deliberately incomplete for execution and should produce a pause decision. The example and automated tests use synthetic records, not student data or completed lesson work. The CLI reads state and prints JSON; it does not mutate records, run commands, contact services, or schedule another invocation.

## What the prototype checks

- Record shape, source references, supersession relationships, and version bindings.
- Whether recorded reviews apply to the exact artifact/context and contain the required passed checks.
- Duplicate completed attempts under matching inputs, skills, rubric, evaluator, and reference context.
- Missing agreement, finite budgets, checkpoint conditions, stopping reasons, and explicit no-change outcomes.

These are checks on recorded claims. The tool cannot establish source truth, pedagogical validity, actual review independence, approval authenticity, or student learning. Its input digests must be computed from real artifacts by the caller; it cannot attest that a supplied digest matches a file it has not read. It supplies no append-only storage enforcement or concurrent writer locking.

A requested **30-minute checkpoint** is planning metadata, not a scientific optimum, a hard process-kill boundary, or a running timer. A continue recommendation never grants permission to create a lesson, start recurrence, publish, merge, or change governing skills.

## pstack as the starting point

The design retains pstack's scoped recall, one-owner work units, independent verification, frozen measurements, keep/revert decisions, and structural correction before additional prose rules. Educational scope, evaluator calibration, record fingerprints, and explicit supersession are adaptations or supplements whose local benefit remains unverified.

Upstream baseline: Lauren Tan's [pstack v0.15.36](https://github.com/cursor/plugins/tree/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack), commit `c742dd61706fbacc1b95f1a20b7b988cf096ce6c` (2026-10-27). See [source-to-local mapping](docs/pstack-traceability.md) and [license attribution](THIRD_PARTY_NOTICES.md). Cursor-specific persistence and model routing are not implemented by copying these files. The [unofficial pstack-codex comparison](docs/codex-port-comparison.md) records host differences and the limits of file parity; that port was inspected, not installed or executed.

## Curriculum grounding

The course target remains a draft: KOAI 2027 middle-school preparation, with basic coding assumed and ten two-hour classes proposed. Confirm learner prerequisites and realistic homework time before producing materials.

The [published 2027 rules](https://kitpa.org/notice/89) cover syllabus sections 1–4 and written plus coding examinations for both divisions. The linked [syllabus](https://kitpa.org/koai/syllabus) still says IOAI 2026. Preserve both the rule year and the syllabus version; older sample notices do not define the 2027 scope.

## Earlier prototype files

`tools/validate.py` and `examples/graph.json` remain a basic graph-format demonstration with their original tests. That validator cannot justify a `verified` label or establish scholarly support. The older `templates/run.json` and `templates/review.json` are illustrative placeholders, not the new workflow state contract.

No measured gain in teaching quality, memory accuracy, unattended reliability, or reduced human effort is claimed. The evaluation protocol describes how to investigate those questions after the necessary criteria are agreed.
