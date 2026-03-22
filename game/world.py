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
            description=(
                "You stand beneath a weathered stone arch wrapped in ivy. "
                "Cold air spills from the ruins to the north, carrying the smell of rain and old dust."
            ),
            exits={"north": "foyer"},
            items=["lamp"],
        ),
        "foyer": Room(
            name="Foyer",
            description=(
                "A vaulted antechamber opens around you, its moss-dark walls etched with faded glyphs "
                "that seem to shift in the dim light. Strange inscriptions cover the stonework, "
                "their meaning lost to time. A narrow passage bends east while daylight lingers weakly to the south."
            ),
            exits={"south": "trailhead", "east": "cavern"},
            items=["key"],
        ),
        "cavern": Room(
            name="Cavern",
            description=(
                "A black-stone cavern swallows the light, each drip echoing like a distant clock. "
                "A bronze gate seals the northern tunnel while the western passage returns to the foyer."
            ),
            exits={"west": "foyer", "north": "treasury"},
            items=[],
            locks={"north": "key"},
        ),
        "treasury": Room(
            name="Treasury",
            description=(
                "A hidden vault glitters in low amber light. A carved pedestal with a coin-sized slot "
                "rests near the center, and an ancient idol watches from the shadows. "
                "The only open passage leads south."
            ),
            exits={"south": "cavern"},
            items=["idol"],
        ),
    }
