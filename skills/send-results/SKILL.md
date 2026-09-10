---
name: send-results
description: "Send a Slack message that stands alone as a durable record: the caller's full content (not a one-line stub) plus a file's absolute path, so a person can read what happened without reopening a file that may already be regenerated, and can still open and edit it directly. Generic — any automation, any kind of file. Takes FILE_PATH (absolute, must exist) and SUMMARY (durable content, capped under Slack's limits); redacts secrets, converts Markdown to Slack mrkdwn, skips exact duplicates, and reports Slack's real delivery status. Use when a task's result needs a durable, readable Slack record plus a file to open directly — a dream/memory-improvement run, a generated report, any file-shaped deliverable. Not for sending a file's raw contents verbatim (the caller composes SUMMARY as the record; this skill never opens FILE_PATH to read it), and not for choosing which Slack channel the message lands in — that is fixed at webhook-creation time and this skill cannot override it."
---

# Send results

This skill posts one Slack message: the caller's own content (SUMMARY) plus a file's absolute
path. It never reads or sends the file's own content — SUMMARY is not a stub, it's the durable
record the caller composed, and it's what a person will actually read in Slack. It never assumes
anything about who is calling it or what the file is — a dream run, a report generator, a one-off
script, anything that has produced a file and a description of what happened can use this
unchanged.

## 1. Arguments

Two required inputs:

- **FILE_PATH** — absolute path to the file. Required. Must exist. A missing, relative, or
  nonexistent path is a hard failure (§4), not a silent no-op.
- **SUMMARY** — the durable content of the message: everything a person should be able to read
  and act on in Slack without reopening the file, because the file may be regenerated (or moved,
  or deleted) before anyone gets back to it. Required. This is caller-composed prose/Markdown, not
  the file's raw contents — see §5 for the cap and §6 for what syntax to write it in.

Invoked as `/send-results <file-path> <summary text...>` — the first whitespace-delimited token of
the arguments is `FILE_PATH`, everything after it (trimmed) is `SUMMARY`. A programmatic caller
(another skill, a script) may instead `export FILE_PATH=...` and `export SUMMARY=...` directly and
skip parsing a single argument string — both forms feed the same script in §8. They must be
`export`ed, not just assigned: the script in §8 runs in a separate `python3` process, which only
sees exported environment variables, not plain shell variables of the calling shell. Multi-line,
multi-paragraph content should be built and `export`ed this way rather than typed on a single
slash-command line.

One optional input, an environment variable (see §7 for the guard it controls):

- **SEND_RESULTS_DEDUP_WINDOW_SECONDS** — how long an identical message is remembered for
  duplicate-skipping. Integer seconds. Default `900` (15 minutes) if unset. `0` disables the guard.

The message cap in §5 is a fixed constant, not configurable — a caller can't accidentally
reintroduce Slack's silent truncation by raising it past a safe margin.

If either required argument is missing, stop and ask for it. Do not guess a summary from the
file's content and do not guess a path from context.

## 2. The path is a pointer; SUMMARY is the record

Never read the target file into the message, never attach it, never paste an excerpt from it "just
this once" — the absolute path in §1 is how a person gets to the file itself. SUMMARY is different:
it is meant to carry real content, enough for the Slack message to stand alone as a record of what
happened even after the file at that path has changed. The caller composes SUMMARY; this skill's
only job on it is to redact secrets, convert formatting, and cap length (§5, §8) — it does not
summarize, excerpt, or read the file on the caller's behalf.

## 3. The channel is fixed, not a parameter

The webhook URL determines the destination channel; that binding happened when the webhook was
created and cannot be changed per call. Do not add a `channel` field to the payload — a modern
Slack incoming webhook ignores it, and Slack's own docs confirm incoming webhooks cannot override
the channel, username, or icon (https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks).

## 4. Validate before doing anything else

`FILE_PATH` must be absolute and must exist on disk. Check this before reading the webhook or
composing any message — a bad path should fail loudly and immediately, not after a network call.
This is handled in the script in §8; do not skip it by hand-rolling a shortcut.

## 5. Limits, verified from Slack's own docs

