---
name: improve-memory
description: "Draft a proposed cleanup of this project's long-term memory (MEMORY.md plus its detail files in ~/.claude/projects/<slug>/memory/) and its CLAUDE.md files, given a learnings list — typically the output of `session-analysis dream`. Merges duplicate memories, resolves contradictions, fixes broken index/wiki-link pointers, and proposes CLAUDE.md or path-scoped-rules upgrades, writing everything to one memory-improvement-overview.md for a human to ratify. Use when the user asks to clean up, audit, deduplicate, or reconcile memory, to fold session-analysis dream output into memory, or types `/improve-memory`. Not for extracting learnings from transcripts in the first place — that's `session-analysis dream`, and this skill takes its output as input rather than reproducing it. Not for applying an approved change — writing the overview is the whole job; editing MEMORY.md, a detail file, or any CLAUDE.md is a separate, deliberate step this skill never performs itself."
---

# Improve memory

This skill drafts a memory cleanup. It never applies one. Given a learnings list, the current
state of memory plus CLAUDE.md, and any decisions already ratified in a prior run's overview, it
writes exactly two things — the live overview and a dated archive copy of it (§10) — and touches
nothing else. The distinction matters enough to repeat: **this skill has no write access to
MEMORY.md, any detail file, or any CLAUDE.md, project or user.** Not "prefers not to" —  it must
not, under any circumstance, even a fix that looks obviously correct, and even a decision the human
already ratified. Every finding below is a draft for a human to ratify; every ratified item is a
draft for a human — or a separate, deliberate step — to apply.

## 1. Get the learnings list

This skill takes one required input: a learnings list, in the shape `session-analysis dream`
produces (statement, category, evidence per entry). If the user did not supply one and none is
already in the conversation, **stop and ask them to run `/session-analysis dream` first.** Do not
run that mode yourself, and do not guess at learnings from context — this mirrors how
`session-analysis` itself refuses to guess a missing mode argument.

## 2. Locate the inputs

```bash
MEMDIR="$HOME/.claude/projects/$(pwd | sed 's/\//-/g')/memory"
ls -d "$MEMDIR"                       # confirm it exists before going further
USER_CLAUDE_MD="$HOME/.claude/CLAUDE.md"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
PROJECT_CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md"   # may not exist — that's fine, note it and move on
```

Also check for `~/.claude/rules/` — in this setup it is a symlink into a git repo
(`claude-skills/rules/`) holding small, cross-project instruction files; symlinked rules directories
are a supported setup, not a workaround. `~/.claude/rules/*.md` is a first-class auto-load mechanism
on its own — no `@`-import, hook, plugin, or settings entry makes it load. Some of those files carry
a `paths: ["<glob>"]` frontmatter field that scopes them to matching file paths; a file with **no**
`paths` field loads into every session unconditionally, at the same priority as `CLAUDE.md`. That has
a consequence worth stating plainly, because it's easy to get backwards: moving unconditional text
out of `CLAUDE.md` into an unconditional rules file saves **zero** tokens — both load every session
regardless. Token savings come only from adding a `paths:` field, which turns an always-loaded rule
into one that loads only when Claude reads a matching file — write that glob relative to the repo
(e.g. `skills/**/*.md`), never as an absolute path; every documented and in-repo example is relative,
and there's no absolute-path form to match against. This is the mechanism §7 uses for folder-scoped
proposals — confirm it's present before citing it (`ls "$HOME/.claude/rules"`), and read one scoped
and one unscoped example rather than assuming the frontmatter shape.

Also check for a prior run's ratified decisions, before generating anything:

```bash
OVERVIEW="$MEMDIR/memory-improvement-overview.md"
[ -f "$OVERVIEW" ] && grep -n '^## Ratified by ' "$OVERVIEW"
```

If `$OVERVIEW` exists and has a `## Ratified by ...` heading, `Read` the file and extract that
section verbatim — from the `## Ratified by ...` line up to, but not including, the next literal
`## Auto-approved` line (the fixed section that always follows it, per §9). Don't use "the next `##`
line" as the boundary: a ratified item can legitimately quote a CLAUDE.md or rules-file heading
inside its own text, and that quoted `##` is not a section break.

This section is settled input, not something for this run to re-derive or re-argue: carry it into
the new overview unchanged (§9), and never re-list a decision it already made under Needs-your-call
(§8), even when this run's own checks in §3–§6 still turn up the same underlying defect on disk.

