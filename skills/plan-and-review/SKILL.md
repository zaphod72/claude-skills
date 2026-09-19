---
name: plan-and-review
description: "Produce a ratified plan for a piece of work: pair it with a tracker ticket, decide whether it needs a plan at all, check every claim before writing it down, review the draft with a subagent, and resolve every open question with the user. Use when a ticket needs implementing and has no plan, when a plan doc exists with no ticket, when deciding whether work is simple enough that its ticket description is the plan, when a plan's claims have never been checked against the code, when a draft plan needs reviewing before anyone builds it, when a plan still carries open questions, or when a ratified plan is blocked on work outside it. Not where a plan doc lives or how it stays true once work starts (plan-docs), or delivering a plan or ticket as merged PRs through coordinators and coding sub-agents (plan-rollout)."
---

# Plan and review

A plan is a set of assertions made at writing time, and every unchecked one is an error a
downstream agent will implement faithfully. This skill produces the plan those agents can be
trusted with: paired to a ticket, claim-checked before drafting, reviewed by a subagent, and with
every open question actually resolved.

**Done when the plan is homed in `plan/`, carries its ticket key, states a partition in the shape
`plan-rollout`'s `partition()` reads, and has zero open questions left in it; or when you have stated, with the
reason, that this work needs no plan.** Those are the only two exits.

## Usage

```
/plan-and-review BOOK-1234              # ticket → plan (if one is needed)
/plan-and-review @<plan-doc>            # plan → ticket, then review
/plan-and-review BOOK-1234 @<plan-doc>  # both given: straight to step 3
```

## Steps

### 1. Establish the ticket/plan pair

The unit is the pair, because a plan with no ticket has nowhere to put its findings: findings, open
questions, and decisions live on the tracker, not beside the doc (`plan-docs` §3).

- **A plan with no ticket:** search for a duplicate, then create one (an epic when the work spans
  stories) and write its key into the plan doc. **Scope the search's returned fields.** A `text ~`
  JQL with default fields returns every field of every match; one such search came back at 130k
  characters and overflowed the context it was run in. Request `summary`, `issuetype`, `status`
  and `parent` only, save the result to a file, and read it with `jq`.
- **A ticket with no plan:** step 2 decides whether to write one.
- **Neither:** ask what the work is. Do not infer it from the branch or the last thing discussed.

### 2. Decide whether this work needs a plan

**Most tickets do not.** Say which answer you reached and why, before doing anything else.

Write a plan when any of these holds:

- the work spans more than one PR;
- it names more than one service or repo;
- it leaves a design choice genuinely open, so an implementer would have to invent an architecture;
- it implies deploy-time ordering (`claims-and-scope-discipline` §12): a flag, a migration, an env
  var that has to land before or with something else;
- it asserts facts nobody has checked.

Otherwise **the ticket description is the plan.** A ticket a single agent can deliver in one PR
gains nothing from a plan doc and a wave engine, and writing one anyway buys a document that starts
decaying immediately. Hand it to `plan-rollout` with all three of: **the ticket key** (step 1
may have just created it), **the reason no plan is needed**, and **anything step 1 already
established** (the repo's real integration branch, a claim you happened to check). `plan-rollout`
treats this as a one-PR, one-aspect partition, so a single-aspect plan still gets a coordinator
there: the hand-off has a real target. A bare "go do this ticket" makes the next agent re-derive
what you already hold, and drops the ticket you just filed on the floor if it was created here.

When this decision arrives from `plan-rollout` (which calls this skill when it has no ratified plan),
return it there instead; that skill hands off itself.

### 3. Check every claim before writing it down

Authoring is the cheapest moment in the whole lifecycle to apply
`claims-and-scope-discipline` §1: **call it** and classify anything that does not hold as stale or
wrong. A claim caught here costs a grep; the same claim caught at rollout costs a dispatched agent's
whole story, and caught in review it costs a round.

Check, before drafting rather than after:

- **Every symbol, path, and file** the work will touch: grep for each one.
- **Every number** you are about to assert. Run the query, count the rows. The number becomes a
  target in a sub-agent's brief later, so a wrong one propagates.
- **Every prerequisite the ticket calls pending**: merged PRs, applied migrations, deployed jobs.
  Check `git log`, `gh pr view`, and the live schema, not the ticket's status field.
- **Any runtime path, end to end (reading, not grepping).** Grep verifies what a file *says*;
  only reading the code verifies what it *does*. One plan's frozen migration baseline turned out
  to execute every view in `ddl.py` at runtime, which made a later column change impossible; a
  deploy-blocking fact no grep of the objects named could surface. For a migration plan that
  means `env.py` and the baseline's `upgrade()` in full.
- **Any claim of the form "no environment has X"**: enumerate environments from the
  infrastructure source of truth, the tfvars, not from one cluster's listing. Inferring it from
  the four databases in front of you is how this exact inference failed once already.
- **Anything whose answer lives outside this repo**: a library's actual contract, an API's real
  response shape, another service's behaviour. Use `/mattpocock-skills:research` and cite what it
  returns.

Drafting first and checking after inverts the incentive: an unchecked claim already written down
gets defended rather than tested.

### 4. Draft the plan

Home it per the `plan-docs` skill (`~/.claude/skills/plan-docs/SKILL.md`): it owns where the plan
lives and how it stays true. **Read it now.**

The draft carries, beyond the work itself:

- **The partition**: a stack diagram or an explicit per-PR list with dependencies, in the shape
  `plan-rollout`'s `partition()` reads back, with operational steps kept out of the code PRs and
  named as the operational units they are, each carrying its own ticket.
- **A `## Runtime-only checks` section** in `plan-docs` §3's format, for everything that can only be
  confirmed once the code runs.
- **An explicit open-questions list.** Every question you could not settle from the code, each one
  naming what someone has to find out rather than just what is unclear
  (`claims-and-scope-discipline` §13).

### 5. Review the draft with a subagent

Dispatch one `Plan` subagent against the finished draft. **Opus** when the plan leaves design
choices open or crosses services; **Sonnet** when it is well-specified feature or fix work.

Brief it per `plan-rollout` (`references/brief-contract.md`), including its evidence demand: **the commands it
ran and the raw output, alongside every conclusion, and an explicit split between what it verified
and what it inferred.** A review that returns conclusions alone cannot be checked. The same
reference's suppression-artifact rule (full re-read at write time and at every design change,
scoped headings only) applies to this plan doc once it starts carrying "verified, do not
re-derive" claims of its own.

