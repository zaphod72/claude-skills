---
name: plan-rollout
description: "Delivers a plan or ticket as merged PRs: two coordinator levels and their coding sub-agents falsify it against the repo, partition it into PR units, and run each as a build-review-fix-merge loop that continues until a human is genuinely needed. Use when a ticket or plan needs implementing through coding sub-agents; when partitioning work into PRs or dependency waves, dispatching an agent that edits or commits, choosing agent count/model, or placing a PR's review and fix passes; when a PR draws repeated finding rounds, or a finding needs a ticket versus a direct fix; when a sub-agent's deviation, a shared file, or merge/deploy ordering across PRs could bite; or when the change itself is tests or test infrastructure. Not authoring or reviewing the plan itself (plan-and-review), where a plan doc lives and how it stays true (plan-docs), verifying a single written claim outside a run (claims-and-scope-discipline), git and worktree mechanics (git-worktree-topology), or finding prose (review)."
---

# Plan rollout

Four actors deliver a plan as merged PRs: a **top-level coordinator** that owns the plan and the
base branch, one **second-level coordinator** per aspect that owns its PR loop, **coding sub-agents**
that write the code, and an **auditor** that re-runs the evidence behind each report. An **aspect**
is one independently deliverable slice of the plan.

**Continuation is the invariant.** A finished PR is a loop iteration, not a checkpoint.
`needs_human()` below is the complete set of reasons to stop; reporting progress is not one.

## Known constraint

Every actor's reference file, `references/auditor.md`, `scripts/rollout-db`, and all four
`agents/plan-rollout-*.md` definitions are loaded live through `~/.claude/skills` and
`~/.claude/agents`, symlinks into this repo's working tree. This skill only functions when the
working tree checked out at those symlink targets holds this content — merged to trunk, or this
branch checked out directly. Switching branches in that checkout while a plan-rollout run is live
breaks every running instance: ledger writes and dispatch fail outright, and a mismatched
`brief-contract.md` can silently reappear and reject an agent's report with a "missing required
heading(s)" error that looks like the agent's mistake rather than a checkout problem.

## Read your own file, and only it

| You are | Dispatched as | Read | It holds |
|---|---|---|---|
| Top-level coordinator | the session itself | `references/top-level-coordinator.md` | The plan loop, waves, the run directory and ledger, close-out |
| Second-level coordinator | `plan-rollout-slc` | `references/second-level-coordinator.md` | The PR loop, review rounds, the tracker |
| Coding sub-agent | `plan-rollout-coder` | `references/coding-agent.md` | Worktree setup, `mattpocock-skills:tdd`, the final gate (the last format-then-test pass before commit) |
| Auditor | `plan-rollout-auditor` | `references/auditor.md` | One report's evidence, re-run against the repo; the blast-radius answer |
| Reviewing tests or test infrastructure | `plan-rollout-reviewer` | `references/review-efficacy-axis.md` | Mutation testing: does the suite still catch what it claims? |
| Dispatching anything | — | `references/brief-contract.md` | Every required brief field and its paired report field |

Loading another actor's loop wastes the context that keeps this run accurate. Each agent definition
preloads the one file its actor reads, so a brief names that file and no other.

## Where a run keeps its state

Two homes, both derived from the ticket, so any actor — including a restarted one — resolves them
without being told.

- `~/.claude/plan-rollout-runs/<ticket>/` holds this run's prose: briefs, reports, audits, review
  recommendations, per-PR review files, the changes inventory.
- `~/.claude/plan-rollout-runs/rollout.db` is the ledger, shared by every run. Fixed-field,
  multi-writer data lives there — the partition, agents, report headers, notes, traps, tickets,
  decisions, audits — because `Edit` and `Write` rewrite whole files and concurrent appends clobber
  each other silently. `~/.claude/skills/plan-rollout/scripts/rollout-db` is the only way in.

**Every report is two tiers.** The dispatched agent writes its full report to
`<run dir>/reports/<agent>.md` under fixed `##` headings, then runs `rollout-db report <name>`,
which parses the file, writes the `headers` row, and prints a **routing header** — status, branch,
SHAs, the counts, `empty_sections` — at most 30 lines. The header is the only thing that returns
inline, and the parent opens the report file only when a count sends it there. `report` resolves the
run from that agent's ledger row, so a dispatcher runs `agent upsert` before its child can report.
`references/brief-contract.md` owns the headings, the fields, and the pairing rule between them.

