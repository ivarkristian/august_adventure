# August Adventure

A text-based adventure game inspired by classic exploration games.

This repository is intentionally designed for a multi-agent workflow:
- OpenCode acts as the primary developer.
- August (PicoClaw) acts as tester and creative consultant.
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
- `examine <target>`
- `listen`
- `inventory` / `i`
- `save [path]`
- `load [path]`
- `help`
- `quit`

Canonical automation prompt context sources:

- game description: `game/game_description.md`
- rules/actions: `game/game_rules.md`

## Current Puzzle Loop

- Core progression is built around discovery and gated exploration across connected rooms.
- Key items such as the `key`, `lamp`, `coin`, and `tablet` matter to progression, but the game expects players to infer their best uses from context.
- Environmental details, inscriptions, and room interactions are meant to guide experimentation toward narrative payoff.

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

## Automation Runbook

- GitHub and branch policy setup: `docs/github_setup.md`
- August autonomous tester setup: `docs/august_playtest_automation.md`
- Qualitative scoring anchors: `docs/playtest_rubric.md`
- OpenCode hourly dev loop setup: `docs/opencode_dev_loop.md`

August automation keeps historical text artifacts in `history_docs/` on the August host,
including source-derived maps, playthrough-derived maps, role notes, and story-arc notes for each tested commit.
