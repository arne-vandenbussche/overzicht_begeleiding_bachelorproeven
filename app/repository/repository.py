"""
Repository helpers for Student and Opvolging.

This module provides a small repository layer that wraps SQLAlchemy sessions
and the ORM models to perform common CRUD operations.

Design notes:
- Each repository method accepts an optional `session: Session`. If a session
  is provided the repository will use it and will only commit if `commit=True`.
  If no session is provided the repository will create its own session using
  `session_scope()` which commits/rolls-back automatically.
- Methods return ORM instances (not plain dicts). Use the model's `to_dict()`
  helper if you need serializable output.
- This file expects the project-level SQLAlchemy setup and models to exist:
  - app.db.session: `session_scope`, `get_session`
  - app.models.models: `Student`, `Opvolging`
"""

from typing import Any, Dict, List, Optional
import logging

from sqlalchemy.orm import Session

from app.db.session import session_scope, get_session
from app.models.models import Student, Opvolging


class StudentRepository:
    """Repository for `Student` model."""

    @staticmethod
    def create(data: Dict[str, Any], session: Optional[Session] = None, commit: bool = True) -> Student:
        """
        Create and persist a Student.

        :param data: dict of Student fields (e.g. voornaam, naam, bedrijf, ...)
        :param session: optional SQLAlchemy Session
        :param commit: whether to commit the session (ignored when using an external
                       session and the caller wants to manage transactions themselves)
        :return: persisted Student instance with id populated
        """
        if session is None:
            with session_scope() as s:
                return Student.insert(s, commit=True, **data)
        else:
            # Use provided session. Delegate to model method for consistency.
            # Respect the 'commit' flag.
            return Student.insert(session, commit=commit, **data)

    @staticmethod
    def get_by_id(student_id: int, session: Optional[Session] = None) -> Optional[Student]:
        """
        Retrieve a Student by primary key.
        """
        if session is None:
            with session_scope() as s:
                return Student.get_by_id(s, student_id)
        else:
            return Student.get_by_id(session, student_id)

    @staticmethod
    def list_all(session: Optional[Session] = None, offset: int = 0, limit: Optional[int] = None) -> List[Student]:
        """
        List students with optional pagination.
        Returns a concrete `list` to match the annotated return type.
        """
        if session is None:
            with session_scope() as s:
                result = Student.get_all(s, offset=offset, limit=limit)
                return list(result)
        else:
            result = Student.get_all(session, offset=offset, limit=limit)
            return list(result)

    @staticmethod
    def update(student_id: int, changes: Dict[str, Any], session: Optional[Session] = None, commit: bool = True) -> Optional[Student]:
        """
        Update an existing Student with provided fields.
        Returns the updated Student or None if not found.
        """
        if session is None:
            with session_scope() as s:
                return Student.update(s, student_id, commit=commit, **changes)
        else:
            return Student.update(session, student_id, commit=commit, **changes)

    @staticmethod
    def delete(student_id: int, session: Optional[Session] = None, commit: bool = True) -> bool:
        """
        Delete a student by id. Returns True if a row was deleted, False if no such student.
        Note: This performs a SQLAlchemy ORM delete via fetching the object first so
        that cascade rules and relationships are respected.
        """
        own_session = False
        s = session
        if s is None:
            s = get_session()
            own_session = True

        try:
            obj = s.get(Student, student_id)
            if obj is None:
                if own_session:
                    s.close()
                return False
            s.delete(obj)
            if commit:
                s.commit()
            else:
                s.flush()
            if own_session:
                s.close()
            return True
        except Exception:
            # Ensure we attempt to rollback and close the session if we created it,
            # but do not silence any errors. Log rollback/close failures and re-raise
            # the original exception so callers receive the original traceback.
            if own_session:
                # try to rollback and close if we created the session
                try:
                    s.rollback()
                except Exception as rb_exc:
                    # Log rollback failure but keep original exception
                    logging.exception("Failed to rollback session after exception: %s", rb_exc)
                try:
                    s.close()
                except Exception as close_exc:
                    logging.exception("Failed to close session after exception: %s", close_exc)
            # Re-raise original exception preserving traceback
            raise


