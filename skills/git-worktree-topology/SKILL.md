---
name: git-worktree-topology
description: "Git ref-naming, worktree-isolation, and stacked-PR merge mechanics for running multiple agents in parallel against one repo. Use when planning or dispatching parallel/concurrent subagents that each get their own branch or worktree, when designing a branch-naming scheme for a multi-PR or stacked-PR run, when an agent hits 'cannot lock ref' / 'already exists' on branch creation, or when deciding how to derive a PR's base branch, whether to squash a stacked PR, or whether to force-push into a chain, when a wave dispatches against a base branch cut earlier, or when reading branch or file state another agent's worktree or a merged PR produced. Not about orchestration control flow (dispatch/resume/pause of the agents themselves) — only the git/worktree mechanics underneath it."
---

# Git worktree topology for parallel agents

Running several agents in parallel against one repo — one branch or worktree each — hits the same
few git mechanics every time: how branches can be named without colliding, what a worktree does
and does not isolate, and how a stack of branches has to be merged to survive. Get these three
settled before dispatching anything; each was learned from a run that had to stop and unwind work
because it wasn't.

## 1. Branch naming: pick one flat prefix, never nest

**A branch cannot be named under an existing branch.** Git refuses any ref that is a strict
path-prefix of another, in any ref store, local or remote. So the instinctive scheme
`<integration>/<aspect>/<story>` is unsatisfiable the moment `<integration>` is itself a branch:

```
$ git branch review-fixes-08-22/dev-environment
fatal: cannot lock ref 'refs/heads/review-fixes-08-22/dev-environment':
       'refs/heads/review-fixes-08-22' exists
```

It fails **twice** — once at the aspect level, once at the story level — so renaming only the top
level moves the failure one step later rather than fixing it. And it can't be fixed by deleting or
renaming the integration/parent branch: that branch is checked out somewhere and is the merge
target for everything in the run.

**Rule: pick one prefix that is never itself a branch, and go flat inside it.**

```
<prefix>/<aspect>                      # aspect branch
<prefix>/<aspect>-<ticketnum>-<slug>   # story branch — a sibling, not a child
```

Nothing is a path-prefix of anything else, and `git branch --list '<prefix>/*'` still groups the
whole run. Confirmed in practice at the scale of a real run: 15 branches under one flat prefix,
every one created without a manual naming correction.

**Do this before dispatching anything.** One `git branch` call in a scratch repo proves the scheme
works; discovering the collision after two coordinators have already started is a stopped dispatch,
twice.

## 2. Worktree isolation: less than you think

A worktree isolates the working tree and `HEAD`. It does **not** isolate all repository state —
some git state is per-repository, shared by every worktree pointed at the same `.git`. Two known
instances; treat the list as a starting point, not exhaustive, and ask which category any new git
feature falls into before assuming it's per-worktree.

### 2a. Isolation mechanisms may cut from the wrong base — verify this in your harness

*This is a property observed once in one harness's `Agent` tool, not a git fact — check it in
whatever you're using before relying on it.*

One harness's `isolation: "worktree"` option was observed cutting a new worktree from the
**default** branch rather than the calling session's branch. In a repo where the default branch
shared only the root commit with the working line, the resulting worktree had none of the
in-progress tree — no plan directory, no docs, no package source — and a subagent told to "read
the plan first" failed on its first command.

**Rule: never let a subagent inherit its base implicitly. Make it explicit as step 0, before any
read**, regardless of what the isolation mechanism claims to do:

```
git -C <WT> fetch origin <parentBranch>
git -C <WT> checkout -B <workBranch> origin/<parentBranch>
git -C <WT> rev-parse HEAD          # must equal origin/<parentBranch>
```

This is strictly better than gating on an expected SHA: a gate only *detects* the problem after the
fact, and it can't silently drift if the harness's behavior changes later.

Confirmed a second time in a different role: a review agent dispatched with `isolation: "worktree"`
got a tree cut from the default branch and would have read nonsense from working-tree paths. What
saved it was luck of style — and that style is the second defense: **commands with explicit refs are
immune**. `git show origin/<branch>:<path>` and `git diff <base>...<branch>` do not care what is
checked out. Fix the base first (above), and prefer explicit refs anyway.