For each item in that section, do one more mechanical check — no judgment involved — before writing
anything: read the file(s) the item names and see whether its stated "before → after" already
matches what's on disk. That check only decides what status note, if any, gets attached to the item
in §9; it is a read, and changes nothing, on this file or any other. Carrying a decision forward and
reporting whether it's landed is not the same as applying it — that stays exactly as forbidden as it
always was (§11), ratified items included.

If no `memory-improvement-overview.md` exists yet, or it exists with no `## Ratified by ...`
section, there is nothing to carry forward: proceed exactly as the rest of this skill already
describes.

## 3. Survey the memory dir cheaply

Never `cat`, `Read`, or otherwise load all 50-odd detail files wholesale — that is most of a
context window spent before any drafting starts. Pull frontmatter plus the first two body lines of
each file instead; that is enough to judge whether a file is a plausible duplicate, a stale label,
or worth reading in full later:

```bash
cd "$MEMDIR"
for f in *.md; do
  [ "$f" = "MEMORY.md" ] && continue
  echo "###FILE: $f"
  awk '
    /^---$/ { dashes++; print; next }
    dashes==1 { print; next }
    dashes>=2 && !started && NF { started=1 }
    dashes>=2 && started { if (!NF) exit; print; n++; if (n>=2) exit }
  ' "$f"
  echo
done
```

Tested against a live 50-file memory dir: full output is well under what one whole file alone
would cost, and every frontmatter block plus lead line was legible enough to spot candidate
duplicates without opening the files themselves.

## 4. Cross-check the index against disk

`MEMORY.md` is a flat list of `- [label](target.md) — description` lines. Three defects are
mechanical to detect and require no judgment to *find* (only, sometimes, to fix):

```bash
# Scope these scratch files under $TMPDIR (falls back to /tmp) plus this shell's PID, which
# alone is enough to make them collision-free per run — unlike session-analysis's $OUT_FILE,
# nothing outside this skill needs to independently derive these filenames, so there's no
# reason to also thread a project slug through them (and doing so via `pwd` here would be
# unreliable anyway: this block's own `cd "$MEMDIR"` below means a slug computed from `pwd` in
# a *later* block, after cwd has already moved, would resolve against $MEMDIR instead of the
# project root). They're pure intermediates for the comm checks right below and are deleted at
# the end of this block — no downstream step or other skill reads them.
SCRATCH_DIR="${TMPDIR:-/tmp}"
SCRATCH_DIR="${SCRATCH_DIR%/}"
IM_TARGETS="$SCRATCH_DIR/im-targets-$$.txt"
IM_ACTUAL="$SCRATCH_DIR/im-actual-$$.txt"

cd "$MEMDIR"
grep -oE '\([a-zA-Z0-9_.-]+\.md\)' MEMORY.md | tr -d '()' | sort -u > "$IM_TARGETS"
ls *.md | grep -v '^MEMORY.md$' | sort -u > "$IM_ACTUAL"

# a) targets that don't exist on disk
comm -23 "$IM_TARGETS" "$IM_ACTUAL"

# b) files on disk that MEMORY.md never points to (orphans)
comm -13 "$IM_TARGETS" "$IM_ACTUAL"

# c) two or more index lines pointing at the same file
grep -oE '\([a-zA-Z0-9_.-]+\.md\)' MEMORY.md | tr -d '()' | wc -l   # N: pointer lines total
wc -l < "$IM_TARGETS"                                                # M: distinct targets
grep -oE '\([a-zA-Z0-9_.-]+\.md\)' MEMORY.md | tr -d '()' | sort | uniq -d

rm -f "$IM_TARGETS" "$IM_ACTUAL"
```