Ask it to grade five axes and report per finding:

1. **Every factual claim** — does the code say what the plan says it says?
2. **Every dependency** — is it real, or an assumed ordering nobody verified?
3. **The partition** — are the PRs small, and does each stacked one genuinely need its parent?
4. **Deploy-time ordering** — anything that has to happen in a particular order at deploy time and
   is invisible in the diff.
5. **The open questions** — is each one genuinely open, or already answered somewhere in the repo?

**If you are the top level, do not idle while it runs.** Useful work is nearly always available:
correcting the ticket's own description, writing this run's notepad entries, a triage pass the
user asked for. Keep it off the plan doc the reviewer is reading. **If you are yourself a
subagent** (called by `plan-rollout` inside a larger run), the opposite holds: your
turn ends the moment you dispatch, so hold still and take no side work in the shared tree.

You assess and combine what comes back; that synthesis never gets delegated. Treat a confident
finding as a claim, not a result: check the evidence against the plan before acting on it.

**After folding findings that change the design, resume the same reviewer with `SendMessage` for
a delta pass on the rewritten sections.** It keeps its context and costs minutes; a fresh agent
re-reads the whole tree and grades the new text without knowing what it replaced.

### 6. Resolve every open question

**Zero open questions is the bar**, and the questions that need a human decision go to the human.
Use `/mattpocock-skills:grilling` to stress-test a decision the user is making on instinct, or one
where the plan's whole shape depends on the answer.

**When a review finding reverses a decision the user already made, attach the reviewer's raw
output to the question.** Two findings did exactly that on one plan (reversing a decision, and
reopening one the user had closed by implication), and both closed in a single round because the
evidence went with the question.

Each resolution **rewrites its plan section** as the new statement of what the work does
(`plan-docs` §2: rewrite, never append: a reader cannot tell an appended note from a live
instruction). Record the decision itself on the ticket.

A question you cannot close stays a question; move it to the `## Runtime-only checks` table if a
live run would settle it, or to a ticket of its own if it needs someone else. What it must not do is
stay in the open-questions list while you call the plan ready.

### 7. Hand off, or return

- **Called by `plan-rollout`:** **return** the plan path, the ticket key, and the partition to
  the caller, and stop. Control belongs to that run.
- **Invoked directly:** **call `plan-rollout`** with the plan path and the ticket key.
- **Ratified but blocked:** the plan is done and something outside it must land first: another
  epic's PR, a migration, a deploy. Say so, name the blocker and what clears it, and **stop**.
  Rollout is the user's to invoke once it clears; calling `plan-rollout` on a blocked plan starts
  a run that cannot finish.

Exactly one of these fires per run. `plan-rollout` calls this skill for a plan and then continues on
its own, so calling it back from here would restart that run from the top; the condition is how
*this* skill was entered, and no description can carry that state, which is why it is stated here.
`plan-rollout` states the same rule at its own side of the seam.

## Self-improvement protocol

While working under this skill, append dated entries to
`~/.claude/orchestration-notepad.md`: what fired, what misfired, what the skill lacked. Head each
entry with the skill it came from; the orchestration-family skills share this notepad. When
everything the work touched is merged and reviewed, present candidate augmentations to the user;
ratified ones land as edits to the relevant skill and the entries get marked extracted.
