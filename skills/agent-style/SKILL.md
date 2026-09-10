---
name: agent-style
description: Literature-backed prose rules for engineering documents a human reads later — READMEs, code comments, commit/PR/issue text, changelogs, runbooks, postmortems, and docs that explain technical work to a non-technical reader. Apply as a pass after drafting such a document. Not for the chat reply itself — the active output style governs that.
---

agent-style (v0.4.2, +RULE-J) is 22 rules against recurring failure patterns in LLM-written technical prose: 12 canonical rules from Strunk & White, Orwell, Pinker, and Gopen & Swan, plus 10 patterns observed directly in LLM output, 2022–2026. Run it as one pass over a finished draft, not as 22 separate steps.

**Escape hatch:** *"Break any of these rules sooner than say anything outright barbarous."* — Orwell, 1946. Rules serve clarity; drop one when it fights the sentence.

**Scope:** prose in engineering docs, comments, commit/PR/issue text, changelogs, runbooks, postmortems, and explainers for a non-technical reader. Full citations, severity, and BAD→GOOD examples for every rule: [`RULES.md`](RULES.md).

**Relation to the Plain English output style** (`~/.claude/output-styles/plain-english.md`): that style governs the chat reply itself; this skill governs a document the reply produces or references. They share ground — RULE-02 (active voice), RULE-03 (concrete over abstract), RULE-H (cite or show evidence) restate Plain English's active-voice, quantify-don't-intensify, and no-unverifiable-claims rules for the document case. One difference is deliberate, not a gap: Plain English favors bullets and tables for a busy chat reader; RULE-A favors flowing prose in a document someone reads carefully later. Follow whichever this document is.

## Canonical rules

- **RULE-01 — curse of knowledge** (critical): name a concrete reader; define or cut any term that reader would have to look up.
- **RULE-02 — passive voice** (high): name the agent — "Y did X", not "X was done by Y" — unless the agent is genuinely unknown or irrelevant.
- **RULE-03 — abstraction** (high): replace category words ("factors", "issues", "considerations") with the specific thing behind them.
- **RULE-04 — needless words** (high): cut filler — "in order to", "due to the fact that", "it is important to note that".
- **RULE-05 — dying metaphors** (high): cut clichés ("pushes the boundaries", "paradigm shift"); state the number, comparison, or mechanism instead.
- **RULE-06 — avoidable jargon** (medium): "leverage" → "use", "utilize" → "use", "methodology" → "method". Keep jargon that carries distinct technical meaning.
- **RULE-07 — positive form** (medium): "not large" → "small"; don't stage a claim as "X, not Y" unless the rejected Y is specific and informative.
- **RULE-08 — claim calibration** (high): match the verb to the evidence — "suggests"/"shows" for results, "proves" only for derivations; name the source instead of "prior work shows".
- **RULE-09 — parallel structure** (medium): coordinate items (bullets, "and"/"or" lists) share one grammatical form.
- **RULE-10 — related words together** (medium): keep subject next to verb; move a long parenthetical to the sentence's end or a new sentence.
- **RULE-11 — stress position** (medium): put the fact you want remembered at the sentence's end, not buried mid-sentence.
- **RULE-12 — sentence length** (high): split sentences over 30 words; vary length across a paragraph.

## Field-observed rules

- **RULE-A — bullet overuse** (medium): keep argued or causal prose in sentences; bullets only for genuine parallel enumerations. Don't force a 3-item triad where 2 items or one sentence fit.
- **RULE-B — dash punctuation** (medium): no em/en dash as casual punctuation — use a comma, semicolon, colon, or parentheses instead. (Numeric ranges and paired names are fine.)
- **RULE-C — same-word openers** (medium): don't start two consecutive sentences with the same word.
- **RULE-D — transition overuse** (medium): don't open a sentence with "Additionally"/"Furthermore"/"Moreover" unless the logical move genuinely needs flagging.
- **RULE-E — summary closers** (medium): don't end every paragraph with a sentence that restates its own point.
- **RULE-F — term consistency** (medium): once a term or abbreviation is defined, keep using that exact form — no synonym drift, no re-defining it later.
- **RULE-G — heading case** (low): title-case section headings, unless the venue's own convention is sentence-case.
- **RULE-H — unsupported claims** (critical): back a factual claim with a citation or concrete evidence, never a handwavy "prior work shows". Never fabricate a citation — verify it exists first, or mark `[UNVERIFIED]`.
- **RULE-I — contractions** (low): full forms in formal prose ("does not", not "doesn't"); contractions are fine in informal registers, held consistently within the document.
- **RULE-J — self-certifying language** (medium): cut "honestly", "frankly", "to be clear" — state the thing plainly instead of announcing that you're being honest about it.
