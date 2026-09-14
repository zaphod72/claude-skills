---
name: dual-scoped-review-plans
description: "Author two review plans for one change, each scoped from a different source, so two review passes find different things: one scoped from what the work already worried about, one from the repo's documented standards with no memory of it. Use when a large or long-running change needs reviewing, when one review pass is not enough, when a plan-rollout run reaches close-out, when deciding what a review pass may look at, when briefing a review-plan author or a reviewer running one of these plans, when writing a review plan that a Claude agent rather than a person will execute, or when two passes have both reported and need synthesising. Checks for the repo's standards docs first and stops if there are none, since a second scope needs a second source. Not the prose a finding is written in (review), grouping findings into a fix plan (root-cause-fix), the review rounds inside a run (plan-rollout), or verifying one finding before acting on it (claims-and-scope-discipline)."
---

# Dual-scoped review plans

Two review passes are worth more than one **only if they were scoped independently.** Two plans
written from the same source find the same things twice.

So: two authors, two **scope sources**, and an **exclusion list** keeping each from seeing the
other's. A *scope source* is the set of files an author may derive its plan from.

| Plan | Scoped from | Finds |
|---|---|---|
| Notes-scoped | What this change already produced — review recommendations, per-PR review files, deviations, and the run's notes from its ledger | Where we already know we worried |
| Docs-scoped | The repo's own standards and architecture docs, with no memory of the change | Where the code departs from what the repo says it does |

**Agreement between the two passes is signal, and so is divergence.** A defect both find is real. One
only the docs-scoped pass finds is a standard nobody thought about. One only the notes-scoped pass
finds is a worry the docs never encoded — there, the doc is the gap. Merging the plans first, or
letting one author read the other's source, collapses both passes into one and throws that away.

**Three roles, and one of them is defined by what it must not know:**

| Role | Sees | Never sees |
|---|---|---|
| **Dispatcher** | Paths, and status | The *content* of either plan or either pass |
| **Author / reviewer** | Its own scope source | The sibling source, the sibling plan, the sibling findings |
| **Synthesiser** | Both passes, and the run | — but it must have watched the run, not merely dispatched |

## Step 0: no standards docs, no skill

**Check for the docs source before anything else. `ls AGENTS*.md CLAUDE.md` at the repo root — if
neither exists, stop here.** Say the repo has no standards docs to scope a second pass from, and
author neither plan.

This is a real exit, not a degraded mode. The premise is two *independent* scopes; with one source
there is no second scope, and a docs-scoped author with nothing to grade against writes a plan that
reads the code and calls it consistent with itself — confident, and worth nothing. A single review
plan is ordinary work that needs no skill.

Report the absence. A repo carrying no documented standards is worth a sentence to the user, and
possibly a ticket, but fixing it is not this skill's job.

## Resolve the two sources before briefing anyone

**The docs source is per-repo. Resolve it; never assume a filename.** In this org the convention
varies: some repos carry `AGENTS.md` plus a family of `AGENTS.<topic>.md` files, some carry only
`CLAUDE.md`, and some carry both.

1. List what step 0 found, plus any architecture doc under `docs/` the user names.
2. Pick the topic files matching what the change touched — a test-infrastructure change scopes from
   the testing doc, a schema change from the database doc.

The notes source is whatever the change accumulated. After a `plan-rollout` run that is the run's own
artifacts, which live under `~/.claude/plan-rollout-runs/<ticket>/`: the review recommendations, the
per-PR review files, the changes inventories, and the deviations. The run's notes sit beside them in
the ledger, `~/.claude/plan-rollout-runs/rollout.db`, readable with
`~/.claude/skills/plan-rollout/scripts/rollout-db dump <ticket>`.

## The exclusion list covers content, not just paths

An author is defined by what it cannot see, and it is briefed by a session that holds everything. A
brief saying "scope from the standards docs" leaks the moment the author asks a clarifying question,
or the brief helpfully summarises what to look for.

- **Name the files this author reads.** Absolute paths.
- **Name the files it does not receive.** For the docs-scoped author that is every run artifact and
  the sibling plan. It gets the diff, the ticket, and its standards docs — nothing else.
- **Quoted, paraphrased and summarised material from a banned file counts as the file.** The
  exclusion is on the content, so restating a notes finding in your own words breaks it exactly as
  pasting the file would.
- **Require the read-back.** Each author and each reviewer reports the files it actually read — the
  downward-requirement / upward-field pairing `plan-rollout`'s `references/brief-contract.md` is
  built on. It is what makes a leak visible afterwards rather than hoped against.

Answering a docs-scoped agent's question about the run is itself a leak. Send it back to its own
scope source instead.

**A reviewer that suspects its own plan is steering it toward the other scope should say so as a
finding**, rather than silently complying. A docs-scoped plan pointing at notes-derived material
means the authoring boundary already failed, and that is worth more to the user than the finding it
was being steered toward.

## The isolation has to survive the pass, not just the plan

