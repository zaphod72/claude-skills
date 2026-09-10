# Second-level coordinator

This coordinator owns one aspect — SKILL.md's independently deliverable slice of the plan — end to
end: cutting its aspect base branch, running every PR inside that aspect through build, review, and
merge, and reporting upward when the aspect is done or blocked.

This actor never edits code. Every fix is a dispatch to a coding agent, and every review is a
dispatch to a review agent — never run inline. Goal 3 is why: this coordinator stays a small, cheap
loop only if it never carries a diff or a review pass in its own context, across every PR in the
aspect.

## Model, agent count, and `/tdd` mode per PR

Every coding dispatch carries three decisions this coordinator makes, never the coding agent:
which model, how many agents, and which `/tdd` mode.

**Model.** Sonnet is the default for well-specified work — the brief already carries the decision
the agent needs. Move up to Opus where accuracy rests on judgment the brief cannot fully carry:
shared test infrastructure, an inverted guarantee, subtle transaction or concurrency semantics. Move
down to Haiku only for the most mechanical dispatches — a fix round confined to findings already
judged cosmetic, or a slice with no open design decision. Between two plausible choices, take the
higher one.

**Agent count.** One coding agent per PR by default; it creates the PR's worktree and works
`pr_branch` until merge. Add a second agent only when this coordinator judges the two will not
collide — and two agents can never share `pr_branch`, since git refuses to check out one branch
twice, so the second gets its own **slice branch**: a branch cut off the PR branch for one
non-colliding piece of the same PR, merged back into `pr_branch` once it reports. Files that must
tell one story — a migration, its test, a hand-copied mirror, the doc describing all three — are one
file set and one agent; splitting a single story across agents is how the doc ends up describing a
design the code never implemented.

**`/tdd` mode.** New code goes red-first; code that already works and is only gaining tests goes
mutation-with-control-arm instead. Deciding which mode a PR or slice gets is this coordinator's call
— the brief carries the decision (`brief-contract.md`), and `references/coding-agent.md` owns how
each mode actually executes.

## The review-and-fix cycle

Each PR in the aspect runs the same five-step cycle, at most three review rounds, counting every
review dispatch of any kind. From round 2 the reviewer carries an extra **demand**, not an extra
dispatch — so the cap of three holds even though later rounds ask for more.

1. Dispatch a review agent running `/review`. From round 2 its brief also asks for the convergence
   diagnosis (below), which that same dispatch answers alongside its findings.
2. If every finding is `is_cosmetic()`, or there are none, dispatch a fix agent when there is
   anything to fix, append the fix-round summary, and the PR has converged — go to step 5.
3. Otherwise dispatch a fix agent — briefed to fix directly when every finding is `is_trivial()`,
   or to run `root-cause-fix` first when not (see Cross-references) — append the fix-round summary,
   and go back to step 1.
4. If the third review still finds non-cosmetic issues, open the **escalation PR** — opened without
   converging, for the human to read, never to be merged — and stop this PR.
5. Open the PR and merge it into the aspect base branch.

A fix round is one such dispatch — a coding agent addressing one round's findings, under the same
brief contract as the original build, `/tdd` included.

**The escalation threshold is non-cosmetic, not non-trivial.** Step 4 fires only when a genuine
non-cosmetic finding survives to the third review — never merely because a fix needed
`root-cause-fix` rather than a direct edit.

Round 1's reviewer and every fix agent are read the same way: each reads the PR's review file before
doing anything, and appends its own findings or fix-round summary after. That file is this cycle's
**round memory** — the mechanism that lets round 2's reviewer see round 1's findings and fixes
without this coordinator carrying either in its own context (goal 6). See Review artifacts, below,
for what else the file holds and where it lives.

### The fix-round summary

Every fix round appends one summary to the PR's review file, kept to what a later round's reviewer
cannot already see from the fix commits or the plan updates:

| Post | Do not post |
|---|---|
| The round number | A restatement of the diff |
| Findings deliberately **not** fixed, and why | Anything already in a fix commit message |
| Findings ticketed as unrelated, with keys | Anything already written into the plan |
| Findings judged cosmetic that a reviewer might re-raise | |
| Commit SHAs, as bare pointers | |

**Findings deliberately not fixed, and why, is the line that matters most.** That judgment exists
nowhere in the commits — a diff shows what changed, never what was looked at and left alone — so
leaving it off means round N+1 re-discovers and re-reports the same finding from nothing.

### The out-of-band deadline finding

A review dispatched while other work in the aspect depends on its outcome should not sit on what it
finds until the full report is ready. Name the one finding that has a deadline in that review's
brief, and ask for that finding alone the moment the reviewer reaches a confident verdict on it —
ahead of, and separate from, the full findings report. A review's value is not uniform across its
findings, and the standard full-report convention delivers the urgent one at the same time as the
cosmetic ones, which is too late once dependent work is already running on the wrong assumption.

## The escalation PR

Reaching the third review with non-cosmetic findings still open is the one case where this
coordinator opens a PR that has not converged: push `pr_branch`, open the PR into the aspect base,
comment the last review onto it, and say plainly in that comment that the PR is not for merging — it
exists for the human to read. Then call `AWAIT_DECISION()`.

