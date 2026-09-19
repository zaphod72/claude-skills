# The integration-merge digest

The full case for `SKILL.md` §9: what the digest contains, why the forcing function had to move
into the definition of done, and how to hand an entry over without a conflict.

## Why it exists at all

Each aspect branch on this run was reviewed three times over before reaching the integration
branch, while the integration branch's own merge into trunk is reviewed at a size none of those
passes approached: 298 commits. A reviewer starting that cold cannot tell what was already
checked from what was never looked at, so they either re-review everything or trust nothing.

The digest buys back exactly that distinction. It is **not** a changelog; PR descriptions already
carry the change list. It records what has been reviewed and at what depth, so the final reviewer
can trust that and spend their effort on the four things a per-aspect review structurally cannot
see:

- **deploy gates** (`SKILL.md` §12): invisible in every diff, and the reasoning that finds them is
  gone by review time;
- **a watchlist of every file two independently-reviewed branches both touched.** This is the
  payoff. A same-file collision between two scopes is the class `SKILL.md` §8 describes, one level
  up: no per-scope review can see it. It is cheap to name while each aspect still remembers its own
  shared-file list, and expensive to reconstruct from a 15-branch diff later;
- **deliberate non-fixes, and deviations already litigated**, so they are not re-flagged as new;
- **behaviour changes with runtime consequences**, plus cross-aspect follow-ups deferred elsewhere,
  so someone can confirm they landed.

## Why the entry is part of the definition of done

The digest rotted once despite a header announcing its own update discipline: it still described
merged PRs as open and covered five of twelve aspects, under an orchestrator who had read that
header. Nothing forced the append: no test, no reviewer, no merge gate. Reconstruction cost two
sub-agents and needed hand-adjudication of contradictions between the harvested and hand-written
halves.

A header asking to be maintained is not a forcing function. An aspect without its entry not being
finished is. The coordinator writes its own entry because it holds the context; the one entry
written that way was the best in the file. The orchestrator writes only the cross-cutting
sections (deploy gates, the watchlist, deliberate non-fixes).

## Hand the entry over as text, do not commit it

The digest lives on the integration branch. Any earlier-cut aspect branch that appends its own copy
conflicts at end-of-file; observed twice, identically, and it will happen with every long-lived
shared doc. So the coordinator **hands its entry over as text** for the orchestrator to append, and
there is no conflict to resolve.

When a conflict happens anyway, resolve it **downward** (`git-worktree-topology` §3): fold the
entry into the integration branch and have the coordinator revert its copy. Never merge the
integration branch into the aspect branch to clear it.

## Where the raw material comes from

Every merged PR carries a **review recommendations** section in its description
(`plan-rollout` (`references/second-level-coordinator.md`) owns the format): what was reviewed and at what depth, cross-cutting
concerns for the level above, and what needs no re-review. The digest aggregates those sections
rather than re-deriving them from the diffs, which is what keeps it cheap enough to stay alive.
