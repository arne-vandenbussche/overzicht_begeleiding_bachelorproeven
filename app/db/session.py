# app/db/session.py
"""
SQLAlchemy engine and session setup.

- Loads database URL from the project's .env (keys: SQLALCHEMY_DATABASE_URL or DATABASE_URL).
- Exposes `engine`, `SessionLocal`, and `Base` for models.
- Provides a `session_scope` context manager for safe transactional sessions.
- Provides `init_db()` helper to create tables from model metadata.

This file targets SQLAlchemy 1.4+ usage (uses the ORM Session class).
"""

from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import sys
import logging

# Try to load .env from project root if python-dotenv is available.
# This is optional (import error is handled) so the code still works if dotenv isn't installed
# and environment variables are provided by other means.
try:
    from dotenv import load_dotenv

    # Prefer loading a .env file located at project root (one level up from app/)
    project_root = Path(__file__).resolve().parents[2]  # .../overzicht_begeleiding_bachelorproeven/app/db -> project root
    dotenv_path = project_root / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        # fallback to default loader (looks in CWD)
        load_dotenv()
except Exception:
    # If python-dotenv isn't installed or load fails, log the error to a file and print a message,\
    # then re-raise the exception so failures are not silently ignored.\

    # Determine a log file path (prefer project root; fallback to CWD)\
    try:
        project_root = Path(__file__).resolve().parents[2]
        log_file = project_root/"app.log"
    except Exception:
        log_file = Path.cwd()/"app.log"
    # Configure logging to write to file (and still allow console output via StreamHandler)\
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(
            logging.Formatter("%(levelname)s: %(message)s")
        )
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.WARNING)
    msg = "Failed to load .env using python-dotenv; continuing with environment variables if available."
    # Include original exception details for debugging
    logger.exception(msg)
    print(msg, file=sys.stderr)
    # Re-raise the original exception so callers are aware of failures (no longer silenced).
    raise

# Read the DB url from environment; fall back to a reasonable default
DATABASE_URL: str = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL") or "sqlite:///./opvolging.db"

# Detect sqlite and set proper connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # For file-based SQLite, allow usage from multiple threads by disabling same-thread check
    # (SQLAlchemy's recommended option for SQLite when using session across threads).
    connect_args = {"check_same_thread": False}

# engine is created once and reused across the application
engine: Engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

# Use a Session factory bound to the engine
# expire_on_commit=False keeps objects usable after commit (common for web apps / CLI apps)
SessionLocal: sessionmaker = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)

# Declarative base for model classes
Base = declarative_base()


def get_engine() -> Engine:
    """
    Return the application Engine instance.

    If you need a fresh engine for tests, create your own with `create_engine(...)`.
    """
    return engine


def get_session() -> Session:
    """
    Return a new Session instance from the configured SessionLocal factory.

    Caller is responsible for closing the session or using the `session_scope` context manager.
    """
    return SessionLocal()


@contextmanager
def session_scope() -> Iterator[Session]:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with session_scope() as session:
            session.add(obj)
            # changes are committed on successful exit, rolled back on exception
    """
    session: Optional[Session] = None
    try:
        session = get_session()
        yield session
        session.commit()
    except Exception:
        if session is not None:
            session.rollback()
        raise
    finally:
        if session is not None:
            session.close()


def init_db(bind_engine: Optional[Engine] = None) -> None:
    """
    Create all database tables from the metadata of `Base`.

    You can supply a custom engine (useful for tests); otherwise the module engine is used.
    """
    _engine = bind_engine or engine
    Base.metadata.create_all(bind=_engine)
