from enum import Enum, auto
import math


class StatusCondition(Enum):
    BURN = auto()
    PARALYZE = auto()
    SLEEP = auto()
    FREEZE = auto()
    POISON = auto()


class Category(Enum):
    PHYSICAL = "Physical"
    SPECIAL = "Special"
    STATUS = "Status"


class Stat(Enum):
    HP = "hp"
    ATTACK = "attack"
    DEFENSE = "defense"
    SP_ATK = "sp_atk"
    SP_DEF = "sp_def"
    SPEED = "speed"
    ACCURACY = "accuracy"
    EVASION = "evasion"


_STAT_STAGE_TABLE = {
    -6: 2 / 8,
    -5: 2 / 7,
    -4: 2 / 6,
    -3: 2 / 5,
    -2: 2 / 4,
    -1: 2 / 3,
     0: 2 / 2,
    +1: 3 / 2,
    +2: 4 / 2,
    +3: 5 / 2,
    +4: 6 / 2,
    +5: 7 / 2,
    +6: 8 / 2,
}


def stat_stage_multiplier(stage: int) -> float:
    if stage < -6:
        stage = -6
    if stage > 6:
        stage = 6
    return _STAT_STAGE_TABLE[stage]
