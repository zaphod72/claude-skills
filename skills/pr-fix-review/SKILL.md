---
name: pr-fix-review
description: "Use when a PR has been through multiple rounds of review and fix — findings keep turning up round after round on the same PR, or the user asks whether a PR is converging or stuck. Diagnoses whether the recurring findings share one missing core concept or structural risk, or are independent bugs converging to completion, using the PR description, its Jira ticket, and (if given) its plan doc — and checks whether that starting context was itself detailed enough for the size of the change. When the diagnosis lands on a missing concept or a significant context gap, gates implementation: any coding agent reading the output must stop and ask the user rather than fix the findings itself. Hands the diagnosis to the /review skill as context, then prepends the gate and diagnosis above /review's findings. Also directly invocable, e.g. `/pr-fix-review 492` or `/pr-fix-review 492 BOOK-317 @plan/availity-codes.md`."
---

# PR fix-review

A PR draws a second, third round of findings. Before running another review pass
head-down into the diff, step back: is each round finding independent bugs and the
count is shrinking — **converging** — or does the same design gap keep re-manifesting
as a new symptom every round — **stuck**? And before blaming the coding agent for
that, check what it was actually given to work from — a vague ticket or a missing
plan doc produces exactly this pattern, one guess at a time. This skill answers both
questions, then runs `/review` with the answers as context.

## Steps

### 1. Gather the record

Collect, for the PR under review (`<pr-number>` from the invocation):

- **PR description and metadata** — `gh pr view <pr-number> --json title,body,url,state,author`.
- **Change size** — `gh pr view <pr-number> --json additions,deletions,changedFiles,files` and
  `gh pr diff <pr-number> --stat`. This is the yardstick step 3 measures the starting
  context against.
- **Every review round on record** — `gh pr view <pr-number> --json reviews,comments` and
  `gh api repos/<owner>/<repo>/pulls/<pr-number>/comments --paginate` for inline
  findings. Pull every round, not just the latest — a finding's *recurrence* across
  rounds is the evidence this skill runs on.
- **The Jira ticket** — auto-detect from a `https://*.atlassian.net/browse/<KEY>` link
  in the PR body; if none is found and the invocation didn't supply one, ask the user
  for the ticket key before continuing. Fetch it in full (summary, description,
  every comment) via the Atlassian MCP tools.
- **The plan doc**, if the invocation passed one as `@<path>` — read it in full. Its
  absence is itself data for step 3, not a gap to fill by asking — don't ask for one
  that wasn't supplied.

Done when every review round is captured as data (reviewer, verdict, each finding's
location and one-line claim), not paraphrased from memory of an earlier summary.

### 2. Build the round timeline

For each round in order, record: what was found, what the author's fix was, and
whether that round's findings were themselves triggered by the *previous* round's
fix (a fix that introduced the next round's bug is the strongest signal of a
recurring gap — flag it explicitly when it happens).

### 3. Assess whether the starting context was enough to build from

Judge the Jira ticket (and plan doc, if any) against the change size from step 1 —
not against how the PR turned out:

1. **Ticket detail vs. what the implementation needed to decide.** Walk the findings
   from step 2 and ask, for each: was the answer to this actually stated in the
   ticket, or did the coding agent have to infer it? A ticket that states a goal
   ("use payer-specific codes") without the deciding details (which payers are
   actually live, which field carries which signal, who else reads the output) hands
   the agent exactly the kind of decision that review rounds keep catching wrong.
   Name the specific missing detail, quoting what the ticket does say alongside it.
2. **Plan doc expected but absent.** A change is plan-doc-sized when it does two or
   more of: touches multiple packages/services, introduces a new external
   integration or client, adds a schema/constant consumed by more than one
   consumer, or requires a cross-cutting design decision (a new shared map, a new
   gate/flag controlling behavior, a new field two services must agree on). If the
   change from step 1 meets that bar and no plan doc is linked in the PR body, on
   the ticket, or passed to this skill — that is a **significant miss**, independent
   of whether the reviews found bugs. State it as such, don't soften it into a
   suggestion.
3. **Vague vs. sufficient is a judgment call — back it with evidence.** Don't call a
   ticket insufficient because it's short; call it insufficient when a specific,
   consequential decision in the diff has no ticket answer to point to. Quote the
   ticket's own words when it does provide the needed detail, so the assessment
   reads as checked, not assumed.

### 4. Diagnose the review-round pattern

Check, in this order:

