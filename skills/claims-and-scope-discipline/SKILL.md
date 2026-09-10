---
name: claims-and-scope-discipline
description: "Verifying a written claim about code — a review finding, a ticket, a plan step — before acting on it, and deciding what a fix may touch. Use when a finding's citation does not match the code, when a ticket prescribes the fix or quantifies its blast radius, when a ticket reads Done and the repo has more than one branch lineage, when a defect crosses a service or scope boundary, when two tickets describe one defect, when a diff looks small enough to skip review, when verifying a claimed deletion or a check that could not run, when shared test infrastructure must change, when a change implies deploy-time ordering, when several findings cluster in one area, or when separately-reviewed branches will collapse into one integration merge. Not grouping already-verified findings into a fix plan (root-cause-fix), orchestration control flow or agent briefing (plan-rollout), or git/worktree mechanics (git-worktree-topology)."
---

# Claims and scope discipline

A review finding, a ticket, and a plan step are the same object: **a written claim about code at a
moment**. §1–5 are what a reader owes such a claim before implementing it. §6–13 are the other
side — what a review, a diff, or a green check cannot show, and so what its silence does not prove.

**Before implementing any finding: classify its drift (§1) and confirm it belongs to this scope
(§6).** With every finding classified and scoped, **call `/root-cause-fix`** to group them by
cause. That skill sends classification back here, so the two are a hand-off, not a loop.

Every rule here came from one 24-hour run — an 81-ticket epic across 15 repo aspects, implemented
by parallel agents. Each cost real work to learn; none is speculative.

## 1. Stale or wrong — classify every drift

Every drift is one of two modes, and assuming which is how an agent invents a false cause:

| Mode | What it means | Response |
|---|---|---|
| **Stale** | true when written, since changed | implement against what the code does now |
| **Wrong** | never true, even at review time | report as a plan error; do not implement |

```
git log --diff-filter=A --format='%h %ad' --date=iso -- <file>
git merge-base --is-ancestor <sha> <review-branch>
```

**"Uncommitted WIP hid it" is not available as an explanation for an already-committed file** — the
false cause an agent produced here after assuming staleness. A wrong location can **change the
fix**: `core.py:255` was cited in a 146-line file whose named function has never existed at any
commit, and wrapping the cited site would have timed out the surrounding error handling. Wrong
counts are cheaper but not free — they size the review gate (§7) and the test matrix.

**Require drift entries *classified*, not merely listed**, in your notes and in any brief you write
(`plan-rollout` (`references/brief-contract.md`) for the rest of what a brief owes its recipient).

## 2. "Done" is scoped to a lineage, not to the repo

**Where a repo has more than one active lineage, a cited ticket's Done status is scoped to *a*
branch, not proven for *this* one.** Find the PR that actually closed the ticket, then:

```
git merge-base --is-ancestor <that PR's merge commit> <your branch>
```

A different question from §1's `--is-ancestor`: that one asks whether a *fact* predated the review,
this one whether a *fix* reached your lineage. Neither *stale* nor *wrong* fits what it catches —
the finding is true, just not here. One Done ticket cited a path absent from the working branch
because two lineages had diverged and the fix landed only on the other one's copy; the identical
defect was live here, tracked by nothing.

**Sweep once one instance turns up** — the gap plausibly exists on every ticket closed by the same
source. One bundled PR closed five tickets into the other lineage, and two later drew independent
fixes here (overlapping scope, not propagation), so "some of these are fine" stops short.

## 3. A prescribed fix is a claim too — check the mechanism, not the mandate

- Where a ticket names the fix, **verify the mechanism can do what the fix requires** before
  endorsing it. Read the library's own docstring and contract, not your model of it.
- A ticket's scope claim ("confined to one function") is a claim, checked like its location claims.
- Where a fix needs a design decision the ticket cannot contain, **rescope to plan-first**: produce
  a plan, stop, and let implementation follow separately, rather than letting an implementer
  improvise an architecture.
- **Separate "the defect is real" from "the prescribed fix works"** — say which failed, or the
  defect gets dropped along with its bad fix.

Both routes one such ticket offered were broken by the platform, not the codebase: the timeout
mechanism is **transaction-scoped** (`SET LOCAL`), so applying it at session acquisition is inert,
and the helper that does apply it correctly holds a transaction across a slow network call another
rule forbids. The orchestrator's error is the reusable part — it read two rules in genuine tension
as "a rule plus a sloppy restatement" and satisfied the first: reasoning about the
**documentation** instead of the **code**.

