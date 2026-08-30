# Stall detection and the nudge cycle

The rest of `SKILL.md` §1 ("The orchestrator is the pump") — the pgrep clock, the nudge cadence, and
what "still waiting" twice in a row actually means.

- **A 7-story chain is 7 orchestrator nudges, not one dispatch.** Budget a round trip per step, and
  design the run around "resume on completion notification" rather than "the subordinate loops".
  Do not dodge the round trips by fanning a serial chain out in parallel: stories in one aspect
  share a worktree and a moving `HEAD`, and concurrent `checkout -b`/commit/push against one index
  is the hazard the serial design exists to prevent. The nudge is cheaper than either.
- **A dispatched subtask is the only thing happening.** A coordinator can read "runs in the
  background" as "so I have spare time right now" — one announced it would use the idle time to go
  check an unrelated side note, in the same shared worktree its in-flight story was using.
  Background dispatch is async completion of the subordinate, not concurrency for the dispatcher's
  own hands. Put it in every brief: no side reading, no side edits, nothing in the shared worktree,
  until the child reports.
- **A waiting coordinator holds still; the orchestrator owns the clock.** The coordinator cannot
  wake itself and gains nothing by watching, so neither side burns turns on attention. The way to
  know *when* to pump is a backgrounded process watch that completes when the work does:

  ```
  # Bash tool, run_in_background — one notification when the suite exits
  until ! pgrep -f "junitxml=.*after_543.xml" >/dev/null 2>&1; do sleep 10; done; echo done
  ```

  This is the pump's clock — scheduled waiting, not hand-polling between nudges.

**Two consecutive identical reports mean stalled — once the process table says so.** "Waiting on
the background agent" twice in a row is not slow unless something genuinely in flight explains it:
a 6-minute `pytest` or a 14-minute suite is a real wait, and nudging it there wastes the run it is
waiting for. `pgrep -f <the command>` settles which. Process alive: schedule the wake with the
clock above and leave the coordinator alone. Nothing running: tell the agent to stop waiting and
**run the work inline** — this is exactly the false stall the pgrep check exists to catch.

**To pause a chain, send nothing.** The pump property makes pausing free — in-flight work finishes
and nothing new starts — but it also means a "please pause" message is itself a nudge, and resumes
the coordinator that receives it.
