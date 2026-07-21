import math
import random
from src.game_engine.enums import StatusCondition, Stat, stat_stage_multiplier, Category
from src.game_engine.stat_calculator import calculate_total_hp, calculate_total_stat, parse_nature


class BattlePokemon:
    def __init__(
        self,
        pokemon_id: int,
        name: str,
        base_stats: dict[str, int],
        evs: dict[str, int],
        nature_str: str | None,
        types: list[str],
        level: int = 100,
    ):
        self.pokemon_id = pokemon_id
        self.name = name
        self.level = level
        self.types = types

        nature_mults = parse_nature(nature_str)

        self.max_hp = calculate_total_hp(base_stats["hp"], evs["hp"], level)
        self.current_hp = self.max_hp

        self._total_stats: dict[str, int] = {}
        for s in ("attack", "defense", "sp_atk", "sp_def", "speed"):
            self._total_stats[s] = calculate_total_stat(
                base_stats[s], evs[s], nature_mults[s], level
            )

        self.status: StatusCondition | None = None
        self._badly_poisoned: bool = False
        self._poison_tick: int = 0
        self._sleep_turns: int = 0
        self._flinch_turns: int = 0

        self._stat_stages: dict[Stat, int] = {s: 0 for s in Stat}

    # -- Public stat accessors --

    def total_for(self, stat: Stat) -> int:
        raw = self._total_stats[stat.value]
        stage = self._stat_stages[stat]
        return max(1, math.floor(raw * stat_stage_multiplier(stage)))

    @property
    def attack(self) -> int:
        return self.total_for(Stat.ATTACK)

    @property
    def defense(self) -> int:
        return self.total_for(Stat.DEFENSE)

    @property
    def sp_atk(self) -> int:
        return self.total_for(Stat.SP_ATK)

    @property
    def sp_def(self) -> int:
        return self.total_for(Stat.SP_DEF)

    @property
    def speed(self) -> int:
        effective = self.total_for(Stat.SPEED)
        if self.status == StatusCondition.PARALYZE:
            effective = math.floor(effective * 0.5)
        return effective

    @property
    def total_stats(self) -> dict[str, int]:
        return {s: self.total_for(Stat(s)) for s in ("hp", "attack", "defense", "sp_atk", "sp_def", "speed")}

    @property
    def evs(self) -> dict[str, int]:
        return self._evs

    @evs.setter
    def evs(self, value: dict[str, int]):
        self._evs = value

    # -- HP --

    def take_damage(self, amount: int) -> int:
        amount = max(0, amount)
        actual = min(amount, self.current_hp)
        self.current_hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        amount = max(0, amount)
        actual = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual
        return actual

    def is_fainted(self) -> bool:
        return self.current_hp <= 0

    # -- Status --

    def apply_status(self, status: StatusCondition, badly_poisoned: bool = False) -> bool:
        if self.status is not None:
            return False
        self.status = status
        self._badly_poisoned = badly_poisoned
        self._poison_tick = 0
        if status == StatusCondition.SLEEP:
            self._sleep_turns = random.randint(1, 3)
        return True

    def has_status(self) -> bool:
        return self.status is not None

    def can_act(self) -> bool:
        if self.status == StatusCondition.SLEEP and self._sleep_turns > 0:
            return False
        if self.status == StatusCondition.FREEZE:
            return False
        if self._flinch_turns > 0:
            return False
        if self.status == StatusCondition.PARALYZE and random.random() < 0.25:
            return False
        return True

    def get_cannot_act_reason(self) -> str | None:
        if self.status == StatusCondition.SLEEP and self._sleep_turns > 0:
            return "sleep"
        if self.status == StatusCondition.FREEZE:
            return "freeze"
        if self._flinch_turns > 0:
            return "flinch"
        if self.status == StatusCondition.PARALYZE and random.random() < 0.25:
            return "paralyze"
        return None

    def apply_end_of_turn_status(self) -> int:
        damage = 0
        if self.status == StatusCondition.BURN:
            damage = max(1, math.floor(self.max_hp / 16))
        elif self.status == StatusCondition.POISON:
            if self._badly_poisoned:
                self._poison_tick += 1
                damage = max(1, math.floor(self.max_hp * self._poison_tick / 16))
            else:
                damage = max(1, math.floor(self.max_hp / 8))
        if damage > 0:
            self.take_damage(damage)
        return damage

    def advance_turn(self):
        if self.status == StatusCondition.SLEEP and self._sleep_turns > 0:
            self._sleep_turns -= 1
            if self._sleep_turns == 0:
                self.status = None
        if self._flinch_turns > 0:
            self._flinch_turns -= 1
        # Frozen: 20% chance to thaw each turn
        if self.status == StatusCondition.FREEZE and random.random() < 0.20:
            self.status = None

    # -- Flinch --

    def apply_flinch(self, turns: int):
        self._flinch_turns = turns

    # -- Stat stages --

    def modify_stat(self, stat: Stat, stages: int) -> int:
        if stages == 0:
            return 0
        current = self._stat_stages[stat]
        new = max(-6, min(6, current + stages))
        actual = new - current
        self._stat_stages[stat] = new
        return actual

    def reset_stat_stages(self):
        for s in Stat:
            self._stat_stages[s] = 0
