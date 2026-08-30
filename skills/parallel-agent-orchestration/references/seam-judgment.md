# Seam judgment

The full case for `SKILL.md` §5.

Guidance that says "confirm the seams under test with the user before writing any test" assumes an
interactive session. An unattended implementer has nobody to ask, and will either stall or pick
silently.

**Name the seams in the plan or ticket, for review, before implementation is dispatched.** Planning
happens with a human present; that is when the confirmation is possible. Treat a missing seam list
like a missing acceptance criterion.

For a run already underway, the seam pass is cheap by construction: each coordinator proposes seams
for its scope and **stops**; **the orchestrator rules on them**; the human receives one batched
summary per wave and holds a veto. Full human review of four waves caught two genuine scope errors
— and both were caught by the coordinators' own analysis, the human only ratifying — which is the
evidence for ruling low and reserving the human for the veto. Implementation inherits its seams
either way and reports a wrong one as a plan error rather than substituting its own.

**Corollary for every concurrency brief:** an agent reaching for `gather` of two workers, a
sleep-based interleaving, or a retry loop to make a test pass has chosen the wrong seam — stop and
report. A flaky concurrency test is worse than none: it passes while the race stays live, and
teaches people to re-run. Ask per story whether the defect can be provoked deterministically — on
one run, every finding turned out to be a missing WHERE-clause predicate, a property of **state**
rather than timing, which turned the tests from timing harnesses into ordinary data fixtures.
