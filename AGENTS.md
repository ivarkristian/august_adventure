# AGENTS
Operational guidance for coding agents working in `august-adventure`.

## Project Snapshot
- Language: Python (`>=3.10`, CI runs `3.11`).
- Packaging: setuptools via `pyproject.toml`.
- Test framework: `pytest`.
- Entrypoint: `august-adventure` -> `game.cli:main`.
- Main code lives in `game/`; tests in `tests/`; smoke scenario in `scripts/playthrough_smoke.py`.

## Roles And Collaboration
- OpenCode is the primary developer and release manager.
- August (PicoClaw on `192.168.0.96`) is tester and creative consultant.
- Human owner approves goals and direction.
- GitHub issues and PRs are the planning and review channel.

## External Rule Files (Cursor/Copilot)
- `.cursor/rules/` not present.
- `.cursorrules` not present.
- `.github/copilot-instructions.md` not present.
- This file is the canonical in-repo agent instruction source.

## Mandatory Development Loop
Before implementation:
1. Review all open issues labeled `august-feedback` and `triage-needed`.
2. Classify each issue as accepted, deferred, or won't-fix with rationale.
3. Record triage decisions in `DECISIONS.md`.

After implementation:
1. Run `pytest`.
2. Run `python scripts/playthrough_smoke.py`.
3. Update docs/tests when behavior or commands change.

## Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Build, Lint, And Test Commands
The repository has tests configured, but no dedicated linter/formatter toolchain in `pyproject.toml`.

### Build / Install
```bash
# editable install
pip install -e ".[dev]"

# run CLI
august-adventure --seed 7
```

Optional release build check:
```bash
python -m pip install build
python -m build
```

### Lint / Static Checks
```bash
# lightweight syntax/import sanity check
python -m compileall game tests scripts

# quality gate
pytest
```

### Test Commands (pytest)
```bash
# full suite
pytest

# run one test file
pytest tests/test_engine.py

# run one test function (node id)
pytest tests/test_engine.py::test_save_load_roundtrip

# run by pattern
pytest -k inventory
```

Required smoke run after code changes:
```bash
python scripts/playthrough_smoke.py
```

## Code Style Guidelines
Follow current conventions in `game/` and `tests/`.

### Imports
- Use `from __future__ import annotations` first when present.
- Import order: standard library, then first-party (`game.*`).
- Prefer absolute imports (for example, `from game.engine import GameEngine`).
- Avoid wildcard imports and unused imports.

### Formatting
- Use 4-space indentation and PEP 8 style.
- Keep lines reasonably short and functions focused.
- Use blank lines between top-level defs.
- Only add comments when logic is not obvious from code.

### Types And Data Modeling
- Add type hints for parameters and return values.
- Prefer built-in generics (`list[str]`, `dict[str, bool]`, `tuple[str, bool]`).
- Use dataclasses for structured state/value objects (`GameState`, `Room`, `Command`).
- Prefer explicit types over `Any`.
- Keep parser/helpers deterministic and low side effect.

### Naming Conventions
- `snake_case` for functions, methods, variables, and modules.
- `PascalCase` for classes.
- `UPPER_SNAKE_CASE` for module constants.
- Use descriptive domain names (`location`, `inventory`, `seed`).
- Name tests by behavior (for example, `test_locked_exit_requires_key`).

### Error Handling And Validation
- For player input errors, return user-facing messages instead of raising exceptions.
- Validate file existence before loading saves.
- Keep save/load I/O explicit and UTF-8 encoded.
- Do not silently swallow unexpected exceptions.
- Add regression tests when introducing new failure paths.

### Determinism Rules
- Keep gameplay deterministic under test.
- Route randomness through seeded RNG instances (`random.Random(seed)`), not global random state.
- Preserve and honor CLI `--seed` behavior.

### Save/Load Compatibility
- Preserve save-file shape unless a migration is explicitly planned.
- Current save keys include `seed`, `state`, and `rooms`.
- Maintain backward compatibility for existing fields when possible.
- If format changes are required, document migration in PR/docs.

## Testing Expectations For Changes
- Bug fixes should include a regression test in `tests/`.
- New behavior should add focused tests near related modules.
- Use `tmp_path` for filesystem I/O tests.
- Assertions should verify user-visible behavior and state transitions.
- Run both required gates: `pytest` and `python scripts/playthrough_smoke.py`.

## PR And Documentation Hygiene
- Keep changes incremental; avoid unrelated rewrites.
- Update `README.md`/docs when commands or behavior change.
- Reflect triage outcomes in `DECISIONS.md`.
- Follow `.github/pull_request_template.md` checklist:
  - triage done
  - tests run
  - smoke playthrough run

## Quick Agent Checklist
1. Triage `august-feedback` and `triage-needed` issues.
2. Write accepted/deferred/won't-fix decisions to `DECISIONS.md`.
3. Implement minimal, deterministic changes.
4. Add/update tests.
5. Run `pytest`.
6. Run `python scripts/playthrough_smoke.py`.
7. Update docs when behavior or commands changed.
