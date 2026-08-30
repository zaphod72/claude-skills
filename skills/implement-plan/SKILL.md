---
name: implement-plan
description: "Implement a multi-PR plan by dispatching one sub-agent per PR in dependency waves, checking each one's deviations before they reach the next."
disable-model-invocation: true
---

# /implement-plan

Drive a stacked-PR plan to completion from this conversation: parse the plan into a PR graph, dispatch one sub-agent per PR in dependency **waves**, and check every **deviation** each sub-agent reports before it can reach the PRs built on top of it.

This conversation stays the orchestrator throughout. Sub-agents implement single PRs and report; they never judge how their work affects other PRs.

The plan is a living document, not a fixed brief. It lives in the repo, it gets corrected as the run falsifies it, and its runtime-only checks section stays true until validation consumes it.

## Usage

```
/implement-plan @<plan-doc> --base <branch>     # full run
/implement-plan @<plan-doc> --base <branch> --no-pr    # commit + push nothing, open no PRs
/implement-plan @<plan-doc> --base <branch> --serial    # one sub-agent at a time
/implement-plan @<plan-doc> --base <branch> --only PR8,PR9    # just these PRs
```

## Steps

### 1. Pin the inputs

The **base branch** is the root the whole stack sits on. Require it explicitly: take it from `--base`, and if it is absent, ask. A base stated inside the plan doc is a suggestion to confirm with the user, not an answer. Never infer it from the current branch, `main`, or `staging`. If the plan has a top-level ticket and no root branch exists yet, the `ticketed-plan-rollout` skill cuts one (named after the ticket, off the repo's real integration branch) and commits the plan doc to it — that branch is `--base`.

Record the plan path as given and the flags in effect.

### 2. Home the plan doc

**Follow the `plan-docs` skill** (`~/.claude/skills/plan-docs/SKILL.md`) — it owns where the plan lives, how it stays true, where findings go, and the runtime-only checks section. Read it now; the rest of this skill assumes it.

Do this **before** step 3 reads the plan for facts: step 3 writes corrections back into the doc, and a plan falsified at one path and relocated afterwards leaves its corrections behind.

Two of `plan-docs` §4's rules matter most in a multi-agent run:
- The orchestrator is the only writer, always in the main working tree — a sub-agent's edit strands on its own branch.
- `docs(plan):` commit on the base branch at each wave boundary.

### 3. Falsify the plan, and correct it in place

Read the plan doc in full — and **check its factual claims against the repo and the live system before you dispatch anyone.** A plan is a set of assertions made at writing time. Some decayed since; some were never true. Every one you falsify now is one a sub-agent would otherwise implement faithfully, because its brief is the plan.

Falsify at least:

- **Every symbol and path the plan names.** Grep for each function, table, column, config key, and file it says to change. A plan section describing code that is not in this repo is the cheapest catch available and the most expensive miss — the sub-agent will invent something plausible to satisfy it.
- **Every number the plan asserts.** If it says a query yields N rows, or a column is populated on M of K, run it. These become the sub-agent's targets in step 8.
- **Every prerequisite the plan says is pending.** Merged PRs, applied migrations, deployed jobs. Check `git log`, `gh pr view`, and the live schema — not the plan's status column.
- **Every rule the plan prescribes, against the data it will act on.** A rule can read correctly in prose and still be wrong. Measure what it would actually select and reject before anyone builds it.

**Write each correction into the plan doc itself, not only into the sub-agent brief.** A brief-only correction fixes this run and loses the finding: the plan still asserts the false claim, so the next run rebuilds the error you already paid to find. Findings beyond the correction itself go on Jira tickets per `plan-docs` §3 — the story's ticket, or the epic when they span stories.

When your measurement contradicts the plan, **stop and put it to the user, with the measurement, before dispatching.** This is a different trigger from step 9's deviations: those fire after an agent reports, this one fires before any code exists, and it is where the largest errors are cheapest to fix.

Done when the base ref, the plan's new path, the flags in effect, and every claim you falsified are stated back to the user.

### 4. Build the PR graph

A plan's dependencies come from three places, and the tree alone is incomplete:

- **The stack diagram** — indentation gives each PR its parent; siblings at one indent share a parent.
- **Annotations on parentless PRs** — e.g. `needs PR4 + PR17` on a PR cut straight from the base.
- **The prose constraints section** — ordering stated only in sentences, e.g. `PR2 → PR3, PR8, PR9`.

Read all three. Per PR, record: id, branch name, parent (or none), extra dependencies, the plan section covering it, and the files/modules its section names.

### 5. Read each PR's status, and interpret it out loud

Plans carry per-PR status, and its vocabulary is local to the plan. `DONE` frequently means "code written, branch local, still needs pushing" — a PR that still has work. Classify each PR as **implement**, **push-only**, or **skip**, and put that classification in the step 7 table for the user to correct. Guessing here is fine; guessing silently is not.

### 6. Assign models and compute waves

**Model per PR**, from the scope of its plan section:
- **Opus** — design-heavy, cross-cutting, or where the plan leaves real choices open.
- **Sonnet** — well-specified feature and fix work.
- **Haiku** — mechanical edits: renames, config, docs, wiring already fully described.

**Waves.** A PR is eligible when its parent and every extra dependency has landed. Siblings sharing a parent go in the same wave **only when their plan sections name no overlapping files** — two isolated worktrees both editing a lockfile, `pyproject.toml`, a migration sequence, or one module conflict at merge time, invisibly. Serialize overlapping siblings within the wave and record why.

`--serial` collapses every wave to one PR at a time. `--only` narrows the run to the PRs listed; any ancestor left out is treated as already landed, and its child branches from that ancestor's existing branch.

### 7. Gate on user approval

Show one table before any code changes: PR, branch, base ref, action from step 5, model, wave, and for serialized siblings the overlap that forced it. List the deviation-escalation rule you'll apply (step 9).

Wait for approval. This is the only gate before branches and PRs start existing.

### 8. Run the wave

Resolve each PR's base ref to a SHA and record it — step 9 compares the agent's reported SHA against this.

Dispatch one sub-agent per PR in the wave — all of them in a single message so they run concurrently — each with `isolation: "worktree"`, its assigned model, and the brief described in `references/sub-agent-brief.md`.

`references/sub-agent-brief.md` — read at step 8, before dispatching each sub-agent.

**Worktrees are for fan-out, not for chains.** When a run is serial and consecutive PRs rework the same module, isolation costs more than it saves: you get N copies of one heavily-edited file to merge, and each agent reads a stale version of the code its predecessor just restructured. Run those in the main tree, one at a time, and let each agent read what actually landed.

**A sub-agent can die mid-run** — a dropped connection, a stall, a terminal API error. When one does, `git status` before relaunching. Three outcomes, three responses: a clean tree means relaunch the same brief; a coherent partial (a helper written but not yet wired up) is worth keeping and finishing; a broken partial should be reverted, not patched. After two failures on the same small task, do it inline — a third dispatch costs more than the work.

**Push-only PRs need no sub-agent.** Their branch and commits already exist, so a brief that creates the branch would either collide or redo landed work. Handle them inline: `git push -u origin <branch>` then `gh pr create --base <parent-branch>`. They still occupy their wave slot, because a child cannot open its PR until this parent reaches the remote.

**Push sequencing differs by mode, and it is not optional:**
- **Default** — every branch in a wave pushes before the next wave starts. `gh pr create --base <parent-branch>` fails when the parent branch is absent from the remote, so children cannot open PRs until their parent is pushed.
- **`--no-pr`** — nothing pushes and no PR opens. Children still branch from their parent correctly, because worktrees share one `.git` and see local branches.

### 9. Check what came back

Per sub-agent: confirm the base SHA it reports matches the SHA you recorded at dispatch. A mismatch means it built on the wrong parent — stop and resolve before the wave's work propagates.

**Re-verify what the agent claims about its own work; read closely what it claims about the domain.** These pull in opposite directions and both matter. Its `checks` field is a claim you can cheaply falsify, so falsify it. Its `plan_errors` cannot be re-derived from a diff — the agent read the code with the plan section in hand, which is a vantage point you did not have when you wrote the brief. Expect some of them to contradict *your* brief rather than the plan, and treat that as the report working: a section that comes back with an empty `plan_errors` every time usually means the brief left no room to push back, not that the plan was flawless.

**Re-run the checks yourself rather than reading the agent's `checks` field.** That field is a claim, and claims fail in both directions: agents have returned placeholder text instead of a report, and editor diagnostics captured mid-edit have shown undefined symbols in files that were correct by the time the agent finished. Run the repo's lint and type tasks plus the PR's own test files — seconds each — and spot-check the assertions the plan cared about. Where the agent's report and your own run disagree, your run wins. Long full suites go in the background (see the brief); you do not need to block on one to start reviewing, writing the commit message, or updating docs.

Then compute **blast radius** yourself from the factual change inventory each agent returns. The agent saw only its own plan section, so it cannot know what a later PR assumes; you hold the graph, so you do. Map each changed file, symbol, signature, schema, and config key onto the plan sections of every PR not yet built.

**Pause and bring it to the user** when any of these holds:
- A change alters a shared interface, function signature, DB schema, config key, or other cross-PR contract.
- A changed file or symbol appears in a descendant PR's plan section.
- The agent skipped or deferred work the plan called for.
- The agent is blocked, or its checks are red and the failure does not reproduce on the base ref.

Otherwise record the deviation and continue.

#### Write the wave back into the plan doc

Before the next wave dispatches, edit the plan itself. Every accepted deviation and every confirmed `plan_error` goes into the affected plan section, as the new statement of what that PR does — not as an appended note about what it was once supposed to do. The brief tells each agent that deviation notes already in a plan section count as accepted, and that only works if something writes them there.

Then put anything still open on a ticket — the story's ticket, or the epic when it spans stories — so it survives the wave boundary. Commit the plan doc on the base branch (`docs(plan):`) at each wave boundary.

#### Cases only a live run can settle

**Watch for behavior no static read of the diff can confirm** — it depends on live data, timing, concurrency, or an external service. These usually surface in an agent's `follow_ups` or `runtime_only_concerns`, or in your own blast-radius read of the diff. For each one:

1. **Check the logging is sufficient to catch it running.** Open the changed code and confirm there's a structured log line at the decision point, with the fields needed to spot it later (event type, IDs, the value or branch taken). If it's missing or too thin, add it yourself or send it back to the sub-agent before the wave closes. Logging comes first — never let the record outrun the instrumentation.
2. **Record it** in the plan doc's `## Runtime-only checks` section, in the format `plan-docs` specifies, tagged with the story's ticket key. Where you measured a number in step 3, that number is the expected value.

#### Carry the wave forward

Into the brief of each descendant, and of any PR the plan says depends on this one, fold both:
- **every accepted deviation**, and
- **the change inventory entries that intersect that PR's plan section** — the same blast-radius mapping, pointed at the child rather than at escalation.

A PR that followed its plan exactly still reports no deviation while having fixed the real signature, keyword names, config key, and module path its children consume. The inventory is what carries those.

Report the wave's outcome, then return to step 8 for the next wave.

### 10. Close out

Prune the run's worktrees — commits live on branches in the shared `.git`, so removing the worktrees keeps every branch. Write a run report to the scratchpad: per PR its branch, PR link, checks result, and deviations.

Make the plan doc final and committed — reflecting what was actually built, with every runtime-checks row either struck (validated) or migrated to a Jira ticket per `plan-docs` §5. Tell the user the path, and give a one-line summary of what was migrated rather than validated — those tickets are the part of the run that isn't done just because checks were green.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/implement-plan-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
