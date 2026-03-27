from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
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


ROLE_ORDER = ["qa", "narrative", "puzzle", "agency", "publisher"]


ROLE_HEADINGS = {
    "qa": "Role 1: QA Bug Hunter",
    "narrative": "Role 2: Narrative Designer",
    "puzzle": "Role 3: Puzzle Architect",
    "agency": "Role 4: Player Agency Advocate",
    "publisher": "Role 5: Experienced Game Publisher",
}


ROLE_LABELS = {
    "qa": "QA Bug Hunter",
    "narrative": "Narrative Designer",
    "puzzle": "Puzzle Architect",
    "agency": "Player Agency Advocate",
    "publisher": "Experienced Game Publisher",
}


ROLE_WORKSPACE_DIR = {
    "qa": "qa",
    "narrative": "narrative",
    "puzzle": "puzzle",
    "agency": "agency",
    "publisher": "publisher",
}


ROLE_FIELD_PRIORITY = {
    "overall_thoughts": ["publisher", "narrative", "qa", "puzzle", "agency"],
    "location_assessment": ["narrative", "publisher", "qa", "agency", "puzzle"],
    "quests_challenges_assessment": ["puzzle", "publisher", "qa", "narrative", "agency"],
    "agency_assessment": ["agency", "publisher", "qa", "puzzle", "narrative"],
    "story_arc_assessment": ["narrative", "publisher", "agency", "puzzle", "qa"],
}


DIMENSION_ROLE_PRIORITY = {
    "environment_richness": ["narrative", "publisher", "qa", "puzzle", "agency"],
    "description_vividness": ["narrative", "publisher", "qa", "puzzle", "agency"],
    "puzzle_challenge": ["puzzle", "qa", "publisher", "agency", "narrative"],
    "player_agency": ["agency", "publisher", "qa", "puzzle", "narrative"],
    "world_coherence": ["qa", "narrative", "puzzle", "publisher", "agency"],
    "curiosity_engagement": ["publisher", "narrative", "puzzle", "agency", "qa"],
}


@dataclass
class ContextCaps:
    rubric: int
    role_guidance: int
    game_description: int
    rules: int
    smoke: int
    transcript_summary: int
    transcript_excerpt: int


@dataclass
class GameProfile:
    game_name: str
    short_description: str
    allowed_actions: list[str]
    exploratory_scenarios: list[dict[str, Any]]
    gameplay_terms: list[str]


@dataclass
class ConsultantDiagnostics:
    role_success: dict[str, bool]
    substantive_roles: int
    attempt_records: list[dict[str, Any]]


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


