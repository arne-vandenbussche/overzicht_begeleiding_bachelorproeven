#!/usr/bin/env python3
"""
CLI entry point for overzicht_begeleiding_bachelorproeven.

This script shows a first screen listing all students together with the date
of the most recent "opvolging" (follow-up) for each student.

Notes:
- This is intentionally only the first screen. If the user chooses to view the
  detailed opvolgingen for a student the CLI will show a placeholder message
  ("Not implemented yet") and return to the main screen.
- The code uses the repository layer (`app.repository.repository`) as the public
  API for data access.
"""

from typing import List, Optional

from app.repository.repository import StudentRepository, OpvolgingRepository


def format_row(idx: int, student: object, last_date: Optional[str]) -> str:
    """Return a formatted single-line representation for a student row."""
    id_str = str(student.id) if getattr(student, "id", None) is not None else "?"
    name = f"{student.voornaam} {student.naam}"
    company = student.bedrijf or ""
    last = last_date or "N/A"
    return f"{idx:3d} | {id_str:4s} | {name:30s} | {company:20s} | Last: {last}"


def get_last_opvolging_date(student_id: int) -> Optional[str]:
    """
    Return the datum (string) of the most recent Opvolging for `student_id`,
    or None when there are no records.

    Implementation detail: the repository returns Opvolging records ordered by
    `datum` (ascending) so the latest is the last element if any.
    """
    try:
        ops = OpvolgingRepository.list_for_student(student_id)
    except Exception:
        # Don't fail the whole screen because of a single student's follow-ups.
        return None

    if not ops:
        return None
    # ops is a concrete list; the last element is the most recent if ordering is by datum ascending
    last = ops[-1]
    return getattr(last, "datum", None)


def show_students_screen(limit: Optional[int] = None) -> None:
    """
    Fetch students and render the main screen.

    :param limit: optional maximum number of students to show
    """
    try:
        students: List[object] = StudentRepository.list_all(limit=limit)  # type: ignore[arg-type]
    except Exception as exc:
        print("Failed to load students from the database:")
        print("  ", exc)
        return

    print("=" * 90)
    print("Students and most recent opvolging")
    print("=" * 90)
    header = " #  | ID   | Name                           | Company              | Summary"
    print(header)
    print("-" * 90)

    if not students:
        print("(no students found)")
    else:
        for idx, st in enumerate(students, start=1):
            last_date = get_last_opvolging_date(getattr(st, "id"))
            print(format_row(idx, st, last_date))

    print("-" * 90)
    print("Options:")
    print("  [number]  - (placeholder) view opvolgingen for the chosen student (not implemented yet)")
    print("  q         - quit")
    print()


def main() -> None:
    """
    Simple interactive loop for the first screen.

    The CLI currently only implements the first screen and a placeholder for
    the "view opvolgingen" action.
    """
    while True:
        show_students_screen()
        choice = input("Enter option (number or 'q' to quit): ").strip()
        if not choice:
            continue
        if choice.lower() == "q":
            print("Goodbye.")
            return
        # Try to parse a number; we do not show details yet.
        try:
            num = int(choice)
            print(f"You selected student #{num}.")
            print("Showing the student's opvolgingen is not implemented yet.")
            input("Press Enter to return to the main screen...")
            continue
        except ValueError:
            print("Unrecognized option. Please enter a number or 'q'.")
            continue


if __name__ == "__main__":
    main()