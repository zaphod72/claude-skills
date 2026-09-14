# Coding sub-agent

You build one PR. Your coordinator dispatched you with a worktree, a base branch already pushed to
`origin`, and a brief. `SKILL.md` holds `AWAIT_DECISION()`, the predicates, and the rules that apply
to you; this file adds only the execution detail specific to this actor.

## Scope

You work at PR level (or a slice branch cut from the PR branch, if your coordinator judged two
agents could build one PR without colliding — `SKILL.md`'s "one branch, one worktree" rule still
applies to you). PR-level work is a collision-avoidance choice, not a hard rule: several coding
agents on one plan must not overwrite each other's edits, and one branch per agent is what makes
that true.

You may dispatch coding sub-agents of your own to keep your own context small — goal 3. The cap in
this skill is on *coordinator* levels, not on agent depth: a sub-agent you dispatch is still a
coding agent underneath you, not a third coordinator.

If a unit of work would touch a file outside your assigned scope, do not widen your scope on your
own judgment and proceed. Call `AWAIT_DECISION()` and wait — your coordinator resumes you once it
has a decision.

## Building the PR

```
implement(unit_of_work, pr_branch, worktree):
    if worktree is NEW:
        worktree = create_worktree(isolation = "worktree")
    in worktree:                                    # step 0, before any read — name the base explicitly
        fetch(origin, pr_branch)
        checkout -B pr_branch origin/pr_branch       # never inherit the base implicitly
        assert rev-parse HEAD == origin/pr_branch

    for unit IN unit_of_work.units:
        loop:                                        # mattpocock-skills:tdd red-green-refactor, one slice at a time
            if out_of_scope(self, files_i_must_touch(unit)):
                decision = AWAIT_DECISION(files, ["widen my scope", "leave it"])  # out-of-scope escalation
                apply(decision)

            write_failing_test(unit)
            implement_until_green(unit)               # test freely here — format before the final test run
                                                        # governs only the last run, below
            refactor(unit)
            if unit is done: break

        loop:                                         # the final gate — format before the final test run
            run(every_step_that_can_modify_a_file)     # format, imports, lint --fix, types
                                                        # scoped to MY files, never repo-wide
            run(tests_selected_from_diff)              # last, so formatting cannot force a redo
            if all passed: break
            fix_failures()

        commit(unit, by_explicit_path)                 # incrementally, before reporting.
                                                        # never `git add -A`, never stash
    push(pr_branch)
    assert rev-parse(f"origin/{pr_branch}") is not None   # read `## head_sha` back from origin
                                                        # after this push, never from local HEAD —
                                                        # a SHA that never reached origin merges nothing

    # never writes the plan doc — deviations go upward as data
    for item IN my_notes + my_traps + my_tickets:      # ledger rows BEFORE the report — `report`
        rollout_db(item)                                # counts rows that already exist
    write_report_file(my_report_path)                  # <run dir>/reports/<name>.md, named in my
                                                        # brief; all 25 `##` headings present
    header = rollout_db("report", self.name, file = my_report_path)   # parses, writes the row, prints
    return report_upward(header)                       # return the printed header, nothing else
```

## Step 0: never inherit a base implicitly

A worktree dispatch has been observed cutting from the repo's default branch instead of the
session's. Step 0 makes that irrelevant: `fetch` and `checkout -B` the named base explicitly before
reading anything, and assert `rev-parse HEAD` equals `origin/<base>`. See `git-worktree-topology`
§2a for why this is a harness property to re-verify on the day, not a git guarantee to trust.

## Building test-first

Load the `mattpocock-skills:tdd` skill for red-green-refactor itself; here is only what a coding sub-agent adds to it.

Work in **vertical slices** — a slice is one small piece of behavior built and proven end to end,
rather than a horizontal block (all fixtures first, then all logic across them). Each slice earns
its own red test, and the red output is your evidence: a test never seen failing is evidence of
nothing.

Two execution modes exist, and your brief names which one a given slice gets:

- **New code: red-first.** Write the failing test, watch it fail, then implement until it passes.
- **Retrofitting tests onto code that already works: mutation with a control arm.** Red-first isn't
  available — the code already passes. Instead mutate the **seam** (the point in the code where a
  test can observe the behavior in question), watch the test go red against the mutation, revert
  the mutation, and watch it go green again. That reverted, unmutated run is the **control arm** —
  proof the test doesn't fail unconditionally.

Your brief names the seam. When the brief and the plan section together still leave it
undeterminable, stop and report `status: blocked` with the specific question, rather than guessing
one — a guessed seam is an unreviewed design decision, not yours to make silently.

`mattpocock-skills:tdd` is a default, not an absolute. Where it doesn't fit — no reachable seam, pure config,
generated output, Terraform or other declarative-infra changes whose own `plan`/`apply` cycle is
the verification loop — your brief says so, and says why. Follow that rather than forcing a loop
that buys nothing.

## The final gate

The **final gate** is the last file-modifying pass plus the test run that follows it, run once
before a unit's commit. `SKILL.md` states the ordering — every file-modifying step first, the test
run last, because formatting after a test run forces it to be repeated. What's specific to you:
scope every step to the files you touched, never repo-wide, and select the tests from your own
diff. Test as often as you like while a slice is still red-green-refactor; this ordering governs
only the last run before a commit.

Its exit code only says the command returned, not what it covered — `brief-contract.md`'s "Exit
code is never the check" is what you report against.

## Committing and reporting

Commit incrementally, by explicit file path, before you report. Never `git add -A`; never
`git stash` — see `git-worktree-topology` §2b: the stash is repository-wide, and a shared one
silently swaps another worktree's uncommitted work into yours.

You never write the plan doc; that's a coordinator's job. Report your deviations upward as data.

Reporting is four steps, in this order. `brief-contract.md` owns the 25 `##` headings and what each
one carries; what matters here is the order, because three of the four steps fail quietly out of it:

1. Write your `note add`, `trap add`, and `ticket add` rows with
   `~/.claude/skills/plan-rollout/scripts/rollout-db`. `report` counts rows that already exist, so a
   row added after it is invisible to your coordinator. Any ticket you file for a pre-existing or
   out-of-scope finding gets exactly one triage label at creation — `ready-for-agent` when it is
   fully specified, otherwise `ready-for-human` — plus the labels `common-facts.md` names; never
   leave it unlabelled or on `needs-triage`.
2. Write the full report to the path your brief names,
   `~/.claude/plan-rollout-runs/<ticket>/reports/<your-name>.md`, every heading present. A missing
   heading is a parse error that writes no row at all.
3. Run `rollout-db report <your-name> --file <that path>`.
4. Return exactly what it printed — the routing header, at most 30 lines. That header is what your
   coordinator routes on; the report file carries everything else.

Report anything that turns out to be wrong under `## brief_errors`, including anything your own
brief asserted, and anything the plan got wrong under `## plan_errors`. Refusing a wrong
instruction beats implementing it.
