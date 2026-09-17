# The brief contract

Neither a rule (always loaded) nor a skill (invoked on demand): the **brief contract** is a
required section of every dispatch prompt — what a parent puts in a child's prompt, and what the
child must send back.

**Pairing is the whole mechanism, and it is why this file exists.** Every downward requirement
below has an upward field that would expose its omission. A run whose briefs required
`mattpocock-skills:tdd` in prose alone got agents that quietly skipped it, because nothing in the report would have revealed
the skip — an unpaired requirement drifts silently, and a more emphatic sentence fails the same
way. State the requirement and its paired field together, or don't bother stating it.

Every upward field is a fixed `##` heading in the agent's report file, and the routing header's
`empty_sections` line names every heading whose body came back blank. That line is what makes an
omission visible to a parent that never reads the report.

Every `report_upward()`, `brief_for(...)`, `brief_for_review(...)`, `brief_for_fix(...)`, and
`resume(...)` called in `top-level-coordinator.md`, `second-level-coordinator.md`, and
`coding-agent.md`'s pseudo-code means the tables below — they do not restate the fields, and neither should you when writing an
actual brief. Call `AWAIT_DECISION()`, `needs_human()`, `is_cosmetic()`, and `is_trivial()` by name;
their bodies live in `SKILL.md` and nowhere else.

## Two tiers: the report file and the routing header

The ledger script is `~/.claude/skills/plan-rollout/scripts/rollout-db`, and it is the only write
interface to the run's data. `--db <path>` is a global flag placed **before** the subcommand;
without it the script reads `ROLLOUT_DB_PATH`, then defaults to
`~/.claude/plan-rollout-runs/rollout.db`.

A dispatching coordinator writes the agent's row at dispatch:

```
rollout-db agent upsert <name> --run <ticket> --role <r> --parent <p> --aspect <a> --pr <n> \
    --branch <b> --base-sha <s> --worktree <path> --status dispatched --brief-path <p>
```

A dispatched agent reports in four steps, in this order:

1. Write its ledger rows — `note add`, `trap add`, `ticket add` — one call per item. `report`
   counts rows that already exist; rows added afterwards are missing from the header its parent
   reads.
2. Write `~/.claude/plan-rollout-runs/<ticket>/reports/<agent>.md`, every `##` heading below
   present, in this order.
3. Run `rollout-db report <name> --file <path>`.
4. Return **only** what that command printed.

`report` takes no `--run`: it resolves the run from the agent's own row, so `agent upsert` for that
exact name has to have run first. On an unknown name it exits 1 with
`no agent row found for '<name>'; run 'agent upsert' first`.

## Report file sections

Fixed strings, this order. A missing heading is a hard parse error naming every heading missing,
and no row is written. A body that is empty or exactly `none` counts as empty, and that heading's
name lands in `empty_sections`.

