#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${AUGUST_ENV_FILE:-$HOME/.config/august-playtest.env}"

FORCE_OVERRIDE="${AUGUST_FORCE-__unset__}"
SYNC_MODE_OVERRIDE="${AUGUST_SYNC_MODE-__unset__}"
REPO_DIR_OVERRIDE="${AUGUST_REPO_DIR-__unset__}"
REPO_URL_OVERRIDE="${AUGUST_REPO_URL-__unset__}"

if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi

if [ "$FORCE_OVERRIDE" != "__unset__" ]; then
  AUGUST_FORCE="$FORCE_OVERRIDE"
fi
if [ "$SYNC_MODE_OVERRIDE" != "__unset__" ]; then
  AUGUST_SYNC_MODE="$SYNC_MODE_OVERRIDE"
fi
if [ "$REPO_DIR_OVERRIDE" != "__unset__" ]; then
  AUGUST_REPO_DIR="$REPO_DIR_OVERRIDE"
fi
if [ "$REPO_URL_OVERRIDE" != "__unset__" ]; then
  AUGUST_REPO_URL="$REPO_URL_OVERRIDE"
fi

: "${AUGUST_REPO_DIR:=$HOME/.picoclaw/workspace/august_adventure}"

if [ -z "${AUGUST_REPO_URL:-}" ] && [ -n "${AUGUST_GITHUB_REPO:-}" ]; then
  AUGUST_REPO_URL="https://github.com/${AUGUST_GITHUB_REPO}.git"
fi

: "${AUGUST_REPO_URL:=}"

export AUGUST_REPO_DIR
export AUGUST_REPO_URL

exec /usr/bin/python3 "$AUGUST_REPO_DIR/ops/august/runner.py"
