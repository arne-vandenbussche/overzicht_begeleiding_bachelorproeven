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
    print("Opties:")
    print("  [nummer] - Bekijk opvolgingen voor de gekozen student (nog niet geïmplementeerd)")
    print("  q        - Afsluiten")
    print()


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
    opts = Text()
    opts.append("Opties:\n", style="bold")
    opts.append("  [nummer] - Bekijk opvolgingen voor de gekozen student (nog niet geïmplementeerd)\n")
    opts.append("  q        - Afsluiten\n")
    console.print(Panel(opts, subtitle="Gebruik", expand=False))


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
    """Tekstfallback: toon studentgegevens en lijst met opvolgingen, en een menu met acties (placeholders)."""
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
    print("Acties:")
    print("  1 - Wijzig studentgegevens")
    print("  2 - Voeg opvolging toe")
    print("  3 - Verwijder opvolging")
    print("  4 - Bewerk opvolging")
    print("  b - Terug naar hoofdscherm")
    print()
    choice = input("Kies actie (nummer of 'b' om terug te keren): ").strip()
    if not choice or choice.lower() == "b":
        return
    if choice == "1":
        print("Wijzig studentgegevens: nog niet geïmplementeerd (placeholder).")
        input("Druk op Enter om terug te keren...")
    elif choice == "2":
        print("Opvolging toevoegen: nog niet geïmplementeerd (placeholder).")
        input("Druk op Enter om terug te keren...")
    elif choice == "3":
        print("Opvolging verwijderen: nog niet geïmplementeerd (placeholder).")
        input("Druk op Enter om terug te keren...")
    elif choice == "4":
        print("Opvolging bewerken: nog niet geïmplementeerd (placeholder).")
        input("Druk op Enter om terug te keren...")
    else:
        print("Onbekende optie.")
        input("Druk op Enter om terug te keren...")


def _render_student_detail_rich(console: "Console", student: object) -> None:
    """Rich-weergave: toon studentgegevens en lijst met opvolgingen en menu met acties (placeholders)."""
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

    # Acties (placeholders)
    actions = Text()
    actions.append("Acties:\n", style="bold")
    actions.append("  1 - Wijzig studentgegevens\n")
    actions.append("  2 - Voeg opvolging toe\n")
    actions.append("  3 - Verwijder opvolging\n")
    actions.append("  4 - Bewerk opvolging\n")
    actions.append("  b - Terug naar hoofdscherm\n")
    console.print(Panel(actions, subtitle="Gebruik", expand=False))

    try:
        choice = Prompt.ask("Kies actie (nummer of 'b' om terug te keren)")
    except Exception:
        choice = input("Kies actie (nummer of 'b' om terug te keren): ")

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
    elif choice == "2":
        console.print(Panel("Opvolging toevoegen: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
        Prompt.ask("Druk op Enter om terug te keren", default="")
    elif choice == "3":
        console.print(Panel("Opvolging verwijderen: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
        Prompt.ask("Druk op Enter om terug te keren", default="")
    elif choice == "4":
        console.print(Panel("Opvolging bewerken: nog niet geïmplementeerd (placeholder).", title="Placeholder", style="yellow"))
        Prompt.ask("Druk op Enter om terug te keren", default="")
    else:
        console.print("[red]Onbekende optie.[/red]")
        Prompt.ask("Druk op Enter om terug te keren", default="")

    try:
        console.clear()
    except Exception:
        pass


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