# Bookend Claude Skills and Rules

Claude Code skills and rules used across Bookend repos. `skills/` holds 16 skill
directories (a `SKILL.md` each, some with a `references/` folder disclosed from it);
`rules/` holds four standalone convention docs; `output-styles/` holds chat-reply styles.

## Install

`~/.claude/skills`, `~/.claude/rules`, and `~/.claude/output-styles` are symlinks
straight into this repo's `skills/`, `rules/`, and `output-styles/` directories —
nothing is copied anywhere. Edit a file here and every session on the machine reads
the change immediately; there is no sync step.

```
ln -s "$(pwd)/skills" ~/.claude/skills
ln -s "$(pwd)/rules" ~/.claude/rules
ln -s "$(pwd)/output-styles" ~/.claude/output-styles
```

Some entries under `skills/` are symlinks into `~/.agents/skills` rather than files in
this repo — `code-review`, `tdd`, `writing-for-agents` and about a dozen more. They are
gitignored and machine-local: they get replaced on reinstall, so edits to them do not
survive, and they are not part of the 16 directories counted above. `.gitignore` has the
current list.

## Which skill to reach for

### Delivering a plan or a ticket

- **plan-rollout** — the front door for "make this happen". Takes a ticket or a plan doc
  and drives it to merged PRs: falsifies the plan against the live repo, cuts a base
  branch, partitions the work into PRs and into *operational units* (a deploy, an IAM
  grant, a migration — things no agent can perform), then runs each slice of the work as a
  build → review → fix → merge loop. Fires when a ticket or plan needs implementing, when
  work needs partitioning, or when any agent is about to be dispatched to edit code.

  It is built from **three actors**, and each reads only its own reference file — a
  coordinator never loads another actor's loop:

  | Actor | Reads | Owns |
  |---|---|---|
  | Top-level coordinator | `references/top-level-coordinator.md` | The plan, the base branch, dependency waves, run artifacts, close-out |
  | Second-level coordinator (one per aspect) | `references/second-level-coordinator.md` | Its aspect's PR loop, review rounds, the Jira tracker |
  | Coding sub-agent | `references/coding-agent.md` | One PR's worktree, `/tdd`, the commits |

  Two more reference files are read by whoever needs them:
  `references/brief-contract.md` (every field a dispatch brief must carry, paired with the
  report field that would expose its omission) and `references/review-efficacy-axis.md`
  (mutation testing, for when the thing under review is itself tests).

  The design point worth knowing before you read it: **continuation is the invariant.** A
  finished PR is a loop iteration, not a checkpoint. The skill carries one predicate,
  `needs_human()`, that is the complete list of reasons the run may stop — six conditions,
  and "a PR is done" is deliberately not one of them.

- **git-worktree-topology** — the git mechanics underneath a multi-agent run: branch
  naming that cannot collide, what a worktree does and does not isolate, how a stacked-PR
  chain has to merge. Fires when planning branch names or when an agent hits
  `cannot lock ref`.

### Plans, claims, and write-ups

- **plan-and-review** — produces the plan `plan-rollout` can be trusted with: pairs it
  with a ticket, decides whether the work needs a plan at all (many tickets don't — it
  says so and hands off), checks every claim before drafting, reviews the draft with a
  subagent, and resolves every open question. Fires when a ticket has no plan, a plan has
  no ticket, or a draft still carries open questions.
- **plan-docs** — conventions for a plan doc that is actively being implemented: it lives
  in `plan/`, gets corrected *in place* as work falsifies it (never appended to), and its
  runtime-only checks table survives until validation consumes it. Fires when starting or
  continuing a plan-driven run.
- **claims-and-scope-discipline** — how to verify a written claim (a review finding, a
  ticket, a plan step) before acting on it, and how to decide what a fix may touch. Fires
  when a finding's citation doesn't match the code, a ticket prescribes its own fix, or a
  scope boundary is in question.
- **bug-report** — the structured write-up format for a bug found mid-investigation:
  current diagnosis first, dated evidence, ruled-out hypotheses compressed. Fires when a
  write-up is about to land in chat, a ticket, or a plan tracker.

### Review and fix

- **review** — runs the `mattpocock-skills:code-review` workflow, then rewrites every
  finding into a readable structured template (summary, numbered code flow, references,
  glossary). Inside a `plan-rollout` run it is also handed a per-PR review file to read
  first and append to, which is how a later round's reviewer sees the earlier rounds.
  Fires on `/review`.
- **root-cause-fix** — before any fix is written, groups every outstanding finding by
  shared root cause instead of patching each one. Fires right after a review produces
  findings, or when one area has drawn findings across more than one round. Its behaviour
  splits by caller: invoked directly by a human it stops for approval, invoked from a fix
  brief inside a run it hands the plan to that same agent to implement test-first.
