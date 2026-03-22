# app/models/models.py
"""
ORM models for the application with properly-generic classmethod signatures.

This version uses TypeVar + Type annotations so that classmethods preserve the
concrete subclass type for call sites. E.g. when a subclass of `Student` calls
`get_all`, the return type will be `Sequence[ThatSubclass]` instead of
`Sequence[Student]`.

Notes:
- The database column `OPVOLGING.omschrijving` is TEXT. This model maps
  `omschrijving` to SQLAlchemy's `Text` type so the Python model matches the
  current database schema.
- We use `Sequence[...]` for collection return types to avoid variance pitfalls
  while still preserving concrete element types via TypeVars.
"""

from __future__ import annotations

import enum
from typing import Any, Dict, Optional, Sequence, Type, TypeVar

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Session, relationship

from app.db.session import Base

# Type variables for generics bound to the concrete classes
TStudent = TypeVar("TStudent", bound="Student")
TOpvolging = TypeVar("TOpvolging", bound="Opvolging")


class OpvolgingType(enum.Enum):
    contact = "contact"
    controle = "controle"


class Student(Base):
    __tablename__ = "STUDENT"

    id = Column(Integer, primary_key=True)
    voornaam = Column(String, nullable=False)
    naam = Column(String, nullable=False)
    bedrijf = Column(String, nullable=True)
    aceproject = Column(String, nullable=True)
    opvolgingsdocument = Column(String, nullable=True)

    # relationship: a student can have many opvolging records
    # Use a string forward reference to avoid ordering issues.
    opvolgingen = relationship("Opvolging", back_populates="student_obj", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student(id={self.id!r}, naam={self.naam!r}, voornaam={self.voornaam!r})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "voornaam": self.voornaam,
            "naam": self.naam,
            "bedrijf": self.bedrijf,
            "aceproject": self.aceproject,
            "opvolgingsdocument": self.opvolgingsdocument,
        }

    # Generic classmethod signatures: preserve concrete subclass type via TStudent
    @classmethod
    def insert(cls: Type[TStudent], session: Session, commit: bool = True, **kwargs) -> TStudent:
        """
        Create and persist a Student (or subclass) instance.

        Returns the created instance (type TStudent).
        """
        obj = cls(**kwargs)  # type: ignore[call-arg]
        session.add(obj)
        if commit:
            session.commit()
            session.refresh(obj)
        else:
            session.flush()
        return obj  # type: ignore[return-value]

    @classmethod
    def get_by_id(cls: Type[TStudent], session: Session, obj_id: int) -> Optional[TStudent]:
        """
        Retrieve an instance by primary key; returns Optional[TStudent].
        """
        return session.get(cls, obj_id)  # type: ignore[return-value]

    @classmethod
    def get_all(cls: Type[TStudent], session: Session, offset: int = 0, limit: Optional[int] = None) -> Sequence[TStudent]:
        """
        Return all instances of `cls` (possibly a subclass). The return type is
        Sequence[TStudent] to preserve element typing while avoiding invariance issues.
        """
        q = session.query(cls).offset(offset)
        if limit is not None:
            q = q.limit(limit)
        # q.all() returns a List[TStudent] at runtime; Sequence[TStudent] is compatible.
        return q.all()  # type: ignore[return-value]

    @classmethod
    def update(cls: Type[TStudent], session: Session, obj_id: int, commit: bool = True, **kwargs) -> Optional[TStudent]:
        """
        Update fields for the instance with id `obj_id`. Returns the updated object
        (type TStudent) or None if not found.
        """
        obj = session.get(cls, obj_id)  # type: ignore[assignment]
        if obj is None:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        if commit:
            session.commit()
            session.refresh(obj)
        else:
            session.flush()
        return obj  # type: ignore[return-value]


class Opvolging(Base):
    __tablename__ = "OPVOLGING"

    id = Column(Integer, primary_key=True)
    datum = Column(String, nullable=False)  # In the database this column is TEXT; keep it as String in the model.
    type = Column(String, nullable=False)  # Enforced by check constraint below.
    # Note: the database column `omschrijving` is TEXT; map to SQLAlchemy `Text`.
    omschrijving = Column(Text, nullable=True)
    student = Column(Integer, ForeignKey("STUDENT.id"), nullable=True)

    # relationship back to Student
    student_obj = relationship("Student", back_populates="opvolgingen")

    __table_args__ = (
        CheckConstraint("type IN ('contact','controle')", name="ck_opvolging_type_allowed"),
    )

    def __repr__(self) -> str:
        return f"<Opvolging(id={self.id!r}, datum={self.datum!r}, type={self.type!r}, student={self.student!r})>"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "datum": self.datum,
            "type": self.type,
            "omschrijving": self.omschrijving,
            "student": self.student,
        }

    # Generic classmethod signatures for Opvolging preserving subclass types
    @classmethod
    def insert(cls: Type[TOpvolging], session: Session, commit: bool = True, **kwargs) -> TOpvolging:
        """
        Create and persist an Opvolging (or subclass) instance.
        """
        # basic validation for type
        t = kwargs.get("type")
        if t is not None and t not in {v.value for v in OpvolgingType}:
            raise ValueError(f"Invalid type: {t!r}. Allowed: {[v.value for v in OpvolgingType]}")
        obj = cls(**kwargs)  # type: ignore[call-arg]
        session.add(obj)
        if commit:
            session.commit()
            session.refresh(obj)
        else:
            session.flush()
        return obj  # type: ignore[return-value]

    @classmethod
    def get_by_id(cls: Type[TOpvolging], session: Session, obj_id: int) -> Optional[TOpvolging]:
        return session.get(cls, obj_id)  # type: ignore[return-value]

    @classmethod
    def get_all_for_student(cls: Type[TOpvolging], session: Session, student_id: int, offset: int = 0, limit: Optional[int] = None) -> Sequence[TOpvolging]:
        """
        Return Opvolging records for a specific student. Return type preserves subclass type.
        """
        q = session.query(cls).filter(cls.student == student_id).order_by(cls.datum).offset(offset)
        if limit is not None:
            q = q.limit(limit)
        return q.all()  # type: ignore[return-value]

    @classmethod
    def update(cls: Type[TOpvolging], session: Session, obj_id: int, commit: bool = True, **kwargs) -> Optional[TOpvolging]:
        """
        Update provided fields for the Opvolging with id `obj_id`. Returns the updated
        object (type TOpvolging) or None if not found.
        """
        obj = session.get(cls, obj_id)  # type: ignore[assignment]
        if obj is None:
            return None
        if "type" in kwargs:
            t = kwargs["type"]
            if t not in {v.value for v in OpvolgingType}:
                raise ValueError(f"Invalid type: {t!r}. Allowed: {[v.value for v in OpvolgingType]}")
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        if commit:
            session.commit()
            session.refresh(obj)
        else:
            session.flush()
        return obj  # type: ignore[return-value]
