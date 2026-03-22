from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MAX_BUGS = 3
DEFAULT_MAX_FEATURES = 3

DIMENSIONS: list[tuple[str, str]] = [
    ("environment_richness", "Environment Richness"),
    ("description_vividness", "Description Vividness"),
    ("puzzle_challenge", "Puzzle and Challenge Quality"),
    ("player_agency", "Player Agency"),
    ("world_coherence", "World Coherence"),
    ("curiosity_engagement", "Curiosity and Engagement"),
]


@dataclass
class CmdResult:
    code: int
    out: str
    err: str


@dataclass
class GitHubIssue:
    title: str
    body: str
    labels: list[str]


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


def run_cmd_binary(command: list[str], input_bytes: bytes, timeout: int = 60) -> tuple[int, bytes, str]:
    proc = subprocess.run(
        command,
        input=input_bytes,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", errors="replace").strip()


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


def run_exploratory_scenarios(repo_dir: Path, python_bin: Path) -> dict[str, str]:
    scenarios = [
        (
            "curious_explorer",
            11,
            ["look", "take lamp", "north", "look", "east", "look", "use lamp", "look", "north", "look", "quit"],
        ),
        (
            "puzzle_solver",
            13,
            ["take lamp", "north", "take key", "east", "use lamp", "take coin", "north", "take idol", "inventory", "quit"],
        ),
        (
            "skeptical_breaker",
            17,
            ["drop lamp", "use lamp", "north", "east", "north", "save /tmp/august_save.json", "load /tmp/missing.json", "help", "quit"],
        ),
    ]

    results: dict[str, str] = {}
    for name, seed, commands in scenarios:
        py = (
            "from game.playtest import run_playthrough\n"
            f"cmds={json.dumps(commands)}\n"
            f"r=run_playthrough(cmds,seed={seed})\n"
            "print('\\n'.join(r.transcript))\n"
        )
        result = run_cmd([str(python_bin), "-c", py], cwd=repo_dir, timeout=300)
        if result.code != 0:
            results[name] = f"Scenario failed: {result.err}"
        else:
            results[name] = result.out
    return results


def load_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def clean_line(text: str, limit: int = 160) -> str:
    out = re.sub(r"\s+", " ", text).strip()
    return out[:limit]


def env_positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def parse_json_object(text: str) -> dict[str, Any]:
    ansi_clean = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)

    fenced: list[str] = []
    for match in re.finditer(r"```json\s*(\{.*?\})\s*```", ansi_clean, flags=re.IGNORECASE | re.DOTALL):
        fenced.append(match.group(1))

    for block in reversed(fenced):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    decoder = json.JSONDecoder()
    for i, ch in enumerate(ansi_clean):
        if ch != "{":
            continue
        try:
            data, _end = decoder.raw_decode(ansi_clean[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data

    start = ansi_clean.find("{")
    end = ansi_clean.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    blob = ansi_clean[start : end + 1]
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_dimension_scores(raw_scores: Any) -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}

    if isinstance(raw_scores, list):
        for item in raw_scores:
            if not isinstance(item, dict):
                continue
            dim = str(item.get("dimension", "")).strip().lower()
            dim = dim.replace(" ", "_")
            score = item.get("score", 3)
            why = clean_line(str(item.get("why", "")), limit=240)
            try:
                score_int = int(score)
            except (TypeError, ValueError):
                score_int = 3
            score_int = max(1, min(5, score_int))
            by_name[dim] = {"dimension": dim, "score": score_int, "why": why}

    normalized: list[dict[str, Any]] = []
    for dim_id, _label in DIMENSIONS:
        item = by_name.get(dim_id, {"dimension": dim_id, "score": 3, "why": "No clear assessment provided."})
        normalized.append(item)
    return normalized


def normalize_suggestions(raw: dict[str, Any], max_bugs: int, max_features: int) -> dict[str, Any]:
    review = raw.get("overall_review", {})
    if not isinstance(review, dict):
        review = {}

    bugs_raw = raw.get("bugs", [])
    features_raw = raw.get("features", [])
    if not isinstance(bugs_raw, list):
        bugs_raw = []
    if not isinstance(features_raw, list):
        features_raw = []

    bugs: list[dict[str, Any]] = []
    for bug in bugs_raw:
        if not isinstance(bug, dict):
            continue
        bugs.append(
            {
                "title": clean_line(str(bug.get("title", "Playtest bug")), 120),
                "summary": clean_line(str(bug.get("summary", "")), 800),
                "repro_steps": [clean_line(str(x), 240) for x in bug.get("repro_steps", [])[:10]]
                if isinstance(bug.get("repro_steps"), list)
                else [],
                "severity": clean_line(str(bug.get("severity", "medium")), 16).lower(),
            }
        )
    bugs = bugs[:max_bugs]

    features: list[dict[str, Any]] = []
    for feature in features_raw:
        if not isinstance(feature, dict):
            continue
        features.append(
            {
                "title": clean_line(str(feature.get("title", "Playtest feature idea")), 120),
                "player_value": clean_line(str(feature.get("player_value", "")), 800),
                "proposal": clean_line(str(feature.get("proposal", "")), 800),
            }
        )
    features = features[:max_features]

    dim_scores = normalize_dimension_scores(review.get("dimension_scores", []))
    average = sum(item["score"] for item in dim_scores) / len(dim_scores)

    normalized = {
        "overall_review": {
            "overall_thoughts": clean_line(str(review.get("overall_thoughts", "")), 1200),
            "dimension_scores": dim_scores,
            "overall_score": round(average, 2),
            "location_assessment": clean_line(str(review.get("location_assessment", "")), 1200),
            "quests_challenges_assessment": clean_line(str(review.get("quests_challenges_assessment", "")), 1200),
            "agency_assessment": clean_line(str(review.get("agency_assessment", "")), 1200),
            "top_strengths": [clean_line(str(x), 220) for x in review.get("top_strengths", [])[:3]]
            if isinstance(review.get("top_strengths"), list)
            else [],
            "top_improvements": [clean_line(str(x), 220) for x in review.get("top_improvements", [])[:3]]
            if isinstance(review.get("top_improvements"), list)
            else [],
        },
        "bugs": bugs,
        "features": features,
    }
    return normalized


def build_consultant_prompt(
    commit_sha: str,
    test_results: dict[str, CmdResult],
    exploratory: dict[str, str],
    rubric_text: str,
    roles_text: str,
    max_bugs: int,
    max_features: int,
) -> str:
    transcript = []
    for name, text in exploratory.items():
        transcript.append(f"## Scenario: {name}\n{text[:2800]}")
    transcript_blob = "\n\n".join(transcript)

    prompt = f"""
You are August, a senior text-adventure playtester and creative consultant.

Follow the rubric and role guidance below.

RUBRIC:
{rubric_text[:9000]}

ROLE GUIDANCE:
{roles_text[:7000]}

Context:
- Commit: {commit_sha}
- Pytest exit: {test_results['pytest'].code}
- Smoke exit: {test_results['smoke'].code}
- Pytest output:
{test_results['pytest'].out[:2200]}
{test_results['pytest'].err[:1200]}

- Smoke output:
{test_results['smoke'].out[:2200]}
{test_results['smoke'].err[:1200]}

Exploratory transcripts:
{transcript_blob}

Return STRICT JSON only with this schema:
{{
  "overall_review": {{
    "overall_thoughts": "string",
    "dimension_scores": [
      {{"dimension":"environment_richness","score":1-5,"why":"string"}},
      {{"dimension":"description_vividness","score":1-5,"why":"string"}},
      {{"dimension":"puzzle_challenge","score":1-5,"why":"string"}},
      {{"dimension":"player_agency","score":1-5,"why":"string"}},
      {{"dimension":"world_coherence","score":1-5,"why":"string"}},
      {{"dimension":"curiosity_engagement","score":1-5,"why":"string"}}
    ],
    "location_assessment":"string",
    "quests_challenges_assessment":"string",
    "agency_assessment":"string",
    "top_strengths":["string"],
    "top_improvements":["string"]
  }},
  "bugs": [{{"title":"string","summary":"string","repro_steps":["string"],"severity":"low|medium|high"}}],
  "features": [{{"title":"string","player_value":"string","proposal":"string"}}]
}}

Rules:
- Max {max_bugs} bugs.
- Max {max_features} features.
- Base scores on rubric anchors, do not invent a custom scale.
- Keep bug and feature titles concise.
- Ensure qualitative sections are specific and evidence-based.
""".strip()
    return prompt


def ask_august_consultant(
    commit_sha: str,
    test_results: dict[str, CmdResult],
    exploratory: dict[str, str],
    rubric_text: str,
    roles_text: str,
    max_bugs: int,
    max_features: int,
) -> dict[str, Any]:
    prompt = build_consultant_prompt(
        commit_sha,
        test_results,
        exploratory,
        rubric_text,
        roles_text,
        max_bugs,
        max_features,
    )

    def is_meaningful(pack: dict[str, Any]) -> bool:
        review = pack.get("overall_review", {}) if isinstance(pack, dict) else {}
        if not isinstance(review, dict):
            return False
        if str(review.get("overall_thoughts", "")).strip():
            return True
        if isinstance(review.get("top_strengths"), list) and review.get("top_strengths"):
            return True
        if isinstance(review.get("top_improvements"), list) and review.get("top_improvements"):
            return True
        return False

    attempts: list[str] = [prompt]

    concise_transcript = ""
    for key in ["puzzle_solver", "curious_explorer", "skeptical_breaker"]:
        if key in exploratory and exploratory[key].strip():
            concise_transcript = exploratory[key][:1800]
            break

    concise_prompt = f"""
You are August, a text-adventure playtester. Return STRICT JSON only.
Use rubric anchors exactly; do not invent scoring scales.

Rubric:
{rubric_text[:3500]}

Context:
- Commit: {commit_sha}
- Pytest exit: {test_results['pytest'].code}
- Smoke exit: {test_results['smoke'].code}
- Smoke output excerpt:
{test_results['smoke'].out[:1400]}

- Exploratory excerpt:
{concise_transcript}

Schema:
{{
  "overall_review": {{
    "overall_thoughts": "string",
    "dimension_scores": [
      {{"dimension":"environment_richness","score":1-5,"why":"string"}},
      {{"dimension":"description_vividness","score":1-5,"why":"string"}},
      {{"dimension":"puzzle_challenge","score":1-5,"why":"string"}},
      {{"dimension":"player_agency","score":1-5,"why":"string"}},
      {{"dimension":"world_coherence","score":1-5,"why":"string"}},
      {{"dimension":"curiosity_engagement","score":1-5,"why":"string"}}
    ],
    "location_assessment":"string",
    "quests_challenges_assessment":"string",
    "agency_assessment":"string",
    "top_strengths":["string"],
    "top_improvements":["string"]
  }},
  "bugs": [{{"title":"string","summary":"string","repro_steps":["string"],"severity":"low|medium|high"}}],
  "features": [{{"title":"string","player_value":"string","proposal":"string"}}]
}}

Limits:
- max {max_bugs} bugs
- max {max_features} features
""".strip()
    attempts.append(concise_prompt)

    for attempt in attempts:
        result = run_cmd(["picoclaw", "agent", "-m", attempt], timeout=420)
        text = "\n".join(part for part in [result.out, result.err] if part)
        parsed = parse_json_object(text)
        pack = normalize_suggestions(parsed, max_bugs, max_features)
        if is_meaningful(pack):
            return pack

    return normalize_suggestions({}, max_bugs, max_features)


def format_iso_to_ts(iso_text: str) -> float:
    value = iso_text.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).timestamp()


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def build_github_app_jwt(app_id: str, private_key_path: Path) -> str:
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
    unsigned = f"{b64url(json.dumps(header, separators=(',', ':')).encode())}.{b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    code, sig, err = run_cmd_binary(
        ["openssl", "dgst", "-binary", "-sha256", "-sign", str(private_key_path)],
        unsigned.encode("utf-8"),
    )
    if code != 0:
        raise RuntimeError(f"openssl sign failed: {err}")
    return f"{unsigned}.{b64url(sig)}"