def run_cmd(
    command: list[str],
    cwd: Path | None = None,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> CmdResult:
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CmdResult(124, stdout.strip(), clean_line(f"timeout after {timeout}s: {stderr}", 220))
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
    if not repo_url.strip():
        raise RuntimeError("AUGUST_REPO_URL is required when local repo checkout does not exist")
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    result = run_cmd(["git", "clone", repo_url, str(repo_dir)], timeout=600)
    if result.code != 0:
        raise RuntimeError(f"git clone failed: {result.err}")


def parse_github_slug_from_remote(remote_url: str) -> str:
    value = remote_url.strip()
    patterns = [
        re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", re.IGNORECASE),
        re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", re.IGNORECASE),
        re.compile(r"^ssh://git@github\.com/([^/]+)/([^/]+?)(?:\.git)?$", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.match(value)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return ""


def detect_repo_slug(repo_dir: Path, explicit_slug: str) -> str:
    if explicit_slug.strip():
        return explicit_slug.strip()
    origin = run_cmd(["git", "remote", "get-url", "origin"], cwd=repo_dir)
    if origin.code != 0:
        return ""
    return parse_github_slug_from_remote(origin.out)


def parse_short_description_from_markdown(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            if lines:
                break
            continue
        if line.startswith("#"):
            continue
        lines.append(line)

    if not lines:
        return ""
    return clean_line(" ".join(lines), 700)


def parse_allowed_actions_from_rules_text(text: str) -> list[str]:
    actions: list[str] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-", "*")):
            item = line[1:].strip()
        else:
            numbered = re.match(r"^\d+[\.)]\s+(.*)$", line)
            if not numbered:
                continue
            item = numbered.group(1).strip()

        cleaned = clean_line(item, 120)
        if cleaned:
            actions.append(cleaned)

    deduped: list[str] = []
    seen: set[str] = set()
    for action in actions:
        key = action.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(action)
    return deduped


def load_game_profile(repo_dir: Path) -> GameProfile:
    profile_path = repo_dir / "ops" / "august" / "game_profile.json"
    if not profile_path.exists():
        raise RuntimeError(f"missing required game profile: {profile_path}")

    try:
        raw = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid game profile JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise RuntimeError("invalid game profile: expected JSON object")

    game_name = str(raw.get("game_name", "")).strip()
    short_description = str(raw.get("short_description", "")).strip()
    allowed_actions_raw = raw.get("allowed_actions", [])
    scenarios_raw = raw.get("exploratory_scenarios", [])
    gameplay_terms_raw = raw.get("gameplay_terms", [])
    description_file_rel = str(raw.get("description_file", "game/game_description.md")).strip()
    rules_file_rel = str(raw.get("rules_file", "game/game_rules.md")).strip()

    if description_file_rel:
        description_path = repo_dir / description_file_rel
        if description_path.exists():
            short_description = parse_short_description_from_markdown(description_path.read_text(encoding="utf-8"))

    allowed_actions: list[str] = []
    if rules_file_rel:
        rules_path = repo_dir / rules_file_rel
        if rules_path.exists():
            allowed_actions = parse_allowed_actions_from_rules_text(rules_path.read_text(encoding="utf-8"))

    if not game_name:
        raise RuntimeError("invalid game profile: game_name is required")
    if not short_description:
        raise RuntimeError("invalid game profile: short_description is required")
    if not isinstance(scenarios_raw, list) or not scenarios_raw:
        raise RuntimeError("invalid game profile: exploratory_scenarios must be a non-empty list")

    if not allowed_actions:
        if not isinstance(allowed_actions_raw, list) or not allowed_actions_raw:
            raise RuntimeError("invalid game profile: allowed_actions must be a non-empty list")
        allowed_actions = [clean_line(str(action), 120) for action in allowed_actions_raw if clean_line(str(action), 120)]

    if not allowed_actions:
        raise RuntimeError("invalid game profile: allowed_actions contains no usable entries")

    scenarios: list[dict[str, Any]] = []
    for idx, entry in enumerate(scenarios_raw):
        if not isinstance(entry, dict):
            raise RuntimeError(f"invalid game profile: exploratory_scenarios[{idx}] must be an object")
        name = clean_line(str(entry.get("name", "")), 60)
        seed = entry.get("seed")
        commands_raw = entry.get("commands", [])
        if not name:
            raise RuntimeError(f"invalid game profile: exploratory_scenarios[{idx}].name is required")
        try:
            seed_int = int(str(seed))
        except (TypeError, ValueError) as exc:
            raise RuntimeError(f"invalid game profile: exploratory_scenarios[{idx}].seed must be int") from exc
        if not isinstance(commands_raw, list) or not commands_raw:
            raise RuntimeError(f"invalid game profile: exploratory_scenarios[{idx}].commands must be non-empty list")
        commands = [clean_line(str(command), 160) for command in commands_raw if clean_line(str(command), 160)]
        if not commands:
            raise RuntimeError(f"invalid game profile: exploratory_scenarios[{idx}].commands has no usable entries")
        scenarios.append({"name": name, "seed": seed_int, "commands": commands})

    gameplay_terms: list[str] = []
    if isinstance(gameplay_terms_raw, list):
        gameplay_terms = [clean_line(str(term).lower(), 40) for term in gameplay_terms_raw if clean_line(str(term), 40)]

    return GameProfile(
        game_name=game_name,
        short_description=short_description,
        allowed_actions=allowed_actions,
        exploratory_scenarios=scenarios,
        gameplay_terms=gameplay_terms,
    )


def sync_repo(repo_dir: Path) -> str:
    sync_mode = os.getenv("AUGUST_SYNC_MODE", "hard-reset").strip().lower()

    if sync_mode == "none":
        head = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        if head.code != 0:
            raise RuntimeError(f"git rev-parse failed: {head.err}")
        return head.out.strip()

    fetch = run_cmd(["git", "fetch", "origin"], cwd=repo_dir, timeout=300)
    if fetch.code != 0:
        raise RuntimeError(f"git fetch failed: {fetch.err}")

    checkout = run_cmd(["git", "checkout", "main"], cwd=repo_dir)
    if checkout.code != 0:
        raise RuntimeError(f"git checkout failed: {checkout.err}")

    if sync_mode == "fast-forward":
        pull = run_cmd(["git", "pull", "--ff-only", "origin", "main"], cwd=repo_dir, timeout=300)
        if pull.code != 0:
            raise RuntimeError(f"git pull --ff-only failed: {pull.err}")
        head = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        if head.code != 0:
            raise RuntimeError(f"git rev-parse failed: {head.err}")
        return head.out.strip()

    rev = run_cmd(["git", "rev-parse", "origin/main"], cwd=repo_dir)
    if rev.code != 0:
        raise RuntimeError(f"git rev-parse failed: {rev.err}")
    sha = rev.out.strip()

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


def role_workspaces_root() -> Path:
    root_raw = os.getenv("AUGUST_PICOCLAW_ROLE_WORKSPACES_ROOT", "").strip()
    if root_raw:
        return Path(root_raw).expanduser()
    return Path.home() / ".picoclaw" / "workspace" / "august-playtest" / "workspaces"


def resolve_role_workspace(role_key: str) -> Path | None:
    root = role_workspaces_root()
    role_dir = ROLE_WORKSPACE_DIR.get(role_key, role_key)
    path = root / role_dir
    if path.exists():
        return path
    return None


def sanitize_turn_command(raw: str) -> str:
    value = raw.strip().strip("`\"")
    value = re.sub(r"\s+", " ", value)
    return value[:80].strip()


def extract_turn_command(text: str) -> str:
    parsed = parse_json_object(text)
    if isinstance(parsed, dict):
        candidate = sanitize_turn_command(str(parsed.get("command", "")))
        if candidate:
            return candidate

    cleaned = sanitize_agent_output(text, 400)
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("{") or stripped.startswith("["):
            continue
        if ":" in stripped and len(stripped.split()) > 5:
            continue
        candidate = sanitize_turn_command(stripped)
        if candidate:
            return candidate
    return ""


def load_roles_text(repo_dir: Path) -> str:
    roles_dir = repo_dir / "ops" / "august" / "roles"
    sections: list[str] = []

    if roles_dir.exists():
        for role_key in ROLE_ORDER:
            role_path = roles_dir / f"{role_key}.md"
            if not role_path.exists():
                continue
            body = role_path.read_text(encoding="utf-8").strip()
            if not body:
                continue
            sections.append(f"## {ROLE_HEADINGS[role_key]}\n\n{body}")

        synthesis_path = roles_dir / "synthesis.md"
        if synthesis_path.exists():
            synthesis = synthesis_path.read_text(encoding="utf-8").strip()
            if synthesis:
                sections.append(f"## Synthesis Guidance\n\n{synthesis}")

    if sections:
        return "\n\n".join(sections).rstrip() + "\n"

    return load_text_file(repo_dir / "ops" / "august" / "consultant_roles.md")


def build_turn_prompt(
    role_key: str,
    profile: GameProfile,
    short_description: str,
    location: str,
    inventory: list[str],
    turn_index: int,
    max_actions: int,
    location_changes: int,
    max_location_changes: int,
    recent_transcript: str,
) -> str:
    role_label = ROLE_LABELS[role_key]
    actions = "\n".join(f"- {item}" for item in profile.allowed_actions)
    inv = ", ".join(sorted(inventory)) if inventory else "(empty)"
    location_budget = (
        f"{location_changes}/{max_location_changes}" if max_location_changes > 0 else f"{location_changes} (unlimited)"
    )
    return f"""
TASK_MODE: NEXT_COMMAND
Role: {role_label}
Game: {profile.game_name}
Game description: {short_description}
Action: {turn_index}/{max_actions}
Current location key: {location}
Inventory: {inv}
Location changes used: {location_budget}

You are actively playtesting. Decide the next command based on current evidence.
Prefer exploration, fair puzzle discovery, and meaningful interactions.
Avoid save/load/help unless absolutely necessary.

Allowed actions:
{actions}

Recent transcript:
{recent_transcript}

Return STRICT JSON only:
{{"command":"<next command>","reason":"<short reason>"}}
""".strip()


def run_exploratory_scenarios(repo_dir: Path, profile: GameProfile) -> dict[str, str]:
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

    try:
        from game.engine import GameEngine  # type: ignore
        from game.parser import parse_command  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {"role_runner": f"Failed to load game modules for unscripted playtest: {exc}"}

    model_override = os.getenv("AUGUST_PICOCLAW_MODEL", "").strip()
    escalation_model = os.getenv("AUGUST_PICOCLAW_ESCALATION_MODEL", "").strip()
    session_prefix = os.getenv("AUGUST_PICOCLAW_SESSION_PREFIX", "cli:august-playtest")
    max_actions = env_positive_int("AUGUST_ROLE_MAX_ACTIONS", env_positive_int("AUGUST_ROLE_MAX_TURNS", 32))
    max_location_changes = env_nonnegative_int("AUGUST_ROLE_MAX_LOCATION_CHANGES", 16)
    transcript_window = env_positive_int("AUGUST_ROLE_TRANSCRIPT_WINDOW", 14)

    results: dict[str, str] = {}

    for idx, role_key in enumerate(ROLE_ORDER):
        seed = 101 + (idx * 17)
        engine = GameEngine(seed=seed)
        session_key = build_consultant_session_key(session_prefix, f"play-{role_key}", idx + 1)
        workspace = resolve_role_workspace(role_key)

        transcript_lines = [engine.look()]
        stagnant_turns = 0
        previous_signature = ""
        location_changes = 0

        for turn in range(1, max_actions + 1):
            current_location = str(getattr(engine.state, "location", "unknown"))
            recent = "\n".join(transcript_lines[-transcript_window:])
            prompt = build_turn_prompt(
                role_key=role_key,
                profile=profile,
                short_description=profile.short_description,
                location=current_location,
                inventory=list(getattr(engine.state, "inventory", [])),
                turn_index=turn,
                max_actions=max_actions,
                location_changes=location_changes,
                max_location_changes=max_location_changes,
                recent_transcript=recent,
            )

            result = run_picoclaw_consultant(
                prompt,
                session_key,
                model_override,
                role_workspace=workspace,
                timeout=180,
                reset_main=False,
            )
            combined = "\n".join(part for part in [result.out, result.err] if part)
            command = validate_turn_command(extract_turn_command(combined), parse_command)
            if not command and escalation_model:
                escalation_result = run_picoclaw_consultant(
                    prompt,
                    session_key,
                    escalation_model,
                    role_workspace=workspace,
                    timeout=180,
                    reset_main=False,
                )
                escalation_combined = "\n".join(part for part in [escalation_result.out, escalation_result.err] if part)
                command = validate_turn_command(extract_turn_command(escalation_combined), parse_command)
            if not command:
                command = "look"

            transcript_lines.append(f"> {command}")
            output, done = engine.step(command)
            transcript_lines.append(output)

            next_location = str(getattr(engine.state, "location", "unknown"))
            if next_location != current_location:
                location_changes += 1

            signature = "|".join(
                [
                    str(getattr(engine.state, "location", "")),
                    ",".join(sorted(getattr(engine.state, "inventory", []))),
                    clean_line(output.lower(), 120),
                ]
            )
            if signature == previous_signature:
                stagnant_turns += 1
            else:
                stagnant_turns = 0
            previous_signature = signature

            if done:
                break
            if max_location_changes > 0 and location_changes >= max_location_changes:
                transcript_lines.append(
                    f"[runner] stopping role run: location-change budget reached ({location_changes}/{max_location_changes})"
                )
                break
            if stagnant_turns >= 6:
                transcript_lines.append("[runner] stopping role run: low-progress loop detected")
                break

        results[f"role_{role_key}"] = "\n".join(transcript_lines).strip()

    return results


def load_world_from_source(repo_dir: Path) -> dict[str, Any]:
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))
    try:
        from game.world import build_world  # type: ignore
    except Exception:  # noqa: BLE001
        return {}
    try:
        world = build_world()
    except Exception:  # noqa: BLE001
        return {}
    return world if isinstance(world, dict) else {}


def build_source_map_text(game_name: str, world: dict[str, Any]) -> str:
    lines = [
        f"{game_name} Source Map",
        "(derived from available world source when supported)",
        "",
    ]

    if not world:
        lines.append("World source map unavailable for this game profile.")
        return "\n".join(lines).rstrip() + "\n"

    for room_key in world:
        room = world[room_key]
        room_name = getattr(room, "name", room_key)
        lines.append(f"Room: {room_name} [{room_key}]")

        exits = getattr(room, "exits", {})
        if exits:
            lines.append("  Exits:")
            for direction, dest in exits.items():
                dest_name = getattr(world.get(dest, None), "name", dest)
                lines.append(f"    - {direction} -> {dest_name} [{dest}]")
        else:
            lines.append("  Exits: none")

        locks = getattr(room, "locks", {})
        if locks:
            lines.append("  Locks:")
            for direction, item in locks.items():
                lines.append(f"    - {direction} requires {item}")

        items = getattr(room, "items", [])
        if items:
            lines.append("  Items:")
            for item in items:
                lines.append(f"    - {item}")
        else:
            lines.append("  Items: none")

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def extract_room_sequence(transcript: str, room_names: set[str]) -> list[str]:
    sequence: list[str] = []
    for raw in transcript.splitlines():
        line = raw.strip()
        if line in room_names:
            if not sequence or sequence[-1] != line:
                sequence.append(line)
    return sequence


def build_playthrough_map_text(game_name: str, exploratory: dict[str, str], world: dict[str, Any]) -> str:
    room_names = {getattr(room, "name", key) for key, room in world.items()}
    visit_counts: dict[str, int] = {name: 0 for name in room_names}
    edge_counts: dict[tuple[str, str], int] = {}
    scenario_sequences: dict[str, list[str]] = {}

    for scenario, transcript in exploratory.items():
        seq = extract_room_sequence(transcript, room_names)
        scenario_sequences[scenario] = seq
        for room in seq:
            visit_counts[room] = visit_counts.get(room, 0) + 1
        for i in range(len(seq) - 1):
            edge = (seq[i], seq[i + 1])
            edge_counts[edge] = edge_counts.get(edge, 0) + 1

    lines = [
        f"{game_name} Playthrough Map",
        "(derived from exploratory run transcripts)",
        "",
        "Scenario room sequences:",
    ]
    for scenario, seq in scenario_sequences.items():
        seq_text = " -> ".join(seq) if seq else "(no recognized rooms)"
        lines.append(f"- {scenario}: {seq_text}")

    lines.extend(["", "Observed room visit counts:"])
    for room in sorted(visit_counts):
        lines.append(f"- {room}: {visit_counts[room]}")

    lines.extend(["", "Observed transitions:"])
    if edge_counts:
        for (src, dst), count in sorted(edge_counts.items(), key=lambda item: (-item[1], item[0][0], item[0][1])):
            lines.append(f"- {src} -> {dst} (seen {count}x)")
    else:
        lines.append("- none")

    unseen = [room for room, count in sorted(visit_counts.items()) if count == 0]
    lines.extend(["", "Unseen rooms in exploratory runs:"])
    if unseen:
        for room in unseen:
            lines.append(f"- {room}")
    else:
        lines.append("- none")

    return "\n".join(lines).rstrip() + "\n"


def build_intro_text(game_name: str, game_description: str, commit_sha: str, review: dict[str, Any]) -> str:
    strengths = review.get("top_strengths", [])
    strength_lines = "\n".join(f"- {x}" for x in strengths[:3]) if strengths else "- (none reported this run)"
    return (
        f"{game_name} - Introduction\n"
        "\n"
        f"{clean_line(game_description, 800)}\n"
        "\n"
        f"Current analyzed commit: {commit_sha[:12]}\n"
        f"Latest overall score (1-5): {review.get('overall_score', 0.0)}\n"
        "\n"
        "Current highlights:\n"
        f"{strength_lines}\n"
    )


def build_rules_text(profile: GameProfile, world: dict[str, Any], smoke_output: str) -> str:
    lines = [
        f"{profile.game_name} - Current Rules",
        "",
        "Primary player actions:",
        *[f"- {action}" for action in profile.allowed_actions],
        "",
        "Rule hints from source:",
    ]

    found_lock = False
    for room_key, room in world.items():
        locks = getattr(room, "locks", {})
        if not locks:
            continue
        found_lock = True
        room_name = getattr(room, "name", room_key)
        for direction, item in locks.items():
            lines.append(f"- {room_name} [{room_key}] direction {direction} requires {item}")
    if not found_lock:
        lines.append("- no lock metadata discovered from source")

    lines.extend(["", "Observed mechanics from smoke run:"])
    interesting = re.compile(r"(taken:|you use|you unlock|you open|you discover|you find|you cannot|can't|locked|requires|carry:|inventory|save|load)", re.IGNORECASE)
    highlights = compact_lines([line.strip() for line in smoke_output.splitlines() if interesting.search(line)], 8, 180)
    if highlights:
        lines.extend(f"- {line}" for line in highlights)
    else:
        lines.append("- no notable mechanics extracted from smoke run")

    return "\n".join(lines).rstrip() + "\n"


def build_latest_brief_text(
    game_name: str,
    repo: str,
    commit_sha: str,
    review: dict[str, Any],
    test_results: dict[str, CmdResult],
    snapshot_id: str,
) -> str:
    score = float(review.get("overall_score", 0.0))
    strengths = review.get("top_strengths", [])
    improvements = review.get("top_improvements", [])
    narrative_additions = review.get("narrative_additions", [])
    puzzle_additions = review.get("puzzle_additions", [])

    dim_name = {dim_id: label for dim_id, label in DIMENSIONS}
    score_lines = []
    for item in review.get("dimension_scores", []):
        label = dim_name.get(str(item.get("dimension", "")), str(item.get("dimension", "")))
        score_lines.append(f"- {label}: {item.get('score', 3)}/5 ({clean_line(str(item.get('why', '')), 220)})")

    strength_lines = [f"- {clean_line(str(x), 280)}" for x in strengths[:2]] if strengths else ["- None"]
    improvement_lines = [f"- {clean_line(str(x), 280)}" for x in improvements[:5]] if improvements else ["- None"]
    narrative_lines = [f"- {clean_line(str(x), 320)}" for x in narrative_additions[:5]] if narrative_additions else ["- None"]
    puzzle_lines = [f"- {clean_line(str(x), 320)}" for x in puzzle_additions[:5]] if puzzle_additions else ["- None"]

    lines = [
        f"{game_name} - Latest Playtest Brief",
        f"Repo: {repo}",
        f"Commit: {commit_sha[:12]}",
        f"Snapshot: {snapshot_id}",
        f"Overall score: {score:.2f}/5",
        f"Pytest: {'PASS' if test_results['pytest'].code == 0 else 'FAIL'}",
        f"Smoke: {'PASS' if test_results['smoke'].code == 0 else 'FAIL'}",
        "",
        "Dimension scores:",
        *score_lines,
        "",
        "Environment/location assessment:",
        clean_line(str(review.get("location_assessment", "")), 500),
        "",
        "Quests/challenges assessment:",
        clean_line(str(review.get("quests_challenges_assessment", "")), 500),
        "",
        "Player agency assessment:",
        clean_line(str(review.get("agency_assessment", "")), 500),
        "",
        "Story arc assessment:",
        clean_line(str(review.get("story_arc_assessment", "")), 500),
        "",
        "Top strengths:",
        *strength_lines,
        "Top improvements:",
        *improvement_lines,
        "",
        "Narrative additions suggested:",
        *narrative_lines,
        "Puzzle additions suggested:",
        *puzzle_lines,
    ]

    return "\n".join(lines).rstrip() + "\n"


def build_role_notes_text(title: str, notes: list[str]) -> str:
    lines = [title, ""]
    if notes:
        lines.extend(f"- {clean_line(str(note), 260)}" for note in notes)
    else:
        lines.append("- No notes recorded in this run.")
    return "\n".join(lines).rstrip() + "\n"


def build_story_arc_notes_text(review: dict[str, Any]) -> str:
    lines = [
        "Story Arc Notes",
        "",
        clean_line(str(review.get("story_arc_assessment", "No story-arc assessment recorded.")), 2000),
        "",
        "Narrative additions:",
    ]

    narrative_additions = review.get("narrative_additions", [])
    if isinstance(narrative_additions, list) and narrative_additions:
        lines.extend(f"- {clean_line(str(item), 260)}" for item in narrative_additions[:8])
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def build_transcript_text(title: str, transcript: str) -> str:
    lines = [title, ""]
    body = transcript.strip()
    lines.append(body if body else "(no transcript output recorded in this run)")
    return "\n".join(lines).rstrip() + "\n"


def truncate_for_discord(text: str, limit: int = 1800) -> str:
    clean = text.strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 20].rstrip() + "\n... (truncated)"


def generate_history_docs(
    repo: str,
    repo_dir: Path,
    profile: GameProfile,
    commit_sha: str,
    review: dict[str, Any],
    test_results: dict[str, CmdResult],
    exploratory: dict[str, str],
    world: dict[str, Any] | None = None,
) -> dict[str, str]:
    if world is None:
        world = load_world_from_source(repo_dir)

    history_root = repo_dir / "history_docs"
    current_dir = history_root / "current"
    snapshots_root = history_root / "snapshots"
    current_dir.mkdir(parents=True, exist_ok=True)
    snapshots_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_id = f"{timestamp}_{commit_sha[:12]}"
    snapshot_dir = snapshots_root / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    role_notes = review.get("role_notes", {}) if isinstance(review.get("role_notes"), dict) else {}
    qa_notes = role_notes.get("qa", []) if isinstance(role_notes.get("qa"), list) else []
    narrative_notes = role_notes.get("narrative", []) if isinstance(role_notes.get("narrative"), list) else []
    puzzle_notes = role_notes.get("puzzle", []) if isinstance(role_notes.get("puzzle"), list) else []
    agency_notes = role_notes.get("agency", []) if isinstance(role_notes.get("agency"), list) else []
    publisher_notes = role_notes.get("publisher", []) if isinstance(role_notes.get("publisher"), list) else []

    docs: dict[str, str] = {
        "game_intro.txt": build_intro_text(profile.game_name, profile.short_description, commit_sha, review),
        "current_rules.txt": build_rules_text(profile, world, test_results["smoke"].out),
        "source_map.txt": build_source_map_text(profile.game_name, world),
        "playthrough_map.txt": build_playthrough_map_text(profile.game_name, exploratory, world),
        "story_arc_notes.txt": build_story_arc_notes_text(review),
        "role_notes_qa.txt": build_role_notes_text("Role Notes - QA Bug Hunter", qa_notes),
        "role_notes_narrative.txt": build_role_notes_text("Role Notes - Narrative Designer", narrative_notes),
        "role_notes_puzzle.txt": build_role_notes_text("Role Notes - Puzzle Architect", puzzle_notes),
        "role_notes_agency.txt": build_role_notes_text("Role Notes - Player Agency Advocate", agency_notes),
        "role_notes_publisher.txt": build_role_notes_text("Role Notes - Experienced Game Publisher", publisher_notes),
    }

    for role_key in ROLE_ORDER:
        transcript_key = f"role_{role_key}"
        role_label = ROLE_LABELS[role_key]
        docs[f"transcript_{role_key}.txt"] = build_transcript_text(
            f"Full Transcript - {role_label}",
            exploratory.get(transcript_key, ""),
        )

    docs["latest_playtest_brief.txt"] = build_latest_brief_text(
        profile.game_name,
        repo,
        commit_sha,
        review,
        test_results,
        snapshot_id,
    )

    for name, content in docs.items():
        (current_dir / name).write_text(content, encoding="utf-8")
        (snapshot_dir / name).write_text(content, encoding="utf-8")

    index_path = history_root / "INDEX.txt"
    line = (
        f"{timestamp} commit={commit_sha[:12]} score={review.get('overall_score', 0.0)} "
        f"snapshot={snapshot_id} pytest={test_results['pytest'].code} smoke={test_results['smoke'].code}\n"
    )
    with index_path.open("a", encoding="utf-8") as f:
        f.write(line)

    docs_path = str(current_dir)
    pinned_message = (
        docs["latest_playtest_brief.txt"]
        + "\n"
        + f"Host docs path: {docs_path}\n"
        + f"Snapshot path: {snapshot_dir}\n"
    )
    return {
        "snapshot_id": snapshot_id,
        "docs_path": docs_path,
        "snapshot_path": str(snapshot_dir),
        "latest_brief": docs["latest_playtest_brief.txt"],
        "pinned_message": truncate_for_discord(pinned_message, limit=1850),
    }


def load_text_file(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def clean_line(text: str, limit: int = 160) -> str:
    no_ansi = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)
    out = re.sub(r"\s+", " ", no_ansi).strip()
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


def env_nonnegative_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def resolve_consultant_model_for_tier(primary_model: str, escalation_model: str, tier: int, escalate_after_tier: int) -> str:
    if escalation_model and tier >= max(0, escalate_after_tier):
        return escalation_model
    return primary_model


def validate_turn_command(command: str, parse_command: Any) -> str:
    cleaned = clean_line(command, 120)
    if not cleaned:
        return ""
    action = parse_command(cleaned).action
    if action in {"unknown", "empty", "save", "load", "help"}:
        return ""
    return cleaned


def compact_lines(lines: list[str], limit_items: int, limit_chars: int = 200) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        cleaned = clean_line(raw, limit_chars)
        key = cleaned.lower()
        if not cleaned or key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
        if len(out) >= limit_items:
            break
    return out


def extract_markdown_section(text: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(1).strip()


def build_game_description_text(profile: GameProfile, world: dict[str, Any], limit: int = 900) -> str:
    room_names = [str(getattr(room, "name", key)) for key, room in world.items()]
    lock_lines: list[str] = []
    for room_key, room in world.items():
        room_name = str(getattr(room, "name", room_key))
        locks = getattr(room, "locks", {})
        if not locks:
            continue
        for direction, item in locks.items():
            lock_lines.append(f"{room_name}: {direction} requires {item}")

    room_summary = ", ".join(room_names[:8]) if room_names else "unknown rooms"
    lock_summary = "; ".join(lock_lines[:6]) if lock_lines else "no explicit directional locks"
    text = (
        f"{clean_line(profile.short_description, 700)} "
        f"Known locations in this build: {room_summary}. "
        f"Current gating observed from source: {lock_summary}. "
        "The intended feel is atmospheric, fair, and rewarding for players who experiment with commands and items."
    )
    return clean_line(text, limit)


def build_scenario_context_lines(name: str, transcript: str) -> list[str]:
    lines = [line.strip() for line in transcript.splitlines() if line.strip()]
    if not lines:
        return [f"{name}: no transcript output"]

    key_pattern = re.compile(
        r"(taken:|you use|you unlock|you open|you discover|you find|you cannot|can't|locked|requires|"
        r"inventory|save|load|error|puzzle|hint|hidden|passage|door|gate)",
        re.IGNORECASE,
    )

    selected: list[str] = []
    selected.extend(lines[:4])
    selected.extend(line for line in lines if key_pattern.search(line))
    selected.extend(lines[-4:])
    compact = compact_lines(selected, limit_items=14, limit_chars=220)
    return [f"{name}: {line}" for line in compact]


def build_exploratory_summary_text(exploratory: dict[str, str], scenario_order: list[str], limit: int) -> str:
    all_lines: list[str] = []
    for scenario_name in scenario_order:
        if scenario_name in exploratory:
            all_lines.extend(build_scenario_context_lines(scenario_name, exploratory[scenario_name]))
    summary = "\n".join(f"- {line}" for line in compact_lines(all_lines, limit_items=36, limit_chars=220))
    if not summary:
        summary = "- No exploratory transcript summary available."
    return summary[:limit]


def build_exploratory_excerpt_text(exploratory: dict[str, str], scenario_order: list[str], limit: int) -> str:
    chunks: list[str] = []
    per_scenario = max(220, limit // max(1, len(exploratory)))
    for name in scenario_order:
        text = exploratory.get(name, "")
        if not text:
            continue
        chunks.append(f"## Scenario: {name}\n{text[:per_scenario]}")
    payload = "\n\n".join(chunks)
    if not payload:
        payload = "(no exploratory excerpt available)"
    return payload[:limit]


def compute_context_caps(base_budget: int, compression_tier: int) -> ContextCaps:
    factors = [1.0, 0.72, 0.52, 0.36]
    factor = factors[min(compression_tier, len(factors) - 1)]
    effective = max(3200, int(base_budget * factor))

    weights = {
        "rubric": 0.18,
        "role_guidance": 0.16,
        "game_description": 0.08,
        "rules": 0.17,
        "smoke": 0.11,
        "transcript_summary": 0.18,
        "transcript_excerpt": 0.12,
    }

    values = {key: max(160, int(effective * weight)) for key, weight in weights.items()}
    return ContextCaps(
        rubric=values["rubric"],
        role_guidance=values["role_guidance"],
        game_description=values["game_description"],
        rules=values["rules"],
        smoke=values["smoke"],
        transcript_summary=values["transcript_summary"],
        transcript_excerpt=values["transcript_excerpt"],
    )


def is_token_limit_error(result: CmdResult) -> bool:
    payload = f"{result.out}\n{result.err}".lower()
    return "prompt tokens limit exceeded" in payload or "token limit" in payload or "maximum context" in payload


def summarize_consultant_failure(result: CmdResult, parsed: dict[str, Any]) -> str:
    if is_token_limit_error(result):
        return "provider token/context limit exceeded"
    if parsed:
        return "parsed response lacked required substantive fields"
    combined = f"{result.out}\n{result.err}"
    if "████" in combined:
        return "picoClaw CLI output did not contain parseable JSON"
    return clean_line((result.err or result.out or "no output"), 180)


def sanitize_agent_output(text: str, limit: int = 1200) -> str:
    cleaned = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", text)
    lines: list[str] = []
    for raw in cleaned.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "████" in line:
            continue
        lines.append(line)
    payload = "\n".join(lines)
    return payload[:limit]


def summarize_candidate_pack(pack: dict[str, Any]) -> dict[str, Any]:
    review = pack.get("overall_review", {}) if isinstance(pack, dict) else {}
    overall = str(review.get("overall_thoughts", "")).strip() if isinstance(review, dict) else ""
    return {
        "overall_thoughts_len": len(overall),
        "top_strengths": len(review.get("top_strengths", [])) if isinstance(review, dict) and isinstance(review.get("top_strengths", []), list) else 0,
        "top_improvements": len(review.get("top_improvements", [])) if isinstance(review, dict) and isinstance(review.get("top_improvements", []), list) else 0,
        "narrative_additions": len(review.get("narrative_additions", [])) if isinstance(review, dict) and isinstance(review.get("narrative_additions", []), list) else 0,
        "puzzle_additions": len(review.get("puzzle_additions", [])) if isinstance(review, dict) and isinstance(review.get("puzzle_additions", []), list) else 0,
        "bugs": len(pack.get("bugs", [])) if isinstance(pack.get("bugs", []), list) else 0,
        "features": len(pack.get("features", [])) if isinstance(pack.get("features", []), list) else 0,
    }


def has_meaningful_dimension_why(entry: dict[str, Any]) -> bool:
    why = str(entry.get("why", "")).strip().lower()
    return bool(why and why != "no clear assessment provided.")


def dedupe_feature_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def is_concrete_gameplay_feature(feature: dict[str, Any], gameplay_terms: list[str]) -> bool:
    step_text = " ".join(str(item) for item in feature.get("implementation_steps", []) if isinstance(item, str))
    acceptance_text = " ".join(str(item) for item in feature.get("acceptance_checks", []) if isinstance(item, str))
    text = (
        f"{feature.get('title', '')} "
        f"{feature.get('proposal', '')} "
        f"{feature.get('location_anchor', '')} "
        f"{feature.get('placement_trigger', '')} "
        f"{feature.get('integration_with_existing_loop', '')} "
        f"{step_text} {acceptance_text}"
    ).lower()
    concrete_keywords = [
        "room",
        "location",
        "puzzle",
        "item",
        "inventory",
        "command",
        "interaction",
        "player",
        "world",
        "story",
        "lore",
    ]
    abstract_keywords = [
        "pricing",
        "marketing",
        "revenue",
        "ads",
        "monetization",
        "campaign",
        "store page",
        "wishlist",
    ]
    if any(word in text for word in abstract_keywords):
        return False
    dynamic_terms = [term for term in gameplay_terms if term and len(term) > 2]
    return any(word in text for word in concrete_keywords + dynamic_terms)


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

    def clean_list(values: Any, limit_items: int, limit_chars: int = 220) -> list[str]:
        if not isinstance(values, list):
            return []
        return [clean_line(str(x), limit_chars) for x in values[:limit_items] if clean_line(str(x), limit_chars)]

    role_notes_raw = review.get("role_notes", {})
    if not isinstance(role_notes_raw, dict):
        role_notes_raw = {}
    role_notes = {
        "qa": clean_list(role_notes_raw.get("qa", []), 8, 260),
        "narrative": clean_list(role_notes_raw.get("narrative", []), 8, 260),
        "puzzle": clean_list(role_notes_raw.get("puzzle", []), 8, 260),
        "agency": clean_list(role_notes_raw.get("agency", []), 8, 260),
        "publisher": clean_list(role_notes_raw.get("publisher", []), 8, 260),
    }

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
                "expected_result": clean_line(str(bug.get("expected_result", "")), 600),
                "actual_result": clean_line(str(bug.get("actual_result", "")), 600),
                "severity": clean_line(str(bug.get("severity", "medium")), 16).lower(),
            }
        )
    bugs = bugs[:max_bugs]

    features: list[dict[str, Any]] = []
    for feature in features_raw:
        if not isinstance(feature, dict):
            continue
        concrete_raw = feature.get("concrete_gameplay_change")
        concrete_flag = False
        if isinstance(concrete_raw, bool):
            concrete_flag = concrete_raw
        elif isinstance(concrete_raw, str):
            concrete_flag = concrete_raw.strip().lower() in {"1", "true", "yes", "y"}
        features.append(
            {
                "title": clean_line(str(feature.get("title", "Playtest feature idea")), 120),
                "player_value": clean_line(str(feature.get("player_value", "")), 800),
                "proposal": clean_line(str(feature.get("proposal", "")), 800),
                "location_anchor": clean_line(str(feature.get("location_anchor", "")), 120),
                "placement_trigger": clean_line(str(feature.get("placement_trigger", "")), 240),
                "integration_with_existing_loop": clean_line(str(feature.get("integration_with_existing_loop", "")), 800),
                "implementation_steps": [clean_line(str(x), 260) for x in feature.get("implementation_steps", [])[:10]]
                if isinstance(feature.get("implementation_steps"), list)
                else [],
                "acceptance_checks": [clean_line(str(x), 260) for x in feature.get("acceptance_checks", [])[:10]]
                if isinstance(feature.get("acceptance_checks"), list)
                else [],
                "concrete_gameplay_change": concrete_flag,
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
            "story_arc_assessment": clean_line(str(review.get("story_arc_assessment", "")), 1200),
            "narrative_additions": clean_list(review.get("narrative_additions", []), 6, 260),
            "puzzle_additions": clean_list(review.get("puzzle_additions", []), 6, 260),
            "top_strengths": [clean_line(str(x), 220) for x in review.get("top_strengths", [])[:2]]
            if isinstance(review.get("top_strengths"), list)
            else [],
            "top_improvements": [clean_line(str(x), 220) for x in review.get("top_improvements", [])[:5]]
            if isinstance(review.get("top_improvements"), list)
            else [],
            "role_notes": role_notes,
        },
        "bugs": bugs,
        "features": features,
    }
    return normalized


def consultant_review_has_substance(review: dict[str, Any]) -> bool:
    text_fields = [
        "overall_thoughts",
        "location_assessment",
        "quests_challenges_assessment",
        "agency_assessment",
        "story_arc_assessment",
    ]
    for field in text_fields:
        if str(review.get(field, "")).strip():
            return True

    list_fields = ["top_strengths", "top_improvements", "narrative_additions", "puzzle_additions"]
    for field in list_fields:
        values = review.get(field, [])
        if isinstance(values, list) and any(str(v).strip() and str(v).strip().lower() != "none" for v in values):
            return True

    role_notes = review.get("role_notes", {})
    if isinstance(role_notes, dict):
        for key in ["qa", "narrative", "puzzle", "agency", "publisher"]:
            notes = role_notes.get(key, [])
            if isinstance(notes, list) and any(str(v).strip() for v in notes):
                return True

    dim_scores = review.get("dimension_scores", [])
    if isinstance(dim_scores, list):
        for item in dim_scores:
            if not isinstance(item, dict):
                continue
            why = str(item.get("why", "")).strip()
            if why and why.lower() != "no clear assessment provided.":
                return True

    return False


def build_consultant_session_key(prefix: str, commit_sha: str, attempt_index: int) -> str:
    clean_prefix = prefix.strip() if prefix.strip() else "cli:august-playtest"
    nonce = f"{int(time.time())}-{time.time_ns() % 1_000_000:06d}-{attempt_index}"
    return f"{clean_prefix}:{commit_sha[:12]}:{nonce}"


def maybe_reset_picoclaw_main_session() -> None:
    reset_raw = os.getenv("AUGUST_RESET_PICOCLAW_MAIN_SESSION", "1").strip().lower()
    if reset_raw in {"0", "false", "no", "off"}:
        return

    sessions_dir = Path.home() / ".picoclaw" / "workspace" / "sessions"
    for name in ["agent_main_main.jsonl", "agent_main_main.meta.json"]:
        path = sessions_dir / name
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def run_picoclaw_consultant(
    message: str,
    session_key: str,
    model: str,
    role_workspace: Path | None = None,
    timeout: int = 420,
    reset_main: bool = True,
) -> CmdResult:
    if reset_main:
        maybe_reset_picoclaw_main_session()

    cmd = ["picoclaw", "agent", "--session", session_key]
    if model:
        cmd.extend(["--model", model])
    cmd.extend(["-m", message])

    env = None
    if role_workspace is not None:
        env = dict(os.environ)
        env["PICOCLAW_AGENTS_DEFAULTS_WORKSPACE"] = str(role_workspace)

    return run_cmd(cmd, timeout=timeout, env=env)


def build_role_guidance_text(roles_text: str, role_key: str, cap: int) -> str:
    role_heading = ROLE_HEADINGS[role_key]
    role_body = extract_markdown_section(roles_text, role_heading)
    synthesis = extract_markdown_section(roles_text, "Synthesis Guidance")
    lines = [f"{role_heading}"]
    if role_body:
        lines.append(role_body)
    if synthesis:
        lines.append("Synthesis Guidance")
        lines.append(synthesis)
    payload = "\n\n".join(lines).strip()
    return payload[:cap]


def build_role_prompt(
    role_key: str,
    commit_sha: str,
    test_results: dict[str, CmdResult],
    rubric_text: str,
    role_guidance: str,
    game_description: str,
    rules_text: str,
    smoke_excerpt: str,
    exploratory_summary: str,
    exploratory_excerpt: str,
    role_max_bugs: int,
    role_max_features: int,
) -> str:
    role_label = ROLE_LABELS[role_key]
    ambition_rule = (
        "- Ambition: help create the greatest text-based adventure game ever."
        if role_key in {"narrative", "puzzle", "agency", "publisher"}
        else ""
    )
    publisher_rule = (
        "- As publisher role, include feature suggestions only when they are concrete gameplay/content changes.\n"
        "- For every feature include `concrete_gameplay_change` boolean. Use true only for concrete in-game changes."
        if role_key == "publisher"
        else "- Set `concrete_gameplay_change` to true only when the feature is a concrete in-game gameplay/content change."
    )
    role_feature_rule = ""
    if role_key == "puzzle":
        role_feature_rule = (
            "- Puzzle role feature proposals must be original puzzle designs with exact placement and integration details.\n"
            "- For each puzzle feature, include where it is placed, clue chain, dependencies, and how it extends the existing key/lamp/coin/tablet loop."
        )
    elif role_key == "narrative":
        role_feature_rule = (
            "- Narrative role feature proposals must be anchored to specific locations and moments in this build.\n"
            "- For each narrative feature, specify where it appears, when it triggers, and exact content additions (not generic hints)."
        )

    return f"""
You are August acting only as: {role_label}.

Follow rubric anchors and role guidance exactly.

RUBRIC EXCERPT:
{rubric_text}

ROLE GUIDANCE:
{role_guidance}

Game description:
{game_description}

Game rules and actions:
{rules_text}

Test context:
- Commit: {commit_sha}
- Pytest exit: {test_results['pytest'].code}
- Smoke exit: {test_results['smoke'].code}
- Smoke excerpt:
{smoke_excerpt}

Game output summary:
{exploratory_summary}

Game output excerpt:
{exploratory_excerpt}

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
    "story_arc_assessment":"string",
    "narrative_additions":["string"],
    "puzzle_additions":["string"],
    "top_strengths":["string"],
    "top_improvements":["string"],
    "role_notes": {{
      "qa":["string"],
      "narrative":["string"],
      "puzzle":["string"],
      "agency":["string"],
      "publisher":["string"]
    }}
  }},
  "bugs": [{{"title":"string","summary":"string","repro_steps":["string"],"expected_result":"string","actual_result":"string","severity":"low|medium|high"}}],
  "features": [{{
    "title":"string",
    "player_value":"string",
    "proposal":"string",
    "location_anchor":"string",
    "placement_trigger":"string",
    "integration_with_existing_loop":"string",
    "implementation_steps":["string"],
    "acceptance_checks":["string"],
    "concrete_gameplay_change":true
  }}]
}}

Rules:
- You are only this role: {role_label}.
- Max {role_max_bugs} bugs.
- Max {role_max_features} features.
- Base scores on rubric anchors, do not invent a custom scale.
- Keep positive feedback brief (1-2 short bullets).
- Put most detail into actionable improvements/additions.
- Keep bug/feature recommendations specific enough to become clear GitHub issues.
- Every bug must include reproducible `repro_steps`, plus clear `expected_result` and `actual_result`.
- Every feature must include concrete `location_anchor`, `placement_trigger`, `integration_with_existing_loop`, `implementation_steps`, and `acceptance_checks`.
{ambition_rule}
{role_feature_rule}
{publisher_rule}
""".strip()


def role_pack_is_meaningful(pack: dict[str, Any]) -> bool:
    review = pack.get("overall_review", {}) if isinstance(pack, dict) else {}
    if isinstance(review, dict) and consultant_review_has_substance(review):
        return True
    bugs = pack.get("bugs", []) if isinstance(pack, dict) else []
    features = pack.get("features", []) if isinstance(pack, dict) else []
    return bool(isinstance(bugs, list) and bugs) or bool(isinstance(features, list) and features)


def choose_first_text(role_packs: dict[str, dict[str, Any]], field_name: str) -> str:
    for role in ROLE_FIELD_PRIORITY[field_name]:
        review = role_packs.get(role, {}).get("overall_review", {})
        if not isinstance(review, dict):
            continue
        value = str(review.get(field_name, "")).strip()
        if value:
            return value
    return ""


def merge_dimension_scores(role_packs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for dim_id, _ in DIMENSIONS:
        chosen: dict[str, Any] | None = None
        fallback: dict[str, Any] | None = None
        for role in DIMENSION_ROLE_PRIORITY.get(dim_id, ROLE_ORDER):
            review = role_packs.get(role, {}).get("overall_review", {})
            if not isinstance(review, dict):
                continue
            dim_scores = review.get("dimension_scores", [])
            if not isinstance(dim_scores, list):
                continue
            for item in dim_scores:
                if not isinstance(item, dict):
                    continue
                if str(item.get("dimension", "")) != dim_id:
                    continue
                if fallback is None:
                    fallback = item
                if has_meaningful_dimension_why(item):
                    chosen = item
                    break
            if chosen is not None:
                break
        source = chosen or fallback or {"dimension": dim_id, "score": 3, "why": "No clear assessment provided."}
        score = source.get("score", 3)
        try:
            score_int = int(score)
        except (TypeError, ValueError):
            score_int = 3
        score_int = max(1, min(5, score_int))
        merged.append({"dimension": dim_id, "score": score_int, "why": clean_line(str(source.get("why", "")), 240)})
    return merged


def merge_list_field(
    role_packs: dict[str, dict[str, Any]],
    field_name: str,
    role_priority: list[str],
    limit_items: int,
) -> list[str]:
    collected: list[str] = []
    seen: set[str] = set()
    for role in role_priority:
        review = role_packs.get(role, {}).get("overall_review", {})
        if not isinstance(review, dict):
            continue
        values = review.get(field_name, [])
        if not isinstance(values, list):
            continue
        for value in values:
            text = clean_line(str(value), 220)
            if not text:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            collected.append(text)
            if len(collected) >= limit_items:
                return collected
    return collected


def merge_role_notes(role_packs: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {key: [] for key in ROLE_ORDER}
    for role in ROLE_ORDER:
        review = role_packs.get(role, {}).get("overall_review", {})
        if not isinstance(review, dict):
            continue
        role_notes = review.get("role_notes", {})
        if not isinstance(role_notes, dict):
            continue
        notes = role_notes.get(role, [])
        if not isinstance(notes, list):
            continue
        merged[role] = compact_lines([str(note) for note in notes], limit_items=8, limit_chars=260)
    return merged


def merge_role_consultant_packs(
    role_packs: dict[str, dict[str, Any]],
    max_bugs: int,
) -> dict[str, Any]:
    scores = merge_dimension_scores(role_packs)
    average = sum(item["score"] for item in scores) / len(scores)

    review = {
        "overall_thoughts": choose_first_text(role_packs, "overall_thoughts"),
        "dimension_scores": scores,
        "overall_score": round(average, 2),
        "location_assessment": choose_first_text(role_packs, "location_assessment"),
        "quests_challenges_assessment": choose_first_text(role_packs, "quests_challenges_assessment"),
        "agency_assessment": choose_first_text(role_packs, "agency_assessment"),
        "story_arc_assessment": choose_first_text(role_packs, "story_arc_assessment"),
        "narrative_additions": merge_list_field(role_packs, "narrative_additions", ["narrative", "publisher", "qa"], 6),
        "puzzle_additions": merge_list_field(role_packs, "puzzle_additions", ["puzzle", "publisher", "qa"], 6),
        "top_strengths": merge_list_field(role_packs, "top_strengths", ["publisher", "narrative", "puzzle", "agency", "qa"], 2),
        "top_improvements": merge_list_field(role_packs, "top_improvements", ["publisher", "puzzle", "narrative", "agency", "qa"], 5),
        "role_notes": merge_role_notes(role_packs),
    }

    bug_priority = ["qa", "puzzle", "agency", "narrative", "publisher"]
    feature_priority = ["publisher", "puzzle", "narrative", "agency", "qa"]

    bugs: list[dict[str, Any]] = []
    seen_bugs: set[str] = set()
    for role in bug_priority:
        for bug in role_packs.get(role, {}).get("bugs", []):
            if not isinstance(bug, dict):
                continue
            title_key = dedupe_feature_title(str(bug.get("title", "")))
            if not title_key or title_key in seen_bugs:
                continue
            seen_bugs.add(title_key)
            bugs.append(bug)
            if len(bugs) >= max_bugs:
                break
        if len(bugs) >= max_bugs:
            break

    # Keep merged pack focused on cross-role review and bug rollup.
    # Feature issues are opened per-role from raw role packs.
    return {"overall_review": review, "bugs": bugs, "features": []}


def ask_august_consultant(
    commit_sha: str,
    test_results: dict[str, CmdResult],
    exploratory: dict[str, str],
    profile: GameProfile,
    world: dict[str, Any],
    rubric_text: str,
    roles_text: str,
    max_bugs: int,
    max_features_per_role: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str], ConsultantDiagnostics]:
    model_override = os.getenv("AUGUST_PICOCLAW_MODEL", "").strip()
    escalation_model = os.getenv("AUGUST_PICOCLAW_ESCALATION_MODEL", "").strip()
    escalate_after_tier = env_nonnegative_int("AUGUST_PICOCLAW_ESCALATE_AFTER_TIER", 2)
    session_prefix = os.getenv("AUGUST_PICOCLAW_SESSION_PREFIX", "cli:august-playtest")
    context_budget = env_positive_int("AUGUST_CONTEXT_CHAR_BUDGET", 14000)

    scenario_order = [f"role_{role}" for role in ROLE_ORDER if f"role_{role}" in exploratory]
    if not scenario_order:
        scenario_order = sorted(exploratory.keys())
    game_description_raw = build_game_description_text(profile, world, limit=1200)
    rules_raw = build_rules_text(profile, world, test_results["smoke"].out)
    exploratory_summary_raw = build_exploratory_summary_text(exploratory, scenario_order, limit=6000)

    role_max_bugs_map = {
        "qa": max_bugs,
        "narrative": min(1, max_bugs),
        "puzzle": min(2, max_bugs),
        "agency": min(1, max_bugs),
        "publisher": min(1, max_bugs),
    }
    role_max_features_map = {
        "qa": max_features_per_role,
        "narrative": max_features_per_role,
        "puzzle": max_features_per_role,
        "agency": max_features_per_role,
        "publisher": max_features_per_role,
    }

    role_packs: dict[str, dict[str, Any]] = {}
    runner_notes: list[str] = []
    role_success: dict[str, bool] = {role: False for role in ROLE_ORDER}
    attempt_records: list[dict[str, Any]] = []

    for role_key in ROLE_ORDER:
        role_pack = normalize_suggestions({}, max_bugs, max_features_per_role)
        role_succeeded = False
        role_workspace = resolve_role_workspace(role_key)
        if role_workspace is None:
            runner_notes.append(f"role={role_key} workspace missing under {role_workspaces_root()}")

        for tier in range(4):
            caps = compute_context_caps(context_budget, tier)
            role_guidance = build_role_guidance_text(roles_text, role_key, caps.role_guidance)
            prompt = build_role_prompt(
                role_key=role_key,
                commit_sha=commit_sha,
                test_results=test_results,
                rubric_text=rubric_text[: caps.rubric],
                role_guidance=role_guidance,
                game_description=game_description_raw[: caps.game_description],
                rules_text=rules_raw[: caps.rules],
                smoke_excerpt=(test_results["smoke"].out + "\n" + test_results["smoke"].err)[: caps.smoke],
                exploratory_summary=exploratory_summary_raw[: caps.transcript_summary],
                exploratory_excerpt=build_exploratory_excerpt_text(exploratory, scenario_order, caps.transcript_excerpt),
                role_max_bugs=role_max_bugs_map[role_key],
                role_max_features=role_max_features_map[role_key],
            )

            model_for_tier = resolve_consultant_model_for_tier(
                primary_model=model_override,
                escalation_model=escalation_model,
                tier=tier,
                escalate_after_tier=escalate_after_tier,
            )
            session_key = build_consultant_session_key(session_prefix, f"{commit_sha[:12]}-{role_key}", tier + 1)
            result = run_picoclaw_consultant(
                prompt,
                session_key,
                model_for_tier,
                role_workspace=role_workspace,
            )
            text = "\n".join(part for part in [result.out, result.err] if part)
            parsed = parse_json_object(text)
            candidate = normalize_suggestions(parsed, max_bugs, max_features_per_role)
            meaningful = role_pack_is_meaningful(candidate)

            parsed_keys = sorted(parsed.keys())[:10] if isinstance(parsed, dict) else []
            reason = summarize_consultant_failure(result, parsed)
            attempt_records.append(
                {
                    "role": role_key,
                    "tier": tier,
                    "session_key": session_key,
                    "model": model_for_tier or "default",
                    "workspace": str(role_workspace) if role_workspace is not None else "",
                    "rc": result.code,
                    "token_limited": is_token_limit_error(result),
                    "prompt_chars": len(prompt),
                    "parsed_keys": parsed_keys,
                    "meaningful": meaningful,
                    "reason": reason,
                    "candidate_summary": summarize_candidate_pack(candidate),
                    "stdout_excerpt": sanitize_agent_output(result.out, 1200),
                    "stderr_excerpt": sanitize_agent_output(result.err, 1200),
                }
            )

            if meaningful:
                role_pack = candidate
                role_succeeded = True
                break

            token_limited = is_token_limit_error(result)
            runner_notes.append(
                f"role={role_key} tier={tier} non-meaningful rc={result.code} token_limited={token_limited} reason={reason}"
            )

        if not role_succeeded:
            runner_notes.append(f"role={role_key} exhausted compression tiers; using empty fallback output")
        role_success[role_key] = role_succeeded
        role_packs[role_key] = role_pack

    substantive_roles = sum(1 for ok in role_success.values() if ok)

    merged = merge_role_consultant_packs(
        role_packs,
        max_bugs=max_bugs,
    )
    diagnostics = ConsultantDiagnostics(
        role_success=role_success,
        substantive_roles=substantive_roles,
        attempt_records=attempt_records,
    )
    return merged, role_packs, runner_notes, diagnostics


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


def discord_request(token: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json",
        "User-Agent": "august-playtest-bot",
    }
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url=f"https://discord.com/api/v10{path}", method=method, data=data, headers=headers)
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body) if body else {}


