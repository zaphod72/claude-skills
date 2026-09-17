# Second-level coordinator

This coordinator owns one aspect — SKILL.md's independently deliverable slice of the plan — end to
end: cutting its aspect base branch, running every PR inside that aspect through build, review, and
merge, and reporting upward when the aspect is done or blocked.

This actor never edits code. Every fix is a dispatch to a coding agent, and every review is a
dispatch to a review agent — never run inline. Goal 3 is why: this coordinator stays a small, cheap
loop only if it never carries a diff or a review pass in its own context, across every PR in the
aspect.

You are dispatched under the name `plan-rollout-slc-<aspect>`, and every artifact of this run lives
under `~/.claude/plan-rollout-runs/<ticket>/` — the `run_dir` your brief names, as an absolute
path. `~/.claude/skills/plan-rollout/scripts/rollout-db` is the only write interface to the run's
data; `--db <path>` is a global flag before the subcommand.

## Model, agent count, and `mattpocock-skills:tdd` mode per PR

Every coding dispatch carries three decisions this coordinator makes, never the coding agent:
which model, how many agents, and which `mattpocock-skills:tdd` mode.

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

**`mattpocock-skills:tdd` mode.** New code goes red-first; code that already works and is only gaining tests goes
mutation-with-control-arm instead. Deciding which mode a PR or slice gets is this coordinator's call
— the brief carries the decision (`brief-contract.md`), and `references/coding-agent.md` owns how
each mode actually executes.

## The seam: routing headers up, ledger rows sideways

Every agent this coordinator dispatches writes its full report to
`<run_dir>/reports/<agent>.md` and runs `rollout-db report <agent> --file <path>`, returning
only the routing header that command prints — at most 30 lines. `brief-contract.md` owns the 25
report headings and the header's shape.

Two rules make that work, and both belong to this coordinator:

- **`agent upsert` before the agent can report.** `rollout-db report` resolves the run from the
  agent's own `agents` row and exits 1 on an unknown name, so every dispatch that will report goes
  through `dispatch_agent()`, which writes that row and the brief file first. An auditor records an
  `audits` row rather than a report, and is dispatched directly.
- **Route on the header; audit the report.** The header carries counts, SHAs, and
  `empty_sections`. The evidence behind it is checked by an auditor dispatch per coding report
  (`references/auditor.md`), which returns a verdict of at most 10 lines. Read the verdict,
  re-verify one claim yourself, and act on discrepancies.

Notes, traps, and tickets go straight into the ledger — `rollout-db note add`, `trap add`,
`ticket add` — where the top-level coordinator queries them at close-out. This coordinator's own
report carries counts, not the text.

What each header line buys this coordinator:

| Header line | The action it drives |
|---|---|
| `status`, `blocked_on` | `blocked` resolves inside the aspect, or goes up through `AWAIT_DECISION()` |
| `branch`, `head_sha`, `base_at_dispatch` | Check against `origin` before merging a slice; a `head_sha` that is not on `origin` is the audit's first discrepancy |
| `report_file` | The auditor's input. Open a section yourself only when a verdict sends you there |
| `shared_contract_changes` | `SendMessage` to the siblings that build against it, and a bullet in this aspect's own report |
| `deviations`, `plan_errors` | Deviations reach the plan doc through `write_deviations_into_plan()`; a plan error corrects the plan itself |
| `brief_errors` | Fix the next brief before dispatching it — the count is how a wrong instruction stops spreading |
| `left_undone`, `skipped`, `red_not_on_base` | Already `notes` rows. A non-zero count decides whether this PR can converge |
| `tickets`, `ledger_rows` | The tracker. A finding you ticketed with `tickets: none` in the header means the `ticket add` row was never written |
| `files_written` | Confirms `review-recommendations.md` and `inventory-<aspect>.md` were actually written |
| `empty_sections` | Brief compliance: a heading left blank is a requirement nobody answered |

## Sibling coordinators

Cross-aspect facts travel sideways, not through the top-level coordinator. Every sibling
coordinator is named `plan-rollout-slc-<aspect>`, and your brief lists the siblings live at the
moment you were dispatched — that roster is a snapshot, so a later wave's brief names a different
set.

