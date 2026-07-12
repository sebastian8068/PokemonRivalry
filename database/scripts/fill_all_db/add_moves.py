import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

DAMAGE_CLASS: dict[int, str] = {
    1: "Status",
    2: "Physical",
    3: "Special",
}


def load_moves(conn, type_id_map: dict[int, int],
               progress=None, task_id=None) -> dict[int, int]:
    """Load moves from CSV. Returns dict mapping csv_id → db_id."""
    cursor = conn.cursor()
    id_map: dict[int, int] = {}
    name_map: dict[int, str] = {}
    effect_map: dict[int, str] = {}

    with open(DATA_DIR / "move_names.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                name_map[int(row["move_id"])] = row["name"]

    with open(DATA_DIR / "move_effect_prose.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                eid = int(row["move_effect_id"])
                short = row.get("short_effect", "").strip()
                effect = row.get("effect", "").strip()
                effect_map[eid] = short or effect

    moves: list[tuple[int, int, str, str, int, int | None, int | None, str]] = []
    with open(DATA_DIR / "moves.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            name = name_map.get(csv_id, row["identifier"])

            csv_type_id = int(row["type_id"])
            if csv_type_id not in type_id_map:
                continue
            type_id = type_id_map[csv_type_id]

            dc_id = int(row["damage_class_id"]) if row["damage_class_id"] else 1
            category = DAMAGE_CLASS.get(dc_id, "Status")

            pp_raw = row["pp"]
            pp = int(pp_raw) if pp_raw else 0

            power = int(row["power"]) if row["power"] else None
            accuracy = int(row["accuracy"]) if row["accuracy"] else None

            effect_id = int(row["effect_id"]) if row["effect_id"] else 0
            effect = effect_map.get(effect_id, "")

            moves.append((csv_id, type_id, name, category, pp, power, accuracy, effect))

    cursor.execute("SELECT Name, MoveID FROM `Move`")
    existing_names: dict[str, int] = {row[0]: row[1] for row in cursor.fetchall()}

    if progress and task_id is not None:
        progress.update(task_id, total=len(moves))

    batch_names: list[str] = []
    batch_rows: list[tuple[int, str, str, int, int | None, int | None, str]] = []
    for csv_id, type_id, name, category, pp, power, accuracy, effect in moves:
        if name in existing_names:
            id_map[csv_id] = existing_names[name]
        else:
            batch_rows.append((type_id, name, category, pp, power, accuracy, effect))
            batch_names.append(name)

        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if batch_rows:
        cursor.executemany(
            """INSERT IGNORE INTO `Move` (TypeID, Name, Category, PP, Power, Accuracy, Effect)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            batch_rows,
        )

        placeholders = ",".join("?" for _ in batch_names)
        cursor.execute(
            f"SELECT MoveID, Name FROM `Move` WHERE Name IN ({placeholders})",
            batch_names,
        )
        name_to_id: dict[str, int] = {row[1]: row[0] for row in cursor.fetchall()}
        for csv_id, type_id, name, *_ in moves:
            if name in name_to_id:
                id_map[csv_id] = name_to_id[name]

    cursor.close()
    return id_map
