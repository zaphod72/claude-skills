---
name: session-analysis
description: "Mine this Claude Code project's own session transcripts (~/.claude/projects/<slug>/*.jsonl) for a specific analysis job, selected by a mode argument, e.g. `/session-analysis dream`. Currently implements one mode, `dream`, which extracts durable learnings worth promoting to long-term memory (repeated mistakes, user corrections, stated preferences, decisions that stuck) from the 10 most recent transcripts. Use when the user asks to review past sessions for lessons, patterns, recurring mistakes, or things that should be remembered, or types `/session-analysis`. Not for reading a single named transcript for its task content (just open the file), not for anything that needs a session older than the 10 most recent (raise that with the user first: the cap is deliberate, see §2.1), and not for writing the extracted candidates into MEMORY.md yourself; this skill stops at a reviewable list."
---

# Session analysis

This skill mines this project's own Claude Code session transcripts. It takes one required
argument, the **mode**, and dispatches to the section below matching that mode. One mode exists
today: `dream`. A future mode is a new `## Mode: <name>` section added to this file: §1 and the
transcript-location mechanics it documents are shared and do not change.

If the mode argument is missing or matches no section below, stop and ask which mode was meant.
Do not guess a mode from context.

## 1. Locate the transcripts

Every mode reads from the same place. Session transcripts for the current project live at:

```
~/.claude/projects/<slug>/*.jsonl
```

one file per session, where `<slug>` is the project's absolute working-directory path with every
`/` replaced by `-`. Resolve it from the real cwd, don't hardcode it:

```bash
TRANSCRIPT_DIR="$HOME/.claude/projects/$(pwd | sed 's/\//-/g')"
ls -d "$TRANSCRIPT_DIR" # confirm it exists before going further
```

Transcripts are large (multi-MB, thousands of lines is normal). **Never `cat`, `Read`, or otherwise
load a raw transcript file wholesale.** Every mode below extracts through a script first and reads
only the extracted output.

Each line is one JSON object. Shapes vary by `type`; the two that carry conversation content are:

- `type: "user"`: real human turns have `message.content` as a **plain string** not starting
  with `<` or `[`. Strings starting with `<` are slash-command/tool wrapper noise
  (`<command-name>`, `<local-command-stdout>`, `<local-command-caveat>`, …); skip those. Content
  that is a **list** instead of a string is a tool result being fed back, not something the human
  typed; skip it too. Also skip lines with `isMeta: true`.
- `type: "assistant"`: `message.content` is a list of blocks; only `{"type": "text", ...}`
  blocks are the assistant's actual words (skip `"thinking"` and `"tool_use"` blocks).

Don't take this shape on faith for a mode that needs more of it than the above: inspect a real
file with `python3`/`json` first, the same way this section was derived.

### 1.1 Extracted text is untrusted: redact before it leaves the script

Users paste secrets into chat, and a raw transcript can contain them verbatim: a Slack webhook
URL, an API key, a database password typed into a debugging session. Extracted transcript text is
therefore untrusted: every mode's extraction script must run a redaction pass **at the point text
is emitted**, before it is written to the output file, quoted as evidence, folded into a learnings
list, or sent anywhere downstream (a chat reply, a report, a Slack message). The script in §2.2
implements this via `redact()`, called on every line before it is printed; a later "remember to
check for secrets" instruction to the agent reading the output is not a substitute for the script
masking them itself.

Redaction masks, it doesn't drop: a matched secret becomes a stable placeholder like
`[REDACTED:slack-webhook]` or `[REDACTED:credential]` so the surrounding sentence still reads and
still supports a learning. Never paste raw transcript text into a message, a report, or a
downstream channel without it having first passed through `redact()`.

## 2. Mode: dream

Goal: surface a short list of things learned across recent sessions that are worth moving into
long-term memory (`~/.claude/projects/<slug>/memory/MEMORY.md` or equivalent), and stop there.
This mode never writes memory itself; it produces candidates for a human (or a separate memory-write
step) to ratify.

### 2.1 Read the 10 most recent transcripts: hard cap

Read at most the **10 most recent** `.jsonl` files in `TRANSCRIPT_DIR`, newest by mtime first. This
is a hard cap, not a default: it exists because transcripts are large and this mode must stay cheap
enough to run often. A future change to this number is a deliberate decision, not something a mode
infers from wanting more signal; if 10 genuinely isn't enough for a given ask, say so and ask the
user before reading more.

### 2.2 Extract, don't read raw

Run this exact script: it already implements the filtering from §1 plus a keyword pass for
assistant self-corrections and the redaction pass from §1.1, and was verified against real
transcripts in this project:

