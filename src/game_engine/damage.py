import math
import random
from dataclasses import dataclass
from src.game_engine.enums import Stat, StatusCondition, Category, stat_stage_multiplier
from src.game_engine.type_effectiveness import get_effectiveness
from src.game_engine.pokemon import BattlePokemon


@dataclass
class DamageResult:
    damage: int
    effectiveness: float
    stab: bool
    crit: bool


def calculate_damage(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    move_power: int,
    move_category: str,
    move_type: str,
    crit: bool = False,
    random_factor: float | None = None,
) -> DamageResult:
    if move_category == Category.PHYSICAL.value:
        atk = attacker.attack
        defense = defender.defense
    else:
        atk = attacker.sp_atk
        defense = defender.sp_def

    if random_factor is None:
        random_factor = random.randint(85, 100) / 100.0

    base = math.floor(math.floor(math.floor(2 * attacker.level / 5 + 2) * move_power * atk / defense) / 50) + 2

    if crit:
        base = math.floor(base * 1.5)

    base = math.floor(base * random_factor)

    stab = move_type in attacker.types
    if stab:
        base = math.floor(base * 1.5)

    effectiveness = get_effectiveness(move_type, defender.types)
    base = math.floor(base * effectiveness)

    if (
        attacker.status == StatusCondition.BURN
        and move_category == Category.PHYSICAL.value
    ):
        base = math.floor(base * 0.5)

    return DamageResult(
        damage=max(0, base),
        effectiveness=effectiveness,
        stab=stab,
        crit=crit,
    )