| `##` heading | Carries | Paired downward requirement |
|---|---|---|
| `## status` | `done` \| `blocked` \| `partial` | Call `AWAIT_DECISION()` for a decision you cannot make |
| `## agent` | The dispatch name, matching the `agent upsert` row | The name this dispatch is given |
| `## branch` | Branch name, resolved against `origin` | Your base branch, already pushed |
| `## head_sha` | Short SHA at `origin` after your last push | Commit and push incrementally, and before reporting |
| `## base_at_dispatch` | The base SHA the brief recorded, checked against `origin` rather than quoted back | The base SHA recorded at dispatch |
| `## worktree` | Absolute path, and whether you created it or were handed it | The worktree path, created at the named base |
| `## blocked_on` | The decision needed, and the options you see | `AWAIT_DECISION()`; a review agent's BLOCKED verdict lands here, with `status: blocked` |
| `## shared_contract_changes` | Bullets, one per contract a sibling aspect can see: `signature:`, `schema:`, `event:`, `status vocab:`, `config key:` | Name what you changed that a sibling aspect builds against |
| `## changes_inventory` | Every file, symbol, signature, schema, or config key touched and what changed about it, with no judgment about other PRs | Ask for the changes inventory |
| `## deviations` | Bullets: what you chose to do differently, as deviations rather than narrative | Report deviations as deviations |
| `## plan_errors` | Bullets: where the plan was simply wrong, each also a `note add --kind plan_error` row | Report plan errors separately from deviations |
| `## brief_errors` | Bullets: which brief statements turned out wrong, and the correction, each also a `note add --kind brief_error` row | "Report anything here that turns out to be wrong, including anything I have told you" |
| `## left_undone` | Bullets, each also a `note add --kind left_undone` row | Say what you could not finish |
| `## skipped` | Bullets, each also a `note add --kind skipped` row | Name any work the plan called for that you skipped |
| `## red_not_on_base` | `yes` \| `no` — does the same failure reproduce on the base ref; plus a `note add --kind red_not_on_base` row | If checks are red, commit and report anyway rather than stopping — the PR is a draft either way |
| `## tickets` | Bullets, key, one line, and its labels, each also a `ticket add` row | Record tracker changes; every ticket carries exactly one triage label at creation — `ready-for-agent` when it is fully specified (file:line evidence, a stated fix, an acceptance check), otherwise `ready-for-human` — plus the labels `common-facts.md` names |
| `## traps` | Bullets, each also a `trap add --repo <r> --path <p>` row: what bit you, where, and what it costs the next agent | Report any new trap you hit |
| `## tdd_mode_and_seam` | The mode — red-first, mutation-with-a-control-arm, or the brief's no-`mattpocock-skills:tdd` call still holding — and the seam the tests sit at | Which `mattpocock-skills:tdd` mode this slice gets, and the seam |
| `## skills_used` | Which skills you used, and which of them helped | Use `mattpocock-skills:tdd` unless told otherwise; say which skills helped |
| `## verification` | Each verification command, **what it covers** as you read it from the task or script definition, and its result; whether a long suite ran inline or was backgrounded, and its result once it lands | What the verification command actually covers |
| `## evidence` | Commands with raw output and counts; what you verified versus inferred; the discriminating test's result; every target number reproduced or flagged; your commit SHAs, plural | Show your work |
| `## runtime_only_concerns` | Per entry: what needs a live run to confirm, and the log line added to catch it, or why none was | Ask what can only be confirmed once the code runs |
| `## deploy_ordering` | Whether anything has to happen in a particular order at deploy time — required even when the answer is "no" | Ask about deploy-time ordering |
| `## files_written` | Bullets: the artifact files you wrote, by name | The run directory, as an absolute path |
| `## review_notes` | For a review or fix agent: rounds read by number and where you appended, recommendations relied on, declared gaps checked, the fix-round summary | Record how the review went |

Nine sections are bullet-counted — `shared_contract_changes`, `deviations`, `plan_errors`,
`brief_errors`, `left_undone`, `skipped`, `tickets`, `traps`, `files_written` — and the count in the
header is the number of top-level `- ` bullets.

## The routing header

`rollout-db report` prints this, at most 30 lines, and it is the whole of what the agent returns
inline. Eleven lines for a fully populated report:

```
status: done
agent: slc-a1  branch: feat/a1  head: deadbee  base_at_dispatch: abc123
report_file: /abs/path/to/report.md
shared_contract_changes: 2
  - signature: foo(x)
  - schema: bar
deviations: 1  plan_errors: 1  brief_errors: 0
left_undone: 0  skipped: 0  red_not_on_base: no
tickets: none
ledger_rows: notes +0, traps +0, tickets +0   files_written: review-recommendations.md, inventory-a1.md
empty_sections: ["blocked_on", "brief_errors", "left_undone", "skipped", "runtime_only_concerns"]
```

The `blocked_on` line prints only when `status` is `blocked`. `ledger_rows` is counted from the
database and `tickets` is read from the `tickets` table, so a ticket named in `## tickets` and never
added with `ticket add` prints as `tickets: none`. `files_written` is parsed from the
`## files_written` section.

**Read `empty_sections`, `plan_errors`, and `left_undone` first.** A report that omits "I could not
do X" is the failure mode, and `empty_sections` is where the omission shows.

## Pre-dispatch gate

Four defects from one root cause: a brief that asserts something the dispatcher never verified.
Run this gate — the dispatcher's own hands, before sending any brief, not something a script
downstream can catch after the fact:

