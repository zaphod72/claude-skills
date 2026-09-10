---
name: plan-rollout
description: "Delivers a plan or ticket as merged PRs: two coordinator levels and their coding sub-agents falsify it against the repo, partition it into PR units, and run each as a build-review-fix-merge loop that continues until a human is genuinely needed. Use when a ticket or plan needs implementing through coding sub-agents; when partitioning work into PRs or dependency waves, dispatching an agent that edits or commits, choosing agent count/model, or placing a PR's review and fix passes; when a PR draws repeated finding rounds, or a finding needs a ticket versus a direct fix; when a sub-agent's deviation, a shared file, or merge/deploy ordering across PRs could bite; or when the change itself is tests or test infrastructure. Not authoring or reviewing the plan itself (plan-and-review), where a plan doc lives and how it stays true (plan-docs), verifying a single written claim outside a run (claims-and-scope-discipline), git and worktree mechanics (git-worktree-topology), or finding prose (review)."
---

# Plan rollout

Three actors deliver a plan as merged PRs: a **top-level coordinator** that owns the plan and the
base branch, one **second-level coordinator** per aspect that owns its PR loop, and **coding
sub-agents** that write the code. An **aspect** is one independently deliverable slice of the plan.

**Continuation is the invariant.** A finished PR is a loop iteration, not a checkpoint.
`needs_human()` below is the complete set of reasons to stop; reporting progress is not one.

## Read your own file, and only it

| You are | Read | It holds |
|---|---|---|
| Top-level coordinator | `references/top-level-coordinator.md` | The plan loop, waves, run artifacts, close-out |
| Second-level coordinator | `references/second-level-coordinator.md` | The PR loop, review rounds, the tracker |
| Coding sub-agent | `references/coding-agent.md` | Worktree setup, `/tdd`, the final gate (the last format-then-test pass before commit) |
| Dispatching anything | `references/brief-contract.md` | Every required brief field and its paired report field |
| Reviewing tests or test infrastructure | `references/review-efficacy-axis.md` | Mutation testing: does the suite still catch what it claims? |

Loading another actor's loop wastes the context that keeps this run accurate. Each brief names the
one file its recipient reads, and the report field "which reference file was read" catches a miss.

## Goals, in priority order

Settle every judgment call against this list, top down.

1. **Accurate code and simple reviews** — small PRs, and `/tdd`.
2. **A clear testable seam per PR.** This partitions the work, not just decorates it.
3. **Small context windows,** by splitting work across sub-agents.
4. **`/tdd` plus at most three reviews.** Both earn their place; keep both.
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
        report_upward(status = blocked, blocked_on = reason, options = options)
        return resumed_with_decision()

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

**Select tests from the diff.** Run the full suite only when it is genuinely necessary; CI runs it
on the PR. (A repo's own memory carries the commands; this states the rule.)

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
| Slice → PR branch | Its second-level coordinator |
| PR → aspect base branch | Its second-level coordinator, once the review cycle converges |
| Aspect base → base branch | Top-level coordinator |
| Base branch → trunk | **The human.** The top-level coordinator opens this PR and leaves it |

One actor performs each level's merges in sequence, so no ordering queue is needed. A merge conflict
between two aspect base branches is a `needs_human()` stop.
