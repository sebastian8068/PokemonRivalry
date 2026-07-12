types_names: list[str] = [
    "bug",
    "dragon",
    "fairy",
    "fire",
    "ghost",
    "grass",
    "ground",
    "normal",
    "psychic",
    "steel",
    "dark",
    "electric",
    "fighting",
    "flying",
    "ice",
    "poison",
    "rock",
    "water",
]


def ensure_types(conn) -> dict[str, int]:
    cursor = conn.cursor()
    type_map: dict[str, int] = {}
    for name in types_names:
        cursor.execute("SELECT TypeID FROM `Type` WHERE Name = ?", (name,))
        row = cursor.fetchone()
        if row:
            type_map[name] = row[0]
        else:
            cursor.execute("INSERT INTO `Type` (Name) VALUES (?)", (name,))
            type_map[name] = cursor.lastrowid
    cursor.close()
    return type_map


def get_type_id(conn, type_name: str, type_map: dict[str, int]) -> int | None:
    if type_name in type_map:
        return type_map[type_name]
    cursor = conn.cursor()
    cursor.execute("SELECT TypeID FROM `Type` WHERE Name = ?", (type_name,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        type_map[type_name] = row[0]
        return row[0]
    cursor = conn.cursor()
    cursor.execute("INSERT INTO `Type` (Name) VALUES (?)", (type_name,))
    type_map[type_name] = cursor.lastrowid
    cursor.close()
    return type_map[type_name]
