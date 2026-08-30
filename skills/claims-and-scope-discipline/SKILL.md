---
name: claims-and-scope-discipline
description: "Verifying a written claim about code — a review finding, a ticket, a plan step — before acting on it, and deciding what a fix may touch. Use when a finding's citation does not match the code, when a ticket prescribes the fix or quantifies its blast radius, when a ticket reads Done and the repo has more than one branch lineage, when a defect crosses a service or scope boundary, when two tickets describe one defect, when deciding whether a diff is small enough to skip review, when verifying a claimed deletion or a check that could not run, when test infrastructure other tests depend on must change, when a change implies deploy-time ordering, when several findings cluster in one area, or when many separately-reviewed branches will collapse into one integration merge. Not grouping already-verified findings into a fix plan (root-cause-fix), orchestration control flow or agent briefing (parallel-agent-orchestration), handing a run to a successor session (agent-run-handover), or git/worktree mechanics (git-worktree-topology)."
---

# Claims and scope discipline

A review finding, a ticket, and a plan step are all the same object: **a written claim about code at
a moment**. Sections 1–5 are what a reader owes such a claim before implementing it. Sections 6–13
are the other side — what a review, a diff, or a green check cannot show, and therefore what its
silence does not prove.

**Before implementing any finding: classify its drift (§1) and confirm it belongs to this scope
(§6).** Once findings are verified and scoped, `root-cause-fix` groups them into a fix plan.

Everything here came from one 24-hour run: an 81-ticket remediation epic across 15 repo aspects,
reviewed and implemented by parallel agents. Each rule cost real work to learn; none is speculative.

## 1. Stale or wrong — classify every drift, never assume

| Mode | What it means | Response |
|---|---|---|
| **Stale** | true when written, since changed | implement against what the code does now |
| **Wrong** | never true, even at review time | report as a plan error; do not implement |

Telling them apart is two commands:

```
git log --diff-filter=A --format='%h %ad' --date=iso -- <file>
git merge-base --is-ancestor <sha> <review-branch>
```

If the fact was already true at review time, the finding was simply **wrong**. **"Uncommitted WIP
hid it" is not available as an explanation for an already-committed file** — and that is exactly the
plausible-sounding false cause an agent produced when it assumed staleness.

Three wrong findings caught in the first two waves:

- A count of files given as 5 when it was 7, all committed the day *before* the review.
- "~15 endpoints" when there were 9. That number sizes both the diff (feeding the review size gate,
  §7) and the test matrix.
- A cited file that **has never contained the code** — `core.py:255` where `core.py` is 146 lines
  and the named function has never appeared in it at any commit. Correcting it **changed the fix**:
  the right wrap site was in a different file, and wrapping the cited one would have timed out the
  surrounding error handling.

**Require drift entries to be *classified*, not merely listed** — in your own notes and in any brief
you write for an implementer. An agent that assumes staleness will accept a finding that was never
right and invent a cause for it. (The rest of what a brief owes its recipient belongs to
`parallel-agent-orchestration` §4.)

## 2. "Done" is scoped to a lineage, not to the repo

A ticket described a credential-in-query-string fix, marked Done, citing a file path. The path did
not exist on the working branch — not from a rename, but because two branch lineages had
independently diverged (one consolidated several packages, the other never did) and the fix had only
ever landed on the *other* lineage's copy of the logic. The identical defect was fully live on the
working branch, tracked by nothing, because a tracker's status field has no concept of "done on
which lineage." Neither *stale* nor *wrong* fits: the finding was and is true, just not here.

**Where a repo has more than one active branch lineage, a cited ticket's Done status is scoped to
*a* branch, not proven for *this* one.** The check is fast and decisive — find the PR that actually
closed the ticket, then:

```
git merge-base --is-ancestor <that PR's merge commit> <your branch>
```

This is a different question from §1's `--is-ancestor` call, which asks whether a *fact* predated
the review. This one asks whether a *fix* reached your lineage.

**Sweep once one instance turns up**, because the same gap plausibly exists on every ticket closed
by the same source. On this run one bundled PR had closed five tickets by name in its title, merged
into the other lineage; two of the five happened to also get real independent fixes on the working
lineage later — overlapping scope, not propagation — so a naive "some of these are fine" would have
stopped short. The ancestry check settles every ticket in a bundle in one command each, with no
code-reading needed for the yes/no. Reserve the code-reading for what the still-missing fix needs.

## 3. A prescribed fix is a claim too — check the mechanism, not the mandate

One of the run's highest-value catches was a subordinate refusing the orchestrator's instruction.

