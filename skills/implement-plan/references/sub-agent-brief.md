# Sub-agent brief and return contract

Moved from `SKILL.md` step 8 ("Run the wave") — fill this in per sub-agent before dispatch.

## The sub-agent brief

Give each sub-agent exactly this, filled in:

- **Its PR**: id, branch name to create, base ref to branch from.
- **Its plan section**, verbatim, from the plan doc at its homed `plan/` path.
- **Cross-branch constraints** from the plan that name this PR.
- **What its ancestors actually built** — accepted deviations plus the ancestor change inventory entries touching this PR's plan section, both carried forward from step 9. Deviation notes already written into the plan's PR sections count as accepted deviations here.
- **Every claim you falsified in step 3 that touches this section**, with the correction. Otherwise the agent reads the plan and rebuilds the error you already found.
- **The numbers you measured**, as targets it must reproduce — plus, explicitly: *"If your number differs, that is a bug in your work. Do not adjust the expectation to match your output."* Without that clause an agent that gets 4 where you measured 7 writes down 4 and moves on.
- **The discriminating test** — name the one test that fails if the design is wrong, and say that it is the one that matters. An agent handed a list writes all of them equally; an agent told which is load-bearing designs toward it. "Two coverages on one carrier must issue exactly one model call" is a design constraint disguised as a test.
- **The disagreement rule, wherever this PR makes a value deterministic:** *for every value this makes deterministic, write a test in which the other source would give a different answer.* A fixture where both sources agree proves nothing about which one the code actually read — that is precisely how a wrong-source bug survives a fully green suite.
- **Traps earlier agents hit**, not just interfaces they changed: a DDL splitter that breaks on a semicolon inside a prose comment, a join that silently returns zero rows unless a prefix is stripped, a duplicated block shadowing a live assignment. These cost the discovering agent real time and are invisible in a diff.
- **What not to touch**, named explicitly: files a later PR owns, symbols a later section deletes, tables belonging to another repo. Sequential sections reworking one module will otherwise undo each other, and "leave X working, a later PR removes it" is not inferable from a plan section. **Name the plan doc as the one repo file you write**: the agent reports plan errors in its return contract; the orchestrator writes them into the doc, and an edit made from a worktree strands the edit on the agent's own branch. Tell the agent findings go on its Jira ticket (`plan-docs` §3 explains why that has to be said explicitly).
- **Long test suites belong in the background** (`parallel-agent-orchestration` §4). Specific to this brief: run the PR's own test files first — those catch the real failures in seconds — before backgrounding the full suite.
- **An explicit invitation to contradict the brief**, not only the plan (`parallel-agent-orchestration` §4's refuse-a-wrong-instruction rule) — quote it: *"report anything here that turns out to be wrong, including anything I have told you."*
- **Repo conventions**: point at `CLAUDE.md` and the real task runner. Read `[tool.poe.tasks]` in `pyproject.toml` (or `scripts` in `package.json`) for the actual task names rather than assuming them.
- **First action, before any edit:**
  ```
  git rev-parse --verify <base-ref>    # stop and report if this fails
  git checkout -b <branch> <base-ref>
  git log --oneline -1                 # report this SHA back
  ```
- **Verification bar**: run the repo's own test, lint, and type tasks. Green means commit and open a normal PR. Red means still commit, open the PR as a draft, and report the failure — plus whether the same failure reproduces on the base ref, since a stacked child inherits red from its parent.
- **Cases only a live run can settle**: if this PR's section implies behavior that can't be confirmed from the diff alone (depends on live data, timing, concurrency, an external service), add a structured log line at the decision point before opening the PR, and report the case in `runtime_only_concerns` rather than silently trusting the tests.
- **PR creation**: `gh pr create --base <parent-branch>` after pushing. Under `--no-pr`, commit only: no push, no PR.
- **The return contract** below, quoted to it.

## Sub-agent return contract

Require these fields back:

- **status** — `complete`, `partial`, or `blocked`.
- **branch**, **base_ref**, **base_sha** — the SHA actually branched from.
- **commits** — SHAs and subjects.
- **pr_url** — or `none (--no-pr)`.
- **checks** — tasks run, pass or fail, failure excerpt, and `reproduces_on_base`: yes / no / not checked.
- **changes** — a factual inventory: per entry the file, the symbol, signature, schema, or config key touched, and what changed about it. No judgement about other PRs; this is the raw material for blast radius.
- **deviations** — per entry: what the plan said, what the agent did, why.
- **plan_errors** — factual claims in the plan section that turned out to be false, with the evidence. Distinct from a deviation: a deviation is what the agent chose to do differently, this is where the plan was simply wrong. Ask for it explicitly, or you will not get it.
- **follow_ups** — work the plan implies that this PR left undone.
- **runtime_only_concerns** — per entry: what can only be confirmed once the code runs, and the log line added to catch it (or, if none was added, why).
