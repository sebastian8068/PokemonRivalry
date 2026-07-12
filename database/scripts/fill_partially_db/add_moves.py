from time import sleep
import requests
from add_types import get_type_id


def add_move(conn, move_name: str, type_map: dict[str, int]) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT MoveID FROM `Move` WHERE Name = ?", (move_name,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        return row[0]

    sleep(1)
    resp = requests.get(f"https://pokeapi.co/api/v2/move/{move_name}/")
    if resp.status_code != 200:
        print(f"  ⚠ Could not fetch move '{move_name}' (HTTP {resp.status_code})")
        cursor.close()
        return 0

    data = resp.json()

    type_name = data.get("type", {}).get("name", "normal")
    type_id = get_type_id(conn, type_name, type_map)

    category = data.get("damage_class", {}).get("name", "status")

    pp_raw = data.get("pp", 0)
    pp = int(pp_raw * 1.6)

    power = data.get("power")
    accuracy = data.get("accuracy")

    effect = ""
    for entry in data.get("effect_entries", []):
        if entry.get("language", {}).get("name") == "en":
            effect = entry.get("short_effect", "") or entry.get("effect", "")
            break

    cursor.execute(
        """INSERT INTO `Move` (TypeID, Name, Category, PP, Power, Accuracy, Effect)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (type_id, move_name, category, pp, power, accuracy, effect),
    )
    move_id = cursor.lastrowid
    cursor.close()
    return move_id
