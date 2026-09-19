# The efficacy axis

**Trigger:** the PR under review changes tests or test infrastructure itself, not just the production code they cover.

Standards and Spec both read the diff; neither tells you whether the suite actually catches
anything: only running it, deliberately broken, does. Add a third reviewer that mutates the code,
runs the suite, and records what goes red. Shared test infrastructure is never a trivial finding
either way (a test turning **green** is the more dangerous direction, and neither shows in the
diff, per `SKILL.md`'s `is_never_trivial()`). Baseline it first: `claims-and-scope-discipline` §11 and
`claims-and-scope-discipline/references/test-infra-baseline.md` own that procedure.

When the authors already mutation-tested, spot-check their list for truthfulness rather than
re-running it, and spend the saved effort where nobody has mutated yet: one such pass found a
column no test asserted after a detach, including the test named for that detach.

## A. Mutate the harness, not only the code

Where a test's determinism rests on a harness mechanism (a scripted barrier, a fake clock, a
seeded shuffle), mutate the *mechanism* alongside the production code, and ask two questions
instead of one: does the suite stay green, and does it **stop catching what it is designed to catch**?
The second question is the one that finds a **disarmed** test: a scripted race can quietly degrade
into scheduling luck, and nothing notices, because everything stays green against correct code.
Only an *executing* axis finds this: a mechanism's own docstring can be confident and wrong, and
both reading axes will pass it.

**Worked example.** A barrier's `wait_for` (the half that blocks one worker until the other
signals `reached`) was neutered to a bare `return`, and the suite run ten times. Two cases stayed
green 10/10 against correct code either way. With the script intact, those same two cases caught a
real defect (`skip_locked=False`) 5 times out of 5; neutered, 0 out of 5: the two cases whose
catch rate died are the ones the suite proves the barrier earns. A third case went red either way:
belt-and-braces, not load-bearing. **Report:** every harness mechanism in scope, named, and for
each one both arms' catch rate, not a single green/red verdict.

## B. Choose a mutation the suite could survive

A mutation that breaks construction, imports, or syntax reddens everything and measures nothing:
an experiment whose result is fixed in advance is not evidence, however much output it produces.
Choose the variant that discriminates: one a correct suite could plausibly still pass. A cheap
throwaway probe, built first, is the fast way to confirm the difference is observable at all
before committing to a full run. **Report:** why each chosen mutation is survivable, and any
mutation rejected, with the ground for rejecting it.

## C. Give a fence with N terms N cases

Where a guard rejects on a conjunction of terms, write one test per *term*, not one per guard.
"The fence rejected the stale write" passes if **any** term rejects, so it cannot tell you which
term did the work; a row differing on three terms proves nothing about any one of them, and
dropping a single term in production still passes every existing case. Generalises past database
CAS fences to any compound predicate. **Report:** the guard's terms, enumerated, and coverage per
term.

## D. Mutate each half of a cooperating pair separately

Where a primitive has two halves that cooperate (signal and wait, acquire and release, encode and
decode), mutate each half on its own. "We fixed the tautology" is a statement about one edit, not
about coverage: a self-test rewritten to remove a tautological assertion tends to fix the half its
author was looking at, leaving the other half uncovered. **Report:** where a brief names a
primitive, a mutation per half, and both results.

## Reading a mutation result

An uncaught mutation has three explanations; name which one before filing a coverage gap: the
test is **hollow** (it passes whether or not the behaviour it names is present), the mutated code
is unreachable, or the property genuinely does not hold.

A result means nothing without its control arm: run the unmutated baseline, and, wherever a helper
is credited with a catch, run without that helper too. A caught mutation proves the suite works,
not that your helper caused the catch.

## Glossary

- **efficacy axis** — the third review axis, alongside Standards and Spec: where those read code,
  this one runs it, via mutation. Used whenever the deliverable is tests or test infrastructure.
- **mutation testing** — break one line of production code, run the suite, record what goes red;
  measures whether a suite catches what it claims to.
- **meta-mutation** — mutation testing aimed at the harness itself, asking if the tests still test.
- **control arm** — the comparison that makes a mutation result mean something: the unmutated
  baseline, and, where a helper is credited with the catch, the run without it.
- **hollow test** — a test that passes whether or not the behaviour it names is present.
- **tautological assertion** — an assertion whose expected value is computed by the same code
  under test, so a regression agrees with itself on both sides and the test still passes.
- **fence** — a guard on a write that rejects it unless the row still matches every term the
  caller expected; implemented as compare-and-swap.
- **CAS** — compare-and-swap: read a value, then write only if it has not changed since the read.

## Elsewhere

- Review rounds, the cap of three, and the review file: `references/second-level-coordinator.md`.
- The brief's required fields: `references/brief-contract.md`.
