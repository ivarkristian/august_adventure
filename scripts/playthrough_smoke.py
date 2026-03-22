from __future__ import annotations

import sys

from game.playtest import run_playthrough


COMMANDS = [
    "take lamp",
    "north",
    "take key",
    "east",
    "use key",
    "use lamp",
    "take coin",
    "north",
    "use coin",
    "take tablet",
    "take idol",
    "inventory",
    "quit",
]

REQUIRED_SNIPPETS = [
    "Taken: lamp.",
    "Taken: key.",
    "clicks open",
    "hidden coin",
    "Taken: coin.",
    "revealing a tablet",
    "Taken: tablet.",
    "Treasury",
    "Taken: idol.",
    "Farewell, adventurer.",
]


def main() -> int:
    result = run_playthrough(COMMANDS, seed=7)
    text = "\n".join(result.transcript)
    print(text)

    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    if missing:
        print("\nSMOKE PLAYTHROUGH FAILED")
        for item in missing:
            print(f"- Missing snippet: {item}")
        return 1

    print("\nSMOKE PLAYTHROUGH PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
