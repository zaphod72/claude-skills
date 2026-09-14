# Claude Skills — Agent Guide

This repo holds the Claude Code skills, rules, output styles, and agent definitions used
across Bookend repos. `README.md` is the human-facing index of what each skill does and
when to reach for it — read it for that; this file covers what an edit here implies and
how to verify one.

## Layout

| Dir | What lives there | Owned or vendored |
|---|---|---|
| `skills/` | One `SKILL.md` per skill dir, some with a `references/` folder disclosed from it | Owned |
| `rules/` | Standalone convention docs, always-on unless scoped by `paths:` frontmatter | Owned |
| `output-styles/` | Chat-reply output styles | Owned |
| `agents/` | `plan-rollout-{slc,coder,reviewer,auditor}` subagent definitions (frontmatter + prose) | Owned |
| `.github/workflows/ci.yml` | Runs `skill-check` over the repo on every PR | Owned |
| `skill-check.config.json` | skill-check rule overrides — read it, don't guess the settings | Owned |

Every `skills/*` entry is owned by this repo. Skills this repo depends on but does not
own — `mattpocock-skills:tdd`, `mattpocock-skills:writing-for-agents`, and others — come
from the `mattpocock-skills` plugin instead of a vendored directory here; a citation of
one of those always carries the `mattpocock-skills:` prefix. See `README.md`'s Install
section for which plugin skills this repo cites and the pinned version they were cited
against.

## Install implies live edits

`~/.claude/skills`, `~/.claude/rules`, `~/.claude/output-styles`, and `~/.claude/agents`
are symlinks into this repo's matching directories — nothing is copied. An edit here goes
live for every Claude session on the machine the moment it lands: every `SKILL.md`
description sits in every session's skill list, a `rules/*.md` with no `paths:`
frontmatter loads into every session, and one with `paths:` loads whenever a matching file
is in play. A half-written description or a broken frontmatter block degrades those
sessions immediately, not just work in this repo.

Consequence: edit on a branch, and keep the working tree coherent at every commit — no
half-written skill or malformed frontmatter left in place overnight or between commits.

## Editing rules

- State the rule, not its history. No "previously", "used to", "no longer", "replaces" —
  that belongs in the commit message and PR body, never in skill text, this file, or
  `rules/`.
- Code comment flags: only `TODO` and `BUGBUG` — see `rules/comment-flags.md`. No invented
  labels.
- Run the `mattpocock-skills:writing-for-agents` skill as a pass over every `SKILL.md`,
  reference file, or agent definition you edit.
- Editing anything under `skills/**/*.md`: read `rules/skill-authoring.md` first. It
  documents a positional-argument substitution trap in fenced code blocks and a BSD- vs
  GNU-tool portability gap, both silent at review time.
- Commit by explicit path. Never `git add -A`, never `git stash` — this working tree is
  shared by parallel agents, and `refs/stash` is one ref for the whole repo, not
  branch-scoped.
- Conventional-commit messages, each ending with the `Co-Authored-By:` line the session's
  attribution reminder supplies (the model name in it varies by session).
- Each `plan-rollout` actor reads only its own reference file; a brief names that file by
  path rather than restating its content. See `skills/plan-rollout/SKILL.md` for the actor
  table and which reference file backs which actor.
- Jira tickets are `BOOK-*` on `panape.atlassian.net`.

## Verification before opening a PR

- `python3 -m unittest discover -s skills/plan-rollout/scripts -p 'test_*.py' -t .` from
  the repo root — tests for `rollout-db`, the plan-rollout ledger CLI. Stdlib-only; there
  is no pytest in this repo.
- Confirm skill-check passes. CI is the real gate: `.github/workflows/ci.yml` runs
  `thedaviddias/skill-check@v1.2.0` over the whole repo on every PR. Locally, if `npx` is
  available, spot-check one skill dir first:
  `npx skill-check@1.2.0 check <skill dir> --format text --no-security-scan`.

## plan-rollout runtime state

This skill is loaded live via symlinks (`~/.claude/skills`, `~/.claude/agents`) into this
repo's working tree, so it requires its owning branch merged to trunk, or checked out directly, to
function. Switching branches in this checkout while a plan-rollout run is live breaks every running
instance — see `skills/plan-rollout/SKILL.md`'s "Known constraint" section.

`skills/plan-rollout/scripts/rollout-db` is a stdlib-Python SQLite ledger CLI for
plan-rollout runs; its tests live beside it as `test_rollout_db.py`. Its database lives at
`~/.claude/plan-rollout-runs/rollout.db`, outside this repo — nothing under that path is
checked in, and cloning the repo does not restore it. A `SubagentStop` hook in
`~/.claude/settings.json` (not in this repo) calls `rollout-db hook-check` against it.

## Pointers

- `README.md` — human-facing index of what each skill does and when to reach for it.
- `skills/plan-rollout/SKILL.md` — the plan-rollout actor table and its reference-file map.
