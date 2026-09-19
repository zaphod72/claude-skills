---
name: agent-style
description: "Literature-backed prose rules for engineering documents a human reads later: READMEs, code comments, commit/PR/issue text, changelogs, runbooks, postmortems, and docs that explain technical work to a non-technical reader. Apply as a pass after drafting such a document. Not for the chat reply itself; the active output style governs that."
---

agent-style (v0.6.0, +RULE-N-O) is 27 rules against recurring failure patterns in LLM-written technical prose: 12 canonical rules from Strunk & White, Orwell, Pinker, and Gopen & Swan, plus 15 patterns observed directly in LLM output, 2022–2026. Run it as one pass over a finished draft, not as 27 separate steps.

**Escape hatch:** *"Break any of these rules sooner than say anything outright barbarous."* — Orwell, 1946. Rules serve clarity; drop one when it fights the sentence.

**Scope & output styles:** Full rule citations, severity, and BAD→GOOD examples: [`RULES.md`](RULES.md). Match the document type to its guide and recommended output style:

| Document Type | Detailed Guide | Output Style (`/output-style <name>`) |
|---|---|---|
| Code comments, docstrings, invariants | [`code-comments.md`](code-comments.md) | [`code-comments`](../../output-styles/code-comments.md) |
| Engineering docs, runbooks, AGENTS files | [`repo-docs.md`](repo-docs.md) | [`technical-docs`](../../output-styles/technical-docs.md) |
| Commit/PR text, changelogs, postmortems, chat | [`RULES.md`](RULES.md) | [`plain-english`](../../output-styles/plain-english.md) |

## Canonical rules

- **RULE-01 — curse of knowledge** (critical): name a concrete reader; define or cut any term that reader would have to look up.
- **RULE-02 — passive voice** (high): name the agent ("Y did X", not "X was done by Y") unless the agent is genuinely unknown or irrelevant.
- **RULE-03 — abstraction** (high): replace category words ("factors", "issues", "considerations") with the specific thing behind them.
- **RULE-04 — needless words** (high): cut filler: "in order to", "due to the fact that", "it is important to note that".
- **RULE-05 — dying metaphors** (high): cut clichés ("pushes the boundaries", "paradigm shift"); state the number, comparison, or mechanism instead.
- **RULE-06 — avoidable jargon** (medium): "leverage" → "use", "utilize" → "use", "methodology" → "method". Keep jargon that carries distinct technical meaning.
- **RULE-07 — positive form** (medium): "not large" → "small"; don't stage a claim as "X, not Y" unless the rejected Y is specific and informative.
- **RULE-08 — claim calibration** (high): match the verb to the evidence, "suggests"/"shows" for results, "proves" only for derivations; name the source instead of "prior work shows".
- **RULE-09 — parallel structure** (medium): coordinate items (bullets, "and"/"or" lists) share one grammatical form.
- **RULE-10 — related words together** (medium): keep subject next to verb; move a long parenthetical to the sentence's end or a new sentence.
- **RULE-11 — stress position** (medium): put the fact you want remembered at the sentence's end, not buried mid-sentence.
- **RULE-12 — sentence length** (high): split sentences over 30 words; vary length across a paragraph.

## Field-observed rules

- **RULE-A — unsupported claims** (critical): back a factual claim with a citation or concrete evidence, never a handwavy "prior work shows". Never fabricate a citation. Verify it exists first, or mark `[UNVERIFIED]`.
- **RULE-B — changelog narration** (critical): don't narrate past bugs, what the code used to do, or ticket numbers in code comments or docs. State current behavior, not what changed. Three exemptions: a test docstring may cite the ticket it pins, a commit or PR title may carry a ticket key where the repo's convention uses one, and a guide to queryable historical data may date a cutover, written as a property of the rows.
- **RULE-C — tombstone documentation** (critical): never document deleted scripts, decommissioned clusters, or obsolete manual steps. Document current reality only.
- **RULE-D — reviewer debate** (high): don't argue with imaginary reviewers or justify choices against hypothetical future refactors. State the invariant, not the debate.
- **RULE-E — bullet overuse** (medium): keep argued or causal prose in sentences; bullets only for genuine parallel enumerations. Don't force a 3-item triad where 2 items or one sentence fit.
- **RULE-F — dash punctuation** (medium): no em/en dash as casual punctuation; use a comma, semicolon, colon, or parentheses instead. (Numeric ranges, paired names, attributions, and a label-separator dash like "RULE-01 — curse of knowledge" are fine.)
- **RULE-G — same-word openers** (medium): don't start two consecutive sentences with the same word.
- **RULE-H — transition overuse** (medium): don't open a sentence with "Additionally"/"Furthermore"/"Moreover" unless the logical move genuinely needs flagging.
- **RULE-I — summary closers** (medium): don't end every paragraph with a sentence that restates its own point.
- **RULE-J — term consistency** (medium): once a term or abbreviation is defined, keep using that exact form: no synonym drift, no re-defining it later.
- **RULE-K — self-certifying language** (medium): cut "honestly", "frankly", "to be clear". State the thing plainly instead of announcing that you're being honest about it.
- **RULE-L — heading case** (low): title-case section headings, unless the venue's own convention is sentence-case.
- **RULE-M — contractions** (low): full forms in formal prose ("does not", not "doesn't"); contractions are fine in informal registers, held consistently within the document.
- **RULE-N — evidence altitude** (high): keep the rule and one checkable number in the comment; move the full measurement to the docs and point at it. Never delete evidence to satisfy a length limit.
- **RULE-O — banner art and caps** (medium): no box banners or ALL-CAPS emphasis; use a heading, a bold label, or plain sentence order.
