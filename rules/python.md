---
paths: ["**/*.py"]
---

## Python projects: always `uv`

- Every Python project here uses **`uv`** as the package manager, so a `pyproject.toml` is always
  present; read it before guessing at tooling.
- **Run everything through `uv run`.** It auto-loads the project's `.venv`, so there is never a
  reason to activate the venv, or to invoke `.venv/bin/python`, a bare `python3`, or `pip` directly.
  - Python: `uv run python -c "..."`
  - A script: `uv run <script>.py`
- **Task runner is poe-the-poet**, with tasks declared in `pyproject.toml` under `[tool.poe.tasks]`.
  Prefer these over hand-rolled commands for tests, coverage, lint, and type checks:
  `uv run poe <task>` (e.g. `uv run poe cov-all`). Read the section for the real task names in that
  repo rather than assuming a naming scheme.

## Testing philosophy

- Code Coverage Best Practice: 100% coverage is not strictly required; focus on covering functionality, critical paths, and negative test cases (edge cases) rather than just hitting lines of code.
- Unit Testing Philosophy: Do not write tests just for coverage; test behavior (what the function promises), not implementation. Every test should use Arrange/Act/Assert (AAA) pattern.
- Test Cases to Cover: Prioritize and ensure coverage of Negative cases (e.g. invalid inputs, missing data, 404s/500s from downstream) and Edge cases (empty collections, boundary variables).
- Mocking Strategy: Mock at the boundary (e.g., HTTP clients, DB wrappers), not deep inside internal dependencies. For FastAPI, properly mock `httpx.Response` components and use real functions for `Depends()` instead of Mock objects.
