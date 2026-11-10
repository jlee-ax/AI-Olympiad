# KOAI repository skills

These five skills describe task procedures. They are repository-local files, not an installed personal plugin or an automatic execution system.

| Task | Skill |
|---|---|
| Establish current sources, scope, and learner constraints | [koai-ground](koai-ground/SKILL.md) |
| Coordinate one bounded unit and its checkpoint | [koai-orchestrate](koai-orchestrate/SKILL.md) |
| Resume from current, source-linked records | [koai-recall](koai-recall/SKILL.md) |
| Review exact revisions and calibrate evaluation | [koai-evaluate](koai-evaluate/SKILL.md) |
| Propose measured improvements to tools or skills | [koai-reflect](koai-reflect/SKILL.md) |

Ask an agent to read the relevant SKILL.md. Keep its relative references intact. A compatible host may load repository skills through its own configuration; the `agents/openai.yaml` files are display metadata, not installation. There is no automatic document injection or proof-of-reading mechanism.

The usual path is ground → recall → orchestrate → evaluate. Reflect runs when recurring evidence warrants a workflow change. Read the references needed for that task rather than loading the whole library.

Use the [concrete quality specification](references/quality-specification.md) and relevant [catalog entries](references/criteria.json) for definitions, measurements, failures, uncertainty, priority and effect hypotheses. The [week 1–2 unit specifications](koai-evaluate/references/unit-specifications.json) define actual production objects and prerequisite tasks.

Shared references contain [the workflow and pending decisions](references/workflow.md) and [research evidence](references/evidence.md). Detailed [evaluation guidance](koai-evaluate/references/evaluation.md) belongs to the evaluation skill; [state and CLI documentation](../tools/README.md) lives beside the tool. The [template](../templates/workflow.json) is inactive until configured from real decisions.

Educational benefit and reduced human effort remain hypotheses. Source and license information is retained in [third-party notices](../THIRD_PARTY_NOTICES.md).
