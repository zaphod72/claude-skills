---
name: plan-docs
description: "Conventions for a plan doc that is actively being implemented: home it in the repo's plan/ dir, correct it in place as the work falsifies it, keep its runtime-only checks section until validation consumes it, and put findings on Jira tickets. Use when starting or continuing an implementation run driven by a plan doc, when a skill like /plan-rollout or /root-cause-fix hands one over, or when a review plan lands in plan/ alongside an implementation plan and the two need telling apart. Not for docs merely being read, cited, or asked about; those stay where they are."
---

# Plan docs

A plan is a set of assertions made at writing time. Some decay, some were never true, and work reveals both. A plan doc that is never corrected becomes a trap: the next person reads it as current and rebuilds an error someone already paid to find.

This skill covers three things: where the plan lives, how it stays true, and where findings go. It does not cover creating the branch the plan lives on; when a plan has a top-level ticket and needs a root branch cut for it, that's `plan-rollout`. Nor does it cover writing the plan in the first place; that's `plan-and-review`.

## 0. Two species of doc live in `plan/`

Everything below describes an **implementation plan**: a statement of work intended, corrected as the work falsifies it.

A **review plan** is the other species. `dual-scoped-review-plans` authors two at a run's close-out: agent-executable instruction sets for a review pass, written for a Claude agent rather than a person. They take §1's homing rules and §4's separate-commit rule, and four conventions below deliberately do **not** carry:

| Convention | Why a review plan is exempt |
|---|---|
| §2, correct it in place | The work does not falsify it. It is an instruction set consumed once per pass, and editing it mid-pass changes what the pass was |
| §3, "the plan doc alone" | The two review plans sit beside the implementation plan on purpose |
| §4, one writer, the coordinator | Two independently-scoped authors write them, and the coordinator **must not read either**; that isolation is the whole point of two passes |
| §5, consumed by close-out | It is the input to a pass that runs *after* the plan is done, so it outlives the doc it sits beside |

Tell them apart by what the file instructs: work to perform, or a review to conduct. When a run produces both, `plan-rollout`'s close-out states which paths are which.

## 1. Home the plan in the repo

**Relocate only when work is starting from this plan**: the user handed it over to be implemented, or an invoking skill did. A doc you are reading, citing, or answering a question about **stays exactly where it is**. Moving a doc is not a tidy-up you perform on the way to answering something.

Two hard stops:

- **A tracked doc that other files link stays put unless the user agrees to the move.** Check first: `grep -rn '<basename>' --include='*.md' .`. A repo's standing punch list or architecture doc is cited from other docs and from commit messages; relocating it silently breaks those.
- **When in doubt, ask.** The cost of asking is one sentence; the cost of a wrong `git mv` is every inbound link.

Once relocation is warranted: **plan docs live in `plan/` off the repo root.** Resolve the root with `git rev-parse --show-toplevel`; never trust cwd, which lies inside a worktree. Create `plan/` if it does not exist.

Home the doc **before** reading it for facts. Corrections and status get written back into it, and a plan corrected at one path then relocated leaves those edits behind.

| Where the doc is now | What to do |
|---|---|
| Already in `plan/` | Leave it |
| Tracked by git, elsewhere in the repo | `git mv` |
| Untracked, inside the repo | `mv` |
| Outside the repo (scratchpad, Downloads, an attachment) | **Copy**, don't move; the user may have the original open |

Echo the new path back and use it from then on. If other docs link the old path, fix them (`grep -rn '<old-basename>'`).

## 2. Keep the plan true as you work

**Correct the plan doc itself, in place.** Not a note in your reply, not only a line in a sub-agent's brief: the doc. A correction that lives anywhere else fixes today's run and loses the finding.

- **A falsified claim gets rewritten**, with the measurement that replaced it. State what is true now.
- **An accepted deviation rewrites the section** as the new statement of what that work does. Do not append "originally we intended X": a plan section is a description of the current intent, and a reader cannot tell an appended note from a live instruction.
- **A contradiction you cannot settle alone** goes to the user with the measurement, before more work builds on it. Then record the outcome on the epic ticket.
- **Status stays calibrated.** Plan status vocabulary is local to each plan and unreliable: `DONE` often means "written, unpushed". Say what you read it as, and let the user correct you.

## 3. Where findings go

Findings, open questions, and decisions go on **Jira tickets**: the story's own ticket, or the epic when the finding spans more than one story. The plan directory carries the plan doc alone; no companion findings file lives beside it (a review plan is the one exception; see §0). Write finding comments in the `bug-report` format (`~/.claude/skills/bug-report/SKILL.md`): current diagnosis first, dated evidence, ruled-out hypotheses compressed.

State this placement in briefs as a standing instruction. Agents holding older conventions create companion files beside the plan out of habit unless told where findings belong.

### Cases only a live run can settle

Some findings cannot be confirmed from code at all: they depend on live data, timing, concurrency, or an external service. Those become rows in the plan doc's own `## Runtime-only checks` section, one per case:

| Ticket | Item | Why it can't be checked statically | Where (PR / file:line) | Log line(s) to watch | Expected value | What a deviation means | Status |
|---|---|---|---|---|---|---|---|

**Record the expected value and the defect a deviation implies, not just the log line to watch.** "Watch the disambiguation event count" is unusable months later; "expect tens, not thousands; thousands means the cache is written under one key and read under another" is a diagnosis someone can act on without re-deriving the design. Where a number was measured, that number is the expectation. Where a deviation has exactly one plausible cause, name it.

**This table never substitutes for logging.** If the decision point has no structured log line carrying the fields needed to spot the case, add the log line first. A row pointing at a log line that does not exist is worse than no row.

**The rows are the tickets' validation bar.** "Validate in dev/staging" means running the row (exercise the flow, watch the named log lines, compare against the expected value), and a ticket whose rows are red stays In Progress. A plan completes only when every ticket has been built, deployed, and validated, so by completion the table is fully consumed: strike rows as their validations pass.

Fold in the questions the work could not settle: an assumption belonging to another repo, a rule whose correctness depends on production traffic, a mapping left deliberately narrow. Those rows do not block validation; see §5 for what happens to them at close-out.

## 4. Ownership and commits

**One writer** (for an implementation plan; a review plan has its own author and no coordinator reader; see §0). Whoever coordinates the work owns the plan doc and edits it in the **main** working tree, never inside a worktree. A file written in a worktree lands on that branch, so a continuously updated doc fragments across branches and conflicts at merge. Sub-agents *report* plan errors and findings; the coordinator writes the former into the doc and files the latter on tickets. Name the plan doc in any sub-agent's "what not to touch".

**If you are in a worktree and there is no coordinator above you**, say so rather than writing the file to the wrong branch. Give the user the entry you would have written and let them choose: land it on the main tree, or accept it on this branch.

**Commit the plan separately.** A `docs(plan):` commit on the base branch at each natural boundary keeps the plan's evolution out of every feature diff and survives a lost session.

## 5. Close out

Before declaring the work done, state the plan path back to the user and account for the runtime table: every row either struck (validated) or migrated to a Jira ticket. Rows that could never be checked at completion time (production traffic that has not accumulated yet, another repo's behavior, a live-data shape that does not exist yet) migrate **before** the plan doc is removed, so nothing dies with the document. That residue is the part of the run that is not finished just because the tests were green.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/plan-docs-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
