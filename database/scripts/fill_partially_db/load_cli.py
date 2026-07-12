import sys
import time

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Prompt, IntPrompt
from rich.live import Live
from rich.spinner import Spinner
from rich import box

from db_connection import get_connection
from add_types import ensure_types
from add_natures import ensure_natures
from add_pokemons import add_pokemon
from add_items import add_item_by_name

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

DESCRIPTION = "Here you will be able to add a Pokémon (with all their moves and abilities) or an item, one by one :]"

console = Console()


def print_header():
    console.print(Panel(TITLE, style="bold cyan", box=box.HEAVY))
    console.print(Panel(DESCRIPTION, style="bold cyan", box=box.HEAVY))
    console.print()


def run_add_pokemon(conn, name: str):
    type_map = ensure_types(conn)

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
        result = add_pokemon(
            conn, name.lower(), type_map, progress, task, spinner
        )

    if "error" in result:
        console.print(f"\n[red]✖ Error: {result['error']}[/red]")
        return

    table = Table(
        title=f"[bold yellow]{result['name'].capitalize()}[/bold yellow]  (#{result['id']})",
        box=box.ROUNDED,
        style="cyan",
    )
    table.add_column("Stat", style="bold white")
    table.add_column("Value", style="cyan")

    table.add_row("HP", str(result["hp"]))
    table.add_row("Attack", str(result["attack"]))
    table.add_row("Defense", str(result["defense"]))
    table.add_row("Sp. Atk", str(result["sp_atk"]))
    table.add_row("Sp. Def", str(result["sp_def"]))
    table.add_row("Speed", str(result["speed"]))
    table.add_row("Types", ", ".join(result["types"]))
    table.add_row("Abilities", ", ".join(result["abilities"]))

    console.print("\n")
    console.print(table)
    console.print(
        f"\n[green]✔[/green] {result['name'].capitalize()} added successfully!\n"
        f"   [dim]Moves: {result['moves_added']} added, "
        f"{result['moves_skipped']} skipped[/dim]"
    )


def run_add_item(conn, name: str):
    result = add_item_by_name(conn, name.lower())

    if "error" in result:
        console.print(
            f"\n[red]✖ Error fetching item '{name}': {result['error']}[/red]"
        )
        return

    table = Table(
        title=f"[bold yellow]Item: {result['name']}[/bold yellow]",
        box=box.ROUNDED,
        style="cyan",
    )
    table.add_column("Field", style="bold white")
    table.add_column("Value", style="cyan")

    table.add_row("Name", result["name"])
    table.add_row("Description", result["description"] or "[dim](none)[/dim]")
    table.add_row(
        "Status",
        (
            "[green]Newly added[/green]"
            if result["new"]
            else "[dim]Already existed[/dim]"
        ),
    )

    console.print("\n")
    console.print(table)


def main():
    print_header()

    args = [a.lower() for a in sys.argv[1:]]
    item_mode = False
    direct_name = None

    if args and args[0] in ("--item", "-i"):
        item_mode = True
        direct_name = args[1] if len(args) > 1 else None
    elif args:
        direct_name = args[0]

    conn = get_connection()

    with console.status(
        "[bold green]Syncing types and natures...", spinner="dots"
    ):
        ensure_types(conn)
        ensure_natures(conn)
        time.sleep(0.3)
    console.print("[green]✔[/green] Types and natures synced\n")

    if direct_name:
        if item_mode:
            run_add_item(conn, direct_name)
        else:
            run_add_pokemon(conn, direct_name)
        conn.close()
        return

    while True:
        console.print("[bold]What would you like to do?[/bold]")
        console.print("  [cyan]1[/cyan]  Add a Pokémon")
        console.print("  [cyan]2[/cyan]  Add an Item")
        console.print("  [cyan]0[/cyan]  Exit")

        choice = IntPrompt.ask("\n[bold]Option", default=1)

        if choice == 0:
            break
        elif choice == 1:
            name = Prompt.ask("[cyan]Pokémon name")
            run_add_pokemon(conn, name.strip().lower())
        elif choice == 2:
            name = Prompt.ask("[cyan]Item name")
            run_add_item(conn, name.strip().lower())
        else:
            console.print("[red]Invalid option[/red]")
            continue

        console.print("\n" + "─" * 50 + "\n")

    conn.close()
    console.print("[bold green]Goodbye![/bold green]")


if __name__ == "__main__":
    main()