1. **No unresolved placeholders.** `grep -n '__[A-Z_]*__'` over the brief text returns nothing. A
   brief with a literal `__BASE_SHA__` still in it was sent and dispatched against nothing.
2. **Every unit named in the brief already exists in the ledger.** Resolve each one against
   `rollout-db state` or `rollout-db query` before the brief goes out — never invent a unit on the
   spot ("cut E2") because a name felt natural to write. A discovery outside the current partition
   becomes a labelled ticket (check for an existing duplicate first) and stays out of current scope;
   it is never an improvised in-run unit.
3. **A sentence asserting ledger state is written only after the dispatcher has made that state
   true.** "Your `agents` row exists already" is false, and misleads the child, unless
   `agent upsert` for that exact name already ran. Create or verify the row first, then write the
   sentence that assumes it.
4. **A claim about what a PR added or removed is never taken from one commit's diff.** Per-commit
   churn in a stacked pair is indistinguishable from a real deletion; `git diff <base> <head>` is
   the only thing that settles it. A brief written from `git show <one commit>` can assert a
   deletion that never happened.
5. **Every fact the brief states carries the command that produced it.** The verified-facts section
   is the most dangerous text in the run: the brief tells the agent not to re-derive it, so it is
   trusted by construction, and it is exactly where a dispatcher's unchecked inference lands wearing
   the voice of a measured fact. Write the command beside each fact. Where you reasoned a fact out
   rather than ran it, label it an inference and say the agent should check it. On one run a
   coordinator was wrong four times and a sub-agent caught every one — every error was an inference
   written as a verified fact.
6. **Suppression-class artifacts get a full re-read, not a partial one, at write time and at every
   design change.** Review recommendations, a "verified, do not re-derive" brief block, a changes
   inventory a later wave is briefed against — each exists to stop someone downstream from
   checking something. That function means a stale claim inside one is never caught by anything
   else further down the pipeline; only re-reading the whole artifact, every time the design under
   it changes, catches it.
7. **A heading inside a suppression artifact is scoped, never blanket.** A reader takes the heading
   as the instruction and will not read a qualifying body underneath it — so a heading that reads
   as "skip all of X" when the body means "skip X in this one case" gets treated as the broader,
   wrong claim.

`top-level-coordinator.md` and `second-level-coordinator.md` both point here at the moment they
describe writing or sending a brief, rather than restating these checks.

## Every brief

