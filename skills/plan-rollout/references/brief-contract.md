# The brief contract

Neither a rule (always loaded) nor a skill (invoked on demand): the **brief contract** is a
required section of every dispatch prompt — what a parent puts in a child's prompt, and what the
child must send back.

**Pairing is the whole mechanism, and it is why this file exists.** Every downward requirement
below has an upward report field that would expose its omission. A run whose briefs required
`/tdd` in prose alone got agents that quietly skipped it, because nothing in the report would have
revealed the skip — an unpaired requirement drifts silently, and a more emphatic sentence fails the
same way. State the requirement and its paired field together, or don't bother stating it.

Every `report_upward()`, `brief_for(...)`, `brief_for_review(...)`, and `brief_for_fix(...)` called
in `top-level-coordinator.md`, `second-level-coordinator.md`, and `coding-agent.md`'s pseudo-code
means the tables below — they do not restate the fields, and neither should you when writing an
actual brief. Call `AWAIT_DECISION()`, `needs_human()`, `is_cosmetic()`, and `is_trivial()` by name;
their bodies live in `SKILL.md` and nowhere else.

## Every brief

| Brief says (downward) | Report must carry (upward) |
|---|---|
| Use `/tdd` unless told otherwise, and read exactly one reference file for your role, named here by path — not left for you to infer | Which skills were used, and which reference file was actually read |
| Your assigned file scope; stop and report before leaving it | `blocked_on`, if it fired, naming the files |
| Your base branch name, already pushed, and the base SHA recorded now, at dispatch | Branch name and short commit SHAs, resolved against origin — checked against what was recorded at dispatch, not just quoted back |
| The worktree path you are to work in, created at the base branch named here | The worktree's absolute path, and whether you created it or were handed one |
| Commit incrementally, and before reporting | The SHAs, plural |
| The run artifact directory, as an absolute path — never let the agent resolve "the session scratchpad" itself; a sub-agent can land in a different directory with no error at all | Which artifact files it wrote |
| Facts already verified — do not re-derive them | What you verified vs. inferred, stated explicitly |
| **Traps earlier agents hit**, not only interfaces they changed — a DDL splitter that breaks on a semicolon inside a prose comment, a join that silently returns zero rows unless a prefix is stripped, a duplicated block shadowing a live assignment. These cost the discovering agent real time and are invisible in a diff | Any new trap this agent hit, in the same shape, so the next brief can carry it |
| Show your work | Commands run, with raw output and counts |
| **What the verification command actually covers**, read from the task or script definition before the first brief. Nine agents once reported `check-types` clean as evidence their new test files were sound; that task ran the type checker over `src` trees only and had never looked at a test file — run by hand, one test tree held 20 errors | The command's scope as the agent understands it, alongside its result. A green whose scope neither party has checked is a claim wearing a number |
| The numbers you measured, as targets to reproduce. This is the **anti-gaming clause**: a stated number is a target the agent must reproduce, and if its own output differs that is a bug in its work, not a license to adjust the expectation | The value you actually got, matched against the target or flagged as a discrepancy — never silently rewritten to agree |
| Name **the discriminating test** — the one test that fails if the design is wrong, called out explicitly so it can't be lost in a list of equals | Confirmation it ran, and its result — silence on this one test is a gap, not a pass |
| **The disagreement rule, wherever this PR makes a value deterministic:** for every value it pins, write a test in which the *other* source would give a different answer | Those tests, one per pinned value. A fixture where both sources agree proves nothing about which one the code read — that is how a wrong-source bug survives a fully green suite |
| Ask for **the changes inventory** — a factual, per-item list of every file, symbol, signature, schema, or config key touched, and what changed about it, with no judgment about other PRs | The inventory itself: raw material for blast radius, not an opinion about it |
| Which `/tdd` mode this slice gets — red-first, or mutation-with-a-control-arm — and the seam the tests sit at; where neither fits (no reachable seam, pure config, generated output, Terraform and other declarative-infra changes), say so and why. Mechanics for both modes live in `coding-agent.md` | Confirmation of the mode and the seam, or confirmation the brief's no-`/tdd` call still held |
| Report deviations as deviations, not as narrative | Plan deviations, listed |
| Report where the plan was simply wrong, separately from what you chose to do differently | `plan_errors`, distinct from deviations — ask for it explicitly or you will not get it |
| Ask: does this change require anything to happen in a particular order at deploy time? | The answer, even when it is "no" |
| Ask what can only be confirmed once the code runs | `runtime_only_concerns` — per entry, what needs a live run to confirm, and the log line added to catch it, or why none was. `plan-docs` owns the `## Runtime-only checks` table these feed |
| Say what you could not finish | What you left undone, and why |
| Name any work the plan called for that you skipped | The skipped items — not a stop, it reaches run notes |
| If checks are red, commit anyway and open the PR as a draft, and say whether the same failure reproduces on the base ref | Red-check status, the base-ref answer, and confirmation it opened as a draft — not a stop, it reaches run notes |
| If you need a decision you cannot make, call `AWAIT_DECISION()` | `status: blocked` plus `blocked_on`: the decision needed and the options you see |
| Where a known defect stands between you and the task, it is named here as a decision with options — never as a caution to watch for | Which option you chose, and why — a workaround picked under budget pressure stays visible instead of silent |
| Where your scope is one file, you may report which of your own tests went red. You may never report that a mutation reddens "only" those — cross-file kills are invisible from inside one file | Which of your own tests went red, scoped honestly. An unqualified "only" is a finding the parent checks against the cross-file pass in `review-efficacy-axis.md`, not a result it relays |
| Run the PR's own test files first — they catch real failures in seconds — then background any long suite rather than blocking on it | Whether the long suite ran inline or was backgrounded, and its result once it lands |
| Record how the review went | Review notes, and how many rounds it took |
| Record tracker changes | Tickets created or touched, with keys |
| Say which skills helped and which did not | The skill-efficacy entries |
| "Report anything here that turns out to be wrong, including anything I have told you" | Which brief statements, if any, turned out wrong, and the correction — an empty list is a claim too, not a default |

