from src.game_engine.effects import MoveEffect, DamageEffect


MOVE_EFFECTS: dict[str, list[MoveEffect]] = {
    "Earthquake": [DamageEffect()],
}


def get_move_effects(move_name: str) -> list[MoveEffect] | None:
    return MOVE_EFFECTS.get(move_name)
