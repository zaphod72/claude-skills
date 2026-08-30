---
name: parallel-agent-orchestration
description: "Control flow and briefing for a run of many parallel subagents against one repo — how a dispatched agent actually advances, and what every brief must demand of the agent receiving it. Use when fanning out parallel coordinators or story agents, when an agent reports being 'still waiting' on its own child two turns running, when two agents need the same file, when ordering the merges of sibling PRs from different agents, when placing review passes in the run, when deciding whether to act on a subagent's report, when naming or ruling on a concurrency seam before dispatch, or when checking the ticket list against the plan's findings before computing waves. Not for a single subagent doing one task; not the git/worktree mechanics underneath (git-worktree-topology), the partitioning of a plan into PRs (ticketed-plan-rollout), or wave computation (implement-plan)."
---

# Orchestrating parallel agents

Everything here came from real multi-agent runs against one repo. Each rule cost real work to
learn; none is speculative.

## 1. The orchestrator is the pump

An `Agent` call made from inside a subagent runs in the background and the dispatching agent's
**turn ends**. The await does not survive the turn boundary — nothing wakes a coordinator when its
child finishes. Only the orchestrator can advance it.

`references/stall-detection.md` — read when a coordinator reports "still waiting" more than once.

### Reviews execute here

Coordinators must never spawn review sub-agents themselves — a coordinator that spawns one stalls
on it the same way any dispatch stalls it, so reviews run in the top-level session via
`/code-review` and route fixes back down. Two review-and-fix cycles on one PR is the working limit;
a third means the change is not converging.

`references/review-placement.md` — read when placing a review pass in the run.

## 2. Shared files: sequence, don't reassign

When a ticket needs a file another aspect owns, sequence the later agent behind the earlier one
instead of reassigning the ticket. A conflict in a document another writer owns is reported, never
resolved.

`references/shared-files.md` — read when two agents need the same file.

## 3. Merge readiness: green status lies

GitHub's `mergeable` evaluates each PR against its base independently, so two sibling PRs can both
report green and still conflict with each other on merge. The check that holds is an actual merge
in a throwaway worktree, run before choosing a merge order.

`references/merge-readiness.md` — read when ordering the merge of sibling PRs.

## 4. What every brief must demand

- **Evidence, not conclusions.** The commands run and their raw output, plus an explicit split of
  what was verified and what was inferred. A confident report with no command behind it is a claim,
  not a result. This is the safeguard that does not depend on predicting what matters: "keep it
  inline when the context is critical" only fires when you already know a fact is critical, and the
  facts that burn you are the ones you did not know to flag. This has caught a wrong pool-size
  figure the orchestrator itself had relayed.
- **Commit and push before reporting, and commit incrementally.** State the reason honestly,
  because agents discount rationales they can falsify: worktrees survive kills every time, so the
  cost of uncommitted work is not loss; it is unreadability. Neither the resuming agent nor the
  orchestrator deciding resume-versus-restart can tell what state ten dirty files were in; ten
  commits with messages are resume points.
- **Refuse a wrong instruction rather than implement it.** Say it explicitly: *report anything in
  this brief, the plan, or a finding that turns out to be wrong; do not silently implement a wrong
  instruction.* **Take the correction and name it as valuable**; defending the instruction teaches
  the next agent to comply silently.
- **Check the tickets' own sequencing notes, and refuse your order when they conflict.**
  Ticket-authored constraints were written with all the tickets in view; your ordering is a guess
  made from summaries. The refusal is the point.
- **Ask: does this change require anything to happen in a particular order at deploy time?** By
  review time the reasoning that produces a gate has been discarded, so this is a brief question,
  not a review question. What the gates look like: `claims-and-scope-discipline` §12.
- **Background long-running suites rather than blocking on them.** Anything longer than the
  watchdog dies mid-run, and it collects the agents whose job *is* running tests.
- **Demand output land somewhere readable when you will need the result.** Tee long commands to a
  file rather than letting them write only to the dispatched agent's own shell.
- **Express a base as ancestry, never equality.** Never pin an exact base SHA in a brief while
  another agent is pushing to that branch. The gate is `git merge-base --is-ancestor <sha> HEAD`.
  Better still, have the agent set its base explicitly rather than assert anything about it — see
  `git-worktree-topology` §2a.

`references/brief-demands-evidence.md` — read if a §4 bullet's rationale is unclear.

## 5. Seams are chosen at planning time, and ruled cheaply

Confirming a test's seam interactively assumes a human is present; an unattended implementer has
nobody to ask. Name seams in the plan or ticket before dispatch, and treat a concurrency test that
needs `gather`, sleeps, or retries to pass as proof the seam is wrong, not proof the test works.

`references/seam-judgment.md` — read when naming or ruling on a concurrency seam.

## 6. Reading what comes back

A finding routes to the level that owns it, not wherever it lands. Consolidation, unanimity, and
completion claims are the coordinator's to verify, never to relay unchecked.

`references/reading-reports.md` — read when deciding whether to act on a subagent's report.

## 7. The ticket list is not the work list

**Diff the source document against the tickets that exist.** Do it before computing waves, not
after.

## 8. Write the resume state table as you go

Per chain: stories done, PRs open, PRs merged, branch SHA, what is pending. Minutes to write while
the run is live; much more expensive and error-prone to reconstruct afterward, which is what a
successor session has to do without it — see the `agent-run-handover` skill.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/parallel-agent-orchestration-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
