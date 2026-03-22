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
5. Run one exploratory playthrough transcript.
6. Ask August model for up to 2 bug reports and 2 feature suggestions.
7. Create GitHub issues (if `AUGUST_GITHUB_TOKEN` is configured).
8. DM a run summary to the owner via Discord bot token already in PicoClaw config.

## Required Credential

Add a GitHub bot token to:

`~/.config/august-playtest.env`

Required permission scope: repo issues for this repository.

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

Set `AUGUST_GITHUB_TOKEN=...`.

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