| Brief says (downward) | Report must carry (upward) |
|---|---|
| Use `mattpocock-skills:tdd` unless told otherwise | Which skills were used → `## skills_used` |
| Your assigned file scope; stop and report before leaving it | `## blocked_on`, if it fired, naming the files |
| Your base branch name, already pushed, and the base SHA recorded now, at dispatch | `## branch`, `## head_sha`, `## base_at_dispatch` — resolved against origin, checked against what was recorded at dispatch, not just quoted back |
| The worktree path you are to work in, created at the base branch named here | `## worktree`: the absolute path, and whether you created it or were handed one |
| Commit **and push** incrementally, and before reporting. Committing survives your own exit; pushing survives losing the machine's view of your work, which is what a rate limit takes | The SHAs, plural → `## evidence`, and `## head_sha` resolved at `origin` — the one field that exposes a commit which never left the worktree |
| The run directory `~/.claude/plan-rollout-runs/<ticket>/`, as an absolute path — never let the agent resolve a working directory itself; a sub-agent can land somewhere else with no error at all | `## files_written` |
| The facts you verified, each carrying the command that produced it, so the agent need not re-derive them; anything you reasoned out rather than ran, labelled an inference the agent should check | What you verified vs. inferred → `## evidence`; a fact that turns out wrong → `## brief_errors` |
| **Traps earlier agents hit**, not only interfaces they changed — a DDL splitter that breaks on a semicolon inside a prose comment, a join that silently returns zero rows unless a prefix is stripped, a duplicated block shadowing a live assignment. These cost the discovering agent real time and are invisible in a diff. `rollout-db traps --repo <name> [--path <glob>]` returns them across runs | `## traps`, in the same shape, plus a `trap add` row, so the next brief carries it |
| Show your work | `## evidence`: commands run, with raw output and counts |
| **What the verification command actually covers**, read from the task or script definition before the first brief. Nine agents once reported `check-types` clean as evidence their new test files were sound; that task ran the type checker over `src` trees only and had never looked at a test file — run by hand, one test tree held 20 errors. "Exit code is never the check" below generalizes this. **The inverse too: never infer *unrunnable* from a gate's flag.** `--integration` gates pytest collection, which is not the same constraint as needing a live database — one suite declined as needing infrastructure nobody had wanted only a Docker daemon, its fixture starting and destroying a `testcontainers` Postgres itself, and ran 156 tests in 30.74s. Read the fixture before concluding a suite cannot run here | `## verification`: the command's scope as the agent understands it, alongside its result; for a gate declined as unrunnable, what the fixture actually requires |
| The numbers you measured, as targets to reproduce. This is the **anti-gaming clause**: a stated number is a target the agent must reproduce, and if its own output differs that is a bug in its work, not a license to adjust the expectation | `## evidence`: the value you actually got, matched against the target or flagged as a discrepancy — never silently rewritten to agree |
| Name **the discriminating test** — the one test that fails if the design is wrong, called out explicitly so it can't be lost in a list of equals | `## evidence`: confirmation it ran, and its result — silence on this one test is a gap, not a pass |
| **The disagreement rule, wherever this PR makes a value deterministic:** for every value it pins, write a test in which the *other* source would give a different answer | Those tests, one per pinned value → `## evidence`. A fixture where both sources agree proves nothing about which one the code read — that is how a wrong-source bug survives a fully green suite |
| Ask for **the changes inventory** — a factual, per-item list of every file, symbol, signature, schema, or config key touched, and what changed about it, with no judgment about other PRs | `## changes_inventory`: raw material for blast radius, not an opinion about it |
| Name the **shared contract surfaces** this unit may move — signatures, schemas, events, status vocabulary, config keys — and who else builds against them | `## shared_contract_changes`, one bullet each, so the header carries the count and a sibling coordinator can be told directly |
| Which `mattpocock-skills:tdd` mode this slice gets — red-first, or mutation-with-a-control-arm — and the seam the tests sit at; where neither fits (no reachable seam, pure config, generated output, Terraform and other declarative-infra changes), say so and why. Mechanics for both modes live in `coding-agent.md` | `## tdd_mode_and_seam`: confirmation of the mode and the seam, or confirmation the brief's no-`mattpocock-skills:tdd` call still held |
| Report deviations as deviations, not as narrative | `## deviations` |
| Report where the plan was simply wrong, separately from what you chose to do differently | `## plan_errors`, distinct from deviations, plus a `note add --kind plan_error` row — ask for it explicitly or you will not get it |
| Ask: does this change require anything to happen in a particular order at deploy time? | `## deploy_ordering`: the answer, even when it is "no" |
| Ask what can only be confirmed once the code runs | `## runtime_only_concerns` — per entry, what needs a live run to confirm, and the log line added to catch it, or why none was. `plan-docs` owns the `## Runtime-only checks` table these feed |
| Say what you could not finish | `## left_undone`, and why, plus a `note add --kind left_undone` row |
| Name any work the plan called for that you skipped | `## skipped` plus a `note add --kind skipped` row — not a stop |
| If checks are red, commit and report anyway rather than stopping, and say whether the same failure reproduces on the base ref | `## red_not_on_base` plus a `note add --kind red_not_on_base` row — not a stop |
| If you need a decision you cannot make, call `AWAIT_DECISION()` | `## status: blocked` plus `## blocked_on`: the decision needed and the options you see |
| Where a known defect stands between you and the task, it is named here as a decision with options — never as a caution to watch for | `## deviations`: which option you chose, and why — a workaround picked under budget pressure stays visible instead of silent |
| Where your scope is one file, you may report which of your own tests went red. You may never report that a mutation reddens "only" those — cross-file kills are invisible from inside one file | `## evidence`: which of your own tests went red, scoped honestly. An unqualified "only" is a finding the parent checks against the cross-file pass in `review-efficacy-axis.md`, not a result it relays |
| Select the tests by grepping the **changed symbols** across the whole test tree — "Select tests by symbol, not by filename" below | `## verification`: the count of test files the grep selected, and why — an under-selection is invisible to a parent without it |
| Run that selected set first — it catches real failures in seconds — then background any long suite rather than blocking on it | `## verification`: whether the long suite ran inline or was backgrounded, and its result once it lands |
| Record how the review went | `## review_notes`, and how many rounds it took |
| Record tracker changes; every new ticket gets exactly one triage label at creation — `ready-for-agent` when fully specified, otherwise `ready-for-human` — plus the labels `common-facts.md` names; never leave a new ticket unlabelled or on `needs-triage` | `## tickets`, with keys and labels, each also a `ticket add` row |
| Say which skills helped and which did not | `## skills_used`: the skill-efficacy entries |
| "Report anything here that turns out to be wrong, including anything I have told you" | `## brief_errors`: which brief statements, if any, turned out wrong, and the correction, each also a `note add --kind brief_error` row — an empty list is a claim too, not a default |