Two fields carry the most routing weight: **plan deviations**, and **what the agent left undone**.
A report that omits "I could not do X" is the failure mode — read those two first.

## A review agent's brief adds

| Brief says (downward) | Report must carry (upward) |
|---|---|
| The absolute path of this PR's review file; read it before reviewing, append to it after | Which prior rounds it read, by number, and where it appended |
| The review recommendations for this aspect — code already reviewed and found correct, and the declared scope gaps for this PR (every "this PR deliberately does not…" decision, stated as what it is and why) | Which recommendations it relied on to skip re-review, and which declared gaps it checked a finding against before raising it as a defect |
| From round 2 on, the two convergence-diagnosis questions — do the rounds so far share one missing concept, and was the ticket or plan ever detailed enough for the size of this change — asked of this same dispatch, never a second one, so the cap of three holds | A verdict of OPEN or BLOCKED beside the findings. BLOCKED names the decision nobody made; OPEN says plainly that these are ordinary bugs converging round by round |
| The agreed design, not just the ticket — including anything settled after the ticket was written | Confirmation the design, not just the ticket, was what Spec was graded against |
| You are read-only in the PR worktree, and you never fix a finding — not even a trivial one; fixes are a separate dispatch, so the same eyes that found a defect don't grade their own fix | Confirmation, and the SHA reviewed |

## A fix agent's brief adds

| Brief says (downward) | Report must carry (upward) |
|---|---|
| The review file path | Confirmation it was read, and the round number this fix responds to |
| The findings to fix, from this round's review | Which findings were fixed, and how |
| The findings excluded — unrelated significant ones, ticketed separately rather than fixed here | Confirmation none of the excluded findings were touched, with their ticket keys |
| Whether to run `/root-cause-fix` first — required unless every finding is `is_trivial()` | Which path was taken: direct fix, or `/root-cause-fix` first |
| Report the fix-round summary's content once this round lands, for the coordinator to append to the review file — only what a later review can't already see from the fix commits or the plan updates | The summary: round number; findings deliberately not fixed, and why (the load-bearing line — that judgment exists nowhere in the commits, so the next round re-reports it unless it's written down here); findings ticketed as unrelated, with keys; findings judged `is_cosmetic()` that a reviewer might re-raise; commit SHAs as bare pointers. Full field list: `second-level-coordinator.md` |

A fix agent's report is the standard contract above plus this fix-round summary — not a
replacement for either.

## What the parent does with what comes back

A confident report is a claim, not a result; plausible-and-wrong is the normal failure mode.
Check the evidence a report carries — the commands run, with raw output and counts — before acting
on any finding, and re-read what a claim cites in the code rather than relay it unchecked
(`claims-and-scope-discipline`).
