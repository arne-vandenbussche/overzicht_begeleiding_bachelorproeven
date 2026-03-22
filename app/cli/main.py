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
        if use_rich and console is not None:
            show_students_screen_rich(console)
            try:
                choice = Prompt.ask("Kies optie (nummer of 'q' om te stoppen)")
            except Exception:
                # Fallback naar simple input als Prompt faalt
                choice = input("Kies optie (nummer of 'q' om te stoppen): ")
        else:
            show_students_screen_text()
            choice = input("Kies optie (nummer of 'q' om te stoppen): ")

        if not choice:
            continue
        if choice.strip().lower() == "q":
            if use_rich and console is not None:
                console.print(Panel(Text("Tot ziens.", style="bold"), expand=False))
            else:
                print("Tot ziens.")
            return

        # Probeer numerieke keuze
        try:
            num = int(choice)
            # Placeholder gedrag: toon melding en wacht op Enter
            if use_rich and console is not None:
                console.print()
                console.print(Panel(f"Je hebt student #{num} gekozen.\n\nHet tonen van de opvolgingen is nog niet geïmplementeerd.", title="Opgelet", style="yellow"), justify="center")
                try:
                    Prompt.ask("Druk op Enter om terug te keren", default="")
                except Exception:
                    input("Druk op Enter om terug te keren...")
                # Opruimen / scherm wissen voor een nettere terugkeer
                try:
                    console.clear()
                except Exception:
                    pass
            else:
                print(f"Je hebt student #{num} gekozen.")
                print("Het tonen van de opvolgingen van deze student is nog niet geïmplementeerd.")
                input("Druk op Enter om terug te keren...")
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