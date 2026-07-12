import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

STAT_ABBR: dict[int, str] = {
    1: "HP",
    2: "Atk",
    3: "Def",
    4: "SpA",
    5: "SpD",
    6: "Spe",
}


def load_natures(conn, progress=None, task_id=None) -> dict[int, int]:
    """Load natures from CSV. Returns dict mapping csv_id → db_id."""
    cursor = conn.cursor()
    id_map: dict[int, int] = {}
    name_map: dict[int, str] = {}

    with open(DATA_DIR / "nature_names.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if int(row["local_language_id"]) == 9:
                name_map[int(row["nature_id"])] = row["name"]

    natures: list[tuple[int, str, str]] = []
    with open(DATA_DIR / "natures.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            csv_id = int(row["id"])
            name = name_map.get(csv_id, row["identifier"])

            dec = int(row["decreased_stat_id"])
            inc = int(row["increased_stat_id"])

            if dec == inc:
                stat_changed = ""
            else:
                stat_changed = f"(-{STAT_ABBR[dec]}, +{STAT_ABBR[inc]})"

            natures.append((csv_id, name, stat_changed))

    cursor.execute("SELECT Name, NatureID FROM `Nature`")
    existing: dict[str, int] = {row[0]: row[1] for row in cursor.fetchall()}

    if progress and task_id is not None:
        progress.update(task_id, total=len(natures))

    batch: list[tuple[str, str]] = []
    batch_ids: list[int] = []
    for csv_id, name, stat_changed in natures:
        if name in existing:
            id_map[csv_id] = existing[name]
        else:
            batch.append((name, stat_changed))
            batch_ids.append(csv_id)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if batch:
        cursor.executemany(
            "INSERT IGNORE INTO `Nature` (Name, StatChanged) VALUES (?, ?)",
            batch,
        )
        for i, csv_id in enumerate(batch_ids):
            cursor.execute(
                "SELECT NatureID FROM `Nature` WHERE Name = ?",
                (batch[i][0],),
            )
            row = cursor.fetchone()
            if row:
                id_map[csv_id] = row[0]

    cursor.close()
    return id_map