## The BLOCKED gate, from round 2 on

A round cap counts symptoms; it does not ask why they recur. So from round 2 the review brief adds
two diagnosis questions on top of the findings, and asks for a verdict of **OPEN** or **BLOCKED**:

- Do the rounds so far share **one missing concept** — a single decision nobody made, showing up as
  several separate-looking findings?
- Was the ticket or plan ever **detailed enough for the size of the change** it was asked to carry?

Where the answer to both is no, the verdict is OPEN: these are ordinary bugs with unambiguous fixes,
converging round by round, and the cycle continues. A **BLOCKED** verdict means a decision nobody
made is the real cause of the recurring findings — that is a `needs_human()` condition, raised via
`AWAIT_DECISION()` with the diagnosis as the reason. Firing it at round 2 rather than round 3 is
deliberate: it catches a real gap after one fix round instead of after two more rounds spent
patching that gap's symptoms one at a time.

## The tracker

Every finding from a review round is sorted before it reaches a fix brief:

| Finding | Action |
|---|---|
| Cosmetic or trivial | Fix now. No ticket. |
| Significant and related to the plan | Ticket **and** fix now, in the PR already open |
| Significant and unrelated | Ticket only, excluded from the fix brief, and reported upward as a run note (`top-level-coordinator.md`) |

Set a merged PR's ticket to `Testing` when it needs a dev-env run to verify, or decide whether `Done`
is right when it does not. A ticket labeled `ready-for-human` is never worked — reaching one is a
`needs_human()` stop, not a judgment call.

## Review artifacts: recommendations vs. the per-PR review file

Two artifacts serve goal 6 — spending review effort once — and they are split because they serve
different readers at different scopes.

**Review recommendations, per aspect.** The top-level coordinator seeds this after partitioning
(`top-level-coordinator.md`); this coordinator updates it as each PR converges, so every later PR in
the aspect benefits from what an earlier one already established. It tracks:

- code already reviewed and found correct, so a later round does not re-review it,
- areas touched by more than one agent — a slice's overlap with the rest of its PR,
- areas that took more than one fix round,
- declared scope gaps: every "this PR deliberately does not…" decision, written down as what it is
  and why, so a reviewer never mistakes an intended gap for a defect — harvested before each review
  is dispatched, not after a reviewer has already filed one as a finding,
- a PR's review outcome once its cycle converges or escalates: the axis reviewed (Standards, Spec,
  or the efficacy axis), a one- or two-line findings summary, the round count, and the outcome —
  converged clean, converged with fixes, or escalated — so a later reviewer skips ground this PR's
  cycle already covered instead of re-litigating it,
- anything else this coordinator or its siblings judge worth flagging.

**The per-PR review file.** One file per PR, holding its whole review history: every round's
findings and every fix round's summary. This is the round-memory mechanism named above — a
reviewer's context comes from this file, never from this coordinator relaying it, which is why the
file is scoped to the one PR a reviewer is actually looking at rather than to the whole aspect.

## When the deliverable is tests

When a PR's own deliverable is tests or test infrastructure, its review gains a third axis beyond
Standards and Spec: see `references/review-efficacy-axis.md`.

## Cross-references

`brief-contract.md` owns every brief and report field; `brief_for()`, `brief_for_review()`, and
`brief_for_fix()` all mean that file. This actor's own contribution to a brief is the decisions above
it does not delegate: which model, how many agents, which `/tdd` mode, and — for a fix brief — which
findings are excluded as unrelated (the tracker, above).

`root-cause-fix` is the not-all-trivial fix path. Dispatched from inside this cycle, it fixes in-run
rather than stopping for approval — its own step 6 stop applies only when a human invokes it
directly, not when a fix brief hands it to a coding agent.

`claims-and-scope-discipline` covers verifying a finding before acting on it — the discipline behind
checking a review agent's report before sorting its findings into the tracker — and its §11 carries
the shared-test-infrastructure baseline procedure `is_never_trivial()` relies on.

`/review` owns the finding template every review dispatch produces. `/tdd` owns how a coding agent
actually builds, red-first or otherwise.

Waves, partitioning, run notes, the base branch, and close-out all belong to
`references/top-level-coordinator.md` — this file only receives an aspect already cut from that
partition.

## The `coordinate_aspect` loop

Two nested loops: the outer over the aspect's PRs, the inner over one PR's review rounds. The round
counter belongs to the inner loop, and to this actor — a review agent is dispatched per round and
does not own the count.

