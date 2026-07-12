import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


def load_items(conn, progress=None, task_id=None) -> dict[int, int]:
    """Load items from CSV. Returns dict mapping csv_id → db_id."""
    cursor = conn.cursor()
    id_map: dict[int, int] = {}
    name_map: dict[int, str] = {}
    desc_map: dict[int, str] = {}

    with open(DATA_DIR / "item_names.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                name_map[int(row["item_id"])] = row["name"]

    with open(DATA_DIR / "item_prose.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                iid = int(row["item_id"])
                short = row.get("short_effect", "").strip()
                effect = row.get("effect", "").strip()
                desc_map[iid] = (short or effect)[:100]

    items: list[tuple[int, str, str]] = []
    with open(DATA_DIR / "items.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            name = name_map.get(csv_id, row["identifier"])
            description = desc_map.get(csv_id, "")
            items.append((csv_id, name, description))

    cursor.execute("SELECT Name, ItemID FROM `Item`")
    existing: dict[str, int] = {row[0]: row[1] for row in cursor.fetchall()}

    if progress and task_id is not None:
        progress.update(task_id, total=len(items))

    batch: list[tuple[str, str]] = []
    batch_ids: list[int] = []
    for csv_id, name, description in items:
        if name in existing:
            id_map[csv_id] = existing[name]
        else:
            batch.append((name, description))
            batch_ids.append(csv_id)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if batch:
        cursor.executemany(
            "INSERT IGNORE INTO `Item` (Name, Description) VALUES (?, ?)",
            batch,
        )
        for i, csv_id in enumerate(batch_ids):
            cursor.execute(
                "SELECT ItemID FROM `Item` WHERE Name = ?",
                (batch[i][0],),
            )
            row = cursor.fetchone()
            if row:
                id_map[csv_id] = row[0]

    cursor.close()
    return id_map
