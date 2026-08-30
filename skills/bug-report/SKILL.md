---
name: bug-report
description: Write up a bug, defect, or anomalous measurement found during an investigation in the structured bug-report format — current diagnosis first, dated evidence, ruled-out hypotheses compressed, references table, glossary. Use when a write-up is about to land in chat, a plan tracker, or a ticket, or when the user types /bug-report.
---

# Bug reports from investigations

A bug report is a **state, not a log**. It states the current best understanding
first; the investigation's chronology is not the reader's problem. This skill
governs the prose wherever the report lands — a chat reply, a Jira ticket, a
plan doc's runtime-checks row, a PR description. The `plan-docs` skill owns
where findings live; this skill owns how they read. One bug per report: a
distinct issue found mid-investigation gets its own report and a one-line
cross-reference, never a subsection. Existing entries are not retro-fixed —
apply this to new entries and entries being rewritten anyway.

## Report template

### <One sentence: the cause when known, the symptom until then> *(status)*

The heading states the **cause once diagnosed, the symptom until then**, and is
**rewritten on supersession** — it must never still assert a falsified
diagnosis. Status is one of: `confirmed` · `probable — <the one fact
outstanding>` · `undiagnosed — symptom only`.

**Summary.** 2–5 sentences readable with zero prior context. Name functions,
tables, services, and log events by their real names. No line numbers here. No
coined shorthand.

**Code flow.** Only once the mechanism is known. Numbered steps, one action per
step, every actor named. Use a mermaid diagram instead of prose when the flow
has 3+ branches or a cycle.

**Evidence.** Every count carries its query or command, environment, time
window, and date. Label each claim **measured**, **read from code**, or
**inferred** — never let the three blur. Numbers age; the query is what makes
the report re-runnable.

**Impact.** Blast radius as measured numbers ("13 of 308 rows disagree"), plus
the ongoing cost while unfixed ("a model call per coverage") and whether it
converges or repeats.

**Trigger conditions.** The exact input or state that makes the bug bite, and
the nearest neighboring case that does NOT bite.

**Ruled out.** Each superseded hypothesis in 1–3 sentences: what was believed,
the measurement that killed it, why it looked plausible. This section is where
dead diagnoses go when the report is rewritten — compressed, not deleted, so
they are not re-proposed.

**Open questions.** What the investigation could not settle, and what evidence
would settle each one. A question whose answer decides the fix goes first.

**Candidate fixes.** Directions, not decisions — each with its cost. Say so
explicitly when a fix belongs to another repo or team.

**References.** A numbered table: `| # | Location | What it is |`. In the body,
cite locations as `[n]`, never as inline `file:line` or bare `:836`.

**Glossary.** One line per function, table, flag, or domain term used above
whose purpose is not obvious from its name and was not already explained. Omit
if empty.

## Supersession

When a measurement falsifies the diagnosis, **rewrite the report in place**:
new heading, new Summary stating what is true now, dead hypothesis compressed
into **Ruled out**. Never append a correction subsection below the old text —
a report whose heading and opening are wrong, corrected further down, is worse
than no report.

## Writing rules

- Never use a compressed label for a behavior ("the wedge", "the no-clobber
  branch") unless the full behavior was already stated in the same report and
  the label was attached to it explicitly.
- Never cite a PR, ticket, or item number bare ("#491", "item 30") — attach a
  half-sentence of what it is on first mention.
- Every "it", "this path", "that divergence" must have a named antecedent in
  the same paragraph. When in doubt, repeat the name.
- Repetition between the Summary and the detail sections is fine. Unexplained
  brevity is not.
- Omit sections that do not apply; never leave them empty.
- Sentences under 25 words, active voice, one idea per sentence.

## Handoff form

When the destination cannot carry the full structure (a ticket summary, a
standup line): what breaks, for whom, current status — two sentences, drawn
from the Summary and status, nothing new.
