---
name: dream
description: "Runs one memory-improvement cycle by composing session-analysis (mode dream), improve-memory, and send-results into one loop, never reimplementing them. Optional mode: `full` (default) or `apply-fixes`. Only one of the four that writes MEMORY.md, a detail file, or a CLAUDE.md. Always ends with one send-results call, even when nothing changed. Use when the user asks to run a memory dream cycle, an end-to-end review-and-cleanup, or types `/dream`. Not for extracting learnings on its own (call `session-analysis dream` directly), not for drafting a cleanup without applying it (call `improve-memory` directly), not for posting an arbitrary one-off message to Slack (call `send-results` directly), and not something to run unattended the first time on a project: the first ever run applies zero ratified items (there's nothing to ratify yet) but still writes memory-improvement-overview.md and mines transcripts, so treat even a first `full` run as a deliberate act, not something triggered incidentally."
---

# Dream

This skill runs one memory-improvement cycle. It never mines transcripts, drafts a cleanup, or
posts to Slack itself: it calls `session-analysis` (mode `dream`), `improve-memory`, and
`send-results` for those three jobs, in that order, and adds exactly one thing none of them do:
applying a human's already-ratified decisions to real memory. **Rule: compose, never reimplement.**
If following this skill ever tempts you to inline session-analysis's extraction script,
improve-memory's survey/cross-check logic, or send-results' redaction/mrkdwn/dedup script instead
of invoking that skill, stop: that duplication is exactly what this skill exists to avoid, and a
divergence between the inlined copy and the real skill is a bug waiting to happen. If one of those
three skills seems to be missing something dream needs, that is a defect in that skill to report,
not a gap for dream to patch around by reimplementing the missing piece itself.

## 1. Mode argument

One optional argument, **mode**:

- **`full`** (default; used when no mode is given): the self-correcting cycle in §4–§8.
- **`apply-fixes`**: apply only the changes already ratified in the latest overview (§5's
  procedure, invoked standalone); no session-analysis or improve-memory call. See §9.

Any other value: stop and ask which mode was meant. Do not guess, matching how
`session-analysis` itself refuses to guess a missing mode.

## 2. Locate the inputs

```bash
MEMDIR="$HOME/.claude/projects/$(pwd | sed 's/\//-/g')/memory"
ls -d "$MEMDIR"                                        # confirm it exists first
OVERVIEW="$MEMDIR/memory-improvement-overview.md"       # the live file: see §2 of improve-memory

# session-analysis's dream mode writes here (its own SKILL.md §2.2): a path scoped by this
# project's slug, under $TMPDIR (falling back to /tmp), using the identical formula for
# TRANSCRIPT_DIR/$MEMDIR above. Compute it here to match; don't invent a different one: if
# session-analysis's §2.2 formula ever changes, this line must change with it (§6).
SCRATCH_DIR="${TMPDIR:-/tmp}"
SCRATCH_DIR="${SCRATCH_DIR%/}"
SA_OUT_FILE="$SCRATCH_DIR/session-analysis-dream$(pwd | sed 's/\//-/g').txt"
```

`MEMDIR` and `OVERVIEW` use the identical derivation improve-memory itself uses, so "the latest
overview" always means the same file both skills would independently find.

## 3. Detect whether the latest overview has been reviewed

```bash
[ -f "$OVERVIEW" ] && grep -n '^## Ratified by ' "$OVERVIEW"
```

If `$OVERVIEW` doesn't exist yet, or exists with no `## Ratified by ...` heading: **not reviewed**:
skip §5 (see §8 for `full`, §9 for `apply-fixes`).

If it exists with that heading, check whether a literal `^## Auto-approved` line appears **after**
it:

- **No `## Auto-approved` line follows.** A human appended `## Ratified by ...` at the end of the
  file, or otherwise didn't reproduce improve-memory's expected shape, and the section then has no
  defined end. Treating EOF as the boundary would mean dream inventing a rule improve-memory
  doesn't share: exactly the kind of disagreement about "where reviewed content ends" this skill
  exists to prevent, since an unbounded extraction risks silently swallowing `## Needs your call`
  into what §5 applies. **Fail closed: reviewed-but-malformed.** Skip §5, report the overview as
  malformed in §10's summary (name the file and say why), and go straight to §10; in `full` mode,
  §6–§7 still run as normal, since a malformed Ratified section blocks applying, not analysing.
