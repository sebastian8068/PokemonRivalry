import argparse
import importlib.util
import sys
from pathlib import Path

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, BarColumn, TextColumn
from rich.live import Live
from rich.spinner import Spinner
from rich import box

from db_connection import get_connection

_SCRIPTS_DIR = Path(__file__).resolve().parent

_CONFLICTING = {
    "db_connection", "add_types", "add_natures", "add_abilities",
    "add_moves", "add_items", "add_pokemons",
    "runner", "truncate",
}

console = Console()


def _load_isolated(subdir, module_name):
    subdir_path = _SCRIPTS_DIR / subdir
    file_path = subdir_path / f"{module_name}.py"
    unique_name = f"_isolated_{subdir}_{module_name}"

    spec = importlib.util.spec_from_file_location(unique_name, file_path)
    mod = importlib.util.module_from_spec(spec)

    old_path = sys.path.copy()
    saved = {}
    for name in _CONFLICTING:
        if name in sys.modules:
            saved[name] = sys.modules.pop(name)

    sys.path = [str(subdir_path), str(_SCRIPTS_DIR)] + old_path

    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path = old_path
        for name in list(sys.modules.keys()):
            if name in _CONFLICTING:
                del sys.modules[name]
            elif name.startswith("_isolated_"):
                del sys.modules[name]
        sys.modules.update(saved)

    return mod


def cmd_fill_all():
    mod = _load_isolated("fill_all_db", "runner")

    if not Confirm.ask(
        "[bold yellow]This will populate the entire database. Continue?",
        default=True,
    ):
        console.print("[dim]Aborted.[/dim]")
        return

    truncate = not Confirm.ask(
        "[bold]Do you want to truncate all tables before loading?",
        default=False,
    )
    console.print()

    conn = get_connection()
    mod.fill_all(conn, truncate_first=truncate)
    conn.close()


def cmd_remove_all():
    conn = get_connection()
    mod = _load_isolated("remove_db", "truncate")
    counts = mod.truncate_all(conn)
    conn.close()


def cmd_delete_user(name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT UserID, Name, Score FROM `User` WHERE Name = ?", (name,)
    )
    user = cursor.fetchone()

    if not user:
        console.print(f"\n[red]✖ User '{name}' not found.[/red]")
        cursor.close()
        conn.close()
        return

    table = Table(
        title=f"User: {user[1]}",
        box=box.ROUNDED,
        style="cyan",
    )
    table.add_column("Field", style="bold white")
    table.add_column("Value", style="cyan")
    table.add_row("UserID", str(user[0]))
    table.add_row("Name", user[1])
    table.add_row("Score", str(user[2]))
    console.print()
    console.print(table)
    console.print()

    if not Confirm.ask(
        f"[bold yellow]Are you sure you want to delete user '{user[1]}'?[/bold yellow]",
        default=False,
    ):
        console.print("[dim]Aborted.[/dim]")
        cursor.close()
        conn.close()
        return

    cursor.execute("DELETE FROM `User` WHERE Name = ?", (name,))
    console.print(
        f"\n[green]✔[/green] User '{name}' and all their teams have been deleted."
    )

    cursor.close()
    conn.close()


