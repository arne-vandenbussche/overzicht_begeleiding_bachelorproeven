# overzicht_begeleiding_bachelorproeven

Eenvoudige applicatie om te beheren en bekijken welke contacten en opvolging er geweest zijn in het kader van de begeleiding van bachelorproeven.

Deze README geeft Nederlandstalige instructies voor installatie, configuratie, gebruik en ontwikkeling.

---

## Inhoud van dit project (kort)

- `app/` - applicatiecode
  - `app/db/` - SQLAlchemy engine en session setup
  - `app/models/` - ORM-modellen (`Student`, `Opvolging`)
  - `app/repository/` - repositorylaag: applicatie API voor CRUD
  - `app/cli/` - interactieve menu-gestuurde CLI
- `run.py` - eenvoudige entrypoint om de interactieve applicatie te starten
- `.env.example` - voorbeeld configuratiebestand voor omgevingvariabelen
- `requirements.txt` - minimale runtime dependencies
- `opvolging_ddl.sql` - originele DDL met tabeldefinities

---

## Vereisten

- Python 3.10+ (of een recentere 3.x-release die SQLAlchemy 1.4+/2.0 ondersteunt)
- Virtuele omgeving (aanbevolen)
- Runtime dependencies:
  - `SQLAlchemy` (ORM)
  - `python-dotenv` (optioneel, voor het automatisch laden van `.env`)

De exacte dependencies staan in `requirements.txt`.

---

## Snelle start (lokale installatie)

1. Maak en activeer een virtuele omgeving (aanbevolen)

   macOS / Linux:
       python -m venv .venv
       source .venv/bin/activate

   Windows (PowerShell):
       python -m venv .venv
       .\.venv\Scripts\Activate.ps1

2. Installeer de dependencies

       pip install -r requirements.txt

3. Kopieer `.env.example` naar `.env` en pas aan indien nodig

   - De belangrijkste variabele is `SQLALCHEMY_DATABASE_URL`.
   - Een veelgebruikte waarde voor een file-based SQLite in de projectmap:
       SQLALCHEMY_DATABASE_URL=sqlite:///./opvolging.db

   - Voor absolute paden (macOS/Linux):
       SQLALCHEMY_DATABASE_URL=sqlite:////Users/jou/path/opvolging.db

   - Voor Windows (voorbeeld):
       SQLALCHEMY_DATABASE_URL=sqlite:///C:/pad/naar/opvolging.db

   - Voor tests (in-memory):
       SQLALCHEMY_DATABASE_URL=sqlite:///:memory:

4. (Optioneel) Initialiseer de database (maakt tabellen aan op basis van modellen)

       python -c "from app.db.session import init_db; init_db()"

   Dit is vooral nodig als je een nieuwe lege SQLite-file gebruikt.

5. Start de applicatie (interactive CLI)

       python run.py

   - De applicatie toont het eerste scherm: een lijst van studenten met de datum van de meest recente opvolging.
   - Navigeer via de toetsopties die op het scherm worden weergegeven (menu-gestuurd; geen CLI-argumenten nodig).

---

## Beschrijving van de CLI (huidige status)

Het CLI-UI is menu-gestuurd en start zonder command-line opties. De huidige eerste schermfunctionaliteit:

- Toon alle studenten in de database met:
  - volgnummer in de lijst
  - student-id
  - voornaam + naam
  - bedrijf (indien aanwezig)
  - datum van de meest recente opvolging (of "N/A")
- Opties:
  - invoeren van een getal: placeholder die aangeeft welke student gekozen werd (de detailweergave wordt later geïmplementeerd)
  - `q` om te stoppen

De code voor het eerste scherm staat in `app/cli/main.py`. Als je de feature "bekijk opvolgingen voor een student" wilt implementeren, dan is dat de volgende stap.

---

## Documentatie van belangrijke onderdelen

- `app/db/session.py`
  - Maakt `engine`, `SessionLocal` en `Base` aan.
  - Biedt `session_scope()` contextmanager en `init_db()` helper.
  - Leest optioneel `.env` voor `SQLALCHEMY_DATABASE_URL`.