### 2c. A worktree another agent is using is read-only for you

A review agent was handed the coordinator's own worktree path and ran `git checkout` there while
the coordinator was committing and rebasing. It caught the flapping state itself — two consecutive
`git status` calls disagreed, a modified file appeared and vanished — stopped touching git, and
reported. Reflog verified afterwards; nothing lost. That outcome was the agent's discipline, not
the setup's safety.

Reviewing needs none of it: `gh pr diff <n>`, `gh pr view <n> --json files,body`, and
`git show <sha>:<path>` are read-only and need no working tree. If a checkout is genuinely
required, create your **own** worktree and remove it after. **Never run a mutating git command in a
directory you did not create** — one agent's checkout against another agent's index is the same
shared-state class as `refs/stash` (§2b).

### 2b. `refs/stash` is repository-wide

This is the expensive one, and it is plain git behavior, not harness-specific. Every worktree
shares one stash stack even though their working trees and `HEAD`s are isolated. In a real run, two
agents in different worktrees silently swapped uncommitted work through it: agent A stashed its
implementation, agent B popped and received it. A was left holding only its modified **test**
files — a change set that still passes its own targeted tests while the implementation is missing,
which is exactly the shape that reaches review looking complete. No structured return contract
catches this, because an agent reports what it *did*, not what actually survived in the tree.

**Rules:**
- **Never `git stash` / `stash pop` / `stash apply`** in a multi-worktree run. To set changes
  aside, commit to your own branch instead — a commit is worktree-local and reversible. To
  compare against another state, use `git diff <ref>`.
- **Commit by explicit file path.** Never `git add -A` or `git add .` while other worktrees are
  active, so a stray file from another tree can't ride along onto the wrong branch.

**The generalization matters more than either rule:** before assuming parallel agents are
isolated from each other, ask which git state is per-worktree and which is per-repository.
`refs/stash` is unlikely to be the only shared one.

## 3. Stacking and merge mechanics

**Derive the PR base from where HEAD actually is; never pass one in.** In a shared worktree,
`HEAD` is wherever the previous story left it, so every story after the first *necessarily* stacks
on its predecessor. "Branch off the tip but open the PR against the aspect/root branch" is not
available — it would put the predecessor's commits in this story's diff. So: story 1 → aspect
branch, story N → story N-1's branch.

**Never squash a stacked PR.** Squashing story 1 rewrites the commits story 2's diff is computed
against, corrupting it. Merge the chain in order with `--merge`. Check the very first merge of any
run — it's the cheapest place to catch the instruction having been ignored, and confirms itself
cleanly when followed: the parent branch carries a real `Merge pull request #N` commit with the
story's commits intact beneath it.

**Force-push safely or not at all.** A rebase at the chain's *tip* is safe — nothing stacks on it.
The same rebase on story 2 of a 7-story chain silently detaches every PR built on top of it. State
this as an explicit rule as chains get longer; it's not obvious from the tip case alone.

Both of the above held in practice at real scale, not just in principle: at one run's pause point,
15 branches under one flat prefix, 8 open story PRs, every derived base correct, zero manual
corrections. The derived-base rule reads like bureaucracy until a 7-deep chain survives without
anyone tracking bases by hand — that's what it buys.

**Pausing a chain is free if nothing lets a subordinate self-resume.** If the surrounding control
flow only ever advances a chain when something outside it explicitly resumes the next step, then
pausing needs no special handling: in-flight work finishes and nothing new starts. (That control-
flow property — what makes a subordinate advance or stall — is a different concern from the git
mechanics here; this skill only notes that the git side comes for free once it holds.)

**Prefer merging a completed stage into the integration branch over stacking the next stage on top
of it, when a merge is available.** When later work depends on an earlier stage's output, there
are two options:
1. Cut the next stage's branches off the earlier stage's branch (a stack).
2. Merge the earlier stage's PR into the integration branch first, then cut the next stage from
   there.

