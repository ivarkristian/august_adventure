# August Playtest Automation

This runbook sets up August (`192.168.0.96`) to monitor and test this repository.

## What The Runner Does

`ops/august/runner.py` performs this loop:

1. Pull latest `origin/main` from `ivarkristian/august_adventure`.
2. Skip if commit SHA was already tested.
3. Create/update local venv and install project.
4. Run:
   - `pytest`
   - `python scripts/playthrough_smoke.py`
5. Run three exploratory playthroughs (explorer, puzzle, skeptic).
6. Ask August for a structured assessment using:
   - `docs/playtest_rubric.md`
   - `ops/august/consultant_roles.md`
7. Produce:
   - up to 3 bug issues,
   - up to 3 feature issues,
   - 1 qualitative overall review issue.
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
   - `current/latest_playtest_brief.txt`
   - snapshots in `history_docs/snapshots/<timestamp>_<commit>/`
10. Pin the latest playtest brief in Discord.

## Required Credentials

Preferred auth is a GitHub App.

Add app credentials to:

`~/.config/august-playtest.env`

Required app permission: **Issues: Read and write** on this repository.

Set:

- `AUGUST_GH_APP_ID`
- `AUGUST_GH_INSTALLATION_ID`
- `AUGUST_GH_APP_PRIVATE_KEY_PATH`

Store the app private key file at the configured path with mode `600`.

Fallback auth (`AUGUST_GITHUB_TOKEN`) is supported but not recommended.

## Install On August Host

On `192.168.0.96`:

```bash
cd ~/august_adventure
bash ops/august/install_on_august.sh
```

Then edit env file:

```bash
nano ~/.config/august-playtest.env
```

Set app credentials (recommended) or fallback PAT.

If using app auth, verify key permissions:

```bash
chmod 600 ~/.config/august-github-app.pem
chmod 600 ~/.config/august-playtest.env
```

Optional Discord pin target:

- `AUGUST_DISCORD_PIN_CHANNEL_ID=<channel_id>`

Playtest report destination (recommended for channel-only reporting):

- `AUGUST_DISCORD_REPORT_CHANNEL_ID=<channel_id>`
  or
- `AUGUST_DISCORD_REPORT_CHANNEL_NAME=august-adventure`

If not set, runner pins the latest brief in the owner DM channel.

## Operations

Run once manually:

```bash
systemctl --user start august-playtest.service
journalctl --user -u august-playtest.service -n 120 --no-pager
```

Check schedule:

```bash
systemctl --user list-timers august-playtest.timer --no-pager
```

Force test even without new commit:

```bash
AUGUST_FORCE=1 systemctl --user start august-playtest.service
```

## Notes

- Overall score is the arithmetic average of all rubric dimensions.
- If GitHub auth is missing, runner still executes tests and sends DM summary in dry-run mode.
- `AUGUST_MAX_BUGS` and `AUGUST_MAX_FEATURES` control per-run issue caps.
- Historical docs are always refreshed for each tested commit and snapshotted for later reference.
- If report channel env is set, summaries are posted to that channel instead of DM.
- Consultant output includes additive narrative/puzzle suggestions and overarching story-arc assessment.
