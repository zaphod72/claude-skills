---
name: root-cause-fix
description: "Use before writing any fix for code review findings — including right after /code-review or /code-review --fix produces findings, after a human posts PR review comments, or whenever the same file/area has drawn findings across more than one review round. Reads the plan, the PR description, and the implementation for discrepancies between them, groups every outstanding finding by root cause, and produces a fix plan organized by root cause instead of one fix per finding. Also directly invocable with a planning-doc reference, e.g. `/root-cause-fix 461 @docs/plan.md`."
---

# Root-cause fix planning

Findings get fixed one at a time, and the same area keeps drawing new findings every round because the fix addressed the symptom, not the root cause. This skill runs before any code changes: diagnose what the findings have in common, then plan around the root cause.

**Verify before grouping.** A finding whose citation no longer matches the code, or that names a
file outside this PR's scope, poisons the root-cause grouping — it invents a shared cause out of a
stale claim. Classify each finding as stale, wrong, or live first: see the
`claims-and-scope-discipline` skill.

## Steps

### 1. Gather the record

Collect, for the PR under review:

- **The plan** — a planning-doc file if one was passed as `@<path>` in the invocation; otherwise the PR description and any linked issue/ticket are the plan.
- **The PR description** — `gh pr view <n> --json body,title`.
- **The implementation** — `gh pr diff <n>`, scoped to the changed files.
- **Every review round on record** — automated findings (this session's review output, prior `ReportFindings` calls) and human reviewer comments (`gh pr view <n> --json reviews,comments`). Pull all rounds, not just the latest; a finding repeated across rounds is itself evidence for step 3.

Done when every source above is quoted at the specific line or passage relied on, not paraphrased from memory.

### 2. Check for discrepancies

Compare the sources pairwise. Record every mismatch, quoting both sides:

- **Plan vs. description** — does the PR description claim something the plan doesn't, or drop something the plan requires?
- **Plan/description vs. implementation** — does the code do something neither called for, or skip something they did?
- **Review vs. plan** — does a reviewer's explanation of a problem contradict what the plan says the code is supposed to do? This flags a review arguing against the design, which needs a different response than a code fix — e.g. correcting the plan/description, or explaining the design decision back to the reviewer.

Zero discrepancies is a valid result.

### 3. Group findings by root cause

Take every open finding from every round gathered in step 1. A **root cause** is one design flaw, missing abstraction, or unenforced invariant that produces more than one symptom. Two findings share a root cause when fixing one the right way would have prevented the other, regardless of file or round.

Assign every finding to exactly one group. A group of one is fine for a genuinely isolated finding — but check first: a finding that recurred after an earlier fix almost always belongs to a group, not a singleton.

### 4. Diagnose each group

State the underlying problem in one sentence per group: what invariant is missing, what responsibility is split across call sites that shouldn't be, what contract nobody enforces. Not "these lines are wrong" — why the same mistake stayed an available choice after the last fix.

### 5. Plan the fix, by root cause

For each group, propose one structural change that removes the root cause — a shared helper, a single write path, an enforced contract — sized to eliminate every finding in the group at once. Fold each discrepancy from step 2 in as its own line item (e.g. "update the PR description," "the plan needs to state X").

Order groups by how many findings/rounds each explains, most first.

### 6. Stop

Hand the diagnosis and plan to the user for approval. Implementation is a separate, later pass.

## Output shape

Per root-cause group:

- **Root cause** — the one-sentence diagnosis
- **Findings it explains** — file:line, tagged with which round each came from
- **Fix** — the structural change, and which individual patches it makes unnecessary

Plus a **Discrepancies** section for anything found in step 2, including ones that don't map to any root-cause group.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/root-cause-fix-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
