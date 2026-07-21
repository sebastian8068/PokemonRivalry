# Creating Pokémon Moves

## File to edit
`src/game_engine/moves.py` — add an entry to the `MOVE_EFFECTS` dict.

## Available effects (`src/game_engine/effects.py`)

| Effect | Constructor | Description |
|--------|-------------|-------------|
| `DamageEffect()` | — | Standard damage with STAB, type effectiveness, crit |
| `SelfDamageEffect(recoil_fraction)` | `float` (e.g. 0.25) | Damage + recoil to self (fraction of dealt damage) |
| `StatusEffect(status, accuracy, badly_poisoned)` | `StatusCondition`, `float`, `bool` | Apply status condition to target |
| `FlinchEffect(turns, accuracy)` | `int`, `float` | Target flinches (can't act this turn) |
| `StatChangeEffect(stat, stages, target, accuracy)` | `Stat`, `int`, `"self"/"opponent"`, `float` | Raise/lower a stat |

## Enums

**`StatusCondition`**: `BURN`, `PARALYZE`, `SLEEP`, `FREEZE`, `POISON`

**`Stat`**: `ATTACK`, `DEFENSE`, `SP_ATK`, `SP_DEF`, `SPEED`, `ACCURACY`, `EVASION`

## Patterns

```python
# Pure damage
"Earthquake": [DamageEffect()],

# Damage + secondary effect (e.g. 10% paralyze)
"Thunderbolt": [
    DamageEffect(),
    StatusEffect(status=StatusCondition.PARALYZE, accuracy=0.10),
],

# Damage + stat change (e.g. 30% lower Defense)
"Iron Tail": [
    DamageEffect(),
    StatChangeEffect(stat=Stat.DEFENSE, stages=-1, target="opponent", accuracy=0.30),
],

# Damage + flinch (e.g. 30% flinch)
"Headbutt": [
    DamageEffect(),
    FlinchEffect(turns=1, accuracy=0.30),
],

# Pure stat change — status move (e.g. sharply raise Sp. Atk)
"Nasty Plot": [
    StatChangeEffect(stat=Stat.SP_ATK, stages=+2, target="self"),
],

# Damage + recoil (e.g. 25% of dealt damage)
"Take Down": [
    SelfDamageEffect(recoil_fraction=0.25),
],
```

## Requirements

- The move name in `MOVE_EFFECTS` must match exactly the `Name` column in the DB `Move` table (case-sensitive)
- No need to modify the database — just add to `MOVE_EFFECTS`
- Effect order in the list determines execution order
- `accuracy` is a probability (`0.0`–`1.0`), checked via `random.random()`
- If a move is not registered in `MOVE_EFFECTS`, the engine falls back to 5 flat damage

## Not implemented (falls back to 5 damage)

- Priority moves (order is determined purely by Speed)
- Multi-hit moves
- Two-turn moves (e.g. Dig, Fly, Solar Beam)
- Abilities and items interactions
- Move-specific edge cases
- Healing moves
- Protecting moves
