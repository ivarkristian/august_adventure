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
  use <item>
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
    flags: dict[str, bool] = field(default_factory=dict)


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

        return "I do not understand that command.", False

    def current_room(self) -> Room:
        return self.world[self.state.location]

    def look(self) -> str:
        room = self.current_room()
        lines = [room.name, room.description]

        if self.state.location == "cavern":
            if self.state.flags.get("cavern_north_unlocked"):
                lines.append("The bronze gate to the north stands open.")
            else:
                lines.append("A locked bronze gate blocks the northern tunnel.")

        if self.state.location == "treasury" and not self.state.flags.get("coin_offered"):
            lines.append("The pedestal slot looks exactly coin-sized.")

        if self.state.location == "treasury" and self.state.flags.get("idol_placed"):
            lines.append("The idol rests upon the pedestal, and a hidden alcove gleams with ancient verses.")
        elif room.items:
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

        self.state.location = room.exits[direction]
        return self.look()

    def take(self, cmd: Command) -> str:
        item = cmd.target.lower()
        if not item:
            return "Take what?"
        room = self.current_room()
        if item not in room.items:
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
            return f"You do not have {item}."

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

        if item == "lamp" and self.state.location == "foyer" and not self.state.flags.get("foyer_inscriptions_seen"):
            self.state.flags["foyer_inscriptions_seen"] = True
            return (
                "You raise the lamp. The faded glyphs on the walls sharpen into focus: "
                "'The river's memory flows deep. Where water echoes, truth sleeps.'"
            )

        if item == "key" and self.state.location == "cavern":
            if self.state.flags.get("cavern_north_unlocked"):
                return "The bronze gate is already unlocked."
            self.state.flags["cavern_north_unlocked"] = True
            self.state.flags["unlock:cavern:north"] = True
            return "You work the key into an old lock. The bronze gate clicks open."

        if item == "coin" and self.state.location == "treasury":
            if self.state.flags.get("coin_offered"):
                return "The pedestal has already accepted your coin."
            self.state.flags["coin_offered"] = True
            self.state.inventory.remove("coin")
            if "tablet" not in self.current_room().items:
                self.current_room().items.append("tablet")
            return (
                "You place the coin in the pedestal slot. A hidden compartment slides open, "
                "revealing a weathered tablet. Strange symbols cover its surface, hinting at a purpose "
                "beyond these ruins."
            )

        if item == "idol" and self.state.location == "treasury":
            if self.state.flags.get("idol_placed"):
                return "The idol already rests upon the pedestal."
            self.state.flags["idol_placed"] = True
            self.state.inventory.remove("idol")
            if "idol" in self.current_room().items:
                self.current_room().items.remove("idol")
            return (
                "You set the idol upon the pedestal. Ancient mechanisms grind to life. "
                "A hidden alcove shimmers into existence, inscribed with forgotten verses: "
                "'The worthy who seek shall find. The worthy who give shall receive.'"
            )

        if item == "tablet":
            return (
                "You study the weathered tablet. The strange symbols resolve into words: "
                "'The river remembers what the stone forgets. Seek the echoes where the water weeps. "
                "There, beneath the weight of ages, the true tablet awaits.'"
            )

        return f"You try using the {item}, but nothing happens."

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
