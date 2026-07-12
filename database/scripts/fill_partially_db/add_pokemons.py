from time import sleep
import requests
from add_types import get_type_id
from add_abilities import add_ability
from add_moves import add_move


def add_pokemon(
    conn,
    pokemon_name: str,
    type_map: dict[str, int],
    progress=None,
    task_id=None,
    spinner=None,
) -> dict:
    if spinner:
        spinner.text = f"Fetching {pokemon_name} from PokeAPI..."

    sleep(1)
    resp = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_name}/")
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}

    data = resp.json()
    poke_id = data["id"]
    name = data["name"]

    cursor = conn.cursor()
    cursor.execute("SELECT PokemonID FROM `Pokemon` WHERE Name = ?", (name,))
    existing = cursor.fetchone()
    if existing:
        cursor.close()
        return {
            "error": f"'{name}' already exists in DB (PokemonID={existing[0]})"
        }

    stats_raw = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    hp = stats_raw.get("hp", 0)
    attack = stats_raw.get("attack", 0)
    defense = stats_raw.get("defense", 0)
    sp_atk = stats_raw.get("special-attack", 0)
    sp_def = stats_raw.get("special-defense", 0)
    speed = stats_raw.get("speed", 0)

    front_png = f"sprites/pokemon/png/front/{poke_id}.png"
    back_png = f"sprites/pokemon/png/back/{poke_id}.png"
    front_gif = f"sprites/pokemon/gif/front/{poke_id}.gif"
    back_gif = f"sprites/pokemon/gif/back/{poke_id}.gif"

    cursor.execute(
        """INSERT INTO `Pokemon`
           (Name, Hp, Attack, Defense, SpAtk, SpDef, Speed,
            FrontSpriteGIF, BackSpriteGIF, FrontSpritePNG, BackSpritePNG)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            name,
            hp,
            attack,
            defense,
            sp_atk,
            sp_def,
            speed,
            front_gif,
            back_gif,
            front_png,
            back_png,
        ),
    )
    pokemon_id = cursor.lastrowid
    cursor.close()

    abilities = data.get("abilities", [])
    moves = data.get("moves", [])

    if progress and task_id is not None:
        total = 1 + len(abilities) + len(moves)
        progress.update(task_id, total=total, completed=1)
    if spinner:
        spinner.text = f"[cyan]Pokémon data fetched ({len(abilities)} abilities, {len(moves)} moves)"

    types_processed: list[str] = []
    for t in data.get("types", []):
        type_name = t["type"]["name"]
        type_id = get_type_id(conn, type_name, type_map)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT IGNORE INTO `Type_pokemon` (PokemonID, TypeID) VALUES (?, ?)",
            (pokemon_id, type_id),
        )
        cursor.close()
        types_processed.append(type_name)

    abilities_processed: list[str] = []
    for i, a in enumerate(abilities, 1):
        ab_name = a["ability"]["name"]
        if spinner:
            spinner.text = f"[cyan]Ability {i}/{len(abilities)}: {ab_name}"
        ab_id = add_ability(conn, ab_name)
        if ab_id:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT IGNORE INTO `Ability_pokemon` (PokemonID, AbilityID) VALUES (?, ?)",
                (pokemon_id, ab_id),
            )
            cursor.close()
            abilities_processed.append(ab_name)
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    moves_added = 0
    moves_skipped = 0
    for i, m in enumerate(moves, 1):
        mv_name = m["move"]["name"]
        if spinner:
            spinner.text = f"Move {i}/{len(moves)}: {mv_name}"
        mv_id = add_move(conn, mv_name, type_map)
        if mv_id:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT IGNORE INTO `Move_pokemon` (PokemonID, MoveID) VALUES (?, ?)",
                (pokemon_id, mv_id),
            )
            cursor.close()
            moves_added += 1
        else:
            moves_skipped += 1
        if progress and task_id is not None:
            progress.update(task_id, advance=1)

    if spinner:
        spinner.text = "Done!"

    return {
        "id": poke_id,
        "pokemon_id": pokemon_id,
        "name": name,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "sp_atk": sp_atk,
        "sp_def": sp_def,
        "speed": speed,
        "types": types_processed,
        "abilities": abilities_processed,
        "moves_added": moves_added,
        "moves_skipped": moves_skipped,
    }
