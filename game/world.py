from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Room:
    name: str
    description: str
    exits: dict[str, str]
    items: list[str] = field(default_factory=list)
    locks: dict[str, str] = field(default_factory=dict)


def build_world() -> dict[str, Room]:
    return {
        "trailhead": Room(
            name="Trailhead",
            description="You stand before a weathered stone arch. A path leads north.",
            exits={"north": "foyer"},
            items=["lamp"],
        ),
        "foyer": Room(
            name="Foyer",
            description="A cool chamber with mossy walls. Corridors lead east and south.",
            exits={"south": "trailhead", "east": "cavern"},
            items=["key"],
        ),
        "cavern": Room(
            name="Cavern",
            description="A dark cavern. You hear slow drips. Paths lead west and north.",
            exits={"west": "foyer", "north": "treasury"},
            items=[],
            locks={"north": "key"},
        ),
        "treasury": Room(
            name="Treasury",
            description="A hidden vault glitters softly. The only exit is south.",
            exits={"south": "cavern"},
            items=["idol"],
        ),
    }
