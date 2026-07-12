natures_names: dict[str, str] = {
    "Adamant": "(+Atk, -SpA)",
    "Bashful": "",
    "Bold": "(+Def, -Atk)",
    "Brave": "(+Atk, -Spe)",
    "Calm": "(+SpD, -Atk)",
    "Careful": "(+SpD, -SpA)",
    "Docile": "",
    "Gentle": "(+SpD, -Def)",
    "Hardy": "",
    "Hasty": "(+Spe, -Def)",
    "Impish": "(+Def, -SpA)",
    "Jolly": "(+Spe, -SpA)",
    "Lax": "(+Def, -SpD)",
    "Lonely": "(+Atk, -Def)",
    "Mild": "(+SpA, -Def)",
    "Modest": "(+SpA, -Atk)",
    "Naive": "(+Spe, -SpD)",
    "Naughty": "(+Atk, -SpD)",
    "Quiet": "(+SpA, -Spe)",
    "Quirky": "",
    "Rash": "(+SpA, -SpD)",
    "Relaxed": "(+Def, -Spe)",
    "Sassy": "(+SpD, -Spe)",
    "Serious": "",
    "Timid": "(+Spe, -Atk)",
}


def ensure_natures(conn) -> dict[str, int]:
    cursor = conn.cursor()
    nature_map: dict[str, int] = {}
    for name, stat_changed in natures_names.items():
        cursor.execute("SELECT NatureID FROM `Nature` WHERE Name = ?", (name,))
        row = cursor.fetchone()
        if row:
            nature_map[name] = row[0]
        else:
            cursor.execute(
                "INSERT INTO `Nature` (Name, StatChanged) VALUES (?, ?)",
                (name, stat_changed),
            )
            nature_map[name] = cursor.lastrowid
    cursor.close()
    return nature_map