1. **Traces to the context gap from step 3.** Does a finding exist because the
   coding agent guessed at something the ticket/plan never specified? Say so
   directly — this is the most actionable diagnosis, since the fix is answering the
   ticket, not patching the symptom again.
2. **Same wrong signal reused.** Do findings across different rounds trace back to
   one value, flag, or field being read for a purpose it was never designed for —
   the same contaminated signal surfacing in a new call site each round? Name the
   signal and every site it corrupted.
3. **Structural duplication.** Does the architecture itself require the same fact
   to be derived independently in two or more places (two payer maps, two branch
   selectors, two owners of one concept)? If so, every future round that touches
   either copy can reintroduce the divergence regardless of how many rounds already
   passed — this is a standing risk, not a bug the review can close.
4. **Scope drift from the ticket.** Does the PR's actual behavior, or a reviewer's
   objection, contradict what the Jira ticket (or plan doc) says the feature is
   for? A finding that argues with the ticket's scope needs a scope decision, not
   another code fix.
5. **Genuine independence.** If none of the above holds — each finding is a local,
   unrelated mistake, and the count of new findings is shrinking round over round —
   the PR is converging. Say so plainly; don't manufacture a pattern where the
   evidence is just normal review noise.

### 5. Write the verdict

Two parts, both always present even when one has nothing notable to say:

- **Starting-context assessment** (from step 3): sufficient, or the named gaps and
  the missing-plan-doc call, if any — this runs regardless of how the round-pattern
  diagnosis below comes out.
- **Round-pattern verdict** (from step 4): **converging**, **stuck on a missing
  concept** (name it), or **structurally at risk** (name the duplicated
  responsibility) — not exclusive; a PR can be converging on symptoms while sitting
  on a structural risk, or stuck purely because the ticket never specified the
  answer.

Back both with the specific rounds, findings, and ticket passages from steps 2–3,
not a restatement of the categories.

### 6. Decide the gate

The verdict from step 5 sometimes means a coding agent cannot safely fix the
findings by itself — because the correct fix depends on a decision nobody has
made yet, not on effort. Set the gate to **BLOCKED** when either holds:

- The round-pattern verdict is **stuck on a missing concept** — by definition, the
  findings recur because nobody has written down what the concept means, so
  patching each finding individually just produces the next round's recurrence.
- The starting-context assessment named a **significant miss** (step 3.2) and at
  least one open finding needs the missing decision answered to be fixed
  correctly — not just to be fixed at all.

**Converging**, or **structurally at risk** on its own with no named context
gap, sets the gate to **OPEN** — the duplication's correct resolution is already
determinable from existing code (a shared helper, an established convention),
so a coding agent can consolidate it without new input from anyone.

When BLOCKED, write, in this order:

1. The exact missing decision, one sentence: what nobody has specified, not a
   restatement of the finding.
2. The literal question to ask the user.
3. If some findings need the missing decision and others are self-contained
   mechanical fixes (a duplication whose correct target is already unambiguous
   in existing code) — split them: name which are blocked and which are safe to
   fix now. If every finding depends on the same missing decision, say that
   instead of forcing a split.

When OPEN, state that plainly and move on — don't manufacture a gate where the
findings are just ordinary bugs with unambiguous fixes.

### 7. Run /review with the verdict as context

Invoke the `review` skill (which runs `code-review` and applies the structured
finding template). Pass through: the verdict from step 5, the gate from step 6,
the Jira ticket content, the plan doc content (if any), and instruct it to
explicitly re-verify — not just trust — every prior round's claimed fix, the
same way this skill's step 1 pulled every round rather than the latest summary.

### 8. Prepend the gate and verdict to the output

`/review`'s own output is the findings report. Put the step 6 gate first, then
the step 5 verdict, as one header above it in the same response — a coding
agent reading top-down hits the gate before it reaches a single finding to fix.

## Output shape

```
## Implementation gate

<BLOCKED — STOP. Do not implement fixes below.
Missing: <the one sentence from step 6.1>
Ask the user: "<the literal question from step 6.2>"
Blocked findings: <list, or "all"> | Safe to fix now: <list, or "none">

 -- or --

OPEN. No missing decision blocks these fixes; proceed normally.>

## Review-pattern assessment

**Starting context:** <sufficient, or named gaps / missing-plan-doc call>

**Round pattern:** <converging | stuck on <concept> | structurally at risk on <responsibility>>
<round-by-round evidence>

---
<review skill's findings report, unmodified>
```

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/pr-fix-review-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
