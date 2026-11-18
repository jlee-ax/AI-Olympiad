# Imported custom metrics

External observations — SkillEvaluator did not execute these tests or verify their source claims.
Only JSON validation, custom-metric aggregation and paired comparison ran locally.
No canonical dimensions, Overall, pass/fail or publication evidence are assigned.

Source SHA-256: `1556122c87150c1684fbf76ab461395d43cbcb945b51071a4ff4d2759c545fc1`
Imported at: 2026\-11\-18T12:10:17\.913736\+00:00

## Declared provenance and evaluation context

- producer: anonymous semantic adjudication and generated rule\-based verifier replay
- run\_id: koai\-20261118\-blind\-depth
- created\_at: 2026\-11\-18T12:04:45Z
- dataset\_id: koai\-novice\-depth\-finite\-review
- dataset\_version: 1
- skill\_id: koai\-evaluate
- skill\_version: 356f74268ebf35f1d1d07b7f267534fa632e6fc1bf659798896a084f3ee41f06
- agent: Codex conversation subagent
- agent\_version: unspecified
- model: gpt\-6\.2\-astra \(requested\)
- environment: separate conversation sessions

## Custom scores (0-1)

Arm scores are means over available observations; n/total shows coverage, not test success.
Missing scores are excluded, never replaced with zero.

| Custom metric | Version | Unit | Direction | With skill (n/total) | Without skill (n/total) | Paired delta | Improvement | Paired cases/attempts |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| editorial\_review\_complete | 1 | fraction | higher\_is\_better | 1.0000 (11/11) | 1.0000 (11/11) | 0.0000 | 0.0000 | 11/11 |
| selection\_and\_probe\_correct | 1 | fraction | higher\_is\_better | 1.0000 (11/11) | 1.0000 (11/11) | 0.0000 | 0.0000 | 11/11 |

Paired delta is with-skill minus without-skill for matching case/attempt IDs in this declared context.
Matched attempt deltas are averaged within each case, then equally across cases.
It may differ from subtraction of arm means when coverage differs.
Improvement reverses the delta for lower-is-better metrics; positive means better.
NO SCORE means no compatible scored pairs, not zero lift. No statistical significance is claimed.
