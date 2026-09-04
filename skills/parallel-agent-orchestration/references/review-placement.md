# Where reviews execute

The full case for `SKILL.md`'s "Reviews execute here" stub under §1: why coordinators must never
spawn review sub-agents, and how review passes are placed instead.

Left alone, coordinators spawn review sub-agents despite briefs forbidding it in exact words — one
coordinator explained that quiet waiting looked like compliance with the anti-polling guidance.
Results dispatched low arrive high regardless: a review sub-agent's output lands at the orchestrator
instead of the coordinator that spawned it. A coordinator cannot wake itself, so any review it
spawns stalls it. The design:

- **Reviews run in this session only.** Whichever branch needs reviewing — a story PR, a merged
  aspect branch, the integration branch — `/mattpocock-skills:code-review` is invoked here, where sub-agents complete
  and notify instead of dead-ending a coordinator's turn. Fixes route down to the owning
  coordinator.
- **Coordinators never spawn reviewers.** Their final report asks for review — what changed,
  described at function level — and handles the fixes that come back. Two review-and-fix cycles on
  one PR is the working limit; a third means the change is not converging, and that goes to the
  human rather than around again.
- **Fresh context stays fresh.** Reviewer briefs carry the diff, the scope boundary, and the
  finding format — none of the implementer's reasoning, which is the likeliest thing to anchor a
  verdict. Its absence is what keeps independent angles independent.
- **Match the review mode to the change.** For a change to test infrastructure, **execution is the
  review**: the strongest aspect review of one run executed ~900 tests across every package the
  aspect touched and verified each claimed removal against final file contents via `git show`,
  coming back seven hazards clean — while six-angle reading fan-outs elsewhere produced overlaps,
  duplicates, and three angles converging on one wrong answer needing consolidation. Brief it as
  "run the affected suites and report counts", not "review this diff". Reading reviews still earn
  their place — they found the data-corruption path — but they answer different questions than
  running does.