- `app/models/models.py`
  - ORM-definities voor `STUDENT` en `OPVOLGING`.
  - Classmethod helpers (`insert`, `get_by_id`, `get_all`, `update`) die werken met een `Session`.
  - Typing gebruikt `TypeVar`-patroon om classmethods subclass-compatibel te houden.

- `app/repository/repository.py`
  - Een eenvoudige repositorylaag die session-management en publiek API aanbiedt.
  - Repository-methoden zijn (nu) `@staticmethod` en delegaten aan model-methoden; zij verzorgen transacties en session lifecycle wanneer nodig.
  - Delete-methoden doen robuuste foutafhandeling met logging en re-raise (niet stil zwijgen).

---

## Ontwikkeling en testen

- Aanbevolen workflows:
  - Maak een aparte virtuele omgeving per project (gebruik `.venv` in projectroot zodat editors die vaak automatisch detecteren).
  - Voor tests kun je een tijdelijke database gebruiken: `sqlite:///:memory:` of een tijdelijke file.

- Veelvoorkomende ontwikkeltaken:
  - Tabellen opnieuw aanmaken:
        python -c "from app.db.session import init_db; init_db()"

  - Start de CLI tijdens ontwikkeling:
        python run.py

- Logging:
  - `run.py` leest `LOG_LEVEL` uit de `.env` (defaults: `INFO`).
  - Voor debugging kun je `LOG_LEVEL=DEBUG` zetten in je `.env`.

---

## Veel voorkomende problemen & oplossingen

- Fout: `ModuleNotFoundError: No module named 'sqlalchemy'` of je IDE laat zien dat `sqlalchemy` niet gevonden wordt.
  - Zorg dat je de dependencies installeert in dezelfde Python-interpreter die je editor/language-server gebruikt.
  - Activeer de virtuele omgeving in je terminal en start de editor opnieuw of configureer de editor om de project-venv te gebruiken.
  - Controleer met:
       python -m pip show SQLAlchemy
       python -c "import sqlalchemy; print(sqlalchemy.__version__)"

- De applicatie start niet of `app.cli.main` kan niet geïmporteerd worden:
  - Controleer of `run.py` vanaf de projectroot wordt gestart (zodat relatieve imports werken).
  - Zorg dat `.env` correct staat en dat `SQLALCHEMY_DATABASE_URL` naar een toegankelijke locatie verwijst.

- Problemen met type-checker / linter (bijv. met je IDE)
  - Sommige types en generics worden gebruikt in `models.py` om subclass-precisie te behouden. Dit kan leiden tot linterwaarschuwingen in oudere setups. Zorg dat de linter de juiste Python-interpreter en typechecker gebruikt.

---

## Conventies en ontwerpkeuzes (kort)

- Model-methoden:
  - Definiëren schema en model-logica; kleine helpers en validaties zijn hier geplaatst.
  - Classmethod-signatures zijn generiek (`TypeVar`) zodat subclass-returntypes correct worden gemodelleerd.

- Repositorylaag:
  - Biedt een stabiele façade en beheert sessies en transacties.
  - Houdt applicatiecode los van direct session-management.

- CLI:
  - Menu-gestuurd, geen commandline flags. Dit faciliteert interactiviteit en eenvoudige navigatie voor gebruikers die commandline-argumenten niet willen of nodig hebben.

---

## Bijdragen

- Fork het project en maak een feature-branch.
- Zorg voor duidelijke commitberichten.
- Open een pull request met een beschrijving van de wijziging en relevante tests.
- Voordat je PR indient: voer de test- en lint-stappen uit (indien aanwezig).

---

## Licentie

- Voeg hier je licentie toe (indien gewenst). Standaard staat er geen expliciete licentie in dit repository. Als je wilt dat ik een licentiebestand (`LICENSE`) toevoeg (bijv. MIT of Apache 2.0), laat het weten.

---

Als je wilt, kan ik:
- De detailweergave van opvolgingen voor een gekozen student implementeren (volgende CLI-scherm).
- Unit-tests en een `dev-requirements.txt` toevoegen met tools zoals `pytest`.
- Een kleine `Makefile` of nuttige `scripts/` toevoegen voor veelvoorkomende taken (venv setup, db init, lint, tests).
