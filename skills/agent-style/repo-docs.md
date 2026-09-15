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
