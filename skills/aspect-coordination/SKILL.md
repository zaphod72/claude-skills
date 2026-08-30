---
name: aspect-coordination
description: "Run one aspect of a multi-agent implementation as its coordinator: own the aspect branch, merge story agents' PRs into it, drive review-and-fix cycles on the merged result, write the PR's review-recommendations section, and decide which discovered issues become tickets versus direct fixes. Use when coordinating several coding subagents against one aspect branch, when deciding whether review findings warrant tickets or fixes, or when acting as the middle layer between a top-level orchestrator and coding subagents. Not wave computation for the whole plan (implement-plan), the initial partition and dispatch of it (ticketed-plan-rollout), control flow above this level (parallel-agent-orchestration), or git/worktree mechanics underneath (git-worktree-topology)."
---

# Coordinating one aspect

You are the middle layer of a parallel implementation: coding subagents below, an orchestrator
above. You own one aspect branch and everything merged into it. The role is self-similar — a
coordinator-of-coordinators runs this same loop one level up, with aspect branches as its children —
so nothing here changes with altitude.

## 1. Own the aspect branch

- Name it under the run's flat prefix (`git-worktree-topology` §1) and derive its base from where
  HEAD actually is — never accept a passed-in base (§2a, §3).
- Story agents dispatch in their own worktrees. Brief them with the full demand list in
  `parallel-agent-orchestration` §4: evidence not conclusions, commit incrementally,
  refuse-a-wrong-instruction, check the tickets' sequencing notes against your order, the
  deploy-gate question, background long suites, tee output you will need.
- Your turn ends every time you dispatch one of them. Only the orchestrator advances you; hold
  still while a child runs — no side work in the shared tree.

## 2. Merge children, then review the merged result

Story PRs merge into the aspect branch with `--merge`, in order (`git-worktree-topology` §3). The
merged result then gets reviewed before it moves up:

- **Request review in your report; never spawn a reviewer yourself** — see
  `parallel-agent-orchestration`'s "Reviews execute here" section (under its §1). Fixes route back
  down to you.
- **Fixes are yours, ticket-free by default.** A review finding inside your scope is fixed by you
  directly; the fix does not need a ticket.
- **Low-level items are your judgment call** — fix or defer, and say which.
- **Two review-and-fix cycles is the limit** — same section as above.
- **Tangential discoveries get tickets.** Review often surfaces issues unrelated to the PR — those
  follow the outward-leakage rule (`claims-and-scope-discipline` §6): reported, ticketed, kept out
  of this scope.

When the aspect branch survives review, its PR goes to the top-level branch — human-merged where
the run's gates say so.

## 3. Write the review-recommendations section

Every PR you open carries one, in the description:

- what was reviewed, and at what depth;
- cross-cutting concerns the level above should look at;
- what explicitly does **not** need re-review.

The top level aggregates these sections into its integration digest rather than re-deriving them
(`claims-and-scope-discipline` §9) — so a reviewer of the big merge skips covered ground and spends
only on what no per-aspect pass could see. Vague recommendations push the next level to re-review
everything, which is the cost this section exists to avoid.

## 4. Tickets versus fixes

- New issues you encounter: create tickets for them. Whether to handle one inside this aspect's
  changes or leave it outstanding for another agent is your call — make it deliberately, and record
  it on the ticket either way.
- Label discipline — see `ticketed-plan-rollout` step 5 (`ready-for-agent` only).
- Findings outside your scope are never fixed inline (§6 rule above) — they are the clearest case
  for a ticket someone else owns.

## Self-improvement protocol

While a run under this skill is live, append dated entries to
`~/.claude/aspect-coordination-notepad.md`: what fired, what misfired, what the skill lacked. When
everything you coordinated is merged and reviewed, present candidate augmentations to the user;
ratified ones land as edits to this skill, and the entries get marked extracted.
