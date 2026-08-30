# Reading what comes back

The full case for `SKILL.md` §6.

- **Route a finding to the level that owns it — after verifying it.** A review sub-agent two levels
  down had its output delivered to the orchestrator instead of the coordinator that spawned it —
  this is the main channel for misrouting, not an edge case, and nested story results misroute the
  same way. Both halves matter: unrouted, the defect ships in a PR marked reviewed; routed
  unverified, the coordinator acts on a claim. Expect other agents' children on your desk; verify,
  then route down.
- **Consolidation is yours and cannot be skipped.** Several review angles on one PR can produce
  overlapping, contradictory, and duplicate findings; handed the raw set, a coordinator fixes
  refuted work. Verify each finding yourself, dedupe, rank, and route **one** consolidated list —
  with an explicit *rejected, and why* section, whose absence invites the coordinator to
  re-litigate every rejection.
- **Relay a split verdict as split — and verify unanimity as hard as you verify a split.** Three
  review angles on one diff: two called a change a regression, the third gave a good counter-
  argument that it was intentional and usable. Reporting "two reviewers confirmed" was wrong and
  had to be corrected. The converse fails the same way: three independent angles proposed the same
  fix for one diff and **all three were wrong identically** — the helper's own docstring, four
  hundred lines up, marks it the deliberate generic bucket for exactly the case the merge would
  have reintroduced, and none of the three read it. "Three reviewers agree" would have shipped the
  bug: convergence is evidence of a shared blind spot as readily as of correctness.
- **Kill findings with evidence, and record the kill.** An adversarial verification pass refuted
  two findings outright — a reconcile-delete "data loss" scenario proven impossible (two
  `patient_id` namespaces disjoint through the router), and the mapping merge above. Post the
  refutation with its reasoning in the PR body: a finding killed with evidence is worth as much as
  one fixed, and it stops the next reviewer re-raising it.
- **Verify completion claims separately from work claims.** "Collection succeeds" is not "the
  unblocked tests pass". An agent reported `--collect-only` succeeding; the two sibling files it had
  un-blocked had been unrunnable for as long as the break stood and could have carried stale
  failures.