- **`SUMMARY` is capped at 12,000 characters**, truncated with a clear marker if it runs over. That
  is 3x headroom below Slack's real hard limit (next bullet), generous enough to hold a genuine
  multi-paragraph findings write-up — headings-as-bold-lines, bullets, code spans (§6) — without
  needing to trim, while still bounded so `SUMMARY` can't turn into an unbounded log dump. Raise it
  further only with a reason, and never past the next bullet's real ceiling.
- The full composed message (`SUMMARY` plus the `File: `path`` line) is capped again at **40,000
  characters** as a hard backstop — Slack's own `text` field is not rejected past that limit, it is
  silently *truncated* once it exceeds 40,000 characters
  (https://docs.slack.dev/changelog/2018-truncating-really-long-messages/). This skill truncates
  first, with its own visible marker, so a caller never depends on Slack's silent cut.
- **Payload shape: a bare `{"text": ...}` payload, not Block Kit blocks.** Slack's formatting doc
  states plainly, in its "Disabling formatting" section: *"For the top-level `text` field in
  messages, include a `mrkdwn` property set to `false` [...] when publishing"* to turn mrkdwn
  parsing *off* (https://docs.slack.dev/messaging/formatting-message-text). That sentence is a
  directly-quoted, verified fact; that top-level `text` is mrkdwn-parsed *by default* is this
  skill's own inference from it (the disable-instruction only makes sense if parsing is already on
  by default, with nothing extra to set to enable it) — a documented instruction to turn a thing
  off is strong evidence the thing defaults on, but it is inference, not a sentence anywhere that
  states the default directly, and is called out as such rather than asserted as fact. That single
  field is also verified to hold up to 40,000 characters (previous
  bullet). Block Kit's `section` block text object uses the *identical* mrkdwn parser — Slack's own
  docs describe `mrkdwn` as one formatting method usable both as "the default formatting method
  when publishing a message" and "to format blocks and elements" — so blocks buy no different
  rendering here, only a much tighter per-block ceiling: a section block's `text` is capped at
  **3,000 characters**, well under the 12,000-character `SUMMARY` cap this skill now needs
  (https://docs.slack.dev/reference/block-kit/blocks/section-block), which would force the message
  to be split across multiple section blocks (up to 50 per message) purely to work around the
  block-level cap. That splitting logic is exactly the kind of complexity this skill is told to
  avoid ("keep it simple and predictable — do not build a full Markdown parser"). One `text` field,
  capped once, sent once, stays simple and covers the full 12,000-character range in a single field
  — so this skill keeps the bare `text` payload.
- **Do not link the path with a `file://` URL or assume it renders as clickable.** Slack's
  formatting docs only document linkification for `http(s)://` and `mailto:` schemes and say
  nothing about `file://` or any other custom scheme, so this skill does not assume one is
  clickable. **This was tested and the answer is settled: it does not work.** A one-off manual test
  sent `<file:///absolute/path|link text>` — the same `<url|text>` syntax documented for `http(s)`
  links — to a real webhook. Slack accepted and delivered it (HTTP 200, body `ok`), so the payload
  shape is not rejected, but a human then looked at the delivered message in their own Slack client
  and confirmed the link was **not clickable**. Delivery proved nothing about rendering; the human
  check did. The script in §8 therefore sends the absolute path as plain inline-code text
  (backticks), not a link: unambiguous, exact, and reliably copy-pasteable into a terminal, editor
  "open" dialog, or `open <path>` on macOS. Do not re-litigate this — a `file://` link is a dead
  end, already tested against a real client. If a clickable link is ever genuinely needed, it has
  to be an `http(s)://` URL, which means hosting the file somewhere, not linking local disk.
- The `channel` field in the JSON payload is ignored by modern incoming webhooks (§3) — confirmed
  in the same webhooks doc above, not merely assumed.

## 6. What syntax to write `SUMMARY` in

**Slack's `mrkdwn` is not standard Markdown.** Slack's own docs say so directly: *"mrkdwn is
Slack's custom text formatting syntax. It is inspired by markdown, but uses different rules."*
(https://docs.slack.dev/messaging/formatting-message-text). Writing standard Markdown and expecting
Slack to render it produces literal `**`, `#`, and `[text](url)` punctuation in the message instead
of formatting — the constraint below exists because of that mismatch, not because of any one
caller's habits. Write `SUMMARY` in mrkdwn directly where you can; the table below is what actually
works, each line verified against Slack's formatting docs (same URL as above unless noted):

| Write this in `SUMMARY` | Renders as | Verified |
|---|---|---|
| `*bold*` | **bold** | *"`*bold*` will produce **bold** text"* |
| `_italic_` | _italic_ | *"`_italic_` will produce *italicized* text"* |
| `~strike~` | ~~strike~~ | *"`~strike~` will produce ~~strikethrough~~ text"* |
| `` `inline code` `` | `inline code` | *"surround it with backtick (\`) characters"*; text inside is not further formatted |
| triple backtick block | multi-line code block | same Code blocks section, 3-backtick form |
| a literal newline (`\n`) | a line break | *"Insert a newline by including the string `\n` in your text"* |
| `<https://example.com\|link text>` | a clickable link | *"Adjust the text that appears as the link from the URL to something else: `<https://docs.slack.dev/\|This message is a link>`"* |
| `- item` per line | looks like a list | *"There's no specific list syntax [...] but you can mimic list formatting with regular text and line breaks"* — it's plain text that happens to look like a list, not a parsed construct |

Two things mrkdwn has **no syntax for at all** — confirmed by their total absence from Slack's own
formatting reference, which otherwise documents every construct above in detail:

- **Headings** (`#`, `##`, ...) — no heading syntax exists. Do not expect hierarchy or size changes.
- **Tables** — no table syntax exists. Write a flat list instead.

Because a caller will still naturally reach for standard Markdown, the script in §8 runs a small,
*fixed* conversion on `SUMMARY` before sending — not a Markdown parser, just these substitutions,
in this order, with existing code spans/blocks protected from all of them:

1. `[text](http(s)://url)` → `<http(s)://url|text>` (Slack's own link syntax; only `http(s)://`
   URLs are converted — `file://` and anything else are left as-is, see §5).
2. A `#`/`##`/.../`######` heading line → that line's text, bolded (`*text*`) — the closest mrkdwn
   equivalent to a heading, since none exists.
3. `**bold**` → `*bold*` (mrkdwn's own bold is a single asterisk).
4. `~~strike~~` → `~strike~` (mrkdwn's own strikethrough is a single tilde).

This is deliberately narrow: it does not touch a standalone single-asterisk `*text*` (already valid
mrkdwn — it renders bold rather than the italic a Markdown author might have intended, which is a
minor semantic drift, not literal junk), and it does not handle deeply nested combinations (e.g. a
bolded heading) perfectly. It also does **not** convert standard Markdown's `__bold__`
(double-underscore) form — deliberately, since that syntax is indistinguishable from a Python
dunder identifier (`__init__`, `__main__`, `__pycache__`, ...), and a findings write-up that
mentions code is exactly the kind of `SUMMARY` this skill expects; converting it would silently
mangle those names. Write `*bold*` directly, or wrap a literal `__dunder__` in backticks so it's
protected as code (it renders unformatted either way — see the code-span row above). Prefer
writing mrkdwn directly per the table above when precision matters; treat the conversion as a
safety net for the common cases, not a guarantee for everything.

## 7. Send-once guard — duplicate messages are skipped, not resent

A scheduled, unattended caller (a cron-style Routine, a retried call after a timeout) can fire the
same logical send more than once. Without a guard, that means the same message lands in the channel
twice. This skill remembers what it has sent and skips an exact repeat within a recent window —
loudly, not silently.

- **What counts as a duplicate**: the exact final message text that would be POSTed — after
  redaction, mrkdwn conversion, and capping (§8) — hashed with SHA-256. Two calls only collide if
  they would produce byte-identical Slack messages (same `SUMMARY` content *and* same `FILE_PATH`,
  since the path is part of the composed text).
- **State file**: `~/.claude/.send-results-sent.json`, created mode `600`, plus a small sidecar
  lock file `~/.claude/.send-results-sent.json.lock` (also mode `600`) used only to serialize
  concurrent invocations — it holds no message data, just an advisory OS lock. Both live next to
  the webhook file (`~/.claude/.dream-slack-webhook`), the same private, single-user trust boundary
  this skill already operates in, and follow the same dot-prefixed naming convention. Mode `600`
  because the state file records hashes and timestamps of what was sent — not the plaintext, but
  enough to reconstruct when and how often this skill has posted — and no other local user has a
  reason to read or write either file.
- **Default window: 900 seconds (15 minutes)**. This is sized around the failure mode the guard
  exists for — a Routine firing twice back-to-back, or a caller retrying after a client-side
  timeout — which happens within seconds to a couple of minutes, not longer. Fifteen minutes gives
  that generous headroom while staying far shorter than any realistic *legitimate* repeat: even an
  hourly schedule is 4x longer than the window, and "the same summary sent again tomorrow" is
  ~96x longer. **Tradeoff**: a caller that deliberately wants to resend byte-identical content
  sooner than 15 minutes apart will be skipped too — that's the guard working as intended
  (idempotency), and it's escapable per-call via `SEND_RESULTS_DEDUP_WINDOW_SECONDS` (§1): set it
  lower for a tighter guard, or `0` to disable it outright for that call.
- **Bounded, self-pruning storage**: every check and every record prunes entries older than the
  *active* window before doing anything else — an entry older than the window can never match again,
  so there's no reason to keep it. On top of that, a hard cap of 500 retained entries is enforced
  regardless of window size (oldest dropped first), so even a caller who sets a very large window
  can't make the file grow without bound.
- **On a detected duplicate**, the script prints a clearly labeled skip line to stdout and exits
  `0` (not a failure) *without* making the Slack HTTP call at all — see §8's exact wording. This is
  never a silent no-op: something is always printed explaining why nothing was sent.
- A message is recorded as sent **only after Slack confirms delivery** (HTTP 200, body `ok`) — a
  failed send is never recorded, so a legitimate retry after a real failure is not blocked by the
  guard.

## 8. Redact, convert, cap, dedup, then send — run this exact script

Set `FILE_PATH` and `SUMMARY` from §1 (and optionally `SEND_RESULTS_DEDUP_WINDOW_SECONDS`), then
run this. The redaction logic is ported from `skills/session-analysis/SKILL.md` §2.2's `redact()`
(last synced at commit 719e7a8) — same patterns, same approach, kept in sync rather than
reimplemented weaker. It runs on every piece of dynamic text before that text is composed into the
outgoing message, not as a comment reminding a human to check later.

```bash
python3 - <<'PY'
import hashlib, json, os, re, sys, time, urllib.request, urllib.error

MAX_SUMMARY_CHARS = 12000  # durable-record cap, well under Slack's hard limit — see SKILL.md §5
MAX_TEXT_CHARS = 40000     # Slack's hard truncation limit on the "text" field — verified, see SKILL.md §5
TRUNCATION_MARKER = " …[truncated]"

STATE_PATH = os.path.expanduser("~/.claude/.send-results-sent.json")
DEFAULT_DEDUP_WINDOW_SECONDS = 900  # 15 minutes — see SKILL.md §7 for why
MAX_STATE_ENTRIES = 500             # hard bound regardless of configured window — see SKILL.md §7

# --- redaction, ported from skills/session-analysis/SKILL.md §2.2 redact() — keep in sync ---

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
    """Mask secrets in outgoing text. Every dynamic string passes through this before it is
    composed into the message sent to Slack — see SKILL.md §8."""
    if not s:
        return s
    for label, pattern in _STRUCTURED_SECRETS:
        s = pattern.sub(f"[REDACTED:{label}]", s)
    s = _CONN_STRING_RE.sub(lambda m: f"{m.group(1)}://[REDACTED:credentials]@", s)
    s = _BEARER_RE.sub("Bearer [REDACTED:bearer-token]", s)
    s = _redact_assignments(s)
    return s

# --- end ported redaction block ---

# --- standard-Markdown -> Slack mrkdwn, fixed substitutions only — see SKILL.md §6 ---

_CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
_MD_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)")
_MD_HEADING_RE = re.compile(r"^#{1,6}[ \t]+(.+)$", re.MULTILINE)
_MD_BOLD_STAR_RE = re.compile(r"\*\*(.+?)\*\*")
_MD_STRIKE_RE = re.compile(r"~~(.+?)~~")
# NOTE: standard Markdown's __bold__ (double-underscore) is deliberately NOT converted — it is
# indistinguishable from Python dunder identifiers (__init__, __main__, __pycache__, ...), and a
# findings write-up that mentions code is exactly the kind of SUMMARY this skill expects. Write
# *bold* directly, or wrap __dunder__ names in backticks, per SKILL.md §6.

def to_mrkdwn(s):
    """Defensively convert the handful of standard-Markdown constructs a caller will naturally
    reach for into Slack mrkdwn (SKILL.md §6) — NOT a full Markdown parser. Existing code
    spans/blocks are protected from these substitutions so code samples are never rewritten;
    mrkdwn's own *bold*/_italic_/~strike~/`code`/<url|text> syntax is already correct and is left
    untouched."""
    if not s:
        return s
    placeholders = []

    def _stash(m):
        placeholders.append(m.group(0))
        return f"\x00{len(placeholders) - 1}\x00"

    s = _CODE_BLOCK_RE.sub(_stash, s)
    s = _CODE_SPAN_RE.sub(_stash, s)

    s = _MD_LINK_RE.sub(lambda m: f"<{m.group(2)}|{m.group(1)}>", s)
    s = _MD_HEADING_RE.sub(lambda m: f"*{m.group(1).strip()}*", s)
    s = _MD_BOLD_STAR_RE.sub(lambda m: f"*{m.group(1)}*", s)
    s = _MD_STRIKE_RE.sub(lambda m: f"~{m.group(1)}~", s)

    for i, original in enumerate(placeholders):
        s = s.replace(f"\x00{i}\x00", original)
    return s

# --- end markdown-conversion block ---

def cap(s, limit):
    if len(s) <= limit:
        return s
    return s[: max(0, limit - len(TRUNCATION_MARKER))] + TRUNCATION_MARKER

def fail(msg):
    print(f"send-results: FAILED — {msg}", file=sys.stderr)
    sys.exit(1)

# --- send-once guard state — see SKILL.md §7 ---

def _flock_handle():
    """Best-effort advisory lock so two concurrent invocations don't corrupt the state file.
    Falls back to unlocked (rare platforms without fcntl) rather than failing the send. The lock
    file holds no message data — it exists only to be flock()'d — but is still created mode 600
    like the state file it guards (SKILL.md §7)."""
    try:
        import fcntl
    except ImportError:
        return None
    lock_path = STATE_PATH + ".lock"
    try:
        fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        os.chmod(lock_path, 0o600)  # enforce 600 even if the file already existed with a wider mode
        fh = os.fdopen(fd, "r+")
        fcntl.flock(fh, fcntl.LOCK_EX)
        return fh
    except OSError:
        return None

def _flock_release(fh):
    if fh is None:
        return
    try:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_UN)
    except OSError:
        pass
    fh.close()

def _load_state():
    try:
        with open(STATE_PATH) as fh:
            data = json.load(fh)
        entries = data.get("sent")
        if isinstance(entries, list):
            return [e for e in entries if isinstance(e, dict) and "hash" in e and "ts" in e]
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
        pass
    return []

def _save_state(entries):
    tmp_path = f"{STATE_PATH}.tmp{os.getpid()}"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        json.dump({"sent": entries}, fh)
    os.replace(tmp_path, STATE_PATH)
    os.chmod(STATE_PATH, 0o600)

def _prune(entries, now, window_seconds):
    return [e for e in entries if now - e["ts"] <= window_seconds][-MAX_STATE_ENTRIES:]

def dedup_check(message, window_seconds):
    """Returns (is_duplicate, age_seconds). A window <= 0 disables the guard entirely."""
    if window_seconds <= 0:
        return False, None
    now = time.time()
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
    lock = _flock_handle()
    try:
        entries = _prune(_load_state(), now, window_seconds)
        _save_state(entries)  # persist the prune even on a plain check, so the file stays bounded
        for e in entries:
            if e["hash"] == digest:
                return True, now - e["ts"]
        return False, None
    finally:
        _flock_release(lock)

def dedup_record(message, window_seconds):
    if window_seconds <= 0:
        return
    now = time.time()
    digest = hashlib.sha256(message.encode("utf-8")).hexdigest()
    lock = _flock_handle()
    try:
        entries = _prune(_load_state(), now, window_seconds)
        entries.append({"hash": digest, "ts": now})
        _save_state(entries[-MAX_STATE_ENTRIES:])
    finally:
        _flock_release(lock)

# --- end send-once guard state ---

file_path = os.environ.get("FILE_PATH", "").strip()
summary = os.environ.get("SUMMARY", "")

if not file_path:
    fail("FILE_PATH is required and was empty.")
if not os.path.isabs(file_path):
    fail(f"FILE_PATH must be an absolute path, got: {file_path!r}")
if not os.path.exists(file_path):
    fail(f"file does not exist: {file_path}")
if not summary.strip():
    fail("SUMMARY is required and was empty.")

window_raw = os.environ.get("SEND_RESULTS_DEDUP_WINDOW_SECONDS", "").strip()
if window_raw:
    try:
        dedup_window_seconds = int(window_raw)
    except ValueError:
        fail(f"SEND_RESULTS_DEDUP_WINDOW_SECONDS must be an integer number of seconds, got: {window_raw!r}")
else:
    dedup_window_seconds = DEFAULT_DEDUP_WINDOW_SECONDS

webhook_path = os.path.expanduser("~/.claude/.dream-slack-webhook")
if not os.path.exists(webhook_path):
    fail(f"webhook file not found at {webhook_path}")
with open(webhook_path) as fh:
    webhook_url = fh.read().strip()
if not webhook_url:
    fail(f"webhook file at {webhook_path} is empty")
# Validate the shape, never the value: urllib.request.Request() raises ValueError("unknown url
# type: ...") on a malformed URL, and that exception's message embeds the value itself — outside
# the two except clauses below, which would let a corrupted webhook file's contents leak into a
# traceback. Fail on the file, never on what it contains.
if not webhook_url.startswith("https://hooks.slack.com/services/"):
    fail(f"webhook file at {webhook_path} does not contain a Slack incoming-webhook URL")

# Redact BEFORE anything else — never convert or slice through an unredacted secret.
safe_summary = redact(summary.strip())
safe_summary = to_mrkdwn(safe_summary)
safe_summary = cap(safe_summary, MAX_SUMMARY_CHARS)
safe_path = redact(file_path)  # defensive: a path shouldn't carry a secret, but nothing here is trusted

message = f"{safe_summary}\n\nFile: `{safe_path}`"
message = cap(message, MAX_TEXT_CHARS)

is_dup, age = dedup_check(message, dedup_window_seconds)
if is_dup:
    print(
        f"send-results: SKIPPED — an identical message was already sent {age:.0f}s ago, "
        f"within the {dedup_window_seconds}s dedup window ({STATE_PATH}). Not sending again. "
        f"Set SEND_RESULTS_DEDUP_WINDOW_SECONDS to change the window, or 0 to disable the guard."
    )
    sys.exit(0)

payload = json.dumps({"text": message}).encode("utf-8")
req = urllib.request.Request(
    webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
)
# webhook_url is used only as the request target below — never printed, logged, or echoed.

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        status = resp.status
        body = resp.read().decode("utf-8", errors="replace")
except urllib.error.HTTPError as e:
    status = e.code
    body = e.read().decode("utf-8", errors="replace")
except urllib.error.URLError as e:
    fail(f"network error posting to Slack: {e.reason}")

ok = status == 200 and body.strip() == "ok"
print(f"send-results: HTTP {status}, response body: {body.strip()!r}")
if not ok:
    fail(f"Slack did not confirm delivery (HTTP {status}, body {body.strip()!r}).")
dedup_record(message, dedup_window_seconds)
print("send-results: OK — message delivered.")
PY
```

## 9. Report delivery honestly

Slack's own contract (verified, not assumed): a successful incoming-webhook POST returns HTTP 200
with the literal plain-text body `ok`; a failure returns a non-200 status with a plain-text error
such as `invalid_payload`, `channel_not_found`, `invalid_token`, `no_text`, `channel_is_archived`,
or `team_disabled`
(https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks). The script in §8
checks both the status code and the exact response body — not just "did curl exit zero" — and exits
non-zero with the real status and body on anything else. Relay that status and body back verbatim;
never report success because the script merely ran without a Python exception. Report a duplicate
skip (§7) just as plainly — say clearly that the send was skipped as a duplicate and why, never
report it as a successful delivery and never let it pass with no output at all.
