# OpenCode Scheduled Dev Loop

This loop runs OpenCode hourly on your Mac in `august-adventure`, evaluates August feedback from GitHub, and can push directly to `main` after validation.

The scheduled agent is sandboxed so it can write only inside `august-adventure/`.

## Behavior

`ops/opencode/dev_loop.py` does the following:

1. Verifies repository is clean.
2. Pulls latest `origin/main` (fast-forward only).
3. Queries open GitHub issues labeled `august-feedback` and `triage-needed`.
4. Skips run if no relevant issues.
5. Runs OpenCode with a strict prompt to:
   - evaluate narrative fit and location fit for each issue,
   - update `DECISIONS.md`,
   - implement accepted items,
   - run `pytest` and smoke playthrough,
   - commit and push to `main` only when tests pass.

## GitHub Credential Isolation (Repo-Only)

The loop uses a dedicated deploy key stored inside the repository sandbox:

- `.opencode_sandbox/keys/august_adventure_deploy_key`

Requirements:

1. Add the corresponding public key as a **Deploy Key with write access** on:
   - `ivarkristian/august_adventure`
2. Do not add this key to any other repository.

Helper command to create/show the key:

```bash
bash ops/opencode/ensure_deploy_key.sh
```

Runtime hardening:

- `SSH_AUTH_SOCK` is unset.
- `GIT_SSH_COMMAND` uses `-F /dev/null` and forces `IdentitiesOnly=yes` with only that deploy key.
- `origin` fetch/push URL must exactly match `git@github.com:ivarkristian/august_adventure.git`.
- Additional push remotes are blocked.

## Install Hourly Schedule (macOS launchd)

From repo root:

```bash
bash ops/opencode/install_launchd.sh
```

This installs label:

- `com.ivarkristian.august-adventure.opencode-dev-loop`

And schedules hourly via `StartInterval = 3600`.

## Sandbox Boundary

The launch agent runs through:

- `/usr/bin/sandbox-exec -f ops/opencode/opencode-dev-loop.sb`

Sandbox policy:

- allows read access as needed for runtimes/tools,
- allows network outbound/inbound,
- allows write access only under `/Users/ikw/work/august-adventure`.

OpenCode state/cache/tmp are redirected into:

- `.opencode_sandbox/`

## Manual Run

```bash
bash ops/opencode/run_dev_loop.sh
```

## Logs

- `august-adventure/.opencode_sandbox/logs/opencode-dev-loop.out.log`
- `august-adventure/.opencode_sandbox/logs/opencode-dev-loop.err.log`

## Disable / Remove

```bash
bash ops/opencode/uninstall_launchd.sh
```