- **dual-scoped-review-plans** — for a change big enough to want two review passes, authors
  two plans from deliberately *different* sources: one from what the work already worried
  about (its notes, findings, deviations), one from the repo's own `AGENTS*.md` / `CLAUDE.md`
  standards with no knowledge of the work at all. Agreement between the passes is signal and
  so is divergence, which is why neither author may see the other's source. The isolation has
  to survive the pass, not just the plan: fresh sub-agents only, never a fork, and the
  dispatching session hands over *paths* rather than content — which is what disqualifies it
  from synthesising later. Each plan is written for a Claude agent to execute rather than a
  person to read, so it carries completion criteria a reviewer can fail plus its own scope and
  exclusion list — a later session running the pass may never see the brief that produced the
  plan. Writing the plans and running the passes are separate steps. Exits
  immediately if the repo has no standards docs — with one source there is no second scope.
  Fires at a `plan-rollout` close-out, or when a review needs more than one pass.

### Memory maintenance

- **dream** — the full memory-improvement cycle, composed from the three skills below
  rather than reimplementing them: apply whatever a human already ratified, run a fresh
  analysis pass, then post the result. The only one of the four allowed to write
  `MEMORY.md` or a `CLAUDE.md`, and only for a ratified item whose before-text still
  matches disk. Fires on `/dream`.
- **session-analysis** — mines this project's own session transcripts for a specific
  analysis job, selected by a mode argument (`/session-analysis dream` extracts durable
  learnings). Stops at a reviewable list; it never writes memory itself.
- **improve-memory** — takes a learnings list and drafts a proposed cleanup of memory and
  the `CLAUDE.md` files: merges duplicates, resolves contradictions, fixes broken index
  and wiki-link pointers. Writing the overview is the whole job — applying it is a
  separate, deliberate step.
- **send-results** — posts a Slack message that stands alone as a durable record: the
  caller's full content plus a file's absolute path. Deliberately generic; any automation
  can call it.

### Writing

- **agent-style** — 22 literature-backed prose rules for engineering docs a human
  reads later (READMEs, comments, commit/PR/issue text, changelogs, runbooks,
  postmortems, explainers for a non-technical reader). Cross-references the
  `plain-english` output style rather than restating it; the two divide by whether
  the prose is the chat reply itself or a document it produces. Fires as a pass after
  drafting such a document.

### Tooling and lookups

- **context7-mcp** — resolves a library to a Context7 ID and fetches its current docs, one
  concept per query. Fires on setup questions, library code requests, or a named framework.
- **benchmark-code-graphs** — measures which of several overlapping code-intelligence tools
  (gitnexus, graphify, understand-anything, LSP) is actually trustworthy for which task in
  a given repo, then writes the routing rules into `CLAUDE.md`. Fires when a repo has more
  than one such tool and their self-reported guidance has never been checked against grep
  ground truth.

## rules/

- **comment-flags.md** — restricts code comment flags to `TODO` and `BUGBUG`; invented
  labels like `KNOWN GAP` are invisible to linters and CI sweeps.
- **context7.md** — the four-step Context7 procedure (resolve an ID, pick the best match,
  query one concept at a time, answer from the docs). It defers the *when-to-trigger*
  question to the Context7 plugin's own server instructions, so it is a procedure doc
  rather than a trigger — and it overlaps in content with the `context7-mcp` skill, which
  does carry its own triggers.
- **python.md** — `uv`/`poe` conventions for this org's Python projects (never a bare
  `python`/`pip`) plus a short testing philosophy. Carries `paths: ["**/*.py"]`
  frontmatter, so unlike the other rules it auto-applies whenever a `.py` file is in play.
- **skill-authoring.md** — two traps in writing skills for this machine. A bare `$0`–`$9`
  inside a fenced code block in a `SKILL.md` gets silently rewritten with a word from the
  caller's argument string when the skill is invoked with `args` — the file on disk stays
  correct, so review never surfaces it. And skill snippets run against BSD tools, so
  `head -n -N` and `date -d` do not work. Carries `paths: ["skills/**/*.md"]`.

## Call graph

Built by matching real invocation forms — a backticked skill name, a `/name`, or "the X
skill" — across every `.md` file in each skill's directory, excluding frontmatter
`description:` lines (those carry routing exclusions like "Not … (other-skill)", which are
deliberately not calls).

Two shapes of edge show up, and they mean different things to a reader:

- **Delegation** — the text tells you to go run the other skill, or to follow it wholesale.
- **Citation** — the text points at the other skill to back one rule, without handing over
  control.