## A review agent's brief adds

| Brief says (downward) | Report must carry (upward) |
|---|---|
| The absolute path of this PR's review file; read it before reviewing, append your findings to it as soon as you reach a verdict — before writing the report file, not after. A killed agent that had already appended is salvageable; one that had only written the report is not | `## review_notes`: which prior rounds it read, by number, and where it appended |
| The review recommendations for this aspect — code already reviewed and found correct, and the declared scope gaps for this PR (every "this PR deliberately does not…" decision, stated as what it is and why) | `## review_notes`: which recommendations it relied on to skip re-review, and which declared gaps it checked a finding against before raising it as a defect |
| From round 2 on, the two convergence-diagnosis questions — do the rounds so far share one missing concept, and was the ticket or plan ever detailed enough for the size of this change — asked of this same dispatch, never a second one, so the cap of three holds | A verdict of OPEN or BLOCKED beside the findings. BLOCKED sets `## status: blocked` and names the decision nobody made in `## blocked_on`, so the routing header carries it; OPEN reports `## status: done` and says plainly in `## review_notes` that these are ordinary bugs converging round by round |
| The agreed design, not just the ticket — including anything settled after the ticket was written | `## review_notes`: confirmation the design, not just the ticket, was what Spec was graded against |
| You are read-only in the PR worktree, and you never fix a finding — not even a trivial one; fixes are a separate dispatch, so the same eyes that found a defect don't grade their own fix | Confirmation in `## review_notes`, and the SHA reviewed in `## head_sha` |

Every scope gap and every skip permission stated in `review-recommendations.md` carries the
command that would falsify it — not every sentence in the document, only these two claim types.
A scope gap or a skip permission *removes* scrutiny from something a reviewer would otherwise
check, so an agent trusting it needs a way to check the claim itself; a claim that merely
directs attention toward something carries no such risk and needs no falsifying command.

## A fix agent's brief adds

