<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Code Comments and Docstrings Guide

Apply this guide when writing or editing docstrings, inline comments, constants, and type annotations in source code.

## Core Rules

### 1. State the Rule, Not Its History
- Never explain what the code used to do, why a previous bug occurred, or what changed in a recent ticket.
- Ticket IDs (`BOOK-123`), bug post-mortems, and commit rationale belong in git commit messages and PR descriptions, not in code comments.
- Exemption: a test docstring or test comment may cite the ticket the test pins, because the ticket is what tells a later reader why the test exists. Production code comments may not.
- **BAD**:
  ```python
  # BOOK-638 #8: previously matched only an exact Organization/{id} string,
  # so an absolute-URL or otherwise-unnormalized reference silently fell
  # through to organization=None with no log. Normalizes each candidate ref.
  def _match_coverage_organization(...):
  ```
- **GOOD**:
  ```python
  def _match_coverage_organization(...):
      """Match a coverage payor reference against shredded organizations."""
  ```

### 2. Explain *Why* (Invariants), Never *What* (Syntax)
- Do not restate what the code visibly does.
- Document non-obvious business logic, concurrency invariants, rate-limit gates, or external API quirks.
- **BAD**:
  ```python
  # Loop over candidate refs and check if ref is not None
  for ref in candidate_refs:
      if ref: ...
  ```
- **GOOD**:
  ```python
  # -inf ensures the initial heartbeat fires immediately on worker startup.
  self._last_heartbeat_at = float("-inf")
  ```

### 3. Public Contract in Docstrings, Not Internal Mechanics
- Function and method docstrings describe the contract: purpose, arguments, return values, exceptions raised, and pre/post-conditions.
- Do not narrate internal variable assignments, helper selection rationale, or query mechanics.
- **BAD**:
  ```python
  async def _repend_task(...) -> int:
      """Fenced UPDATE that re-pends a task: status -> PENDING, next_retry_at set,
      started_at/claim_token cleared. Shared by _handle_task_failure's 429 branch
      and ordinary-retry branch, which differ only in extra columns...
      Collapsing the shared shape here means a future change won't drift.
      """
  ```
- **GOOD**:
  ```python
  async def _repend_task(...) -> int:
      """Reset a task to PENDING with a new retry timestamp and cleared claim.

      Returns the matched row count (0 if the claim token was invalidated by the reaper).
      """
  ```

### 4. Zero Reviewer Debate and Defensive Justification
- Do not argue against hypothetical alternatives or justify refactor choices to an imaginary reviewer.
- State the design invariant as a fact.
- **BAD**:
  ```python
  # Deliberately NOT derived from is_active/terminal-status generally:
  # ACCEPTED and PARTIALLY_APPROVED are also terminal but must keep taking
  # the no-op path, not be routed into resubmission.
  _RESUBMIT_REQUIRED_STATUSES = frozenset({SubmissionStatus.REJECTED, SubmissionStatus.ERROR})
  ```
- **GOOD**:
  ```python
  # Only unaccepted payer outcomes require bundle resubmission.
  _RESUBMIT_REQUIRED_STATUSES = frozenset({SubmissionStatus.REJECTED, SubmissionStatus.ERROR})
  ```

### 5. Tiered Length Limits
- **Ordinary inline comments**: Maximum 1 to 2 sentences.
- **Constants and enums**: Exactly 1 concise sentence describing the boundary condition or domain constraint.
- **Docstrings**: Maximum 1 short paragraph (3–4 sentences) for standard functions. Use structured sections (`Args:`, `Returns:`, `Raises:`) only when the signature is non-trivial.
- **A named invariant** (a concurrency contract, a lock ordering, a fencing rule): up to 12 lines. Anything a maintainer can get wrong and not find out until production earns the extra lines.
- **An evidence-bearing comment** (states a rule and cites the number or document behind it): up to 4 lines. This tier applies to a new comment as much as to the remnant of a relocated one.
- **Over 12 lines**: the block is a design document in the wrong file. Move it to `docs/` and leave a 2 to 4 line comment stating the rule plus the pointer. See rule 8.

The tiers are a ceiling, not a target. Two sentences that state the invariant beat twelve lines that circle it.

### 6. Punctuation Discipline
- No em-dashes (`—`) or double-hyphens (`--`).
- Use commas, colons, or split into separate sentences. Em-dashes in comments encourage rambling, run-on thoughts.

### 7. Standardized Comment Flags
- Use only `TODO` for deferred work and `BUGBUG` for active defects.
- Never invent bespoke tags (`KNOWN GAP`, `FIXME`, `HACK`, `WORKAROUND`).

### 8. Move Measurements into `docs/`, Keep the Rule in the Comment
- A measurement study (sample sizes, per-variant rates, example identifiers, the query behind them) belongs in the repository's docs, dated, not above the statement it justifies.
- The comment keeps the rule, the single number that makes the rule checkable, and a pointer to the document section holding the rest.
- Never resolve a length limit by deleting the evidence. A constant with no surviving justification gets removed by the next reader.
- **BAD**:
  ```python
  # Measured across the gGastro carriers whose id resolves to exactly one Stedi payer, a
  # 5-char id shares a brand token with Stedi's DisplayName 60.9% of the time; a 4-char id
  # does so 1.4% of the time and a 3-char id 0%. That is a cliff, not a gradient [...]
  # (20 more lines of measurement)
  if len(normalized_id) < _MIN_EDI_PAYER_ID_LENGTH and normalized_id.isdigit():
  ```
- **GOOD**:
  ```python
  # A short all-digit CarrierID is a source-system row number, not a registry key, and
  # matches a Stedi alias only by coincidence. The guard drops 162 joins, 160 of them
  # wrong. Rates per id length: docs/payer-identity-and-matching.md, section 4.
  if len(normalized_id) < _MIN_EDI_PAYER_ID_LENGTH and normalized_id.isdigit():
  ```

### 9. Use a Table for an Enumeration
- Three or more parallel items with the same fields (tiers, states, flags, gates) are a table, not paragraphs. This holds in a comment as much as in a document.
- Docstrings use `Args:`/`Returns:`/`Raises:` for the same reason: fixed fields, scannable.
- **BAD**:
  ```python
  # TIER 1 -- LEAF semaphore (get_ehr_semaphore()). Process-wide, constructed once in the
  #   FastAPI lifespan. One permit == one outbound EHR HTTP send [...]
  # TIER 2 -- SEARCH-LOCAL semaphore (search_local_sem, defined inside [...]
  ```
- **GOOD**:
  ```python
  # Acquisition order is strictly 3 -> 2 -> 1. Three distinct objects, never one nested.
  #   3  fanout_sem          per call    bounds per-reference fan-out in fetch_ref
  #   2  search_local_sem    per call    bounds fetch_one over a warm query cache
  #   1  get_ehr_semaphore() per process bounds outbound EHR sends
  ```

### 10. No Banner Art or Shouty Capitals
- No box banners (`═══`, `***`, ASCII rules) around a comment block.
- No ALL CAPS for emphasis (`WHY:`, `THREE DISTINCT`, `THIS IS THE CANONICAL COPY`). Capitals are correct only for identifiers that are genuinely uppercase (`QUEUED`, `NULL`, `TODO`).
- A banner invites growth: once a block has one, later additions land inside it instead of beside it.

