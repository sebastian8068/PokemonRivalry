from src.game_engine.effects import MoveEffect, DamageEffect, StatusEffect, StatChangeEffect, FlinchEffect
from src.game_engine.enums import StatusCondition, Stat


MOVE_EFFECTS: dict[str, list[MoveEffect]] = {
    "Earthquake": [DamageEffect()],

    "Thunderbolt": [
        DamageEffect(),
        StatusEffect(status=StatusCondition.PARALYZE, accuracy=0.10),
    ],

    "Iron Tail": [
        DamageEffect(),
        StatChangeEffect(stat=Stat.DEFENSE, stages=-1, target="opponent", accuracy=0.30),
    ],

    "Headbutt": [
        DamageEffect(),
        FlinchEffect(turns=1, accuracy=0.30),
    ],

    "Ice Beam": [
        DamageEffect(),
        StatusEffect(status=StatusCondition.FREEZE, accuracy=0.10),
    ],

    "Ice Fang": [
        DamageEffect(),
        StatusEffect(status=StatusCondition.FREEZE, accuracy=0.10),
    ],

    "Ice Punch": [
        DamageEffect(),
        StatusEffect(status=StatusCondition.FREEZE, accuracy=0.10),
    ],

    "Nasty Plot": [
        StatChangeEffect(stat=Stat.SP_ATK, stages=+2, target="self"),
    ],
}


def get_move_effects(move_name: str) -> list[MoveEffect] | None:
    return MOVE_EFFECTS.get(move_name)
