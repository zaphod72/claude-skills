# Baselining shared test infrastructure

The full case for `SKILL.md` §11: the evidence that the JUnit-diff gate catches what review does
not, and the four rules that decide what to do with a drift once it shows.

The highest-risk change in a 12-aspect run was two stories rewriting one `conftest.py` that tests
merged by three earlier waves depended on. Nothing in either story's diff touched those tests.

## What the gate caught

A test three directories from anything the story edited was silently depending on a removed
`autouse=True` fixture:

```
before      tests=1777 failures=2 errors=0
after       tests=1778 failures=3 errors=1   <- + FAILED and ERROR at teardown
after fix   tests=1777 failures=2 errors=0   <- exact match
```

Without the baseline that ships looking green.

**Fix direction matters:** make the test declare the fixture it needs; do not re-add
`autouse=True`. And concluding that autouse is the only safe answer is a finding about the ticket,
reported as such, not a workaround to apply.

## Read the diff in both directions

A one-line fixture change (`expire_on_commit=False`, to match production) looked strictly like an
improvement until the gate showed it broke three tests in two already-merged aspects. The dangerous
half was not the new failures: making ORM attributes *stop* expiring at commit means a test that
**starts passing** while asserting a stale value is the one lying to you.

Explain both flips. For this class of change, a test turning green is the more dangerous turn.

## Recompute the expected delta for every comparison

One coordinator carried "+3 tests expected" forward from an earlier story-by-story diff into a
comparison where zero change was correct. Had a real +3 appeared, the stale expectation would have
waved it through. State the delta before running, derived from this comparison's own inputs.

## Scope, don't repair

Do not rewrite other aspects' merged tests to accommodate your fix. Scope the change to the
directory that needs it and file the general question as a ticket.

## Free by-product

The baseline surfaces pre-existing failures already live on the integration branch: here two, one
of them the repo's own doc-link checker. Ticket those separately so they cannot be mistaken for the
change's fault, and note the keys in the aspect PR.
