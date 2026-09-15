---
name: Code Comments and Docstrings
description: Concise docstrings and inline comments focused on contracts and invariants — zero changelog history, zero reviewer debate, no em-dashes
keep-coding-instructions: true
---

Write code comments and docstrings that optimize for clarity, low cognitive load, and long-term maintainability.

## Core Rules

- **State the rule, not its history**: Never write what the code used to do, why an old bug happened, or cite ticket numbers (e.g. `BOOK-123`). Commit messages and PRs own history; code comments own current invariants.
- **Explain *Why*, not *What***: Never rephrase the code in English. Comment only non-obvious business logic, boundary conditions, or concurrency invariants.
- **Zero reviewer debate**: Do not justify design choices against hypothetical future refactors or argue with imaginary reviewers ("collapsing this helper ensures X won't drift..."). State the rule directly.
- **No em-dashes**: Do not use em-dashes (`—`) or double hyphens (`--`). Use commas, colons, or start a new sentence.

## Docstrings

- **Focus on the public contract**: Document parameters, return values, raised exceptions, and state pre/post-conditions.
- **Keep internals out of docstrings**: Do not explain internal variable assignments, query shapes, or step-by-step implementation details in the function docstring.
- **Imperative summary**: Begin with a crisp, one-line summary in the imperative mood (`"Return the matching patient record."`, not `"This function returns..."`).
- **Length limit**: Keep docstrings under one short paragraph unless documenting a complex public API boundary.

## Inline Comments & Constants

- **Length limit**: Maximum 1 to 2 sentences per comment block.
- **Constants and enums**: Document the domain constraint or boundary condition in a single concise sentence.
- **Flag words**: Use only `TODO` for deferred work and `BUGBUG` for active defects. Never invent bespoke flags.
