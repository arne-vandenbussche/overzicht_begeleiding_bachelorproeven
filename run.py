#!/usr/bin/env python3
"""
Entry point for the 'overzicht_begeleiding_bachelorproeven' application.

Responsibilities:
- Ensure minimal package __init__.py files exist so the `app` package and its subpackages
  are importable in older Python installers / tooling that expect them.
- Load environment variables from a `.env` file if python-dotenv is available.
- Configure basic logging from `LOG_LEVEL` env var.
- Import and start the CLI main loop from `app.cli.main`.

Notes:
- This script does not accept command-line arguments. It starts an interactive menu-driven
  UI (delegated to `app.cli.main.main()`).
- If your environment does not have required libraries (SQLAlchemy, python-dotenv, ...),
  the script prints a helpful message.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Iterable

# --- Helpers for package initialization --------------------------------------------------


def ensure_package_init(package_dirs: Iterable[Path]) -> None:
    """
    Ensure each directory in `package_dirs` has an `__init__.py` file.

    This is safe to call repeatedly; existing files are not overwritten.
    """
    for d in package_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If creation fails, we continue: import may still work via namespace packages.
            continue
        init_file = d / "__init__.py"
        if not init_file.exists():
            try:
                init_file.write_text("# Package initializer created by run.py\n")
            except Exception:
                # Non-fatal: if we can't write, leave it and allow import to try as namespace package.
                pass


def project_root() -> Path:
    """Return the root directory of the project (directory containing this run.py)."""
    return Path(__file__).resolve().parent


# --- Environment & logging -------------------------------------------------------------


def load_dotenv_if_available(env_path: Path) -> None:
    """Try to load env vars from `.env` using python-dotenv if installed; otherwise skip."""
    try:
        from dotenv import load_dotenv

        if env_path.exists():
            load_dotenv(env_path)
    except Exception:
        # python-dotenv not available; rely on environment variables instead.
        pass


def configure_logging() -> None:
    """Configure basic logging using LOG_LEVEL env var (default INFO)."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )


# --- Main runner -----------------------------------------------------------------------


def main() -> None:
    root = project_root()

    # Ensure project root is on sys.path so `import app...` works when running run.py directly.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    # Ensure __init__.py for the main package and subpackages so imports behave consistently.
    # We create them only if missing to be non-invasive.
    package_dirs = [
        root / "app",
        root / "app" / "cli",
        root / "app" / "models",
        root / "app" / "db",
        root / "app" / "repository",
        root / "app" / "config",
    ]
    ensure_package_init(package_dirs)

    # Load .env if present (optional)
    load_dotenv_if_available(root / ".env")

    # Configure logging
    configure_logging()
    logger = logging.getLogger("run")
    logger.info("Starting overzicht_begeleiding_bachelorproeven")

    # Import and start the CLI. We import lazily so that the environment and packages are set up above.
    try:
        # Import using importlib to provide clearer error messages on failures.
        import importlib

        cli_module = importlib.import_module("app.cli.main")
    except Exception as exc:  # pragma: no cover - runtime error handling
        logger.exception("Failed to import the CLI module 'app.cli.main'.")
        print("\nERROR: Cannot start the application because required modules failed to import.")
        print("This usually means a missing dependency or a broken installation.")
        print("Actions to try:")
        print("  1) Ensure you're using the correct Python interpreter (the one where your venv is activated).")
        print("  2) Install runtime dependencies: pip install -r requirements.txt")
        print("  3) If you changed packages, restart your editor/terminal so environment changes take effect.")
        print("\nOriginal error:")
        print("  ", exc)
        return

    # Verify the module exposes a callable `main` function
    if not hasattr(cli_module, "main"):
        logger.error("module app.cli.main does not define a 'main()' function.")
        print("ERROR: CLI entry module does not expose `main()` (expected function).")
        return

    # Run the CLI main loop. Any exceptions bubble up (we log them).
    try:
        cli_main = getattr(cli_module, "main")
        cli_main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
    except Exception as exc:  # pragma: no cover - runtime error handling
        logger.exception("Unhandled exception in CLI main loop.")
        print("\nAn unexpected error occurred while running the CLI.")
        print("See log output for details.")
        print("Original exception:", exc)
    finally:
        logger.info("Exiting application.")


if __name__ == "__main__":  # pragma: no cover - entry point
    main()