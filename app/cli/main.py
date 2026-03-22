#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry point using Rich (when available) with centralized input helpers.

This refactor centralizes input/validation helpers and the `add_opvolging`
workflow so both the Rich UI and the plain-text fallback share the same logic.

Behavior:
- Show list of students with their most recent opvolging date.
- Choose a student number to open the student detail screen.
- In the student detail screen you can:
  - Edit student (placeholder)
  - Add opvolging (implemented, with date validation and default to today)
  - Delete opvolging (placeholder)
  - Edit opvolging (placeholder)
  - Press 'b' to return to the main screen

The CLI prefers `rich` for nicer output but falls back to plain text if it's not installed.
"""

from __future__ import annotations

from typing import Any, List, Optional, TYPE_CHECKING
from datetime import date

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.align import Align
    from rich.text import Text
    _HAS_RICH = True
except Exception:
    Console = None  # type: ignore
    _HAS_RICH = False

if TYPE_CHECKING:
    # Import Rich symbols only for type checking / IDEs. These imports are not required at runtime.
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.align import Align
    from rich.text import Text

from app.repository.repository import StudentRepository, OpvolgingRepository

# Centralized UI text
MAIN_OPTIONS = [
    "Opties:",
    "  [nummer] - Bekijk opvolgingen voor de gekozen student",
    "  q        - Afsluiten",
]

STUDENT_ACTIONS = [
    "Acties:",
    "  1 - Wijzig studentgegevens",
    "  2 - Voeg opvolging toe",
    "  3 - Verwijder opvolging",
    "  4 - Bewerk opvolging",
    "  b - Terug naar hoofdscherm",
]


# ------------------------------
# Helpers: validation / input
# ------------------------------
def validate_date_str(s: str) -> Optional[str]:
    """
    Validate a date string in ISO format YYYY-MM-DD.
    Returns normalized YYYY-MM-DD when valid, otherwise None.
    """
    if not s:
        return None
    try:
        d = date.fromisoformat(s)
        return d.isoformat()
    except Exception:
        return None


def ask_date(console: Any = None) -> str:
    """
    Ask the user for a date. If the user presses Enter without providing a date,
    today's date is used as default.

    Returns a validated date string (YYYY-MM-DD). This function loops until a valid
    date is provided.
    """
    today_str = date.today().isoformat()
    while True:
        if _HAS_RICH and console is not None:
            try:
                datum_input = Prompt.ask(f"  Datum (YYYY-MM-DD) [ENTER = {today_str}]", default=today_str)
            except Exception:
                # fallback to standard input
                datum_input = input(f"  Datum (YYYY-MM-DD) [ENTER = {today_str}]: ").strip()
                if not datum_input:
                    datum_input = today_str
        else:
            datum_input = input(f"  Datum (YYYY-MM-DD) [ENTER = {today_str}]: ").strip()
            if not datum_input:
                datum_input = today_str

        datum_norm = validate_date_str(datum_input)
        if datum_norm is None:
            if _HAS_RICH and console is not None:
                console.print("[red]Ongeldige datum. Gebruik YYYY-MM-DD (bv. 2023-12-31).[/red]")
            else:
                print("Ongeldige datum. Gebruik YYYY-MM-DD (bv. 2023-12-31).")
            continue
        return datum_norm


def ask_type(console: Any = None) -> str:
    """
    Ask for the opvolging type. Must be 'contact' or 'controle'.
    Loops until a valid choice is given.
    """
    while True:
        if _HAS_RICH and console is not None:
            try:
                t = Prompt.ask("  Type", choices=["contact", "controle"], default="contact")
            except Exception:
                t = input("  Type ('contact' of 'controle') [default: contact]: ").strip() or "contact"
        else:
            t = input("  Type ('contact' of 'controle') [default: contact]: ").strip() or "contact"

        if t in ("contact", "controle"):
            return t
        if _HAS_RICH and console is not None:
            console.print("[red]Ongeldig type. Voer 'contact' of 'controle' in.[/red]")
        else:
            print("Ongeldig type. Voer 'contact' of 'controle' in.")


def ask_omschrijving(console: Any = None) -> Optional[str]:
    """
    Ask for an optional textual omschrijving. Returns None when left empty.
    """
    if _HAS_RICH and console is not None:
        try:
            oms = Prompt.ask("  Omschrijving (optioneel)", default="")
        except Exception:
            oms = input("  Omschrijving (optioneel): ").strip()
    else:
        oms = input("  Omschrijving (optioneel): ").strip()
    return oms if oms else None


# ------------------------------
# Rendering helpers
# ------------------------------
def render_main_options_text() -> None:
    for line in MAIN_OPTIONS:
        print(line)
    print()


def render_main_options_rich(console: Any) -> None:
    opts = Text()
    opts.append(MAIN_OPTIONS[0] + "\n", style="bold")
    for line in MAIN_OPTIONS[1:]:
        opts.append(line + "\n")
    console.print(Panel(opts, subtitle="Gebruik", expand=False))


def render_students_text(students: List[object]) -> None:
    header = f"{' #':>3} | {'ID':4} | {'Naam':30} | {'Bedrijf':20} | Laatste opvolging"
    sep = "-" * len(header)
    print("=" * len(header))
    print("Studenten en meest recente opvolging".center(len(header)))
    print("=" * len(header))
    print(header)
    print(sep)
    if not students:
        print("(geen studenten gevonden)")
    else:
        for idx, st in enumerate(students, start=1):
            sid = getattr(st, "id", "?")
            name = f"{st.voornaam} {st.naam}"
            company = st.bedrijf or ""
            last = get_last_opvolging_date(getattr(st, "id"))
            last_str = last or "N.v.t."
            print(f"{idx:3d} | {str(sid):4s} | {name:30s} | {company:20s} | {last_str}")
    print(sep)
    render_main_options_text()


def render_students_rich(console: Any, students: List[object]) -> None:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3, justify="right")
    table.add_column("ID", style="cyan", width=6)
    table.add_column("Naam", style="green")
    table.add_column("Bedrijf", style="yellow")
    table.add_column("Laatste opvolging", style="white", justify="center")

    if not students:
        table.add_row("", "", "(geen studenten gevonden)", "", "")
    else:
        for idx, st in enumerate(students, start=1):
            sid = getattr(st, "id", "?")
            name = f"{st.voornaam} {st.naam}"
            company = st.bedrijf or ""
            last = get_last_opvolging_date(getattr(st, "id"))
            last_str = last or "N.v.t."
            table.add_row(str(idx), str(sid), name, company, last_str)

    title = Text("Studenten en meest recente opvolging", style="bold white on blue")
    console.print(Panel(Align.center(title), expand=True))
    console.print(table)
    console.print()
    render_main_options_rich(console)


# ------------------------------
# Business helpers
# ------------------------------
def get_last_opvolging_date(student_id: int) -> Optional[str]:
    """
    Geef de 'datum' van de meest recente Opvolging terug voor `student_id`,
    of None wanneer er geen records zijn.
    """
    try:
        ops = OpvolgingRepository.list_for_student(student_id)
    except Exception:
        return None
    if not ops:
        return None
    last = ops[-1]
    return getattr(last, "datum", None)


def add_opvolging_for_student(student: object, console: Any = None) -> bool:
    """
    Interactieve routine om een opvolging toe te voegen voor `student`.
    Returns True when a new opvolging was created, False otherwise.
    """
    # Vraag datum (ENTER => vandaag)
    datum = ask_date(console)
    # Vraag type
    type_input = ask_type(console)
    # Vraag omschrijving
    oms_val = ask_omschrijving(console)

    data = {
        "datum": datum,
        "type": type_input,
        "omschrijving": oms_val,
        "student": getattr(student, "id"),
    }

    try:
        new_op = OpvolgingRepository.create(data)
        if _HAS_RICH and console is not None:
            console.print(Panel(f"Opvolging succesvol toegevoegd (id={getattr(new_op, 'id', '?')}).", title="Succes", style="green"))
        else:
            print(f"Opvolging succesvol toegevoegd (id={getattr(new_op, 'id', '?')}).")
        return True
    except Exception as exc:
        if _HAS_RICH and console is not None:
            console.print(Panel(f"Fout bij toevoegen van opvolging: {exc}", title="Fout", style="red"))
        else:
            print("Fout bij toevoegen van opvolging:", exc)
        return False


def delete_opvolging_for_student(student: object, console: Any = None) -> bool:
    """
    Interactieve routine om een opvolging van `student` te verwijderen.
    Returns True when a deletion occurred, False otherwise.
    """
    try:
        ops = OpvolgingRepository.list_for_student(getattr(student, "id"))
    except Exception as exc:
        if _HAS_RICH and console is not None:
            console.print(Panel(f"Fout bij ophalen van opvolgingen: {exc}", title="Fout", style="red"))
        else:
            print("Fout bij ophalen van opvolgingen:", exc)
        return False

    if not ops:
        if _HAS_RICH and console is not None:
            console.print(Panel("(geen opvolgingen gevonden)", title="Opvolgingen", style="dim"))
        else:
            print("(geen opvolgingen gevonden)")
        return False

    # Toon lijst met opvolgingen en laat selectie maken
    if _HAS_RICH and console is not None:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=3, justify="right")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Datum", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Omschrijving", style="white")
        for i, o in enumerate(ops, start=1):
            table.add_row(str(i), str(getattr(o, "id", "?")), str(getattr(o, "datum", "")), str(getattr(o, "type", "")), str(getattr(o, "omschrijving", "")))
        console.print(Panel(table, title="Kies te verwijderen opvolging"))
        # Ask for index
        while True:
            try:
                choice = Prompt.ask("Voer nummer van opvolging om te verwijderen (of 'c' om te annuleren)")
            except Exception:
                choice = input("Voer nummer van opvolging om te verwijderen (of 'c' om te annuleren): ").strip()
            if not choice:
                continue
            if choice.lower() == "c":
                return False
            try:
                idx = int(choice)
            except Exception:
                console.print("[red]Ongeldige invoer, voer een nummer of 'c' in.[/red]")
                continue
            if idx < 1 or idx > len(ops):
                console.print(f"[red]Kies een nummer tussen 1 en {len(ops)}.[/red]")
                continue
            selected = ops[idx - 1]
            # Confirm deletion
            try:
                confirm = Prompt.ask(f"Weet je zeker dat je opvolging id={getattr(selected,'id','?')} wilt verwijderen? (j/n)", choices=["j", "n"], default="n")
            except Exception:
                confirm = input(f"Weet je zeker dat je opvolging id={getattr(selected,'id','?')} wilt verwijderen? (j/n): ").strip().lower()
            if confirm.lower().startswith("j"):
                try:
                    success = OpvolgingRepository.delete(getattr(selected, "id"))
                    if success:
                        console.print(Panel("Opvolging verwijderd.", title="Succes", style="green"))
                        return True
                    else:
                        console.print(Panel("Opvolging kon niet verwijderd worden.", title="Fout", style="red"))
                        return False
                except Exception as exc:
                    console.print(Panel(f"Fout bij verwijderen: {exc}", title="Fout", style="red"))
                    return False
            else:
                return False
    else:
        # Plain text path
        print("Kies te verwijderen opvolging:")
        for i, o in enumerate(ops, start=1):
            print(f"  {i:2d}. ID={getattr(o,'id','?')}, Datum={getattr(o,'datum','')}, Type={getattr(o,'type','')}, Omschrijving={getattr(o,'omschrijving','')}")
        while True:
            choice = input("Voer nummer van opvolging om te verwijderen (of 'c' om te annuleren): ").strip()
            if not choice:
                continue
            if choice.lower() == "c":
                return False
            try:
                idx = int(choice)
            except Exception:
                print("Ongeldige invoer, voer een nummer of 'c' in.")
                continue
            if idx < 1 or idx > len(ops):
                print(f"Kies een nummer tussen 1 en {len(ops)}.")
                continue
            selected = ops[idx - 1]
            confirm = input(f"Weet je zeker dat je opvolging id={getattr(selected,'id','?')} wilt verwijderen? (j/n): ").strip().lower()
            if confirm.startswith("j"):
                try:
                    success = OpvolgingRepository.delete(getattr(selected, "id"))
                    if success:
                        print("Opvolging verwijderd.")
                        return True
                    else:
                        print("Opvolging kon niet verwijderd worden.")
                        return False
                except Exception as exc:
                    print("Fout bij verwijderen:", exc)
                    return False
            else:
                return False


# ------------------------------
def edit_opvolging_for_student(student: object, console: Any = None) -> bool:
    """
    Interactieve routine om een bestaande opvolging te bewerken.
    Returns True when a modification occurred, False otherwise.
    """
    try:
        ops = OpvolgingRepository.list_for_student(getattr(student, "id"))
    except Exception as exc:
        if _HAS_RICH and console is not None:
            console.print(Panel(f"Fout bij ophalen van opvolgingen: {exc}", title="Fout", style="red"))
        else:
            print("Fout bij ophalen van opvolgingen:", exc)
        return False

    if not ops:
        if _HAS_RICH and console is not None:
            console.print(Panel("(geen opvolgingen gevonden)", title="Opvolgingen", style="dim"))
        else:
            print("(geen opvolgingen gevonden)")
        return False

    # Toon lijst met opvolgingen en laat selectie maken
    if _HAS_RICH and console is not None:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", width=3, justify="right")
        table.add_column("ID", style="cyan", width=6)
        table.add_column("Datum", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Omschrijving", style="white")
        for i, o in enumerate(ops, start=1):
            table.add_row(str(i), str(getattr(o, "id", "?")), str(getattr(o, "datum", "")), str(getattr(o, "type", "")), str(getattr(o, "omschrijving", "")))
        console.print(Panel(table, title="Kies te bewerken opvolging"))
        # Ask for index
        while True:
            try:
                choice = Prompt.ask("Voer nummer van opvolging om te bewerken (of 'c' om te annuleren)")
            except Exception:
                choice = input("Voer nummer van opvolging om te bewerken (of 'c' om te annuleren): ").strip()
            if not choice:
                continue
            if choice.lower() == "c":
                return False
            try:
                idx = int(choice)
            except Exception:
                console.print("[red]Ongeldige invoer, voer een nummer of 'c' in.[/red]")
                continue
            if idx < 1 or idx > len(ops):
                console.print(f"[red]Kies een nummer tussen 1 en {len(ops)}.[/red]")
                continue
            selected = ops[idx - 1]

            # Datum (prefilled)
            try:
                current_datum = str(getattr(selected, "datum", "") or "")
                new_datum = Prompt.ask("  Datum (YYYY-MM-DD)", default=current_datum)
            except Exception:
                new_datum = input(f"  Datum (YYYY-MM-DD) [{getattr(selected,'datum','')}]: ").strip() or getattr(selected, "datum", "")
            new_datum_norm = validate_date_str(new_datum)
            if new_datum_norm is None:
                console.print("[red]Ongeldige datum. Bewerking afgebroken.[/red]") if _HAS_RICH and console is not None else print("Ongeldige datum. Bewerking afgebroken.")
                return False

            # Type (prefilled)
            try:
                current_type = str(getattr(selected, "type", "contact") or "contact")
                new_type = Prompt.ask("  Type", choices=["contact", "controle"], default=current_type)
            except Exception:
                new_type = input(f"  Type ('contact' of 'controle') [{getattr(selected,'type','contact')}]: ").strip() or getattr(selected, "type", "contact")
            if new_type not in ("contact", "controle"):
                console.print("[red]Ongeldig type. Bewerking afgebroken.[/red]") if _HAS_RICH and console is not None else print("Ongeldig type. Bewerking afgebroken.")
                return False

            # Omschrijving (prefilled)
            try:
                current_oms = str(getattr(selected, "omschrijving", "") or "")
                new_oms = Prompt.ask("  Omschrijving (optioneel)", default=current_oms)
            except Exception:
                new_oms = input(f"  Omschrijving (optioneel) [{getattr(selected,'omschrijving','') or ''}]: ").strip()
            new_oms_val = new_oms if new_oms else None

            # Perform update
            try:
                updated = OpvolgingRepository.update(getattr(selected, "id"), {"datum": new_datum_norm, "type": new_type, "omschrijving": new_oms_val})
                if updated:
                    if _HAS_RICH and console is not None:
                        console.print(Panel("Opvolging bijgewerkt.", title="Succes", style="green"))
                    else:
                        print("Opvolging bijgewerkt.")
                    return True
                else:
                    if _HAS_RICH and console is not None:
                        console.print(Panel("Opvolging niet gevonden.", title="Fout", style="red"))
                    else:
                        print("Opvolging niet gevonden.")
                    return False
            except Exception as exc:
                if _HAS_RICH and console is not None:
                    console.print(Panel(f"Fout bij bijwerken: {exc}", title="Fout", style="red"))
                else:
                    print("Fout bij bijwerken:", exc)
                return False
    else:
        # Plain text path
        print("Kies te bewerken opvolging:")
        for i, o in enumerate(ops, start=1):
            print(f"  {i:2d}. ID={getattr(o,'id','?')}, Datum={getattr(o,'datum','')}, Type={getattr(o,'type','')}, Omschrijving={getattr(o,'omschrijving','')}")
        while True:
            choice = input("Voer nummer van opvolging om te bewerken (of 'c' om te annuleren): ").strip()
            if not choice:
                continue
            if choice.lower() == "c":
                return False
            try:
                idx = int(choice)
            except Exception:
                print("Ongeldige invoer, voer een nummer of 'c' in.")
                continue
            if idx < 1 or idx > len(ops):
                print(f"Kies een nummer tussen 1 en {len(ops)}.")
                continue
            selected = ops[idx - 1]
            # prompt fields
            new_datum = input(f"  Datum (YYYY-MM-DD) [{getattr(selected,'datum','')}]: ").strip() or getattr(selected, "datum", "")
            new_datum_norm = validate_date_str(new_datum)
            if new_datum_norm is None:
                print("Ongeldige datum. Bewerking afgebroken.")
                return False
            new_type = input(f"  Type ('contact' of 'controle') [{getattr(selected,'type','contact')}]: ").strip() or getattr(selected, "type", "contact")
            if new_type not in ("contact", "controle"):
                print("Ongeldig type. Bewerking afgebroken.")
                return False
            new_oms = input(f"  Omschrijving (optioneel) [{getattr(selected,'omschrijving','') or ''}]: ").strip()
            new_oms_val = new_oms if new_oms else None
            try:
                updated = OpvolgingRepository.update(getattr(selected, "id"), {"datum": new_datum_norm, "type": new_type, "omschrijving": new_oms_val})
                if updated:
                    print("Opvolging bijgewerkt.")
                    return True
                else:
                    print("Opvolging niet gevonden.")
                    return False
            except Exception as exc:
                print("Fout bij bijwerken:", exc)
                return False
# ------------------------------
# Student detail screen (keeps open until 'b')
# ------------------------------
def student_detail_loop(student: object, console: Any = None) -> None:
    """
    Show student detail and actions in a loop until user presses 'b'.
    Works with both Rich (console provided) and plain-text (console None).
    """
    while True:
        # Render header + opvolgingen
        if _HAS_RICH and console is not None:
            # Clear and render rich detail
            try:
                console.clear()
            except Exception:
                pass
            title = Text(f"Details student: {student.voornaam} {student.naam}", style="bold white on green")
            console.print(Panel(title, expand=True))
            info_table = Table(show_header=False, box=None)
            info_table.add_column(justify="right", style="bold")
            info_table.add_column()
            info_table.add_row("ID", str(getattr(student, "id", "?")))
            info_table.add_row("Bedrijf", student.bedrijf or "-")
            info_table.add_row("ACE project", student.aceproject or "-")
            info_table.add_row("Opvolgingsdocument", student.opvolgingsdocument or "-")
            console.print(info_table)
            console.print()

            # Opvolgingen tabel
            ops = OpvolgingRepository.list_for_student(getattr(student, "id"))
            if not ops:
                console.print(Panel("(geen opvolgingen gevonden)", title="Opvolgingen", style="dim"))
            else:
                ops_table = Table(show_header=True, header_style="bold magenta")
                ops_table.add_column("#", width=3, justify="right")
                ops_table.add_column("ID", style="cyan", width=6)
                ops_table.add_column("Datum", style="green")
                ops_table.add_column("Type", style="yellow")
                ops_table.add_column("Omschrijving", style="white")
                for i, o in enumerate(ops, start=1):
                    ops_table.add_row(
                        str(i),
                        str(getattr(o, "id", "?")),
                        str(getattr(o, "datum", "")),
                        str(getattr(o, "type", "")),
                        str(getattr(o, "omschrijving", "")),
                    )
                console.print(Panel(ops_table, title="Opvolgingen"))

            # Actions prompt
            choice = prompt_student_action_rich(console)
        else:
            # Plain text rendering
            print("=" * 80)
            print("Student:".ljust(12), f"{student.voornaam} {student.naam}")
            print("ID:".ljust(12), getattr(student, "id", "?"))
            print("Bedrijf:".ljust(12), student.bedrijf or "-")
            print("ACE project:".ljust(12), student.aceproject or "-")
            print("Opvolgingsdocument:".ljust(12), student.opvolgingsdocument or "-")
            print("-" * 80)
            print("Opvolgingen:")
            ops = OpvolgingRepository.list_for_student(getattr(student, "id"))
            if not ops:
                print("  (geen opvolgingen gevonden)")
            else:
                for i, o in enumerate(ops, start=1):
                    oms = getattr(o, "omschrijving", "")
                    print(f"  {i:2d}. ID={getattr(o,'id','?')}, Datum={getattr(o,'datum', '')}, Type={getattr(o,'type','')}, Omschrijving={oms}")
            print("-" * 80)
            choice = prompt_student_action_text()

        # Handle choice
        if not choice or choice.lower() == "b":
            # Clear rich screen before returning
            if _HAS_RICH and console is not None:
                try:
                    console.clear()
                except Exception:
                    pass
            return

        if choice == "1":
            # Placeholder edit student
            if _HAS_RICH and console is not None:
                console.print(Panel("Wijzig studentgegevens: nog niet geïmplementeerd.", title="Placeholder", style="yellow"))
                Prompt.ask("Druk op Enter om terug te keren", default="")
                try:
                    console.clear()
                except Exception:
                    pass
            else:
                print("Wijzig studentgegevens: nog niet geïmplementeerd.")
                input("Druk op Enter om terug te keren...")
            continue

        if choice == "2":
            # Add opvolging and remain in detail view
            added = add_opvolging_for_student(student, console if _HAS_RICH else None)
            if _HAS_RICH and console is not None:
                Prompt.ask("Druk op Enter om terug te keren", default="")
                try:
                    console.clear()
                except Exception:
                    pass
            else:
                input("Druk op Enter om terug te keren...")
            # loop continues, showing updated list
            continue

        if choice == "3":
            # Delete an opvolging and remain in the detail view
            deleted = delete_opvolging_for_student(student, console if _HAS_RICH else None)
            if _HAS_RICH and console is not None:
                Prompt.ask("Druk op Enter om terug te keren", default="")
                try:
                    console.clear()
                except Exception:
                    pass
            else:
                input("Druk op Enter om terug te keren...")
            # loop continues, showing updated list
            continue

        if choice == "4":
            # Edit an opvolging and remain in the detail view
            edited = edit_opvolging_for_student(student, console if _HAS_RICH else None)
            if _HAS_RICH and console is not None:
                Prompt.ask("Druk op Enter om terug te keren", default="")
                try:
                    console.clear()
                except Exception:
                    pass
            else:
                input("Druk op Enter om terug te keren...")
            # loop continues to show updated list
            continue

        # Unknown option
        if _HAS_RICH and console is not None:
            console.print("[red]Onbekende optie.[/red]")
            Prompt.ask("Druk op Enter om terug te keren", default="")
            try:
                console.clear()
            except Exception:
                pass
        else:
            print("Onbekende optie.")
            input("Druk op Enter om terug te keren...")


# ------------------------------
# Prompts for actions (shared)
# ------------------------------
def prompt_student_action_text() -> str:
    for line in STUDENT_ACTIONS:
        print(line)
    print()
    return input("Kies actie (nummer of 'b' om terug te keren): ").strip()


def prompt_student_action_rich(console: Any) -> str:
    actions = Text()
    actions.append(STUDENT_ACTIONS[0] + "\n", style="bold")
    for line in STUDENT_ACTIONS[1:]:
        actions.append(line + "\n")
    console.print(Panel(actions, subtitle="Gebruik", expand=False))
    try:
        return Prompt.ask("Kies actie (nummer of 'b' om terug te keren)")
    except Exception:
        return input("Kies actie (nummer of 'b' om terug te keren): ").strip()


# ------------------------------
# Main loop
# ------------------------------
def main() -> None:
    if _HAS_RICH:
        console = Console()
    else:
        console = None

    # Start main interactive loop
    while True:
        # Load students
        try:
            students: List[object] = StudentRepository.list_all()  # type: ignore[arg-type]
        except Exception as exc:
            if _HAS_RICH and console is not None:
                console.print("[red]Fout bij laden van studenten uit de database:[/red]")
                console.print(f"[red]{exc}[/red]")
            else:
                print("Fout bij laden van studenten uit de database:")
                print(" ", exc)
            return

        # Render students list
        if _HAS_RICH and console is not None:
            try:
                console.clear()
            except Exception:
                pass
            render_students_rich(console, students)
            try:
                choice = Prompt.ask("Kies optie (nummer of 'q' om te stoppen)")
            except Exception:
                choice = input("Kies optie (nummer of 'q' om te stoppen): ")
        else:
            render_students_text(students)
            choice = input("Kies optie (nummer of 'q' om te stoppen): ")

        if not choice:
            continue
        if choice.strip().lower() == "q":
            if _HAS_RICH and console is not None:
                console.print(Panel(Text("Tot ziens.", style="bold"), expand=False))
            else:
                print("Tot ziens.")
            return

        # Numeric selection -> student detail
        try:
            num = int(choice)
        except ValueError:
            if _HAS_RICH and console is not None:
                console.print("[red]Onbekende optie. Voer een nummer of 'q' in.[/red]")
            else:
                print("Onbekende optie. Voer een nummer of 'q' in.")
            continue

        if num < 1 or num > len(students):
            if _HAS_RICH and console is not None:
                console.print(f"[red]Ongeldig nummer: {num}. Kies een nummer tussen 1 en {len(students)}.[/red]")
            else:
                print(f"Ongeldig nummer: {num}. Kies een nummer tussen 1 en {len(students)}.")
            continue

        student = students[num - 1]
        # Enter student detail loop (stays there until user presses 'b')
        student_detail_loop(student, console if _HAS_RICH else None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if _HAS_RICH:
            try:
                Console().print("\n[bold]Afgebroken door gebruiker.[/bold]")
            except Exception:
                print("\nAfgebroken door gebruiker.")
        else:
            print("\nAfgebroken door gebruiker.")