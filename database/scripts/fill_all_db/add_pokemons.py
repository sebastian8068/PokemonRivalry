import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

STAT_ID_MAP: dict[int, str] = {
    1: "hp",
    2: "attack",
    3: "defense",
    4: "sp_atk",
    5: "sp_def",
    6: "speed",
}


def _load_stat_names() -> dict[int, str]:
    stat_names: dict[int, str] = {}
    with open(DATA_DIR / "stats.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = int(row["id"])
            identifier = row["identifier"].replace("-", "_").lower()
            if sid <= 6:
                stat_names[sid] = identifier
    return stat_names


def load_pokemon(conn, type_id_map: dict[int, int],
                 ability_id_map: dict[int, int],
                 move_id_map: dict[int, int],
                 progress=None, task_id=None) -> dict:
    cursor = conn.cursor()

    stat_names = {
        1: "hp",
        2: "attack",
        3: "defense",
        4: "sp_atk",
        5: "sp_def",
        6: "speed",
    }

    pokemon_stats: dict[int, dict[str, int]] = {}
    with open(DATA_DIR / "pokemon_stats.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = int(row["pokemon_id"])
            sid = int(row["stat_id"])
            if sid in stat_names:
                pokemon_stats.setdefault(pid, {})[stat_names[sid]] = int(row["base_stat"])

    pokemon_list: list[tuple[int, str, int, int, int, int, int, int, str, str, str, str]] = []
    with open(DATA_DIR / "pokemon.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = int(row["id"])
            name = row["identifier"][:20]
            stats = pokemon_stats.get(pid, {})
            hp = stats.get("hp", 0)
            attack = stats.get("attack", 0)
            defense = stats.get("defense", 0)
            sp_atk = stats.get("sp_atk", 0)
            sp_def = stats.get("sp_def", 0)
            speed = stats.get("speed", 0)

            front_png = f"sprites/pokemon/png/front/{pid}.png"
            back_png = f"sprites/pokemon/png/back/{pid}.png"
            front_gif = f"sprites/pokemon/gif/front/{pid}.gif"
            back_gif = f"sprites/pokemon/gif/back/{pid}.gif"

            pokemon_list.append((pid, name, hp, attack, defense, sp_atk, sp_def, speed,
                                 front_gif, back_gif, front_png, back_png))

    inserted = 0
    skipped = 0
    for i, (pid, name, hp, attack, defense, sp_atk, sp_def, speed,
            fg, bg, fp, bp) in enumerate(pokemon_list, 1):
        if progress and task_id is not None:
            progress.update(task_id, advance=1,
                            description=f"Pokémon {i}/{len(pokemon_list)}: {name}")

        cursor.execute("SELECT PokemonID FROM `Pokemon` WHERE Name = ?", (name,))
        existing = cursor.fetchone()
        if existing:
            skipped += 1
            continue

        cursor.execute(
            """INSERT IGNORE INTO `Pokemon`
               (PokemonID, Name, Hp, Attack, Defense, SpAtk, SpDef, Speed,
                FrontSpriteGIF, BackSpriteGIF, FrontSpritePNG, BackSpritePNG)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, name, hp, attack, defense, sp_atk, sp_def, speed,
             fg, bg, fp, bp),
        )
        if cursor.rowcount == 0:
            skipped += 1
            continue
        inserted += 1

    cursor.close()
    return {"inserted": inserted, "skipped": skipped, "total": len(pokemon_list)}


def load_pokemon_types(conn, type_id_map: dict[int, int],
                       progress=None, task_id=None) -> int:
    cursor = conn.cursor()
    count = 0
    rows: list[tuple[int, int]] = []
    with open(DATA_DIR / "pokemon_types.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            pid = int(row["pokemon_id"])
            tid = int(row["type_id"])
            if tid in type_id_map:
                rows.append((pid, type_id_map[tid]))
            if len(rows) >= 1000:
                cursor.executemany(
                    "INSERT IGNORE INTO `Type_pokemon` (PokemonID, TypeID) VALUES (?, ?)",
                    rows,
                )
                count += cursor.rowcount
                rows.clear()
                if progress and task_id is not None:
                    progress.update(task_id, completed=i)

    if rows:
        cursor.executemany(
            "INSERT IGNORE INTO `Type_pokemon` (PokemonID, TypeID) VALUES (?, ?)",
            rows,
        )
        count += cursor.rowcount
        if progress and task_id is not None:
            progress.update(task_id, completed=i)

    cursor.close()
    return count


def load_pokemon_abilities(conn, ability_id_map: dict[int, int],
                           progress=None, task_id=None) -> int:
    cursor = conn.cursor()
    count = 0
    rows: list[tuple[int, int]] = []
    with open(DATA_DIR / "pokemon_abilities.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            pid = int(row["pokemon_id"])
            aid = int(row["ability_id"])
            if aid in ability_id_map:
                rows.append((pid, ability_id_map[aid]))
            if len(rows) >= 1000:
                cursor.executemany(
                    "INSERT IGNORE INTO `Ability_pokemon` (PokemonID, AbilityID) VALUES (?, ?)",
                    rows,
                )
                count += cursor.rowcount
                rows.clear()
                if progress and task_id is not None:
                    progress.update(task_id, completed=i)

    if rows:
        cursor.executemany(
            "INSERT IGNORE INTO `Ability_pokemon` (PokemonID, AbilityID) VALUES (?, ?)",
            rows,
        )
        count += cursor.rowcount
        if progress and task_id is not None:
            progress.update(task_id, completed=i)

    cursor.close()
    return count


def load_pokemon_moves(conn, move_id_map: dict[int, int],
                       progress=None, task_id=None) -> int:
    cursor = conn.cursor()
    count = 0
    rows: list[tuple[int, int]] = []
    with open(DATA_DIR / "pokemon_moves.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            pid = int(row["pokemon_id"])
            mid = int(row["move_id"])
            if mid in move_id_map:
                rows.append((pid, move_id_map[mid]))
            if len(rows) >= 1000:
                cursor.executemany(
                    "INSERT IGNORE INTO `Move_pokemon` (PokemonID, MoveID) VALUES (?, ?)",
                    rows,
                )
                count += cursor.rowcount
                rows.clear()
                if progress and task_id is not None:
                    progress.update(task_id, completed=i)

    if rows:
        cursor.executemany(
            "INSERT IGNORE INTO `Move_pokemon` (PokemonID, MoveID) VALUES (?, ?)",
            rows,
        )
        count += cursor.rowcount
        if progress and task_id is not None:
            progress.update(task_id, completed=i)

    cursor.close()
    return count