## 4. A quantified blast radius is behavioural or structural — decide which

**When a ticket quantifies blast radius, decide whether the number is a behavioural claim (test it)
or a structural one (prove it statically), and say which you did.** A ticket promising timeouts to
~20 call sites that lacked them looked like one test's job; the sites funnel through one function
*by construction*, so testing that choke point once covers them and `grep` establishes the rest.
Chasing a structural claim with tests produces either 20 redundant tests or one dishonest one.

**Record no count you cannot afford to see move.** A doc claimed an enum "has 88 members"; the true
count was 148 within a day, then 152, 160, 175 — two agents disagreeing is itself the argument.
Delete the number and point at the definition: today's value is a lookup, not a fact to cache.

## 5. Duplicates: settle with code, and prefer closing to promoting

**Settle a suspected duplicate by reading both cited ranges, never by comparing their prose** — two
tickets in different scopes described one defect, one range the tail of the other. **Promote a
duplicate to a shared record only when the duplication crosses an *execution* boundary.** Here the
two scopes already shared one coordinator and one chain, so a cross-scope record bought no
coordination; closing is cheaper and leaves one place to look.

## 6. Scope leakage runs both ways

**Outward — a review finding outside the current scope is reported, not fixed.** A whole-branch
pass reads everything, so it surfaces real defects belonging elsewhere; one such fix shipped a
regression by generalising a port change into a file whose only automated caller needed the old
value. Two hard stops: a fix that edits a file another aspect owns, and a fix that contradicts
another aspect's own documentation.

**Inward — a pre-existing defect found mid-task gets a ticket, never an inline fix.** Fixing it
inflates a reviewed diff with changes nobody asked for; merely mentioning it means it never gets
done. Check for a duplicate first, **keep it out of the current epic** (parenting it sweeps it into
wave dispatch, the opposite of "not now"), and fix it only if it blocks. Characterise severity as
it is — **345 static-analysis errors are not 345 bugs** when most are guard patterns the checker
cannot narrow through — and where the finding is systemic, **file the cause, not one instance**,
gating new occurrences rather than cleaning up existing ones.

**Establish provenance before acting; pre-existing is the common case**, and a coordinator told to
"fix these three lines" will not stop to ask whether they are in scope:

```
git diff <base>...<aspect-branch> -- <file> | grep -E "^\+.*<pattern>"
```

Empty output means the defect predates the branch — file it per the inward rule.

## 7. A skipped review leaves a false coverage claim behind

Skipping per-PR review for trivial diffs is worth doing, and a line count is the wrong sole
criterion for it. Name the categories that get a full review **however small the diff**: concurrency
and worker/orchestration code, anything touching locks, CAS, claim tokens or transaction
boundaries, database migrations, and infrastructure-as-code.

**Report every skip with its file count, line count, and the rule that fired.** A silent skip reads
downstream as "reviewed and clean" when it was neither. That is a **false coverage claim** — a
weaker check, or none at all, standing in for a stronger one without saying so. It recurs below,
arriving through a scope boundary (§8) and through the toolchain (§10) as well as through this gate.

## 8. A per-scope review cannot see a chain that leaves the scope

Remediating one credential-in-a-URL finding revealed the credential rode in query strings on
**four** hops; the review found the one hop that crossed the repo boundary and missed the three
that did not. **Wherever a scope hands a credential or identifier to another service, "and what
does the receiver do with it next" is not answerable from that scope's findings.** Ask it
explicitly, and expect the answer to generate tickets the review never had — fixing only the front
door and declaring the class solved is the false coverage claim in this position. Where a fix needs
a counterpart to keep accepting the old form "for one remaining caller", that accommodation is a
ticket, not a resting state, or the transition window never closes.

## 9. Build the integration-merge digest as branches land

When many separately-reviewed branches will collapse into one integration merge, keep a running
digest for whoever reviews *that* merge, appended as each branch lands and never reconstructed
after. It is not a changelog — PR descriptions carry that. It records what has been reviewed and at
what depth, so the reviewer of a 298-commit integration can spend effort on what a per-aspect
review structurally cannot see: deploy gates (§12), cross-aspect file collisions (§8 one level up),
deliberate non-fixes, and behaviour changes with runtime consequences.

Nothing forces the append — no test, no reviewer, no merge gate — so the forcing function lives in
the work itself:

