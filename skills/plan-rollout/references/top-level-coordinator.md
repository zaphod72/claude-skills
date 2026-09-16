# Top-level coordinator

Read this file, and only it. It holds `coordinate_plan(plan)` — the one loop this actor runs — plus
the run artifacts, the operational units, the resume path, the evidence check, and the human's
review surface, all of which the loop below refers to by name.

## What this actor does with its own hands

Docs, tickets, and minor fixes — never implementing a ticket, and a "minor fix" never covers a
finding a sub-agent surfaced as deliberately not actioned. Implementing a ticket, including any fix
round on a PR, is a second-level coordinator's job (`second-level-coordinator.md`); dispatch it.

Otherwise: it always has a base branch, cutting one when none was given; it owns the run directory
and the ledger and passes both absolute paths down in every brief (`brief-contract.md`); it
dispatches one second-level coordinator per **aspect** — one independently deliverable slice of the
plan — even for a single-aspect plan; it performs every aspect-base → base merge and opens the
closing base → trunk PR without merging it; it seeds review recommendations before coding starts;
and it corrects the plan doc in place when falsification or repartitioning moves it (`plan-docs`
owns rewrite-in-place, never append).

Its **context is the scarce resource**, and tracker API payloads drain it fastest. One run spent a
fifth of this actor's window absorbing Jira responses — sixteen `transitionJiraIssue` calls at
~5,700 characters each to change one status field. Deciding a ticket's status is this actor's job;
absorbing the payload is not, and the two get conflated because each call looks individually cheap.

- **Past about three tracker calls, hand a decided table down** — ticket → transition, comment,
  labels — to one sub-agent that executes the batch and reports one line per ticket.
- **A finding a sub-agent surfaces as deliberately not actioned gets its own dispatch.** One such
  gap drew fifteen tool calls of write-code, run-tests, debug and commit from this actor's own
  hands, on a run where a sibling batch of five comparable fixes was correctly dispatched.

Reading this file, cross-session peer messages, the briefs it writes and the ledger it keeps are the
job rather than overhead to trim — the ledger in particular is a small cost here that keeps every
sub-agent's context small.

**Run `ListAgents` at dispatch time**, not when something looks wrong. Unrelated commits describing
a batch that resembles this run are a routine sight, and one call settles whether a second
orchestrator is live before it becomes an alarm.

## Run artifacts this actor owns

Prose in a per-run directory, fixed fields in one ledger. Both paths derive from the ticket, so any
actor — including a restarted one — resolves them without being told, and both go down in every
brief as absolute paths (`brief-contract.md`).

```
~/.claude/plan-rollout-runs/
  rollout.db                   the ledger: every run's rows, each carrying a `run` column
  <ticket>/                    this run's prose, outliving the session
    review-recommendations.md  seeded by this actor before coding starts
    review-<pr>.md             one per PR
    inventory-<aspect>.md      the changes inventory a second-level coordinator writes
    briefs/<agent>.md          every brief
    reports/<agent>.md         every full report
    audits/<agent>.md          every auditor verdict
    ledger.md                  `rollout-db dump <ticket>`, written at close-out for the human
```

The ledger outlives every run — its `traps` rows brief the next one. So does the skill-efficacy log,
`~/.claude/skill-efficacy/<ticket>-<date>.md`; create that directory, it does not exist yet.

Review recommendations and the per-PR review file are `second-level-coordinator.md`'s content: this
actor seeds the first and creates the directory they live in, but what goes in either belongs there.

**The ledger is the only home for fixed-field, multi-writer data** — the run, the partition, agents,
report headers, notes, traps, tickets, decisions, audits — and
`~/.claude/skills/plan-rollout/scripts/rollout-db` is the only way in (`SKILL.md` carries why).

**Notes** — things that must reach the user without stopping the run: work an agent skipped, a red
check that does not reproduce on the base ref, significant-but-unrelated findings that became
tickets only, a brief or plan statement that turned out wrong, a tooling or environment failure, and
any operational unit waiting on the closing PR. Whoever observes one writes the row (`note add
--kind left_undone | skipped | red_not_on_base | unrelated_ticket | hook_warning | brief_error |
plan_error | incident | other`); this actor reads them once, at close-out. `needs_human()` stops the
run now; a note is read at the end. One condition is never both.

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
  closing PR body as an ordered runbook, and into a `notes` row. A PR unit that depends on one is a
  plan defect — `partition()` rejects it and this actor corrects the plan in place rather than
  scheduling the impossible.

