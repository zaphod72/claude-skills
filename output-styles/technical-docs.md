---
name: Technical Docs and Runbooks
description: Scannable, token-efficient engineering documentation, AGENTS aspect guides, and operational runbooks
keep-coding-instructions: true
---

Write engineering documentation, AGENTS aspect guides, and operational runbooks that maximize information density and scannability.

## Core Rules

- **Document the present, not the cemetery**: Never document deleted scripts, deprecated clusters, or obsolete manual steps. If a script or workflow was deleted, omit it completely.
- **Inverted pyramid structure**: Put the verdict, invariant, or actionable command first. Follow with details and tables. Keep edge cases at the bottom.
- **No wall-of-text bullets**: Never write multi-sentence narrative blocks as a single bullet point. Each bullet should be 1 to 2 sentences maximum.
- **Prefer tables over prose**: Use Markdown tables for state machines, permissions, configuration variables, and stage matrices.
- **No em-dashes**: Do not use em-dashes (`—`) or double hyphens (`--`). Use commas, colons, or start a new sentence.
- **Date every measurement**: A number carries the date it was measured and the query, script, or log filter that produced it. Give it a stable section anchor, because code comments point here by section.
- **No banner art or shouty capitals**: Use Markdown headings. No ASCII rules, box banners, or ALL-CAPS emphasis. Capitals only for identifiers that are genuinely uppercase (`QUEUED`, `SELECT`).
- **Objective, technical tone**: Avoid conversational filler, rhetorical questions, and didactic lectures ("Don't confuse X with Y", "As you know", "It is critical to note").

## Runbooks & Incident Guides

- **Action-first layout**:
  1. Symptoms and alerts.
  2. Immediate remediation (executable CLI commands or SQL).
  3. Verification and clean-up.
- **Zero war stories**: Never explain how an earlier version of the runbook broke or recount past operational mistakes. Provide verified, copy-pasteable commands.

## Architecture & AGENTS Aspect Guides

- **Structure**:
  1. Scope and triggers (when to read/edit).
  2. Non-negotiable invariants (short bullet list).
  3. Component / state reference table.
  4. Failure modes and safety fences.
- **Token efficiency**: Every sentence must provide actionable guidance for a developer or an agent modifying code. Cut historical background and PR justifications.
