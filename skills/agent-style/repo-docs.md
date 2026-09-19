<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Repository Documentation and Runbooks Guide

Apply this guide when writing or editing documentation in `docs/`, root architectural guides, and `AGENTS.*.md` aspect files.

## Core Rules

### 1. Document the Present, Not the Cemetery
- Never document deleted files, retired scripts, decommissioned databases, or legacy architectural paths.
- If a script or cluster is gone, remove all references to it. Git history retains the record; current documentation describes only active systems.
- **BAD**:
  ```markdown
  Both predecessors are deleted from the repo: scripts/configure_alloydb_permissions_shared_cluster.sh
  (the shared-cluster script, hand-run through a bastion tunnel as a human DBA) and, earlier,
  scripts/configure_alloydb_permissions.sh (targeting the legacy bknd cluster no workspace uses).
  ```
- **GOOD**:
  ```markdown
  Database permissions and role memberships are managed declaratively in
  `terraform-spoke/alloydb_grants.tf` and applied automatically during deployment.
  ```

### 2. Inverted Pyramid Structure
- Place the core invariant, conclusion, or actionable command in the very first sentence.
- Follow with supporting details, schemas, and tables. Keep edge cases, background, and failure thresholds at the bottom.
- Never force an on-call engineer or busy developer to read through three introductory paragraphs to find the command or rule.

### 3. High Scannability Over Narrative Walls
- Never write 15–20 line narrative blocks inside a single bullet point.
- Keep bullet points to 1 to 2 sentences maximum.
- Use Markdown tables for state transitions, permission matrices, environment variables, and configuration flags.
- **BAD**:
  ```markdown
  - CAS transitions: Each move is UPDATE ... WHERE state = ANY(<expected>) AND current_stage = <stage>
    with RETURNING to detect the winner. The current_stage term stops a late stage-N callback from
    matching a row already advanced to N+1. Fence.at takes one stage, not a set, and distinguishes
    three shapes a caller can express: omitted (no stage term at all — only the planning claim wants
    that), explicit None (a real current_stage IS NULL expectation), and a named stage. Eleven states,
    one column: QUEUED → PLANNING → IN_PROGRESS → FINALIZING...
  ```
- **GOOD**:
  ```markdown
  ### Queue State Transitions (CAS)
  Every transition executes `UPDATE pipeline_queue WHERE state = ANY(...) AND current_stage = ... RETURNING ...`.

  - **`stage=None`**: Expects `current_stage IS NULL`.
  - **`stage="<name>"`**: Matches the current stage to prevent late callbacks from earlier stages.
  - **Omitted stage**: Used only during planning claims.
  ```

### 4. Action-First Runbooks
- Runbooks are emergency tools for humans under stress.
- Structure every runbook section into:
  1. **Symptoms & Alerts**: What broke and how to identify it.
  2. **Remediation**: Copy-pasteable CLI commands or SQL queries.
  3. **Verification**: How to confirm the system recovered.
- **Zero war stories**: Never narrate past incident mistakes or why an earlier version of a query broke.
- **BAD**:
  ```markdown
  A raw UPDATE against this table bypasses clean-state guarantees — an earlier version of
  this runbook's raw SQL referenced a force_reextract column that has never existed, so an
  operator following it got column "force_reextract" does not exist, not a recovery. Use admin_cli.py.
  ```
- **GOOD**:
  ```markdown
  > [!CAUTION]
  > Do not execute manual SQL updates against `pipeline_queue`. Always use `admin_cli.py` to reset runs.
  
  ```bash
  python scripts/admin_cli.py pipeline reset <patient_id> --stage <current_stage>
  ```
  ```

### 5. Objective Technical Voice
- Avoid conversational banter, rhetorical questions, and didactic lecturing ("Don't confuse X with Y", "As you know", "New to this codebase? Start here.").
- Write in clear, declarative technical English.
- Avoid casual em-dashes (`—`) or double-hyphens (`--`). Use commas, colons, or start new sentences.

### 6. AGENTS Aspect Files Discipline
- `AGENTS.*.md` files are read by AI coding agents. Every wasted token dilutes context.
- Keep aspect files compact, factual, and strictly invariant-driven.
- Focus on: (1) Triggers/scope, (2) Non-negotiable rules, (3) Component/state tables, (4) Safety fences.

### 7. Describe a Data Cutover as a Property of the Rows
- A guide to data a reader will query (logs, a warehouse table, an archive) may state a cutover, because the reader is choosing a time range across it. Name the date, and the deploy or ticket if that is what dates it.
- Write what the rows carry, not what the code did. The reader queries rows.
- **BAD**: `Routed through log_decision as of BOOK-943 — previously a raw log.info regardless of outcome, so this fail event logged at INFO and was invisible.`
- **GOOD**: `Rows written before the BOOK-943 deploy are a raw log.info at INFO regardless of outcome, so a severity>=WARNING pull misses this fail event.`

### 8. Date Every Measurement and Name the Query Behind It
- `docs/` is where a measurement relocated out of a code comment lands (see `code-comments.md` rule 8). It has to arrive maintainable.
- Every number carries the date it was measured and the query, script, or log filter that produced it. Re-run before reusing it in a new argument.
- Give the measurement a stable section anchor, because a code comment points at it by section.
- **BAD**:
  ```markdown
  Short numeric carrier ids match Stedi payers badly, so the resolver filters them.
  ```
- **GOOD**:
  ```markdown
  ### 4. Carrier ID Length and Match Quality
  As of 2026-08-11, across gGastro carriers resolving to exactly one Stedi payer:
  a 5-character id shares a brand token with Stedi's `DisplayName` 60.9% of the time,
  a 4-character id 1.4%, a 3-character id 0%. Query: section 4.2.
  ```

### 9. No Banner Art or Shouty Capitals
- Use Markdown headings for structure. No ASCII rules, box banners, or ALL-CAPS emphasis.
- Capitals stay for identifiers that are genuinely uppercase (`QUEUED`, `NULL`, `SELECT`).

