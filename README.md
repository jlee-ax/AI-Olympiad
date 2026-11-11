# AI Olympiad

![Towards the International AI Olympiad](assets/readme/towards-international-ai-olympiad.png)

A workflow prototype for preparing KOAI teaching materials, with repository-local skills, concrete quality criteria, source-linked records and deterministic inspection/planning tools.

## Confirmed course inputs

Middle-school learners with basic coding; **ten weeks, one 120-minute class each week**. These are user-specified inputs. Required and optional outside work remain separate. The earlier 240-minute schedule is superseded.

The [existing student HTML](curriculum/student-plan.html) is preserved in Korean without content changes. The [curriculum contract](curriculum/contract.json) records its weekly allocations and all 60 official syllabus rows. Planned coverage does not establish completed material or student mastery.

## Start here

- Choose a [skill](skills/README.md).
- Read the [concrete specification](skills/references/quality-specification.md) and relevant entries in the [16-criterion catalog](skills/references/criteria.json).
- Review theory with the [notation, derivation, diagram, algorithm and comprehension rubric](skills/koai-evaluate/references/theory-explanation.json).
- Use the [eight week 1–2 unit specifications](skills/koai-evaluate/references/unit-specifications.json) for prerequisite tasks, theory/noncoding/coding/assessment behaviors and existing time placement.
- Inspect the [source-reading register](skills/references/source-readings.json), [research evidence](skills/references/evidence.md), and [evaluation protocol](skills/koai-evaluate/references/evaluation.md) for substantive decisions.
- Read the [state and CLI contract](tools/README.md) before recording decisions.

Skill references are read instructions. The CLI does not automatically load every Markdown file or prove that an agent read it.

## Inspect and plan

Python 3.10+; tools and tests use the standard library.

    python3 -B tools/quality.py baseline
    python3 -B tools/quality.py evaluate templates/quality.json
    python3 -B tools/quality.py plan templates/quality.json
    python3 -B tools/workflow.py decide templates/workflow.json
    python3 -B -m unittest discover -s tests -q

The baseline command reads actual student HTML bytes, visible time allocations and scope rows. The quality tool independently calculates supported finite math cases, binds reviews to actual regions and dependencies, inspects source/research receipts, reports impact and suppresses exact repeated proposals. Its planner applies explicit priorities, finite budgets and the requested 30-minute checkpoint.

For a runnable schema demonstration, use the explicitly [synthetic quality bundle](examples/quality.json), its [bound workflow state](examples/quality-workflow.json), and [fixture receipt](examples/quality-receipt.json). These are not actual lesson or learner records.

The default quality bundle has no learner responses, lesson executions, semantic reviews or agreed numeric policy. It remains incomplete. Non-design workflow decisions additionally require a current bound quality assessment; see the tool contract.

## Evidence and operating limits

A current source/review record is an accountable claim, not authenticated truth. Semantic correctness, educational suitability and learning effectiveness need their own evidence. The implementation does not run Jupyter, browse sources automatically, execute a worker or schedule another invocation. A 30-minute checkpoint is a reported review condition, not a running timer.

Current work implements specifications and checks. Actual lesson production and recurring execution require their concrete criteria and applicable authorization. No locally measured teaching gain is claimed. Diagnostic cutoffs, acceptable outside workload, calibration tolerances and total campaign budgets remain unset.

The earlier graph validator and illustrative graph/run/review files remain available for compatibility. They cannot justify a verified educational claim. See [third-party notices](THIRD_PARTY_NOTICES.md) for retained source/license information.