class OpvolgingRepository:
    """Repository for `Opvolging` model."""

    @staticmethod
    def create(data: Dict[str, Any], session: Optional[Session] = None, commit: bool = True) -> Opvolging:
        """
        Create and persist an Opvolging record.

        :param data: dict of Opvolging fields (datum, type, omschrijving, student)
        :param session: optional SQLAlchemy Session
        :param commit: whether to commit the session
        :return: persisted Opvolging instance
        """
        if session is None:
            with session_scope() as s:
                return Opvolging.insert(s, commit=True, **data)
        else:
            return Opvolging.insert(session, commit=commit, **data)

    @staticmethod
    def get_by_id(opvolging_id: int, session: Optional[Session] = None) -> Optional[Opvolging]:
        """
        Retrieve an Opvolging by id.
        """
        if session is None:
            with session_scope() as s:
                return Opvolging.get_by_id(s, opvolging_id)
        else:
            return Opvolging.get_by_id(session, opvolging_id)

    @staticmethod
    def list_all(session: Optional[Session] = None, offset: int = 0, limit: Optional[int] = None) -> List[Opvolging]:
        """
        List all Opvolging records with optional pagination.
        Returns a concrete `list` to match the annotated return type.
        """
        if session is None:
            with session_scope() as s:
                q = s.query(Opvolging).order_by(Opvolging.datum).offset(offset)
                if limit is not None:
                    q = q.limit(limit)
                return q.all()  # q.all() returns a concrete list
        else:
            q = session.query(Opvolging).order_by(Opvolging.datum).offset(offset)
            if limit is not None:
                q = q.limit(limit)
            return q.all()

    @staticmethod
    def list_for_student(student_id: int, session: Optional[Session] = None, offset: int = 0, limit: Optional[int] = None) -> List[Opvolging]:
        """
        List Opvolging records for a specific student.
        Returns a concrete `list` to match the annotated return type.
        """
        if session is None:
            with session_scope() as s:
                result = Opvolging.get_all_for_student(s, student_id, offset=offset, limit=limit)
                return list(result)
        else:
            result = Opvolging.get_all_for_student(session, student_id, offset=offset, limit=limit)
            return list(result)

    @staticmethod
    def update(opvolging_id: int, changes: Dict[str, Any], session: Optional[Session] = None, commit: bool = True) -> Optional[Opvolging]:
        """
        Update an Opvolging. Returns the updated object or None if not found.
        """
        if session is None:
            with session_scope() as s:
                return Opvolging.update(s, opvolging_id, commit=commit, **changes)
        else:
            return Opvolging.update(session, opvolging_id, commit=commit, **changes)

    @staticmethod
    def delete(opvolging_id: int, session: Optional[Session] = None, commit: bool = True) -> bool:
        """
        Delete an Opvolging by id. Returns True if deleted, False if not found.
        """
        own_session = False
        s = session
        if s is None:
            s = get_session()
            own_session = True

        try:
            obj = s.get(Opvolging, opvolging_id)
            if obj is None:
                if own_session:
                    s.close()
                return False
            s.delete(obj)
            if commit:
                s.commit()
            else:
                s.flush()
            if own_session:
                s.close()
            return True
        except Exception:
            # Ensure we attempt to rollback and close the session if we created it,
            # but do not silence any errors. Log rollback/close failures and re-raise
            # the original exception so callers receive the original traceback.
            if own_session:
                try:
                    s.rollback()
                except Exception as rb_exc:
                    logging.exception("Failed to rollback session after exception: %s", rb_exc)
                try:
                    s.close()
                except Exception as close_exc:
                    logging.exception("Failed to close session after exception: %s", close_exc)
            raise