A ticket said a defect's "fix is confined to that one function" and offered two obvious routes. Both
were broken, for a reason in the platform rather than the codebase: the timeout mechanism is
**transaction-scoped** (`SET LOCAL`), so applying it at session acquisition is inert, and routing
through the helper that does apply it correctly holds a transaction across a slow network call that
another documented rule forbids.

The orchestrator's own error is the reusable part: it read two rules in the same doc as "a rule plus
a sloppily worded restatement" and picked the option satisfying the first. They were two rules in
genuine tension. That was reasoning about the **documentation** instead of the **code**.

- Where a ticket names the fix, verify the mechanism can do what the fix requires before endorsing
  it. Read the library's own docstring and contract, not your model of it.
- A ticket's scope claim ("confined to one function") is a claim, subject to the same check as its
  location claims.
- Where a fix needs a design decision the ticket cannot contain, **rescope to plan-first**: produce
  a plan, stop, and let implementation follow separately, rather than letting an implementer
  improvise an architecture.
- **Separate "the defect is real" from "the prescribed fix works".** The first survived here; only
  the second failed. Say so explicitly, or the defect gets dropped along with its bad fix.

## 4. A quantified blast radius is behavioural or structural — decide which

A ticket said a fix would give ~20 call sites timeouts they lacked. Asked whether one test could
cover that, the right answer turned out to be that **it is not a behavioural claim at all**: all the
sites funnel through one function *by construction*, so testing that function once covers them
because it is the sole choke point. The "all 20 inherit this" half is established by `grep`, not by
a red/green test.

**When a ticket quantifies blast radius, decide whether the number is a behavioural claim (test it)
or a structural one (prove it statically, and say which you did).** Chasing a structural claim with
tests produces either 20 redundant tests or one dishonest one.

**And record no count you cannot afford to see move.** A doc claimed an enum "has 88 members"; the
true count was 148 within a day, then 152, then 160, then 175 as reported by a second agent — the
two agents disagreeing is itself the argument. Delete the hardcoded number and point at the
definition instead: today's value is a lookup, not a fact to cache in prose.

## 5. Duplicates: settle with code, and prefer closing to promoting

Two tickets in different scopes described one defect. It was settled by reading both cited ranges
and finding one was the tail of the other — not by comparing their prose. It was then closed as a
duplicate rather than promoted to a new cross-scope record, because the two scopes already shared
one coordinator and one chain, and a separate record buys no coordination the shared chain does not
already provide.

**Promote a duplicate to a shared record only when the duplication crosses an *execution*
boundary.** If one agent will reach both, closing is cheaper and leaves one place to look.

## 6. Scope leakage runs both ways

**Outward — a whole-branch review pass surfaces other scopes' problems.** A review run against a
whole aspect branch reads everything, so it finds real defects belonging elsewhere. One such fix
shipped a regression: it generalised a port change into a file whose only automated caller needed
the old value, contradicting a *different* aspect's documented invariant.

**A review finding outside the current scope is reported, not fixed.** Two hard stops: a fix that
edits a file another aspect owns, and a fix that contradicts another aspect's own documentation.
Both go to follow-ups for the owning scope. This matters more as waves widen — cross-aspect file
ownership is exactly where an out-of-scope fix is least likely to be caught.

**Inward — a pre-existing defect found mid-task.** Fixing it inflates a reviewed diff with changes
nobody asked for; merely mentioning it means it never gets done. **File a ticket, check for a
duplicate first, keep it out of the current epic, and fix it only if it blocks.** Keeping it out of
the epic is mechanical rather than cosmetic: parenting it sweeps it into wave dispatch, which is the
opposite of "not now".

Quantify before filing, and characterise severity as it is. A static-analysis run reporting **345
errors is not 345 bugs** — sampling the dominant rule showed most were guard patterns the checker
cannot narrow through. Saying so is the difference between a useful ticket and an ignored one. Where
the finding is systemic, **file the cause, not one instance**, and recommend gating new occurrences
over cleaning up all existing ones.

**Before acting on any finding, establish provenance — pre-existing is the common case.** Four
times across one run the orchestrator nearly dispatched a coordinator to fix text it had never
written; the check took seconds each time:

```
git diff <base>...<aspect-branch> -- <file> | grep -E "^\+.*<pattern>"
```

Empty output means the defect predates the branch: file it per the inward rule above rather than
routing it into this scope. The check protects both the coordinator's time and the boundary — a
coordinator told to "fix these three lines" will not stop to ask whether they are in scope. Both
near-misses still turned into real findings: chasing one surfaced eight files across source, tests,
and Terraform referencing plan documents that no longer existed.

## 7. A skipped review leaves a coverage claim behind