## What the human reviews

Every inner PR is reviewed and merged by agents. The human's surface at close-out is exactly three
things: the closing base → trunk PR, whose body lists every inner PR with its ticket and round
count and carries the run's notes in full; the per-PR review files, linked or collapsed into that PR
body; and any escalation PR, left open and explicitly marked not for merging. The inner PRs stay in
history for anyone who wants the raw diff, but the human's own reading is converged agent review, not
diff-by-diff.

## The loop

Falsify the plan against the live repo before any dispatch — every claim left unchecked is one N
agents will implement faithfully, because their brief *is* the plan.

```
coordinate_plan(plan):
    # Never implements a ticket. Docs, tickets, minor fixes only — this actor's own scope.

    db       = "~/.claude/skills/plan-rollout/scripts/rollout-db"   # the only way into the ledger
    run_dir  = "~/.claude/plan-rollout-runs/<ticket>"               # this run's prose; create it
    efficacy_log = "~/.claude/skill-efficacy/<ticket>-<date>.md"    # the skill-efficacy log

    state = `db state <ticket>`       # exits non-zero on a ticket it has never seen: a fresh run
    if that call exited 0:            # resume entry, below
        base    = `db query "SELECT base_branch FROM runs WHERE ticket = '<ticket>'"`
        aspects = state.units                      # the work list, not just a wave number
        reconcile_ledger_with_git(state)           # resume entry, below — BEFORE any dispatch
        resume_wave = lowest unit.wave WHERE unit.status != done
    else:
        base = given_base_branch(plan) OR cut_branch(from = real_trunk, name = plan.ticket)
        `db init <ticket> --plan <plan.path> --base <base> --sha <base_sha>`

        ensure_jira_tree(plan)     # dispatch(model = "sonnet"): epic + stories + tasks
                                   # (tracker-shape rules are second-level-coordinator.md's). It
                                   # diffs the plan against the tickets that exist, and reconciles
                                   # the plan against itself — the ticket list is not the work
                                   # list, and a plan's own count table and wave list can drift
                                   # apart from each other. It returns the KEYS; the Jira tool
                                   # output stays in the sub-agent.

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
                correct_in_place(plan, claim)      # rewrite the section, never append —
                                                    # plan-docs owns this
                if contradicts_the_plan_premise(claim): AWAIT_DECISION(claim)

        aspects = partition(plan)      # yields PR units AND operational units, above
        # partition() criteria, in priority order:
        #   1. small PRs                     (goal 1)
        #   2. a clear testable seam per PR  (goal 2) — the mattpocock-skills:tdd boundary. A design that
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

        for unit IN aspects:
            `db unit upsert <unit> --run <ticket> --aspect <a> --wave <n>
                            --kind <pr|operational> --depends-on <json> --status pending
                            --ticket <key>`        # the partition IS the resume record: write it
                                                    # the moment partition() returns
        seed_review_recommendations(run_dir, aspects)   # review recommendations —
                                                          # second-level-coordinator.md
        resume_wave = the first wave

    for wave IN dependency_waves(aspects) FROM resume_wave:

        # A branch-runnable operational unit blocks its wave — only a human can perform
        # it (branch-runnable, above).
        for unit IN wave WHERE unit.is_operational:
            `db decision add --run <ticket> --reason <unit.runbook_step>
                             --options '["it ran","skip it"]' --decided-by user`   # open from
                                                    # here, so a restart re-asks rather than
                                                    # assumes
            answer = AWAIT_DECISION(unit.runbook_step, ["it ran", "skip it"])   # needs_human()
            `db decision resolve --run <ticket> --reason <unit.runbook_step> --answer <answer>
                                 --decided-by user`  # closes the row `state` was reporting open
            set_ticket_status(unit.ticket)
            `db unit upsert <unit> --run <ticket> --status done`

        pending = []
        for aspect IN wave WHERE NOT aspect.is_operational:
            agent = "plan-rollout-slc-<aspect>"    # named at dispatch, so siblings can message it
            `db agent upsert <agent> --run <ticket> --role slc --aspect <aspect>
                             --branch <aspect_base> --base-sha <sha> --worktree <path>
                             --status dispatched --brief-path <run_dir>/briefs/<agent>.md`
            # upsert BEFORE dispatch: `rollout-db report` resolves the run from this row and
            # exits 1 on a name it has never seen.
            # run `brief-contract.md`'s pre-dispatch gate on brief_for()'s output before sending it
            pending.append(
                dispatch(role  = SECOND_LEVEL_COORDINATOR,
                         agent = "plan-rollout-slc",   # the definition; it preloads the reference
                         model = "opus",      # explicit — a fork would inherit this
                                              # agent's model instead
                         base  = cut_branch(from = base, name = aspect.name),
                         brief = brief_for(aspect, run_dir, db, efficacy_log)))  # brief-contract.md

        # Handle each report as it ARRIVES. Do not wait for the wave to drain —
        # an early finisher must not idle behind a slow sibling. Goal 5.
        while pending NOT empty:
            header = await_next(pending)        # the ROUTING HEADER only — brief-contract.md.
                                                 # The report file stays on disk unless a count
                                                 # sends this actor to it.
            unit = the aspect this agent was dispatched for   # its `agents` row carries it
            `db agent upsert <header.agent> --run <ticket> --status <header.status>
                             --head-sha <header.head_sha> --report-path <header.report_file>`

            # base_at_dispatch is the child's answer against the --base-sha recorded when this
            # actor upserted it. A mismatch means every SHA in the report is measured from a base
            # nobody dispatched, so it becomes the claim to re-verify below.
            if header.base_at_dispatch != agent_row.base_sha:
                `db note add --run <ticket> --agent <header.agent> --kind other
                             --text "reported base <x> against dispatched <y>"`

            # files_written names the artifacts that actually landed. Check the ones a later brief
            # will point an agent at — inventory-<aspect>.md, the review recommendations. A brief
            # naming a file nobody wrote buys a confident review of nothing.
            if the next brief's artifacts NOT IN header.files_written:
                re-dispatch for the missing artifact before briefing anyone against it

            verdict = await(dispatch(role = AUDITOR, agent = "plan-rollout-auditor",
                                     model = "sonnet", fresh = TRUE,
                                     brief = [header.report_file, brief_path, plan.path, origin]))
            reverify_one_claim(verdict)         # one command, this actor's own hands — evidence,
            act_on(verdict.discrepancies)       # below. A clean verdict needs nothing else.
            check_brief_compliance(header.empty_sections, verdict)   # an unfilled contract field
                                                 # is visible without opening the report

            if header.status == blocked:
                # A child hit a needs_human() condition. Surface it, then resume the child.
                # `blocked_on` carries the decision AND the options it saw.
                `db decision add --run <ticket> --reason <header.blocked_on>
                                 --options <options> --decided-by user`
                answer = AWAIT_DECISION(header.blocked_on, options)
                `db decision resolve --run <ticket> --reason <header.blocked_on>
                                     --answer <answer> --decided-by user`
                resume(header.agent, answer); pending.append(header.agent)
                continue

            # left_undone, skipped, red_not_on_base, unrelated tickets: the header carries the
            # COUNTS and the `notes` table already carries the text, written by whoever observed
            # it. `ledger_rows` is the cross-check — a non-zero count beside `notes +0` means the
            # text never reached the ledger and close-out would report nothing. Read the rows
            # themselves once, at close-out.

            if header.plan_errors:      # the child found the PLAN wrong, not its own work
                correct_in_place(plan, `## plan_errors` IN header.report_file)   # this actor
                                         # owns the plan; plan-docs owns rewrite-in-place
            if header.brief_errors:     # the brief was wrong, so the next one would be too
                amend brief_for() before this wave dispatches anything else

            # Carry the wave forward. Checked on EVERY report, deviations or not: a PR can
            # follow its plan exactly, report nothing, and still move a signature its
            # children consume. The changes inventory catches that; a deviation list cannot.
            if affects_later_waves(verdict.blast_radius, header.shared_contract_changes):
                repartition_remaining(aspects)              # the next wave's brief_for() now
                reconcile_jira_tree(plan)                   # dispatch(model = "sonnet"): reads
                                                             # the corrected plan, returns keys
                for unit IN aspects WHERE unit moved:
                    `db unit upsert <unit> --run <ticket> --wave <n> --depends-on <json>`

            merge_into(base, header.branch)                # dispatched to Sonnet — never this
                                                             # actor's own hands — merge readiness, below
            if conflict_between_aspect_base_branches:
                AWAIT_DECISION(conflict)                   # needs_human()
            cleanup(header.branch)                         # dispatched to the same sub-agent — SKILL.md
            `db unit upsert <unit> --run <ticket> --status done`   # keeps resume_wave true,
                                                                    # which is what resume reads
            `db agent upsert <header.agent> --run <ticket> --status done`

    # Close out — what the human reviews, above. ONE read of the ledger's prose.
    trunk_dependent = [u for u IN aspects WHERE u.is_operational AND u.trunk_dependent]
    notes   = `db query "SELECT agent, kind, text FROM notes WHERE run = '<ticket>'"`
    tickets = `db query "SELECT key, title, in_epic, reason FROM tickets WHERE run = '<ticket>'"`
    `db dump <ticket>` > run_dir + "/ledger.md"    # the human's copy of the whole run

    # Author the two review plans for the pass that comes AFTER this run.
    # dual-scoped-review-plans owns the rules. Skipped when the repo carries no
    # AGENTS*.md and no CLAUDE.md — that skill's step 0 exits, no second source.
    review_plan_paths = []
    if repo_has_standards_docs():
        review_plan_paths = [
            await(dispatch(role = PLAN_AUTHOR, fresh = TRUE,      # NEVER fork — a fork
                           scope = run_artifacts(run_dir),        # inherits BOTH scopes
                           excluded = [repo_standards_docs, the_sibling_plan])),
            await(dispatch(role = PLAN_AUTHOR, fresh = TRUE,
                           scope = repo_standards_docs,
                           excluded = [run_dir, the_ledger, the_sibling_plan]))]
                           # gets the diff and the ticket. NO run artifact, ever
        # Each returns a PATH under plan/. This actor does NOT read either one:
        # no Read, no cat/grep/sed, no subshell. Staying scope-clean is what
        # disqualifies it from synthesising, and that is deliberate.

    # This run never RUNS either pass, and never compares the two.

    # No PR inside the stack got CI, so nothing has yet run the gates over the
    # whole aspect. Run them on the merged base BEFORE the closing PR opens --
    # see "No CI inside the stack, before the closing PR".
    gates = await(dispatch(role = VERIFY, model = "sonnet", brief = [base, full_gate_commands]))
    if gates.failed: AWAIT_DECISION()

    pr_url = await(dispatch(role = PR_BODY, model = "sonnet", fresh = TRUE,
                            brief = [base, real_trunk, inner_prs_with_tickets_and_round_counts,
                                     notes, tickets, runbook(trunk_dependent),
                                     review_plan_paths]))    # PATHS, never plan content
             # It assembles the body, calls open_pr(base, into = real_trunk, body = ...), and
             # returns the URL. Its brief forbids merge_pr: the human merges base -> trunk.
    present_to_user(pr_url, notes, efficacy_log, review_plan_paths)
    return pr_url
