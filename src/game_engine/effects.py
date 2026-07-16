from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from src.game_engine.enums import StatusCondition, Stat
from src.game_engine.pokemon import BattlePokemon
from src.game_engine.damage import calculate_damage


@dataclass
class EffectResult:
    damage_to_target: int = 0
    damage_to_self: int = 0
    status_applied: StatusCondition | None = None
    status_failed: bool = False
    flinch_turns: int = 0
    flinch_failed: bool = False
    stat_changes: list[tuple[Stat, int, str]] = field(default_factory=list)
    effectiveness: float = 1.0
    stab: bool = False
    crit: bool = False


class MoveEffect(ABC):
    @abstractmethod
    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult: ...


class DamageEffect(MoveEffect):
    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        if move_power is None or move_power <= 0:
            return EffectResult()
        crit = random.random() < 1 / 24
        result = calculate_damage(
            attacker, defender, move_power, move_category, move_type, crit=crit
        )
        dealt = defender.take_damage(result.damage)
        return EffectResult(
            damage_to_target=dealt,
            effectiveness=result.effectiveness,
            stab=result.stab,
            crit=result.crit,
        )


class SelfDamageEffect(MoveEffect):
    def __init__(self, recoil_fraction: float):
        self.recoil_fraction = recoil_fraction

    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        if move_power is None or move_power <= 0:
            return EffectResult()
        crit = random.random() < 1 / 24
        result = calculate_damage(
            attacker, defender, move_power, move_category, move_type, crit=crit
        )
        dealt_to_target = defender.take_damage(result.damage)
        self_damage = max(1, math.floor(dealt_to_target * self.recoil_fraction))
        attacker.take_damage(self_damage)
        return EffectResult(
            damage_to_target=dealt_to_target,
            damage_to_self=self_damage,
            effectiveness=result.effectiveness,
            stab=result.stab,
            crit=result.crit,
        )


class StatusEffect(MoveEffect):
    def __init__(self, status: StatusCondition, accuracy: float = 1.0, badly_poisoned: bool = False):
        self.status = status
        self.accuracy = accuracy
        self.badly_poisoned = badly_poisoned

    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        if random.random() > self.accuracy:
            return EffectResult()
        success = defender.apply_status(self.status, badly_poisoned=self.badly_poisoned)
        return EffectResult(
            status_applied=self.status if success else None,
            status_failed=not success,
        )


class FlinchEffect(MoveEffect):
    def __init__(self, turns: int = 1, accuracy: float = 1.0):
        self.turns = turns
        self.accuracy = accuracy

    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        if random.random() > self.accuracy:
            return EffectResult(flinch_failed=True)
        defender.apply_flinch(self.turns)
        return EffectResult(flinch_turns=self.turns)


class StatChangeEffect(MoveEffect):
    def __init__(self, stat: Stat, stages: int, target: str, accuracy: float = 1.0):
        self.stat = stat
        self.stages = stages
        self.target = target
        self.accuracy = accuracy

    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        if random.random() > self.accuracy:
            return EffectResult()
        pokemon = attacker if self.target == "self" else defender
        actual = pokemon.modify_stat(self.stat, self.stages)
        if actual != 0:
            return EffectResult(stat_changes=[(self.stat, actual, self.target)])
        return EffectResult()


class CompoundEffect(MoveEffect):
    def __init__(self, effects: list[MoveEffect]):
        self.effects = effects

    def apply(
        self,
        attacker: BattlePokemon,
        defender: BattlePokemon,
        move_type: str,
        move_category: str,
        move_power: int | None,
    ) -> EffectResult:
        combined = EffectResult()
        for effect in self.effects:
            partial = effect.apply(attacker, defender, move_type, move_category, move_power)
            combined.damage_to_target += partial.damage_to_target
            combined.damage_to_self += partial.damage_to_self
            if partial.status_applied is not None and combined.status_applied is None:
                combined.status_applied = partial.status_applied
            combined.status_failed = combined.status_failed or partial.status_failed
            combined.flinch_turns += partial.flinch_turns
            combined.flinch_failed = combined.flinch_failed or partial.flinch_failed
            combined.stat_changes.extend(partial.stat_changes)
            if partial.effectiveness != 1.0:
                combined.effectiveness = partial.effectiveness
            if partial.stab:
                combined.stab = True
            if partial.crit:
                combined.crit = True
        return combined


def apply_move(
    attacker: BattlePokemon,
    defender: BattlePokemon,
    effects: list[MoveEffect] | MoveEffect,
    move_type: str,
    move_category: str,
    move_power: int | None,
) -> EffectResult:
    if isinstance(effects, MoveEffect):
        effects_list = [effects]
    else:
        effects_list = effects
    compound = CompoundEffect(effects_list)
    return compound.apply(attacker, defender, move_type, move_category, move_power)
