<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# The Elements of Agent Style — Rules

Full detail behind [`SKILL.md`](SKILL.md)'s rule index: source, one directive, two BAD→GOOD examples (one engineering-doc context, one non-technical-reader context, where the rule benefits from showing both), and one line of rationale. Every rule shares the same scope (engineering docs, comments, commit/PR/issue text, changelogs, runbooks, postmortems, explainers for non-technical readers) unless noted otherwise, and the same severity scale:

- **critical** — reader cannot understand or trust the prose if violated.
- **high** — externally visible AI-tell, or a recurring failure that breaks skim-reading.
- **medium** — local readability cost, felt but not a trust issue.
- **low** — polish or preference.

> *"Break any of these rules sooner than say anything outright barbarous."* — George Orwell, "Politics and the English Language" (1946), Rule 6.

## Canonical rules

### RULE-01: Resist the Curse of Knowledge (critical)

**Source:** Pinker 2014, Ch. 3.
**Directive:** Name the intended reader before writing (on-call engineer, non-technical stakeholder, new teammate). Do not use a term that reader hasn't been given, and do not launch into mechanics before stating the purpose.

- BAD (runbook): `If the queue is backed up, bounce the workers and clear the dead-letter.`
  GOOD (runbook): `If RabbitMQ queue depth exceeds 10k messages for 5+ minutes: (1) restart the Celery worker pool so new brokers pick up rebalanced connections, (2) drain the dead-letter queue so failed messages don't replay against the fresh workers.`
- BAD (for a non-technical reader): `We added idempotency keys to the payment endpoint to prevent duplicate charges from retries.`
  GOOD (for a non-technical reader): `If a customer's payment request times out and their app retries it, we now recognize the retry and charge them once, not twice.`

An LLM writes at the register of its training corpus by default, with no signal for whether the actual reader shares that background — a gap invisible to the writer and glaring to the reader.

### RULE-02: Avoid Passive Voice When the Agent Matters (high)

**Source:** Orwell 1946 Rule 3; Strunk & White §II.14.
**Directive:** Write "Y did X", not "X was done by Y", when the agent is known. Passive is correct when the agent is genuinely unknown or irrelevant — use it deliberately, not by default.

- BAD: `Errors are logged to /var/log/app.log when the service restarts.`
  GOOD: `The service logs errors to /var/log/app.log on restart.`
- BAD (postmortem): `The incident was caused by a misconfigured load balancer rule.`
  GOOD (postmortem): ``A misconfigured load balancer rule (typo in the ingress-nginx path-rewrite regex) routed `/auth/*` to the wrong upstream.``

Passive hides the agent and forces the reader to reconstruct who did what — costly in postmortems and bug reports specifically, where the actor is the diagnosis.

### RULE-03: Prefer Concrete Language over Abstraction (high)

**Source:** Strunk & White §II.16; Pinker 2014 Ch. 3.
**Directive:** Replace category words ("factors", "aspects", "considerations", "issues") with the specific items behind them. If naming the specifics takes more than one clause, the sentence was hiding the work — do it anyway.

- BAD: `The checkout endpoint has performance issues.`
  GOOD: `The checkout endpoint's p95 latency rose from 120ms to 450ms at 14:00 UTC.`
- BAD (API doc): `Authentication handles multiple scenarios.`
  GOOD (API doc): `Authentication supports three flows: OIDC authorization code (first-party web), client_credentials (service-to-service), and refresh-token rotation (mobile).`

A careful reader who hits "various factors" and finds nothing behind it discounts the rest of the document.

### RULE-04: Omit Needless Words (high)

**Source:** Strunk & White §II.17; Orwell 1946 Rule 3.
**Directive:** Cut stretched phrases: "in order to" → "to"; "due to the fact that" → "because"; "at this point in time" → "now"; "it is important to note that" → delete and state the fact; "may potentially" / "could possibly" → pick one hedge, not both.

- BAD: `It is important to note that the connection pool size was reduced in order to prevent exhaustion under load.`
  GOOD: `We reduced the connection pool size to prevent exhaustion under load.`
- BAD (PR description): `This PR makes some minor adjustments in order to fix an issue that was causing failures in certain test cases.`
  GOOD (PR description): ``Fixes a null-pointer crash in `test_checkout_flow` when the cart has a single item.``

These phrases carry no technical content; each is a pure length tax the reader pays for nothing.

### RULE-05: Avoid Dying Metaphors and Prefabricated Phrases (high)

