# Addendum 01 — Preserve global guards separately from scoped content review

Recorded before reading the implementation candidate. This clarifies criteria v1 items 3/9/10; it does not weaken the original matrix.

An unrelated notebook/plan region can leave a particular content review current while the separate whole-artifact K01 binding, K08 execution receipt, K14 agreement, aggregate workflow context or complete joined source-catalog gate remains stale/blocked. The new feature must not force those gates green merely to demonstrate selective reuse.

Joined preflight already checks every declared local source catalog entry, including unused and historical entries. Preserve that behavior. A changed unused source can block that global source-catalog check while leaving unrelated unit content reviews reusable. ‘Unrelated review retained’ and ‘overall readiness continues’ are different assertions. Where all objects genuinely share a changed declared rubric/dependency, affecting all those objects is not an arbitrary blanket reset.

The actual old quality controls stay old and non-ready; a new fictional normal fixture is distinct from actual human review or user consent. No old real record is refreshed to create a passing real control.
