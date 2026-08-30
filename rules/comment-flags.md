# Code comment flags

Use only the commonly-used comment flags: **`TODO`** and **`BUGBUG`**. Never invent flag words
such as `KNOWN GAP`, `KNOWN FOLLOW-UP`, `KNOWN ISSUE`, `KNOWN LIMITATION`, or `KNOWN CAVEAT`.

**Why:** invented flags are ungreppable and invisible to linters, CI comment sweeps, and IDE
TODO panes. Teams scan for the conventional set, so a bespoke label means a real defect never
surfaces.

## How to apply

- `BUGBUG` — a real defect that exists in the code right now.
- `TODO` — deferred or interim work that isn't yet broken.
- If the repo already uses a scoped form (e.g. `TODO(vendor-detection):`), follow it when the note
  has a natural scope tag.
- Keep the explanatory prose that follows the flag — only the flag word changes.
- Applies to prose too: when docs cross-reference a comment by its flag name, keep the two in sync.
- Don't retro-fix pre-existing invented flags as a drive-by; that's a separate cleanup the user
  has to ask for.
