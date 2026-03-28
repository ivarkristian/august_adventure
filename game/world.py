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
            exits={"west": "foyer", "north": "treasury", "east": "submerged_chamber"},
            items=[],
            locks={"north": "key"},
        ),
        "submerged_chamber": Room(
            name="Submerged Chamber",
            description=(
                "A vast underground chamber filled with still, dark water that reflects no light. "
                "Ancient stone pillars rise from the water, covered in phosphorescent moss that casts "
                "an eerie blue-green glow. In the center, a small island holds a stone plinth with "
                "a final inscription: 'You have followed the water's memory through darkness. "
                "The true treasure was the journey itself—and the wisdom gained along the way.' "
                "The passage back to the cavern lies to the west."
            ),
            exits={"west": "cavern"},
            items=[],
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
        "hidden_passage": Room(
            name="Hidden Passage",
            description=(
                "A narrow passage opens behind a thin veil of water that catches the dim light. "
                "The sound of trickling water fills the air. Ancient stonework gives way to a small alcove "
                "where dust motes dance in the filtered glow. A weathered journal lies open on a stone shelf."
            ),
            exits={"west": "trailhead", "east": "ancient_alcove"},
            items=["journal"],
        ),
        "ancient_alcove": Room(
            name="Ancient Alcove",
            description=(
                "A small chamber carved from living stone, untouched by time. "
                "Water traces down the walls in thin threads, catching faint light. "
                "An altar of dark stone stands at the center, its surface etched with an inscription. "
                "The passage back lies to the west."
            ),
            exits={"west": "hidden_passage"},
            items=["altar"],
        ),
    }
