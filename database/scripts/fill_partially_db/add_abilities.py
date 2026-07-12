from time import sleep
import requests


def add_ability(conn, ability_name: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT AbilityID FROM `Ability` WHERE Name = ?", (ability_name,))
    row = cursor.fetchone()
    if row:
        cursor.close()
        return row[0]

    sleep(1)
    resp = requests.get(f"https://pokeapi.co/api/v2/ability/{ability_name}/")
    if resp.status_code != 200:
        print(f"  ⚠ Could not fetch ability '{ability_name}' (HTTP {resp.status_code})")
        cursor.close()
        return 0

    data = resp.json()
    description = ""
    for entry in data.get("effect_entries", []):
        if entry.get("language", {}).get("name") == "en":
            description = entry.get("effect", "") or entry.get("short_effect", "")
            break

    cursor.execute(
        "INSERT INTO `Ability` (Name, Description) VALUES (?, ?)",
        (ability_name, description),
    )
    ability_id = cursor.lastrowid
    cursor.close()
    return ability_id