| Brief says (downward) | Report must carry (upward) |
|---|---|
| The review file path | `## review_notes`: confirmation it was read, and the round number this fix responds to |
| The findings to fix, from this round's review | `## changes_inventory`: which findings were fixed, and how |
| The findings excluded — unrelated significant ones, ticketed separately rather than fixed here | `## review_notes`: confirmation none of the excluded findings were touched, with their ticket keys in `## tickets` |
| Whether to run `/root-cause-fix` first — required unless every finding is `is_trivial()` | `## review_notes`: which path was taken — direct fix, or `/root-cause-fix` first |
| Report the fix-round summary's content once this round lands, for the coordinator to append to the review file — only what a later review can't already see from the fix commits or the plan updates | `## review_notes`: round number; findings deliberately not fixed, and why (the load-bearing line — that judgment exists nowhere in the commits, so the next round re-reports it unless it's written down here); findings ticketed as unrelated, with keys; findings judged `is_cosmetic()` that a reviewer might re-raise; commit SHAs as bare pointers. Full field list: `second-level-coordinator.md` |

A fix agent's report is the standard contract above plus this fix-round summary — not a
replacement for either.

## A PR-opening or merge agent's brief adds

| Brief says (downward) | Report must carry (upward) |
|---|---|
| Open the PR with `--draft` and no `--reviewer` and no `--assignee`, whatever this repo's default-reviewer convention says — `SKILL.md`'s `open_pr()` owns the rule and its one exception, the closing base → trunk PR | `## evidence`: the `gh pr create` command as run, and the PR's `isDraft` and `reviewRequests` read back from `gh pr view` after it opened |
| To merge an intermediate PR, `gh pr ready` it first — GitHub refuses to merge a draft — then merge; both steps belong to this one dispatch | `## evidence`: both commands and their results |
| Only a closing base → trunk dispatch opens a PR ready for review with the repo's default reviewers, and that dispatch never merges it | `## evidence`: the reviewers requested, and confirmation no merge was attempted |

## A resume brief adds

An agent that stops without reporting — a rate limit, a turn budget — has not failed logically. Its
worktree is intact and its context still holds everything it read, so resume it with `SendMessage`.
A fresh dispatch throws both away and pays to re-derive them.

What each side knows divides cleanly. You can see the **artifacts**: the branch, the head SHA at
`origin`, what is pushed, which PRs are open or merged. Only the agent knows its **phase**, because
commit subjects are inference while the review file, the tracker and the agent's own memory are
record. Telling an agent which phase it is on is the parent guessing at the one thing the child
knows for certain; `second-level-coordinator.md` prices that guess in review rounds.

| Brief says (downward) | Report must carry (upward) |
|---|---|
| The artifacts you verified — branch, head SHA at `origin`, what is pushed, which PRs are open or merged | `## branch`, `## head_sha`: resolved again against `origin`, not quoted back |
| "Report your current phase and next step before you resume" — asked, never asserted | The answer in the agent's reply, before it restarts work; for a review or fix agent, the round it resumed at → `## review_notes` |

## Exit code is never the check

A verification's exit status says the command ran and returned; it says nothing about what it
looked at. A command that exits 0 having checked, collected, or matched nothing reads identically
to one that passed against everything, and only the count the command reports — tests collected,
matches returned, files checked — tells the two apart. Read that count and reconcile it against
the number you expected before believing the result; a green whose scope neither side has checked
carries no more information than the exit code does.

Three shapes recur:

- `uv run mypy <test files>` exits clean before any fix, because mypy skips the bodies of untyped
  defs — a green here proves the signatures typecheck, not that the bodies do.
- A keyword-form grep (`session_type="ehr"`) returns a confident count that misses positional and
  dict-literal forms, and at file-selection level can hide an entire file from the search — the
  count looks precise and is wrong.
- BSD `xargs` on macOS has no `-a` flag, and a shell expansion can silently drop a file list; both
  failures exit 0 having collected 0 tests, and both would read as a pass from the exit code alone.

This binds both sides of a dispatch: a coder reports the count a verification actually produced,
not its exit code, under `## verification` and `## evidence`; a coordinator reading that report
reconciles the count against what it expected before treating the report as a result — the same
standard "What the parent does with what comes back" states for every other claim applies here
too.

## Select tests by symbol, not by filename

"Select tests from the diff" reads as "the tests named after the files I changed", and callers live
in files named after the behaviour they test, not the module they call. An agent that switched
`fhir_persistence.py`'s three outbound calls from a query param to a header ran the five
`test_fhir_persistence_*.py` files and reported 36 green. Eleven test files exercise those
functions; `test_auth_logic.py` asserted the old `kwargs["params"]["smart_session_id"]` shape and
went red on push. The agent did exactly what it was told.

Brief it as **grep the changed symbols across the whole test tree**, and pair it with the count of
files that grep selected. The count is what makes an under-selection visible to a parent that never
reads the test list — this file's opening principle, applied where the instruction otherwise travels
alone. Inside a stack that selection is the entire gate, for the reason
`top-level-coordinator.md` gives.

## What the parent does with what comes back

A confident report is a claim, not a result; plausible-and-wrong is the normal failure mode. The
parent reads the routing header, dispatches an auditor against the full report
(`references/auditor.md`), and re-verifies one claim itself — re-reading what a claim cites in the
code rather than relaying it unchecked (`claims-and-scope-discipline`). Act on discrepancies the
audit names, and on the header's own counts.
