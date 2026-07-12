from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm
from rich import box

from db_connection import get_connection

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
    "Removes all data from the Pokémon Rivalry database.\n"
    "Truncates every table: users, teams, pokémon, moves, abilities, items, and more."
)

console = Console()

TABLES = [
    "Team_member",
    "Team",
    "Ability_pokemon",
    "Move_pokemon",
    "Type_pokemon",
    "Pokemon",
    "User",
    "Move",
    "Item",
    "Ability",
    "Nature",
    "Type",
]


def print_header():
    console.print(Panel(TITLE, style="bold cyan", box=box.HEAVY))
    console.print(Panel(DESCRIPTION, style="bold cyan", box=box.HEAVY))
    console.print()


def get_row_counts(cursor) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
        counts[table] = cursor.fetchone()[0]
    return counts


def show_table(counts: dict[str, int]):
    table = Table(
        title="Tables to truncate",
        box=box.HEAVY,
        style="cyan",
        title_style="bold",
    )
    table.add_column("Table", style="bold white")
    table.add_column("Current rows", style="cyan", justify="right")
    table.add_column("After truncate", style="dim", justify="center")

    for t in TABLES:
        status = str(counts[t]) if counts[t] > 0 else "[dim]0[/dim]"
        table.add_row(t, status, "[red]0[/red]")

    console.print(table)
    console.print()


def main():
    print_header()

    conn = get_connection()
    cursor = conn.cursor()

    counts = get_row_counts(cursor)
    show_table(counts)

    total = sum(counts.values())
    console.print(
        f"[bold red]⚠ Total rows to delete: {total:,}[/bold red]"
    )
    console.print(
        "[red]This action is irreversible. All data will be permanently lost.[/red]\n"
    )

    if not Confirm.ask(
        "[bold yellow]Are you sure you want to delete ALL data?",
        default=False,
    ):
        console.print("[dim]Aborted.[/dim]")
        cursor.close()
        conn.close()
        return

    with console.status("[bold red]Truncating tables...", spinner="dots"):
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in TABLES:
            cursor.execute(f"TRUNCATE TABLE `{table}`")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    console.print("[green]✔[/green] All tables truncated successfully!\n")

    counts_after = get_row_counts(cursor)
    after = Table(
        title="[bold green]Clean slate[/bold green]",
        box=box.HEAVY,
        style="cyan",
    )
    after.add_column("Table", style="bold white")
    after.add_column("Rows", style="cyan", justify="right")
    after.add_column("Status", style="bold green", justify="center")

    for t in TABLES:
        after.add_row(t, str(counts_after[t]), "[green]✔ Truncated[/green]")

    console.print(after)
    console.print("\n[bold green]✔ Database is now empty![/bold green]")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