- **An `## Auto-approved` line does follow.** **Reviewed.** `Read` the file and extract the
  Ratified section using the exact same boundary improve-memory uses when it carries the section
  forward (its own §2): from the `## Ratified by ...` line up to, but **not including**, that
  `## Auto-approved` line. Use this identical rule, not "the next `##` line", so dream and
  improve-memory can never disagree about where the section ends; a ratified item may legitimately
  quote a heading from CLAUDE.md or a rules file inside its own text, and that quoted `##` is not a
  section break. Go to §5.

Presence of the heading (well-formed or not) is what "reviewed" means here, regardless of how many
items sit under it: a human deliberately added it, which is the signal, not the item count. A
well-formed heading with zero actionable items underneath is a legitimate, expected outcome: it
means the human reviewed and approved nothing yet, not that detection failed.

## 4. What "reviewed" governs

Only the Ratified section, and only in this skill, ever gets applied. `## Auto-approved` and
`## Needs your call` are improve-memory's own findings for a human to read: **dream never reads
either of those two sections looking for something to apply, in any mode, no matter how obvious an
Auto-approved item looks.** Promoting an item from Auto-approved or Needs-your-call into something
dream will act on is exactly the act of ratifying it: the human does that by writing (or copying it
into) the `## Ratified by ...` section themselves. Auto-approved is improve-memory's judgment that
a change is *safe to approve*, not evidence that anyone *has* approved it; those are different
facts and dream only acts on the second one.

## 5. Apply the Ratified section

For each item in the extracted Ratified section, identified as the block starting at a
`**What changes**` line and running to the next `**What changes**` line or the section boundary,
whichever is first (this mirrors improve-memory §9's own per-entry field list: What changes,
File(s), Before → after, Why):