Two kinds of fact move this way, the moment you have them rather than at aspect close-out:

| Fact | Where it goes |
|---|---|
| A trap an agent hit — invisible in a diff, costly to rediscover | `rollout-db trap add --run <t> --agent <a> --repo <r> --path <p> --text <s>`, **and** `SendMessage` to every sibling whose aspect touches that repo or path |
| A shared contract this aspect moved — signature, schema, event, status vocabulary, config key | `SendMessage` to every sibling that builds against it, quoting the `## shared_contract_changes` bullets verbatim |

The `traps` table is the durable half and the message is the timely one: `rollout-db traps --repo
<name> [--path <glob>]` returns traps across every run, and is what a later brief is built from. A
sibling that has already finished cannot be messaged, so the ledger row is the one that must always
be written.

**A predicted total is not one of them.** A count you work out for after both aspects land — "once
these merge, `check-event-types` reads 290" — encodes the set of writers you knew about when you
computed it, so it is a tripwire for you and nobody else. One handed to a sibling omitted that
sibling's own pending literal by construction, and adopting it would have made their work read as a
stray arriving from nowhere. Recompute from your own position at the moment you need the number;
never carry one forward, and never adopt one a sibling computed. The general form is
`claims-and-scope-discipline` §16.

**Fallback when `SendMessage` to a named sibling fails** (from an efficacy log, not verified in this
skill): `SendMessage` to a sibling coordinator by its `plan-rollout-slc-<aspect>` name has been
reported unreachable ("no agent named ... is reachable") even when the brief named that sibling as
live. The reported working fallback is appending the fact to the shared `review-recommendations.md`
that every coordinator in the run writes and reviewers read, with the top-level coordinator relaying
it if the sibling still needs a direct nudge — name this fallback rather than re-inventing it each
time the primary channel fails.

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
5. Open the PR and merge it into the aspect base branch — dispatched to Sonnet, like every other
   git mutation; this actor never runs one with its own hands.

A fix round is one such dispatch — a coding agent addressing one round's findings, under the same
brief contract as the original build, `mattpocock-skills:tdd` included.

**The escalation threshold is non-cosmetic, not non-trivial.** Step 4 fires only when a genuine
non-cosmetic finding survives to the third review — never merely because a fix needed
`root-cause-fix` rather than a direct edit.

Round 1's reviewer and every fix agent are read the same way: each reads the PR's review file before
doing anything, and appends its own findings or fix-round summary after. That file is this cycle's
**round memory** — the mechanism that lets round 2's reviewer see round 1's findings and fixes
without this coordinator carrying either in its own context (goal 6). See Review artifacts, below,
for what else the file holds and where it lives.

**A resumed agent is asked which round it is on, never told.** Commit subjects are inference: a
`test:` → `fix:` → `docs:` run reads equally as "build plus one fix round, review pending" and "two
review rounds already closed". The review file above, the tracker, and the agent's own memory are
the record. One coordinator read its stalled agent's eight pushed commits correctly and then told it
to resume at round 2, which it was already past — and with a cap of three, that guess spends the
round standing between this PR and the escalation PR. State the artifacts you verified — branch,
head SHA at `origin`, what is pushed, which PRs are open or merged — and ask for the phase
(`brief-contract.md`, "A resume brief adds").

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

It is still an intermediate PR, so `open_pr()`'s rule holds unchanged: **draft, and no reviewers.**
Draft is what makes "not for merging" mechanical rather than a sentence someone has to notice, and
the human reaches this PR through `AWAIT_DECISION()` — the top-level coordinator hands them the URL
— not through a review request that would ask them to approve a branch nobody intends to merge.

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
| Significant and unrelated | Ticket only, excluded from the fix brief, and recorded with `rollout-db ticket add --in-epic no` plus `note add --kind unrelated_ticket` |

