# Why §4's brief demands hold

Evidence behind `SKILL.md` §4's rules — read if a bullet's rationale is unclear.

**Evidence, not conclusions.** Also caught a "dead permission" claim that needed a call-path trace
to justify, and a coordinator's own false positive, which it then self-corrected.

**Refuse a wrong instruction.** Twice on one run a coordinator was told to do something harmful —
add a field to a model that was simultaneously a live LLM response schema, and add a boolean signal
to a prompt where a test proved it would push the model to the wrong answer — and both stopped and
reported instead. These were the run's highest-value catches.

**Check the tickets' own sequencing notes.** One aspect refused the orchestrator's order outright,
citing tickets whose own text specified the opposite — including a doc story correctly told to land
*last*, which then absorbed the documentation debt of everything before it; another surfaced a
third ticket's constraint the orchestrator did not know existed.

**Deploy-time ordering.** Three gates in one run would each have broken production, none visible in
any diff, and only one was found — by the implementing agent, mid-story, because it traced what the
code would do after the flag it was deleting was gone.

**Tee output to a file.** One coordinator ran its suite inside its own shell; the output went to its
transcript, and the wake-up nudge became "your run finished, you have the result and I do not — act
on it."

**Base as ancestry.** One coordinator correctly halted because its brief said `cbcf4abd` and it
found `14245969`.
