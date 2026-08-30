# Shared files: sequence, don't reassign

The full case for `SKILL.md` §2.

When a ticket turns out to need a file another aspect owns, the fix is **ordering**, not
reassignment — the claim on the ticket stays valid, and moving it discards the context its assignee
already has.

Sequence the later agent behind the earlier one, and brief the later one to:

1. Merge the earlier agent's branch first.
2. Work from the **merged diff**. The line numbers in the original finding are already stale.

Ask the earlier agent to describe its changes **at function level** in its PR body, since line
numbers are useless to a reader of a merged diff.

**A conflict in a document another writer owns is reported, never resolved.** One coordinator found
its aspect PR `CONFLICTING`, diffed all 18 other files to prove the conflict scoped to one shared
doc, established the doc was under active restructuring by someone else, and stopped — reporting
with evidence instead of guessing at the target shape, because guessing risks duplicating or
contradicting whatever has already been extracted. This recurs, and more often than not the change
the agent would have made turns out to be wrong. Escalation here is competence, not caution. Code
conflicts in files you own, you resolve; shared-doc conflicts go up.
