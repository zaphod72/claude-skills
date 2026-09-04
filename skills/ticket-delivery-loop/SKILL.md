---
name: ticket-delivery-loop
description: "Deliver one ticket end to end as the orchestrator of coding subagents: brief them to build test-first, verify what they return, review the resulting PR, and route fixes back down until it converges. Use when a single ticket or bug becomes subagent work, when choosing how many coding agents and which model each gets, when placing the review and fix passes for one PR, or when a PR has drawn two rounds of findings and needs a third. Not a plan doc with an epic to partition (ticketed-plan-rollout), wave computation (implement-plan), owning an aspect branch beneath an orchestrator (aspect-coordination), or git/worktree mechanics (git-worktree-topology)."
---

# Delivering one ticket

One ticket, one PR or a short stack, no plan doc and no aspect branches. You are the only
orchestrator, so reviews spawn from here — `parallel-agent-orchestration` §1's prohibition binds
coordinators that have an orchestrator above them, and you have none.

The loop: **orient → dispatch → verify → review → fix → repeat**.

## 1. Orient before briefing, and keep it inline

Read the ticket in full including its comments, then read the code it names. A brief written from
the summary alone makes the agent re-derive what you could have handed it.

Orientation is not implementation — reading a file to scope the work stays here. Delegate once you
can name the files, the failure, and what done looks like.

## 2. Write the design onto the ticket before dispatching

Post the approach, the file ownership, and the test seams as a ticket comment. Two things follow:
the user corrects the design while it is still cheap, and the seams are named before an unattended
agent has to guess at them (`parallel-agent-orchestration` §5).

State on the ticket which of its asks you are **not** addressing, and why. An operational ask left
silent reads as delivered.

## 3. Dispatch coding agents

- **`/tdd` is the default.** Name the seam and the tests in the brief so the agent writes them red
  first. Where the change has no reachable seam, say so in the brief rather than leaving the agent
  to decide.
- **One agent per file set.** Two agents in one file collide even in separate worktrees. Where the
  work is one coupled change, one agent is right — parallelism is not the goal.
- **Model per agent.** Sonnet for well-specified work. Opus where accuracy rests on judgment the
  brief cannot fully carry: shared test infrastructure, an inverted guarantee, subtle transaction
  or concurrency semantics. Never trade accuracy for tier.
- **Every brief carries `parallel-agent-orchestration` §4's demands**: evidence not conclusions,
  commit before reporting, refuse a wrong instruction, set your own base explicitly.

## 4. Verify what comes back, here

A confident report is a claim. Check the returned evidence against the context only you hold, and
re-run whichever check would be most expensive to have wrong. A passing test the agent wrote is
evidence about the code, not about the premise it was built on.

## 5. Review

Run `/mattpocock-skills:code-review` in a subagent, based at the merge-base. Feed it the ticket
**and** your step-2 comment — without the latter its Spec axis grades against the ticket's original
asks and misses the design agreed after it.

Review once, over everything the ticket produced. A stacked PR reviewed before its sibling lands
spends a pass on half the change, and divergence between the two halves is what the Spec axis
exists to catch.

## 6. Fix, then re-review

- Run `/root-cause-fix` before any fix is written, so findings group by cause instead of getting
  patched one at a time.
- Dispatch the fixes. The reviewer never fixes its own findings.
- Findings outside the ticket's scope get tickets, not inline fixes
  (`claims-and-scope-discipline` §6).

**Two review-and-fix cycles is the working limit.** Needing a third means the change is not
converging: run `/pr-fix-review <pr>` for that pass in place of another normal review. It diagnoses
whether the rounds share one missing concept and whether the ticket was ever detailed enough for
the change, and it gates implementation when the answer is yes.

## 7. Close out

- Review findings are a PR comment. Corrections to the ticket's own text go on the ticket.
- A code ticket goes Done after deploy and verification. Anything with an open PR sits In Progress.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/ticket-delivery-loop-notepad.md`:
what fired, what misfired, what the skill lacked. When everything the work touched is merged and
reviewed, present candidate augmentations to the user; ratified ones land as edits to this skill and
the entries get marked extracted.