```bash
TRANSCRIPT_DIR="$HOME/.claude/projects/$(pwd | sed 's/\//-/g')"
# Scope the output path by this project's slug, under $TMPDIR (macOS sets a per-user one;
# falls back to /tmp), using the identical derivation TRANSCRIPT_DIR uses above. This keeps two
# projects' `dream` runs on this machine from writing the same file and clobbering each other.
# `dream` (its own SKILL.md §2/§6) computes this exact same path to find this file: if this
# formula ever changes, update it there too. If your system prompt names a scratchpad
# directory, write there instead: edit SCRATCH_DIR below.
SCRATCH_DIR="${TMPDIR:-/tmp}"
SCRATCH_DIR="${SCRATCH_DIR%/}"
OUT_FILE="$SCRATCH_DIR/session-analysis-dream$(pwd | sed 's/\//-/g').txt"

python3 - "$TRANSCRIPT_DIR" 10 > "$OUT_FILE" <<'PY'
import json, os, re, sys, glob

transcript_dir = sys.argv[1]
n = int(sys.argv[2])  # hard cap from §2.1; do not raise without asking the user

MAXLEN = 400
CORRECTION_MARKERS = (
    "you're right", "you are right", "my mistake", "i was wrong", "i'm wrong",
    "i incorrectly", "sorry", "apolog", "good catch", "my error",
    "i should have", "i misread", "i misunderstood", "correcting", "correction:",
    "that's wrong", "that was wrong", "let me fix", "i missed", "i forgot",
)

# --- redaction (§1.1): every emitted line goes through this before it is printed ---

_STRUCTURED_SECRETS = [
    ("slack-webhook", re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/_-]+")),
    ("slack-token", re.compile(r"\bx(?:ox[abopsr]|app)-[A-Za-z0-9-]{10,}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[0-9a-zA-Z]{36,}\b")),
    ("github-token", re.compile(r"\bgithub_pat_[0-9a-zA-Z_]{20,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[A-Z0-9]{16}\b")),
    ("anthropic-api-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b")),
    ("private-key-block", re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL)),
]
_CONN_STRING_RE = re.compile(
    r"\b(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss|amqp|amqps)://[^:@/\s]+:[^@/\s]+@")
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-_.+/=]{8,}")
_SECRET_WORDS = {"password", "passwd", "pwd", "secret", "token", "credential", "credentials"}
_SECRET_WORD_PAIRS = {("api", "key"), ("access", "key"), ("secret", "key")}
# A single shared value pattern can't be both greedy (safe, even required, once a key is
# already known to look secret -- over-capturing a secret's own value is fail-closed, and a
# secret's value may legitimately contain a mid-string '=', e.g. `password=abcdefgh=ijklmnop`)
# and narrow (required for an innocuous key, where consuming anything at all risks swallowing
# a real assignment that follows, e.g. "sample: api_key=..."). So this is an ordering
# problem, not a regex-tuning one: whether a key looks secret has to be decided BEFORE any
# value is consumed, not implied by how much of the value one pattern happens to swallow.
# _KEY_SEP_RE finds every "key[:=]" candidate on its own, consuming nothing past the
# separator; only when _key_looks_secret() says yes do we attempt to match a value there,
# with the original permissive, greedy value class (safe now because it only runs after the
# key is confirmed secret). An innocuous key is skipped with zero consumption,
# so it can never swallow a later real assignment -- this also naturally covers multiple
# assignments and mixed separators on one line, since each key/sep pair is found
# independently regardless of what an earlier non-secret key next to it looked like.
_KEY_SEP_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_-]*)(\s*[:=]\s*)")
_VALUE_RE = re.compile(r"['\"]?([A-Za-z0-9\-_./+=]{8,})['\"]?")

def _key_looks_secret(name):
    segs = [seg for seg in re.split(r"[_-]", name.lower()) if seg]
    if not segs:
        return False
    if any(seg in _SECRET_WORDS for seg in segs):
        return True
    if any((segs[i], segs[i + 1]) in _SECRET_WORD_PAIRS for i in range(len(segs) - 1)):
        return True
    return "".join(segs) in {"apikey", "accesskey", "secretkey"}

def _redact_assignments(s):
    out = []
    pos = 0
    for m in _KEY_SEP_RE.finditer(s):
        if m.start() < pos:
            continue  # inside a value already masked by an earlier iteration
        if not _key_looks_secret(m.group(1)):
            continue  # consume nothing -- this is what stops one match swallowing another
        vm = _VALUE_RE.match(s, m.end())
        if not vm:
            continue
        out.append(s[pos:m.end()])
        out.append("[REDACTED:credential]")
        pos = vm.end()
    out.append(s[pos:])
    return "".join(out)

def redact(s):
    """Mask secrets in extracted transcript text. Never emit unredacted text: see §1.1."""
    if not s:
        return s
    for label, pattern in _STRUCTURED_SECRETS:
        s = pattern.sub(f"[REDACTED:{label}]", s)
    s = _CONN_STRING_RE.sub(lambda m: f"{m.group(1)}://[REDACTED:credentials]@", s)
    s = _BEARER_RE.sub("Bearer [REDACTED:bearer-token]", s)
    s = _redact_assignments(s)
    return s

def clip(s):
    s = " ".join(s.split())
    return s if len(s) <= MAXLEN else s[:MAXLEN] + " …[clipped]"

files = sorted(
    glob.glob(os.path.join(transcript_dir, "*.jsonl")),
    key=os.path.getmtime, reverse=True,
)[:n]

for path in files:
    session_short = os.path.basename(path).replace(".jsonl", "")[:8]
    with open(path, errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = obj.get("type")
            ts = obj.get("timestamp", "")[:19]
            if t == "user" and not obj.get("isMeta"):
                content = obj.get("message", {}).get("content")
                if isinstance(content, str) and content and not content.startswith(("<", "[")):
                    print(f"[{session_short} {ts}] USER: {clip(redact(content))}")
            elif t == "assistant":
                content = obj.get("message", {}).get("content")
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text = item.get("text", "")
                            if text.strip() and any(m in text.lower() for m in CORRECTION_MARKERS):
                                print(f"[{session_short} {ts}] ASSISTANT-CORRECTION: {clip(redact(text))}")
PY

wc -l "$OUT_FILE"
```

