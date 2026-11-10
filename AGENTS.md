# Repository agent guidance

## Commit attribution

When Codex materially contributes to a commit in this repository, append this trailer exactly once, after a blank line:

```text
Co-authored-by: Codex <codex@openai.com>
```

Preserve the trailer in the final commit message when squashing or merging, then inspect the resulting commit to verify it. Apply this guidance to new commits; do not rewrite existing history just to add attribution.