Every ticket this coordinator creates gets a `ticket add` row as it is created — key, title,
`--in-epic yes|no`, and the reason — so the closing PR body is assembled from the ledger rather than
from anyone's memory of the run. Every ticket also carries exactly one triage label at creation —
`ready-for-agent` when it is fully specified (file:line evidence, a stated fix, an acceptance check),
otherwise `ready-for-human` — plus the labels `common-facts.md` names; never leave a new ticket
unlabelled or on `needs-triage`.

Set a merged PR's ticket to `Testing` when it needs a dev-env run to verify, or decide whether `Done`
is right when it does not. A ticket labeled `ready-for-human` is never worked — reaching one is a
`needs_human()` stop, not a judgment call.

## Review artifacts: recommendations vs. the per-PR review file

Two artifacts serve goal 6 — spending review effort once — and they are split because they serve
different readers at different scopes.

**Review recommendations, per aspect.** One file, `<run_dir>/review-recommendations.md`. The
top-level coordinator seeds it after partitioning (`top-level-coordinator.md`); this coordinator
updates it as each PR converges, so every later PR in the aspect benefits from what an earlier one
already established. It tracks:

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

**The per-PR review file.** One file per PR, `<run_dir>/review-<pr>.md`, holding its whole
review history: every round's findings and every fix round's summary. This is the round-memory mechanism named above — a
reviewer's context comes from this file, never from this coordinator relaying it, which is why the
file is scoped to the one PR a reviewer is actually looking at rather than to the whole aspect.

## When the deliverable is tests

When a PR's own deliverable is tests or test infrastructure, its review gains a third axis beyond
Standards and Spec: see `references/review-efficacy-axis.md`.

## Cross-references

`brief-contract.md` owns every brief and report field; `brief_for()`, `brief_for_review()`, and
`brief_for_fix()` all mean that file. This actor's own contribution to a brief is the decisions above
it does not delegate: which model, how many agents, which `mattpocock-skills:tdd` mode, and — for a fix brief — which
findings are excluded as unrelated (the tracker, above). Run `brief-contract.md`'s pre-dispatch gate
on the result before sending it — no unresolved placeholders, every named unit already in the
ledger, and no sentence asserting ledger state ahead of this actor actually creating it.

`root-cause-fix` is the not-all-trivial fix path. Dispatched from inside this cycle, it fixes in-run
rather than stopping for approval — its own step 6 stop applies only when a human invokes it
directly, not when a fix brief hands it to a coding agent.

`references/auditor.md` owns the evidence audit behind a report, and
`references/coding-agent.md` owns how a coding agent builds and reports.

`claims-and-scope-discipline` covers verifying a finding before acting on it — the discipline behind
checking a review agent's report before sorting its findings into the tracker — and its §11 carries
the shared-test-infrastructure baseline procedure `is_never_trivial()` relies on.

`/review` owns the finding template every review dispatch produces. `mattpocock-skills:tdd` owns how a coding agent
actually builds, red-first or otherwise.

Waves, partitioning, the base branch, and close-out all belong to
`references/top-level-coordinator.md` — this file only receives an aspect already cut from that
partition, and writes its notes, traps, and tickets straight into the ledger.

## The `coordinate_aspect` loop

Two nested loops: the outer over the aspect's PRs, the inner over one PR's review rounds. The round
counter belongs to the inner loop, and to this actor — a review agent is dispatched per round and
does not own the count.

`ticket`, `plan`, `origin`, and `self.name` come from this coordinator's own brief.