**One fresh sub-agent per plan, and per pass. Never `subagent_type: "fork"`.** A fork inherits the
parent conversation wholesale, so it arrives already holding whatever the parent knows — which is
both scope sources. It looks like a dispatch and behaves like a leak.

The same holds when the passes are eventually run: a reviewer executing the docs-scoped plan is a
fresh agent whose context contains its plan and nothing else.

A pass writes its findings to its own report and nowhere else until synthesis. Not to the PR, not
to the ticket, not back into its own plan file — any surface a sibling pass can read is a channel
between them. A plan step that says "post FAIL findings as PR comments" reads as good practice and
breaks the isolation the second pass depends on: `gh pr view` returns the comments field, so the
sibling reviewer sees the first pass's findings mid-run without ever going looking. Every posting
step waits until both passes have reported.

Audit each plan for this before dispatching. The dispatcher may not read the plan's content, so use
a script that greps each plan for its posting verbs (`gh pr comment`, `addCommentToJiraIssue`, and
the like) and prints the matching step numbers only. A hit means the plan needs a fix, not that the
dispatcher needs to read it.

## The dispatching session stays out of both scopes

**A dispatcher passes paths. It never reads either plan or either pass.** No `Read`, no `cat`,
`grep`, `sed`, `head`, or a subshell that prints a line. A session that absorbs one plan can leak it
into the other agent's brief, or into a later message, without ever intending to — and it cannot
un-know it afterwards.

This is why a dispatcher is disqualified from synthesising: staying scope-clean is exactly what
leaves it unable to reconcile the two.

**When a completeness or sanity check is genuinely needed, put it in an executable script that reads
the files and prints status only** — counts, present/absent, a section-heading tally. Never a quoted
line, never an excerpt. The script may read what the session may not.

## Each plan is an agent's instruction set, not a human's memo

**A Claude agent executes these plans; a human only decides whether to spend the pass.** So an
author is writing an agent-facing document, and `writing-for-agents` applies to it in full — steps
in the order the reviewer performs them, reference it consults on demand, positive phrasing, and no
prose that merely explains the change to a reader.

Two properties matter more here than in a document a person reads:

- **Checkable, exhaustive completion criteria.** A reviewing agent stops when its plan says it is
  done, so a vague bound ends the pass early. "Every fencing call site accounted for" or "each
  guard's terms enumerated with coverage per term" gives a reviewer something it can fail; "review
  the concurrency handling" does not.
- **Self-containment, because a later session runs it.** The plan may be picked up by a session that
  never saw the brief that produced it. **It therefore carries its own scope statement and its own
  exclusion list**, in the document. A plan relying on the dispatcher to re-supply the exclusion
  loses it the first time someone hands the file to an agent, and the isolation evaporates silently
  — the reviewer just reads more than it should, and reports confidently.

A leak inside the plan is permanent in a way a leak in a brief is not: the file persists, so every
future pass run from it inherits the contamination. A notes-scoped plan may quote its notes freely,
that being its scope; a docs-scoped plan contains no notes-derived sentence at all.

State the reviewer's read-back requirement in the plan too, so a pass reports the files it read
whether or not the dispatching brief remembered to ask.

## Authoring and running are separate steps

**Writing a review plan and running the pass it describes are two steps, often two sessions.**
Confirm which the user wants before dispatching any reviewer — a plan is cheap to read and change,
a pass is not.

A `plan-rollout` run ends by authoring both plans and stopping. It never runs the passes: the same
agents just built the code, and each PR already had its rounds. These plans exist for a pass that
runs later on fresh agents, after the closing PR — the human's call is whether to spend it, not to
perform it.

Land both plans in the repo's `plan/` directory per `plan-docs`, whose §0 marks a review plan as a
separate species there — it is not corrected in place, not owned by a coordinator, and not consumed
at close-out, unlike the implementation plan beside it. Three things follow from a durable
path rather than a scratchpad: the dispatcher hands over a path instead of content, a later session
can run the pass without the original brief, and the plans travel with the closing PR so whoever
decides whether to spend the pass can see what it would cover.

## Synthesis: who may do it, and what "not yet" forbids

**Synthesis happens in a session that watched the run, after both passes report.** Never before, and
never in a session that only dispatched them — that session is scope-clean by design and would have
to break its own isolation to read the passes.

**"Do not synthesise" also bans ranking and comparing.** Report each pass's results as two
independent facts, counts included. Even "the docs pass found more than the notes pass" starts the
reconciliation the synthesising session is supposed to do from scratch, and it anchors that session
before it has read a single finding.

Once synthesising, report three groups separately, because they mean different things:

- **Both passes found it** — real, and worth fixing first.
- **Only the docs-scoped pass found it** — a documented standard the change missed. Check the
  standard is current before acting; a doc can be stale.
- **Only the notes-scoped pass found it** — a worry the docs never encoded. If it is real, the doc is
  the gap, and saying so is worth more than the fix.

Verify a finding against the code before acting on it (`claims-and-scope-discipline`), write findings
in the template `review` owns, and group what survives by root cause with `root-cause-fix` rather
than patching each one.