**A run resumes from the ledger.** `rollout-db state <ticket>` returns the units, the agents, and
every decision still open, so a coordinator that was compacted or restarted continues its run instead
of starting a second one. A question is `decision add`ed when it is asked and `decision resolve`d
when the human answers, so what comes back open is exactly what still needs one. A trap can
likewise be retracted with `trap resolve`, linking a correction row to the false one, so
`traps --repo` and `dump` show the correction inline instead of leaving the false trap standing
uncorrected.

## Goals, in priority order

Settle every judgment call against this list, top down.

1. **Accurate code and simple reviews** — small PRs, and `mattpocock-skills:tdd`.
2. **A clear testable seam per PR.** This partitions the work, not just decorates it.
3. **Small context windows,** by splitting work across sub-agents.
4. **`mattpocock-skills:tdd` plus at most three reviews.** Both earn their place; keep both.
5. **Complete the plan.** Related issues get fixed, not parked in tickets.
6. **Review each thing once.** The run artifacts — the review recommendations and the per-PR
   review file — exist to spend review effort once.

## Predicates and primitives

A control-flow spec, not an API: `dispatch()` and the rest name intent. Every loop calls these.

```
is_never_trivial(finding):                                # Checked FIRST
    return finding.area in {state_transitions, locking, CAS, claim_fencing}
        OR finding.changes in {public_signature, schema, migration}
        OR finding.touches_shared_test_infra                # conftest, shared fixtures
        OR (finding.is_missing_test AND finding.reveals_behavior_gap)

is_cosmetic(finding):
    if is_never_trivial(finding):                         return FALSE
    return finding.changes_only_one_of(
        formatting, comments, docstrings, markdown_docs,
        local_naming, log_message_wording, error_message_wording, unused_imports)

is_trivial(finding):
    if is_never_trivial(finding):                         return FALSE
    if is_cosmetic(finding):                              return TRUE
    return finding.fix_is_obvious
       AND finding.confined_to_one_function
       AND NOT finding.changes_behavior_outside_that_function

needs_human(state):
    # The ONLY reasons to stop. Goal 5: finishing a PR is not one of them.
    return state.third_review_still_has_non_cosmetic_findings   # the escalation PR: opened
                                                                  # unconverged, for the human to
                                                                  # read
        OR state.blocking_ticket_labeled("ready-for-human")
        OR state.out_of_scope_escalation_unresolvable_in_scope
        OR state.merge_conflict_between_aspect_base_branches
        OR state.fix_review_verdict == BLOCKED                  # fires from round 2
        OR state.next_wave_node_is_branch_runnable_operational   # branch-runnable: runs against
                                                                  # the base branch mid-run; only
                                                                  # a human can perform it

AWAIT_DECISION(reason, options):
    # The one stop primitive. What it does depends on who calls it.
    if self is TOP_LEVEL_COORDINATOR:
        present_to_user(reason, options); return user_answer()
    else:
        # A sub-agent has no user. End this turn with a blocked report; the parent
        # decides and resumes THIS agent with the answer (SendMessage). Verified
        # 2026-09-07: a nested parent CAN resume an already-finished child, and the
        # child keeps its context — so resume, rather than re-dispatching, is the
        # path. SendMessage may be deferred in a sub-agent; load it via ToolSearch.
        # Fallback if a resume ever fails: re-dispatch fresh with the decision in
        # the brief — same control flow, but the child's worktree state and
        # everything it already read are lost, so it re-derives them.
        write_report_file(my_report_path)      # `## status: blocked`, and `## blocked_on`
                                                # naming the decision and the options you see
        report_upward(`rollout-db report <self> --file <my_report_path>`)
        return resumed_with_decision()

report_upward(header):
    # The one way a dispatched agent ends its turn, blocked or done. Write the full
    # report to <run dir>/reports/<name>.md with every fixed `##` heading present, run
    # `rollout-db report <name> --file <path>`, and return ONLY the routing header it
    # printed — never the report text, never a summary alongside it.
    # brief-contract.md owns the headings and the header's fields.
    return header

