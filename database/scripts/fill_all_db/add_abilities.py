import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_abilities(conn, progress=None, task_id=None) -> dict[int, int]:
    """Load abilities from CSV. Returns dict mapping csv_id → db_id."""
    cursor = conn.cursor()
    id_map: dict[int, int] = {}
    name_map: dict[int, str] = {}
    desc_map: dict[int, str] = {}

    with open(DATA_DIR / "ability_names.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                name_map[int(row["ability_id"])] = row["name"]

    with open(DATA_DIR / "ability_prose.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                aid = int(row["ability_id"])
                short = row.get("short_effect", "").strip()
                effect = row.get("effect", "").strip()
                desc_map[aid] = short or effect

    abilities: list[tuple[int, str, str]] = []
    with open(DATA_DIR / "abilities.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            name = name_map.get(csv_id, row["identifier"])
            description = desc_map.get(csv_id, "")
            abilities.append((csv_id, name, description))

    cursor.execute("SELECT Name, AbilityID FROM `Ability`")
    existing: dict[str, int] = {row[0]: row[1] for row in cursor.fetchall()}

    if progress and task_id is not None:
        progress.update(task_id, total=len(abilities))

    batch: list[tuple[str, str]] = []
    batch_ids: list[int] = []
    for csv_id, name, description in abilities:
        if name in existing:
            id_map[csv_id] = existing[name]
        else:
            batch.append((name, description))
            batch_ids.append(csv_id)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if batch:
        cursor.executemany(
            "INSERT IGNORE INTO `Ability` (Name, Description) VALUES (?, ?)",
            batch,
        )
        for i, csv_id in enumerate(batch_ids):
            cursor.execute(
                "SELECT AbilityID FROM `Ability` WHERE Name = ?",
                (batch[i][0],),
            )
            row = cursor.fetchone()
            if row:
                id_map[csv_id] = row[0]

    cursor.close()
    return id_map
