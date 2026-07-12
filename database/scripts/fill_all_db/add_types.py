import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_types(conn, progress=None, task_id=None) -> dict[int, int]:
    """Load types from CSV. Returns dict mapping csv_id → db_id."""
    cursor = conn.cursor()
    name_map: dict[int, str] = {}
    id_map: dict[int, int] = {}

    with open(DATA_DIR / "type_names.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                name_map[int(row["type_id"])] = row["name"]

    types: list[tuple[int, str]] = []
    with open(DATA_DIR / "types.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            name = name_map.get(csv_id, row["identifier"])
            types.append((csv_id, name))

    cursor.execute("SELECT Name, TypeID FROM `Type`")
    existing: dict[str, int] = {row[0]: row[1] for row in cursor.fetchall()}

    if progress and task_id is not None:
        progress.update(task_id, total=len(types))

    batch: list[str] = []
    batch_ids: list[int] = []
    for csv_id, name in types:
        if name in existing:
            id_map[csv_id] = existing[name]
        else:
            batch.append(name)
            batch_ids.append(csv_id)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if batch:
        cursor.executemany("INSERT IGNORE INTO `Type` (Name) VALUES (?)", [(n,) for n in batch])
        for i, csv_id in enumerate(batch_ids):
            cursor.execute("SELECT TypeID FROM `Type` WHERE Name = ?", (batch[i],))
            row = cursor.fetchone()
            if row:
                id_map[csv_id] = row[0]

    cursor.close()
    return id_map
