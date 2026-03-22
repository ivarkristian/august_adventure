from __future__ import annotations

import argparse

from game.engine import GameEngine


def main() -> None:
    parser = argparse.ArgumentParser(description="August Adventure")
    parser.add_argument("--seed", type=int, default=7, help="Deterministic flavor seed")
    args = parser.parse_args()

    engine = GameEngine(seed=args.seed)
    print("Welcome to August Adventure.")
    print("Type 'help' for commands.")
    print(engine.look())

    while True:
        try:
            text = input("\n> ")
        except EOFError:
            print("\nFarewell, adventurer.")
            break

        output, should_quit = engine.step(text)
        print(output)
        if should_quit:
            break


if __name__ == "__main__":
    main()
