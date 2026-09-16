# A claim crossing a session boundary

The full case for `SKILL.md` §16 — why a provenance label catches only half the failure, what
attribution does over two hops, and why a predicted total is not transferable.

## The enumeration, not its shape

A summary of `_handle_task_failure` described a two-branch chain where the code and the cited docs
both carry three. The loss happened in the summary, not in the source — "it checks A first, then B"
is exactly the form that drops C, and an enumerated list degrades the same way.

That is why a provenance label does not settle it alone — **a doc-sourced claim that loses a branch
is indistinguishable from a verified one.** The label certifies where a claim came from, not whether
it survived the retelling; it would have been accurate on that message while the content was still
wrong. Two distinct failures, and labelling catches one.

## Label anyway, because it catches the other

- **Mark every cross-session claim verified-against-code or read-from-docs**, and prefer
  "unverified, from reading X" to a bare fact. One claim travelled two hops, was folded into a
  durable trap row, and was recorded as verified by a session that had never run the command. It was
  true — and none of that would have been visible to the next reader.
- **A trap row records who ran the command**, never who was talking about the file.
- **Attribution travels worse than content.** Name the originator when you relay a claim, or the
  next hop assigns it to you. A ledger holding the right attribution does not stop the message from
  carrying a wrong one.

## Open the source a citation names

A citation is a pointer, not evidence, and it is cheap to follow precisely because it is named —
following one is what caught the dropped branch above.

**Stopping at the name is not following it.** Re-reading a cited branch's *name* framed a design
question around error class; reading the branch *body* dissolved the question entirely, since the
branch documents itself as terminal for a deterministic failure — which makes retry semantics, not
error class, the deciding axis.

## A predicted total is a tripwire only for whoever computed it

An expected post-merge `check-event-types` total was handed to a peer as *their* tripwire. That peer
had a pending literal of its own, so its real target was one higher, and adopting the number would
have made its own work read as a stray literal arriving from nowhere.

A predicted total encodes the set of writers its author knew about at the moment of computing, and
it decays both when that set was wrong and when it changes afterwards. **Recompute from your own
position at the moment you need the number** — never carry one forward, never accept one computed by
someone else. The number earns its keep because a wrong count is the cheapest available signal that
an unexpected writer exists, and that only works as a per-writer derivation rather than a shared
constant.

## Know who else is running before you dispatch

Not once something looks wrong. Three commits describing a "ten-ticket triage batch" that was not
this session's ten-ticket batch nearly triggered a duplicate-orchestrator alarm; one `ListAgents`
call settled it.