def cmd_set_pikachu_team():
    conn = get_connection()
    cursor = conn.cursor()

    console.print("[bold]Setting up Pikachu team for all users...[/bold]\n")

    cursor.execute("SELECT PokemonID FROM Pokemon WHERE Name = 'Pikachu'")
    row = cursor.fetchone()
    if not row:
        console.print("[red]✖ Pikachu not found in database. Add it first (option 1).[/red]")
        cursor.close()
        conn.close()
        return
    pikachu_id = row[0]

    cursor.execute("SELECT NatureID FROM Nature WHERE Name = 'Hardy'")
    row = cursor.fetchone()
    if not row:
        console.print("[red]✖ Hardy nature not found.[/red]")
        cursor.close()
        conn.close()
        return
    nature_id = row[0]

    cursor.execute("""
        SELECT ap.AbilityID FROM Ability_pokemon ap
        JOIN Ability a ON a.AbilityID = ap.AbilityID
        WHERE ap.PokemonID = ? AND a.Name = 'Static'
    """, (pikachu_id,))
    row = cursor.fetchone()
    if not row:
        console.print("[red]✖ Pikachu has no Static ability registered in Ability_pokemon.[/red]")
        cursor.close()
        conn.close()
        return
    ability_id = row[0]

    move_names = ["Thunderbolt", "Iron Tail", "Headbutt", "Nasty Plot"]
    move_ids = []
    for name in move_names:
        cursor.execute("SELECT MoveID FROM Move WHERE Name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            console.print(f"[red]✖ Move '{name}' not found in database. Aborting.[/red]")
            cursor.close()
            conn.close()
            return
        move_id = row[0]
        cursor.execute(
            "INSERT IGNORE INTO Move_pokemon (PokemonID, MoveID) VALUES (?, ?)",
            (pikachu_id, move_id),
        )
        move_ids.append(move_id)
        console.print(f"  [green]✔[/green] {name} (ID: {move_id}) linked to Pikachu")

    cursor.execute("SELECT UserID, Name FROM User")
    users = cursor.fetchall()
    if not users:
        console.print("[yellow]No users found. Nothing to do.[/yellow]")
        cursor.close()
        conn.close()
        return

    console.print()
    for user_id, user_name in users:
        cursor.execute(
            "INSERT INTO Team (UserID, Name, IsActive) VALUES (?, 'Pikachu Team', 1)",
            (user_id,),
        )
        team_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO Team_member
                (TeamID, Slot, PokemonID, NatureID, ItemID, AbilityID,
                 HpEVs, AttackEVs, DefenseEVs, SpAtkEVs, SpDefEVs, SpeedEVs,
                 Move1ID, Move2ID, Move3ID, Move4ID)
            VALUES (?, 1, ?, ?, NULL, ?,
                    0, 0, 0, 0, 0, 0,
                    ?, ?, ?, ?)
        """, (team_id, pikachu_id, nature_id, ability_id, *move_ids))

        cursor.execute(
            "UPDATE Team SET IsActive = 0 WHERE UserID = ? AND TeamID != ?",
            (user_id, team_id),
        )
        console.print(f"  [green]✔[/green] Team for '{user_name}' (TeamID: {team_id})")

    conn.commit()
    console.print(f"\n[bold green]✔ Done! Pikachu team created for {len(users)} user(s).[/bold green]")
    cursor.close()
    conn.close()


def run_interactive():
    TITLE = """
 ▌ ▌   ▜               ▐
 ▌▖▌▞▀▖▐ ▞▀▖▞▀▖▛▚▀▖▞▀▖ ▜▀ ▞▀▖
 ▙▚▌▛▀ ▐ ▌ ▖▌ ▌▌▐ ▌▛▀  ▐ ▖▌ ▌
 ▘ ▘▝▀▘ ▘▝▀ ▝▀ ▘▝ ▘▝▀▘  ▀ ▝▀
 ▛▀▖   ▌               ▛▀▖▗       ▜
 ▙▄▘▞▀▖▌▗▘▞▀▖▛▚▀▖▞▀▖▛▀▖▙▄▘▄ ▌ ▌▝▀▖▐ ▙▀▖▌ ▌
 ▌  ▌ ▌▛▚ ▛▀ ▌▐ ▌▌ ▌▌ ▌▌▚ ▐ ▐▐ ▞▀▌▐ ▌  ▚▄▌
 ▘  ▝▀ ▘ ▘▝▀▘▘▝ ▘▝▀▘ ▘ ▘▘ ▘▀▘ ▘ ▝▀▘ ▘▘  ▗▄▘
"""
    DESCRIPTION = "Pokémon Rivalry — Unified Database Manager"

    console.print(Panel(TITLE, style="bold cyan", box=box.HEAVY))
    console.print(Panel(DESCRIPTION, style="bold cyan", box=box.HEAVY))
    console.print()

    pk_mod = _load_isolated("fill_partially_db", "add_pokemons")
    it_mod = _load_isolated("fill_partially_db", "add_items")
    tp_mod = _load_isolated("fill_partially_db", "add_types")
    na_mod = _load_isolated("fill_partially_db", "add_natures")

    conn = get_connection()

    with console.status(
        "[bold green]Syncing types and natures...", spinner="dots"
    ):
        tp_mod.ensure_types(conn)
        na_mod.ensure_natures(conn)
    console.print("[green]✔[/green] Types and natures synced\n")

    while True:
        console.print("[bold]What would you like to do?[/bold]")
        console.print("  [cyan]1[/cyan]  Add a Pokémon")
        console.print("  [cyan]2[/cyan]  Add an Item")
        console.print("  [cyan]3[/cyan]  Delete User")
        console.print("  [cyan]4[/cyan]  Fill All Data (from CSV)")
        console.print("  [cyan]5[/cyan]  Remove All Data")
        console.print("  [cyan]6[/cyan]  Set Pikachu Team for all users")
        console.print("  [cyan]0[/cyan]  Exit")

        choice = IntPrompt.ask("\n[bold]Option", default=1)

        if choice == 0:
            break
        elif choice == 1:
            name = Prompt.ask("[cyan]Pokémon name").strip().lower()
            type_map = tp_mod.ensure_types(conn)

            spinner = Spinner("dots", f"[cyan]Fetching {name}...")
            progress = Progress(
                BarColumn(bar_width=None, style="cyan", pulse_style="cyan"),
                TextColumn("  [progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
            )
            task = progress.add_task("", total=None)

            with Live(
                Group(spinner, progress),
                console=console,
                refresh_per_second=10,
            ):
                result = pk_mod.add_pokemon(
                    conn, name, type_map, progress, task, spinner
                )

            if "error" in result:
                console.print(f"\n[red]✖ Error: {result['error']}[/red]")
            else:
                t = Table(
                    title=f"[bold yellow]{result['name'].capitalize()}[/bold yellow]  (#{result['id']})",
                    box=box.ROUNDED,
                    style="cyan",
                )
                t.add_column("Stat", style="bold white")
                t.add_column("Value", style="cyan")
                t.add_row("HP", str(result["hp"]))
                t.add_row("Attack", str(result["attack"]))
                t.add_row("Defense", str(result["defense"]))
                t.add_row("Sp. Atk", str(result["sp_atk"]))
                t.add_row("Sp. Def", str(result["sp_def"]))
                t.add_row("Speed", str(result["speed"]))
                t.add_row("Types", ", ".join(result["types"]))
                t.add_row("Abilities", ", ".join(result["abilities"]))
                console.print("\n")
                console.print(t)
                console.print(
                    f"\n[green]✔[/green] {result['name'].capitalize()} added successfully!\n"
                    f"   [dim]Moves: {result['moves_added']} added, "
                    f"{result['moves_skipped']} skipped[/dim]"
                )

        elif choice == 2:
            name = Prompt.ask("[cyan]Item name").strip().lower()

            result = it_mod.add_item_by_name(conn, name)

            if "error" in result:
                console.print(
                    f"\n[red]✖ Error fetching item '{name}': {result['error']}[/red]"
                )
            else:
                t = Table(
                    title=f"[bold yellow]Item: {result['name']}[/bold yellow]",
                    box=box.ROUNDED,
                    style="cyan",
                )
                t.add_column("Field", style="bold white")
                t.add_column("Value", style="cyan")
                t.add_row("Name", result["name"])
                t.add_row("Description", result["description"] or "[dim](none)[/dim]")
                t.add_row(
                    "Status",
                    "[green]Newly added[/green]"
                    if result["new"]
                    else "[dim]Already existed[/dim]",
                )
                console.print("\n")
                console.print(t)

        elif choice == 3:
            name = Prompt.ask("[cyan]Username to delete")
            cmd_delete_user(name.strip())

        elif choice == 4:
            cmd_fill_all()

        elif choice == 5:
            cmd_remove_all()

        elif choice == 6:
            cmd_set_pikachu_team()

        else:
            console.print("[red]Invalid option[/red]")
            continue

        console.print("\n" + "─" * 50 + "\n")

    conn.close()
    console.print("[bold green]Goodbye![/bold green]")


def main():
    parser = argparse.ArgumentParser(
        description="Pokémon Rivalry Database Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default=None,
        help="fill-all | delete-user NAME | remove-all",
    )
    parser.add_argument("name", nargs="?", default=None, help="Name argument")

    args = parser.parse_args()

    match args.command:
        case None:
            run_interactive()
        case "fill-all":
            cmd_fill_all()
        case "remove-all":
            cmd_remove_all()
        case "delete-user":
            if not args.name:
                console.print(
                    "[red]✖ Error: 'delete-user' requires a name argument.[/red]"
                )
                sys.exit(1)
            cmd_delete_user(args.name)
        case "set-pikachu-team":
            cmd_set_pikachu_team()
        case _:
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