```

## The two review plans, at close-out

The run authors them and stops. **It never runs either pass** — the same agents just built the code,
and each PR already had its review rounds. These plans exist for a fresh pass a human decides
whether to spend, once the closing PR is merged.

Two dispatches, and the whole value is that their scope sources are disjoint: one scopes from what
this run accumulated (the review recommendations, the per-PR review files, the ledger's notes, the
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
agent-facing document per `mattpocock-skills:writing-for-agents`, with completion criteria a reviewer can fail, and it
carries its own scope statement and exclusion list in the file — the session that eventually runs
the pass may never see the brief that produced the plan.

`dual-scoped-review-plans` owns the exclusion lists, the read-back each author reports, the no-fork
rule, and the synthesis rules. It also owns the exit: a repo with no `AGENTS*.md` and no `CLAUDE.md`
has no second scope source, so this step is skipped and the run says so in a `notes` row.

## Resuming, at `rollout-db state`

Every write lands in the ledger before the next step starts, so a compacted, restarted, or crashed
coordinator re-enters `coordinate_plan()` at the top and loses nothing: `state <ticket>` returns the
units, the agents, and every decision still open. Falsification and `partition()` do not re-run — the
`units` rows are the work list. **The wave to continue from is derived from those rows: the lowest
`wave` whose units are not all `done`.** Each open decision goes back to the user; `decision resolve`
closes one as it is answered, so an answered decision never comes back.

**The ledger records what an agent reported; the branch records what it did.** Before dispatching
anything on resume, cross-check the two for every agent whose status is not `done`:

| Check | A mismatch means |
|---|---|
| `agent.head_sha` against `git rev-parse origin/<agent.branch>` | It committed past its last report, or never pushed |
| `git status` in `agent.worktree` | Uncommitted work no report mentions |

A mismatch is a `note add --kind other` row, and that agent is resumed or re-briefed **from what the
branch actually holds**. Briefing from the stale row instead redoes landed work, or skips work that
never landed.

## Evidence, at each report

The routing header carries counts; the report file carries the claims behind them. A **Sonnet
auditor** checks those claims, one dispatch per report, and `references/auditor.md` is the file it
reads — this actor never opens it. Inputs: the brief path, the report path, the plan path, and
`origin`. It resolves SHAs, re-runs counted commands, confirms the discriminating test ran, checks
the verification command's scope claim, and compares `inventory-<aspect>.md` against the plan
sections still outstanding. It writes `audits/<agent>.md` and returns at most ten lines:

```
evidence: clean | <n> discrepancies
blast_radius: none | sections [...]
```

An auditor that returns no verdict hit its turn budget rather than failing. Its audit file is on
disk and partly filled: read it, treat every `NOT CHECKED` heading as unchecked rather than clean,
and resume that auditor on the headings it did not reach instead of dispatching a fresh one.

**Resolve unit and branch names from the ledger, never from the run's branch prefix.** This actor
names base branches after the run and PR branches after the work, so `git branch -r | grep <ticket>`
cannot return a PR branch under any circumstances, and its silence carries no information at all.
`rollout-db query "SELECT unit FROM units WHERE run = '<ticket>'"` is the record.
`claims-and-scope-discipline` holds the general form: before offering a command as evidence, ask
what it would print if the claim were false.

Then this actor **re-verifies exactly one claim with its own hands** — one command — and acts only
on discrepancies. One check catches an auditor that rubber-stamped; a second is this actor re-reading
the report it just paid not to read.

## Carrying the wave forward, at `affects_later_waves`

The predicate is true when **either** a reported deviation **or** an entry in the report's change
inventory touches a descendant's plan section, or a contract two PRs share — a signature, a schema,
an event name, a status vocabulary.

**The inventory is the half that matters, and the reason this runs on every report.** A sub-agent
reports a deviation when it knowingly departed from its plan section. It reports nothing when it
implemented that section faithfully and the section itself moved a shared signature — from its own
seat that is not a deviation, it is the job. The changes inventory is what surfaces it, which is why
`brief-contract.md` demands the inventory rather than trusting a deviation list to carry the case.

The auditor answers that half in one line. Its `blast_radius` is `inventory-<aspect>.md` compared
against the plan sections still outstanding, so this actor decides from the verdict rather than from
the inventory file. The header's `shared_contract_changes` count is the cross-check: a non-zero count
against a `blast_radius: none` verdict is a discrepancy, and the one claim worth re-verifying.

Repartitioning here is cheap and silent; discovering it after the next wave has built on a stale
contract is neither. When it fires, the next wave's `brief_for()` reads the corrected plan, so a
descendant never inherits the stale version, and `unit upsert` rewrites the moved rows so a resumed
coordinator reads the new partition rather than the old one.

## Merge readiness, at `merge_into`

GitHub's `mergeable` field evaluates a PR against its base independently, so two sibling aspect base
branches can each report green and still conflict with each other — whichever merges second breaks.
The check that holds is **performing an actual merge in a throwaway worktree**.

**This actor is a coordinator, never an implementer: every repo-mutating step here is a dispatch,
never this actor's own hands.** `merge_into` is one dispatch to Sonnet, not a call this actor runs
itself. The sub-agent creates the throwaway worktree, performs the actual merge, builds
`claims-and-scope-discipline` §9's integration-merge digest for that branch, and — when the merge is
clean — pushes it and reports a conflict yes/no plus the digest path; the merge output itself never
enters this context. A real conflict there, not a red `mergeable`, is the `needs_human()` signal.
The digest is built as each aspect base branch lands, not after all of them have. The same dispatch
also performs `cleanup(header.branch)` — the branch delete and worktree removal — once the merge has
landed; this actor never runs a git mutation (merge, push, branch create or delete, worktree add or
remove) inline.

## No CI inside the stack, before the closing PR

Read the repo's `pull_request:` trigger list before writing a word about CI into a brief. Where it
names `branches: [main, staging, alloy-db]`, every PR this run opens targets an aspect base or the
run base, so each one gets **zero checks**, and the closing base → trunk PR is the only one CI ever
sees.

**Zero checks renders identically to green.** Nothing shows red, no missing-check warning appears,
and the PR lists as ordinary:

```
gh pr view 973 --json statusCheckRollup,mergedAt \
    --jq '{merged:.mergedAt, checks:(.statusCheckRollup|length)}'
{"checks":0,"merged":"2026-09-15T00:04:39Z"}
```

Read the **count**, never the colour, and state a PR's status as that count plus its base branch.
Two consequences bind this actor:

- **"CI runs the full suite on the PR" stays out of every brief** as a reason to select tests
  narrowly. Inside the stack an agent's own selection is the entire gate, which is what makes
  `brief-contract.md`'s symbol-grep selection load-bearing rather than tidy.
- **Run the full verification on the merged base before opening the closing PR** — as a dispatch,
  like every other repo-touching step. Otherwise the first validation of a whole aspect happens
  after every internal merge has landed, where a failure has nowhere cheap to go.

Where the human directs small fixes straight to the integration branch with no PR, treat it as a
**scope test rather than a standing process change**. A one-line change inside one function is
fine. A shape change across call sites has just lost its only gate: say so, and ask. One such batch
held five one-liners and one three-call-site shape change, and the shape change broke a test on the
integration branch.

## A dispatched second-level coordinator can die mid-run

A dropped connection, a stall, a terminal API error, between one `await_next(pending)` and the next.
A watchdog turn-limit stop is not one of these, and neither is a session rate limit (HTTP 429) —
both hit routinely on work of this size, and the agent and its worktree survive them. Assess the
tree, then resume with `SendMessage`; `brief-contract.md`'s "A resume brief adds" states what that
message may assert and what it has to ask. Re-dispatching fresh discards the worktree and every
file the agent had already read, so reserve the three outcomes below for an agent that is actually
gone. Its `agents` row names the branch and the worktree; the branch, not the
row, says what landed. Check what its aspect base branch actually holds — three outcomes:

- **Clean** — nothing landed since the last merge. Relaunch the same brief.
- **A coherent partial** — a PR merged into the aspect base, or a helper written but not yet wired
  up. Keep it; re-dispatch to finish from there rather than restart.
- **A broken partial** — revert it rather than patch around it.

After two failures on the same aspect, stop re-dispatching a fresh coordinator against the whole
aspect: narrow the brief to only the unit still outstanding, or `AWAIT_DECISION` if narrowing does
not converge either. This actor never implements the fix itself — dispatch remains the only path.

## Cross-references this file does not restate

`needs_human()`, `AWAIT_DECISION()`, and `cut_branch()` are defined once, in `SKILL.md`, which also
states the run directory, the ledger, and the routing header; call them by name. Git and worktree
mechanics belong to `git-worktree-topology`, and `references/auditor.md` belongs to the auditor.

**When no ratified plan exists yet, call `plan-and-review`, consume what it returns, and continue
here.** It gives back the plan path, the ticket key, and the partition. Control comes back to this
actor, which is why `plan-and-review` returns rather than calling this skill: entering it and
letting it re-enter here would restart the run from the top. Both skills state this rule at their
own side of the seam, because no description can carry which end the run started from. When it
reports the work needs no plan at all, that is a one-PR, one-aspect partition — it still gets a
second-level coordinator, so this actor never implements it directly.
