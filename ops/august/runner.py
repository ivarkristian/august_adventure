from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class CmdResult:
    code: int
    out: str
    err: str


def run_cmd(command: list[str], cwd: Path | None = None, timeout: int = 300) -> CmdResult:
    proc = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return CmdResult(proc.returncode, proc.stdout.strip(), proc.stderr.strip())


def ensure_repo(repo_dir: Path, repo_url: str) -> None:
    if (repo_dir / ".git").exists():
        return
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["git", "clone", repo_url, str(repo_dir)], timeout=600)
    if result.code != 0:
        raise RuntimeError(f"git clone failed: {result.err}")


def sync_repo(repo_dir: Path) -> str:
    fetch = run_cmd(["git", "fetch", "origin"], cwd=repo_dir, timeout=300)
    if fetch.code != 0:
        raise RuntimeError(f"git fetch failed: {fetch.err}")

    rev = run_cmd(["git", "rev-parse", "origin/main"], cwd=repo_dir)
    if rev.code != 0:
        raise RuntimeError(f"git rev-parse failed: {rev.err}")
    sha = rev.out.strip()

    checkout = run_cmd(["git", "checkout", "main"], cwd=repo_dir)
    if checkout.code != 0:
        raise RuntimeError(f"git checkout failed: {checkout.err}")

    reset = run_cmd(["git", "reset", "--hard", "origin/main"], cwd=repo_dir)
    if reset.code != 0:
        raise RuntimeError(f"git reset failed: {reset.err}")

    return sha


def ensure_venv(repo_dir: Path) -> Path:
    venv = repo_dir / ".venv"
    python = venv / "bin" / "python"
    pip = venv / "bin" / "pip"

    if venv.exists() and (not python.exists() or not pip.exists()):
        run_cmd(["rm", "-rf", str(venv)], cwd=repo_dir)

    if not python.exists():
        mk = run_cmd(["python3", "-m", "venv", str(venv)], cwd=repo_dir)
        if mk.code != 0:
            raise RuntimeError(f"venv create failed: {mk.err}")

    if not pip.exists():
        ep = run_cmd([str(python), "-m", "ensurepip", "--upgrade"], cwd=repo_dir)
        if ep.code != 0:
            raise RuntimeError(f"ensurepip failed: {ep.err}")

    up = run_cmd([str(pip), "install", "-q", "--upgrade", "pip"], cwd=repo_dir, timeout=600)
    if up.code != 0:
        raise RuntimeError(f"pip upgrade failed: {up.err}")

    inst = run_cmd([str(pip), "install", "-q", "-e", ".[dev]"], cwd=repo_dir, timeout=900)
    if inst.code != 0:
        raise RuntimeError(f"dependency install failed: {inst.err}")
    return python


def run_tests(repo_dir: Path, python_bin: Path) -> dict[str, CmdResult]:
    return {
        "pytest": run_cmd([str(python_bin), "-m", "pytest"], cwd=repo_dir, timeout=900),
        "smoke": run_cmd([str(python_bin), "scripts/playthrough_smoke.py"], cwd=repo_dir, timeout=600),
    }


def run_exploratory(repo_dir: Path, python_bin: Path) -> str:
    script = (
        "from game.playtest import run_playthrough\n"
        "cmds=[\"look\",\"take lamp\",\"north\",\"east\",\"north\",\"use lamp\",\"inventory\",\"quit\"]\n"
        "r=run_playthrough(cmds,seed=11)\n"
        "print('\\n'.join(r.transcript))\n"
    )
    result = run_cmd([str(python_bin), "-c", script], cwd=repo_dir, timeout=300)
    if result.code != 0:
        return f"Exploratory run failed: {result.err}"
    return result.out


def load_picoclaw_discord() -> tuple[str, str]:
    cfg_path = Path.home() / ".picoclaw" / "config.json"
    if not cfg_path.exists():
        return "", ""
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    discord = cfg.get("channels", {}).get("discord", {})
    token = str(discord.get("token", ""))
    allow = discord.get("allow_from", [])
    owner = str(allow[0]) if isinstance(allow, list) and allow else ""
    return token, owner


def api_json(method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url=url, method=method, data=data, headers=headers)
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {}


def parse_consultant_json(text: str) -> dict[str, list[dict[str, Any]]]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"bugs": [], "features": []}
    blob = text[start : end + 1]
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return {"bugs": [], "features": []}
    bugs = data.get("bugs", [])
    features = data.get("features", [])
    if not isinstance(bugs, list) or not isinstance(features, list):
        return {"bugs": [], "features": []}
    return {"bugs": bugs[:2], "features": features[:2]}


def ask_august_consultant(commit_sha: str, test_results: dict[str, CmdResult], exploratory_text: str) -> dict[str, list[dict[str, Any]]]:
    prompt = f"""
You are August, a QA tester and creative consultant for a text adventure game.
Return STRICT JSON only with this schema:
{{
  "bugs": [{{"title":"...","summary":"...","repro_steps":["..."],"severity":"low|medium|high"}}],
  "features": [{{"title":"...","player_value":"...","proposal":"..."}}]
}}
Rules:
- Max 2 bugs and 2 features.
- If no bug found, return empty bugs list.
- Keep titles short and specific.

Context:
- Commit: {commit_sha}
- Pytest exit: {test_results['pytest'].code}
- Smoke exit: {test_results['smoke'].code}
- Pytest output:
{test_results['pytest'].out[:2500]}
{test_results['pytest'].err[:1200]}

- Smoke output:
{test_results['smoke'].out[:2500]}
{test_results['smoke'].err[:1200]}

- Exploratory transcript:
{exploratory_text[:3500]}
""".strip()
    result = run_cmd(["picoclaw", "agent", "-m", prompt], timeout=240)
    text = "\n".join(part for part in [result.out, result.err] if part)
    return parse_consultant_json(text)