| Skill | Delegates to (runs it / follows it wholesale) | Cites (defers to it, keeps control) |
|---|---|---|
| agent-style | — | — |
| benchmark-code-graphs | — | — |
| bug-report | — | plan-docs |
| claims-and-scope-discipline | root-cause-fix (once findings are classified and scoped); git-worktree-topology (on a digest conflict) | plan-rollout (`brief-contract.md`, twice; `second-level-coordinator.md` for the review-recommendations format) |
| context7-mcp | — | — |
| dream | session-analysis; improve-memory; send-results | — |
| dual-scoped-review-plans | — | plan-docs (where the plans land); review (finding prose); root-cause-fix (grouping what survives); claims-and-scope-discipline (verify before acting); plan-rollout (`brief-contract.md`, for the read-back pairing) |
| git-worktree-topology | — | — |
| improve-memory | — | session-analysis (takes its output as input) |
| plan-and-review | plan-docs ("Read it now"); plan-rollout (when the work needs no plan, and again when invoked directly) | plan-docs; claims-and-scope-discipline; plan-rollout (`brief-contract.md`) |
| plan-docs | bug-report (write findings in its format) | plan-rollout, plan-and-review (boundary note: cutting the branch is the first skill's job and writing the plan the second's, not this one's); dual-scoped-review-plans (§0, which of its conventions a review plan is exempt from) |
| plan-rollout | plan-and-review (when no ratified plan exists, and it returns rather than calling back); root-cause-fix (when a fix round's findings are not all trivial); review (every review round is a dispatch); dual-scoped-review-plans (at close-out, to author the plans but never run the passes); **external:** `/tdd` | plan-docs (owns rewrite-in-place and the runtime-only-checks table); claims-and-scope-discipline (the integration-merge digest at the aspect merge, and the shared-test-infra baseline); git-worktree-topology |
| review | **external:** `mattpocock-skills:code-review` | plan-rollout (the per-PR review file it may be handed) |
| root-cause-fix | claims-and-scope-discipline (the classify-before-grouping step) | plan-rollout (`coding-agent.md` for `/tdd`, `brief-contract.md` for the brief) |
| send-results | — | — |
| session-analysis | — | dream (both compute the same lock path; kept in sync by hand) |

Notes on edges that needed a judgment call rather than a mechanical match:

- **`plan-rollout` absorbed four skills, so its old citation edges became internal.** It
  used to cite `parallel-agent-orchestration`, `ticket-delivery-loop`, `pr-fix-review` and
  `stacked-pr-review` by section number. They did not all land the same way:
  `parallel-agent-orchestration` and `ticket-delivery-loop` became reference files,
  `pr-fix-review` became two questions a round-2 review brief asks (so the three-round cap
  still counts one dispatch per round), and only `stacked-pr-review`'s declared-gap harvest
  survived at all. Every external skill that cited them now points at a reference file path
  instead. Citing a numbered section of another skill turned out to go stale constantly —
  the convention now is to cite the skill and its reference file, never a section number.
  That applies to `plan-rollout` itself: it no longer has numbered steps, so nothing cites
  it by step.
- **One edge is easy to exclude by mistake.** `session-analysis` uses the bare word `dream`
  as a *mode argument*, which is not a call — but it separately cites the `dream` skill by
  name, for a lock path the two compute identically. Excluding the skill on the strength of
  the mode argument would have hidden a real keep-in-sync dependency, so the row carries it.
- **`claims-and-scope-discipline` ↔ `root-cause-fix` is a hand-off, not a cycle.** Each end
  calls the other and each says so: classify and scope every finding in the first, then
  call the second to group them by cause.
- **`plan-rollout` ↔ `plan-and-review` is one sequence entered from either end, and exactly
  one direction fires per run.** `plan-rollout` calls `plan-and-review` and then continues
  on its own; `plan-and-review` therefore *returns* when it was entered that way, and calls
  `plan-rollout` only when it was invoked directly. Both state the rule at their own seam,
  because a description cannot carry which end the run started from — without it the pair
  would loop.
- **Both also delegate out to `plan-rollout` when the work turns out to need no plan at
  all.** That exit is the common case for a single-PR ticket. `plan-rollout` handles it as
  a one-PR, one-aspect partition — a single-aspect plan still gets a second-level
  coordinator, so the hand-off has a real target rather than falling through.
- **The `plan-docs` edges from `plan-rollout` and `plan-and-review` are genuinely both**
  delegation and citation — each says "read it now" and also cites it for supporting
  detail. Both columns carry the edge rather than forcing one.
- **`review` now points at the plugin, not the built-in.** It used to invoke the
  unprefixed `code-review`, which on this machine is a gitignored symlink to a local copy
  that had drifted from the plugin of the same name. Two versions of one skill under one
  name was the defect; the symlink is now simply unused.

## Advisor

Set Opus as the default advisor model: `/advisor opus`. This saves `advisorModel: opus` to
your user settings, so Claude consults Opus at key decision points regardless of which
model you're running as the main model.