1. **Skip anything already marked applied.** If the item carries a `Status: already applied.` line
   (improve-memory writes this itself; see §7 below and improve-memory §2), skip it and treat
   this annotation as the **only** reliable guard against double-applying, not a redundant
   convenience checked before a cheaper one. An additive edit (appending or prepending a sentence to
   an index line or a detail-file paragraph (an entirely ordinary shape for a memory change) leaves
   the old "before" text sitting inside the new "after" text as a substring. Step 4's exact-match
   check would still find that substring and re-apply the item, silently double-applying it; it
   does *not* fail closed on its own for this shape of edit. So check the annotation first, before
   ever reaching step 4; don't rely on the match failing to catch what the annotation is for.
2. **If the item doesn't parse into that shape, skip it.** The Ratified section is human-authored
   (a person copying or retyping an item free-hand can drop or reword a field) and improve-memory
   only documents the What-changes/File(s)/Before-→-after/Why shape for its own *generated* entries,
   not for what a human writes back into Ratified. If an item is missing a `File(s)` field, or has no
   literal before/after text to match against, treat it exactly like a stale item (step 4): record it
   as **skipped: unparseable** with a one-line reason, and move on. Never guess at which file or
   text a malformed item meant, and never apply the portion of it that happens to parse while
   dropping the rest.
3. **Read every file the item's `File(s)` field names.** If any named file doesn't exist, treat the
   whole item as unable to apply (next step).
4. **Verify the literal "before" text is still present, verbatim, in the file.** Memory may have
   changed since the overview was drafted (by a person, by a previous dream run, by anything else).
   Require an exact match, the same standard the Edit tool itself enforces: no partial match, no
   fuzzy match, no "close enough." If the exact "before" text is not found in every file the item
   names, **do not apply any part of this item.** Record it as **skipped: stale** with the file(s)
   and a one-line reason ("before text not found verbatim"), and move on. A stale ratified change is
   not a failure to force through; it's a signal the item needs to be re-drafted against current
   content and re-ratified; never overwrite based on a decision made against content that no
   longer exists.
5. **If every named file matches, apply the change**: replace the literal "before" text with the
   literal "after" text in each file, exactly as an Edit call would. Apply an item's files together
   or not at all; never partially apply one item across multiple files.
6. Record what happened (applied / skipped-stale / skipped-unparseable / skipped-already-applied)
   for §10's summary.

**Scope of what dream may touch, stated explicitly**: only `MEMORY.md`, a detail file under
`$MEMDIR`, or a CLAUDE.md (user- or project-level), and only a path a Ratified item's `File(s)`
field names by exact path. Never the overview file itself (`$OVERVIEW`; improve-memory owns
writing that, including the "already applied" annotation; see §7), never its dated archive, never
`$SA_OUT_FILE`, never another skill's `SKILL.md`, never `~/.claude/.dream-slack-webhook` or any
send-results state file, never a file not named by the item being applied. This is a real
privilege the other three skills deliberately lack (session-analysis and improve-memory are both
explicit that they never write memory; send-results only ever posts a message); dream earns it
narrowly, for exactly this one operation, bounded by an exact-match check.

**An item under `## Needs your call` that the human has not moved into Ratified is never
applied.** Not partially, not as a "safe subset," not even the parts of it that look mechanical.
It stays exactly what improve-memory called it: a draft for a human to decide, and until it's
ratified, dream treats it as unreviewed content.

## 6. Read session-analysis's output at its project-scoped path: the remaining collision risk

Invoke `session-analysis` with mode `dream` (its own SKILL.md, unmodified: §2.2 through §2.4). It
writes its extraction to `$SA_OUT_FILE` as computed in §2 (the project-slug-scoped path
session-analysis's own §2.2 derives, under `$TMPDIR` (or `/tmp`)). Read that computed path; do not
edit session-analysis's script to redirect it and do not invent a different output path of your
own: that file's location is entirely session-analysis's decision; dream only mirrors its formula
to find it.

Scoping the path by project slug closes the cross-project case: two different projects' dream
cycles (or a dream cycle here overlapping a bare `/session-analysis dream` run against a
*different* project) now write to different files and cannot clobber each other. **The path still
carries no PID**, so one collision risk remains: worth stating plainly rather than claiming
concurrency is now safe: two concurrent runs against **this same project** (two dream cycles here,
or a dream cycle overlapping a bare `/session-analysis dream` run on this same project in another
terminal) still write the identical file and can clobber each other mid-run. dream cannot fix this
without modifying session-analysis to add a PID or `mktemp` component to its own path, which is out
of scope for this skill: that's session-analysis's own decision to revisit, not something dream
patches around. Mitigate procedurally instead: invoke session-analysis's dream mode and read
`$SA_OUT_FILE` back-to-back with nothing else interleaved, to keep the window as small as possible,
and sanity-check the file actually looks like a fresh extraction (its own header line names how
many of the 10 transcripts were read) before trusting it. Operationally: **do not run two dream
cycles (or a dream cycle and a bare `session-analysis dream`) concurrently on this same
project.** That remains a limitation of the composed skill (now narrowed to same-project overlap
only), not something this build works around by changing session-analysis.

## 7. Run improve-memory

Invoke `improve-memory` (its own SKILL.md, unmodified) with the learnings list just extracted.
improve-memory does its own full job unchanged: it re-reads `$OVERVIEW` itself, and if a Ratified
section is present it carries that section forward verbatim into the new overview, running its own
mechanical "does before→after already match disk" check per item (its §2), which is how an item
dream just applied in §5 gets annotated `Status: already applied.` in the *new* overview, without
dream ever writing to the overview itself. improve-memory then writes fresh `## Auto-approved` and
`## Needs your call` sections from its own analysis, plus the dated archive copy (its §10). Take
its reported live-overview path back as `$OVERVIEW` for §10.

## 8. Ordering, and why it's deliberate

In `full` mode with a reviewed overview, §5 (apply) runs before §6–§7 (fresh analysis). This is
what the build calls for, and it's the right order for a concrete reason: improve-memory's own
mechanical checks (its §3–§6: duplicate index lines, dangling wiki-links, stale labels) run
against whatever is on disk *at the moment it runs*. Applying first means the new overview reflects
the memory as it now stands, post-cleanup: it won't re-flag a defect that was just fixed, and its
"already applied" annotation on the just-applied Ratified item (§7) is only possible because the
disk already matches "after" by the time improve-memory looks. Running analysis before apply would
produce a new overview describing memory that's about to change out from under it.

## 9. `apply-fixes` mode

Run only §2 and §3, then branch on what §3 found. Skip §6–§7 in every branch below: no
session-analysis or improve-memory call, no new overview, regardless of outcome.

- **`$OVERVIEW` does not exist on disk at all.** There is no file to apply against, and nothing
  valid to hand `send-results` as `FILE_PATH` (send-results §4 requires the path to exist and hard
  -fails otherwise). This is the **one named exception** to §10's "every run ends with
  send-results": report in-session, plainly, that no memory-improvement cycle has ever produced an
  overview for this project, suggest running `full` first, and **do not call send-results.** Stop
  here; do not force a call with a path that doesn't exist just to satisfy §10's usual rule.
- **`$OVERVIEW` exists but §3 found it not reviewed, or reviewed-but-malformed (§3).** There is
  nothing safely applicable. Don't fall back to running an analysis: that would silently turn
  `apply-fixes` into `full`. Go to §10 with a summary saying so; `$OVERVIEW` exists, so the normal
  send-results call still applies here.
- **§3 found a well-formed Ratified section.** Run §5. Then go to §10.

## 10. Deliver through send-results

Every dream invocation ends with exactly **one** `send-results` call (including a `full` run that
found no learnings, and an `apply-fixes` run that had nothing ratified to apply), with **one named
exception**: an `apply-fixes` run against a project with no overview file on disk at all (§9), where
there is nothing valid to hand `send-results` as `FILE_PATH`. Outside that one case, the point of
the record is knowing a run happened and what it found or didn't; a silent no-op run is
indistinguishable from a run that never happened at all, which defeats the reason this skill posts
anywhere.

**`FILE_PATH`**: the **live** overview path, `$OVERVIEW` (`$MEMDIR/memory-improvement-overview.md`)
(not the dated archive). The live file is what a human must open and edit to add or extend
`## Ratified by ...`, and it's the exact path §3 reads next run, so it's the actionable artifact, not
a snapshot. History isn't lost by pointing here: improve-memory's own dated archive (its §10)
independently preserves every run's content regardless of what dream sends, and `SUMMARY` (next)
carries the substantive findings into the Slack message itself, per send-results' whole design:
the message is meant to stand alone as a record precisely *because* the file it points to can
change. Pointing `FILE_PATH` at the archive instead would hand the human a snapshot they can't act
on to ratify anything.

**`SUMMARY`**: compose the actual findings, not a stub: this is the durable record per
send-results' own contract, and the live file it points at gets overwritten by the next run. Include:

- Which mode ran, and what §3 found: reviewed, not-reviewed, or reviewed-but-malformed.
- For each Ratified item touched in §5: applied (file + one-line what-changed), skipped-stale
  (file + reason), skipped-unparseable (file, if named, + reason), or skipped-already-applied:
  every item, not just the applied ones, so a skipped-stale or skipped-unparseable item is visible
  to the human who needs to re-ratify or re-draft it.
- For a `full` run: session-analysis's own header line (transcripts read / contributed), a compact
  view of the new overview's `## Auto-approved` and `## Needs your call` (counts plus the one-line
  "what changes" for each, not the full before/after bodies), and a note that the complete detail
  lives in the file at `FILE_PATH`.
- For `apply-fixes` with nothing ratified: say so plainly.

Both `FILE_PATH` and `SUMMARY` must be `export`ed before invoking send-results' script: a plain
assignment is invisible to the separate `python3` process that script runs in, and fails with
"SUMMARY is required and was empty." Leave `SEND_RESULTS_DEDUP_WINDOW_SECONDS` at its default
(900s) unless the human running dream asks for something else; that guard existing is a feature
here too: a dream cycle re-run by mistake moments apart shouldn't double-post either.

## 11. Report delivery status plainly, same standard send-results itself uses

Relay send-results' own reported status verbatim (HTTP status and body, or a duplicate-skip
notice); never claim delivery because the call merely completed without an exception, per
send-results §9. Report every skipped-stale item from §5 with the same visibility as an applied
one; a partial, rosy summary defeats the reason this skill exists.
