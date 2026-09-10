# Top-level coordinator

Read this file, and only it. It holds `coordinate_plan(plan)` — the one loop this actor runs — plus
the run artifacts, the operational units, and the human's review surface, all of which the loop
below refers to by name.

## What this actor does with its own hands

Docs, tickets, and minor fixes — never implementing a ticket. Implementing one, including any fix
round on a PR, is a second-level coordinator's job (`second-level-coordinator.md`); dispatch it.

Otherwise: it always has a base branch, cutting one when none was given; it owns the run artifact
directory and passes its absolute path down in every brief (`brief-contract.md`); it dispatches one
second-level coordinator per **aspect** — one independently deliverable slice of the plan — even for
a single-aspect plan; it performs every aspect-base → base merge and opens the closing base → trunk
PR without merging it; it seeds review recommendations before coding starts; and it writes every
accepted deviation into the plan doc (`plan-docs` owns rewrite-in-place, never append).

## Run artifacts this actor owns

Four artifacts, two homes. Pass each absolute path down in every brief rather than letting a
sub-agent resolve "the scratchpad" itself — a dispatched agent's scratchpad directory carries its
own session UUID, so a resolved-locally path can silently point somewhere else.

| Artifact | Home | Lifetime |
|---|---|---|
| Skill-efficacy log | `~/.claude/skill-efficacy/<ticket>-<date>.md` | Outlives the run — a human reads it afterward. Create the directory; it does not exist yet |
| Review recommendations | This session's scratchpad | The run |
| Per-PR review file | This session's scratchpad | The run |
| **Run notes** | This session's scratchpad | The run; presented in full at close-out |

Review recommendations and the per-PR review file are `second-level-coordinator.md`'s content: this
actor seeds the first and creates the directory both live in, but what goes in either belongs there.

**Run notes** — things that must reach the user without stopping the run: work an agent skipped, a
red check that does not reproduce on the base ref, significant-but-unrelated findings that became
tickets only, and any operational unit waiting on the closing PR. `needs_human()` stops the run now;
a run note is read at the end. One condition is never both.

## Operational units: nodes, not tickets, not PR steps

An **operational unit** is a deploy, an IAM grant, a manual migration, or a cutover — a step no
coding agent can perform. `partition()` returns these alongside PR units, and each occupies a real
node in the wave graph, so a PR unit can depend on one the way it depends on another PR.

Folding one into a code PR hides it: the PR merges, the step does not run, and nothing in the diff
says so. A ticket outside the partition loses the ordering constraint instead — nothing would
sequence it against the PRs around it. A node in the graph is the only place that both runs the step
and keeps its place in line.

Every operational unit is one of two kinds, and `partition()` says which:

- **Branch-runnable** — can run against the base branch mid-run: an IAM grant, a dev-env deploy from
  a branch, a migration on a dev database. It blocks its wave until a human confirms it ran or
  explicitly skips it — the one `needs_human()` condition where the human performs the step, rather
  than reviewing a decision an agent made.
- **Trunk-dependent** — needs code already on trunk: a production deploy, a cutover. Nothing reaches
  trunk until the human merges the closing PR, so these cannot run mid-run at all. They go into the
  closing PR body as an ordered runbook, and into the run notes. A PR unit that depends on one is a
  plan defect — `partition()` rejects it and this actor corrects the plan in place rather than
  scheduling the impossible.

## What the human reviews

Every inner PR is reviewed and merged by agents. The human's surface at close-out is exactly three
things: the closing base → trunk PR, whose body lists every inner PR with its ticket and round
count and carries the run notes in full; the per-PR review files, linked or collapsed into that PR
body; and any escalation PR, left open and explicitly marked not for merging. The inner PRs stay in
history for anyone who wants the raw diff, but the human's own reading is converged agent review, not
diff-by-diff.

## The loop

Falsify the plan against the live repo before any dispatch — every claim left unchecked is one N
agents will implement faithfully, because their brief *is* the plan.

