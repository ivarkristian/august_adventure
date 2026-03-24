#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${AUGUST_REPO_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
REPO_URL="${AUGUST_REPO_URL:-}"
ENV_FILE="$HOME/.config/august-playtest.env"
UNIT_DIR="$HOME/.config/systemd/user"

mkdir -p "$UNIT_DIR" "$HOME/.config"

if [ ! -d "$REPO_DIR/.git" ]; then
  if [ -z "$REPO_URL" ]; then
    echo "Set AUGUST_REPO_URL before first install when repo checkout is missing." >&2
    exit 1
  fi
  git clone "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout main
  git -C "$REPO_DIR" reset --hard origin/main
fi

cp "$REPO_DIR/ops/august/august-playtest.service" "$UNIT_DIR/august-playtest.service"
cp "$REPO_DIR/ops/august/august-playtest.timer" "$UNIT_DIR/august-playtest.timer"

if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_DIR/ops/august/august-playtest.env.example" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Created $ENV_FILE. Edit it with your GitHub bot token before enabling timer."
fi

systemctl --user daemon-reload
systemctl --user enable --now august-playtest.timer

echo "Timer enabled. Next run schedule:"
systemctl --user list-timers august-playtest.timer --no-pager