def get_discord_dm_channel(token: str, owner_id: str) -> str:
    data = discord_request(token, "POST", "/users/@me/channels", {"recipient_id": owner_id})
    channel_id = data.get("id")
    return channel_id if isinstance(channel_id, str) else ""


def find_discord_channel_by_name(token: str, channel_name: str) -> str:
    target = channel_name.strip().lstrip("#").lower()
    if not target:
        return ""

    guilds_data = discord_request(token, "GET", "/users/@me/guilds")
    if not isinstance(guilds_data, list):
        return ""

    for guild in guilds_data:
        if not isinstance(guild, dict):
            continue
        guild_id = guild.get("id")
        if not isinstance(guild_id, str):
            continue
        channels_data = discord_request(token, "GET", f"/guilds/{guild_id}/channels")
        if not isinstance(channels_data, list):
            continue
        for ch in channels_data:
            if not isinstance(ch, dict):
                continue
            ch_name = str(ch.get("name", "")).strip().lower()
            ch_type = ch.get("type")
            ch_id = ch.get("id")
            if ch_name == target and isinstance(ch_id, str) and ch_type in {0, 5}:  # text / announcement
                return ch_id
    return ""


def resolve_report_channel(token: str, owner_id: str) -> str:
    explicit_id = os.getenv("AUGUST_DISCORD_REPORT_CHANNEL_ID", "").strip()
    if explicit_id:
        return explicit_id

    explicit_name = os.getenv("AUGUST_DISCORD_REPORT_CHANNEL_NAME", "").strip()
    if explicit_name:
        found = find_discord_channel_by_name(token, explicit_name)
        if found:
            return found

    if owner_id:
        return get_discord_dm_channel(token, owner_id)
    return ""