```
coordinate_plan(plan):
    # Never implements a ticket. Docs, tickets, minor fixes only — this actor's own scope.

    artifact_dir = this_session_scratchpad_dir()           # absolute — run artifacts, above
    efficacy_log = "~/.claude/skill-efficacy/<ticket>-<date>.md"   # the skill-efficacy log
    ensure_jira_tree(plan)                    # epic + stories + tasks (tracker-shape rules are
                                               # second-level-coordinator.md's); diff the plan
                                               # against the tickets that exist, and reconcile
                                               # the plan against itself — the ticket list is
                                               # not the work list, and a plan's own count table
                                               # and wave list can drift apart from each other
    base = given_base_branch(plan) OR cut_branch(from = real_trunk, name = plan.ticket)

    # Falsify the plan against the live repo BEFORE any dispatch. Every claim left
    # unchecked is one N agents implement faithfully, because their brief IS the plan.
    # Delegate the checking to an agent if the claim list is long (goal 3); the
    # correction is this actor's.
    for claim IN plan.factual_claims:
        #   symbols and paths      -> grep them
        #   asserted numbers       -> re-run the query, count the rows
        #   "pending" prerequisites-> git log / gh pr view / the live schema, not a status field
        #   a prescribed rule      -> measure it against real data
        #   a mechanical acceptance check -> review the CHECK itself, against two things:
        #       does the pattern actually implement the rule it claims to enforce, and
        #       does the criterion survive the change it gates, not just today's code.
        #       A correct pattern enforcing a wrong criterion reports green for three
        #       waves running — that is worse than no check at all.
        if falsified(claim):
            correct_in_place(plan, claim)          # rewrite the section, never append —
                                                    # plan-docs owns this
            if contradicts_the_plan_premise(claim): AWAIT_DECISION(claim)

    aspects = partition(plan)          # yields PR units AND operational units, above
    # partition() criteria, in priority order:
    #   1. small PRs                     (goal 1)
    #   2. a clear testable seam per PR  (goal 2) — the /tdd boundary. A design that
    #      needs `gather`, sleeps, or retries to make a concurrency test pass has the
    #      wrong seam, not a slow test: name the seam now, don't discover it after
    #      dispatch — a coordinator has nobody to ask once the agent is running.
    #   3. AGENTS.md aspect boundaries
    #   4. no two PRs touching one file — shared files get sequenced, never reassigned:
    #      the later PR merges the earlier one's branch first and works from the merged
    #      diff, since the original finding's line numbers are already stale
    #   5. a deploy, IAM grant, migration or cutover is an OPERATIONAL unit, classified
    #      branch-runnable or trunk-dependent (above), never folded into a code PR and
    #      never left out of the graph
    #   6. a PR unit depending on a trunk-dependent unit is a plan defect: correct the plan
    #
    #   A push-only PR — branch and commits already exist — gets no sub-agent: a brief
    #   that creates the branch would collide with or redo landed work. Handle it inline
    #   (`git push`, `gh pr create`); it still occupies its wave slot, because a child
    #   cannot open its PR until this parent reaches the remote.
    # A single-aspect plan is a one-element list. It still gets a coordinator — this
    # actor never runs the PR loop itself (goal 3).
    seed_review_recommendations(artifact_dir, aspects)   # review recommendations —
                                                          # second-level-coordinator.md

    for wave IN dependency_waves(aspects):

        # A branch-runnable operational unit blocks its wave — only a human can perform
        # it (branch-runnable, above).
        for unit IN wave WHERE unit.is_operational:
            AWAIT_DECISION(unit.runbook_step, ["it ran", "skip it"])   # needs_human()
            set_ticket_status(unit.ticket)

        pending = []
        for aspect IN wave WHERE NOT aspect.is_operational:
            pending.append(
                dispatch(role  = SECOND_LEVEL_COORDINATOR,
                         model = "opus",      # explicit — a fork would inherit this
                                              # agent's model instead
                         base  = cut_branch(from = base, name = aspect.name),
                         brief = brief_for(aspect, artifact_dir, efficacy_log)))  # brief-contract.md

        # Handle each report as it ARRIVES. Do not wait for the wave to drain —
        # an early finisher must not idle behind a slow sibling. Goal 5.
        while pending NOT empty:
            report = await_next(pending)                   # brief-contract.md
            check_evidence(report)                         # verified vs. inferred
            check_brief_compliance(report)                 # was /tdd used? report field is enough

            if report.status == blocked:
                # A child hit a needs_human() condition. Surface it, then resume the child.
                answer = AWAIT_DECISION(report.blocked_on, report.options)
                resume(report.agent, answer); pending.append(report.agent)
                continue

            if report.left_undone:           record_run_note(report.left_undone)   # run notes
            if report.skipped_planned_work:  record_run_note(report.skipped)       # not a stop
            if report.red_checks_not_on_base: record_run_note(report.red)          # not a stop
            if report.unrelated_tickets:     record_run_note(report.unrelated_tickets)
                                              # run notes — significant findings ticketed,
                                              # not fixed, because they were unrelated

            if report.deviations:
                write_deviations_into_plan(report.deviations)   # rewrite in place — plan-docs

            # Carry the wave forward. Checked on EVERY report, deviations or not: a PR can
            # follow its plan exactly, report nothing, and still move a signature its
            # children consume. The change inventory catches that; a deviation list cannot.
            if affects_later_waves(report.deviations, report.changes):
                repartition_remaining(aspects)                 # the next wave's brief_for() now
                reconcile_jira_tree(plan)                      # reads the corrected plan

            record_artifacts(artifact_dir, report)         # review recommendations, above
            append_skill_efficacy(efficacy_log, report)    # the skill-efficacy log —
                                                            # outlives the run, not the scratchpad

            merge_into(base, report.aspect_base_branch)    # this actor — merge readiness, below
            if conflict_between_aspect_base_branches:
                AWAIT_DECISION(conflict)                   # needs_human()
            cleanup(report.aspect_base_branch)             # clean up after merge — SKILL.md

    # Close out — what the human reviews, and run notes, both above.
    trunk_dependent = [u for u IN aspects WHERE u.is_operational AND u.trunk_dependent]

    # Author the two review plans for the pass that comes AFTER this run.
    # dual-scoped-review-plans owns the rules. Skipped when the repo carries no
    # AGENTS*.md and no CLAUDE.md — that skill's step 0 exits, no second source.
    review_plan_paths = []
    if repo_has_standards_docs():
        review_plan_paths = [
            await(dispatch(role = PLAN_AUTHOR, fresh = TRUE,      # NEVER fork — a fork
                           scope = run_artifacts(artifact_dir),   # inherits BOTH scopes
                           excluded = [repo_standards_docs, the_sibling_plan])),
            await(dispatch(role = PLAN_AUTHOR, fresh = TRUE,
                           scope = repo_standards_docs,
                           excluded = [artifact_dir, run_notes, the_sibling_plan]))]
                           # gets the diff and the ticket. NO run artifact, ever
        # Each returns a PATH under plan/. This actor does NOT read either one:
        # no Read, no cat/grep/sed, no subshell. Staying scope-clean is what
        # disqualifies it from synthesising, and that is deliberate.

    # This run never RUNS either pass, and never compares the two.
    pr_url = open_pr(base, into = real_trunk,
                     body = inner_prs_with_tickets_and_round_counts
                          + run_notes
                          + runbook(trunk_dependent)
                          + review_plan_paths)     # PATHS, never plan content
    # NEVER merge_pr here. The human merges base -> trunk.
    present_to_user(pr_url, run_notes, efficacy_log, review_plan_paths)
    return pr_url
```

