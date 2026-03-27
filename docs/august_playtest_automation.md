# August Playtest Automation

This runbook describes the August automation workflow for monitoring and testing this repository.

## What The Runner Does

`ops/august/runner.py` performs this loop:

1. Pull latest `origin/main` from the configured repository.
2. Skip if commit SHA was already tested.
3. Create/update local venv and install project.
4. Run:
   - `pytest`
   - `python scripts/playthrough_smoke.py`
5. Run unscripted role-based exploratory playthroughs where each role decides commands turn by turn.
6. Ask August for a structured assessment using role-split consultant passes:
    - `docs/playtest_rubric.md`
    - `ops/august/roles/*.md` (fallback: `ops/august/consultant_roles.md`)
    - roles: QA, Narrative, Puzzle, Agency, Publisher
    - each role receives game output context (raw excerpt or compressed summary), game rules/actions, short game description, and role guidance
    - payloads are capped by adaptive context budgets and retried with compressed packs on token-limit failures
7. Produce:
    - up to 3 bug issues,
    - up to 3 feature issues per role,
    - 1 qualitative overall review issue,
    - only when at least `AUGUST_MIN_SUBSTANTIVE_ROLES` role outputs are substantive.
8. DM a technical + qualitative summary to the owner via Discord.
9. Write and maintain historical reference docs under `history_docs/`:
   - `current/game_intro.txt`
   - `current/current_rules.txt`
   - `current/source_map.txt` (from `game/world.py`)
   - `current/playthrough_map.txt` (from exploratory transcripts)
   - `current/story_arc_notes.txt`
   - `current/role_notes_qa.txt`
   - `current/role_notes_narrative.txt`
    - `current/role_notes_puzzle.txt`
    - `current/role_notes_agency.txt`
    - `current/role_notes_publisher.txt`
    - `current/latest_playtest_brief.txt`
   - snapshots in `history_docs/snapshots/<timestamp>_<commit>/`
10. Pin the latest playtest brief in Discord.

The runner requires a game descriptor at:

- `ops/august/game_profile.json`

This profile defines game description, allowed actions, and gameplay terminology.

## Required Credentials

Preferred auth is a GitHub App.

Store app credentials in a host-local environment file that is not committed to git.

Required app permission: **Issues: Read and write** on this repository.

Set:

- `AUGUST_GH_APP_ID`
- `AUGUST_GH_INSTALLATION_ID`
- `AUGUST_GH_APP_PRIVATE_KEY_PATH`

Store the app private key in a host-local path with mode `600`.

Fallback auth (`AUGUST_GITHUB_TOKEN`) is supported but not recommended.

## Install On August Host

On the August host, from a local checkout of this repository:

```bash
bash ops/august/install_on_august.sh
```

This installer configures PicoClaw-native automation:

- deploy role workspaces to `~/.picoclaw/workspace/august-playtest/workspaces/`
- deploy orchestrator prompt to `~/.picoclaw/workspace/AGENT.md`
- enable PicoClaw cron in `~/.picoclaw/config.json`
- disable legacy `august-playtest.timer` systemd schedule
- install an hourly PicoClaw cron job for playtesting

Then edit your host-local environment file:

```bash
nano <path-to-local-august-playtest-env>
```

Set app credentials (recommended) or fallback PAT.

Ensure these are set for the target game repository:

- `AUGUST_GITHUB_REPO`
- `AUGUST_REPO_URL`
- `AUGUST_REPO_DIR`

If using app auth, verify key permissions:

```bash
chmod 600 <path-to-github-app-key>
chmod 600 <path-to-local-august-playtest-env>
```

Optional Discord pin target:

- `AUGUST_DISCORD_PIN_CHANNEL_ID=<channel_id>`

Playtest report destination (recommended for channel-only reporting):

- `AUGUST_DISCORD_REPORT_CHANNEL_ID=<channel_id>`
  or
- `AUGUST_DISCORD_REPORT_CHANNEL_NAME=august-adventure`

Optional consultant reliability controls:

- `AUGUST_PICOCLAW_MODEL=<model>` (pin a specific model instead of default auto)
- `AUGUST_PICOCLAW_ESCALATION_MODEL=<model>` (optional higher-quality fallback)
- `AUGUST_PICOCLAW_ESCALATE_AFTER_TIER=2` (start using escalation model from tier index)
- `AUGUST_PICOCLAW_SESSION_PREFIX=cli:august-playtest`
- `AUGUST_ROLE_MAX_ACTIONS=32` (hard cap on commands per role run)
- `AUGUST_ROLE_MAX_LOCATION_CHANGES=16` (hard cap on room transitions per role run; `0` disables)
- `AUGUST_CONTEXT_CHAR_BUDGET=14000`
- `AUGUST_MAX_FEATURES_PER_ROLE=3` (fallback alias: `AUGUST_MAX_FEATURES`)
- `AUGUST_RESET_PICOCLAW_MAIN_SESSION=1`
- `AUGUST_MIN_SUBSTANTIVE_ROLES=2`
- `AUGUST_DEBUG_KEEP_RUNS=50`
- `AUGUST_SYNC_MODE=hard-reset` (`fast-forward` and `none` are supported for controlled environments)

If not set, runner pins the latest brief in the owner DM channel.

## Operations

Run once manually (outside schedule):

```bash
/usr/bin/bash ~/.picoclaw/workspace/august_adventure/ops/august/run_from_picoclaw.sh
```

Check PicoClaw schedule:

```bash
picoclaw cron list
```

Force test even without new commit:

```bash
AUGUST_FORCE=1 /usr/bin/bash ~/.picoclaw/workspace/august_adventure/ops/august/run_from_picoclaw.sh
```

Trigger ad-hoc run from Discord by messaging August, for example:

- `run august playtest now`

## Notes

- Overall score is the arithmetic average of all rubric dimensions.
- If GitHub auth is missing, runner still executes tests and sends DM summary in dry-run mode.
- `AUGUST_MAX_BUGS` controls merged bug issue cap; `AUGUST_MAX_FEATURES_PER_ROLE` controls per-role feature issue cap.
- Historical docs are always refreshed for each tested commit and snapshotted for later reference.
- Historical docs now include full per-role transcripts: `transcript_qa.txt`, `transcript_narrative.txt`, `transcript_puzzle.txt`, `transcript_agency.txt`, and `transcript_publisher.txt`.
- Unscripted role prompts source shared game context from `game/game_description.md` and `game/game_rules.md`.
- If report channel env is set, summaries are posted to that channel instead of DM.
- Long Discord summaries are split across multiple sequential messages instead of hard truncating the tail.
- Consultant output includes additive narrative/puzzle suggestions and overarching story-arc assessment.
- Bug suggestions now include `expected_result` and `actual_result` fields, and those fields are included in GitHub bug issue bodies.
- Publisher-role suggestions are only opened as feature issues when they are concrete gameplay/content changes.
- Pipeline/framework failures are not opened as GitHub issues; diagnostics are written locally under `~/.picoclaw/workspace/august-playtest/debug/`.
- On pipeline failure, August posts a short Discord status message with the local debug bundle path.