cut_branch(from, name):
    git checkout -b name from; git push -u origin name    # pushed at once
```

Call these by name. Their bodies live here and nowhere else.

## Finding severity

Three nested tiers: **cosmetic ⊂ trivial ⊂ significant.** `is_never_trivial()` is checked before
either test, so a public rename cannot pass as cosmetic.

| Tier | Definition | Drives |
|---|---|---|
| Cosmetic | No behavior change at all | Whether a review round escalates |
| Trivial | Fix is obvious, confined to one function, cannot change behavior outside it | Direct fix vs. `/root-cause-fix` |
| Significant | Everything else | Always a ticket, and a fix now if related |

**Trivial but not cosmetic:** a small fix inside one function that does change behavior; adding a
case to an existing test for behavior that is already correct.

A *missing* test that reveals a behavior gap is a real finding wearing a test's clothes. Shared test
infrastructure is never trivial in either direction — a test turning **green** there is the more
dangerous one, and neither direction shows in the diff
(`claims-and-scope-discipline` §11 for the baseline procedure).

## Rules

Unconditional, and live only during a run.

### Format before the final test run

Run tests as often as you like while developing. This governs the last run only.

Before what might be the final commit, run every file-modifying step first — formatters, import
ordering, lint `--fix`, type fixes — **then** the final test run. Formatting after a test run forces
that test run to be repeated.

**Select tests by grepping the changed symbols across the whole test tree**, not by filename —
`references/brief-contract.md`, "Select tests by symbol, not by filename", owns why and the count
that pairs with it. Run the full suite only when it is genuinely necessary; inside a stack that
selection is the whole gate, since a repo's `pull_request: branches:` list may not name an aspect
base. (A repo's own memory carries the commands; this states the rule.)

### Always use worktrees, and name the base explicitly

Every PR gets one worktree, created by its first coding agent, living until the PR merges. Slice
agents get their own.

- **Every worktree dispatch `fetch`es and `checkout -B`s its base as step 0**, before any read.
  `isolation: "worktree"` has been observed cutting from the repo's *default* branch rather than the
  session's (`git-worktree-topology` §2a). Step 0 makes the harness behaviour irrelevant.
- The branch a worktree checks out is already on `origin`: whoever cuts a branch pushes it.
- The Agent tool auto-cleans a worktree only when it is *unchanged*, which is what makes the
  cleanup rule below load-bearing.
- `git-worktree-topology` owns the rest: §1 flat ref prefixes, §2b commit by path rather than
  stash, §2c another agent's worktree is read-only, §3 stacked-PR merges.

### One branch, one worktree

Git refuses to check out one branch in two worktrees. So two coding agents on one PR each get their
own **slice branch** cut off the PR branch, and the coordinator merges them in.

### Clean up after merge

Delete the worktree and the branch once the PR merges — the review and fix rounds need them until
then.

## Branches and merges

Every branch reaches `origin` the moment it is cut, by whoever cuts it, so the next worktree can
fetch it.

| Branch | Cut from | Owner |
|---|---|---|
| Base branch | The real trunk | Top-level coordinator. Always exists; create it if not given one |
| Aspect base branch | Base branch | One second-level coordinator |
| PR branch | Its aspect base branch | The second-level coordinator cuts it; the coding sub-agent works it |
| Slice branch | Its PR branch | A second coding agent on the same PR |

| Merge | Performed by |
|---|---|
| Slice → PR branch | A sub-agent dispatched by its second-level coordinator |
| PR → aspect base branch | A sub-agent dispatched by its second-level coordinator, once the review cycle converges |
| Aspect base → base branch | A sub-agent dispatched by the top-level coordinator |
| Base branch → trunk | **The human.** The top-level coordinator opens this PR and leaves it |

A coordinator never performs a git mutation — merge, push, branch create or delete, worktree add or
remove (building a worktree to run the gates in, and tearing it down, are both) — with its own
hands; every one above is a dispatch. One actor's dispatch performs each
level's merges in sequence, so no ordering queue is needed. A merge conflict between two aspect base
branches is a `needs_human()` stop.
