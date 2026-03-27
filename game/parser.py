from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    action: str
    target: str = ""
    raw: str = ""


_DIRECTION_ALIASES = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
}


def parse_command(text: str) -> Command:
    raw = text.strip()
    if not raw:
        return Command(action="empty", raw=text)

    tokens = raw.split()
    head = tokens[0].lower()
    second = tokens[1] if len(tokens) > 1 else ""

    if head in _DIRECTION_ALIASES:
        return Command(action="go", target=_DIRECTION_ALIASES[head], raw=text)
    if head in {"north", "south", "east", "west"}:
        return Command(action="go", target=head, raw=text)

    if head in {"go", "move"}:
        return Command(action="go", target=second, raw=text)
    if head in {"look", "l"}:
        return Command(action="look", raw=text)
    if head in {"take", "get", "pick"}:
        return Command(action="take", target=second, raw=text)
    if head in {"drop", "leave"}:
        return Command(action="drop", target=second, raw=text)
    if head in {"use"}:
        return Command(action="use", target=second, raw=text)
    if head in {"inventory", "inv", "i"}:
        return Command(action="inventory", raw=text)
    if head in {"save"}:
        return Command(action="save", target=second, raw=text)
    if head in {"load"}:
        return Command(action="load", target=second, raw=text)
    if head in {"help", "h", "?"}:
        return Command(action="help", raw=text)
    if head in {"quit", "exit"}:
        return Command(action="quit", raw=text)
    if head in {"listen", "hear"}:
        return Command(action="listen", raw=text)
    if head in {"examine", "inspect", "decode"}:
        return Command(action="examine", target=second, raw=text)
    if head in {"give", "place", "put"}:
        return Command(action="give", target=second, raw=text)

    return Command(action="unknown", raw=text)
