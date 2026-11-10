# KOAI repository skills

These five repository-local skills adapt Lauren Tan's pstack. They are authored skill files, not an installed personal plugin, a scheduler, or authorization to act.

| Task | Skill |
|---|---|
| Establish current sources, scope, and learner constraints | [koai-ground](koai-ground/SKILL.md) |
| Coordinate one bounded unit and its checkpoint | [koai-orchestrate](koai-orchestrate/SKILL.md) |
| Resume from current, source-linked records | [koai-recall](koai-recall/SKILL.md) |
| Review exact revisions and calibrate evaluation | [koai-evaluate](koai-evaluate/SKILL.md) |
| Propose measured improvements to tools or skills | [koai-reflect](koai-reflect/SKILL.md) |

Ask an agent to read the relevant SKILL.md in this repository. A host that supports repository skills may load them through its own configuration; no automatic discovery or cross-model orchestration is assumed here. Keep the repository-relative references intact when using them. The `agents/openai.yaml` files provide display metadata, not installation.

The ordinary path is ground → recall → orchestrate → evaluate. Reflect runs when recurring evidence warrants a workflow change, not automatically after every checkpoint. Read only the relevant skill and linked contract/protocol.

The [workflow CLI](../tools/workflow.py) validates recorded state and recommends a decision. It cannot establish semantic truth, authenticate approvals, execute a worker, create PRs, or schedule another run. Start with [the contract](../docs/workflow-contract.md) and [disabled template](../templates/workflow.json).

See [pstack traceability](../docs/pstack-traceability.md) for retained/adapted/supplemented/unverified choices and [third-party attribution](../THIRD_PARTY_NOTICES.md). Educational benefit and reduced human effort remain hypotheses until locally evaluated.
