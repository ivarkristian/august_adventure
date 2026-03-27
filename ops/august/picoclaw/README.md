# PicoClaw Playtest Layout

This directory contains PicoClaw-native definitions used on the August host.

## Workspaces

- `workspaces/orchestrator/AGENT.md`: main orchestration behavior for run-now and scheduling commands.
- `workspaces/qa/AGENT.md`
- `workspaces/narrative/AGENT.md`
- `workspaces/puzzle/AGENT.md`
- `workspaces/agency/AGENT.md`
- `workspaces/publisher/AGENT.md`

These role workspaces are deployed to the host under:

- `~/.picoclaw/workspace/august-playtest/workspaces/<role>/AGENT.md`

The orchestrator definition is deployed as:

- `~/.picoclaw/workspace/AGENT.md`

so the persistent Discord-connected PicoClaw can trigger and schedule playtests.
