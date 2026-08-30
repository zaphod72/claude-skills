---
name: ticketed-plan-rollout
description: "Turn a plan doc that has a top-level ticket (usually Jira) into a rolled-out multi-PR implementation: cut a root branch named after the ticket, commit the plan doc there, partition the work into small (optionally stacked) PRs — separating code PRs from operational runbooks — then dispatch one Haiku-or-Sonnet subagent per PR in its own worktree. Use when a plan doc has a tracker epic at the top and needs to become a stack of PRs, or when deciding how to partition a multi-PR implementation and dispatch it. Hands off dispatch mechanics to /implement-plan once the partition is big enough to need wave computation and deviation escalation; usable standalone for smaller stacks."
---

# Ticketed plan rollout

A plan doc with a top-level ticket is not yet an implementation — it needs a root branch, a PR partition, and subagents dispatched against that partition. This skill covers the phase before `/implement-plan`'s wave engine takes over: turning the ticket and plan into branches, PRs, and dispatched work. It stands on its own for a small stack; hand off to `/implement-plan` once the partition is big enough to need dependency waves, deviation escalation, and the full sub-agent return contract.

## Steps

### 1. Create the root branch and commit the plan doc

- Resolve the repo's real integration branch first — never assume `main` or whatever branch you're currently on. Check what recently merged PRs actually target: `gh pr list --state merged --limit 20 --json baseRefName` (or equivalent), and confirm with the user if it's ambiguous.
- Name the root branch after the top-level ticket: `<TICKET-KEY>/<slug>`, e.g. `BOOK-431/split-fhir-works-from-cloud-infra`.
- Branch off the confirmed integration branch using the `EnterWorktree` tool — not `git worktree add` plus manual `cd` — so later commands run there without repeated permission prompts on compound `cd` commands.
- Home the plan doc per the `plan-docs` skill: it moves to `plan/<plan_name>.md`. Commit the plan doc on the root branch — every stacked PR branches from here and inherits it. Findings and open questions go on Jira tickets (the story's ticket, or the epic when they span stories); the plan directory carries the plan doc alone.

### 2. Partition the work into PRs

- Prefer small PRs over large ones.
- Stack a PR on another only when it genuinely depends on it — it shares files with the parent, or needs the parent's code to work. Otherwise branch it straight off the root branch, so it can be reviewed and merged independently of its siblings.
- Separate **code PRs** from **operational steps** that need live credentials or production access — deploys, manual cutover, IAM grants, a one-off migration run by hand. Operational steps are not PRs: write them as a runbook plus an explicit review/approval gate, and sequence them relative to the code PRs in the partition rather than folding them into one.
- Write the partition into the plan doc itself (a stack diagram or explicit per-PR list), in the same shape `/implement-plan` expects to read — that's what lets this rollout hand off cleanly if the stack later needs the wave engine.

### 3. Dispatch a subagent per PR, in its own worktree

- One git worktree per PR, always — unconditional here, unlike `/implement-plan`'s wave runner, which collapses a serial chain reworking one module into the main tree to avoid N stale copies of one heavily-edited file. If you hit that situation in a standalone rollout, either accept the same exception explicitly and say so, or hand the run to `/implement-plan`, which already encodes it.
- Use the same `EnterWorktree` tool, one worktree per PR.
- Assign explicit file ownership per subagent whenever PRs run concurrently, so parallel agents never edit the same file.
- Choose the model per subtask using the Haiku/Sonnet criteria in `~/.claude/skills/implement-plan/SKILL.md` step 6. Reserve your own (coordinator) model for synthesis, architecture review, and any subtask whose accuracy depends on context only you hold — never delegate that.
- Brief each subagent with:
  - The verified facts you already established (integration branch, root branch, ticket, this PR's slice of the plan) — don't make it re-derive them.
  - The evidence and commit-before-reporting demands from `parallel-agent-orchestration` §4.
  - That findings and open questions go on Jira tickets, per `plan-docs` §3.
- Definition of done includes the integration-digest entry written by the coordinator itself (`claims-and-scope-discipline` §9) — an aspect whose entry does not exist is not finished.

### 4. Synthesize, never delegate

- Check every subagent's returned evidence against the full context you hold — a confident report is a claim, not a result.
- Update the plan doc yourself — corrections, accepted deviations, status — and update the tracker tickets yourself once the PRs and their scope are known. Subagents report findings; they don't write these — an edit made from a worktree strands on that PR's branch (see `plan-docs` §4).

### 5. Reconcile tickets with the actual partition

- Subtask ticket descriptions written before implementation go stale: scope moves between tickets as PRs get cut, and some subtasks turn out already-done by the time their PR starts.
- Before implementing each subtask, check its ticket's premises against the current code, not just against the plan.
- Close or rescope tickets that reality has overtaken, rather than implementing a stale description as written.
- Only pick up tickets labeled `ready-for-agent`. A `ready-for-human` ticket is the human's own queue — an agent tackling one bypasses the triage decision it encodes.

## When to hand off to /implement-plan

Once the plan doc carries a real partition (stack diagram, per-PR dependencies) and the stack is big enough to need dependency waves, cross-PR deviation escalation, or the full sub-agent return contract, run `/implement-plan @plan/<plan_name>.md --base <root-branch>` instead of dispatching by hand. This skill produces exactly the inputs that command consumes: a homed plan doc with a partition already written into it, and a root branch to serve as `--base`.

## Related skills

- `plan-docs` — owns where the plan doc lives and how it stays true, and where findings go (Jira tickets); follow it for step 1's doc placement and step 4's write-it-yourself discipline.
- `implement-plan` — owns wave computation, deviation escalation, and the sub-agent return contract for executing an already-partitioned plan; hand off to it once the partition exists (see above). It is user-invoked only (`disable-model-invocation: true`), so this skill is the one a session lands on automatically when a ticketed plan first needs rolling out.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/ticketed-plan-rollout-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