## The two review plans, at close-out

The run authors them and stops. **It never runs either pass** — the same agents just built the code,
and each PR already had its review rounds. These plans exist for a fresh pass a human decides
whether to spend, once the closing PR is merged.

Two dispatches, and the whole value is that their scope sources are disjoint: one scopes from what
this run accumulated (the review recommendations, the per-PR review files, the run notes, the
deviations), the other from the repo's own standards docs with no knowledge of the run at all. The
second author receives the diff and the ticket and nothing else — handing it a run artifact, or
answering its question about the run, collapses two passes into one.

Three constraints bind this actor specifically, and each is easy to break by being helpful:

- **Dispatch fresh agents, never a fork.** A fork inherits this conversation, which holds the entire
  run — so a forked docs-scoped author starts already contaminated.
- **Hand over paths, never content.** This actor does not read either plan. It has just spent a whole
  run accumulating exactly the context the docs-scoped side must not receive, so anything it absorbs
  it can leak into a brief or a later message.
- **Do not compare them.** Not even the counts. Reporting that one plan is longer starts the
  reconciliation a later session is meant to perform from scratch.

Because it stays scope-clean, this actor cannot be the one that synthesises the passes. That falls to
a session that watched the run without dispatching the authors.

**Brief each author that a Claude agent will execute its plan, not a person.** Each plan is an
agent-facing document per `writing-for-agents`, with completion criteria a reviewer can fail, and it
carries its own scope statement and exclusion list in the file — the session that eventually runs
the pass may never see the brief that produced the plan.

