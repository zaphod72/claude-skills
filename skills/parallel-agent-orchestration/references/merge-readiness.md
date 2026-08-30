# Merge readiness: green status lies

The full case for `SKILL.md` §3.

GitHub's `mergeable` evaluates each PR against its base **independently**. Two sibling PRs from two
agents can both report `MERGEABLE` and still conflict with each other; whichever merges second
breaks.

*(Observed once, verify in yours: `git merge-tree` also reported clean on a conflict that was real.)*

**The check that holds is an actual merge in a throwaway worktree.** Run it before choosing an order
for sibling merges.

Once the order is settled, the git side — base derivation, `--merge` versus squash, force-push
safety within a chain — belongs to the `git-worktree-topology` skill.
