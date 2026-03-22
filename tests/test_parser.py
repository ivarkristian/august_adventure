from game.parser import parse_command


def test_direction_aliases() -> None:
    cmd = parse_command("n")
    assert cmd.action == "go"
    assert cmd.target == "north"


def test_inventory_alias() -> None:
    cmd = parse_command("i")
    assert cmd.action == "inventory"


def test_unknown_command() -> None:
    cmd = parse_command("xyzzy")
    assert cmd.action == "unknown"
