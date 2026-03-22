#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry point using Rich for overzicht_begeleiding_bachelorproeven.

Dit vervangt de eenvoudige tekst-output met een rijkere tabelweergave (kleur,
uitlijning) met behulp van de `rich` library. Het gedrag blijft hetzelfde:
- Toon lijst met studenten en de datum van hun meest recente opvolging.
- Laat de gebruiker een nummer kiezen (placeholder: detailweergave niet geïmplementeerd).
- 'q' sluit de applicatie.

Als `rich` niet beschikbaar is, valt de CLI terug op een eenvoudige tekstweergave
met dezelfde interactie.
"""

from __future__ import annotations

from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.align import Align
    from rich.text import Text
except Exception:
    Console = None  # type: ignore

from app.repository.repository import StudentRepository, OpvolgingRepository
from datetime import date

# UI text constants (centralized so rendering / prompts share the same strings)
MAIN_OPTIONS = [
    "Opties:",
    "  [nummer] - Bekijk opvolgingen voor de gekozen student (nog niet geïmplementeerd)",
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


def get_last_opvolging_date(student_id: int) -> Optional[str]:
    """
    Geef de 'datum' van de meest recente Opvolging terug voor `student_id`,
    of None wanneer er geen records zijn.
    """
    try:
        ops = OpvolgingRepository.list_for_student(student_id)
    except Exception:
        # Falen bij ophalen van opvolgingen mag het hoofdscherm niet breken.
        return None

    if not ops:
        return None
    last = ops[-1]
    return getattr(last, "datum", None)


def validate_date_str(s: str) -> Optional[str]:
    """
    Validate a date string in ISO format YYYY-MM-DD.

    Returns the normalized YYYY-MM-DD string when valid, otherwise returns None.
    This uses datetime.date.fromisoformat which accepts the ISO date format.
    """
    if not s:
        return None
    try:
        d = date.fromisoformat(s)
        return d.isoformat()
    except Exception:
        return None


# --- Shared UI helpers to avoid duplication ---------------------------------------

def print_main_options_text() -> None:
    """Print the main menu options in the plain-text fallback."""
    for line in MAIN_OPTIONS:
        print(line)
    print()


def render_main_options(console: "Console") -> None:
    """Render the main menu options as a Rich Panel."""
    opts = Text()
    # Use MAIN_OPTIONS constant so the same text is used everywhere
    opts.append(MAIN_OPTIONS[0] + "\n", style="bold")
    for line in MAIN_OPTIONS[1:]:
        opts.append(line + "\n")
    console.print(Panel(opts, subtitle="Gebruik", expand=False))


def prompt_student_action_text() -> str:
    """
    Show the student actions menu (plain-text) and return the user's choice.
    Keeps the same prompts as before but extracted to a single function.
    """
    for line in STUDENT_ACTIONS:
        print(line)
    print()
    return input("Kies actie (nummer of 'b' om terug te keren): ").strip()


def prompt_student_action_rich(console: "Console") -> str:
    """
    Show the student actions menu using Rich and return the user's choice.
    Falls back to regular input if Prompt.ask fails.
    """
    actions = Text()
    # Use STUDENT_ACTIONS so presentation matches the plain-text fallback
    actions.append(STUDENT_ACTIONS[0] + "\n", style="bold")
    for line in STUDENT_ACTIONS[1:]:
        actions.append(line + "\n")
    console.print(Panel(actions, subtitle="Gebruik", expand=False))
    try:
        return Prompt.ask("Kies actie (nummer of 'b' om terug te keren)")
    except Exception:
        return input("Kies actie (nummer of 'b' om terug te keren): ").strip()

# -------------------------------------------------------------------------------



def render_table_text(students: List[object]) -> None:
    """Fallback tekstweergave wanneer Rich niet beschikbaar is."""
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
    print_main_options_text()


def render_table_rich(console: "Console", students: List[object]) -> None:
    """Rich-gebaseerde tabelweergave."""
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
    render_main_options(console)


def show_students_screen_rich(console: "Console", limit: Optional[int] = None) -> None:
    """Laad studenten via de repository en render met rich."""
    try:
        students: List[object] = StudentRepository.list_all(limit=limit)  # type: ignore[arg-type]
    except Exception as exc:
        console.print("[red]Fout bij laden van studenten uit de database:[/red]")
        console.print(f"[red]{exc}[/red]")
        return

    render_table_rich(console, students)


def show_students_screen_text(limit: Optional[int] = None) -> None:
    """Laad studenten via de repository en render als tekst (fallback)."""
    try:
        students: List[object] = StudentRepository.list_all(limit=limit)  # type: ignore[arg-type]
    except Exception as exc:
        print("Fout bij laden van studenten uit de database:")
        print(" ", exc)
        return

    render_table_text(students)


def _render_student_detail_text(student: object) -> None:
    """Tekstfallback: toon studentgegevens en lijst met opvolgingen, en een menu met acties.
    Blijft zichtbaar totdat de gebruiker 'b' kiest.
    """
    while True:
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
        if not choice or choice.lower() == "b":
            return

        if choice == "1":
            print("Wijzig studentgegevens: nog niet geïmplementeerd (placeholder).")
            input("Druk op Enter om terug te keren...")
            # blijf in detail scherm
            continue

        elif choice == "2":
            # Implementatie: voeg een nieuwe Opvolging toe voor deze student, met datumvalidatie
            # Standaard: ENTER = vandaag
            print("Opvolging toevoegen")
            while True:
                datum_in = input("  Datum (YYYY-MM-DD) [ENTER = vandaag]: ").strip()
                if not datum_in:
                    # Gebruik vandaag als standaard
                    datum = date.today().isoformat()
                    print(f"  Standaarddatum gebruikt: {datum}")
                    break
                datum_norm = validate_date_str(datum_in)
                if datum_norm is None:
                    print("  Ongeldige datum. Gebruik het formaat YYYY-MM-DD (bv. 2023-12-31).")
                    continue
                # valide datum verkregen
                datum = datum_norm
                break
            # Als we hier geen datum hebben (één of andere reden), annuleer
            if not (datum):
                input("Druk op Enter om terug te keren...")
                continue
            else:
                # Vraag type en valideer
                while True:
                    type_input = input("  Type ('contact' of 'controle') [verplicht]: ").strip()
                    if type_input in ("contact", "controle"):
                        break
                    print("  Ongeldig type. Voer 'contact' of 'controle' in.")
                # Omschrijving (optioneel, tekstveld)
                oms_txt = input("  Omschrijving (optioneel): ").strip()
                oms_val = oms_txt if oms_txt else None
                data = {
                    "datum": datum,
                    "type": type_input,
                    "omschrijving": oms_val,
                    "student": getattr(student, "id"),
                }
                try:
                    new_op = OpvolgingRepository.create(data)
                    print(f"  Opvolging succesvol toegevoegd (id={getattr(new_op, 'id', '?')}).")
                except Exception as e:
                    print("  Fout bij toevoegen van opvolging:", e)
                input("Druk op Enter om terug te keren...")
                # terug naar de detailweergave (loop opnieuw)
                continue

        elif choice == "3":
            print("Opvolging verwijderen: nog niet geïmplementeerd (placeholder).")
            input("Druk op Enter om terug te keren...")
            continue

        elif choice == "4":
            print("Opvolging bewerken: nog niet geïmplementeerd (placeholder).")
            input("Druk op Enter om terug te keren...")
            continue

        else:
            print("Onbekende optie.")
            input("Druk op Enter om terug te keren...")
            continue


def _render_student_detail_rich(console: "Console", student: object) -> None:
    """Rich-weergave: toon studentgegevens en lijst met opvolgingen en menu met acties.
    Blijft zichtbaar totdat de gebruiker 'b' kiest; na acties keert het scherm terug naar
    hetzelfde student-detail (in plaats van hoofdscherm).
    """
    while True:
        # Studentgegevens
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

        # Opvolgingen
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
                ops_table.add_row(str(i), str(getattr(o, "id", "?")), str(getattr(o, "datum", "")), str(getattr(o, "type", "")), str(getattr(o, "omschrijving", "")))
            console.print(Panel(ops_table, title="Opvolgingen"))

        # Acties
        choice = prompt_student_action_rich(console)

        if not choice or choice.lower() == "b":
            # Clear and return to main screen for nicer UX
            try:
                console.clear()
            except Exception:
                pass
            return

        if choice == "1":
            console.print(Panel("Wijzig studentgegevens: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
            Prompt.ask("Druk op Enter om terug te keren", default="")
            # blijf in detailweergave
            try:
                console.clear()
            except Exception:
                pass
            continue

        elif choice == "2":
            # Interactieve datuminvoer met default vandaag en validatie
            today_str = date.today().isoformat()
            while True:
                try:
                    datum_input = Prompt.ask(f"  Datum (YYYY-MM-DD) [ENTER = {today_str}]", default=today_str)
                except Exception:
                    datum_input = input(f"  Datum (YYYY-MM-DD) [ENTER = {today_str}]: ").strip()
                    if not datum_input:
                        datum_input = today_str
                datum_norm = validate_date_str(datum_input)
                if datum_norm is None:
                    console.print("[red]Ongeldige datum. Gebruik YYYY-MM-DD (bijv. 2023-12-31).[/red]")
                    continue
                datum = datum_norm
                break

            # Type met keuzemogelijkheden
            try:
                type_input = Prompt.ask("  Type", choices=["contact", "controle"], default="contact")
            except Exception:
                while True:
                    type_input = input("  Type ('contact' of 'controle'): ").strip()
                    if type_input in ("contact", "controle"):
                        break
                    console.print("[red]Ongeldig type. Voer 'contact' of 'controle' in.[/red]")

            # Omschrijving (optioneel, tekstveld)
            try:
                oms_txt = Prompt.ask("  Omschrijving (optioneel)", default="")
            except Exception:
                oms_txt = input("  Omschrijving (optioneel): ").strip()
            oms_val = oms_txt if oms_txt else None

            data = {
                "datum": datum,
                "type": type_input,
                "omschrijving": oms_val,
                "student": getattr(student, "id"),
            }
            try:
                new_op = OpvolgingRepository.create(data)
                console.print(Panel(f"Opvolging succesvol toegevoegd (id={getattr(new_op, 'id', '?')}).", title="Succes", style="green"))
            except Exception as e:
                console.print(Panel(f"Fout bij toevoegen van opvolging: {e}", title="Fout", style="red"))
            Prompt.ask("Druk op Enter om terug te keren", default="")
            # blijf in detailweergave - scherm wissen en hertekenen
            try:
                console.clear()
            except Exception:
                pass
            continue

        elif choice == "3":
            console.print(Panel("Opvolging verwijderen: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
            Prompt.ask("Druk op Enter om terug te keren", default="")
            try:
                console.clear()
            except Exception:
                pass
            continue

        elif choice == "4":
            console.print(Panel("Opvolging bewerken: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
            Prompt.ask("Druk op Enter om terug te keren", default="")
            try:
                console.clear()
            except Exception:
                pass
            continue

        else:
            console.print("[red]Onbekende optie.[/red]")
            Prompt.ask("Druk op Enter om terug te keren", default="")
            try:
                console.clear()
            except Exception:
                pass
            continue


def main() -> None:
    """
    Hoofdloop van de CLI. Geen CLI-argumenten — alles gebeurt via menu-keuzes.
    """
    if Console is None:
        # Fallback pad: geen rich beschikbaar
        use_rich = False
        console = None
    else:
        use_rich = True
        console = Console()
        # Probeer het scherm leeg te maken voor betere UX (niet kritisch)
        try:
            console.clear()
        except Exception:
            pass

    while True:
        # Haal studenten op voordat we renderen zodat we bij nummerkeuze direct de juiste student hebben
        try:
            students: List[object] = StudentRepository.list_all()  # type: ignore[arg-type]
        except Exception as exc:
            if use_rich and console is not None:
                console.print("[red]Fout bij laden van studenten uit de database:[/red]")
                console.print(f"[red]{exc}[/red]")
            else:
                print("Fout bij laden van studenten uit de database:")
                print(" ", exc)
            return

        # Render de lijst
        if use_rich and console is not None:
            render_table_rich(console, students)
            try:
                choice = Prompt.ask("Kies optie (nummer of 'q' om te stoppen)")
            except Exception:
                choice = input("Kies optie (nummer of 'q' om te stoppen): ")
        else:
            render_table_text(students)
            choice = input("Kies optie (nummer of 'q' om te stoppen): ")

        if not choice:
            continue
        if choice.strip().lower() == "q":
            if use_rich and console is not None:
                console.print(Panel(Text("Tot ziens.", style="bold"), expand=False))
            else:
                print("Tot ziens.")
            return

        # Probeer numerieke keuze - kaart die naar student detail
        try:
            num = int(choice)
            if num < 1 or num > len(students):
                if use_rich and console is not None:
                    console.print(f"[red]Ongeldig nummer: {num}. Kies een nummer tussen 1 en {len(students)}.[/red]")
                else:
                    print(f"Ongeldig nummer: {num}. Kies een nummer tussen 1 en {len(students)}.")
                continue

            student = students[num - 1]
            # Toon detailweergave met opvolgingen en acties (placeholders)
            if use_rich and console is not None:
                _render_student_detail_rich(console, student)
            else:
                _render_student_detail_text(student)

            # na retour naar hoofdscherm, probeer scherm te wissen voor nettere UX
            if use_rich and console is not None:
                try:
                    console.clear()
                except Exception:
                    pass

            continue
        except ValueError:
            if use_rich and console is not None:
                console.print("[red]Onbekende optie. Voer een nummer of 'q' in.[/red]")
            else:
                print("Onbekende optie. Voer een nummer of 'q' in.")
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Nettere afsluiting bij Ctrl-C
        try:
            if Console is not None:
                Console().print("\n[bold]Afgebroken door gebruiker.[/bold]")
            else:
                print("\nAfgebroken door gebruiker.")
        except Exception:
            pass