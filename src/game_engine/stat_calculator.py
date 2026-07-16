import math
import re


_STAT_ABBR_MAP: dict[str, str] = {
    "Atk": "attack",
    "Def": "defense",
    "SpA": "sp_atk",
    "SpD": "sp_def",
    "Spe": "speed",
    "SpAtk": "sp_atk",
    "SpDef": "sp_def",
}


def calculate_total_hp(base_hp: int, ev_hp: int, level: int = 100) -> int:
    return math.floor((2 * base_hp + 31 + math.floor(ev_hp / 4)) * level / 100) + level + 10


def calculate_total_stat(base_stat: int, ev: int, nature_multiplier: float, level: int = 100) -> int:
    raw = math.floor((2 * base_stat + 31 + math.floor(ev / 4)) * level / 100) + 5
    return math.floor(raw * nature_multiplier)


def parse_nature(stat_changed: str | None) -> dict[str, float]:
    mults = {"attack": 1.0, "defense": 1.0, "sp_atk": 1.0, "sp_def": 1.0, "speed": 1.0}
    if not stat_changed:
        return mults
    m = re.match(r"\(-(\w+),\s*\+(\w+)\)", stat_changed)
    if not m:
        return mults
    dec_key = _STAT_ABBR_MAP.get(m.group(1))
    inc_key = _STAT_ABBR_MAP.get(m.group(2))
    if dec_key:
        mults[dec_key] = 0.9
    if inc_key:
        mults[inc_key] = 1.1
    return mults
