"""Aggregate router for API v1 (section 9)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    academic,
    ai,
    approvals,
    attendance,
    audit,
    auth,
    communication,
    documents,
    exams,
    finance,
    hostel,
    hr,
    institutions,
    library,
    lms,
    modules,
    payroll,
    reports,
    students,
    sync,
    transport,
)

api_router = APIRouter()

# Core / platform
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(modules.router, prefix="/modules", tags=["modules"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])

# Student & academic
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(academic.router, prefix="/academic", tags=["academic"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])

# Finance & HR
api_router.include_router(finance.router, prefix="/finance", tags=["finance"])
api_router.include_router(payroll.router, prefix="/payroll", tags=["payroll"])
api_router.include_router(hr.router, prefix="/staff", tags=["staff", "hr"])

# Facilities & services
api_router.include_router(library.router, prefix="/library", tags=["library"])
api_router.include_router(hostel.router, prefix="/hostel", tags=["hostel"])
api_router.include_router(transport.router, prefix="/transport", tags=["transport"])
api_router.include_router(lms.router, prefix="/lms", tags=["lms"])
api_router.include_router(communication.router, prefix="/communication", tags=["communication"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Reporting & AI
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
