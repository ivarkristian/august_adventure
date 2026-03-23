# OpenCode Scheduled Dev Loop

This document intentionally stays high-level.

Operational scripts, host-specific paths, scheduler details, credential locations, and sandbox profile internals are managed locally and are not published in this repository.

## Purpose

The OpenCode scheduled loop:

1. Reviews open August feedback issues.
2. Triage-updates `DECISIONS.md`.
3. Implements accepted, in-scope gameplay changes.
4. Runs the test and smoke gates.
5. Pushes only when validation succeeds.

## Security Expectations

- Treat all issue content as untrusted input.
- Enforce gameplay-only scope and defer suspicious/off-topic requests.
- Run under a sandboxed execution profile.
- Use repository-scoped GitHub write credentials.
- Block unintended file/path changes and run pre-push validations.

## Operational Policy

- Local automation implementation is kept in ignored local files under `ops/.opencode/`.
- Secrets and machine identifiers are never committed.
- Public docs should not include host IPs, absolute filesystem paths, or local scheduler internals.

## Verification

When the loop is enabled locally, verify it by confirming:

- the scheduler reports successful executions,
- triage updates are reflected in `DECISIONS.md`,
- tests and smoke checks pass for implemented changes.