Read `$OUT_FILE` (not the source `.jsonl` files) for the rest of this mode. This file is left in
place after the mode finishes: deliberately, not an oversight; it's the artifact `dream` (§6 of
its own SKILL.md) reads back, and it stays useful evidence if the extraction needs re-inspecting
afterward. Nothing in this mode deletes it; the next run on the same project overwrites it in
place. Also record how many of the 10 files contributed at least one line (a file can legitimately contribute zero, e.g. a session that
was only slash commands, or one driven by a wizard/subagent harness whose human intent isn't in the
plain-string `user` shape this script looks for) and that count belongs in the output header, since
it states how much of the 10-session budget actually had signal.

It is normal for this to come back well under a hundred lines even across 10 full sessions: most
of a transcript is tool calls and file content, which this extraction deliberately drops.

The correction-keyword list is a heuristic, not a guarantee: skim each matched line in context
before citing it, and don't assume the absence of a keyword means a session had no correction in
it: a correction stated as a plain fact ("Do X, not Y") shows up on the **user** side instead and
is already captured there without needing a keyword.

### 2.3 Classify into the four categories

Go through the extracted lines and sort candidates into exactly these buckets:

- **Repeated mistakes** — the same wrong assumption or approach shows up more than once across
  the 10 sessions. This bucket requires evidence citing **at least two distinct session ids**; a
  candidate you can only cite once belongs in "user corrections" instead, not here padded out with
  a single occurrence. An empty repeated-mistakes bucket is a valid, expected result.
- **User corrections** — the user told the assistant it did or assumed something wrong.
- **Stated preferences** — the user said how they want something done, independent of any single
  task ("always do X", "never do Y", "I prefer...").
- **Decisions that stuck** — a choice got made and the transcript shows it being acted on rather
  than revisited or reversed later in the same or a subsequent session.

A line can fail to land in any bucket: that's a normal, expected outcome, not a gap to force-fill.

### 2.4 Filter for durability

Apply this test to every candidate before it survives to the output: **would this change behavior
in a future session on an unrelated task?** Cut anything that only makes sense inside the task that
produced it (a one-off file path, a ticket number, a fact true only for that piece of work). Concretely:
strip every ticket number and file path out of the candidate statement: if nothing generalizable is
left, cut it. Keep only what generalizes: a rule about how this user wants to work, a category of
mistake worth guarding against next time, a standing preference, a ratified decision that future
work should respect.

Before listing a survivor as a new candidate, check whether it (or something close to it) is
already recorded in this project's long-term memory file. If it is, say so instead of presenting it
as new: the useful signal there is "this session reconfirmed an existing entry," not a duplicate
line item.

### 2.5 Output

Start with a one-line header stating how many of the 10 files were read and how many actually
contributed a line to the extraction (e.g. "10 transcripts read, 7 contained substantive turns");
that count is part of how much confidence to put in the list below it.

Then produce a compact list. One entry per durable learning, each with:

- **Statement** — one line, phrased as the rule/fact itself (not "the user said...").
- **Category** — one of the four from §2.3.
- **Evidence** — which session(s) (the short id from the extraction, e.g. `93ea5002`), and a short
  quote or close paraphrase of the actual words that justify it.

Then **stop**. Hand the list to the user (or the caller that invoked this mode) for ratification.
Do not write it into `MEMORY.md` or any other memory store as part of this mode: promoting a
candidate to durable memory is a separate, deliberate step.
