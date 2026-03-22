from pathlib import Path

from game.engine import GameEngine


def test_locked_exit_requires_key() -> None:
    engine = GameEngine(seed=1)

    engine.step("north")
    engine.step("east")
    output, _ = engine.step("north")
    assert "locked" in output.lower()


def test_inventory_take_and_drop() -> None:
    engine = GameEngine(seed=1)
    out_take, _ = engine.step("take lamp")
    assert "Taken: lamp." == out_take

    out_drop, _ = engine.step("drop lamp")
    assert "Dropped: lamp." == out_drop


def test_save_load_roundtrip(tmp_path: Path) -> None:
    save = tmp_path / "save.json"

    e1 = GameEngine(seed=42)
    e1.step("take lamp")
    e1.step("north")
    e1.step("take key")
    out_save, _ = e1.step(f"save {save}")
    assert str(save) in out_save

    e2 = GameEngine(seed=0)
    out_load, _ = e2.step(f"load {save}")
    assert str(save) in out_load

    inv, _ = e2.step("inventory")
    assert "lamp" in inv and "key" in inv