`dual-scoped-review-plans` owns the exclusion lists, the read-back each author reports, the no-fork
rule, and the synthesis rules. It also owns the exit: a repo with no `AGENTS*.md` and no `CLAUDE.md`
has no second scope source, so this step is skipped and the run says so in the run notes.

## Carrying the wave forward, at `affects_later_waves`

The predicate is true when **either** a reported deviation **or** an entry in the report's change
inventory touches a descendant's plan section, or a contract two PRs share — a signature, a schema,
an event name, a status vocabulary.

**The inventory is the half that matters, and the reason this runs on every report.** A sub-agent
reports a deviation when it knowingly departed from its plan section. It reports nothing when it
implemented that section faithfully and the section itself moved a shared signature — from its own
seat that is not a deviation, it is the job. The change inventory is what surfaces it, which is why
`brief-contract.md` demands the inventory rather than trusting a deviation list to carry the case.

Repartitioning here is cheap and silent; discovering it after the next wave has built on a stale
contract is neither. When it fires, the next wave's `brief_for()` reads the corrected plan, so a
descendant never inherits the stale version.

## Merge readiness, at `merge_into`

GitHub's `mergeable` field evaluates a PR against its base independently, so two sibling aspect base
branches can each report green and still conflict with each other — whichever this actor merges
second breaks. The check that holds is **performing an actual merge in a throwaway worktree** before
trusting the result; run it before `merge_into` and treat a real conflict there, not a red
`mergeable`, as the `needs_human()` signal. This is also the moment to build
`claims-and-scope-discipline` §9's integration-merge digest — as each aspect base branch lands, not
after all of them have.

## A dispatched second-level coordinator can die mid-run

A dropped connection, a stall, a terminal API error, between one `await_next(pending)` and the next.
Before relaunching, check what its aspect base branch actually holds — three outcomes:

- **Clean** — nothing landed since the last merge. Relaunch the same brief.
- **A coherent partial** — a PR merged into the aspect base, or a helper written but not yet wired
  up. Keep it; re-dispatch to finish from there rather than restart.
- **A broken partial** — revert it rather than patch around it.

After two failures on the same aspect, stop re-dispatching a fresh coordinator against the whole
aspect: narrow the brief to only the unit still outstanding, or `AWAIT_DECISION` if narrowing does
not converge either. This actor never implements the fix itself — dispatch remains the only path.

## Cross-references this file does not restate

`needs_human()`, `AWAIT_DECISION()`, and `cut_branch()` are defined once, in
`SKILL.md`; call them by name. Git and worktree mechanics belong to `git-worktree-topology`.

**When no ratified plan exists yet, call `plan-and-review`, consume what it returns, and continue
here.** It gives back the plan path, the ticket key, and the partition. Control comes back to this
actor, which is why `plan-and-review` returns rather than calling this skill: entering it and
letting it re-enter here would restart the run from the top. Both skills state this rule at their
own side of the seam, because no description can carry which end the run started from. When it
reports the work needs no plan at all, that is a one-PR, one-aspect partition — it still gets a
second-level coordinator, so this actor never implements it directly.
