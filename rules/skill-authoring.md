---
paths: ["skills/**/*.md"]
---

## No positional patterns in a skill's code blocks

Never write a bare **`$0`–`$9`** inside a fenced code block in a `SKILL.md`. That includes `awk`
one-liners, shell snippets, and any command a skill tells an agent to run verbatim.

**Why:** when a skill is invoked with `args`, Claude Code substitutes positional-argument
placeholders into the skill body it delivers, and it does **not** exclude fenced code blocks. The
file on disk stays correct; only the delivered copy is rewritten, with a token taken from the
caller's argument string. Reviewing the file never surfaces it, and what the line becomes depends
on who called the skill, so it does not reproduce consistently.

Observed 2026-09-04 in `skills/improve-memory/SKILL.md` (BOOK-851). A retention-prune line
committed as `awk -v keep="$KEEP" '{a[NR]=$0} ...'` was delivered as
`awk -v keep="$KEEP" '{a[NR]=Learnings} ...'` (`Learnings` being the first word of that
invocation's `args`). `$KEEP` on the same line survived, so the rewrite targets positional patterns
specifically, not shell variables generally.

The failure is silent at every layer. The corrupted line above is valid `awk` that does nothing:
an undefined variable evaluates to empty, the output is blank lines, and the downstream `rm`
becomes a no-op. Retention pruning simply stopped happening, with no error anywhere.

## How to apply

- **Check before committing a skill:** `grep -n '\$[0-9]' skills/*/SKILL.md` must return nothing.
- **Rewrite around the pattern rather than escaping it.** Reach for a form that needs no positional
  reference at all: `sort -r | tail -n +N` in place of an `awk` line-buffer, or a
  `while IFS= read -r` loop.
- **Prefer invoking skills with no `args`.** Pass inputs as exported environment variables instead;
  a skill invoked with no argument string has nothing to substitute. This is also why a skill that
  takes structured input should document env vars rather than an argument string.
- If a skill genuinely must document a command containing `$0`, keep it out of a fenced block and
  describe it in prose, flagging that it must be retyped rather than copied.

## Portability: this is a macOS machine

Skill snippets run against BSD tools, not GNU. Two that have already bitten:

- **`head -n -N` does not work.** BSD `head` rejects a negative line count with
  `head: illegal line count`. Use `tail -n +N` against a reversed sort instead.
- **`date -d` does not work.** BSD `date` uses `-v`. Prefer a count-based rule over an
  age-based one when a skill needs to prune or filter by recency.

## Split a skill by circumstance of use

A `SKILL.md` carries what **every** invocation needs. Material that fires only under a particular
circumstance goes in `references/<aspect>.md`, with a one-line pointer where that circumstance
comes up:

```
`references/test-infra-baseline.md` — read before changing shared test infrastructure.
```

**Split by circumstance, never by length or by topic tidiness.** The reader is an agent deciding
what to load before it knows what it will find, so the pointer has to name the moment (*read
before changing shared test infrastructure*, not *more on testing*). Splitting by subject scatters
material one invocation needs across two files and buys nothing.

**What stays behind is the rule itself**, in a sentence or two, never a bare "see elsewhere". A
reader who never opens the reference file still gets the rule; the file holds the instances, the
commands, and the worked evidence behind it. Open each reference file by naming the section it
backs (e.g. `The full case for SKILL.md §9: …`) so a file opened on its own says what it belongs to.

`skill-check`'s `body.max_lines` is set to `warn` in `skill-check.config.json`, so length is a
smell it reports rather than a gate. A long `SKILL.md` every invocation reads end to end is fine;
a short one hiding a circumstance-gated procedure behind a subject heading is not.