**Source:** Orwell 1946 Rule 1.
**Directive:** Cut any metaphor or phrase you've seen often in print ("pushes the boundaries", "unlocks the full potential", "best-in-class"). Replace with a specific number, comparison, or mechanism, or delete the sentence outright.

- BAD (design doc): `This architecture unlocks the full potential of our data pipeline.`
  GOOD (design doc): `This architecture lets the pipeline process 3x the record volume without adding worker nodes.`
- BAD (release note): `This release delivers significant improvements to user experience and performance.`
  GOOD (release note): `Reduce p99 dashboard load latency from 820ms to 240ms. Fix a crash in CSV export when a cell contains an embedded newline.`

If you can't replace the cliché with a specific number or mechanism, the cliché was hiding the absence of one.

### RULE-06: Avoid Avoidable Jargon (medium)

**Source:** Orwell 1946 Rule 5; Pinker 2014 Ch. 2.
**Directive:** "leverage" → "use"; "utilize" → "use"; "methodology" → "method"; "functionality" → "function"/"feature"; "operationalize" → "start"/"build". Keep jargon that carries distinct technical meaning ("idempotency key", "connection pooling") — the rule targets substitutable corporate-speak, not necessary terms of art.

- BAD: `We leverage a retry queue to facilitate delivery of failed webhooks.`
  GOOD: `We use a retry queue to redeliver failed webhooks.`
- BAD (changelog): `The system has been optimized to efficiently utilize available resources in a more performant manner.`
  GOOD (changelog): `Reduce memory footprint from 1.2GB to 380MB at idle by lazy-loading the embedding cache.`

An experienced reader mentally substitutes the shorter word anyway, so the longer one buys nothing.

### RULE-07: State Claims in Positive Form (medium)

**Source:** Strunk & White §II.15.
**Directive:** "not important" → "trivial"; "did not remember" → "forgot"; prefer one affirmative word over two negating ones. At the clause level, don't stage a claim as "X, not Y" / "not just X, but Y" for cadence — state the claim directly, and keep a contrast only when the rejected alternative is specific and informs the reader ("the bottleneck is disk I/O, not CPU").

- BAD: `Startup time is not as slow as in the previous release.`
  GOOD: `Startup time drops from 4.2s to 1.8s by deferring the plugin scan to first interactive action.`
- BAD (antithesis, heading): `The Outage Was Caused by the Retry Storm, Not the Deploy`
  GOOD (antithesis, heading): `A Retry Storm, Not the Deploy, Caused the Outage` *(keep only if "not the deploy" rules out something the reader would otherwise suspect; otherwise drop the tail entirely.)*

Double negation costs the reader a hold-then-invert step; antithesis for cadence invents a foil that adds rhythm, not information.

### RULE-08: Calibrate Claims to the Evidence (high)

**Source:** Pinker 2014 Ch. 6; Gopen & Swan 1990.
**Directive:** Match the verb to the evidence: a measured result "shows" or "measures"; an inference from logs "suggests" or "indicates" (pending confirmation). Don't overclaim ("fixes the root cause" for "fixes one reproduction") or underclaim via reflexive hedging ("it might be worth considering" for "we should do X").

- BAD (PR description): `This refactor future-proofs the payment service.`
  GOOD (PR description): `This refactor separates the payment-provider adapter from the checkout flow, so adding a new provider no longer requires touching checkout code.`
- BAD (issue report): `Everything is broken; nothing works.`
  GOOD (issue report): ``/auth/login returns 500 for all requests after the 2026-04-18 deploy. /auth/logout and /auth/refresh unaffected.``

A technical reader scans for unwarranted "fixes" or "best" and discounts the rest of the document once found.

## Sentence Structure

### RULE-09: Express Coordinate Ideas in Similar Form (medium)

**Source:** Strunk & White §II.19.
**Directive:** In a list or a set of items joined by "and"/"or", give every item the same grammatical form — all noun phrases, or all verb-initial clauses, not a mix.

- BAD: `The pipeline cleans the data, feature extraction, and then trains the model.`
  GOOD: `The pipeline cleans the data, extracts features, and trains the model.`
- BAD (API doc): `The endpoint accepts JSON input, you get XML back, and pagination is via cursor.`
  GOOD (API doc): `The endpoint accepts JSON input, returns XML output, and paginates by cursor.`

A reader forms an expected shape from item 1; a mismatched item 2 forces a backtrack and reparse.

### RULE-10: Keep Related Words Together (medium)

**Source:** Strunk & White §II.20; Gopen & Swan 1990.
**Directive:** Keep subject close to verb, verb close to object. When a long parenthetical would separate them, move it to the end of the sentence or split into two sentences. Rough test: more than 8 words between subject and verb — split.

