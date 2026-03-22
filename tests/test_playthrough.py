from game.playtest import run_playthrough


def test_smoke_playthrough_reaches_treasury() -> None:
    commands = [
        "take lamp",
        "north",
        "take key",
        "east",
        "use lamp",
        "take coin",
        "north",
        "take idol",
        "quit",
    ]

    result = run_playthrough(commands, seed=7)
    text = "\n".join(result.transcript)

    assert "Treasury" in text
    assert "Taken: idol." in text
    assert result.completed
