---
name: benchmark-code-graphs
description: "Use when a repo has multiple overlapping code-intelligence tools (gitnexus, graphify, understand-anything, LSP) and you need to determine empirically which to trust for which task, then write the routing rules into that project's CLAUDE.md. Also use when generated CLAUDE.md/AGENTS.md blocks contain MUST/NEVER rules whose accuracy has never been verified against the actual repo."
---

# /benchmark-code-graphs

Benchmark the overlapping code-graph tools in a repo against grep ground truth, then write
task-routing rules into the project `CLAUDE.md`.

## Why this exists

These tools ship with self-confident generated instructions ("MUST run impact before editing any
symbol", "NEVER commit without detect_changes"). Those rules are written by the tool vendor, not
measured against your repo. In at least one large Python monorepo every one of the following was
false: the mandated `base_ref` was the wrong branch, the mandated `rename` command did not exist,
the mandated `explain` command was MCP-only and needed an index flag that had never been run, and
the mandated `impact` check returned `risk: LOW` for a function with two live callers.

The point of this skill is to replace assertion with measurement.

## Ground rule

**Do not trust any tool's documentation about itself. Measure it.** Every claim written into
CLAUDE.md must be backed by a command actually run in this repo, with its output. Cite `file:line`
and real numbers, not adjectives.

---

## Phase 1: Inventory

For each tool establish: installed? indexed? how stale? how do I invoke it?

- `which graphify`; `ls graphify-out/`; mtime of `graphify-out/graph.json`
- `ls .gitnexus/`; `node .gitnexus/run.cjs status` (prints indexed vs current commit)
- `ls .ua/` or `.understand-anything/`; read `meta.json` for `gitCommitHash`
- Python LSP: confirm a server responds at all (see Phase 4 trap 8)

Two things that are easy to miss:

**MCP tools may not be loaded.** gitnexus is often registered in `~/.claude.json` yet absent from
the session tool list, because MCP servers handshake at session start. A newly installed server
needs a client restart. `node .gitnexus/run.cjs <cmd>` serves the identical index: confirm parity,
don't assume it, and prefer the CLI in written guidance since it always works.

**Check for hooks.** Look in `~/.claude/settings.json` and `.claude/settings*.json`. gitnexus
commonly installs a `PreToolUse` hook on `Grep|Glob|Bash` that auto-injects graph context into
every search. If present, index staleness silently contaminates all your work: that belongs in
CLAUDE.md.

---

## Phase 2: Choose test symbols deliberately

Not at random. You need at least these four, and ground truth from grep **before** consulting any
graph:

1. A function called via a **lazy / function-local import**
   (`def f(): from x import y; y()`). FastAPI `lifespan`, plugin loaders, and circular-import
   workarounds are good hunting grounds. This is the highest-yield test.
2. A widely-called internal function (10+ refs) called from **both** source and `scripts/`, not
   only tests.
3. A **third-party** symbol imported from a dependency.
4. A symbol **added recently**: `git diff <trunk>...HEAD -- '*.py' | grep '^+.*def '`

Ground truth (mind the quoting, zsh eats a bare glob):

```bash
grep -rn "<symbol>" --include='*.py' <source dirs>
```

---

## Phase 3: Head-to-head

Per symbol, record verbatim output:

```bash
node .gitnexus/run.cjs impact <sym> --direction upstream
node .gitnexus/run.cjs context <sym>
graphify explain "<sym>"
graphify affected "<sym>" --depth 2
```

Plus LSP `findReferences` and `incomingCalls` at the definition site.

understand-anything has **no query CLI**: read `.ua/knowledge-graph.json` and
`.ua/domain-graph.json` with `python3 -c` or `jq`.

Score against grep. **Report false negatives separately from false positives**: they have opposite
consequences. Over-reporting wastes time; under-reporting says an edit is safe when it isn't. Only
the second one causes incidents.

### Index fidelity (run for every graph, not just graphify)

Symbol-level accuracy is meaningless if the index describes files that no longer exist. For each
graph, count nodes whose recorded path is gone from disk:

```bash
python3 -c "import json,os; g=json.load(open('<graph>.json')); \
n=[x for x in g['nodes'] if x.get('source_file') and not os.path.exists(x['source_file'])]; \
print(len(n),'orphans of',len(g['nodes'])); \
[print('  ',x['source_file']) for x in n[:10]]"
```

Adapt the path key per tool (`source_file`, `filePath`, …). A few orphans in a just-deleted file is
normal; a cluster in a directory that has been empty for weeks means the refresh path is additive
and never prunes. Report the percentage: it bounds how much of *any* answer from that graph can be
trusted.

---

## Phase 4: Traps

Each of these produced a plausible-but-wrong conclusion before being checked. Work through all
eight.

1. **Staleness confound.** Before calling a miss a resolver bug, prove the call site existed at the
   indexed commit: `git show <indexed-sha>:<path> | grep -n <symbol>`. Otherwise re-index and
   re-run. "Stale index" and "structural blind spot" have opposite remedies: refresh more often
   vs. never trust this answer.

2. **graphify has two kinds of edge.** `[EXTRACTED]` = AST. `[INFERRED]` = LLM semantic pass. If
   graphify wins on recall, check whether the winning edges are `[INFERRED]`. If so that advantage
   applies **only to code older than the last semantic pass**; date it via
   `graphify-out/.graphify_semantic_marker` and the labels file mtime. `graphify update .` is
   AST-only and does **not** regenerate inferred edges. Confirm by running `graphify explain` on
   the recently-added symbol from Phase 2; if it returns no caller edges, the advantage does not
   extend to new code and CLAUDE.md must say so explicitly.

3. **A full `/graphify .` rebuild can be lossy, and `update` has the opposite flaw.** Current
   graphify sends only docs/papers/images to semantic extraction; code is AST-only by design. So
   if the graph holds code→code `[INFERRED]` edges from an older version, a rebuild cannot
   recreate them, only drop them. A shrink guard refuses to write a smaller graph; **do not
   `--force` past it.** Back up `graphify-out/graph.json` first and diff after.

   Prefer `graphify update .`, but know its two gaps:
   - **It is additive; it does not prune deleted files.** Audit with:
     ```bash
     python3 -c "import json,os; g=json.load(open('graphify-out/graph.json')); \
     print(sum(1 for n in g['nodes'] if n.get('source_file') and not os.path.exists(n['source_file'])), 'orphan nodes')"
     ```
     Non-trivial count → `graphify update . --force`, which is documented for exactly this.
   - **It re-anchors `[INFERRED]` edges to new line numbers without re-deriving them**, so a stale
     inferred claim acquires fresh-looking coordinates. Re-anchoring confers false freshness.

   Decide rebuild-vs-update by *failure mode*, not by age: `update` routinely; `--force` after a
   refactor that deletes files; a full rebuild only when you suspect the inferred layer has gone
   **false** (points at moved/renamed code), because a wrong edge is worse than a missing one.

   Before concluding the inferred layer isn't worth preserving, **measure its precision**: sample
   ~15 `[INFERRED]` edges and verify with grep, reporting source→source separately from
   `test_* → target`. In one repo source→source scored 4/4 and captured attribute assignment
   (`get_settings.cache_clear = _custom_clear`) and framework callback registration
   (`FastAPI(..., lifespan=lifespan)`), indirection an AST call-graph cannot see by construction,
   while ~73% of the sample was test noise. Both halves of that finding matter.

4. **The gitnexus CLAUDE.md block is machine-generated.** It sits between
   `<!-- gitnexus:start -->` / `<!-- gitnexus:end -->` and is regenerated by **both** `setup` *and*
   a plain `analyze`; a bare `analyze` has been observed silently rewriting it. Put your findings
   in a section **outside** the markers. If you also correct the inside, switch all future
   refreshes to `node .gitnexus/run.cjs analyze --skip-agents-md` and note that in the file.

5. **`AGENTS.md` carries a duplicate block.** It's what non-Claude agents read. Fix it too or it
   will contradict CLAUDE.md.

6. **Verify `base_ref`.** The generated block hardcodes `detect_changes(base_ref: "main")`. If the
   real integration branch isn't `main`, that command reports the whole branch divergence as
   "critical" and is useless. Find the true trunk (`gh pr list`, or compare
   `git rev-list --count <candidate>..HEAD`) and record both numbers as justification.

7. **Confirm commands exist.** Run `--help`. Previously found: no `rename` CLI command despite a
   NEVER-rule mandating it; `explain` MCP-only and requiring `analyze --pdg`, never run.

8. **Prove the LSP server is alive before blaming it.** If `findReferences` returns only the
   definition, run `hover` at the same position. Working hover + empty references means a healthy
   server with no cross-package index (common in `uv`/workspace monorepos), a fact that
   overrides any global instruction preferring LSP over grep for reference-finding.

---

## Phase 5: Write CLAUDE.md

One consolidated section, routed by **task type**, not a tool ranking:

- **Comparison table** — index location, refresh command + cost, edge quality / failure mode.
- **Route-by-task bullets** — blast radius; "who calls X"; pre-commit scope; call-chain tracing;
  architecture orientation; free-text exploration; type/signature lookup.
- **Trust rule** — state the asymmetry you measured, with the command and output proving it.
  Example shape: *a HIGH is credible; a LOW or `impactedCount: 0` is not a clearance.*
- **"Don't bother" list** — capabilities strictly worse than grep/Explore. Name them.
- **Cost** — flag what needs an LLM pass to refresh versus what's free AST.
- Replace absolutist MUST/NEVER with calibrated guidance. "MUST run impact before editing any
  symbol" is actively harmful when the tool's *reassuring* answer is the unreliable one.

If the repo has a global instruction this contradicts (e.g. "prefer LSP over grep for references"),
scope the override to the project file rather than editing the global one.

---

## Operating rules

- Back up any artifact before an operation that could overwrite it; diff afterward.
- Refreshing indexes is fine when free/AST-only and the dirs are gitignored; check
  `git check-ignore -v` first. Ask before anything costing an LLM pass.
- Report negative results plainly and accurately. The tool that scored badly is usually the most valuable
  finding.
- If a tool is genuinely redundant, say so. If none are, say that, then name the worthless
  *capabilities* inside each, which is where the real answer usually lives.

## Self-improvement protocol

While working under this skill, append dated entries to `~/.claude/benchmark-code-graphs-notepad.md`: what fired,
what misfired, what the skill lacked. When everything the work touched is merged and reviewed,
present candidate augmentations to the user; ratified ones land as edits to this skill and the
entries get marked extracted.
