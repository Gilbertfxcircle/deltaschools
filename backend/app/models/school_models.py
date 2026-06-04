"""Per-school schema models (section 3.2).

These models carry no fixed schema; the active ``school_{id}`` schema is pinned
per session via ``SET search_path`` (see :mod:`app.db.session`). A representative
core of the per-school tables is implemented here; remaining tables from the
brief (library_books, hostel_allocations, transport_routes, payroll, leaves,
report_cards, documents, notifications) follow the same pattern and are added in
subsequent migrations.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import SchoolBase
from app.models.mixins import TimestampMixin, UUIDPKMixin


class User(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A user inside a school (director, teacher, parent, student, ...)."""

    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))  # see app.core.rbac.Role
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Role(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A custom, per-school role (RBAC is configurable per institution)."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(80), unique=True)
    level: Mapped[int] = mapped_column(Integer)


class Permission(SchoolBase, UUIDPKMixin):
    """Role -> permission mapping, e.g. ('TEACHER', 'marks:write')."""

    __tablename__ = "permissions"

    role_name: Mapped[str] = mapped_column(String(80), index=True)
    permission: Mapped[str] = mapped_column(String(80))


class Student(SchoolBase, UUIDPKMixin, TimestampMixin):
    """Student master record. ``national_id_enc`` is AES-256 encrypted at rest."""

    __tablename__ = "students"

    admission_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    national_id_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Staff(SchoolBase, UUIDPKMixin, TimestampMixin):
    """Staff record (teachers and non-teaching staff)."""

    __tablename__ = "staff"

    staff_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)


class SchoolClass(SchoolBase, UUIDPKMixin, TimestampMixin):
    """An academic class / stream (e.g. 'S1 East')."""

    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(80))
    academic_year: Mapped[str] = mapped_column(String(16))


class Subject(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A subject in the catalog."""

    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(120))


class Enrollment(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A student's enrollment into a class for an academic year."""

    __tablename__ = "enrollments"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(16))


class Attendance(SchoolBase, UUIDPKMixin):
    """A single attendance record for a student on a date."""

    __tablename__ = "attendance"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    class_id: Mapped[str] = mapped_column(ForeignKey("classes.id"), index=True)
    on_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(16))  # present/absent/late/excused
    recorded_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Examination(SchoolBase, UUIDPKMixin, TimestampMixin):
    """An exam schedule (e.g. 'Term 1 Mid-Term')."""

    __tablename__ = "examinations"

    name: Mapped[str] = mapped_column(String(120))
    academic_year: Mapped[str] = mapped_column(String(16))
    term: Mapped[str | None] = mapped_column(String(20), nullable=True)


class Mark(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A student's score in a subject for an examination (protected data)."""

    __tablename__ = "marks"

    examination_id: Mapped[str] = mapped_column(ForeignKey("examinations.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    subject_id: Mapped[str] = mapped_column(ForeignKey("subjects.id"), index=True)
    score: Mapped[float] = mapped_column(Numeric(5, 2))
    grade: Mapped[str | None] = mapped_column(String(4), nullable=True)


class FeeStructure(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A fee definition (e.g. 'S1 Tuition - Term 1')."""

    __tablename__ = "fee_structures"

    name: Mapped[str] = mapped_column(String(120))
    academic_year: Mapped[str] = mapped_column(String(16))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(8), default="UGX")


class Invoice(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A student invoice (protected financial data)."""

    __tablename__ = "invoices"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    fee_structure_id: Mapped[str] = mapped_column(ForeignKey("fee_structures.id"))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    balance: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="unpaid")


class Payment(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A payment transaction against an invoice (protected financial data)."""

    __tablename__ = "payments"

    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(30))  # cash/mtn_momo/airtel/bank
    reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SchoolAuditLog(SchoolBase, UUIDPKMixin):
    """School-level immutable audit trail (mirror of the global one)."""

    __tablename__ = "audit_log"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_id: Mapped[str] = mapped_column(String(36))
    user_email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    school_id: Mapped[str] = mapped_column(String(40))
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(20))
    resource: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default="auto")
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SyncQueue(SchoolBase, UUIDPKMixin):
    """Pending items for cloud sync (section 6.1). Append-only on each write."""

    __tablename__ = "sync_queue"

    operation: Mapped[str] = mapped_column(String(10))  # INSERT/UPDATE/DELETE
    resource: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str] = mapped_column(String(36))
    payload: Mapped[str] = mapped_column(Text)  # JSON
    local_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    synced: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sync_attempts: Mapped[int] = mapped_column(Integer, default=0)
    conflict_flag: Mapped[bool] = mapped_column(Boolean, default=False)