```
coordinate_aspect(aspect, aspect_base, artifact_dir, efficacy_log):
    recs = review_recommendations_for(aspect, artifact_dir)         # review recommendations, per aspect

    for pr IN aspect.prs:                     # ---- OUTER: one iteration per PR ----
        # a finished PR is an iteration, not a checkpoint — continuation is the invariant
        pr_branch = cut_branch(from = aspect_base, name = pr.name)  # pushed at cut time
        review_file = artifact_dir + "/review-" + pr.name + ".md"   # per-PR review file
        create_file(review_file, header = "# Review: " + pr.name)   # so round 1's read finds an
                                                                     # empty history instead of a
                                                                     # missing path

        # one coding agent per PR by default; its worktree lives until merge
        agents = [dispatch(role  = CODING_AGENT, model = pick_model(pr),
                           base  = pr_branch, worktree = NEW,
                           skill = "/tdd",             # required in the brief — brief-contract.md
                           brief = brief_for(pr, artifact_dir))]

        if coordinator_judges_no_collision(pr):
            # they cannot share pr_branch — git refuses (one branch, one worktree)
            for slice IN pr.non_colliding_slices:
                agents.append(
                    dispatch(role  = CODING_AGENT, model = pick_model(slice),
                             base  = cut_branch(from = pr_branch, name = slice.name),
                             worktree = NEW, skill = "/tdd",
                             brief = brief_for(slice, artifact_dir)))

        deviations = []
        while agents NOT all reported:
            report = await_next(agents)                    # brief-contract.md
            check_evidence(report)
            check_brief_compliance(report)                 # /tdd used? — the paired report field brief-contract.md demands

            if report.status == blocked:                   # out-of-scope, or any decision
                if resolvable_within(aspect):
                    resume(report.agent, decision); continue
                else:
                    answer = AWAIT_DECISION(report.blocked_on, report.options)  # -> my parent
                    resume(report.agent, answer); continue

            deviations += report.deviations
            if report.branch != pr_branch:                 # a slice — one branch, one worktree; merge order in SKILL.md
                merge_into(pr_branch, report.branch)
                cleanup(report.worktree, report.branch)    # slices only; pr_branch and its
                                                           # worktree survive to merge (clean up after merge)
        pr_worktree = the primary agent's worktree

        write_deviations_into_plan(deviations)             # this coordinator writes plan deviations

        round = 0
        loop:                                 # ---- INNER: review rounds, at most three ----
            round += 1

            # always dispatch — never review inline (goal 3)
            # every round runs /review. from round 2 the brief adds the convergence
            # diagnosis, so it stays ONE review dispatch per round and the cap holds
            # reads review_file first, appends to it, read-only in pr_worktree — round
            # memory; brief-contract.md
            result = await(dispatch(role  = REVIEW_AGENT, skill = "/review",
                                    worktree = pr_worktree, read_only = TRUE,
                                    brief = brief_for_review(review_file, recs,
                                            diagnose_convergence = (round >= 2))))
            if result.verdict == BLOCKED:
                AWAIT_DECISION(result.diagnosis)           # needs_human(). A decision is missing
            findings = result.findings

            if findings is empty OR all(is_cosmetic(f) for f IN findings):
                if findings NOT empty:
                    await(dispatch(role = CODING_AGENT, skill = "/tdd",     # fixes are dispatched — this actor never edits code
                                   worktree = pr_worktree,
                                   brief = brief_for_fix(findings, review_file)))
                append_fix_summary(review_file, round)     # the fix-round summary
                break                                      # converged — PR opens below

            if round >= 3:
                # limit reached with issues outstanding. Open the PR anyway so the
                # human can read it. This PR is NOT for merging — say so (the escalation PR)
                push(pr_branch)
                pr_url = open_pr(pr_branch, into = aspect_base, body = pr.description)
                comment(pr_url, findings, note = "review limit reached; not for merge")
                AWAIT_DECISION(pr_url)                     # needs_human() — the escalation PR

            # sort the findings before briefing the fix — the tracker
            unrelated = [f for f IN findings WHERE NOT is_trivial(f) AND NOT related_to_plan(f)]
            for f IN unrelated: create_ticket(f, outside_epic = TRUE)   # ticket only — significant and unrelated
            to_fix = findings - unrelated
            for f IN to_fix WHERE NOT is_trivial(f): create_ticket(f, in_epic = TRUE)  # ticket and fix — significant and related to the plan

            await(dispatch(role = CODING_AGENT, skill = "/tdd",
                           worktree = pr_worktree,
                           brief = brief_for_fix(to_fix, review_file,
                                   excluded  = unrelated,           # excluded — brief-contract.md's fix-agent brief
                                   root_cause_first = NOT all(is_trivial(f) for f IN to_fix))))
            append_fix_summary(review_file, round)         # the fix-round summary — only what commits won't show

        update_review_recommendations(recs,                # goal 6
            reviewed_and_correct = pr.files,
            fix_rounds           = round,
            multi_agent_areas    = overlap_of(agents))     # review recommendations

        # converged — now the PR is opened and merged (the cycle's step 5)
        push(pr_branch)
        pr_url = open_pr(pr_branch, into = aspect_base, body = pr.description)
        merge_pr(pr_url, into = aspect_base)               # this coordinator merges — SKILL.md's merge table
        cleanup(pr_worktree, pr_branch)                    # clean up after merge — only now
        set_ticket_status(pr.ticket)                       # Testing | Done — the tracker's statuses
        append_skill_efficacy(efficacy_log, pr)            # skill efficacy log

    report_upward(aspect)                                  # brief-contract.md's report fields, including unrelated_tickets
```