Option 2 is strictly better whenever a merge is actually available: one base to track instead of a
chain, and no risk of a rejected PR having to be unwound across everything built on top of it.
Option 1 is the fallback for when the merge is blocked (e.g. pending human review with no reviewer
yet available). Decide this per stage, not once for the whole run — availability can change stage
to stage.

**A branch's base is a fact about when it was cut, not about where the run is now.** Cutting every
aspect base at setup — one dispatch, one approval, all from the run base's current SHA — is correct
at the moment of creation and wrong by the time a later wave dispatches. Wave 1 merges into the run
base; a wave-2 aspect base cut at setup still points at the pre-wave-1 SHA, so wave 2 builds against
a tree holding none of wave 1's diff, which is the dependency the wave ordering exists to enforce.

Nothing surfaces it. Every branch exists and is valid, the ledger reads wave 1 `done` and wave 2
`pending`, and it is not a conflict — wave 2's PRs build, test and merge cleanly against the stale
base and drop the dependency in silence. What does surface is a sub-agent that cannot find work
that landed: one run renamed `_get_now_date` to `resolve_reference_date` in wave 1, and a wave-2
agent on a stale base greps for the new name, finds nothing, and reasonably concludes the
coordinator's trap rows are wrong.

**Cut an aspect base at the moment its wave dispatches.** Where bases were pre-cut, refreshing them
is a recorded step of the wave's dispatch, not something remembered:

```
git rev-list --count <run-base>..<aspect-base>   # what the aspect base carries alone
git rev-list --count <aspect-base>..<run-base>   # landed work the aspect base is missing
```

The second count is the discriminator — non-zero at dispatch time means the base is stale. When the
first count is `0` the base carries nothing of its own, so re-point it with
`git branch -f <aspect-base> <run-base>`; when it is non-zero, merge the run base in instead,
because re-pointing would discard real commits. Either way git refuses while the base is checked
out — `fatal: cannot force update the branch 'x' used by worktree at ...` — so release that
worktree first. Merging a run base into an aspect *base* is not the integration-into-aspect merge
forbidden below: nothing is stacked on it yet, and there is no PR diff to pollute.

**Never merge the integration branch into an aspect branch.** When an aspect branch and the
integration branch have both appended to one shared file and conflict at merge, the reconciliation
is directional: land the integration-side version on the integration branch, then have the aspect
branch revert its local copy. Merging the integration branch *into* the aspect branch drags every
unrelated integration commit into the aspect PR, and the PR's diff then lies to its reviewer.
Observed once, resolved correctly exactly this way — the orchestrator folded the conflicting entry
into the integration branch, the coordinator reverted its duplicate.

**A gating deadlock to check for before a run starts:** if the plan requires stage N+1 to wait for
stage N to merge, *and* separately forbids the agents from merging into the integration branch
themselves, then nothing can ever start stage N+1 without a human doing the merge. That's fine if
it's intended — but confirm it's intended, because unnoticed it's a silent stall with no error to
surface it.

**Read `origin/<branch>` after a fetch; a local branch ref answers a different question.** One
branch, three refs, and in a parallel run they routinely disagree:

- `refs/heads/<b>` moves when *this* checkout commits, merges or resets. A fetch never moves it.
- `refs/remotes/origin/<b>` moves when you fetch or pull, and not otherwise.
- The branch on the remote moves when any agent pushes, and when a PR merges on the forge.

A coordinator's own checkout does none of the run's work. Merges land in a sub-agent's worktree and
get pushed, or on the forge when a PR is merged, and neither touches the coordinator's
`refs/heads/<b>` — reading it is reading your own history, not the run's. One coordinator read a
merged worker loop from its local ref, found the pre-change code, and concluded a PR's split had
never landed.

Worktrees of one `.git` do share `refs/heads`, so a sibling worktree's *local* commit moves the ref
normally. That is what makes the failure selective, and so easy to trust wrongly: the work that
goes missing is exactly the work that left via the remote.

Fetch first, every time — before a fetch, `origin/<b>` is a cache that is stale in precisely the
same way. Then read with `git show origin/<b>:<path>` and `git log origin/<b>`.
`claims-and-scope-discipline` owns the general rule that a command which cannot return the
disproving case is not evidence; this one is only about which ref tracks what.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/git-worktree-topology-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