Skipping per-PR review for trivial diffs is worth doing, and a line count is the wrong sole
criterion for it. Name the categories that get a full review **however small the diff**: concurrency
and worker/orchestration code, anything touching locks, CAS, claim tokens or transaction boundaries,
database migrations, and infrastructure-as-code.

**Report every skip with its file count, line count, and the rule that fired.** A silent skip reads
downstream as "reviewed and clean" when it was neither — the same false-coverage problem as §8 and
§9, arriving through the gate instead of through the scope boundary.

## 8. A per-scope review cannot see a chain that leaves the scope

Remediating one credential-in-a-URL finding revealed the credential rode in query strings on
**four** hops, not one. The review found the single hop that crossed the repo boundary and missed
the three that did not — two inside the other service, one outbound from this one.

**Wherever a scope hands a credential or identifier to another service, "and what does the receiver
do with it next" is not answerable from that scope's findings.** Ask it explicitly, and expect the
answer to generate tickets the review never had.

Fixing only the front door and declaring the class solved is the failure mode. Where a fix requires
a counterpart to keep accepting the old form "for one remaining caller", that accommodation is a
ticket, not a resting state — otherwise the transition window never closes.

## 9. Build the integration-merge digest as branches land

When many separately-reviewed branches will eventually collapse into one big integration merge, keep
a running digest for whoever reviews *that* merge — built as each branch lands, not reconstructed
after. On this run each aspect branch was reviewed three times over before reaching the integration
branch, while the integration branch's own eventual merge into trunk is reviewed at a size none of
those passes approached; a reviewer starting that cold cannot tell what was already checked from
what was never looked at.

The digest is not a changelog — PR descriptions already carry that. It is specifically:

- what was reviewed, and at which layer;
- deviations already litigated, so they are not re-flagged as new;
- cross-aspect follow-ups deferred elsewhere, so someone can confirm they landed;
- **a watchlist of every file two independently-reviewed branches both touched.**

That last one is the payoff. A same-file collision between two scopes is exactly the class of defect
no per-scope review can see (§8, one level up), and it is cheap to name while each aspect still
remembers its own shared-file list, expensive to reconstruct from a 15-branch diff later.

The digest rotted once despite a header announcing its own update discipline — it still described
merged PRs as open and covered five of twelve aspects, under an orchestrator who had read that
header. Nothing forced the append: no test, no reviewer, no merge gate. Reconstruction cost two
sub-agents and needed hand-adjudication of contradictions between the harvested and hand-written
halves. So the forcing function moved into the work itself:

- **An aspect's entry is part of its definition of done**, alongside the aspect PR — an aspect
  without its entry is not finished.
- **The coordinator writes its own entry**; it holds the context. The orchestrator writes only the
  cross-cutting sections — deploy gates, the watchlist, deliberate non-fixes. The one entry written
  this way was the best in the file. Better still, the coordinator **hands the entry over as text**
  instead of committing it to the aspect branch: the digest lives on the integration branch, so any
  earlier-cut branch that appends its own copy conflicts at end-of-file — observed twice,
  identically, and it will happen with every long-lived shared doc. Handed over, there is no
  conflict to resolve.
- When a conflict happens anyway, resolve it downward (`git-worktree-topology` §3): fold the entry
  into the integration branch, have the coordinator revert its copy — never merge the integration
  branch into the aspect branch.

What the digest is for, because it drives the whole structure: not a changelog — PR descriptions
carry that. It records what has been checked and at what depth, so the final reviewer of a
298-commit integration can trust that and spend effort on the four things a per-aspect review
structurally cannot see: deploy gates (§12), cross-aspect collisions (the watchlist), deliberate
non-fixes, and behavior changes with runtime consequences.

The raw material comes from below: every merged PR carries a **review recommendations** section in
its description (`aspect-coordination` owns the format) — what was reviewed and at what depth,
cross-cutting concerns for the level above, and what does not need re-review. The digest aggregates
those sections instead of re-deriving them, which is what keeps it cheap enough to stay alive.

## 10. Verify against the artifact, not the narrative

A commit message, PR body, and code comment all claimed a dead helper *and* its backing Terraform
metric resource were deleted; the comment above the resource had been rewritten and the 24-line
block below it was live — and the author's own self-review missed it by reading the diff.
**A deletion is verified by the absence of the thing in the final artifact, never by reading the
diff that claims to remove it.** A diff shows what changed; it does not show what remains. Grep the
finished file end-to-end.