def send_discord_message(token: str, channel_id: str, content: str) -> str:
    payload = truncate_for_discord(content, limit=1900)
    data = discord_request(token, "POST", f"/channels/{channel_id}/messages", {"content": payload})
    message_id = data.get("id")
    return message_id if isinstance(message_id, str) else ""


def edit_discord_message(token: str, channel_id: str, message_id: str, content: str) -> str:
    payload = truncate_for_discord(content, limit=1900)
    data = discord_request(
        token,
        "PATCH",
        f"/channels/{channel_id}/messages/{message_id}",
        {"content": payload},
    )
    edited_id = data.get("id")
    return edited_id if isinstance(edited_id, str) else ""


def split_for_discord_messages(text: str, limit: int = 1840) -> list[str]:
    clean = text.strip()
    if not clean:
        return []

    lines = clean.splitlines()
    parts: list[str] = []
    current_lines: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current_lines, current_len
        if current_lines:
            parts.append("\n".join(current_lines).strip())
            current_lines = []
            current_len = 0

    for raw_line in lines:
        line = raw_line
        if not line:
            candidate_len = current_len + (1 if current_lines else 0)
            if candidate_len > limit:
                flush()
            else:
                if current_lines:
                    current_lines.append("")
                    current_len = candidate_len
            continue

        while len(line) > limit:
            flush()
            parts.append(line[: limit - 1] + "…")
            line = line[limit - 1 :]

        extra = len(line) + (1 if current_lines else 0)
        if current_lines and current_len + extra > limit:
            flush()

        if current_lines:
            current_lines.append(line)
            current_len += 1 + len(line)
        else:
            current_lines = [line]
            current_len = len(line)

    flush()
    return parts


