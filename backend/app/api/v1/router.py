"""Aggregate router for API v1 (section 9)."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    approvals,
    audit,
    auth,
    institutions,
    modules,
    students,
    sync,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(modules.router, prefix="/modules", tags=["modules"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(sync.router, prefix="/sync", tags=["sync"])
