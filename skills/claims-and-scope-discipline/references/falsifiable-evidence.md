# Evidence that cannot come back negative

The full case for `SKILL.md` §14: the six instances where a command was offered as evidence and
could not have produced the disproving result, the two commands that answer them, and the
measured-versus-implied gap that lets a live defect get closed.

Every conclusion below was right. That is the point: the claim survives, the evidence looks like
evidence, and nothing surfaces until the same method meets a claim that is wrong.

## The six instances

| Offered as evidence | Why it cannot falsify | What answers it |
|---|---|---|
| a grep of `git branch -r` for the run's ticket key, proving a PR's branch absent | the run's units are named `pr1-fail-closed-pause-guards` and `pr2-loop-error-boundaries`; a coordinator names base branches after the run and PR branches after the work, so no PR branch carries the key | the unit names in the ledger |
| grepping the ticket's identifier `lease_expires_at` to prove a finding stale | the mechanism is live under a renamed field, `lock.lease_expiry` | a grep for the mechanism |
| reading a merged file from the local branch ref | every merge and push in a parallel run lands in another agent's worktree, so a local ref tracks only what your own checkout did (`git-worktree-topology`) | `git fetch`, then read `origin/<branch>` |
| a PR showing nothing red | zero checks renders identically to all-green: no badge, no missing-check warning, and `mergeStateStatus` still reads `CLEAN` | the check *count*; zero means untested, not passing |
| `mergeable` or `mergeStateStatus` on a merged PR | GitHub stops computing merge state at merge, so `CONFLICTING` and `UNKNOWN` both appear on cleanly-merged PRs | nothing: post-merge those fields carry no information |
| `find . -name <file>` | agent worktrees under `.claude/worktrees/` hold a copy of every file; one such lookup returned 34 | `git grep` and `git ls-files`, which are scoped to the checkout |

The two that need a command rather than a habit:

```
rollout-db query "SELECT unit FROM units WHERE run='<ticket>'"
gh pr view <n> --json statusCheckRollup --jq '.statusCheckRollup | length'
```

## Measured versus implied

The renamed-field row above is the measured-versus-implied gap in one direction.

It runs the other way too. `EHR_WALL_SECONDS = 60.5` **does** exist on the working lineage, which
yielded the generalisation "the whole file set is absent", while the ticket claimed a
*duplication*: two declarations, and exactly one exists. Right verdict, wrong reasoning, and it is
the reasoning that gets reused on the next ticket in the batch.