def list_pinned_discord_messages(token: str, channel_id: str) -> list[dict[str, Any]]:
    data = discord_request(token, "GET", f"/channels/{channel_id}/pins")
    return data if isinstance(data, list) else []


def is_august_brief_message(message: dict[str, Any]) -> bool:
    content = str(message.get("content", ""))
    first_line = content.splitlines()[0].strip() if content.strip() else ""
    if not re.match(r"^.+ - Latest Playtest Brief$", first_line):
        return False
    author = message.get("author")
    return isinstance(author, dict) and bool(author.get("bot"))


def pin_discord_message(token: str, channel_id: str, message_id: str) -> None:
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "august-playtest-bot",
    }
    req = Request(
        url=f"https://discord.com/api/v10/channels/{channel_id}/pins/{message_id}",
        method="PUT",
        data=b"",
        headers=headers,
    )
    with urlopen(req, timeout=30):
        pass


def unpin_discord_message(token: str, channel_id: str, message_id: str) -> None:
    headers = {
        "Authorization": f"Bot {token}",
        "User-Agent": "august-playtest-bot",
    }
    req = Request(
        url=f"https://discord.com/api/v10/channels/{channel_id}/pins/{message_id}",
        method="DELETE",
        headers=headers,
    )
    with urlopen(req, timeout=30):
        pass