- BAD (postmortem): `The database replica, which had been failing its health checks intermittently for three days before the outage but was never promoted to primary because of a misconfigured priority setting, was the direct cause of the outage.`
  GOOD (postmortem): `The database replica was the direct cause of the outage. It had been failing health checks intermittently for three days; a misconfigured priority setting prevented promotion to primary during that period.`

The reader holds the subject in working memory until the verb arrives; a long intervening clause risks losing it.

### RULE-11: Put New Information in the Stress Position (medium)

**Source:** Gopen & Swan 1990.
**Directive:** End a sentence with the fact you want remembered. If the key fact sits mid-sentence, move it to the end. Applies especially to result sentences, conclusions, and root-cause lines.

- BAD (commit message): `Fix for issue where users occasionally see a blank page in the dashboard when their session has expired and they try to navigate to a protected route.`
  GOOD (commit message): `On expired-session navigation to a protected route, redirect to /login instead of rendering a blank dashboard frame.`

Gopen & Swan show readers expect new information at the sentence's end; front-loading it and tailing off into old material reads as flat and forces a re-read.

### RULE-12: Break Long Sentences; Vary Length (high)

**Source:** Strunk & White §II.18; Pinker 2014 Ch. 4.
**Directive:** Split any sentence over 30 words. Vary sentence length across a paragraph — a run of same-length sentences reads as monotone even when each one is fine on its own.

- BAD (design doc, 38 words): `The ingestion pipeline processes incoming records in batches of one thousand items, stores them in the primary document store, and maintains an index on the timestamp field that supports the range queries the dashboard relies on for reporting.`
  GOOD (design doc, three sentences): `The ingestion pipeline processes incoming records in batches of a thousand. It writes them to the primary document store, which keeps a timestamp index. The dashboard's range queries rely on that index.`

Long sentences with nested clauses tax the reader's parsing budget past the point where the sentence's own logic can carry it.

## Field-Observed Rules

The next ten rules (RULE-A–J) come from observing LLM output across writing projects and code releases, 2022–2026 — not drawn from a cited authority, but treated as binding alongside the 12 canonical rules above.

### RULE-A: Don't Convert Prose into Bullets Unless It's a Genuine List (medium)

**Directive:** Keep prose in paragraphs when ideas connect by cause, argument, or narrative. Use bullets only for genuinely parallel enumerations (endpoints, config options, checklist steps). Don't force a 3-item "first, second, third" triad where 2 items or a plain sentence fit.

- BAD (design doc): a 4-bullet list where each bullet is a clause of one causal sentence ("Two-tower retrieval" / "Because the query embedding caches" / "And the document index updates nightly" / "Without re-running inference").
  GOOD (design doc): `We chose two-tower retrieval because the query embedding caches across sessions and the document index updates nightly without re-running inference.`

Bullets read as "organized," so models reach for them by default — but each bullet strips the connective tissue (because, therefore) the argument needs.

### RULE-B: Don't Use Em/En Dashes as Casual Punctuation (medium)

**Directive:** Use a comma for an appositive, a semicolon for linked independent clauses, a colon for an expansion, parentheses for an aside — not an em or en dash. Numeric ranges (`2020-2026`) and paired names are unaffected; those are hyphens, not this rule's target.

- BAD: `The deploy rolled back automatically — because the health check failed — within 90 seconds.`
  GOOD: `The deploy rolled back automatically because the health check failed, within 90 seconds.`

LLMs produce dashes at several times a skilled human writer's rate, and readers now recognize the cadence as an AI-tell.

### RULE-C: Don't Start Consecutive Sentences with the Same Word (medium)

**Directive:** Vary the opener across consecutive sentences — pronoun subjects ("It", "We", "The") are the most common offenders once a fluent opener gets reused.

- BAD (postmortem): `It started at 14:00 UTC. It lasted 37 minutes. It affected 12% of users.`
  GOOD (postmortem): `The incident started at 14:00 UTC, lasted 37 minutes, and affected 12% of users.`

Once an opener works, next-token sampling keeps reusing it — the paragraph reads as template-filled even when each sentence is individually correct.

### RULE-D: Don't Overuse Transition Words (medium)

**Directive:** Don't open a sentence with "Additionally"/"Furthermore"/"Moreover"/"In addition"/"Notably" unless the logical move (contrast, concession) genuinely needs flagging — usually the content alone makes the connection.

