---
name: review
description: Run the code-review workflow, then write every finding in the structured finding format — plain-language summary first, numbered code flow, trigger conditions, references table, glossary. Use when the user types /review, asks for a review with readable findings, or is passed a review-file path to read and append findings to.
---

# Review with structured findings

0. If given a review-file path — a per-PR review file, used inside a `plan-rollout`
   run as the round-memory mechanism — read it before reviewing, so this round sees
   earlier rounds' findings and their fixes.
1. Invoke the `mattpocock-skills:code-review` skill via the Skill tool. Pass this
   skill's arguments through verbatim (target, effort level, `--comment`, `--fix`),
   plus the finding template below, so that skill formats its own output with it.
2. Follow the `mattpocock-skills:code-review` skill for **process**: scope, passes,
   verification, verdicts, and any `ReportFindings` call it requires.
3. For finding **prose** — in the chat response and in any review document written
   to disk — use the template below. It overrides the review workflow's default
   finding prose. Keep the workflow's heading markers (ID, verdict, pass number).
4. If given a review-file path, append this round's findings to it, so a later
   round's reviewer sees them. Report which prior rounds were read, by number.

## Finding template

### <ID>. <One sentence: what breaks, in plain words> — <VERDICT> *(pass, status)*

**Summary.** 2–5 sentences readable with zero prior context. Name functions,
tables, scripts, and log events by their real names. No line numbers here. No
coined shorthand.

**Code flow.** Numbered steps, one action per step, every actor named:

1. <data item> is written by <function> when <condition>.
2. Processing branches on <check>:
   - Path A (<condition>): <function> does <what>, then <outcome>.
   - Path B (<condition>): <what>.
3. ...

Give each path needing more detail its own short paragraph after the list.
Use a mermaid diagram instead of prose when the flow has 3+ branches or a cycle.

**Why it persists.** Only for stuck or permanent states: list each repair
mechanism that was checked and why it does not fire.

**Trigger conditions.** The exact input or state that makes the bug bite, and
the nearest neighboring case that does NOT bite.

**Relation to known items.** Only when the finding overlaps a tracked item:
what that item already records, then what is new here.

**References.** A numbered table: `| # | Location | What it is |`. In the body,
cite locations as `[n]`, never as inline `file:line` or bare `:836`.

**Glossary.** One line per function, table, or flag used above whose purpose is
not obvious from its name and was not already explained. Omit if empty.

## Writing rules

- Never use a compressed label for a behavior ("the write-nothing permanence",
  "the wedge") unless the full behavior was already stated in the same finding
  and the label was attached to it explicitly.
- Every "it", "this path", "that divergence" must have a named antecedent in the
  same paragraph. When in doubt, repeat the name.
- Repetition between the Summary and the detail sections is fine. Unexplained
  brevity is not.
- Omit sections that do not apply; never leave them empty.
- Sentences under 25 words, active voice, one idea per sentence.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/review-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