def send_discord_dm(token: str, owner_id: str, content: str) -> tuple[str, str]:
    channel_id = get_discord_dm_channel(token, owner_id)
    if not channel_id:
        return "", ""
    message_id = send_discord_message(token, channel_id, content)
    return channel_id, message_id


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


def write_debug_bundle(
    commit_sha: str,
    mode: str,
    run_status: str,
    role_success: dict[str, bool],
    runner_notes: list[str],
    attempt_records: list[dict[str, Any]],
    review_pack: dict[str, Any],
    test_results: dict[str, CmdResult],
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{timestamp}_{commit_sha[:12]}"
    debug_root = Path.home() / ".picoclaw" / "workspace" / "august-playtest" / "debug"
    bundle_dir = debug_root / run_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    substantive_roles = sum(1 for ok in role_success.values() if ok)
    manifest = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "commit": commit_sha,
        "mode": mode,
        "run_status": run_status,
        "substantive_roles": substantive_roles,
        "role_success": role_success,
        "pytest_exit": test_results["pytest"].code,
        "smoke_exit": test_results["smoke"].code,
    }
    (bundle_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    with (bundle_dir / "role_attempts.jsonl").open("w", encoding="utf-8") as f:
        for record in attempt_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    review = review_pack.get("overall_review", {}) if isinstance(review_pack, dict) else {}
    review_dump = {
        "overall_review": review,
        "bugs_count": len(review_pack.get("bugs", [])) if isinstance(review_pack.get("bugs", []), list) else 0,
        "features_count": len(review_pack.get("features", [])) if isinstance(review_pack.get("features", []), list) else 0,
    }
    (bundle_dir / "review_output.json").write_text(json.dumps(review_dump, indent=2) + "\n", encoding="utf-8")

    summary_lines = [
        "August Playtest Debug Bundle",
        f"Run ID: {run_id}",
        f"Commit: {commit_sha[:12]}",
        f"Status: {run_status}",
        f"Mode: {mode}",
        f"Substantive roles: {substantive_roles}/{len(role_success)}",
        "Role matrix:",
        *[f"- {role}: {'ok' if role_success.get(role, False) else 'fail'}" for role in ROLE_ORDER],
        "Runner notes:",
    ]
    if runner_notes:
        summary_lines.extend(f"- {clean_line(note, 320)}" for note in runner_notes[:40])
    else:
        summary_lines.append("- none")
    (bundle_dir / "summary.txt").write_text("\n".join(summary_lines).rstrip() + "\n", encoding="utf-8")

    keep_runs = env_positive_int("AUGUST_DEBUG_KEEP_RUNS", 50)
    entries = sorted([p for p in debug_root.iterdir() if p.is_dir()])
    if len(entries) > keep_runs:
        for old in entries[: len(entries) - keep_runs]:
            run_cmd(["rm", "-rf", str(old)])

    return str(bundle_dir)


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
    narrative_additions = "\n".join(f"- {x}" for x in review.get("narrative_additions", [])) or "- None"
    puzzle_additions = "\n".join(f"- {x}" for x in review.get("puzzle_additions", [])) or "- None"

    body = (
        f"Automated August qualitative review for commit `{commit_sha}`.\n\n"
        f"Overall score (average): **{review['overall_score']}/5**\n\n"
        f"Overall thoughts:\n{review.get('overall_thoughts', '')}\n\n"
        f"### Rubric Scores\n{score_table}\n\n"
        f"### Environment and Locations\n{review.get('location_assessment', '')}\n\n"
        f"### Quests and Challenges\n{review.get('quests_challenges_assessment', '')}\n\n"
        f"### Player Agency\n{review.get('agency_assessment', '')}\n\n"
        f"### Story Arc\n{review.get('story_arc_assessment', '')}\n\n"
        f"### Top Strengths\n{strengths}\n\n"
        f"### Top Improvements\n{improvements}\n\n"
        f"### Narrative Additions Suggested\n{narrative_additions}\n\n"
        f"### Puzzle Additions Suggested\n{puzzle_additions}\n\n"
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
    expected_result = str(bug.get("expected_result", "")).strip() or "(not provided)"
    actual_result = str(bug.get("actual_result", "")).strip() or "(not provided)"
    body = (
        f"Automated August bug report for commit `{commit_sha}`.\n\n"
        f"Summary:\n{bug.get('summary', '')}\n\n"
        f"Severity: {bug.get('severity', 'medium')}\n\n"
        f"Repro steps:\n{steps_text}\n\n"
        f"Expected result:\n{expected_result}\n\n"
        f"Actual result:\n{actual_result}\n\n"
        "Context:\n"
        f"- pytest exit: {test_results['pytest'].code}\n"
        f"- smoke exit: {test_results['smoke'].code}\n"
    )
    title = f"[August][Bug] {bug.get('title', 'Playtest bug')}"
    return GitHubIssue(title=title, body=body, labels=["august-feedback", "bug", "playtest", "triage-needed"])


def build_feature_issue(
    commit_sha: str,
    role_key: str,
    feature: dict[str, Any],
    test_results: dict[str, CmdResult],
) -> GitHubIssue:
    role_label = ROLE_LABELS.get(role_key, role_key)
    location_anchor = str(feature.get("location_anchor", "")).strip() or "(not provided)"
    placement_trigger = str(feature.get("placement_trigger", "")).strip() or "(not provided)"
    integration = str(feature.get("integration_with_existing_loop", "")).strip() or "(not provided)"
    implementation_steps = feature.get("implementation_steps", [])
    acceptance_checks = feature.get("acceptance_checks", [])

    steps_text = (
        "\n".join(f"- {clean_line(str(step), 260)}" for step in implementation_steps if str(step).strip())
        if isinstance(implementation_steps, list)
        else ""
    )
    checks_text = (
        "\n".join(f"- {clean_line(str(check), 260)}" for check in acceptance_checks if str(check).strip())
        if isinstance(acceptance_checks, list)
        else ""
    )

    body = (
        f"Automated August feature suggestion for commit `{commit_sha}`.\n\n"
        f"Proposed by role: {role_label}\n\n"
        f"Player value:\n{feature.get('player_value', '')}\n\n"
        f"Proposal:\n{feature.get('proposal', '')}\n\n"
        f"Location anchor:\n{location_anchor}\n\n"
        f"Placement trigger:\n{placement_trigger}\n\n"
        f"Integration with existing loop:\n{integration}\n\n"
        "Implementation steps:\n"
        f"{steps_text or '- (not provided)'}\n\n"
        "Acceptance checks:\n"
        f"{checks_text or '- (not provided)'}\n\n"
        "Context:\n"
        f"- pytest exit: {test_results['pytest'].code}\n"
        f"- smoke exit: {test_results['smoke'].code}\n"
    )
    title = f"[August][Feature][{role_key}] {feature.get('title', 'Playtest feature idea')}"
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
        score_lines.append(f"- {label}: {item.get('score', 3)}/5 - {clean_line(str(item.get('why', '')), 220)}")

    strengths = review.get("top_strengths", [])
    improvements = review.get("top_improvements", [])
    narrative_additions = review.get("narrative_additions", [])
    puzzle_additions = review.get("puzzle_additions", [])

    strength_lines = [f"- {clean_line(str(x), 280)}" for x in strengths[:2]] if strengths else ["- None"]
    improvement_lines = [f"- {clean_line(str(x), 280)}" for x in improvements[:5]] if improvements else ["- None"]
    narrative_lines = [f"- {clean_line(str(x), 320)}" for x in narrative_additions[:3]] if narrative_additions else ["- None"]
    puzzle_lines = [f"- {clean_line(str(x), 320)}" for x in puzzle_additions[:3]] if puzzle_additions else ["- None"]

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
        f"- Environment and locations: {clean_line(str(review.get('location_assessment', '')), 320)}",
        f"- Quests and challenges: {clean_line(str(review.get('quests_challenges_assessment', '')), 320)}",
        f"- Player agency: {clean_line(str(review.get('agency_assessment', '')), 320)}",
        f"- Story arc: {clean_line(str(review.get('story_arc_assessment', '')), 320)}",
        "Top strengths:",
        *strength_lines,
        "Top improvements:",
        *improvement_lines,
        "Creative additions (narrative):",
        *narrative_lines,
        "Creative additions (puzzle):",
        *puzzle_lines,
        f"Issues opened: {len(opened_urls)}",
        f"Issues skipped (duplicate): {skipped_count}",
    ]

    if opened_urls:
        lines.append("Issue links:")
        lines.extend(f"- {url}" for url in opened_urls[:7])
    return "\n".join(lines)


def main() -> int:
    repo_slug_env = os.getenv("AUGUST_GITHUB_REPO", "").strip()
    repo_url_env = os.getenv("AUGUST_REPO_URL", "").strip()
    default_repo_dir = Path(__file__).resolve().parents[2]
    repo_dir_raw = os.getenv("AUGUST_REPO_DIR", "").strip()
    repo_dir = Path(repo_dir_raw).expanduser() if repo_dir_raw else default_repo_dir
    state_path = Path.home() / ".picoclaw" / "workspace" / "august-playtest" / "state.json"
    force = os.getenv("AUGUST_FORCE", "0") == "1"
    max_bugs = env_positive_int("AUGUST_MAX_BUGS", DEFAULT_MAX_BUGS)
    max_features_per_role = env_positive_int("AUGUST_MAX_FEATURES_PER_ROLE", env_positive_int("AUGUST_MAX_FEATURES", 3))
    min_substantive_roles = env_positive_int("AUGUST_MIN_SUBSTANTIVE_ROLES", 2)

    if not repo_url_env and repo_slug_env:
        repo_url_env = f"https://github.com/{repo_slug_env}.git"

    state = load_state(state_path)

    try:
        ensure_repo(repo_dir, repo_url_env)
        sha = sync_repo(repo_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"sync failed: {exc}")
        return 1

    repo = detect_repo_slug(repo_dir, repo_slug_env)
    if not repo:
        print("sync failed: unable to determine GitHub repo slug; set AUGUST_GITHUB_REPO")
        return 1

    try:
        profile = load_game_profile(repo_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"profile load failed: {exc}")
        return 1

    world = load_world_from_source(repo_dir)

    if not force and state.get("last_tested_sha") == sha:
        print("no-new-commit")
        return 0

    try:
        python_bin = ensure_venv(repo_dir)
        test_results = run_tests(repo_dir, python_bin)
        exploratory = run_exploratory_scenarios(repo_dir, profile)
    except Exception as exc:  # noqa: BLE001
        print(f"test setup failed: {exc}")
        return 1

    rubric_text = load_text_file(repo_dir / "docs" / "playtest_rubric.md")
    roles_text = load_roles_text(repo_dir)
    review_pack, role_packs, runner_notes, consultant_diag = ask_august_consultant(
        sha,
        test_results,
        exploratory,
        profile,
        world,
        rubric_text,
        roles_text,
        max_bugs,
        max_features_per_role,
    )

    role_matrix = ", ".join(
        f"{role}={'ok' if consultant_diag.role_success.get(role, False) else 'fail'}" for role in ROLE_ORDER
    )
    runner_notes.append(
        f"role-matrix: {role_matrix} (substantive={consultant_diag.substantive_roles}/{len(ROLE_ORDER)})"
    )

    consultant_pipeline_ok = consultant_diag.substantive_roles >= min_substantive_roles
    review_meaningful = consultant_review_has_substance(review_pack["overall_review"])
    if not review_meaningful:
        runner_notes.append("Consultant output was minimal; qualitative review issue suppressed.")
    if not consultant_pipeline_ok:
        runner_notes.append(
            "Consultant pipeline failed quality gate: "
            f"{consultant_diag.substantive_roles}/{len(ROLE_ORDER)} substantive roles, "
            f"minimum required is {min_substantive_roles}."
        )

    gameplay_terms = compact_lines(
        profile.gameplay_terms
        + [profile.game_name]
        + profile.allowed_actions
        + re.findall(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}", profile.short_description.lower()),
        80,
        30,
    )

    gh = GitHubClient(repo)
    open_titles = list_open_issue_titles(gh)
    opened_urls: list[str] = []
    skipped_count = 0
    github_errors: list[str] = []

    if gh.mode != "none" and consultant_pipeline_ok:
        issues: list[GitHubIssue] = []
        for bug in review_pack["bugs"]:
            issues.append(build_bug_issue(sha, bug, test_results))
        for role_key in ROLE_ORDER:
            role_features = role_packs.get(role_key, {}).get("features", [])
            if not isinstance(role_features, list):
                continue
            for feature in role_features[:max_features_per_role]:
                if not isinstance(feature, dict):
                    continue
                if role_key == "publisher":
                    if not bool(feature.get("concrete_gameplay_change")):
                        continue
                    if not is_concrete_gameplay_feature(feature, gameplay_terms):
                        continue
                issues.append(build_feature_issue(sha, role_key, feature, test_results))
        if review_meaningful:
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
    elif gh.mode != "none" and not consultant_pipeline_ok:
        runner_notes.append("Skipped GitHub issue creation due to consultant pipeline failure.")

    docs_meta = generate_history_docs(
        repo=repo,
        repo_dir=repo_dir,
        profile=profile,
        commit_sha=sha,
        review=review_pack["overall_review"],
        test_results=test_results,
        exploratory=exploratory,
        world=world,
    )

    prev_score = None
    if isinstance(state.get("last_overall_score"), (int, float)):
        prev_score = float(state["last_overall_score"])

    mode = gh.mode if not github_errors else f"{gh.mode}-with-errors"
    failure_classes: list[str] = []
    if not consultant_pipeline_ok:
        failure_classes.append("consultant_pipeline_failure")
    if github_errors:
        failure_classes.append("publishing_failure")

    run_status = "ok" if not failure_classes else "+".join(failure_classes)

    debug_bundle_path = write_debug_bundle(
        commit_sha=sha,
        mode=mode,
        run_status=run_status,
        role_success=consultant_diag.role_success,
        runner_notes=runner_notes,
        attempt_records=consultant_diag.attempt_records,
        review_pack=review_pack,
        test_results=test_results,
    )

    summary = format_summary(repo, sha, mode, test_results, review_pack["overall_review"], opened_urls, skipped_count, prev_score)
    summary += (
        "\nHistory docs:\n"
        f"- current: {docs_meta['docs_path']}\n"
        f"- snapshot: {docs_meta['snapshot_path']}\n"
        f"- snapshot_id: {docs_meta['snapshot_id']}\n"
        f"- debug_bundle: {debug_bundle_path}"
    )
    if github_errors:
        summary += "\nGitHub errors:\n- " + "\n- ".join(clean_line(x, 240) for x in github_errors[:5])
    if runner_notes:
        summary += "\nRunner notes:\n- " + "\n- ".join(clean_line(x, 240) for x in runner_notes[:20])
    print(summary)

    state.update(
        {
            "last_tested_sha": sha,
            "last_run_utc": datetime.now(UTC).isoformat(),
            "last_pytest_exit": test_results["pytest"].code,
            "last_smoke_exit": test_results["smoke"].code,
            "last_overall_score": float(review_pack["overall_review"].get("overall_score", 0.0)),
            "last_snapshot_id": docs_meta["snapshot_id"],
            "last_docs_path": docs_meta["docs_path"],
            "last_snapshot_path": docs_meta["snapshot_path"],
            "last_debug_bundle_path": debug_bundle_path,
            "last_run_status": run_status,
            "last_substantive_roles": consultant_diag.substantive_roles,
            "last_role_matrix": consultant_diag.role_success,
        }
    )

    discord_token, owner_id = load_picoclaw_discord()
    discord_errors: list[str] = []
    if discord_token:
        report_channel_id = ""
        try:
            report_channel_id = resolve_report_channel(discord_token, owner_id)
            if report_channel_id:
                chunks = split_for_discord_messages(summary, limit=1840)
                summary_message_ids: list[str] = []
                for idx, chunk in enumerate(chunks, start=1):
                    payload = chunk
                    if len(chunks) > 1:
                        payload = f"[Part {idx}/{len(chunks)}]\n{chunk}"
                    message_id = send_discord_message(discord_token, report_channel_id, payload)
                    if message_id:
                        summary_message_ids.append(message_id)

                if summary_message_ids:
                    state["last_summary_message_id"] = summary_message_ids[-1]
                    state["last_summary_message_ids"] = summary_message_ids
                    state["last_report_channel_id"] = report_channel_id
        except Exception as exc:  # noqa: BLE001
            discord_errors.append(f"summary send failed: {exc}")

        if run_status != "ok" and report_channel_id:
            short_status = (
                f"August playtest pipeline degraded for `{repo}` at `{sha[:12]}`. "
                f"Substantive roles: {consultant_diag.substantive_roles}/{len(ROLE_ORDER)} "
                f"(minimum {min_substantive_roles}). "
                f"Debug bundle: {debug_bundle_path}"
            )
            try:
                send_discord_message(discord_token, report_channel_id, short_status)
            except Exception as exc:  # noqa: BLE001
                discord_errors.append(f"failure status send failed: {exc}")

        pin_channel_id = os.getenv("AUGUST_DISCORD_PIN_CHANNEL_ID", "").strip() or report_channel_id
        if pin_channel_id:
            try:
                prev_pin_id = str(state.get("last_pinned_message_id", ""))
                prev_pin_channel = str(state.get("last_pinned_channel_id", ""))

                pin_message_id = ""
                if prev_pin_id and prev_pin_channel == pin_channel_id:
                    pin_message_id = edit_discord_message(
                        discord_token,
                        pin_channel_id,
                        prev_pin_id,
                        docs_meta["pinned_message"],
                    )
                if not pin_message_id:
                    pin_message_id = send_discord_message(discord_token, pin_channel_id, docs_meta["pinned_message"])

                if pin_message_id:
                    if prev_pin_id and prev_pin_channel and prev_pin_channel != pin_channel_id:
                        try:
                            unpin_discord_message(discord_token, prev_pin_channel, prev_pin_id)
                        except Exception:  # noqa: BLE001
                            pass
                    elif prev_pin_id and prev_pin_channel == pin_channel_id and prev_pin_id != pin_message_id:
                        try:
                            unpin_discord_message(discord_token, pin_channel_id, prev_pin_id)
                        except Exception:  # noqa: BLE001
                            pass

                    pin_discord_message(discord_token, pin_channel_id, pin_message_id)

                    try:
                        for pinned_msg in list_pinned_discord_messages(discord_token, pin_channel_id):
                            other_id = str(pinned_msg.get("id", ""))
                            if not other_id or other_id == pin_message_id:
                                continue
                            if is_august_brief_message(pinned_msg):
                                try:
                                    unpin_discord_message(discord_token, pin_channel_id, other_id)
                                except Exception:  # noqa: BLE001
                                    pass
                    except Exception:  # noqa: BLE001
                        pass

                    state["last_pinned_message_id"] = pin_message_id
                    state["last_pinned_channel_id"] = pin_channel_id
            except Exception as exc:  # noqa: BLE001
                discord_errors.append(f"pin update failed: {exc}")

    if discord_errors:
        runner_notes.extend(discord_errors[:5])
        if "publishing_failure" not in failure_classes:
            failure_classes.append("publishing_failure")
        run_status = "+".join(failure_classes)
        try:
            (Path(debug_bundle_path) / "discord_errors.txt").write_text(
                "\n".join(discord_errors).rstrip() + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    state["last_run_status"] = run_status

    save_state(state_path, state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