class GitHubClient:
    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.pat = self._normalize_env_token("AUGUST_GITHUB_TOKEN")
        self.app_id = os.getenv("AUGUST_GH_APP_ID", "").strip()
        self.installation_id = os.getenv("AUGUST_GH_INSTALLATION_ID", "").strip()
        self.app_key_path = Path(os.getenv("AUGUST_GH_APP_PRIVATE_KEY_PATH", "").strip())

        self.installation_token = ""
        self.installation_expiry = 0.0

    @staticmethod
    def _normalize_env_token(name: str) -> str:
        token = os.getenv(name, "").strip()
        if token in {"", "ghp_replace_me", "replace_me"}:
            return ""
        return token

    @property
    def mode(self) -> str:
        if self.app_id and self.installation_id and self.app_key_path.exists():
            return "app"
        if self.pat:
            return "pat"
        return "none"

    def _request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None = None,
    ) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(url=url, method=method, data=data, headers=headers)
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}

    def _refresh_installation_token(self, force: bool = False) -> None:
        if self.mode != "app":
            return
        now = time.time()
        if not force and self.installation_token and now < self.installation_expiry - 300:
            return

        jwt = build_github_app_jwt(self.app_id, self.app_key_path)
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "august-playtest-bot",
            "Content-Type": "application/json",
        }
        data = self._request_json(
            "POST",
            f"https://api.github.com/app/installations/{self.installation_id}/access_tokens",
            headers,
            {},
        )
        if not isinstance(data, dict):
            raise RuntimeError("invalid installation token response")
        token = data.get("token")
        expires_at = data.get("expires_at")
        if not isinstance(token, str) or not isinstance(expires_at, str):
            raise RuntimeError("missing installation token fields")
        self.installation_token = token
        self.installation_expiry = format_iso_to_ts(expires_at)

    def _repo_headers(self) -> dict[str, str]:
        if self.mode == "app":
            self._refresh_installation_token()
            token = self.installation_token
        elif self.mode == "pat":
            token = self.pat
        else:
            raise RuntimeError("github auth is not configured")

        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "august-playtest-bot",
            "Content-Type": "application/json",
        }

    def request_repo(self, method: str, path: str, payload: dict[str, Any] | None = None, retry: bool = True) -> Any:
        url = f"https://api.github.com/repos/{self.repo}{path}"
        headers = self._repo_headers()
        try:
            return self._request_json(method, url, headers, payload)
        except HTTPError as exc:
            if self.mode == "app" and retry and exc.code in {401, 403}:
                self._refresh_installation_token(force=True)
                return self.request_repo(method, path, payload, retry=False)
            raise