- BAD (release note): `This release adds OAuth support. Additionally, it fixes the CSV export crash. Furthermore, it improves startup time.`
  GOOD (release note): `OAuth support lands in this release. The CSV export crash is fixed. Startup time drops from 4.2s to 1.8s.`

These transitions appear at far higher frequency in LLM output than in skilled technical prose, producing a distinctive, recognizable cadence.

### RULE-E: Don't Close Every Paragraph with a Summary Sentence (medium)

**Directive:** Don't end a body paragraph with a sentence restating its own point ("In summary, ...", "Overall, this means ..."). Reserve summary closers for the final paragraph of a piece, or a long section meant to be skimmed. Test: if deleting the closer leaves the point intact, delete it.

- BAD (design doc): `We chose two-tower retrieval because query embeddings cache across sessions. Thus, the architecture is well-suited to our caching strategy.`
  GOOD (design doc): `We chose two-tower retrieval because query embeddings cache across sessions.`

The closer signals "I am finishing this thought" without adding information; a skimming reader has already moved on.

### RULE-F: Keep Terms Consistent; Don't Redefine Abbreviations Mid-Document (medium)

**Directive:** Once a term or abbreviation is defined, keep using that exact form. Don't alternate synonyms for the same thing ("the gateway" / "the ingress layer" / "the front door"), and don't re-expand an abbreviation already defined earlier.

- BAD (API doc): `The /users endpoint returns user objects. ... later ... The user endpoint supports filtering. ... later ... Our user resource accepts query parameters.`
  GOOD (API doc): `The /users endpoint returns user objects. ... later ... /users supports filtering. ... later ... /users accepts query parameters.`

Varied terminology masks whether a new term is the same entity or a new one, forcing the reader to check each time.

### RULE-G: Title-Case Section Headings (low)

**Directive:** Capitalize first word, last word, and all major words in headings; lowercase articles, coordinating conjunctions, and short prepositions. Applies to Markdown/RST headings unless the repo's own convention is sentence-case — check existing docs before applying.

- BAD (README): `## Getting started with the API`
  GOOD (README): `## Getting Started with the API`

LLMs default to sentence-case headings from docs-site training data; in a title-case repo this reads as unedited.

### RULE-H: Support Claims with Citation or Concrete Evidence (critical)

**Directive:** When a sentence asserts a factual claim that warrants attribution (a vendor's behavior, an RFC requirement, a measured result), name the specific source or give the concrete evidence (a number, a log line, an observed test run) — never a handwavy "it's generally known that" or "this should be faster". Never invent a source: verify it exists (the vendor's own docs, the RFC text, your own test output) before citing it, or mark `[UNVERIFIED]`.

- BAD (design doc): `Most providers rate-limit aggressively, so we should cache aggressively too.`
  GOOD (design doc): `Stripe's rate limit is 100 req/s per account (per their API docs); we cache idempotent GETs for 60s to stay well under it.`
- BAD (commit message): `Fix based on user feedback.`
  GOOD (commit message): `Fix null-pointer crash reported in issue #1847 (reproducible with an empty cart).`

An uncited claim is unverifiable; a fabricated source is worse, since it destroys reader trust permanently once caught. Related: RULE-03 fights vague nouns and RULE-08 fights uncalibrated verbs — a single sloppy sentence often trips all three.

### RULE-I: Prefer Full Forms over Contractions in Formal Prose (low)

**Directive:** In formal technical prose (specs, API docs, formal design docs), write "it is" not "it's", "cannot" not "can't". Contractions are fine in informal registers (release notes, commit messages) — pick a register and hold it within one document.

- BAD (API spec): `If the request body can't be parsed, the endpoint won't return a 200 response.`
  GOOD (API spec): `If the request body cannot be parsed, the endpoint does not return a 200 response.`

A contraction inside otherwise-formal prose reads as a register break, even though the meaning parses fine either way.

### RULE-J: Don't Use Self-Certifying Language (medium)

**Directive:** Cut "honestly", "frankly", "candidly", "to be clear", "truthfully". State the thing plainly instead of announcing that you're about to be honest about it. Still state limitations and corrections — just without the announcement.

- BAD (PR description): `Honestly, this migration was trickier than expected and touches more files than I'd like.`
  GOOD (PR description): `This migration touches 14 files, more than planned, because the schema change cascades through three downstream views.`
- BAD (postmortem): `To be clear, the root cause was a missing index, not the query itself.`
  GOOD (postmortem): `The root cause was a missing index, not the query itself.`

The qualifier implies every other sentence might not be honest, and adds nothing the plain statement doesn't already carry.
