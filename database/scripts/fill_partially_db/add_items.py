from time import sleep
import requests


def add_item_by_name(conn, item_name: str) -> dict:
    cursor = conn.cursor()
    cursor.execute("SELECT ItemID, Name, Description FROM `Item` WHERE Name = ?", (item_name,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        return {"id": row[0], "name": row[1], "description": row[2], "new": False}

    sleep(1)
    resp = requests.get(f"https://pokeapi.co/api/v2/item/{item_name}/")
    if resp.status_code != 200:
        cursor.close()
        return {"error": f"HTTP {resp.status_code}"}

    data = resp.json()

    description = ""
    for entry in data.get("effect_entries", []):
        if entry.get("language", {}).get("name") == "en":
            description = entry.get("short_effect", "") or entry.get("effect", "")
            break

    cursor.execute(
        "INSERT INTO `Item` (Name, Description) VALUES (?, ?)",
        (item_name, description[:100]),
    )
    description = description[:100]
    item_id = cursor.lastrowid
    cursor.close()
    return {"id": item_id, "name": item_name, "description": description, "new": True}