State the arithmetic explicitly in your findings (e.g. "N pointer lines resolve to M distinct
files, so N-M lines are duplicates") — that count is the proof, not a claim to take on faith.

## 5. Cross-check wiki-links inside the detail files

The `[[...]]` links between detail files are index pointers too, and the file set is inconsistent
about which form they use: a link may name a file's **filename** (underscores) or its frontmatter
**`name:`** field (usually hyphens, but not always — a file whose own `name:` breaks that
convention silently breaks every hyphenated link meant for it). Resolve against the union of both,
and support the `[[label|target]]` piped form. Scan the detail files only — never
`memory-improvement-overview.md`, whose quoted "Before" blocks would resurface links that were
already removed:

```bash
# Same scoped-scratch convention as §4 — PID under $TMPDIR (or /tmp), no project slug (see
# §4's comment for why), deleted at the end of this block.
SCRATCH_DIR="${TMPDIR:-/tmp}"
SCRATCH_DIR="${SCRATCH_DIR%/}"
IM_WL="$SCRATCH_DIR/im-wl-$$.txt"
IM_KNOWN="$SCRATCH_DIR/im-known-$$.txt"

cd "$MEMDIR"
# The overview is excluded: its "Before" blocks quote every link it has ever proposed
# removing, so scanning it reports links that no real memory file still contains.
grep -oh --exclude='memory-improvement-overview*.md' '\[\[[^]]*\]\]' *.md \
  | sed 's/\[\[//; s/\]\]//' | awk -F'|' '{print $NF}' | sort -u > "$IM_WL"
{ ls *.md | sed 's/\.md$//'; grep -h '^name:' *.md | sed 's/^name: *//; s/"//g'; } | sort -u > "$IM_KNOWN"
comm -23 "$IM_WL" "$IM_KNOWN"
rm -f "$IM_WL" "$IM_KNOWN"
```

For every name left unresolved, find its source with `grep -n '<name>' *.md` and read that
sentence in context before deciding what kind of defect it is:

- **A link to a file that plausibly means one specific, unambiguous existing file**, just
  mis-formatted (wrong separator, stale label) — mechanical, no judgment about *which* file it
  means.
- **A link to a file that never existed and has no obvious existing substitute** — the sentence
  around it usually tells you why (a hedge like "if that memory exists", a forward reference to a
  note that was never written). Fixing this means authoring or deciding content, not just
  repointing a link — judgment.
- **A link that resolves to a real file outside the memory dir** (e.g. into `claude-skills/rules/`)
  is not broken. Memory notes legitimately cite the rules layer. Don't flag these.

## 6. Read full content only where §3–§5 raised a question

Once survey descriptions or a broken/duplicate pointer flag two files as plausibly overlapping,
contradictory, or in need of a specific rewrite, `Read` those specific files in full — never more
than the number the checks above actually flagged.

## 7. Fold in the learnings list

For each learning:

1. **Check whether it's already recorded** before treating it as new. Search memory by keyword
   (`grep -il` across `$MEMDIR/*.md`), and also check whether the project's own aspect docs
   (`AGENTS.md` and friends, if this project has them) already state it — some facts live in
   project documentation rather than agent memory, and a learning can be "already covered" there
   even with zero memory hits. If covered, say so and propose no new entry — do not duplicate an
   existing doc into memory.
2. **Weigh the evidence as given**, don't upgrade it. If the learnings list flags evidence as weak
   (a single session, two near-simultaneous instructions that are plausibly one broadcast rather
   than two independent occurrences), carry that caveat into your finding and recommend confirming
   before promotion rather than quietly treating it as solid.
3. **Propose a destination**, using this test: would the learning hold regardless of which repo or
   task you're in?
   - **No, it's true only of this project** → a new (or merged-into-existing) file in `$MEMDIR`,
     indexed from `MEMORY.md`.
   - **Yes, it holds everywhere** → `~/.claude/CLAUDE.md`.
   - **It's cross-project but only fires inside one specific folder or file pattern** → a new
     `~/.claude/rules/<slug>.md` with a `paths: ["<glob>"]` frontmatter field (see §2), naming the
     exact folder or glob **relative to the working directory** — an absolute path never matches.
     Don't fold a folder-scoped fact into the global CLAUDE.md just because it's convenient — that's
     exactly the growing-wall-of-rules failure mode this skill exists to push back on. And don't
     propose lifting an already-unconditional passage from CLAUDE.md into an unconditional rules
     file as a token-saving move — it isn't one (see §2); only a `paths:` field saves anything.

Every decision in this section — placement, whether evidence clears the bar, whether "already
covered" — is judgment. All of it goes to Needs-your-call, even the calls that look obvious to
you. §8 explains why.

## 8. Classify every change: Auto-approved vs Needs-your-call

If §2 found a carried-forward `## Ratified by ...` section, its decisions are out of scope for this
step: don't put something it already decided into either list below, even when §3–§6's mechanical
checks re-surface the same underlying defect. When it's genuinely unclear whether a fresh finding is
the same defect a ratified item already settled, don't silently drop it — list it in the normal
section with a one-line pointer to the ratified item and let a human confirm they're the same thing.
Suppressing a real, distinct finding is worse than listing one redundantly.

**Auto-approved** is narrow on purpose: a change is safe here only if there is exactly one
reasonable way to make it and no reading of the evidence changes the outcome.

- Two `MEMORY.md` lines pointing at the same file → collapse to one (keep the more complete label,
  drop the redundant line).
- A wiki-link whose separator/casing doesn't match its target but whose intended file is
  unambiguous (one file's content obviously matches) → fix the link text.
- An index line's label that flatly contradicts the description sitting right next to it on the
  same line, where the file's own current content already agrees with the description → reword the
  label to match. This is relabeling only — never rewrite the body this way.

**Needs-your-call** is everything else, explicitly including (this is not exhaustive, it's the
floor):

- Every new-memory-vs-CLAUDE.md-vs-rules-file placement decision from §7, no matter how obvious it
  seems.
- Any contradiction between two files where resolving it means rewriting a body paragraph, not
  just repointing a link — say which file wins and why the other is stale, but the edit itself
  waits for ratification.
- Any CLAUDE.md or rules-file restructuring suggestion.
- A dangling wiki-link with no existing file to fall back on.
- Whether a file that duplicates content already living elsewhere (e.g. a memory note that
  restates a CLAUDE.md section in full despite calling itself "a pointer") should be trimmed.

A one- or two-item Auto-approved section is a legitimate outcome, not a thin result — most real
memory defects involve exactly the kind of judgment that belongs in the other section.

## 9. Write the overview

Write to `$MEMDIR/memory-improvement-overview.md` — colocated with the index a human already
opens when reviewing memory, and safe precisely because `MEMORY.md` never links it: nothing loads
it as a memory fact, it is inert until a person acts on it. Regenerate it fresh on every run
(overwrite, don't append) — this live copy is a snapshot of the *current* state, not a running log,
with one carve-out: a `## Ratified by ...` section (§2) is a human decision already made, not run
state, so this step never regenerates or reargues it. The running log lives separately, as an
unmodified dated archive of this same content (§10) — overwriting the live file every run never
loses anything precisely because that archive exists. Compose the new file's full content, then
write it in one shot — this and its archive copy (§10) are still the only files this skill ever
writes.

1. **Carried-forward Ratified section, if §2 found one.** Reproduce it verbatim — same heading,
   same text, no rewording, no re-deriving, nothing dropped. For each item where §2's applied-status
   check found the "before → after" already on disk, add one line directly under that item —
   `Status: already applied.`, citing what you checked — but only if that item doesn't already carry
   this note from a prior run; if it does, leave it as-is rather than adding a second one. Add
   nothing for an item that's still open — the absence of a status note already means that. This is
   the only section that isn't freshly generated; carrying it forward, including reporting whether
   it has landed, is still not applying it — §11's prohibition holds without exception here.
2. **`## Auto-approved`** and **`## Needs your call`**, in that order, composed fresh from this
   run's own analysis (§3–§8) as always — minus anything that duplicates a decision already sitting
   in the Ratified section (§8).

So the body has, at the top level and in this order: `## Ratified by ...` (present only when carried
forward from a prior run), then:

```markdown
## Auto-approved

## Needs your call
```

nothing else at that level.

The file's own opening lines must say what it is, in case anyone finds it without this context: a
generated proposal, not a memory entry, never linked from `MEMORY.md`, nothing here has been
applied — and, when a Ratified section is present, that it is preserved verbatim across runs while
Auto-approved/Needs-your-call are regenerated fresh every time.

Every entry in either section states, at minimum:

- **What changes** — one line.
- **File(s)** — exact path(s).
- **Before → after** — the literal text, not a paraphrase.
- **Why** — one line.

## 10. Archive a dated copy

Every run also writes an unmodified copy of the file §9 just wrote to a dated path, so a run's
findings and decisions survive being overwritten by the next run's live copy. The live file at
`$MEMDIR/memory-improvement-overview.md` stays the only one anything else reads, links, or is
pointed at; the archive exists purely so a human can open a specific past run by date.

```bash
OVERVIEW="$MEMDIR/memory-improvement-overview.md"   # the file §9 just wrote — redefine it here,
                                                      # don't assume it's still set from §2
HISTDIR="$MEMDIR/history"
mkdir -p "$HISTDIR"
STAMP="$(date +%Y-%m-%d)"
ARCHIVE="$HISTDIR/memory-improvement-overview-$STAMP.md"
[ -e "$ARCHIVE" ] && ARCHIVE="$HISTDIR/memory-improvement-overview-$STAMP-$(date +%H%M%S).md"
cp "$OVERVIEW" "$ARCHIVE"
```

Copy the file, don't recompose it — same opening lines, same carried-forward `## Ratified by ...`
section if §9 wrote one, same `## Auto-approved`/`## Needs your call`. A dated file is only a
complete record of what a run proposed and what had already been decided by then if it is
byte-identical to what a reviewer would have seen on that day.

**Same-day collisions get a time suffix, not an overwrite.** The default name is date-only. A
second run on the same day would collide with the first, and overwriting it would reintroduce the
exact history loss this section exists to fix — on the one kind of day it's most likely to matter,
since two runs in a day means something changed between them. So a collision gets a `-HHMMSS`
suffix instead of clobbering the earlier file; the retention prune below deliberately treats both
name shapes the same way (see its note).

**Archives live in `$MEMDIR/history/`, not `$MEMDIR/*.md` directly.** §4's orphan check
(`comm -13` against `MEMORY.md`'s targets) would otherwise flag every one of these as a stray file
needing attention — verified on disk: `MEMORY.md` links nothing named "overview" today, so even
today's single live file would already trip that check if it sat loose in `$MEMDIR`. A subdirectory
keeps the whole, ever-growing archive set out of that comparison instead of teaching three separate
glob-based checks (§3, §4, §5) to exclude a filename pattern. No project's memory dir under
`~/.claude/projects/*/memory/` currently has a subdirectory, and neither this skill nor
`session-analysis` ever walks `$MEMDIR` recursively — so nothing today reads past the top level of
`$MEMDIR`, but flag it plainly if some other, unexamined consumer of the memory dir turns out to.

**Retention: keep the most recent `${IMPROVE_MEMORY_HISTORY_KEEP:-30}` archives, oldest deleted
first, on every run.** 30 covers roughly a month of daily runs — enough to look back across several
ratification cycles — while each archive costs only tens of KB. A plain count, not an age cutoff,
because the natural way to express "everything but the last N" — `head -n -N` — is a GNU extension
that fails outright on the BSD `head` this repo's own macOS boxes ship (verified:
`head -n -3` errors with "illegal line count" here), and an age-based cutoff would need the same
GNU/BSD split again for `date -d` vs `date -v`. The prune below uses `tail -n +N` instead, which is
POSIX and behaves identically on BSD and GNU — no such split needed there. Override the default by
exporting `IMPROVE_MEMORY_HISTORY_KEEP` before running this skill.

**Landmine (BOOK-851):** Claude Code splices a skill's `args` string into the fenced code blocks it
delivers, without sparing bash positional parameters — a `$` immediately followed by a single
digit, anywhere on this page, can come back rewritten by whatever text invoked the skill. Every
shell block in this file avoids that pattern for that reason; keep new ones that way too.

```bash
KEEP="${IMPROVE_MEMORY_HISTORY_KEEP:-30}"
ls -1 "$HISTDIR"/memory-improvement-overview-*.md 2>/dev/null | sort -r | \
  tail -n +$((KEEP+1)) | \
  while IFS= read -r f; do rm -f -- "$f"; done
```

The glob matches both `-<date>.md` and `-<date>-<time>.md` names. `sort -r` orders every archive
newest-first; within a same-day collision pair the plain date name sorts ahead of its `-HHMMSS`
sibling (`-` sorts below `.`), which matches run order — the day's first run, then the collision
run — so the pair is always two consecutive lines, never pulled apart by some other file landing
between them. The keep-newest-N cutoff can still fall between the two: when it does, the day's
first-run copy is kept and the collision copy is the one pruned. Don't "simplify" this to a
date-only glob, it would stop pruning the time-suffixed files at all.

## 11. Stop

Hand the overview's path back. Do not edit MEMORY.md, any detail file, or any CLAUDE.md — not even
the Auto-approved items. Applying a ratified change is a separate, deliberate step outside this
skill.
