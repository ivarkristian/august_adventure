from __future__ import annotations

from dataclasses import dataclass

from game.engine import GameEngine


@dataclass
class PlaythroughResult:
    transcript: list[str]
    completed: bool


def run_playthrough(commands: list[str], seed: int = 7) -> PlaythroughResult:
    engine = GameEngine(seed=seed)
    transcript = [engine.look()]

    done = False
    for command in commands:
        transcript.append(f"> {command}")
        output, done = engine.step(command)
        transcript.append(output)
        if done:
            break

    return PlaythroughResult(transcript=transcript, completed=done)
