from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

from game.parser import Command, parse_command
from game.world import Room, build_world


HELP_TEXT = """Commands:
  look|l
  go <north|south|east|west> (or type direction directly)
  take <item>
  drop <item>
  give <item>
  use <item>
  examine <target>
  listen
  inventory|i
  save [path]
  load [path]
  help
  quit
"""


@dataclass
class GameState:
    location: str = "trailhead"
    inventory: list[str] = field(default_factory=list)
    flags: dict[str, bool | list[str]] = field(default_factory=dict)


class GameEngine:
    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        self.world: dict[str, Room] = build_world()
        self.state = GameState()

    def step(self, text: str) -> tuple[str, bool]:
        cmd = parse_command(text)

        if cmd.action == "empty":
            return "You hesitate.", False
        if cmd.action == "help":
            return HELP_TEXT.rstrip(), False
        if cmd.action == "look":
            return self.look(), False
        if cmd.action == "inventory":
            return self.inventory(), False
        if cmd.action == "go":
            return self.go(cmd), False
        if cmd.action == "take":
            return self.take(cmd), False
        if cmd.action == "drop":
            return self.drop(cmd), False
        if cmd.action == "use":
            return self.use(cmd), False
        if cmd.action == "save":
            return self.save(cmd.target), False
        if cmd.action == "load":
            return self.load(cmd.target), False
        if cmd.action == "quit":
            return "Farewell, adventurer.", True
        if cmd.action == "listen":
            return self.listen(), False
        if cmd.action == "examine":
            return self.examine(cmd.target), False
        if cmd.action == "give":
            return self.give(cmd.target), False

        return "I do not understand that command.", False

    def current_room(self) -> Room:
        return self.world[self.state.location]

    def look(self) -> str:
        room = self.current_room()
        lines = [room.name]

        if self.state.location == "treasury":
            if self.state.flags.get("idol_placed"):
                lines.append(
                    "A hidden vault glitters in low amber light. "
                    "An ancient idol rests upon the pedestal, its features worn smooth by ages, "
                    "and a hidden alcove gleams with forgotten verses. "
                    "The only open passage leads south."
                )
            elif "idol" in room.items:
                lines.append(
                    "A hidden vault glitters in low amber light. "
                    "A carved pedestal with a coin-sized slot rests near the center, "
                    "and an ancient idol watches from the shadows, eyes that seem to follow you. "
                    "The only open passage leads south."
                )
            else:
                lines.append(
                    "A hidden vault glitters in low amber light. "
                    "A carved pedestal with a coin-sized slot rests near the center. "
                    "The only open passage leads south."
                )
            if not self.state.flags.get("coin_offered"):
                lines.append("The pedestal slot looks exactly coin-sized.")
            if room.items and not self.state.flags.get("idol_placed"):
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
            elif self.state.flags.get("idol_placed") and room.items:
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
        elif self.state.location == "cavern":
            lines.append(
                "A black-stone cavern swallows the light, each drip echoing like a distant clock. "
                "A bronze gate seals the northern tunnel while the western passage returns to the foyer."
            )
            if self.state.flags.get("cavern_north_unlocked"):
                lines.append("The bronze gate to the north stands open.")
            else:
                lines.append("A locked bronze gate blocks the northern tunnel.")
            if room.items:
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
            else:
                lines.append("You see nothing useful.")
        elif self.state.location == "hidden_passage":
            lines.append(room.description)
            if room.items:
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
            lines.append("Exits: " + ", ".join(sorted(room.exits.keys())) + ".")
            return "\n".join(lines)
        elif self.state.location == "ancient_alcove":
            lines.append(room.description)
            if room.items:
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
            lines.append("Exits: " + ", ".join(sorted(room.exits.keys())) + ".")
            return "\n".join(lines)
        else:
            lines.append(room.description)
            if self.state.location == "trailhead" and self.state.flags.get("trailhead_listened"):
                lines.append("A faint sound of trickling water echoes from the east.")
            if room.items:
                lines.append("You see: " + ", ".join(sorted(room.items)) + ".")
            else:
                lines.append("You see nothing useful.")

        lines.append("Exits: " + ", ".join(sorted(room.exits.keys())) + ".")

        flavor = [
            "A faint draft brushes past you.",
            "Water echoes somewhere deeper ahead.",
            "Dust motes drift in the dim light.",
        ]
        lines.append(self.rng.choice(flavor))
        return "\n".join(lines)

    def inventory(self) -> str:
        if not self.state.inventory:
            return "Your inventory is empty."
        return "You carry: " + ", ".join(sorted(self.state.inventory)) + "."

    def go(self, cmd: Command) -> str:
        direction = cmd.target.lower()
        if not direction:
            return "Go where?"

        room = self.current_room()
        if direction not in room.exits:
            return "You cannot go that way."

        required = room.locks.get(direction)
        if required:
            lock_flag = f"unlock:{self.state.location}:{direction}"
            if not self.state.flags.get(lock_flag):
                if self.state.location == "cavern" and direction == "north":
                    return "The bronze gate is locked. Try using the key here."
                return f"The way {direction} is locked. You need the {required}."

        if self.state.location == "cavern" and direction == "east":
            if not self.state.flags.get("cavern_east_revealed"):
                return "The eastern wall appears solid. Perhaps more light might reveal something hidden."

        self.state.location = room.exits[direction]
        return self.look()

    def take(self, cmd: Command) -> str:
        item = cmd.target.lower()
        if not item:
            return "Take what?"
        room = self.current_room()
        if item not in room.items:
            if item == "idol" and self.state.location != "treasury":
                return "You recall seeing a similar stone figure deeper within the ruins."
            if item == "tablet" and self.state.location == "treasury":
                return "The tablet is hidden within a compartment. Perhaps something could reveal it."
            if item == "journal" and self.state.location == "hidden_passage":
                return "The journal lies open on a shelf. Perhaps you should examine it."
            return f"There is no {item} here."
        room.items.remove(item)
        self.state.inventory.append(item)
        return f"Taken: {item}."

    def drop(self, cmd: Command) -> str:
        item = cmd.target.lower()
        if not item:
            return "Drop what?"
        if item not in self.state.inventory:
            return f"You are not carrying {item}."
        self.state.inventory.remove(item)
        self.current_room().items.append(item)
        return f"Dropped: {item}."

    def use(self, cmd: Command) -> str:
        item = cmd.target.lower()
        if not item:
            return "Use what?"
        if item not in self.state.inventory:
            if item == "lamp":
                return "You need a lamp to do that. Perhaps one lies nearby in the ruins."
            if item == "key":
                return "You need a key to do that. Perhaps it lies within the ruins."
            if item == "coin":
                return "You do not have a coin. Perhaps something waits to be discovered."
            return f"You do not have {item}. Check your inventory with 'i'."

        if item == "lamp" and self.state.location == "cavern":
            if not self.state.flags.get("coin_revealed"):
                self.state.flags["coin_revealed"] = True
                if "coin" not in self.current_room().items:
                    self.current_room().items.append("coin")
                return "You raise the lamp. A hidden coin glints near a rock."
            if not self.state.flags.get("cavern_water_seen"):
                self.state.flags["cavern_water_seen"] = True
                return (
                    "You sweep the lamp across the cavern walls. Water traces down from above, "
                    "thin threads catching the light before vanishing into the darkness. "
                    "Somewhere above, something holds the weight of ages\u2014and the memory of water."
                )
            if "coin" in self.state.inventory and not self.state.flags.get("cavern_east_revealed"):
                self.state.flags["cavern_east_revealed"] = True
                return (
                    "You raise the lamp again, sweeping it across the eastern wall. "
                    "The light catches something unexpected\u2014a section of stone that "
                    "looks different from the rest. As you approach, ancient mechanisms grind "
                    "to life, and a hidden wall slides aside, revealing a passage to the east "
                    "leading deeper into the waterlogged depths. "
                    "'The water echoes remember,' the inscription reads."
                )

        if item == "lamp" and self.state.location == "foyer" and not self.state.flags.get("foyer_inscriptions_seen"):
            self.state.flags["foyer_inscriptions_seen"] = True
            return (
                "You raise the lamp. The faded glyphs on the walls sharpen into focus: "
                "'The river's memory flows deep. Where water echoes, truth sleeps.'"
            )

        if item == "lamp" and self.state.location == "treasury":
            if not self.state.flags.get("treasury_lamp_revealed"):
                self.state.flags["treasury_lamp_revealed"] = True
                if "coin" not in self.current_room().items and "coin" not in self.state.inventory:
                    self.current_room().items.append("coin")
                return (
                    "You raise the lamp, sweeping it across the treasury. "
                    "In the far corner, a glint catches your eye—a coin, "
                    "half-hidden in the dust near the pedestal base."
                )
            return (
                "You raise the lamp again. The treasury glows with warm amber light, "
                "illuminating the pedestal and the coin you discovered."
            )

        if item == "lamp" and self.state.location == "ancient_alcove":
            return self._handle_stone_puzzle("lamp")

        if item == "key" and self.state.location == "cavern":
            if self.state.flags.get("cavern_north_unlocked"):
                return "The bronze gate is already unlocked."
            self.state.flags["cavern_north_unlocked"] = True
            self.state.flags["unlock:cavern:north"] = True
            return "You work the key into an old lock. The bronze gate clicks open."

        if item == "key" and self.state.location == "foyer":
            if self.state.flags.get("glyph_key_used"):
                return "You've already unlocked the glyph's secret."
            if not self.state.flags.get("foyer_inscriptions_seen"):
                return "The glyphs are too faded to reveal anything to a key. Try using the lamp first."
            self.state.flags["glyph_key_used"] = True
            return (
                "You press the key against a glyph. Mechanisms grind deep within the walls. "
                "A hidden compartment springs open beside the eastern passage, "
                "revealing a fragment of ancient text: "
                "'The worthy place what watches upon the resting place. "
                "The alcove remembers what the vault forgets.' "
                "The compartment then seals itself, its secret now yours."
            )

        if item == "coin" and self.state.location == "treasury":
            if self.state.flags.get("coin_offered"):
                return "The pedestal has already accepted your coin."
            self.state.flags["coin_offered"] = True
            if "tablet" not in self.current_room().items:
                self.current_room().items.append("tablet")
            return (
                "You slide the coin into the pedestal slot. A hidden compartment clicks open, "
                "revealing a weathered tablet. Strange symbols cover its surface, hinting at a purpose "
                "beyond these ruins. You may now take the tablet."
            )

        if item == "idol" and self.state.location == "treasury":
            if self.state.flags.get("idol_placed"):
                return "The idol already rests upon the pedestal."
            self.state.flags["idol_placed"] = True
            if "idol" in self.current_room().items:
                self.current_room().items.remove("idol")
            return (
                "You set the idol upon the pedestal. Ancient mechanisms grind to life. "
                "A hidden alcove shimmers into existence, inscribed with forgotten verses: "
                "'The worthy who seek shall find. The worthy who give shall receive.'"
            )

        if item == "tablet":
            if self.state.location == "ancient_alcove":
                if self.state.flags.get("stone_puzzle_solved"):
                    return (
                        "The true tablet rests in your hands, warm with ancient wisdom. "
                        "Its surface bears the complete truth: "
                        "'The river's tear opens the way. The stone's memory guides. "
                        "The idol's gaze seals the truth. "
                        "The treasure was never gold or gem—the builders' wisdom, "
                        "passed through those who seek. You have found it.'"
                    )
                if not self.state.flags.get("alcove_tablet_read"):
                    self.state.flags["alcove_tablet_read"] = True
                    return (
                        "You speak the tablet's verses aloud in the alcove. "
                        "The words echo against the stone walls. The altar trembles, "
                        "and new inscriptions blaze into view: "
                        "'The treasure was never gold or gem—the builders' wisdom, "
                        "passed through those who seek. You have found it. "
                        "The true tablet is your understanding.'"
                    )
                return (
                    "You read the tablet's verses again. "
                    "The altar glows faintly: 'The treasure was never gold or gem—the builders' wisdom, "
                    "passed through those who seek.'"
                )
            return (
                "You study the weathered tablet. The strange symbols resolve into words: "
                "'The river remembers what the stone forgets. Seek the echoes where the water weeps. "
                "There, beneath the weight of ages, the true tablet awaits.'"
            )

        if item == "journal" and self.state.location == "hidden_passage":
            return (
                "You open the journal. Most pages are water-damaged, but one entry remains readable: "
                "'The builders left three symbols as their legacy—water, stone, and sight. "
                "Together they reveal the path to what was hidden. "
                "The river's tear opens the way. The stone's memory guides. "
                "The idol's gaze seals the truth.'"
            )

        if self.state.location == "ancient_alcove" and item in {"coin", "idol", "lamp"}:
            return self._handle_stone_puzzle(item)

        return f"You try using the {item}, but nothing happens."

    def _handle_stone_puzzle(self, item: str) -> str:
        if item == "lamp":
            if self.state.flags.get("stone_puzzle_solved"):
                return "The stone lock already bears your offering. The true tablet is yours."
            if self.state.flags.get("stone_puzzle_sequence"):
                if item not in self.state.inventory:
                    return f"You do not have the {item}."
                raw_sequence = self.state.flags.get("stone_puzzle_sequence")
                if isinstance(raw_sequence, list):
                    sequence: list[str] = raw_sequence
                else:
                    sequence = []
                sequence.append(item)
                self.state.flags["stone_puzzle_sequence"] = sequence

                expected_sequence = ["coin", "idol", "lamp"]

                if sequence == expected_sequence:
                    self.state.flags["stone_puzzle_solved"] = True
                    self.state.flags.pop("stone_puzzle_sequence", None)
                    if "true_tablet" not in self.current_room().items:
                        self.current_room().items.append("true_tablet")
                    return (
                        "You place the coin on the altar. Ancient grooves light with a faint blue glow. "
                        "You add the idol. The light intensifies, tracing patterns across the stone. "
                        "Finally, you place the lamp. The three elements align—water, stone, and sight. "
                        "The altar shudders. A hidden compartment opens, revealing a radiant true tablet. "
                        "Its surface bears the complete truth: "
                        "'The river's tear opens the way. The stone's memory guides. "
                        "The idol's gaze seals the truth.'"
                    )

                if len(sequence) < len(expected_sequence):
                    remaining = len(expected_sequence) - len(sequence)
                    if remaining == 2:
                        return (
                            f"You place the {item} on the altar. Faint grooves illuminate, "
                            "but nothing further happens. Two more offerings are needed "
                            "in the correct order to unlock the stone lock."
                        )
                    else:
                        return (
                            f"You place the {item} on the altar. The grooves glow brighter, "
                            "but then fade. One more offering in the correct order is needed."
                        )

                self.state.flags.pop("stone_puzzle_sequence", None)
                return (
                    f"You place the {item} on the altar. The grooves flash once and go dark. "
                    "The stone lock does not respond. You sense the order was incorrect."
                )
            if not self.state.flags.get("alcove_lamp_revealed"):
                self.state.flags["alcove_lamp_revealed"] = True
                return (
                    "You raise the lamp, bringing its amber glow to the ancient alcove. "
                    "The light reveals faint inscriptions along the altar's edges, "
                    "hidden in the shadows: 'The river's tear opens the heart. "
                    "The stone's memory holds the path.'"
                )
            return (
                "You raise the lamp again. The inscriptions on the altar glow softly "
                "in the amber light: 'The river's tear opens the heart. "
                "The stone's memory holds the path.'"
            )

        if self.state.flags.get("stone_puzzle_solved"):
            return "The stone lock already bears your offering. The true tablet is yours."

        if item not in self.state.inventory:
            return f"You do not have the {item}."

        raw_sequence = self.state.flags.get("stone_puzzle_sequence")
        if isinstance(raw_sequence, list):
            sequence: list[str] = raw_sequence
        else:
            sequence = []
        sequence.append(item)
        self.state.flags["stone_puzzle_sequence"] = sequence

        expected_sequence = ["coin", "idol", "lamp"]

        if sequence == expected_sequence:
            self.state.flags["stone_puzzle_solved"] = True
            self.state.flags.pop("stone_puzzle_sequence", None)
            if "true_tablet" not in self.current_room().items:
                self.current_room().items.append("true_tablet")
            return (
                "You place the coin on the altar. Ancient grooves light with a faint blue glow. "
                "You add the idol. The light intensifies, tracing patterns across the stone. "
                "Finally, you place the lamp. The three elements align—water, stone, and sight. "
                "The altar shudders. A hidden compartment opens, revealing a radiant true tablet. "
                "Its surface bears the complete truth: "
                "'The river's tear opens the way. The stone's memory guides. "
                "The idol's gaze seals the truth.'"
            )

        if len(sequence) < len(expected_sequence):
            remaining = len(expected_sequence) - len(sequence)
            if remaining == 2:
                return (
                    f"You place the {item} on the altar. Faint grooves illuminate, "
                    "but nothing further happens. Two more offerings are needed "
                    "in the correct order to unlock the stone lock."
                )
            else:
                return (
                    f"You place the {item} on the altar. The grooves glow brighter, "
                    "but then fade. One more offering in the correct order is needed."
                )

        self.state.flags.pop("stone_puzzle_sequence", None)
        return (
            f"You place the {item} on the altar. The grooves flash once and go dark. "
            "The stone lock does not respond. You sense the order was incorrect."
        )

    def listen(self) -> str:
        if self.state.location == "trailhead":
            if not self.state.flags.get("trailhead_listened"):
                self.state.flags["trailhead_listened"] = True
                if "east" not in self.current_room().exits:
                    self.current_room().exits["east"] = "hidden_passage"
                return (
                    "You stand still and listen. The wind fades. "
                    "Then—water. A faint echo rises from the east, "
                    "where no path should be. You hear it clearly now: "
                    "a secret passage, hidden by the sound of trickling water."
                )
            return "The water echoes from the east. The hidden passage awaits."

        if self.state.location == "foyer":
            return "The foyer is silent save for the faint drip of water somewhere beyond the walls."

        if self.state.location == "cavern":
            return "Water drips steadily from above, each drop echoing into the darkness."

        if self.state.location == "treasury":
            return "The treasury is utterly still. Ancient air holds its breath."

        if self.state.location == "ancient_alcove":
            return "Water drips steadily into the altar basin, a patient rhythm marking time beyond memory."

        return "You hear nothing unusual."

    def examine(self, target: str) -> str:
        if not target:
            return "Examine what?"

        if target in {"glyph", "glyphs", "wall", "walls", "inscription", "inscriptions"}:
            if self.state.location == "foyer":
                if self.state.flags.get("foyer_inscriptions_seen"):
                    return (
                        "The glyphs shimmer faintly in the lamplight: "
                        "water-drop symbols arranged in a repeating pattern. "
                        "They seem to encode something—a sequence of three symbols "
                        "repeated near the eastern wall. Perhaps the answer lies in the tablet."
                    )
                return "The glyphs are too faded to read without proper light."

        if target in {"pedestal", "altar"}:
            if self.state.location == "treasury":
                if self.state.flags.get("idol_placed"):
                    return "The idol rests upon the pedestal, eyes gazing upward. The hidden alcove glows softly."
                return "The carved pedestal has a coin-sized slot and empty arms, as if waiting for an offering."

        if target in {"tablet"}:
            if "tablet" in self.state.inventory:
                return (
                    "You study the weathered tablet. The strange symbols resolve into words: "
                    "'The river remembers what the stone forgets. Seek the echoes where the water weeps. "
                    "There, beneath the weight of ages, the true tablet awaits.'"
                )
            if "tablet" in self.current_room().items:
                return "A weathered tablet lies here, covered in strange symbols."

        if target in {"idol", "figure"}:
            if "idol" in self.state.inventory:
                return "A small stone idol, worn smooth by ages. Its expression is serene but watchful."
            if "idol" in self.current_room().items:
                return "An ancient idol watches from the shadows, its stone eyes seeming to follow you."

        if target in {"journal", "book", "note"}:
            if "journal" in self.current_room().items:
                return (
                    "The journal is filled with cramped handwriting, most faded beyond reading. "
                    "One passage stands out: 'The builders hid their greatest treasure "
                    "where the water weeps and the worthy find rest. Three symbols mark the way: "
                    "the first, the river tear; the second, the stone memory; "
                    "the third, the idol gaze.'"
                )

        if target in {"altar", "stone altar"}:
            if self.state.location == "ancient_alcove":
                return (
                    "The altar bears a carved inscription: "
                    "'The river's tear opens the heart. The stone's memory holds the path. "
                    "Place what watches upon the resting place, and truth shall be revealed.' "
                    "Below, a small basin catches the steady drip of water from above."
                )

        return f"You examine the {target}, but find nothing notable."

    def give(self, item: str) -> str:
        if not item:
            return "Give what?"
        if item not in self.state.inventory:
            return f"You are not carrying {item}. Check your inventory with 'i'."

        if item == "coin" and self.state.location == "treasury":
            return self.use(Command(action="use", target="coin"))

        if item == "idol" and self.state.location == "treasury":
            return self.use(Command(action="use", target="idol"))

        if item == "tablet" and self.state.location == "ancient_alcove":
            return self.use(Command(action="use", target="tablet"))

        if item == "lamp" and self.state.location == "treasury":
            return self.use(Command(action="use", target="lamp"))

        if item == "lamp" and self.state.location == "ancient_alcove":
            return self.use(Command(action="use", target="lamp"))

        if item == "key" and self.state.location == "foyer":
            return self.use(Command(action="use", target="key"))

        return f"You try giving the {item}, but nothing happens."

    def save(self, path_text: str) -> str:
        path = Path(path_text) if path_text else Path("savegame.json")
        data = {
            "seed": self.seed,
            "state": {
                "location": self.state.location,
                "inventory": self.state.inventory,
                "flags": self.state.flags,
            },
            "rooms": {name: room.items for name, room in self.world.items()},
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return f"Saved game to {path}."

    def load(self, path_text: str) -> str:
        path = Path(path_text) if path_text else Path("savegame.json")
        if not path.exists():
            return f"No save file found at {path}."

        data = json.loads(path.read_text(encoding="utf-8"))
        self.seed = int(data.get("seed", 0))
        self.rng = random.Random(self.seed)
        self.world = build_world()

        rooms_data = data.get("rooms", {})
        for name, items in rooms_data.items():
            if name in self.world:
                self.world[name].items = list(items)

        state = data.get("state", {})
        self.state.location = state.get("location", "trailhead")
        self.state.inventory = list(state.get("inventory", []))
        self.state.flags = dict(state.get("flags", {}))
        return f"Loaded game from {path}."