```
dispatch_agent(name, role, model, base, worktree, skill, brief, read_only = FALSE):
    # every dispatch in this file goes through here: the `agents` row must exist before the
    # agent can run `rollout-db report`, which resolves the run from it
    write_file(run_dir + "/briefs/" + name + ".md", brief)     # the auditor reads the brief
    rollout_db("agent upsert", name, run = ticket, role = role, parent = self.name,
               aspect = aspect.name, branch = base, base_sha = sha_of(base),
               worktree = worktree, status = "dispatched",
               report_path = run_dir + "/reports/" + name + ".md",
               brief_path  = run_dir + "/briefs/" + name + ".md")
    return dispatch(name = name, role = role, model = model, base = base, worktree = worktree,
                    skill = skill, read_only = read_only, brief = brief)   # returns a routing header

audit(header):                                                     # references/auditor.md
    # dispatched directly: an auditor records an `audits` row, not a report, so it needs no
    # `agents` row to resolve a run from
    verdict = await(dispatch(role = AUDITOR, agent = "plan-rollout-auditor", model = SONNET,
                             read_only = TRUE,
                             brief = [header.report_file,                      # the claims
                                      run_dir + "/briefs/" + header.agent + ".md",   # the targets
                                      plan.path, origin]))
    # no verdict back = turn budget, not failure: read audits/<agent>.md, treat every
    # NOT CHECKED heading as unchecked, and resume that auditor on the ones it missed
    verify_one_claim_myself(header)                                # never delegate the whole check
    return verdict                                                 # <=10 lines: evidence, blast_radius

coordinate_aspect(aspect, aspect_base, run_dir, efficacy_log):
    recs = review_recommendations_for(aspect, run_dir)         # review recommendations, per aspect

    for pr IN aspect.prs:                     # ---- OUTER: one iteration per PR ----
        # a finished PR is an iteration, not a checkpoint — continuation is the invariant
        pr_branch = cut_branch(from = aspect_base, name = pr.name)  # pushed at cut time
        review_file = run_dir + "/review-" + pr.name + ".md"   # per-PR review file
        create_file(review_file, header = "# Review: " + pr.name)   # so round 1's read finds an
                                                                     # empty history instead of a
                                                                     # missing path

        # one coding agent per PR by default; its worktree lives until merge
        agents = [dispatch_agent(name  = pr.name + "-build", role = CODING_AGENT,
                                 model = pick_model(pr),
                                 base  = pr_branch, worktree = NEW,
                                 skill = "mattpocock-skills:tdd",     # required in the brief — brief-contract.md
                                 brief = brief_for(pr, run_dir))]

        if coordinator_judges_no_collision(pr):
            # they cannot share pr_branch — git refuses (one branch, one worktree)
            for slice IN pr.non_colliding_slices:
                agents.append(
                    dispatch_agent(name  = slice.name + "-build", role = CODING_AGENT,
                                   model = pick_model(slice),
                                   base  = cut_branch(from = pr_branch, name = slice.name),
                                   worktree = NEW, skill = "mattpocock-skills:tdd",
                                   brief = brief_for(slice, run_dir)))

        deviations = []
        # A coding or review agent that stops on a watchdog turn limit or a session rate limit
        # (HTTP 429) is not a failure — both hit routinely on work this size, and the agent and its
        # worktree survive them. Assess the tree, then resume with `SendMessage`: state the
        # artifacts, ask the phase (brief-contract.md, "A resume brief adds"). Re-dispatching fresh
        # discards that worktree state (top-level-coordinator.md's die-mid-run section covers the
        # same distinction one level up).
        while agents NOT all reported:
            header = await_next(agents)                    # the routing header, not the report
            verdict = audit(header)                        # the evidence check — references/auditor.md
            act_on(verdict.discrepancies)
            check_brief_compliance(header.empty_sections, verdict)   # an unfilled contract field —
                                                           # mattpocock-skills:tdd and the seam among them

            if header.status == blocked:                   # out-of-scope, or any decision
                if resolvable_within(aspect):
                    resume(header.agent, decision); continue
                else:
                    answer = AWAIT_DECISION(header.blocked_on, header.options)  # -> my parent
                    resume(header.agent, answer); continue

            for trap IN rows_added_by(header.agent, "traps"):       # sideways, the moment I have it
                SendMessage(siblings_touching(trap.repo, trap.path), trap)
            if header.shared_contract_changes > 0:
                SendMessage(siblings_building_against(header), header.shared_contract_changes)

            deviations += read_section(header.report_file, "## deviations")
            if header.branch != pr_branch:                 # a slice — one branch, one worktree; merge order in SKILL.md
                merge_into(pr_branch, header.branch)        # dispatched to Sonnet — this actor never
                                                           # runs a git mutation with its own hands
                cleanup(header.worktree, header.branch)    # slices only; same dispatch — pr_branch and
                                                           # its worktree survive to merge (clean up after merge)
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
            header = await(dispatch_agent(name = pr.name + "-review-r" + round,
                                    role = REVIEW_AGENT, model = pick_model(pr),
                                    skill = "/review",
                                    base = pr_branch, worktree = pr_worktree, read_only = TRUE,
                                    brief = brief_for_review(review_file, recs,
                                            diagnose_convergence = (round >= 2))))
            if header.status == blocked:                   # a BLOCKED verdict reports as blocked
                AWAIT_DECISION(header.blocked_on)          # needs_human(). A decision is missing
            findings = read_findings(review_file)          # appended by the reviewer — round memory

            if findings is empty OR all(is_cosmetic(f) for f IN findings):
                if findings NOT empty:
                    await(dispatch_agent(name = pr.name + "-fix-r" + round,   # fixes are dispatched —
                                   role = CODING_AGENT, model = pick_model(pr),  # this actor never
                                   skill = "mattpocock-skills:tdd", base = pr_branch,             # edits code
                                   worktree = pr_worktree,
                                   brief = brief_for_fix(findings, review_file)))
                append_fix_summary(review_file, round)     # the fix-round summary
                break                                      # converged — PR opens below

            if round >= 3:
                # limit reached with issues outstanding. Open the PR anyway so the
                # human can read it. This PR is NOT for merging — say so (the escalation PR)
                push(pr_branch)                             # dispatched to Sonnet — this actor
                pr_url = open_pr(pr_branch, into = aspect_base, body = pr.description)  # never
                                                             # runs a git mutation with its own hands;
                                                             # draft, no reviewers — SKILL.md's open_pr
                comment(pr_url, findings, note = "review limit reached; not for merge")
                AWAIT_DECISION(pr_url)                     # needs_human() — the escalation PR

            # sort the findings before briefing the fix — the tracker
            unrelated = [f for f IN findings WHERE NOT is_trivial(f) AND NOT related_to_plan(f)]
            for f IN unrelated:                                     # ticket only — significant and unrelated
                key = create_ticket(f, outside_epic = TRUE, labels = triage_labels(f))
                rollout_db("ticket add", key, run = ticket, in_epic = "no", reason = f.summary,
                           labels = triage_labels(f))
                rollout_db("note add", kind = "unrelated_ticket", text = key + ": " + f.summary)
            to_fix = findings - unrelated
            for f IN to_fix WHERE NOT is_trivial(f):                 # ticket and fix — significant and related to the plan
                key = create_ticket(f, in_epic = TRUE, labels = triage_labels(f))
                rollout_db("ticket add", key, run = ticket, in_epic = "yes", reason = f.summary,
                           labels = triage_labels(f))

            await(dispatch_agent(name = pr.name + "-fix-r" + round,
                           role = CODING_AGENT, model = pick_model(pr),
                           skill = "mattpocock-skills:tdd", base = pr_branch,
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
        push(pr_branch)                                    # one dispatch to Sonnet performs push,
        pr_url = open_pr(pr_branch, into = aspect_base, body = pr.description)  # draft, no
                                                            # reviewers — SKILL.md's open_pr
        merge_pr(pr_url, into = aspect_base)               # readies the draft, then merges —
                                                            # SKILL.md's merge table; never this
                                                            # coordinator's own hands
        cleanup(pr_worktree, pr_branch)                    # same dispatch — clean up after merge, only now
        set_ticket_status(pr.ticket)                       # Testing | Done — the tracker's statuses
        append_skill_efficacy(efficacy_log, pr)            # skill efficacy log — this coordinator
                                                            # writes it; nobody relays it upward
        write_inventory(run_dir + "/inventory-" + aspect.name + ".md", pr)  # the auditor's
                                                            # blast-radius input

    write_report_file(run_dir + "/reports/" + self.name + ".md")   # all 25 `##` headings
    return rollout_db("report", self.name, file = that_path)   # return the printed header, nothing else
```
