# AI Olympiad

A workflow prototype for preparing KOAI week 1–2 materials, with repository-local skills, source-linked records, and a read-only state planner.

## Start here

- Choose a [skill](skills/README.md) for the task.
- Read the [workflow and pending decisions](skills/references/workflow.md).
- Use the [tool contract](tools/README.md) and [state template](templates/workflow.json).
- Consult the [evaluation protocol](skills/koai-evaluate/references/evaluation.md) and [research evidence](skills/references/evidence.md) when making or reviewing a substantive change.

References live beside the skills and tools that use them. Skill instructions identify what to read; the CLI does not load Markdown or attest that an agent read it.

## Inspect state

Python 3.10+; the tools and tests use the standard library.

```sh
python3 tools/workflow.py validate templates/workflow.json
python3 tools/workflow.py decide templates/workflow.json
python3 tools/workflow.py fingerprint templates/workflow.json
python3 tools/workflow.py recall examples/workflow.json --query synthetic
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The template pauses because its criteria and budget are unset. The example is synthetic. The CLI checks record structure, version-bound reviews, source references, supersession, exact duplicates, budget limits, and checkpoint conditions. It reads JSON and prints an advisory result; it does not execute agents, write records, schedule work, create lessons, or operate GitHub.

A 30-minute checkpoint is a requested review interval recorded in state, not a running timer or a demonstrated optimum. Actual lesson production and recurring execution remain disabled until their concrete criteria are agreed.

A valid record cannot establish source truth, approval authenticity, independent judgment, or student learning. Digests and execution receipts must come from the real work; this tool does not authenticate them. It supplies no append-only storage enforcement or concurrent writer locking.

## Course scope

The draft target is KOAI 2027 middle-school preparation, with basic coding assumed and ten two-hour classes proposed. Learner prerequisites, week 1–2 objectives, and workload still need agreement. The [scope reference](skills/references/workflow.md#competition-scope-and-course-assumptions) distinguishes official rules from those draft choices.

## Earlier examples

`tools/validate.py` and `examples/graph.json` demonstrate graph-format checks. They cannot justify a verified claim or establish scholarly support. The older `templates/run.json` and `templates/review.json` are illustrative placeholders, not the workflow state contract.

No improvement in teaching quality, memory accuracy, unattended reliability, or human effort has been measured locally. See [third-party notices](THIRD_PARTY_NOTICES.md) for retained source and license information.
