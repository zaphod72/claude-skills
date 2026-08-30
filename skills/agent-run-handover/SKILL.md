---
name: agent-run-handover
description: "Hand a long-running orchestration session off to a successor session: drain all in-flight subtasks, write a handoff doc mapping every on-disk artifact, and give the user its path. Use when the user asks to hand off or wrap up the session so a fresh one can continue, when context is close to full mid-run, or when starting a new session from a handoff doc. Not run-state bookkeeping during a live run or stall diagnosis of a single subtask (parallel-agent-orchestration)."
---

# Agent run handover

One session ends an orchestration run; a fresh session continues it. The bridge is a handoff doc the predecessor writes and the successor verifies. Context pressure is the usual reason: the user starts a new session because this one's window is nearly spent.

## 1. Drain

Stop dispatching new work and wait for every in-flight subtask to complete. The handoff doc describes a stationary run; anything still moving makes it wrong on arrival. If a subtask will not finish, tell the user and record it in the doc — agent name, what it owns, last known state, how to check on or stop it — rather than waiting indefinitely.

## 2. Write the handoff doc

Create `~/.claude/handoffs/<yyyy-mm-dd>-<topic>.md` with:

- **State of the run**: each task done, stalled, or not started, with the evidence (branch, PR, commit, file) beside each claim.
- **Waiting on / recommended actions**: what the run is blocked on, and what the user should do about each item.
- **Artifact map**: every on-disk note the session keeps — run-state files, notepads, plan docs, worktrees and branches, scratchpad files. Scratchpads live under `/private/tmp` and die with the machine or session: copy anything the successor needs into `~/.claude/handoffs/` and point at the copy.
- **Verification list**: the claims the successor must re-check before acting on them.

## 3. Inform the user

Give the doc's path and a one-line state summary, then stop. Work done after this point dates the doc; if more work happens anyway, update the doc before the session ends.

## Resuming as the successor

1. Read the handoff doc in full.
2. Run `ListAgents` before dispatching anything. A handover does not revoke the predecessor, and two live orchestrators on one repo is an observed failure. If the predecessor is still listed, ask the user to close it first.
3. Treat the doc as claims, not facts: verify the branch, PR, and file state it describes before continuing the run.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/agent-run-handover-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