- **An aspect's entry is part of its definition of done**, alongside the aspect PR.
- **The coordinator writes its own entry**; it holds the context. The orchestrator writes only the
  cross-cutting sections.
- On a conflict, **call `git-worktree-topology`** (§3) and resolve downward: fold the entry into
  the integration branch, have the coordinator revert its copy.

Every merged PR carries a **review recommendations** section in its description
(`plan-rollout` (`references/second-level-coordinator.md`) owns the format); the digest aggregates those instead of re-deriving them,
which is what keeps it cheap enough to stay alive.

`references/integration-digest.md` — read when building, appending to, or reviving the digest.

## 10. Verify against the artifact, not the narrative

**A deletion is verified by the absence of the thing in the final artifact, never by reading the
diff that claims to remove it.** A commit message, PR body, and code comment all claimed a dead
helper *and* its backing Terraform metric resource were deleted; the comment above the resource had
been rewritten and the 24-line block below it was live. A diff shows what changed, not what
remains — grep the finished file end to end.

Same defect, different costume: a check that could not run, presented as coverage. `terraform
validate` fails in an agent sandbox (no cached provider plugins) while `fmt -check` passes
everywhere, and letting the weaker one stand in silently is a false coverage claim (§7) arriving
through the toolchain. Run what runs, mark `validate` **not run**, name exactly what needs
validating, and ask the human.

**Report your own misses.** The coordinator that left the resource live found it, fixed it, and
posted a correction on the ticket so it would not read as a clean landing. Name that as expected
behaviour in briefs: a coordinator that never reports a miss does not exist.

## 11. Shared test infrastructure: baseline before anything is touched

Rewriting a `conftest.py` that already-merged tests depend on is the highest-risk change in a
multi-wave run, and it ships looking green unless a baseline was captured first:

1. Before touching anything: full `--collect-only` test-ID list, and a full run with `--junitxml`.
2. After each story lands: re-run, diff the JUnit XML.
3. **Same test IDs collected, same pass/fail per ID, zero new skips.** Any drift is a regression,
   not "probably fine".
4. The second story's baseline is the first story's post-state, not the pre-aspect state — or both
   changes fold into one diff and neither is attributable.

**Read the diff in both directions; a test turning green is the more dangerous turn.** And **the
right resolution is scope, not repair** — do not rewrite other aspects' merged tests to accommodate
your fix; scope the change to the directory that needs it and file the general question as a ticket.

`references/test-infra-baseline.md` — read before changing shared test infrastructure.

## 12. Deploy gates are invisible in the diff — ask while the reasoning exists

Three gates in one run would each have broken production, and none was visible in any diff:

- a schema change to an LLM response required a manual `--update-prompts` flag that no normal
  deploy runs — without it every inference call fails validation;
- new service-account env vars had to land in the same `terraform apply` as — or before — the image
  carrying the matching auth change;
- removing an in-process poller made a startup check unconditional, which required adding an env
  var to **two more services than the ticket scoped**, or the API and pipeline services crash-loop.

Only the third was found proactively, by the implementing agent mid-story, because it traced what
the check would do once the flag it was deleting was gone. That is why this is not a review
question: by review time the reasoning that produces a gate has been discarded. The brief demand
("does this change require anything to happen in a particular order at deploy time?") lives in
`plan-rollout` (`references/brief-contract.md`); once found, gates are standing content in the digest (§9).

## 13. Ticket the question, and find the check that is scoped out

When you defer an investigation to a ticket, **the ticket's job is to name what someone has to find
out.** "The test fixture differs from production" is not actionable; "which is true — production
reads through a fresh session so the tests need an explicit refresh, or some production path holds
an ORM object across a commit and the fixture setting has been masking a real bug — with these
three failing test names" is. Encode the question, the candidate answers, and where the evidence
lives.

When several findings land in one area, ask what single check *would* have caught all of them, and
whether that check is scoped out. Four tickets in one run shared one cause: the type checker ran
over source directories only, never over tests, so none of the four could ever be caught by it.
Name the scoped-out check in the tickets — it is worth more than the individual fixes, because it
is the fixable part.

**Ticket the set, not one of thirty-one call sites.** A lone corrected site among thirty wrong ones
hides the pattern instead of starting to fix it.

## Self-improvement protocol

While working under this skill, append dated entries to
`~/.claude/claims-and-scope-discipline-notepad.md`: what fired, what misfired, what the skill
lacked. When everything the work touched is merged and reviewed, present candidate augmentations to
the user; ratified ones land as edits here and the entries get marked extracted.
