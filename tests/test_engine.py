from pathlib import Path

from game.engine import GameEngine


def test_locked_exit_requires_key() -> None:
    engine = GameEngine(seed=1)

    engine.step("north")
    engine.step("east")
    output, _ = engine.step("north")
    assert "locked" in output.lower()


def test_cavern_gate_requires_using_key_explicitly() -> None:
    engine = GameEngine(seed=2)

    engine.step("north")
    engine.step("take key")
    engine.step("east")

    still_locked, _ = engine.step("north")
    assert "locked" in still_locked.lower()

    unlocked, _ = engine.step("use key")
    assert "clicks open" in unlocked.lower()

    moved, _ = engine.step("north")
    assert "Treasury" in moved


def test_coin_unlocks_tablet_reward() -> None:
    engine = GameEngine(seed=3)

    engine.step("take lamp")
    engine.step("north")
    engine.step("take key")
    engine.step("east")
    engine.step("use key")
    engine.step("use lamp")
    engine.step("take coin")
    engine.step("north")

    use_coin, _ = engine.step("use coin")
    assert "revealing a tablet" in use_coin.lower()

    take_tablet, _ = engine.step("take tablet")
    assert "Taken: tablet." == take_tablet

    inv, _ = engine.step("inventory")
    assert "coin" not in inv
    assert "tablet" in inv


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
