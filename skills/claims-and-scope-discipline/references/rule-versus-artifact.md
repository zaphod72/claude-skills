# When a rule stands in for the artifact

The full case for `SKILL.md` §15 — both directions of the error from one aspect of one run, and the
three corollaries about what to read and how much of it.

## Both directions, one aspect

- **Inferring failure from a rule.** `poe cov` chains four suites and aborts the rest on the first
  failure, a real and documented hazard, so a green result was called untrustworthy. The hazard had
  not fired: the log carried four invocation lines, four `collected` headers, four summaries, and
  arithmetic that reconciled per-suite and in aggregate. **A known hazard is not evidence that it
  occurred.**
- **Inferring safety from a rule.** A test re-run was scoped to one package, justified as "the other
  three suites import nothing from that package". They import ten distinct modules from it. The
  conclusion survived on a narrower fact — nothing outside the package imports the *changed module*,
  directly or transitively — but the stated reason would have licensed the same scoping for a change
  to a module those suites do import.

Both failures were one command away from being caught.

## Scope a test re-run by import graph

A package-level rule skips exactly the suites most able to catch a
regression in a widely-imported module — the second failure above is that rule surviving on luck.

## Absence of a stated reason is weak evidence of an absent reason

A rate-limit threshold was called an off-by-one defect because "no docstring or test gave a
rationale". It was a third party's published ceiling, where unexplained conservatism is the norm
and the reason lives in their documentation rather than your repo.

## Pick the hunk to verify by blast radius

In one review the peripheral files — Terraform, config
provenance — were verified end to end while the largest hunk, 99 added lines of SQL and threshold
logic, was never opened. Verification effort drifts toward what is easy to check unless the choice
is made deliberately.

## A ticket's stated scope is the problem it names, not the file set it will touch

Cross-language gating tooling turns a one-package ticket into a multi-package diff, and it is
invisible in the ticket text: a new `event_type` fails `check-event-types` until every emitted
literal is dispositioned in Terraform, and one finding's cleanup machinery lived in a different
package entirely. Where a repo gates across languages — event-type checks, schema checks, codegen —
assume any new emitted literal or schema symbol pulls in the other language's files.

Verify a file-level scope claim against the actual diff, or state it as "expected scope, not yet
verified" (`SKILL.md` §16 before handing one to another session). Re-issue the assurance when the
diff lands; it is only as good as its last verification.
