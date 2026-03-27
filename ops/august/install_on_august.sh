#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="${AUGUST_REPO_DIR:-$HOME/.picoclaw/workspace/august_adventure}"
REPO_URL="${AUGUST_REPO_URL:-https://github.com/ivarkristian/august_adventure.git}"
ENV_FILE="$HOME/.config/august-playtest.env"
PICO_WORKSPACE="$HOME/.picoclaw/workspace"
ROLE_SRC_DIR="$REPO_DIR/ops/august/picoclaw/workspaces"
ROLE_DST_DIR="$PICO_WORKSPACE/august-playtest/workspaces"
ORCHESTRATOR_AGENT="$ROLE_SRC_DIR/orchestrator/AGENT.md"

mkdir -p "$HOME/.config" "$PICO_WORKSPACE"

if [ ! -d "$REPO_DIR/.git" ]; then
  git clone "$REPO_URL" "$REPO_DIR"
else
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout main
  git -C "$REPO_DIR" reset --hard origin/main
fi

chmod +x "$REPO_DIR/ops/august/run_from_picoclaw.sh"

if [ ! -f "$ENV_FILE" ]; then
  cp "$REPO_DIR/ops/august/august-playtest.env.example" "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Created $ENV_FILE. Edit credentials/channel IDs before first run."
fi

mkdir -p "$ROLE_DST_DIR"
for role in qa narrative puzzle agency publisher; do
  mkdir -p "$ROLE_DST_DIR/$role"
  cp "$ROLE_SRC_DIR/$role/AGENT.md" "$ROLE_DST_DIR/$role/AGENT.md"
done

if [ -f "$PICO_WORKSPACE/AGENT.md" ] && ! grep -q "august-orchestrator" "$PICO_WORKSPACE/AGENT.md"; then
  cp "$PICO_WORKSPACE/AGENT.md" "$PICO_WORKSPACE/AGENT.backup.pre_august_playtest.md"
fi
cp "$ORCHESTRATOR_AGENT" "$PICO_WORKSPACE/AGENT.md"

python3 - <<'PY'
import json
from pathlib import Path

cfg_path = Path.home() / ".picoclaw" / "config.json"
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

model_list = cfg.get("model_list")
if not isinstance(model_list, list):
    model_list = []
    cfg["model_list"] = model_list

openrouter_api_key = ""
for item in model_list:
    if not isinstance(item, dict):
        continue
    model_name = str(item.get("model_name", "")).strip()
    model_slug = str(item.get("model", "")).strip()
    api_key = str(item.get("api_key", "")).strip()
    if model_name == "openrouter-auto" and api_key:
        openrouter_api_key = api_key
        break
    if model_slug.startswith("openrouter/") and api_key:
        openrouter_api_key = api_key


def upsert_openrouter_model(model_name: str, model_slug: str) -> None:
    target = None
    for entry in model_list:
        if isinstance(entry, dict) and str(entry.get("model_name", "")).strip() == model_name:
            target = entry
            break
    if target is None:
        target = {"model_name": model_name}
        model_list.append(target)

    target["model"] = model_slug
    target["api_base"] = "https://openrouter.ai/api/v1"
    if openrouter_api_key and not str(target.get("api_key", "")).strip():
        target["api_key"] = openrouter_api_key


upsert_openrouter_model("openrouter-gpt-oss-20b", "openrouter/openai/gpt-oss-20b")
upsert_openrouter_model("openrouter-gpt-oss-120b", "openrouter/openai/gpt-oss-120b")

tools = cfg.setdefault("tools", {})
cron = tools.setdefault("cron", {})
cron["enabled"] = True
cron.setdefault("exec_timeout_minutes", 10)
cron.setdefault("allow_command", True)

agents = cfg.setdefault("agents", {})
defaults = agents.setdefault("defaults", {})
defaults["model_name"] = "openrouter-gpt-oss-20b"

gateway = cfg.setdefault("gateway", {})
gateway.setdefault("host", "127.0.0.1")
gateway.setdefault("port", 18790)

cfg_path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
PY

systemctl --user disable --now august-playtest.timer >/dev/null 2>&1 || true
systemctl --user disable --now august-playtest.service >/dev/null 2>&1 || true

systemctl --user daemon-reload
systemctl --user enable picoclaw-gateway.service
systemctl --user stop picoclaw-gateway.service >/dev/null 2>&1 || true

python3 "$REPO_DIR/ops/august/configure_picoclaw_cron.py"

systemctl --user start picoclaw-gateway.service

echo "PicoClaw playtest automation installed."
echo "Verify scheduler and service:"
echo "  picoclaw cron list"
echo "  systemctl --user status picoclaw-gateway.service --no-pager"
