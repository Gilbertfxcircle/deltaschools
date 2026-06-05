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



# ---------------------------------------------------------------------------
# Extended module tables (academic, exams, payroll, library, hostel, transport,
# lms, hr, communication, documents). Same per-tenant schema pattern as above.
# ---------------------------------------------------------------------------


class ReportCard(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A generated report card snapshot for a student/exam (protected data)."""

    __tablename__ = "report_cards"

    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    examination_id: Mapped[str] = mapped_column(ForeignKey("examinations.id"), index=True)
    average: Mapped[float] = mapped_column(Numeric(5, 2))
    gpa: Mapped[float] = mapped_column(Numeric(4, 2))
    overall_grade: Mapped[str] = mapped_column(String(4))
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class Payroll(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A staff payslip record for a period (protected financial data)."""

    __tablename__ = "payroll"

    staff_id: Mapped[str] = mapped_column(ForeignKey("staff.id"), index=True)
    period: Mapped[str] = mapped_column(String(16))  # e.g. 2026-06
    gross: Mapped[float] = mapped_column(Numeric(12, 2))
    paye: Mapped[float] = mapped_column(Numeric(12, 2))
    other_deductions: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    net: Mapped[float] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), default="draft")


class Leave(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A staff leave record (hr_management module)."""

    __tablename__ = "leaves"

    staff_id: Mapped[str] = mapped_column(ForeignKey("staff.id"), index=True)
    leave_type: Mapped[str] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class LibraryBook(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A book in the library catalog (library module)."""

    __tablename__ = "library_books"

    isbn: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_copies: Mapped[int] = mapped_column(Integer, default=1)
    available_copies: Mapped[int] = mapped_column(Integer, default=1)


class LibraryLoan(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A book loan to a borrower (library module)."""

    __tablename__ = "library_loans"

    book_id: Mapped[str] = mapped_column(ForeignKey("library_books.id"), index=True)
    borrower_id: Mapped[str] = mapped_column(String(36), index=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class HostelRoom(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A hostel room with a capacity (hostel module)."""

    __tablename__ = "hostel_rooms"

    name: Mapped[str] = mapped_column(String(40))
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)


class HostelAllocation(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A student's hostel room assignment (hostel module)."""

    __tablename__ = "hostel_allocations"

    room_id: Mapped[str] = mapped_column(ForeignKey("hostel_rooms.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(16))


class TransportRoute(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A transport route definition (transport module)."""

    __tablename__ = "transport_routes"

    name: Mapped[str] = mapped_column(String(120))
    fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=0)


class TransportAssignment(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A student assigned to a transport route (transport module)."""

    __tablename__ = "transport_assignments"

    route_id: Mapped[str] = mapped_column(ForeignKey("transport_routes.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    stop_name: Mapped[str | None] = mapped_column(String(120), nullable=True)


class LmsCourse(SchoolBase, UUIDPKMixin, TimestampMixin):
    """An e-learning course (lms module)."""

    __tablename__ = "lms_courses"

    title: Mapped[str] = mapped_column(String(200))
    subject_id: Mapped[str | None] = mapped_column(ForeignKey("subjects.id"), nullable=True)
    teacher_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LmsLesson(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A lesson/resource within an LMS course (lms module)."""

    __tablename__ = "lms_lessons"

    course_id: Mapped[str] = mapped_column(ForeignKey("lms_courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    content_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class Notification(SchoolBase, UUIDPKMixin, TimestampMixin):
    """An internal notification (communication_hub module)."""

    __tablename__ = "notifications"

    recipient_id: Mapped[str] = mapped_column(String(36), index=True)
    channel: Mapped[str] = mapped_column(String(20), default="in_app")  # in_app/sms/email
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class Document(SchoolBase, UUIDPKMixin, TimestampMixin):
    """A file reference stored in object storage (document_management module)."""

    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
