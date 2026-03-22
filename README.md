# August Adventure

A text-based adventure game inspired by classic exploration games.

This repository is intentionally designed for a multi-agent workflow:
- OpenCode acts as the primary developer.
- August (PicoClaw on `192.168.0.96`) acts as tester and creative consultant.
- GitHub issues are the shared planning and feedback channel.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
august-adventure --seed 7
```

## Commands

- `look` / `l`
- `go <direction>` (or `north`, `south`, `east`, `west`)
- `take <item>` / `drop <item>`
- `use <item>`
- `inventory` / `i`
- `save [path]`
- `load [path]`
- `help`
- `quit`

## Test and Playthrough

Run tests:

```bash
pytest
```

Run deterministic smoke playthrough:

```bash
python scripts/playthrough_smoke.py
```

## Planned Collaboration Loop

1. OpenCode ships updates via GitHub PRs.
2. August pulls latest `main`, runs tests + playthrough.
3. August files bug/feature issues and posts Discord summary.
4. OpenCode triages all August feedback before the next implementation cycle.
