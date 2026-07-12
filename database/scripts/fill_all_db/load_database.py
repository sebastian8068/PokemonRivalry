import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Confirm
from rich import box

from db_connection import get_connection
from add_types import load_types
from add_natures import load_natures
from add_abilities import load_abilities
from add_moves import load_moves
from add_items import load_items
from add_pokemons import (
    load_pokemon,
    load_pokemon_types,
    load_pokemon_abilities,
    load_pokemon_moves,
)

TITLE = """
▌ ▌   ▜               ▐
▌▖▌▞▀▖▐ ▞▀▖▞▀▖▛▚▀▖▞▀▖ ▜▀ ▞▀▖
▙▚▌▛▀ ▐ ▌ ▖▌ ▌▌▐ ▌▛▀  ▐ ▖▌ ▌
▘ ▘▝▀▘ ▘▝▀ ▝▀ ▘▝ ▘▝▀▘  ▀ ▝▀
▛▀▖   ▌               ▛▀▖▗       ▜
▙▄▘▞▀▖▌▗▘▞▀▖▛▚▀▖▞▀▖▛▀▖▙▄▘▄ ▌ ▌▝▀▖▐ ▙▀▖▌ ▌
▌  ▌ ▌▛▚ ▛▀ ▌▐ ▌▌ ▌▌ ▌▌▚ ▐ ▐▐ ▞▀▌▐ ▌  ▚▄▌
▘  ▝▀ ▘ ▘▝▀▘▘▝ ▘▝▀ ▘ ▘▘ ▘▀▘ ▘ ▝▀▘ ▘▘  ▗▄▘
"""

DESCRIPTION = (
    "Load all Pokémon data from local CSV files into the database.\n"
    "Populates every table: types, natures, abilities, moves, items,\n"
    "pokémon, and all their relationships."
)

console = Console()


def print_header():
    console.print(Panel(TITLE, style="bold cyan", box=box.HEAVY))
    console.print(Panel(DESCRIPTION, style="bold cyan", box=box.HEAVY))
    console.print()





def main():
    print_header()

    conn = get_connection()

    if not Confirm.ask(
        "[bold yellow]This will populate the entire database. Continue?",
        default=True,
    ):
        conn.close()
        console.print("[dim]Aborted.[/dim]")
        return

    if not Confirm.ask(
        "[bold]Do you want to truncate all tables before loading?",
        default=False,
    ):
        console.print("[dim]Keeping existing data. Duplicates will be skipped.[/dim]\n")
    else:
        with console.status("[bold red]Truncating tables...", spinner="dots"):
            cursor = conn.cursor()
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            for table in [
                "Move_pokemon",
                "Ability_pokemon",
                "Type_pokemon",
                "Pokemon",
                "Team_member",
                "Team",
                "Item",
                "Move",
                "Ability",
                "Nature",
                "Type",
            ]:
                cursor.execute(f"TRUNCATE TABLE `{table}`")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            cursor.close()
        console.print("[green]✔[/green] All tables truncated\n")

    console.print("[bold]Starting database population...[/bold]\n")

    type_id_map = load_types(conn)
    console.print(f"[green]✔[/green] Types: {len(type_id_map)}")

    nature_id_map = load_natures(conn)
    console.print(f"[green]✔[/green] Natures: {len(nature_id_map)}")

    ability_id_map = load_abilities(conn)
    console.print(f"[green]✔[/green] Abilities: {len(ability_id_map)}")

    move_id_map = load_moves(conn, type_id_map)
    console.print(f"[green]✔[/green] Moves: {len(move_id_map)}")

    item_id_map = load_items(conn)
    console.print(f"[green]✔[/green] Items: {len(item_id_map)}")

    with Progress(
        TextColumn("[bold cyan]Pokémon"),
        BarColumn(bar_width=None, style="cyan", pulse_style="cyan"),
        TextColumn("  {task.completed:>4,} / {task.total:<4,}"),
        console=console,
    ) as progress:
        task = progress.add_task("", total=1352)
        pokemon_result = load_pokemon(conn, type_id_map, ability_id_map, move_id_map, progress, task)
    console.print(f"[green]✔[/green] Pokémon: {pokemon_result['inserted']:,} inserted, {pokemon_result['skipped']:,} skipped")

    with Progress(
        TextColumn("[bold cyan]Pokémon-Types"),
        BarColumn(bar_width=None, style="cyan", pulse_style="cyan"),
        TextColumn("  {task.completed:>4,} / {task.total:<4,}"),
        console=console,
    ) as progress:
        task = progress.add_task("", total=2117)
        pt_count = load_pokemon_types(conn, type_id_map, progress, task)
    console.print(f"[green]✔[/green] Type_pokemon: {pt_count:,}")

    with Progress(
        TextColumn("[bold cyan]Pokémon-Abilities"),
        BarColumn(bar_width=None, style="cyan", pulse_style="cyan"),
        TextColumn("  {task.completed:>4,} / {task.total:<4,}"),
        console=console,
    ) as progress:
        task = progress.add_task("", total=2939)
        pa_count = load_pokemon_abilities(conn, ability_id_map, progress, task)
    console.print(f"[green]✔[/green] Ability_pokemon: {pa_count:,}")

    with Progress(
        TextColumn("[bold cyan]Pokémon-Moves"),
        BarColumn(bar_width=None, style="cyan", pulse_style="cyan"),
        TextColumn("  {task.completed:>8,} / {task.total:<8,}"),
        console=console,
    ) as progress:
        task = progress.add_task("", total=635906)
        pm_count = load_pokemon_moves(conn, move_id_map, progress, task)
    console.print(f"[green]✔[/green] Move_pokemon: {pm_count:,}")

    summary = Table(
        title="[bold green]Database population complete![/bold green]",
        box=box.HEAVY,
        style="cyan",
    )
    summary.add_column("Table", style="bold white")
    summary.add_column("Rows", style="cyan", justify="right")

    summary.add_row("Type", str(len(type_id_map)))
    summary.add_row("Nature", str(len(nature_id_map)))
    summary.add_row("Ability", str(len(ability_id_map)))
    summary.add_row("Move", str(len(move_id_map)))
    summary.add_row("Item", str(len(item_id_map)))
    summary.add_row("Pokémon", f"{pokemon_result['inserted']:,} (+{pokemon_result['skipped']:,} skipped)")
    summary.add_row("Type_pokemon", str(pt_count))
    summary.add_row("Ability_pokemon", str(pa_count))
    summary.add_row("Move_pokemon", str(pm_count))

    console.print("\n")
    console.print(summary)
    console.print("\n[bold green]✔ Database fully populated![/bold green]")

    conn.close()


if __name__ == "__main__":
    main()