def list_open_issue_titles(repo: str, token: str) -> set[str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "august-playtest-bot",
    }
    url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=100"
    try:
        data = api_json("GET", url, headers)
    except (HTTPError, URLError):
        return set()
    titles = set()
    if isinstance(data, list):
        for issue in data:
            if not isinstance(issue, dict):
                continue
            title = issue.get("title")
            if isinstance(title, str):
                titles.add(title)
    return titles


def create_issue(repo: str, token: str, title: str, body: str, labels: list[str]) -> None:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "august-playtest-bot",
        "Content-Type": "application/json",
    }
    payload = {"title": title[:120], "body": body[:60000], "labels": labels}
    api_json("POST", f"https://api.github.com/repos/{repo}/issues", headers, payload)


def send_discord_dm(token: str, owner_id: str, content: str) -> None:
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "august-playtest-bot",
    }
    dm = api_json("POST", "https://discord.com/api/v10/users/@me/channels", headers, {"recipient_id": owner_id})
    channel_id = dm.get("id")
    if not isinstance(channel_id, str):
        return
    api_json("POST", f"https://discord.com/api/v10/channels/{channel_id}/messages", headers, {"content": content[:1900]})


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def format_summary(repo: str, sha: str, test_results: dict[str, CmdResult], opened: int, skipped: int, mode: str) -> str:
    return (
        "August playtest report\n"
        f"Repo: {repo}\n"
        f"Commit: {sha[:12]}\n"
        f"Mode: {mode}\n"
        f"Pytest: {'PASS' if test_results['pytest'].code == 0 else 'FAIL'}\n"
        f"Smoke: {'PASS' if test_results['smoke'].code == 0 else 'FAIL'}\n"
        f"Issues opened: {opened}\n"
        f"Issues skipped (duplicate): {skipped}"
    )


def clean_line(text: str) -> str:
    out = re.sub(r"\s+", " ", text).strip()
    return out[:160]


def main() -> int:
    repo = os.getenv("AUGUST_GITHUB_REPO", "ivarkristian/august_adventure")
    repo_url = os.getenv("AUGUST_REPO_URL", f"https://github.com/{repo}.git")
    repo_dir = Path(os.getenv("AUGUST_REPO_DIR", str(Path.home() / "august_adventure")))
    state_path = Path.home() / ".picoclaw" / "workspace" / "august-playtest" / "state.json"
    token = os.getenv("AUGUST_GITHUB_TOKEN", "")
    force = os.getenv("AUGUST_FORCE", "0") == "1"

    state = load_state(state_path)
    try:
        ensure_repo(repo_dir, repo_url)
        sha = sync_repo(repo_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"sync failed: {exc}")
        return 1

    if not force and state.get("last_tested_sha") == sha:
        print("no-new-commit")
        return 0

    try:
        python_bin = ensure_venv(repo_dir)
        test_results = run_tests(repo_dir, python_bin)
        exploratory = run_exploratory(repo_dir, python_bin)
    except Exception as exc:  # noqa: BLE001
        print(f"test setup failed: {exc}")
        return 1

    suggestions = ask_august_consultant(sha, test_results, exploratory)
    open_titles = list_open_issue_titles(repo, token) if token else set()

    opened = 0
    skipped = 0

    if token:
        for bug in suggestions["bugs"]:
            title = f"[August][Bug] {clean_line(str(bug.get('title', 'Playtest bug')))}"
            if title in open_titles:
                skipped += 1
                continue
            steps = bug.get("repro_steps", [])
            steps_text = "\n".join(f"- {clean_line(str(s))}" for s in steps[:8]) if isinstance(steps, list) else "- see transcript"
            body = (
                f"Automated August playtest report for commit `{sha}`.\n\n"
                f"Summary:\n{clean_line(str(bug.get('summary', '')))}\n\n"
                f"Severity: {clean_line(str(bug.get('severity', 'medium')))}\n\n"
                f"Repro steps:\n{steps_text}\n\n"
                "Raw test status:\n"
                f"- pytest exit: {test_results['pytest'].code}\n"
                f"- smoke exit: {test_results['smoke'].code}\n"
            )
            create_issue(repo, token, title, body, ["august-feedback", "bug", "playtest", "triage-needed"])
            open_titles.add(title)
            opened += 1

        for feat in suggestions["features"]:
            title = f"[August][Feature] {clean_line(str(feat.get('title', 'Playtest feature idea')))}"
            if title in open_titles:
                skipped += 1
                continue
            body = (
                f"Automated August creative suggestion for commit `{sha}`.\n\n"
                f"Player value:\n{clean_line(str(feat.get('player_value', '')))}\n\n"
                f"Proposal:\n{clean_line(str(feat.get('proposal', '')))}\n\n"
                "Context:\n"
                f"- pytest exit: {test_results['pytest'].code}\n"
                f"- smoke exit: {test_results['smoke'].code}\n"
            )
            create_issue(repo, token, title, body, ["august-feedback", "feature", "playtest", "triage-needed"])
            open_titles.add(title)
            opened += 1

    state.update(
        {
            "last_tested_sha": sha,
            "last_run_utc": datetime.now(UTC).isoformat(),
            "last_pytest_exit": test_results["pytest"].code,
            "last_smoke_exit": test_results["smoke"].code,
        }
    )
    save_state(state_path, state)

    mode = "full" if token else "dry-run-no-github-token"
    summary = format_summary(repo, sha, test_results, opened, skipped, mode)
    print(summary)

    discord_token, owner_id = load_picoclaw_discord()
    if discord_token and owner_id:
        try:
            send_discord_dm(discord_token, owner_id, summary)
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