Same defect, different costume: a check that could not run presented as coverage. `terraform
validate` fails in an agent sandbox (no cached provider plugins); `fmt -check` passes everywhere.
The honest pattern, used unprompted by two coordinators: run what runs, mark `validate` **not run**,
name exactly what needs validating, and ask the human — who closes the gap in seconds. A weaker
check standing in for a stronger one silently is a false coverage claim (§7), arriving through the
toolchain instead of through the gate.

**Report your own misses.** The coordinator that left the resource live found it, fixed it, and
posted a correction on the ticket so it would not read as a clean landing. Name that as expected
behavior in briefs: a coordinator that never reports a miss does not exist.

## 11. Changing shared test infrastructure? Capture the baseline before anything is touched

The highest-risk change in a 12-aspect run was two stories rewriting one `conftest.py` that tests
merged by three earlier waves depended on. The discipline that worked:

1. Before touching anything: full `--collect-only` test-ID list, and a full run with `--junitxml`.
2. After each story lands: re-run, diff the JUnit XML.
3. **Same test IDs collected, same pass/fail per ID, zero new skips.** Any drift is a regression,
   not "probably fine".
4. The second story's baseline is the first story's post-state, not the pre-aspect state —
   otherwise both changes fold into one diff and neither is attributable.

It caught a test three directories from anything the story edited silently depending on a removed
`autouse=True` fixture:

```
before      tests=1777 failures=2 errors=0
after       tests=1778 failures=3 errors=1   <- + FAILED and ERROR at teardown
after fix   tests=1777 failures=2 errors=0   <- exact match
```

Without the baseline that ships looking green. **Fix direction matters:** make the test declare the
fixture it needs; do not re-add `autouse=True` — and concluding autouse is the only safe answer is
a finding about the ticket, reported as such, not a workaround to apply.

Free by-product: the baseline surfaces pre-existing failures already live on the integration branch
(here two, one the repo's own doc-link checker). Ticket them separately so they cannot be mistaken
for the change's fault, and note the keys in the aspect PR.

**Read the diff in both directions.** A one-line fixture change — `expire_on_commit=False` to match
production — looked strictly like an improvement until the gate showed it broke three tests in two
already-merged aspects. And the dangerous half was not the new failures: making ORM attributes
*stop* expiring at commit means a test that **starts passing** while asserting a stale value is the
one lying to you. Both flips get explained; for this class of change, a test turning green is the
more dangerous turn.

**Recompute the expected delta for every comparison.** One coordinator carried "+3 tests expected"
forward from an earlier story-by-story diff into a comparison where zero change was correct. Had a
real +3 appeared, the stale expectation would have waved it through. State the delta before
running, derived from this comparison's inputs.

**The right resolution is scope, not repair.** Do not rewrite other aspects' merged tests to
accommodate your fix — scope the change to the directory that needs it, and file the general
question as a ticket.

## 12. Deploy gates are invisible in the diff — ask while the reasoning exists

Three gates in one run would each have broken production, and none was visible in any diff:

- a schema change to an LLM response required a manual `--update-prompts` flag that no normal deploy
  runs — without it every inference call fails validation;
- new service-account env vars had to land in the same `terraform apply` as — or before — the image
  carrying the matching auth change;
- removing an in-process poller made a startup check unconditional, which required adding an env
  var to **two more services than the ticket scoped**, or the API and pipeline services crash-loop.

Only the third was found proactively — by the implementing agent, mid-story, because it traced what
the check would do after the flag it was deleting was gone. That is why this is not a review
question: by review time the reasoning that produces a gate has already been discarded. The brief
demand ("does this change require anything to happen in a particular order at deploy time?") lives
in `parallel-agent-orchestration` §4; the cross-cutting sections of the integration digest (§9)
carry the gates as standing content once found.

## 13. Ticket the question, and find the check that is scoped out

When you defer an investigation to a ticket, **the ticket's job is to name what someone has to find
out.** "The test fixture differs from production" is not actionable; "which of these is true —
production reads through a fresh session, so the tests need an explicit refresh, or some production
path holds an ORM object across a commit and the fixture setting has been masking a real bug — with
the evidence and these three failing test names" is. Encode the question, the candidate answers,
and where the evidence lives.

And when several findings land in one area, ask what single check *would* have caught all of them,
and whether that check is scoped out. Four tickets in one run reduced to *test infrastructure
diverging from production*; their common cause was one line — the type checker ran over source
directories only, never over tests, so none of the four could ever be caught by it. Name the
scoped-out check in the tickets: it is worth more than the individual fixes, because it is the
fixable part.

**Do not fix one of thirty-one call sites.** A lone corrected site among thirty wrong ones hides
the pattern instead of starting to fix it. Ticket the set.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/claims-and-scope-discipline-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
