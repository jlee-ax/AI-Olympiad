# Agent Skill Contracts (Draft for Discussion)

This file proposes reusable work procedures. These are not automatically installed platform skills, and they do not grant permission to invoke tools or run repeated work.

## 1. Research and Cross-Check Evidence

- **Inputs:** Question, application context, and existing materials. **Outputs:** Bibliographic information, verified original-source links, the claims they support, what they do not support, and uncertainties.
- **Procedure:** Prefer the original work or a reliable primary source. Record differences between the study design or population and this course. Keep official competition announcements separate from research papers.
- **Completion:** Link each key claim to its sources and limitations; mark anything that could not be verified as unverified.

## 2. Build the Learning Skill Graph

- **Inputs:** Confirmed scope, learners, prior knowledge, and evidence. **Outputs:** A draft of learning objectives, skills, prerequisite relationships, and assessment evidence.
- **Procedure:** Break skills into observable behaviors and state prerequisites and supporting evidence. Relatedness does not automatically imply causation or a prerequisite. Review dependency cycles.
- **Completion:** Identify the objective, prerequisites, assessment evidence, and open questions for each skill. Do not finalize them before discussion with the user.

## 3. Scoped Review and Change Impact Analysis

- **Inputs:** Baseline version, changed items, dependency graph, and assessment criteria. **Outputs:** Impact scope, checks run, failed, or not run, reasons for changes, and residual risks.
- **Procedure:** Starting with changed nodes, follow dependency relationships in reverse to identify affected nodes, while acknowledging that relationships may be missing. Record why any checks were omitted.
- **Completion:** Mark only checks actually performed as passed, and retain errors and unverified areas.

## 4. Iterative Review and Stop Decision

- **Inputs:** Previous record, current results, and agreed assessment and stopping criteria. **Outputs:** A decision (`continue`, `pause`, `stop`, or `blocked`), its reason, the proposed next step, and authorization status.
- **Procedure:** Compare with previous decisions and record the reasons and evidence for changes. Identify stagnation, conflicts, safety concerns, and authorization issues. Do not invent a numerical judgment if thresholds have not been agreed.
- **Completion:** Preserve the history and make the next action and any decision needed from the user clear. `continue` does not authorize automatic execution.

## 5. Handoff and Records

- **Inputs:** User requests, work and verification results, artifacts, evidence, and decisions. **Output:** A structured record distinguishing facts from proposals.
- **Procedure:** Do not record sensitive information or secrets; retain references and versions. Distinguish organizing records from deleting them.
- **Completion:** Another agent can understand the current state, open questions, next steps, and scope of authorization.
