<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Code Comments and Docstrings Guide

Apply this guide when writing or editing docstrings, inline comments, constants, and type annotations in source code.

## Core Rules

### 1. State the Rule, Not Its History
- Never explain what the code used to do, why a previous bug occurred, or what changed in a recent ticket.
- Ticket IDs (`BOOK-123`), bug post-mortems, and commit rationale belong in git commit messages and PR descriptions, not in code comments.
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

### 5. Strict Length Limits
- **Inline comments**: Maximum 1 to 2 sentences.
- **Constants and enums**: Exactly 1 concise sentence describing the boundary condition or domain constraint.
- **Docstrings**: Maximum 1 short paragraph (3–4 sentences) for standard functions. Use structured sections (`Args:`, `Returns:`, `Raises:`) only when the signature is non-trivial.

### 6. Punctuation Discipline
- No em-dashes (`—`) or double-hyphens (`--`).
- Use commas, colons, or split into separate sentences. Em-dashes in comments encourage rambling, run-on thoughts.

### 7. Standardized Comment Flags
- Use only `TODO` for deferred work and `BUGBUG` for active defects.
- Never invent bespoke tags (`KNOWN GAP`, `FIXME`, `HACK`, `WORKAROUND`).