def list_open_issue_titles(gh: GitHubClient) -> set[str]:
    if gh.mode == "none":
        return set()
    try:
        data = gh.request_repo("GET", "/issues?state=open&per_page=100")
    except (HTTPError, URLError, RuntimeError):
        return set()
    titles: set[str] = set()
    if isinstance(data, list):
        for issue in data:
            if isinstance(issue, dict) and isinstance(issue.get("title"), str):
                titles.add(issue["title"])
    return titles


def create_issue(gh: GitHubClient, issue: GitHubIssue) -> str:
    data = gh.request_repo(
        "POST",
        "/issues",
        {"title": issue.title[:120], "body": issue.body[:60000], "labels": issue.labels},
    )
    if isinstance(data, dict) and isinstance(data.get("html_url"), str):
        return data["html_url"]
    return ""


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


def send_discord_dm(token: str, owner_id: str, content: str) -> None:
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "august-playtest-bot",
    }
    dm_req = Request(
        url="https://discord.com/api/v10/users/@me/channels",
        method="POST",
        data=json.dumps({"recipient_id": owner_id}).encode("utf-8"),
        headers=headers,
    )
    with urlopen(dm_req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    dm_data = json.loads(body)
    channel_id = dm_data.get("id")
    if not isinstance(channel_id, str):
        return

    msg_req = Request(
        url=f"https://discord.com/api/v10/channels/{channel_id}/messages",
        method="POST",
        data=json.dumps({"content": content[:1900]}).encode("utf-8"),
        headers=headers,
    )
    with urlopen(msg_req, timeout=30):
        pass


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def format_score_table(scores: list[dict[str, Any]]) -> str:
    lines = ["| Dimension | Score | Why |", "|---|---:|---|"]
    name_map = {dim_id: label for dim_id, label in DIMENSIONS}
    for item in scores:
        dim = str(item.get("dimension", ""))
        label = name_map.get(dim, dim)
        score = item.get("score", 3)
        why = clean_line(str(item.get("why", "")), 180)
        lines.append(f"| {label} | {score} | {why} |")
    return "\n".join(lines)


def build_overall_review_issue(
    commit_sha: str,
    review: dict[str, Any],
    test_results: dict[str, CmdResult],
) -> GitHubIssue:
    scores = review["dimension_scores"]
    score_table = format_score_table(scores)
    strengths = "\n".join(f"- {x}" for x in review.get("top_strengths", [])) or "- None"
    improvements = "\n".join(f"- {x}" for x in review.get("top_improvements", [])) or "- None"

    body = (
        f"Automated August qualitative review for commit `{commit_sha}`.\n\n"
        f"Overall score (average): **{review['overall_score']}/5**\n\n"
        f"Overall thoughts:\n{review.get('overall_thoughts', '')}\n\n"
        f"### Rubric Scores\n{score_table}\n\n"
        f"### Environment and Locations\n{review.get('location_assessment', '')}\n\n"
        f"### Quests and Challenges\n{review.get('quests_challenges_assessment', '')}\n\n"
        f"### Player Agency\n{review.get('agency_assessment', '')}\n\n"
        f"### Top Strengths\n{strengths}\n\n"
        f"### Top Improvements\n{improvements}\n\n"
        "### Test Context\n"
        f"- pytest exit: {test_results['pytest'].code}\n"
        f"- smoke exit: {test_results['smoke'].code}\n"
        "- rubric: docs/playtest_rubric.md\n"
    )
    title = f"[August][Review] Qualitative playtest for {commit_sha[:12]}"
    return GitHubIssue(title=title, body=body, labels=["august-feedback", "playtest", "triage-needed"])


def build_bug_issue(commit_sha: str, bug: dict[str, Any], test_results: dict[str, CmdResult]) -> GitHubIssue:
    steps = bug.get("repro_steps", [])
    steps_text = "\n".join(f"- {x}" for x in steps) if steps else "- See exploratory transcript"
    body = (
        f"Automated August bug report for commit `{commit_sha}`.\n\n"
        f"Summary:\n{bug.get('summary', '')}\n\n"
        f"Severity: {bug.get('severity', 'medium')}\n\n"
        f"Repro steps:\n{steps_text}\n\n"
        "Context:\n"
        f"- pytest exit: {test_results['pytest'].code}\n"
        f"- smoke exit: {test_results['smoke'].code}\n"
    )
    title = f"[August][Bug] {bug.get('title', 'Playtest bug')}"
    return GitHubIssue(title=title, body=body, labels=["august-feedback", "bug", "playtest", "triage-needed"])


def build_feature_issue(commit_sha: str, feature: dict[str, Any], test_results: dict[str, CmdResult]) -> GitHubIssue:
    body = (
        f"Automated August feature suggestion for commit `{commit_sha}`.\n\n"
        f"Player value:\n{feature.get('player_value', '')}\n\n"
        f"Proposal:\n{feature.get('proposal', '')}\n\n"
        "Context:\n"
        f"- pytest exit: {test_results['pytest'].code}\n"
        f"- smoke exit: {test_results['smoke'].code}\n"
    )
    title = f"[August][Feature] {feature.get('title', 'Playtest feature idea')}"
    return GitHubIssue(title=title, body=body, labels=["august-feedback", "feature", "playtest", "triage-needed"])


def format_summary(
    repo: str,
    sha: str,
    mode: str,
    test_results: dict[str, CmdResult],
    review: dict[str, Any],
    opened_urls: list[str],
    skipped_count: int,
    prev_score: float | None,
) -> str:
    score = float(review.get("overall_score", 0.0))
    delta = score - prev_score if prev_score is not None else None
    delta_text = "n/a" if delta is None else f"{delta:+.2f}"

    score_lines = []
    dim_name = {dim_id: label for dim_id, label in DIMENSIONS}
    for item in review.get("dimension_scores", []):
        dim = str(item.get("dimension", ""))
        label = dim_name.get(dim, dim)
        score_lines.append(f"- {label}: {item.get('score', 3)}/5 - {clean_line(str(item.get('why', '')), 90)}")

    strengths = review.get("top_strengths", [])
    improvements = review.get("top_improvements", [])

    strength_lines = [f"- {clean_line(str(x), 120)}" for x in strengths[:3]] if strengths else ["- None"]
    improvement_lines = [f"- {clean_line(str(x), 120)}" for x in improvements[:3]] if improvements else ["- None"]

    lines = [
        "August playtest report",
        f"Repo: {repo}",
        f"Commit: {sha[:12]}",
        f"Mode: {mode}",
        f"Pytest: {'PASS' if test_results['pytest'].code == 0 else 'FAIL'}",
        f"Smoke: {'PASS' if test_results['smoke'].code == 0 else 'FAIL'}",
        f"Overall score: {score:.2f}/5 (trend: {delta_text})",
        "Dimension scores:",
        *score_lines,
        "Qualitative assessment:",
        f"- Environment and locations: {clean_line(str(review.get('location_assessment', '')), 200)}",
        f"- Quests and challenges: {clean_line(str(review.get('quests_challenges_assessment', '')), 200)}",
        f"- Player agency: {clean_line(str(review.get('agency_assessment', '')), 200)}",
        "Top strengths:",
        *strength_lines,
        "Top improvements:",
        *improvement_lines,
        f"Issues opened: {len(opened_urls)}",
        f"Issues skipped (duplicate): {skipped_count}",
    ]

    if opened_urls:
        lines.append("Issue links:")
        lines.extend(f"- {url}" for url in opened_urls[:7])
    return "\n".join(lines)


def main() -> int:
    repo = os.getenv("AUGUST_GITHUB_REPO", "ivarkristian/august_adventure")
    repo_url = os.getenv("AUGUST_REPO_URL", f"https://github.com/{repo}.git")
    repo_dir = Path(os.getenv("AUGUST_REPO_DIR", str(Path.home() / "august_adventure")))
    state_path = Path.home() / ".picoclaw" / "workspace" / "august-playtest" / "state.json"
    force = os.getenv("AUGUST_FORCE", "0") == "1"
    max_bugs = env_positive_int("AUGUST_MAX_BUGS", DEFAULT_MAX_BUGS)
    max_features = env_positive_int("AUGUST_MAX_FEATURES", DEFAULT_MAX_FEATURES)

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
        exploratory = run_exploratory_scenarios(repo_dir, python_bin)
    except Exception as exc:  # noqa: BLE001
        print(f"test setup failed: {exc}")
        return 1

    rubric_text = load_text_file(repo_dir / "docs" / "playtest_rubric.md")
    roles_text = load_text_file(repo_dir / "ops" / "august" / "consultant_roles.md")
    review_pack = ask_august_consultant(
        sha,
        test_results,
        exploratory,
        rubric_text,
        roles_text,
        max_bugs,
        max_features,
    )

    gh = GitHubClient(repo)
    open_titles = list_open_issue_titles(gh)
    opened_urls: list[str] = []
    skipped_count = 0
    github_errors: list[str] = []

    if gh.mode != "none":
        issues: list[GitHubIssue] = []
        for bug in review_pack["bugs"]:
            issues.append(build_bug_issue(sha, bug, test_results))
        for feature in review_pack["features"]:
            issues.append(build_feature_issue(sha, feature, test_results))
        issues.append(build_overall_review_issue(sha, review_pack["overall_review"], test_results))

        for issue in issues:
            if issue.title in open_titles:
                skipped_count += 1
                continue
            try:
                url = create_issue(gh, issue)
            except Exception as exc:  # noqa: BLE001
                github_errors.append(f"{issue.title}: {exc}")
                continue
            if url:
                opened_urls.append(url)
            open_titles.add(issue.title)

    prev_score = None
    if isinstance(state.get("last_overall_score"), (int, float)):
        prev_score = float(state["last_overall_score"])

    mode = gh.mode if not github_errors else f"{gh.mode}-with-errors"
    summary = format_summary(repo, sha, mode, test_results, review_pack["overall_review"], opened_urls, skipped_count, prev_score)
    if github_errors:
        summary += "\nGitHub errors:\n- " + "\n- ".join(clean_line(x, 240) for x in github_errors[:5])
    print(summary)

    state.update(
        {
            "last_tested_sha": sha,
            "last_run_utc": datetime.now(UTC).isoformat(),
            "last_pytest_exit": test_results["pytest"].code,
            "last_smoke_exit": test_results["smoke"].code,
            "last_overall_score": float(review_pack["overall_review"].get("overall_score", 0.0)),
        }
    )
    save_state(state_path, state)

    discord_token, owner_id = load_picoclaw_discord()
    if discord_token and owner_id:
        try:
            send_discord_dm(discord_token, owner_id, summary)
        except Exception:  # noqa: BLE001
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
